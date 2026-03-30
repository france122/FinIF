import argparse
import json
from pathlib import Path

from constraint_parameterization import PARAMETRIC_CONSTRAINT_SPECS, build_parameterization_prompt


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
TRACKS_PATH = DATA_DIR / "tracks" / "id_heldout_all_tracks.json"
OUTPUT_PATH = DATA_DIR / "tracks" / "llm_constraint_parameterization_jobs.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Build LLM parameterization prompts from placeholder tracks.")
    parser.add_argument("--tracks", type=Path, default=TRACKS_PATH, help="Input placeholder tracks json path.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output jobs json path.")
    parser.add_argument("--preview-count", type=int, default=0, help="Print the first N jobs and exit.")
    return parser.parse_args()


def load_tracks(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_jobs(samples):
    jobs = []
    for sample in samples:
        for constraint in sample.get("constraints", []):
            if not constraint.get("is_parametric"):
                continue
            constraint_id = constraint["id"]
            jobs.append(
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
                    "constraint_type": constraint["type"],
                    "constraint_template": constraint["template"],
                    "param_names": list(PARAMETRIC_CONSTRAINT_SPECS[constraint_id]["params"]),
                    "prompt": build_parameterization_prompt(sample, constraint_id),
                }
            )
    jobs.sort(key=lambda x: (x["sample_id"], x["constraint_id"]))
    return jobs


def main():
    args = parse_args()
    samples = load_tracks(args.tracks)
    jobs = build_jobs(samples)

    if args.preview_count:
        print(json.dumps(jobs[: args.preview_count], ensure_ascii=False, indent=2))
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "tracks_path": str(args.tracks),
            "job_count": len(jobs),
        },
        "jobs": jobs,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("jobs", len(jobs))
    print("output", args.output)


if __name__ == "__main__":
    main()
