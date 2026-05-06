#!/usr/bin/env python3
"""
FinIF Benchmark — 多模型评测打分
对生成的回复运行 hard check (code checker) + soft check (LLM judge)，输出分数。
"""

import json
import os
import sys
import re
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(DEMO_DIR, "..", "..", "..", "..", ".."))
sys.path.insert(0, DEMO_DIR)
sys.path.insert(0, PROJECT_ROOT)

import checkers
from gpt_call_all import get_gpt_response

JUDGE_MODEL = "gpt-4o-2024-11-20"

JUDGE_SYSTEM_PROMPT = """你是一个金融文档评测专家。你的任务是严格判断模型输出是否满足给定的约束条件。

判断规则：
1. 仔细阅读约束描述（constraint）和评判标准（rubric）
2. 对照模型输出（output）和原始上下文（context，如有提供）
3. 给出 pass 或 fail 的二值判断

严格判定标准——出现以下任一情况必须判 fail：
- 约束要求特定数值，但输出中的数值与要求不符或计算错误
- 约束要求分析/推导过程，但输出仅罗列数据而未展示推导步骤
- 约束要求引用原文数据，但输出中出现原文中不存在的数值（编造数据）
- 约束要求对比分析，但输出仅提及单方面数据而未进行对比
- 输出仅"提到"了相关概念但未给出具体证据或数值支撑

请以JSON格式输出：
{"pass": true/false, "reason": "判断理由（一句话）"}"""

JUDGE_USER_PROMPT = """## 约束描述
{description}

## 评判标准
{rubric}

## 原始上下文
{context}

## 模型输出
{output}

请判断模型输出是否满足上述约束。以JSON格式输出：{{"pass": true/false, "reason": "..."}}"""


def parse_judge_response(response):
    text = response.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()
    try:
        obj = json.loads(text)
        return {"pass": bool(obj.get("pass", False)), "reason": obj.get("reason", "")}
    except (json.JSONDecodeError, ValueError):
        pass_match = re.search(r'"pass"\s*:\s*(true|false)', text, re.IGNORECASE)
        if pass_match:
            passed = pass_match.group(1).lower() == "true"
            reason_match = re.search(r'"reason"\s*:\s*"([^"]*)"', text)
            reason = reason_match.group(1) if reason_match else ""
            return {"pass": passed, "reason": reason}
        return {"pass": None, "reason": "failed to parse judge response", "raw": text[:200]}


def run_hard_check(config, output):
    fn_name = config["checker"]
    params = config.get("params", None)
    fn = getattr(checkers, fn_name, None)
    if fn is None:
        return {"pass": False, "type": "hard", "error": f"checker '{fn_name}' not found"}
    try:
        passed = fn(output, params)
        return {"pass": bool(passed), "type": "hard", "checker": fn_name}
    except Exception as e:
        return {"pass": False, "type": "hard", "error": str(e)}


def run_soft_check(config, output, context=""):
    rubric = config.get("rubric", "")
    description = config.get("description", "")
    prompt = JUDGE_USER_PROMPT.format(
        description=description,
        rubric=rubric,
        context=context[:3000] if context else "(无)",
        output=output[:3000],
    )
    try:
        response = get_gpt_response(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model_version=JUDGE_MODEL,
            temperature=0,
            max_tokens=256,
            max_try=3,
        )
        if response is None:
            return {"pass": None, "type": "soft", "error": "judge returned None"}
        result = parse_judge_response(response)
        result["type"] = "soft"
        return result
    except Exception as e:
        return {"pass": None, "type": "soft", "error": str(e)}


def evaluate_one_case(case_id, output, context, constraints_config, hard_only=False):
    results = {}
    for key, config in constraints_config.items():
        if not key.startswith(case_id + "#"):
            continue
        if config["type"] == "hard":
            results[key] = run_hard_check(config, output)
        elif not hard_only:
            results[key] = run_soft_check(config, output, context)
        else:
            results[key] = {"pass": None, "type": "soft", "reason": "skipped (hard-only)"}
    return results


def compute_scores(all_results):
    scores = {}
    for case_id, constraints in all_results.items():
        total = len(constraints)
        passed = sum(1 for v in constraints.values() if v.get("pass") is True)
        hard_total = sum(1 for v in constraints.values() if v["type"] == "hard")
        hard_passed = sum(1 for v in constraints.values() if v["type"] == "hard" and v.get("pass") is True)
        soft_total = sum(1 for v in constraints.values() if v["type"] == "soft")
        soft_passed = sum(1 for v in constraints.values() if v["type"] == "soft" and v.get("pass") is True)
        scores[case_id] = {
            "total": total, "passed": passed,
            "score": passed / total if total > 0 else 0,
            "hard": {"total": hard_total, "passed": hard_passed},
            "soft": {"total": soft_total, "passed": soft_passed},
        }
    return scores


def tier_scores(scores):
    tiers = {"T1": [], "T2": [], "T3": []}
    for case_id, s in scores.items():
        tier = case_id.split(".")[0]
        if tier in tiers:
            tiers[tier].append(s["score"])
    result = {}
    for tier, vals in tiers.items():
        if vals:
            result[tier] = sum(vals) / len(vals)
        else:
            result[tier] = 0
    all_vals = [s["score"] for s in scores.values()]
    result["overall"] = sum(all_vals) / len(all_vals) if all_vals else 0
    return result


def eval_model(response_file, constraints_config, output_file, hard_only=False):
    responses = {}
    with open(response_file, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            responses[obj["case_id"]] = obj

    print(f"  Loaded {len(responses)} responses")

    all_results = {}
    for i, (case_id, item) in enumerate(sorted(responses.items())):
        output = item["response"]
        context = item.get("context", "")
        results = evaluate_one_case(case_id, output, context, constraints_config, hard_only)
        all_results[case_id] = results

        h_pass = sum(1 for v in results.values() if v["type"] == "hard" and v.get("pass") is True)
        h_total = sum(1 for v in results.values() if v["type"] == "hard")
        s_pass = sum(1 for v in results.values() if v["type"] == "soft" and v.get("pass") is True)
        s_total = sum(1 for v in results.values() if v["type"] == "soft")
        print(f"  [{i+1}/{len(responses)}] {case_id}: hard={h_pass}/{h_total} soft={s_pass}/{s_total}")

    scores = compute_scores(all_results)
    tiers = tier_scores(scores)

    output_data = {
        "model": item.get("model", ""),
        "results": all_results,
        "scores": scores,
        "tier_scores": tiers,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {output_file}")
    return tiers


def main():
    parser = argparse.ArgumentParser(description="FinIF Benchmark multi-model evaluation")
    parser.add_argument("--input-dir", default=os.path.join(DEMO_DIR, "output"), help="Directory with response files")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: same as input)")
    parser.add_argument("--config", default=os.path.join(DEMO_DIR, "eval_config_all.json"))
    parser.add_argument("--hard-only", action="store_true", help="Skip LLM judge, only run hard checks")
    parser.add_argument("--models", nargs="*", default=None, help="Specific model files to eval")
    args = parser.parse_args()

    output_dir = args.output_dir or args.input_dir
    os.makedirs(output_dir, exist_ok=True)

    with open(args.config, encoding="utf-8") as f:
        eval_config = json.load(f)["constraints"]

    if args.models:
        response_files = []
        for m in args.models:
            path = os.path.join(args.input_dir, f"responses_{m}.jsonl")
            if os.path.isfile(path):
                response_files.append(path)
            elif os.path.isfile(m):
                response_files.append(m)
            else:
                print(f"Warning: {path} not found")
    else:
        response_files = sorted([
            os.path.join(args.input_dir, f)
            for f in os.listdir(args.input_dir)
            if f.startswith("responses_") and f.endswith(".jsonl")
        ])

    if not response_files:
        print("No response files found!")
        return

    print(f"Found {len(response_files)} response files")
    print(f"Eval config: {len(eval_config)} constraints")
    if args.hard_only:
        print("Mode: hard-only (skipping LLM judge)")
    else:
        print(f"Judge model: {JUDGE_MODEL}")

    summary = {}
    for resp_file in response_files:
        basename = os.path.basename(resp_file)
        model_name = basename.replace("responses_", "").replace(".jsonl", "")
        score_file = os.path.join(output_dir, f"scores_{model_name}.json")

        print(f"\n{'='*60}")
        print(f"Evaluating: {model_name}")
        tiers = eval_model(resp_file, eval_config, score_file, args.hard_only)
        summary[model_name] = tiers

    print(f"\n{'='*80}")
    print(f"{'Model':<30s} {'T1':>8s} {'T2':>8s} {'T3':>8s} {'Overall':>8s}")
    print("-" * 80)
    for model_name, tiers in sorted(summary.items()):
        print(f"{model_name:<30s} {tiers.get('T1',0):>7.1%} {tiers.get('T2',0):>7.1%} {tiers.get('T3',0):>7.1%} {tiers.get('overall',0):>7.1%}")


if __name__ == "__main__":
    main()
