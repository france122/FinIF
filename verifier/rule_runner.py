from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from verifier.base import CheckResult
from verifier.registry import get_constraint_meta, get_rule_path


def _load_rule_module(constraint_id: str):
    rule_path = get_rule_path(constraint_id)
    if not rule_path.exists():
        raise FileNotFoundError(f"缺少 rule checker: {rule_path}")
    spec = importlib.util.spec_from_file_location(f"rule_{constraint_id}", rule_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 rule checker: {rule_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_rule_check(
    constraint_id: str,
    response_text: str,
    params: dict | None = None,
    context: dict | None = None,
) -> CheckResult:
    meta = get_constraint_meta(constraint_id)
    if meta["check_mode"] != "rule":
        raise ValueError(f"{constraint_id} 不是 rule 类型约束")
    module = _load_rule_module(constraint_id)
    result = module.check(
        response_text=response_text,
        params=params or {},
        context=context or {},
        meta=meta,
    )
    if not isinstance(result, CheckResult):
        raise TypeError(f"{constraint_id} checker 未返回 CheckResult")
    return result


def _parse_args():
    parser = argparse.ArgumentParser(description="Run a rule-based checker.")
    parser.add_argument("--constraint-id", required=True)
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--response-text")
    parser.add_argument("--params-json", default="{}")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    response_text = args.response_text
    if args.response_file:
        response_text = args.response_file.read_text(encoding="utf-8")
    if response_text is None:
        raise SystemExit("需要提供 --response-file 或 --response-text")
    result = run_rule_check(
        constraint_id=args.constraint_id,
        response_text=response_text,
        params=json.loads(args.params_json),
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
