#!/usr/bin/env python3
"""
生成 Vulcan Track 生成任务的输入 JSONL。

502 queries × 3 批次（hard/soft/mixed）= 1,506 行
每批生成 4 条 track，总计 502 × 12 = 6,024 条 track。

3 批次:
  hard:  SP=track_gen_sp_hard.md   → hard_1a, hard_1b, hard_2, hard_3
  soft:  SP=track_gen_sp_soft.md   → soft_1a, soft_1b, soft_2, soft_3
  mixed: SP=track_gen_sp_mixed.md  → mixed_1h1s_a, mixed_1h1s_b, mixed_1h2s, mixed_2h1s

用法:
  python scripts/gen_track_vulcan_input.py \
    --query-pool data/query_pool/query_pool_v3.json \
    --prompt-dir prompts \
    --output data/tracks/vulcan_track_gen_input.jsonl
"""
import argparse, json
from pathlib import Path

BATCHES = [
    ("hard",  "track_gen_sp_hard.md"),
    ("soft",  "track_gen_sp_soft.md"),
    ("mixed", "track_gen_sp_mixed.md"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-pool", required=True)
    parser.add_argument("--prompt-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.query_pool) as f:
        queries = json.load(f)

    prompt_dir = Path(args.prompt_dir)
    user_template = (prompt_dir / "track_gen_user_template.md").read_text(encoding="utf-8")

    rows = []
    for batch_name, sp_file in BATCHES:
        system_prompt = (prompt_dir / sp_file).read_text(encoding="utf-8")

        for q in queries:
            qid = q.get("query_id", q.get("id", ""))
            query_text = q.get("input", q.get("query_text", ""))

            user_content = user_template.format(
                query_id=qid,
                query_text=query_text,
            )

            row = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "query_id": qid,
                "batch": batch_name,
            }
            rows.append(row)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Generated {len(rows)} rows ({len(queries)} queries × {len(BATCHES)} batches)")
    print(f"  hard:  {len(queries)} rows → {len(queries)*4} tracks")
    print(f"  soft:  {len(queries)} rows → {len(queries)*4} tracks")
    print(f"  mixed: {len(queries)} rows → {len(queries)*4} tracks")
    print(f"  total: {len(queries)*12} tracks")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
