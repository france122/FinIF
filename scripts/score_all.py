#!/usr/bin/env python3
"""
统一评分脚本：对 test response 进行 hard (rule checker) + soft (LLM judge) 评分。

支持多模型输出文件，增量写入，断点续跑。

用法:
  python scripts/score_all.py \
    --response-file data/scores/gpt5_responses.jsonl \
    --output-dir data/scores/gpt5 \
    --judge-model gpt-5-2025-08-07 \
    --concurrency 3
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from verifier.registry import load_constraint_registry, get_constraint_meta
from verifier.rule_runner import run_rule_check
from verifier.rubric_runner import build_judge_prompt
from ref_local_gpt import get_gpt_response


def score_hard(sample_id, constraint, response_text):
    """Hard 约束评分：本地 rule checker"""
    cid = constraint["constraint_id"]
    params = constraint.get("filled_params", {})
    # 归一化 params key 大小写（track 数据用大写 N，checker 用小写 n）
    normalized = {}
    for k, v in params.items():
        normalized[k] = v
        normalized[k.lower()] = v
        normalized[k.upper()] = v
    try:
        result = run_rule_check(cid, response_text, params=normalized)
        return {
            "sample_id": sample_id,
            "constraint_id": cid,
            "hardness": "hard",
            "score": result.score,
            "passed": result.passed,
            "message": result.message,
        }
    except Exception as e:
        return {
            "sample_id": sample_id,
            "constraint_id": cid,
            "hardness": "hard",
            "score": 0,
            "passed": False,
            "message": f"checker error: {e}",
        }


def score_soft(sample_id, constraint, query_text, response_text, judge_model):
    """Soft 约束评分：调 LLM judge"""
    cid = constraint["constraint_id"]
    rendered = constraint.get("rendered_text", "")
    try:
        prompt_data = build_judge_prompt(
            cid, query_text, response_text,
            rendered_constraint_text=rendered,
        )
        messages = [
            {"role": "system", "content": prompt_data["system"]},
            {"role": "user", "content": prompt_data["user"]},
        ]
        raw = get_gpt_response(messages, judge_model, temperature=0, max_tokens=512)
        if not raw:
            return {
                "sample_id": sample_id,
                "constraint_id": cid,
                "hardness": "soft",
                "score": 0,
                "passed": False,
                "message": "judge returned empty",
            }
        # 解析 JSON
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        # 尝试解析
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                parsed = json.loads(m.group())
            else:
                return {
                    "sample_id": sample_id,
                    "constraint_id": cid,
                    "hardness": "soft",
                    "score": 0,
                    "passed": False,
                    "message": f"JSON parse failed: {text[:100]}",
                }
        score = parsed.get("score", 0)
        passed = parsed.get("passed", False)
        reason = parsed.get("reason", "")
        return {
            "sample_id": sample_id,
            "constraint_id": cid,
            "hardness": "soft",
            "score": score,
            "passed": passed,
            "message": reason,
        }
    except Exception as e:
        return {
            "sample_id": sample_id,
            "constraint_id": cid,
            "hardness": "soft",
            "score": 0,
            "passed": False,
            "message": f"judge error: {e}",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--response-file", required=True, help="Response JSONL 文件")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--judge-model", default="gpt-5-2025-08-07", help="Soft 评分 judge 模型")
    parser.add_argument("--concurrency", type=int, default=3, help="Soft 评分并发数")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    hard_output = output_dir / "hard_scores.jsonl"
    soft_output = output_dir / "soft_scores.jsonl"

    # 加载 response 数据
    with open(args.response_file) as f:
        responses = [json.loads(line) for line in f]
    print(f"Loaded {len(responses)} responses")

    # 加载 registry
    registry = load_constraint_registry()

    # 分类任务
    hard_tasks = []
    soft_tasks = []
    for resp in responses:
        sample_id = resp.get("sample_id", "")
        # 兼容两种格式：直接 response 字段 或 vulcan_output.response
        response_text = resp.get("response", "")
        if not response_text and resp.get("vulcan_output"):
            response_text = resp["vulcan_output"].get("response", "")
        # query 从 messages 取
        query_text = resp.get("prompt", "")
        if not query_text and resp.get("messages"):
            query_text = resp["messages"][0].get("content", "")
        # constraints 兼容 vulcan_output
        constraints = resp.get("constraints", [])
        if not constraints and resp.get("vulcan_output"):
            constraints = resp["vulcan_output"].get("constraints", [])

        if not response_text.strip():
            continue

        for c in constraints:
            cid = c["constraint_id"]
            meta = registry.get(cid)
            if not meta:
                print(f"  Warning: unknown constraint {cid}, skipping")
                continue
            if meta["check_mode"] == "rule":
                hard_tasks.append((sample_id, c, response_text))
            else:
                soft_tasks.append((sample_id, c, query_text, response_text))

    print(f"Hard tasks: {len(hard_tasks)}, Soft tasks: {len(soft_tasks)}")

    # --- Hard 评分（本地，瞬间完成）---
    print("\n=== Hard Scoring ===")
    # 断点续跑
    done_hard = set()
    if hard_output.exists():
        with open(hard_output) as f:
            for line in f:
                r = json.loads(line)
                done_hard.add(f"{r['sample_id']}_{r['constraint_id']}")
    remaining_hard = [(s, c, r) for s, c, r in hard_tasks if f"{s}_{c['constraint_id']}" not in done_hard]
    print(f"  Total: {len(hard_tasks)}, Done: {len(done_hard)}, Remaining: {remaining_hard and len(remaining_hard)}")

    with open(hard_output, "a", encoding="utf-8") as f:
        for sample_id, constraint, response_text in remaining_hard:
            result = score_hard(sample_id, constraint, response_text)
            f.write(json.dumps(result, ensure_ascii=False) + "\n")

    # 统计
    with open(hard_output) as f:
        hard_results = [json.loads(line) for line in f]
    hard_pass = sum(1 for r in hard_results if r["passed"])
    print(f"  Hard: {hard_pass}/{len(hard_results)} passed ({hard_pass/len(hard_results)*100:.1f}%)")

    # --- Soft 评分（LLM judge，并发）---
    print(f"\n=== Soft Scoring (judge={args.judge_model}, concurrency={args.concurrency}) ===")
    done_soft = set()
    if soft_output.exists():
        with open(soft_output) as f:
            for line in f:
                r = json.loads(line)
                done_soft.add(f"{r['sample_id']}_{r['constraint_id']}")
    remaining_soft = [(s, c, q, r) for s, c, q, r in soft_tasks if f"{s}_{c['constraint_id']}" not in done_soft]
    print(f"  Total: {len(soft_tasks)}, Done: {len(done_soft)}, Remaining: {len(remaining_soft)}")

    if remaining_soft and args.concurrency > 0:
        completed = 0
        with open(soft_output, "a", encoding="utf-8") as f_out:
            with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = {
                    executor.submit(score_soft, s, c, q, r, args.judge_model): (s, c["constraint_id"])
                    for s, c, q, r in remaining_soft
                }
                for future in as_completed(futures):
                    sample_id, cid = futures[future]
                    try:
                        result = future.result()
                        f_out.write(json.dumps(result, ensure_ascii=False) + "\n")
                        f_out.flush()
                        completed += 1
                        if completed % 10 == 0:
                            print(f"  Progress: {completed}/{len(remaining_soft)}")
                    except Exception as e:
                        print(f"  Error {sample_id}/{cid}: {e}")

    # 最终统计
    with open(soft_output) as f:
        soft_results = [json.loads(line) for line in f]
    soft_pass = sum(1 for r in soft_results if r["passed"])
    print(f"  Soft: {soft_pass}/{len(soft_results)} passed ({soft_pass/len(soft_results)*100:.1f}%)")

    # 总体
    all_results = hard_results + soft_results
    total_pass = sum(1 for r in all_results if r["passed"])
    print(f"\n=== Overall ===")
    print(f"  Constraint-level: {total_pass}/{len(all_results)} ({total_pass/len(all_results)*100:.1f}%)")

    # Instruction-level (strict): 一条 track 所有约束都 pass 才算 pass
    from collections import defaultdict
    by_sample = defaultdict(list)
    for r in all_results:
        by_sample[r["sample_id"]].append(r["passed"])
    inst_pass = sum(1 for v in by_sample.values() if all(v))
    print(f"  Instruction-level: {inst_pass}/{len(by_sample)} ({inst_pass/len(by_sample)*100:.1f}%)")


if __name__ == "__main__":
    main()
