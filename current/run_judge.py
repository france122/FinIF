#!/usr/bin/env python3
"""
批量运行 LLM Judge 评估 pending soft constraints。
用法: python run_judge.py
输入: pending_judge_tasks.jsonl (279条任务)
输出: judge_results.jsonl (279条结果)
"""
import json, os, re, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

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


def parse_judge_response(text):
    text = text.strip()
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
        return {"pass": None, "reason": f"parse failed: {text[:100]}"}


def judge_one(task):
    prompt = JUDGE_USER_PROMPT.format(
        description=task["description"],
        rubric=task["rubric"],
        context=task["context"] or "(无)",
        output=task["output"],
    )
    try:
        text = get_gpt_response(
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model_version=JUDGE_MODEL,
            temperature=0,
            max_tokens=256,
            max_try=3,
        )
        if text is None:
            return {
                "task_id": task["task_id"],
                "constraint_id": task["constraint_id"],
                "model": task["model"],
                "type": "soft",
                "pass": None,
                "reason": "API returned None",
            }
        result = parse_judge_response(text)
        result["task_id"] = task["task_id"]
        result["constraint_id"] = task["constraint_id"]
        result["model"] = task["model"]
        result["type"] = "soft"
        return result
    except Exception as e:
        return {
            "task_id": task["task_id"],
            "constraint_id": task["constraint_id"],
            "model": task["model"],
            "type": "soft",
            "pass": None,
            "reason": f"API error: {e}",
        }


def main():
    input_file = os.path.join(os.path.dirname(__file__), "pending_judge_tasks.jsonl")
    output_file = os.path.join(os.path.dirname(__file__), "judge_results.jsonl")

    with open(input_file) as f:
        tasks = [json.loads(line) for line in f if line.strip()]
    print(f"Loaded {len(tasks)} tasks")

    # Skip already completed
    done_ids = set()
    if os.path.exists(output_file):
        with open(output_file) as f:
            for line in f:
                if line.strip():
                    done_ids.add(json.loads(line)["task_id"])
        print(f"Already completed: {len(done_ids)}, remaining: {len(tasks) - len(done_ids)}")
    tasks = [t for t in tasks if t["task_id"] not in done_ids]

    if not tasks:
        print("All tasks done!")
        return

    completed = 0
    with open(output_file, "a") as out_f:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(judge_one, t): t for t in tasks}
            for future in as_completed(futures):
                result = future.result()
                out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
                out_f.flush()
                completed += 1
                status = "PASS" if result.get("pass") else "FAIL" if result.get("pass") is False else "ERR"
                print(f"[{completed}/{len(tasks)}] {result['task_id']} → {status}")

    print(f"\nDone! Results saved to {output_file}")


if __name__ == "__main__":
    main()
