#!/usr/bin/env python3
"""
FinIF Benchmark — 多模型回复生成
对 6 个通的 GPT 模型 × 54 cases 生成回复。
输出: output/responses_{model_short}.jsonl
"""

import json
import os
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(DEMO_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from gpt_call_all import get_gpt_response

MODELS = [
    "gpt-4o-2024-11-20",
    "gpt-5-2025-08-07",
]


def model_short_name(model):
    return model.replace("/", "_")


def load_all_cases():
    path = os.path.join(DEMO_DIR, "benchmark_all.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    cases = []
    for c in data["cases"]:
        cases.append({
            "case_id": c["case_id"],
            "prompt": c["prompt"],
            "context": c.get("context", ""),
        })
    return cases


REASONING_MODELS = {"gpt-5-2025-08-07", "o3-2025-04-16", "o3-mini", "o1-2024-12-17"}


def gen_one(case, model, temperature, max_tokens):
    effective_max_tokens = 16384 if model in REASONING_MODELS else max_tokens
    messages = [{"role": "user", "content": case["prompt"]}]
    resp = get_gpt_response(
        messages=messages,
        model_version=model,
        temperature=temperature,
        max_tokens=effective_max_tokens,
        max_try=5,
    )
    return resp


def run_model(model, cases, output_dir, temperature, max_tokens, workers):
    short = model_short_name(model)
    out_path = os.path.join(output_dir, f"responses_{short}.jsonl")

    existing_ids = set()
    if os.path.isfile(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    existing_ids.add(obj["case_id"])

    todo = [c for c in cases if c["case_id"] not in existing_ids]
    print(f"\n{'='*60}")
    print(f"Model: {model}")
    print(f"  Total: {len(cases)}, Already done: {len(existing_ids)}, Todo: {len(todo)}")

    if not todo:
        print("  All done, skipping.")
        return

    done = 0
    failed = 0

    def process(case):
        try:
            resp = gen_one(case, model, temperature, max_tokens)
            if resp is None:
                return case["case_id"], None, "API returned None"
            return case["case_id"], resp, None
        except Exception as e:
            return case["case_id"], None, str(e)

    if workers <= 1:
        for case in todo:
            case_id, resp, err = process(case)
            if resp is not None:
                record = {
                    "case_id": case_id,
                    "model": model,
                    "response": resp,
                    "context": case["context"],
                }
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                done += 1
                print(f"  [{done+failed}/{len(todo)}] {case_id} OK ({len(resp)} chars)")
            else:
                failed += 1
                print(f"  [{done+failed}/{len(todo)}] {case_id} FAILED: {err}")
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            future_map = {pool.submit(process, c): c for c in todo}
            for future in as_completed(future_map):
                case = future_map[future]
                case_id, resp, err = future.result()
                if resp is not None:
                    record = {
                        "case_id": case_id,
                        "model": model,
                        "response": resp,
                        "context": case["context"],
                    }
                    with open(out_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    done += 1
                    print(f"  [{done+failed}/{len(todo)}] {case_id} OK ({len(resp)} chars)")
                else:
                    failed += 1
                    print(f"  [{done+failed}/{len(todo)}] {case_id} FAILED: {err}")

    print(f"  Result: {done} OK, {failed} failed")


def main():
    parser = argparse.ArgumentParser(description="FinIF Benchmark multi-model response generation")
    parser.add_argument("--models", nargs="*", default=None, help="Models to test (default: all 6)")
    parser.add_argument("--output-dir", default=os.path.join(DEMO_DIR, "output"), help="Output directory")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--workers", type=int, default=3, help="Concurrent workers per model")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    models = args.models if args.models else MODELS
    cases = load_all_cases()
    print(f"Loaded {len(cases)} cases")
    print(f"Models to run: {models}")

    for model in models:
        run_model(model, cases, args.output_dir, args.temperature, args.max_tokens, args.workers)

    print(f"\n{'='*60}")
    print("All models done!")
    for model in models:
        short = model_short_name(model)
        path = os.path.join(args.output_dir, f"responses_{short}.jsonl")
        if os.path.isfile(path):
            with open(path) as f:
                count = sum(1 for l in f if l.strip())
            print(f"  {model}: {count}/54 responses")


if __name__ == "__main__":
    main()
