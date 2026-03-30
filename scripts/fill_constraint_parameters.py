"""
用 LLM 为参数化约束逐条填写参数值。

支持两类后端：
- `openai_compatible`: 标准 `/chat/completions`
- `minimax_proxy`: 用户自有 proxy 网关
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from constraint_parameterization import (
    SYSTEM_PROMPT,
    build_parameterization_prompt,
    is_parametric_constraint,
    parse_llm_json,
    render_parametric_constraint,
    validate_and_normalize_params,
)


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
TRACKS_PATH = DATA_DIR / "tracks" / "id_heldout_all_tracks.json"
OUTPUT_PATH = DATA_DIR / "tracks" / "llm_constraint_parameters.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Fill parameterized constraints with LLM outputs.")
    parser.add_argument("--tracks", type=Path, default=TRACKS_PATH, help="Input track json path.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output json path.")
    parser.add_argument("--model", default="gpt-4.1-mini", help="Model name for the API call.")
    parser.add_argument(
        "--provider",
        choices=["openai_compatible", "minimax_proxy"],
        default="openai_compatible",
        help="LLM API backend provider.",
    )
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Environment variable containing the API key.")
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"), help="OpenAI-compatible base URL.")
    parser.add_argument("--minimax-token-env", default="MINIMAX_TOKEN", help="Environment variable containing the minimax proxy token.")
    parser.add_argument("--billing-token-env", default="BILLING_TOKEN", help="Environment variable containing the minimax billing token.")
    parser.add_argument(
        "--minimax-proxy-url",
        default=os.environ.get("MINIMAX_PROXY_URL", "http://thirdpart-proxy-prod.xaminim.com/v1/proxy"),
        help="Minimax proxy endpoint URL.",
    )
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature.")
    parser.add_argument("--max-tokens", type=int, default=220, help="Max completion tokens.")
    parser.add_argument("--max-workers", type=int, default=8, help="Parallel request workers.")
    parser.add_argument("--max-retries", type=int, default=2, help="Retries after parse/validation failure.")
    parser.add_argument("--timeout-sec", type=int, default=60, help="Per request timeout in seconds.")
    parser.add_argument("--limit", type=int, default=0, help="Only process the first N requests.")
    parser.add_argument("--preview-count", type=int, default=0, help="Print the first N prompts and exit.")
    return parser.parse_args()


def load_track_samples(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_requests(samples):
    requests = []
    for sample in samples:
        for constraint_id in sample.get("constraint_ids", []):
            if not is_parametric_constraint(constraint_id):
                continue
            requests.append(
                {
                    "sample_id": sample["sample_id"],
                    "query_id": sample["query_id"],
                    "split": sample["split"],
                    "track": sample["track"],
                    "source_type": sample["source_type"],
                    "origin_task": sample.get("origin_task"),
                    "template_id": sample.get("template_id"),
                    "template_name": sample["template_name"],
                    "role_mode": sample["role_mode"],
                    "role": sample.get("role"),
                    "query_input": sample["query_input"],
                    "constraint_id": constraint_id,
                }
            )
    requests.sort(key=lambda x: (x["sample_id"], x["constraint_id"]))
    return requests


def load_existing_records(path: Path):
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = {}
    for record in payload.get("records", []):
        key = (record["sample_id"], record["constraint_id"])
        records[key] = record
    return records


def write_output(path: Path, *, meta: dict, records: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": meta,
        "records": [
            records[key]
            for key in sorted(
                records,
                key=lambda x: (x[0], x[1]),
            )
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_message_text(message):
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(item.get("text", ""))
        return "\n".join(chunks)
    return ""


def call_chat_completion(*, base_url: str, api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int, timeout_sec: int):
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_sec) as response:
        data = json.loads(response.read().decode("utf-8"))
    choices = data.get("choices") or []
    if not choices:
        raise ValueError(f"API 未返回 choices: {data}")
    message = choices[0].get("message") or {}
    content = _extract_message_text(message)
    if not content:
        raise ValueError(f"API 返回内容为空: {data}")
    return content


def call_minimax_proxy_completion(
    *,
    proxy_url: str,
    minimax_token: str,
    billing_token: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    timeout_sec: int,
):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    request = urllib.request.Request(
        proxy_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json;",
            "minimax_token": minimax_token,
            "billing_token": billing_token,
            "Accept-Encoding": "deflate",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_sec) as response:
        data = json.loads(response.read().decode("utf-8"))
    choices = data.get("choices") or []
    if not choices:
        raise ValueError(f"minimax proxy 未返回 choices: {data}")
    message = choices[0].get("message") or {}
    content = _extract_message_text(message)
    if not content:
        raise ValueError(f"minimax proxy 返回内容为空: {data}")
    return content


def generate_one(
    request_item,
    *,
    provider: str,
    base_url: str,
    api_key: str,
    minimax_proxy_url: str,
    minimax_token: str,
    billing_token: str,
    model: str,
    temperature: float,
    max_tokens: int,
    timeout_sec: int,
    max_retries: int,
):
    prompt = build_parameterization_prompt(request_item, request_item["constraint_id"])
    last_error = None
    raw_response = ""

    for attempt in range(1, max_retries + 2):
        retry_prompt = prompt
        if last_error:
            retry_prompt += f"\n\n上一次输出未通过校验，原因：{last_error}\n请重新输出唯一合法的 JSON 对象。"
        if provider == "openai_compatible":
            raw_response = call_chat_completion(
                base_url=base_url,
                api_key=api_key,
                model=model,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=retry_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_sec=timeout_sec,
            )
        else:
            raw_response = call_minimax_proxy_completion(
                proxy_url=minimax_proxy_url,
                minimax_token=minimax_token,
                billing_token=billing_token,
                model=model,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=retry_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_sec=timeout_sec,
            )
        try:
            parsed = parse_llm_json(raw_response)
            params = validate_and_normalize_params(
                request_item["constraint_id"],
                parsed,
                query_input=request_item.get("query_input"),
            )
            return {
                "sample_id": request_item["sample_id"],
                "query_id": request_item["query_id"],
                "split": request_item["split"],
                "track": request_item["track"],
                "constraint_id": request_item["constraint_id"],
                "params": params,
                "rendered_text": render_parametric_constraint(request_item["constraint_id"], params),
                "model": model,
                "attempts": attempt,
                "raw_response": raw_response,
            }
        except Exception as exc:
            last_error = str(exc)

    raise ValueError(
        f"sample_id={request_item['sample_id']} constraint_id={request_item['constraint_id']} 连续失败，最后错误：{last_error}；最后输出：{raw_response}"
    )


def main():
    args = parse_args()
    api_key = os.environ.get(args.api_key_env)
    minimax_token = os.environ.get(args.minimax_token_env)
    billing_token = os.environ.get(args.billing_token_env)
    if args.preview_count == 0:
        if args.provider == "openai_compatible" and not api_key:
            raise SystemExit(f"缺少 API key，请设置环境变量 {args.api_key_env}")
        if args.provider == "minimax_proxy" and (not minimax_token or not billing_token):
            raise SystemExit(
                f"缺少 minimax proxy 凭证，请设置环境变量 {args.minimax_token_env} 和 {args.billing_token_env}"
            )

    samples = load_track_samples(args.tracks)
    requests = collect_requests(samples)
    if args.limit:
        requests = requests[: args.limit]

    if args.preview_count:
        previews = []
        for request_item in requests[: args.preview_count]:
            previews.append(
                {
                    "sample_id": request_item["sample_id"],
                    "constraint_id": request_item["constraint_id"],
                    "prompt": build_parameterization_prompt(request_item, request_item["constraint_id"]),
                }
            )
        print(json.dumps(previews, ensure_ascii=False, indent=2))
        return

    existing_records = load_existing_records(args.output)
    pending = [
        request_item
        for request_item in requests
        if (request_item["sample_id"], request_item["constraint_id"]) not in existing_records
    ]

    if not pending:
        print("all parameter records already exist")
        return

    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    failures = []
    completed = 0
    total = len(pending)

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_map = {
            executor.submit(
                generate_one,
                request_item,
                provider=args.provider,
                base_url=args.base_url,
                api_key=api_key,
                minimax_proxy_url=args.minimax_proxy_url,
                minimax_token=minimax_token,
                billing_token=billing_token,
                model=args.model,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout_sec=args.timeout_sec,
                max_retries=args.max_retries,
            ): request_item
            for request_item in pending
        }

        for future in as_completed(future_map):
            request_item = future_map[future]
            key = (request_item["sample_id"], request_item["constraint_id"])
            try:
                existing_records[key] = future.result()
                completed += 1
                if completed % 20 == 0 or completed == total:
                    meta = {
                        "started_at": started_at,
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "provider": args.provider,
                        "model": args.model,
                        "base_url": args.base_url,
                        "tracks_path": str(args.tracks),
                        "total_requests": len(requests),
                        "completed_records": len(existing_records),
                    }
                    write_output(args.output, meta=meta, records=existing_records)
                    print(f"progress {completed}/{total}", file=sys.stderr)
            except Exception as exc:
                failures.append({"request": request_item, "error": str(exc)})
                print(f"failed {request_item['sample_id']} {request_item['constraint_id']}: {exc}", file=sys.stderr)

    meta = {
        "started_at": started_at,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "provider": args.provider,
        "model": args.model,
        "base_url": args.base_url,
        "tracks_path": str(args.tracks),
        "total_requests": len(requests),
        "completed_records": len(existing_records),
        "failures": len(failures),
    }
    write_output(args.output, meta=meta, records=existing_records)

    if failures:
        failure_path = args.output.with_suffix(".failures.json")
        failure_path.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(f"共有 {len(failures)} 条请求失败，详见 {failure_path}")

    print(f"done {len(existing_records)} records")


if __name__ == "__main__":
    main()
