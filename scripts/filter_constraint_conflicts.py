import json
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
TRACKS_DIR = BASE_DIR / "data" / "tracks"
ARCHIVE_DIR = TRACKS_DIR / "constraint_conflict_data"
CLEAN_DIR = TRACKS_DIR / "cleaned"
VIEWER_PATH = BASE_DIR / "viewer" / "id_heldout_tracks_viewer_clean.html"
TARGET_FLAG = "gv9_forbidden_overlap"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_quality_summary(samples: list[dict]) -> dict:
    scores = [sample["quality_review"]["score"] for sample in samples]
    risk_counts = Counter(sample["quality_review"]["risk_level"] for sample in samples)
    flag_counts = Counter()
    for sample in samples:
        flag_counts.update(sample["quality_review"]["flag_types"])
    return {
        "total_samples": len(samples),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "risk_level_counts": dict(risk_counts),
        "flag_type_counts": dict(flag_counts),
    }


def group_by_track(samples: list[dict]) -> dict[str, list[dict]]:
    grouped = {"V-track": [], "NV-track": [], "Mixed-track": []}
    for sample in samples:
        grouped[sample["track"]].append(sample)
    return grouped


def build_clean_viewer(all_samples):
    data_json = json.dumps(all_samples, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Clean Tracks Viewer</title>
  <style>
    :root {{
      --bg:#0b1020; --panel:#121a2b; --panel2:#18233a; --line:#283554;
      --text:#ebf1ff; --muted:#9fb0d3; --chip:#243452;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    .wrap {{ max-width:1400px; margin:0 auto; padding:24px; }}
    h1 {{ margin:0 0 8px; font-size:28px; }}
    .sub {{ color:var(--muted); line-height:1.7; margin-bottom:20px; }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:18px; }}
    .stat {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px 16px; }}
    .k {{ color:var(--muted); font-size:13px; margin-bottom:8px; }}
    .v {{ font-size:24px; font-weight:700; }}
    .toolbar {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:18px; }}
    input, select {{ width:100%; border:1px solid var(--line); border-radius:12px; padding:12px 14px; background:var(--panel); color:var(--text); font-size:14px; }}
    .hint {{ color:var(--muted); margin-bottom:18px; font-size:13px; }}
    .list {{ display:grid; gap:14px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:16px; overflow:hidden; }}
    .card-head {{ padding:16px 18px 10px; border-bottom:1px solid rgba(255,255,255,0.05); }}
    .title {{ font-size:18px; font-weight:700; margin-bottom:10px; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .chip {{ background:var(--chip); border-radius:999px; padding:5px 10px; font-size:12px; }}
    .body {{ padding:16px 18px 18px; display:grid; gap:14px; }}
    .section {{ font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px; }}
    pre {{ margin:0; white-space:pre-wrap; word-break:break-word; background:var(--panel2); border:1px solid var(--line); border-radius:12px; padding:14px; line-height:1.6; font-size:13px; }}
    .grid3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; }}
    .small {{ color:#95e0c3; font-size:13px; line-height:1.7; }}
    .empty {{ padding:32px 18px; color:var(--muted); text-align:center; background:var(--panel); border:1px solid var(--line); border-radius:16px; }}
    @media (max-width: 1180px) {{ .toolbar,.grid3 {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Clean Tracks Viewer</h1>
    <div class="sub">当前展示的是 clean 训练版 track 数据，已移除 `GV-9` 禁词与 query 题干直接冲突的样本，仅保留纯净训练集。</div>
    <div class="stats" id="stats"></div>
    <div class="toolbar">
      <input id="search" type="text" placeholder="搜索标题、query、constraint 文本" />
      <select id="split"></select>
      <select id="track"></select>
      <select id="sourceType"></select>
      <select id="originTask"></select>
      <select id="templateId"></select>
      <select id="roleMode"></select>
      <select id="parametricId"></select>
    </div>
    <div class="hint" id="hint"></div>
    <div class="list" id="list"></div>
  </div>
  <script>
    const DATA = {data_json};
    const $ = (id) => document.getElementById(id);
    const ids = ["search","split","track","sourceType","originTask","templateId","roleMode","parametricId"];
    function uniq(arr) {{
      return [...new Set(arr)].sort((a,b) => String(a).localeCompare(String(b), "zh-CN"));
    }}
    function esc(str) {{
      return String(str).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
    }}
    function fill(sel, vals, label) {{
      sel.innerHTML = `<option value="">全部${{label}}</option>` + vals.map(v => `<option value="${{esc(v)}}">${{esc(v)}}</option>`).join("");
    }}
    function renderStats() {{
      const stats = {{
        total: DATA.length,
        train: DATA.filter(x => x.split === "train").length,
        test: DATA.filter(x => x.split === "test").length,
        v: DATA.filter(x => x.track === "V-track").length,
        nv: DATA.filter(x => x.track === "NV-track").length,
        mixed: DATA.filter(x => x.track === "Mixed-track").length,
      }};
      $("stats").innerHTML = `
        <div class="stat"><div class="k">总样本数</div><div class="v">${{stats.total}}</div></div>
        <div class="stat"><div class="k">Train 样本</div><div class="v">${{stats.train}}</div></div>
        <div class="stat"><div class="k">Test 样本</div><div class="v">${{stats.test}}</div></div>
        <div class="stat"><div class="k">V-track</div><div class="v">${{stats.v}}</div></div>
        <div class="stat"><div class="k">NV-track</div><div class="v">${{stats.nv}}</div></div>
        <div class="stat"><div class="k">Mixed-track</div><div class="v">${{stats.mixed}}</div></div>
      `;
    }}
    function render() {{
      const q = $("search").value.trim().toLowerCase();
      const split = $("split").value;
      const track = $("track").value;
      const sourceType = $("sourceType").value;
      const originTask = $("originTask").value;
      const templateId = $("templateId").value;
      const roleMode = $("roleMode").value;
      const parametricId = $("parametricId").value;
      const rows = DATA.filter(item => {{
        const hay = [
          item.sample_id, item.title, item.query_input, item.prompt,
          item.track, item.split, item.source_type, item.origin_task || "",
          item.template_id || "", item.role_mode, ...(item.constraint_ids || [])
        ].join("\\n").toLowerCase();
        return (!q || hay.includes(q))
          && (!split || item.split === split)
          && (!track || item.track === track)
          && (!sourceType || item.source_type === sourceType)
          && (!originTask || item.origin_task === originTask)
          && (!templateId || item.template_id === templateId)
          && (!roleMode || item.role_mode === roleMode)
          && (!parametricId || (item.parametric_constraint_ids || []).includes(parametricId));
      }});
      $("hint").textContent = `显示 ${{rows.length}} / ${{DATA.length}} 条`;
      if (!rows.length) {{
        $("list").innerHTML = `<div class="empty">没有匹配结果，换个关键词或清空筛选试试。</div>`;
        return;
      }}
      $("list").innerHTML = rows.map(item => `
        <div class="card">
          <div class="card-head">
            <div class="title">${{esc(item.title)}}</div>
            <div class="meta">
              <span class="chip">${{esc(item.sample_id)}}</span>
              <span class="chip">${{esc(item.split)}}</span>
              <span class="chip">${{esc(item.track)}}</span>
              <span class="chip">${{esc(item.source_type)}}</span>
              ${{item.origin_task ? `<span class="chip">${{esc(item.origin_task)}}</span>` : ""}}
              ${{item.template_id ? `<span class="chip">${{esc(item.template_id)}}</span>` : ""}}
              <span class="chip">${{esc(item.role_mode)}}</span>
              <span class="chip">${{esc(item.role || "无角色")}}</span>
            </div>
          </div>
          <div class="body">
            <div class="grid3">
              <div>
                <div class="section">Constraint IDs</div>
                <div class="small">${{esc((item.constraint_ids || []).join(", "))}}</div>
              </div>
              <div>
                <div class="section">Constraint Text</div>
                <div class="small">${{esc((item.constraints || []).map(x => x.text).join(" | "))}}</div>
              </div>
              <div>
                <div class="section">Parametric IDs</div>
                <div class="small">${{esc((item.parametric_constraint_ids || []).join(", ") || "无")}}</div>
              </div>
            </div>
            <div>
              <div class="section">Query Input</div>
              <pre>${{esc(item.query_input)}}</pre>
            </div>
            <div>
              <div class="section">Final Prompt</div>
              <pre>${{esc(item.prompt)}}</pre>
            </div>
          </div>
        </div>
      `).join("");
    }}
    fill($("split"), uniq(DATA.map(x => x.split)), "split");
    fill($("track"), uniq(DATA.map(x => x.track)), "track");
    fill($("sourceType"), uniq(DATA.map(x => x.source_type)), "来源类型");
    fill($("originTask"), uniq(DATA.map(x => x.origin_task).filter(Boolean)), "FinEval来源任务");
    fill($("templateId"), uniq(DATA.map(x => x.template_id).filter(Boolean)), "模板");
    fill($("roleMode"), uniq(DATA.map(x => x.role_mode)), "角色模式");
    fill($("parametricId"), uniq(DATA.flatMap(x => x.parametric_constraint_ids || []).filter(Boolean)), "参数化约束");
    renderStats();
    render();
    ids.forEach(id => {{
      $(id).addEventListener("input", render);
      $(id).addEventListener("change", render);
    }});
  </script>
</body>
</html>
"""


def main():
    filled_all = load_json(TRACKS_DIR / "id_heldout_all_tracks_filled.json")
    placeholder_all = load_json(TRACKS_DIR / "id_heldout_all_tracks.json")
    params_payload = load_json(TRACKS_DIR / "llm_constraint_parameters.json")

    removed_ids = {
        sample["sample_id"]
        for sample in filled_all
        if TARGET_FLAG in sample.get("quality_review", {}).get("flag_types", [])
    }

    removed_filled = [sample for sample in filled_all if sample["sample_id"] in removed_ids]
    kept_filled = [sample for sample in filled_all if sample["sample_id"] not in removed_ids]
    removed_placeholder = [sample for sample in placeholder_all if sample["sample_id"] in removed_ids]
    kept_placeholder = [sample for sample in placeholder_all if sample["sample_id"] not in removed_ids]

    removed_params = [record for record in params_payload["records"] if record["sample_id"] in removed_ids]
    kept_params = [record for record in params_payload["records"] if record["sample_id"] not in removed_ids]

    removed_summary = {
        "target_flag": TARGET_FLAG,
        "removed_samples": len(removed_ids),
        "removed_by_track": dict(Counter(sample["track"] for sample in removed_filled)),
        "removed_by_split": dict(Counter(sample["split"] for sample in removed_filled)),
        "removed_param_records": len(removed_params),
    }
    write_json(ARCHIVE_DIR / "removed_samples_filled.json", removed_filled)
    write_json(ARCHIVE_DIR / "removed_samples_placeholder.json", removed_placeholder)
    write_json(ARCHIVE_DIR / "removed_param_records.json", {"records": removed_params})
    write_json(ARCHIVE_DIR / "summary.json", removed_summary)

    kept_groups_filled = group_by_track(kept_filled)
    kept_groups_placeholder = group_by_track(kept_placeholder)

    write_json(CLEAN_DIR / "id_heldout_all_tracks_filled.json", kept_filled)
    write_json(CLEAN_DIR / "id_heldout_all_tracks.json", kept_placeholder)
    write_json(CLEAN_DIR / "id_heldout_v_track_filled.json", kept_groups_filled["V-track"])
    write_json(CLEAN_DIR / "id_heldout_nv_track_filled.json", kept_groups_filled["NV-track"])
    write_json(CLEAN_DIR / "id_heldout_mixed_track_filled.json", kept_groups_filled["Mixed-track"])
    write_json(CLEAN_DIR / "id_heldout_v_track.json", kept_groups_placeholder["V-track"])
    write_json(CLEAN_DIR / "id_heldout_nv_track.json", kept_groups_placeholder["NV-track"])
    write_json(CLEAN_DIR / "id_heldout_mixed_track.json", kept_groups_placeholder["Mixed-track"])

    clean_params_payload = {
        "meta": {
            **params_payload.get("meta", {}),
            "filtered_flag": TARGET_FLAG,
            "filtered_samples_removed": len(removed_ids),
        },
        "records": kept_params,
    }
    write_json(CLEAN_DIR / "llm_constraint_parameters.json", clean_params_payload)

    clean_quality_summary = build_quality_summary(kept_filled)
    write_json(CLEAN_DIR / "quality_review_summary.json", clean_quality_summary)
    VIEWER_PATH.write_text(build_clean_viewer(kept_filled), encoding="utf-8")

    manifest = {
        "target_flag": TARGET_FLAG,
        "removed_samples": len(removed_ids),
        "clean_samples": len(kept_filled),
        "clean_track_counts": {track: len(items) for track, items in kept_groups_filled.items()},
        "archive_dir": str(ARCHIVE_DIR),
        "clean_dir": str(CLEAN_DIR),
        "viewer": str(VIEWER_PATH),
    }
    write_json(CLEAN_DIR / "manifest.json", manifest)

    print("removed samples", len(removed_ids))
    print("clean samples", len(kept_filled))
    print("archive", ARCHIVE_DIR)
    print("clean", CLEAN_DIR)
    print("viewer", VIEWER_PATH)


if __name__ == "__main__":
    main()
