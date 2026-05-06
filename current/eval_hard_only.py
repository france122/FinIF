"""Standalone hard-only evaluation — no LLM API needed."""

import json
import os
import sys

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DEMO_DIR)

import checkers


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


def main():
    config_path = os.path.join(DEMO_DIR, "eval_config_all.json")
    with open(config_path, encoding="utf-8") as f:
        all_constraints = json.load(f)["constraints"]

    hard_constraints = {k: v for k, v in all_constraints.items() if v["type"] == "hard"}
    print(f"Hard constraints: {len(hard_constraints)}")

    input_dir = os.path.join(DEMO_DIR, "output")
    response_files = sorted([
        f for f in os.listdir(input_dir)
        if f.startswith("responses_") and f.endswith(".jsonl")
    ])

    model_results = {}

    for resp_file in response_files:
        model_name = resp_file.replace("responses_", "").replace(".jsonl", "")
        responses = {}
        with open(os.path.join(input_dir, resp_file), encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    responses[obj["case_id"]] = obj

        results = {}
        for cid, config in hard_constraints.items():
            case_id = cid.split("#")[0]
            if case_id not in responses:
                continue
            output = responses[case_id]["response"]
            results[cid] = run_hard_check(config, output)

        model_results[model_name] = results

    models = sorted(model_results.keys())

    all_pass_count = 0
    all_fail_count = 0
    discriminating_count = 0

    from collections import Counter
    all_pass_by_checker = Counter()
    all_fail_by_checker = Counter()
    disc_by_checker = Counter()

    for cid in hard_constraints:
        vals = [model_results[m].get(cid, {}).get("pass") for m in models]
        if all(v is True for v in vals):
            all_pass_count += 1
            all_pass_by_checker[hard_constraints[cid]["checker"]] += 1
        elif all(v is False for v in vals):
            all_fail_count += 1
            all_fail_by_checker[hard_constraints[cid]["checker"]] += 1
        else:
            discriminating_count += 1
            disc_by_checker[hard_constraints[cid]["checker"]] += 1

    print(f"\n{'='*70}")
    print(f"ALL PASS (zero discrimination): {all_pass_count}/{len(hard_constraints)}")
    for checker, cnt in all_pass_by_checker.most_common():
        print(f"  {checker}: {cnt}")

    print(f"\nALL FAIL: {all_fail_count}/{len(hard_constraints)}")
    for checker, cnt in all_fail_by_checker.most_common():
        print(f"  {checker}: {cnt}")
    for cid in hard_constraints:
        vals = [model_results[m].get(cid, {}).get("pass") for m in models]
        if all(v is False for v in vals):
            print(f"  → {cid} ({hard_constraints[cid]['checker']})")

    print(f"\nDISCRIMINATING: {discriminating_count}/{len(hard_constraints)}")
    for checker, cnt in disc_by_checker.most_common():
        print(f"  {checker}: {cnt}")

    print(f"\n{'='*70}")
    print(f"Per-model hard pass rates:")
    print(f"{'Model':<30s} {'Pass':>6s} {'Total':>6s} {'Rate':>8s}")
    print("-" * 52)
    for m in models:
        total = len([v for v in model_results[m].values()])
        passed = sum(1 for v in model_results[m].values() if v.get("pass") is True)
        print(f"{m:<30s} {passed:>6d} {total:>6d} {passed/total:>7.1%}")

    per_checker_stats = {}
    for cid, config in hard_constraints.items():
        checker = config["checker"]
        if checker not in per_checker_stats:
            per_checker_stats[checker] = {m: {"pass": 0, "total": 0} for m in models}
        for m in models:
            r = model_results[m].get(cid, {})
            per_checker_stats[checker][m]["total"] += 1
            if r.get("pass") is True:
                per_checker_stats[checker][m]["pass"] += 1

    print(f"\n{'='*70}")
    print("Per-checker pass rates:")
    header = f"{'Checker':<28s} {'Count':>5s}"
    for m in models:
        short = m.split("-")[0] if "-" in m else m[:8]
        header += f" {short:>10s}"
    header += f" {'Spread':>8s}"
    print(header)
    print("-" * len(header))

    for checker in sorted(per_checker_stats.keys(), key=lambda x: -sum(v["total"] for v in per_checker_stats[x].values()) // len(models)):
        stats = per_checker_stats[checker]
        count = list(stats.values())[0]["total"]
        rates = []
        row = f"{checker:<28s} {count:>5d}"
        for m in models:
            s = stats[m]
            rate = s["pass"] / s["total"] if s["total"] > 0 else 0
            rates.append(rate)
            row += f" {rate:>9.1%}"
        spread = max(rates) - min(rates)
        row += f" {spread:>7.1%}"
        print(row)


if __name__ == "__main__":
    main()
