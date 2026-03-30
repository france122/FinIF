from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from verifier.registry import get_constraint_meta, get_rubric_path


JUDGE_SYSTEM_PROMPT = """你是一个严格的约束遵循评测器。

你的任务是判断候选回答是否满足指定约束，并输出严格 JSON。

输出要求：
1. 只能输出一个 JSON 对象
2. `score` 必须严格遵守给定的 `score_type`
3. `passed` 要与评分大体一致：高分通常为 true，低分通常为 false，中间分可按总体判断决定
4. `reason` 要简短，聚焦是否满足约束
5. `evidence` 要摘录回答中的关键证据，不要编造
"""


def build_score_type_instructions(score_type: str) -> str:
    if score_type == "binary_10":
        return """- score_type: binary_10
- 只允许打 `0` 或 `10`
- `10` 表示满足，`0` 表示不满足"""
    if score_type == "ternary_10":
        return """- score_type: ternary_10
- 只允许打 `0`、`5` 或 `10`
- `10` 表示明显满足，`5` 表示部分满足/边界满足，`0` 表示不满足"""
    if score_type == "continuous_10":
        return """- score_type: continuous_10
- 允许打 `0-10` 之间的连续分数
- 请把 rubric 中给出的 `10/5/0` 视为 anchor，再据此细化评分"""
    raise ValueError(f"未知 score_type: {score_type}")


def build_judge_prompt(
    constraint_id: str,
    query_text: str,
    response_text: str,
    *,
    rendered_constraint_text: str | None = None,
    extra_context: str | None = None,
) -> dict[str, str]:
    meta = get_constraint_meta(constraint_id)
    if meta["check_mode"] != "rubric":
        raise ValueError(f"{constraint_id} 不是 rubric 类型约束")
    rubric_path = get_rubric_path(constraint_id)
    rubric_text = rubric_path.read_text(encoding="utf-8")
    constraint_text = rendered_constraint_text or meta["constraint_text"]
    score_type = meta["score_type"]
    score_instructions = build_score_type_instructions(score_type)
    user_prompt = f"""## Constraint Meta

- constraint_id: {constraint_id}
- verifiability: {meta['verifiability']}
- check_mode: {meta['check_mode']}
- score_type: {score_type}
- constraint_text: {constraint_text}
- description: {meta['description']}
- source: {meta['source']}

## Scoring Rules

{score_instructions}

## Rubric

{rubric_text}

## Query

{query_text}

## Candidate Answer

{response_text}
"""
    if extra_context:
        user_prompt += f"\n## Extra Context\n\n{extra_context}\n"
    user_prompt += """
## Output JSON Schema

{
  "constraint_id": "...",
  "score": 0,
  "passed": false,
  "reason": "...",
  "evidence": ["..."]
}
"""
    return {
        "system": JUDGE_SYSTEM_PROMPT,
        "user": user_prompt,
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Build an LLM judge prompt from a rubric.")
    parser.add_argument("--constraint-id", required=True)
    parser.add_argument("--query-file", type=Path)
    parser.add_argument("--query-text")
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--response-text")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    query_text = args.query_text
    response_text = args.response_text
    if args.query_file:
        query_text = args.query_file.read_text(encoding="utf-8")
    if args.response_file:
        response_text = args.response_file.read_text(encoding="utf-8")
    if query_text is None or response_text is None:
        raise SystemExit("需要提供 query 和 response 的文本或文件")
    prompt = build_judge_prompt(args.constraint_id, query_text=query_text, response_text=response_text)
    print(json.dumps(prompt, ensure_ascii=False, indent=2))
