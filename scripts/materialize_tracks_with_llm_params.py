import argparse
import copy
import json
import re
from collections import Counter
from pathlib import Path

from build_id_heldout_tracks import build_viewer
from constraint_parameterization import render_parametric_constraint, validate_and_normalize_params


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
TRACKS_PATH = DATA_DIR / "tracks" / "id_heldout_all_tracks.json"
PARAMS_PATH = DATA_DIR / "tracks" / "llm_constraint_parameters.json"
OUTPUT_DIR = DATA_DIR / "tracks"
VIEWER_PATH = BASE_DIR / "viewer" / "id_heldout_tracks_viewer_filled.html"

TRACK_OUTPUTS = {
    "V-track": OUTPUT_DIR / "id_heldout_v_track_filled.json",
    "NV-track": OUTPUT_DIR / "id_heldout_nv_track_filled.json",
    "Mixed-track": OUTPUT_DIR / "id_heldout_mixed_track_filled.json",
}
ALL_OUTPUT_PATH = OUTPUT_DIR / "id_heldout_all_tracks_filled.json"
MANIFEST_PATH = OUTPUT_DIR / "llm_parameterization_manifest.json"
QUALITY_SUMMARY_PATH = OUTPUT_DIR / "quality_review_summary.json"

DIALOG_QUERY_PATTERNS = [
    r"根据上述对话",
    r"在这次对话中",
    r"用户首先提出了哪个",
    r"讨论的第一个主要挑战",
    r"讨论的第一个主要问题",
    r"对话中提到了哪种方法",
]
GENERIC_FIRST_WORDS = {"结论", "建议", "步骤", "方案", "说明", "策略"}
COMMON_PREFIXES = {"建议：", "要点：", "步骤：", "说明：", "提示：", "发现：", "风险点：", "亮点："}
CATALOG_DOC_STYLES = {"券商研报", "投资备忘录", "监管公告", "客户说明书", "投资顾问信"}
PENALTIES = {"high": 35, "medium": 12, "low": 6}


def parse_args():
    parser = argparse.ArgumentParser(description="Materialize placeholder tracks with LLM-filled constraint parameters.")
    parser.add_argument("--tracks", type=Path, default=TRACKS_PATH, help="Placeholder track file path.")
    parser.add_argument("--params", type=Path, default=PARAMS_PATH, help="LLM-filled parameter json path.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Directory to write filled track files.")
    parser.add_argument("--viewer-path", type=Path, default=VIEWER_PATH, help="Filled viewer output path.")
    parser.add_argument(
        "--strict-extra-records",
        action="store_true",
        help="Fail if the parameter file contains records not used by the input tracks.",
    )
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_param_record_index(payload: dict):
    index = {"by_sample": {}, "by_query_track": {}}
    for record in payload.get("records", []):
        sample_key = (record["sample_id"], record["constraint_id"])
        query_key = (record["query_id"], record["track"], record["constraint_id"])
        index["by_sample"][sample_key] = record
        index["by_query_track"][query_key] = record
    return index


def rebuild_sample_prompt(sample: dict, constraints: list[dict]) -> str:
    lines = [f"{idx}. {constraint['text']}" for idx, constraint in enumerate(constraints, start=1)]
    return sample["query_input"].rstrip() + "\n\n附加要求：\n" + "\n".join(lines)


def has_unbalanced_quotes(text: str) -> bool:
    return text.count("“") != text.count("”") or text.count("‘") != text.count("’")


def add_flag(review: dict, flag_type: str, severity: str, detail: str) -> None:
    review.setdefault("flags", []).append({"type": flag_type, "severity": severity, "detail": detail})


def finalize_quality_review(review: dict) -> dict:
    flags = review.get("flags", [])
    score = max(0, 100 - sum(PENALTIES[flag["severity"]] for flag in flags))
    if any(flag["severity"] == "high" for flag in flags) or score < 70:
        risk_level = "high"
    elif flags:
        risk_level = "medium"
    else:
        risk_level = "low"
    review["score"] = score
    review["risk_level"] = risk_level
    review["flag_count"] = len(flags)
    review["flag_types"] = [flag["type"] for flag in flags]
    return review


def build_quality_review(sample: dict) -> dict:
    review = {"flags": []}
    query_text = sample.get("query_input", "")

    if any(re.search(pattern, query_text) for pattern in DIALOG_QUERY_PATTERNS):
        add_flag(review, "query_meta_reference", "high", "query 像对话复述/元问题，不是纯开放式金融任务。")

    for constraint in sample.get("constraints", []):
        params = constraint.get("filled_params") or {}
        if constraint["id"] == "GV-10" and params.get("word") in GENERIC_FIRST_WORDS:
            add_flag(review, "generic_start_word", "medium", f'GV-10 首词较泛：{params.get("word")}')
        if constraint["id"] == "GV-14" and params.get("prefix") in COMMON_PREFIXES:
            add_flag(review, "common_bullet_prefix", "low", f'GV-14 前缀较常规：{params.get("prefix")}')
        if constraint["id"] == "GV-13":
            first_line = params.get("first_line", "")
            last_line = params.get("last_line", "")
            if any(token in first_line for token in ["结论", "建议", "方案", "分析", "观点", "摘要"]):
                add_flag(review, "template_like_title", "medium", f"GV-13 首行偏模板化：{first_line}")
            if "仅供参考" in last_line or "不构成投资建议" in last_line:
                add_flag(review, "disclaimer_tail", "low", f"GV-13 尾行偏常规免责声明：{last_line}")
        if constraint["id"] == "FV-5":
            currency_rule = params.get("currency_rule", "")
            if len(currency_rule) > 40:
                add_flag(review, "verbose_currency_rule", "medium", f"FV-5 金额格式规则偏长：{currency_rule}")
            if has_unbalanced_quotes(currency_rule):
                add_flag(review, "unbalanced_quote", "high", f"FV-5 金额格式规则存在不成对引号：{currency_rule}")
        if constraint["id"] == "FN-16" and params.get("doc_style") in CATALOG_DOC_STYLES:
            add_flag(review, "catalog_doc_style", "low", f'FN-16 文体落回较通用类别：{params.get("doc_style")}')

    return finalize_quality_review(review)


def build_quality_summary(samples: list[dict]) -> dict:
    scores = [sample["quality_review"]["score"] for sample in samples]
    risk_counts = Counter(sample["quality_review"]["risk_level"] for sample in samples)
    flag_type_counts = Counter()
    for sample in samples:
        flag_type_counts.update(sample["quality_review"]["flag_types"])

    return {
        "total_samples": len(samples),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "risk_level_counts": dict(risk_counts),
        "flag_type_counts": dict(flag_type_counts),
        "score_bands": {
            "90-100": sum(1 for score in scores if score >= 90),
            "70-89": sum(1 for score in scores if 70 <= score < 90),
            "0-69": sum(1 for score in scores if score < 70),
        },
    }


def annotate_global_quality_flags(samples: list[dict]) -> list[dict]:
    prompt_counts = Counter((sample["split"], sample["track"], sample["prompt"]) for sample in samples)

    for sample in samples:
        review = sample["quality_review"]
        query_text = sample.get("query_input", "")

        if prompt_counts[(sample["split"], sample["track"], sample["prompt"])] > 1:
            add_flag(review, "duplicate_prompt_in_split_track", "low", "同一 split + track 内存在重复 prompt。")

        for constraint in sample.get("constraints", []):
            params = constraint.get("filled_params") or {}
            if constraint["id"] == "GV-8":
                overlaps = [kw for kw in [params.get("kw1"), params.get("kw2")] if kw and kw in query_text]
                if overlaps:
                    add_flag(review, "gv8_keyword_overlap", "medium", f'GV-8 关键词直接出现在 query 中：{", ".join(overlaps)}')
            if constraint["id"] == "GV-9":
                forbidden_word = params.get("word")
                if forbidden_word and forbidden_word in query_text:
                    add_flag(review, "gv9_forbidden_overlap", "medium", f"GV-9 禁词直接出现在 query 中：{forbidden_word}")

        sample["quality_review"] = finalize_quality_review(review)

    return samples


def materialize_samples(samples, param_records):
    filled_samples = []
    used_keys = set()

    for sample in samples:
        updated = copy.deepcopy(sample)
        updated_constraints = []

        for constraint in updated.get("constraints", []):
            new_constraint = copy.deepcopy(constraint)
            if new_constraint.get("is_parametric"):
                sample_key = (updated["sample_id"], new_constraint["id"])
                query_key = (updated["query_id"], updated["track"], new_constraint["id"])
                record = param_records["by_sample"].get(sample_key) or param_records["by_query_track"].get(query_key)
                if record is None:
                    raise ValueError(f"缺少参数记录: sample_id={updated['sample_id']} constraint_id={new_constraint['id']}")

                params = validate_and_normalize_params(new_constraint["id"], record["params"])
                rendered_text = render_parametric_constraint(new_constraint["id"], params)

                new_constraint["text"] = rendered_text
                new_constraint["rendered_text"] = rendered_text
                new_constraint["filled_params"] = params
                new_constraint["parameter_source"] = "llm"
                new_constraint["parameter_model"] = record.get("model")
                new_constraint["parameter_attempts"] = record.get("attempts")
                used_keys.add(sample_key)

            updated_constraints.append(new_constraint)

        updated["constraints"] = updated_constraints
        updated["prompt"] = rebuild_sample_prompt(updated, updated_constraints)
        updated["materialization_status"] = "llm_filled"
        updated["quality_review"] = build_quality_review(updated)
        filled_samples.append(updated)

    filled_samples = annotate_global_quality_flags(filled_samples)
    return filled_samples, used_keys


def group_by_track(samples):
    groups = {"V-track": [], "NV-track": [], "Mixed-track": []}
    for sample in samples:
        groups[sample["track"]].append(sample)
    return groups


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    args = parse_args()
    samples = load_json(args.tracks)
    params_payload = load_json(args.params)
    param_records = build_param_record_index(params_payload)

    filled_samples, used_keys = materialize_samples(samples, param_records)
    unused_keys = set(param_records["by_sample"]) - used_keys
    if unused_keys and args.strict_extra_records:
        first_unused = sorted(unused_keys)[0]
        raise ValueError(f"参数文件中存在未使用记录: sample_id={first_unused[0]} constraint_id={first_unused[1]}")

    track_groups = group_by_track(filled_samples)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    track_outputs = {
        "V-track": output_dir / "id_heldout_v_track_filled.json",
        "NV-track": output_dir / "id_heldout_nv_track_filled.json",
        "Mixed-track": output_dir / "id_heldout_mixed_track_filled.json",
    }
    all_output_path = output_dir / "id_heldout_all_tracks_filled.json"
    manifest_path = output_dir / "llm_parameterization_manifest.json"
    quality_summary_path = output_dir / "quality_review_summary.json"
    quality_summary = build_quality_summary(filled_samples)

    for track_name, track_path in track_outputs.items():
        write_json(track_path, track_groups[track_name])
    write_json(all_output_path, filled_samples)
    write_json(quality_summary_path, quality_summary)
    args.viewer_path.parent.mkdir(parents=True, exist_ok=True)
    args.viewer_path.write_text(build_viewer(filled_samples), encoding="utf-8")

    manifest = {
        "tracks_path": str(args.tracks),
        "params_path": str(args.params),
        "output_files": {
            "all": str(all_output_path),
            "viewer": str(args.viewer_path),
            "V-track": str(track_outputs["V-track"]),
            "NV-track": str(track_outputs["NV-track"]),
            "Mixed-track": str(track_outputs["Mixed-track"]),
        },
        "total_samples": len(filled_samples),
        "param_records_total": len(param_records["by_sample"]),
        "param_records_used": len(used_keys),
        "param_records_unused": len(unused_keys),
        "track_counts": {track: len(items) for track, items in track_groups.items()},
        "parameter_meta": params_payload.get("meta", {}),
        "quality_summary_path": str(quality_summary_path),
        "quality_summary": quality_summary,
    }
    write_json(manifest_path, manifest)

    print("filled samples", len(filled_samples))
    print("param records used", len(used_keys))
    print("param records unused", len(unused_keys))
    print("all output", all_output_path)
    print("viewer output", args.viewer_path)
    print("quality summary", quality_summary_path)
    print("manifest output", manifest_path)


if __name__ == "__main__":
    main()
