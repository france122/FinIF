#!/usr/bin/env python3
"""FinIF Benchmark Viewer"""

import json, os, glob
from http.server import HTTPServer, SimpleHTTPRequestHandler

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(DEMO_DIR, "output")

UPGRADED = set([
    "T3.3-001#C1","T3.3-001#C2","T3.3-001#C3",
    "T3.3-002#C2","T3.3-002#C3","T3.3-002#C4",
    "T3.1-004#C1","T3.1-004#C2",
    "T3.2-004#C3","T3.2-004#C4",
    "T3.1-003#C1","T3.1-003#C2",
    "T3.3-004#C1","T3.3-004#C2","T3.3-004#C3",
])


def load_data():
    with open(os.path.join(DEMO_DIR, "benchmark_all.json"), encoding="utf-8") as f:
        cases = {c["case_id"]: c for c in json.load(f)["cases"]}
    with open(os.path.join(DEMO_DIR, "eval_config_all.json"), encoding="utf-8") as f:
        constraints = json.load(f)["constraints"]
    responses = {}
    for fp in sorted(glob.glob(os.path.join(OUTPUT_DIR, "responses_*.jsonl"))):
        model = os.path.basename(fp).replace("responses_", "").replace(".jsonl", "")
        responses[model] = {}
        with open(fp, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    responses[model][obj["case_id"]] = obj.get("response", "")
    scores = {}
    for fp in sorted(glob.glob(os.path.join(OUTPUT_DIR, "scores_*.json"))):
        model = os.path.basename(fp).replace("scores_", "").replace(".json", "")
        with open(fp, encoding="utf-8") as f:
            scores[model] = json.load(f)
    return cases, constraints, responses, scores


def build_api_data(cases, constraints, responses, scores):
    """Build all data as a single JSON blob for the frontend."""
    models = sorted(scores.keys())
    case_ids = sorted(cases.keys())

    # Model summary
    model_summary = []
    for m in models:
        ts = scores[m].get("tier_scores", {})
        sc = scores[m].get("scores", {})
        hard_p = sum(s.get("hard", {}).get("passed", 0) for s in sc.values())
        hard_t = sum(s.get("hard", {}).get("total", 0) for s in sc.values())
        soft_p = sum(s.get("soft", {}).get("passed", 0) for s in sc.values())
        soft_t = sum(s.get("soft", {}).get("total", 0) for s in sc.values())
        model_summary.append({
            "model": m,
            "T1": round(ts.get("T1", 0) * 100, 1),
            "T2": round(ts.get("T2", 0) * 100, 1),
            "T3": round(ts.get("T3", 0) * 100, 1),
            "overall": round(ts.get("overall", 0) * 100, 1),
            "hard": f"{hard_p}/{hard_t}",
            "soft": f"{soft_p}/{soft_t}",
        })

    # Cases
    cases_data = []
    for cid in case_ids:
        c = cases[cid]
        tier = cid.split(".")[0]
        case_constraints = []
        for ck, cv in sorted(constraints.items()):
            if ck.startswith(cid + "#"):
                case_constraints.append({
                    "id": ck,
                    "description": cv.get("description", ""),
                    "type": cv.get("type", ""),
                    "checker": cv.get("checker", ""),
                    "params": cv.get("params"),
                    "upgraded": ck in UPGRADED,
                })
        model_data = []
        for model in models:
            resp = responses.get(model, {}).get(cid, None)
            has_response = resp is not None and resp != ""
            s = scores.get(model, {}).get("scores", {}).get(cid, {})
            rd = scores.get(model, {}).get("results", {}).get(cid, {})
            cr = []
            for cc in case_constraints:
                r = rd.get(cc["id"], {})
                cr.append({
                    "id": cc["id"], "pass": r.get("pass"),
                    "reason": r.get("reason", ""),
                })
            model_data.append({
                "model": model, "response": resp or "",
                "has_response": has_response,
                "score": round(s.get("score", 0), 4) if has_response else None,
                "hard_passed": s.get("hard", {}).get("passed", 0),
                "hard_total": s.get("hard", {}).get("total", 0),
                "soft_passed": s.get("soft", {}).get("passed", 0),
                "soft_total": s.get("soft", {}).get("total", 0),
                "constraints": cr,
            })
        cases_data.append({
            "case_id": cid, "tier": tier,
            "prompt": c.get("prompt", ""),
            "context": c.get("context", ""),
            "constraints": case_constraints,
            "models": model_data,
        })

    return {"models": models, "summary": model_summary, "cases": cases_data}


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FinIF Benchmark Viewer</title>
<style>
:root{--bg:#0f1117;--card:#1a1a2e;--border:#2a2a4a;--accent:#7eb8ff;--green:#4ade80;--red:#f87171;--yellow:#facc15;--text:#e0e0e0;--muted:#888}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text)}

.header{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:18px 28px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:20px;color:#fff}
.header .sub{color:var(--muted);font-size:12px}

.container{max-width:1500px;margin:0 auto;padding:20px}
.sec{margin-bottom:24px}
.sec h2{font-size:15px;margin-bottom:8px;color:#ccc;border-left:3px solid var(--accent);padding-left:8px}

table.dt{width:100%;border-collapse:collapse;background:var(--card);border-radius:6px;overflow:hidden;font-size:13px}
table.dt th{background:#222244;padding:7px 12px;text-align:left;color:#aaa;font-size:11px;text-transform:uppercase}
table.dt td{padding:7px 12px;border-top:1px solid var(--border)}
table.dt tr:hover{background:#222244}
.mn{font-weight:600;color:var(--accent)}
.vg{color:var(--green);font-weight:700}

.filters{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;align-items:center}
.fbtn{padding:4px 12px;border-radius:16px;border:1px solid var(--border);background:transparent;color:#aaa;cursor:pointer;font-size:12px;transition:all .15s}
.fbtn:hover{border-color:var(--accent);color:var(--accent)}
.fbtn.active{background:var(--accent);color:var(--bg);border-color:var(--accent);font-weight:600}
.sbox{padding:4px 10px;border-radius:16px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:12px;width:160px}

.clist{display:flex;flex-direction:column;gap:5px}
.citem{background:var(--card);border:1px solid var(--border);border-radius:5px;padding:8px 14px;cursor:pointer;transition:all .15s;display:flex;align-items:center;gap:10px}
.citem:hover,.citem.sel{border-color:var(--accent);background:#1e1e36}
.cid{font-weight:700;font-size:13px;color:var(--accent);min-width:85px}
.tbadge{font-size:10px;padding:1px 5px;border-radius:3px;font-weight:600}
.tT1{background:#1e3a5f;color:#60a5fa}.tT2{background:#3b2f0a;color:#fbbf24}.tT3{background:#3b1c1c;color:#f87171}
.cdesc{flex:1;font-size:11px;color:#666;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.schips{display:flex;gap:5px}
.schip{font-size:11px;padding:1px 6px;border-radius:8px}
.sh{background:#064e3b;color:var(--green)}.sm{background:#3b3400;color:var(--yellow)}.sl{background:#4c0519;color:#fb7185}
.utag{display:inline-block;font-size:9px;padding:0 4px;border-radius:2px;margin-left:3px;background:#4c1d95;color:#c4b5fd;font-weight:600}

.dpanel{display:none;margin-top:18px}
.dpanel.vis{display:block}
.dbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.dbar h2{font-size:17px;color:#fff}
.closeb{padding:3px 8px;border-radius:3px;border:1px solid var(--border);background:transparent;color:#aaa;cursor:pointer;font-size:12px}
.closeb:hover{border-color:var(--red);color:var(--red)}

.tabs{display:flex;gap:2px;margin-bottom:12px;border-bottom:1px solid var(--border)}
.tab{padding:6px 16px;cursor:pointer;color:var(--muted);font-size:13px;border-bottom:2px solid transparent;transition:all .15s}
.tab:hover{color:#ccc}.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.tc{display:none}.tc.active{display:block}

.tblk{background:#12121e;border:1px solid var(--border);border-radius:5px;padding:12px;font-size:12px;line-height:1.8;white-space:pre-wrap;word-break:break-all;max-height:500px;overflow-y:auto}

.ctbl{width:100%;border-collapse:collapse;font-size:12px;background:#12121e;border-radius:5px;overflow:hidden}
.ctbl th{background:#1a1a2e;padding:5px 8px;text-align:left;color:#aaa;font-size:11px;position:sticky;top:0;z-index:1}
.ctbl td{padding:5px 8px;border-top:1px solid #1e1e2e;vertical-align:top}
.ctbl tr:hover{background:#1a1a2e}
.ctbl .p{color:var(--green);font-weight:600}.ctbl .f{color:var(--red);font-weight:600}.ctbl .s{color:#555}
.ctbl .diff{background:#2a1a3e}
.urow{border-left:2px solid #8b5cf6}

.mtabs{display:flex;gap:3px;margin-bottom:8px;flex-wrap:wrap}
.mtab{padding:4px 10px;cursor:pointer;color:var(--muted);font-size:12px;border:1px solid var(--border);border-radius:4px;transition:all .15s}
.mtab:hover{border-color:var(--accent);color:#ccc}
.mtab.active{background:var(--accent);color:var(--bg);border-color:var(--accent);font-weight:600}
.sbar{display:flex;gap:12px;margin-bottom:8px;font-size:12px;color:#aaa}
.sbar b{color:var(--text)}
</style>
</head>
<body>

<div class="header">
    <div><h1>FinIF Benchmark Viewer</h1><div class="sub" id="headerSub"></div></div>
</div>

<div class="container">
    <div class="sec"><h2>Model Scores</h2><div id="summaryTable"></div></div>
    <div class="sec">
        <h2>Cases</h2>
        <div class="filters">
            <button class="fbtn active" data-f="all">All</button>
            <button class="fbtn" data-f="T1">T1</button>
            <button class="fbtn" data-f="T2">T2</button>
            <button class="fbtn" data-f="T3">T3</button>
            <button class="fbtn" data-f="diff">Diff Only</button>
            <input class="sbox" type="text" placeholder="Search..." id="searchBox">
        </div>
        <div class="clist" id="caseList"></div>
    </div>
    <div class="dpanel" id="dp">
        <div class="dbar"><h2 id="dTitle"></h2><button class="closeb" id="closeBtn">Close</button></div>
        <div class="tabs" id="tabBar"></div>
        <div class="tc active" id="tc-prompt"><div class="tblk" id="promptBox"></div></div>
        <div class="tc" id="tc-compare"><div style="max-height:600px;overflow:auto" id="cmpBox"></div></div>
        <div class="tc" id="tc-responses">
            <div class="mtabs" id="mTabs"></div>
            <div class="sbar" id="sBar"></div>
            <div class="tblk" style="max-height:450px" id="respBox"></div>
            <div style="margin-top:10px" id="rGrid"></div>
        </div>
    </div>
</div>

<script>
const D = __DATA__;
const M = D.models;
let filter='all', search='', selCase=null, selModel=M[0];

const esc = s => { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; };
const scC = s => s>=0.8?'sh':s>=0.5?'sm':'sl';
const shortM = m => m.replace(/-202\d-\d+-\d+/,'');

// Summary
document.getElementById('headerSub').textContent = `${D.cases.length} cases | ${M.length} models`;
{
    let h = '<table class="dt"><thead><tr><th>Model</th><th>T1</th><th>T2</th><th>T3</th><th>Overall</th><th>Hard</th><th>Soft</th></tr></thead><tbody>';
    D.summary.forEach(s => {
        h += `<tr><td class="mn">${s.model}</td><td>${s.T1}%</td><td>${s.T2}%</td><td>${s.T3}%</td><td class="vg">${s.overall}%</td><td>${s.hard}</td><td>${s.soft}</td></tr>`;
    });
    h += '</tbody></table>';
    document.getElementById('summaryTable').innerHTML = h;
}

// Filters
document.querySelectorAll('.fbtn').forEach(b => b.addEventListener('click', () => {
    filter = b.dataset.f;
    document.querySelectorAll('.fbtn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    renderList();
}));
document.getElementById('searchBox').addEventListener('input', e => { search=e.target.value; renderList(); });

function renderList() {
    let h = '';
    D.cases.forEach(c => {
        if (filter==='diff') {
            const ss = c.models.map(m=>m.score);
            if (Math.max(...ss)-Math.min(...ss)<0.05) return;
        } else if (filter!=='all' && c.tier!==filter) return;
        if (search && !c.case_id.toLowerCase().includes(search.toLowerCase())) return;

        const chips = c.models.map(m =>
            `<span class="schip ${scC(m.score)}" title="${m.model}">${shortM(m.model)}: ${(m.score*100).toFixed(0)}%</span>`
        ).join('');
        const nU = c.constraints.filter(x=>x.upgraded).length;
        const ub = nU?`<span class="utag">${nU} upg</span>`:'';

        h += `<div class="citem${selCase===c.case_id?' sel':''}" data-id="${c.case_id}">
            <span class="cid">${c.case_id}</span>
            <span class="tbadge t${c.tier}">${c.tier}</span>
            <span style="font-size:11px;color:#777">${c.constraints.length}C ${ub}</span>
            <span class="cdesc">${esc(c.constraints[0]?.description||'')}</span>
            <div class="schips">${chips}</div>
        </div>`;
    });
    document.getElementById('caseList').innerHTML = h;
    document.querySelectorAll('.citem').forEach(el => el.addEventListener('click', () => openCase(el.dataset.id)));
}

function openCase(id) {
    selCase = id;
    const c = D.cases.find(x=>x.case_id===id);
    if (!c) return;
    document.getElementById('dTitle').textContent = `${id} (${c.constraints.length} constraints)`;
    document.getElementById('promptBox').textContent = c.prompt;

    // Tab bar
    document.getElementById('tabBar').innerHTML = ['Prompt','Constraint Comparison','Model Responses'].map((t,i) =>
        `<div class="tab${i===0?' active':''}" data-t="${['prompt','compare','responses'][i]}">${t}</div>`
    ).join('');
    document.querySelectorAll('#tabBar .tab').forEach(t => t.addEventListener('click', () => switchTab(t.dataset.t)));

    // Comparison table
    let cmp = '<table class="ctbl"><thead><tr><th>ID</th><th>Type</th><th>Checker</th><th style="max-width:300px">Description</th>';
    M.forEach(m => { cmp += `<th>${shortM(m)}</th>`; });
    cmp += '</tr></thead><tbody>';
    c.constraints.forEach((cc, i) => {
        const results = M.map(m => {
            const md = c.models.find(x=>x.model===m);
            return md ? md.constraints[i] : null;
        });
        const vals = results.map(r => r?.pass);
        const allSame = vals.every(v => v===vals[0]);
        const rc = (cc.upgraded?'urow':'') + (!allSame?' diff':'');

        cmp += `<tr class="${rc}">`;
        cmp += `<td style="font-family:monospace;font-size:11px;white-space:nowrap">${cc.id}${cc.upgraded?'<span class="utag">UPG</span>':''}</td>`;
        cmp += `<td><span style="font-size:10px;padding:1px 4px;border-radius:2px;${cc.type==='hard'?'background:#2d1b69;color:#a78bfa':'background:#1b4332;color:#6ee7b7'}">${cc.type}</span></td>`;
        cmp += `<td style="font-family:monospace;font-size:10px;color:#666">${cc.checker||''}</td>`;
        cmp += `<td style="font-size:11px;color:#999;max-width:300px">${esc(cc.description)}</td>`;
        results.forEach(r => {
            if (!r) { cmp += '<td class="s">N/A</td>'; return; }
            const cls = r.pass===true?'p':r.pass===false?'f':'s';
            const icon = r.pass===true?'PASS':r.pass===false?'FAIL':'-';
            const rsn = r.reason ? `<br><span style="font-size:10px;color:#555">${esc(r.reason).substring(0,80)}</span>` : '';
            cmp += `<td class="${cls}">${icon}${rsn}</td>`;
        });
        cmp += '</tr>';
    });
    cmp += '</tbody></table>';
    document.getElementById('cmpBox').innerHTML = cmp;

    // Model tabs
    let mt = '';
    M.forEach(m => {
        const md = c.models.find(x=>x.model===m);
        const sc = md ? (md.score*100).toFixed(0)+'%' : '-';
        mt += `<div class="mtab${selModel===m?' active':''}" data-m="${m}">${m} (${sc})</div>`;
    });
    document.getElementById('mTabs').innerHTML = mt;
    document.querySelectorAll('.mtab').forEach(t => t.addEventListener('click', () => {
        selModel = t.dataset.m;
        document.querySelectorAll('.mtab').forEach(x=>x.classList.remove('active'));
        t.classList.add('active');
        renderResp(c);
    }));

    renderResp(c);
    document.getElementById('dp').classList.add('vis');
    switchTab('prompt');
    renderList();
    document.getElementById('dp').scrollIntoView({behavior:'smooth'});
}

function renderResp(c) {
    const md = c.models.find(x=>x.model===selModel);
    if (!md) {
        document.getElementById('respBox').textContent='(no response)';
        document.getElementById('sBar').innerHTML='';
        document.getElementById('rGrid').innerHTML='';
        return;
    }
    document.getElementById('respBox').textContent = md.response||'(empty)';
    document.getElementById('sBar').innerHTML = `Score: <b>${(md.score*100).toFixed(1)}%</b> | Hard: <b>${md.hard_passed}/${md.hard_total}</b> | Soft: <b>${md.soft_passed}/${md.soft_total}</b>`;

    let rh = '<table class="ctbl"><thead><tr><th>ID</th><th>Type</th><th>Result</th><th>Description / Reason</th></tr></thead><tbody>';
    md.constraints.forEach((cr,i) => {
        const cc = c.constraints[i];
        const cls = cr.pass===true?'p':cr.pass===false?'f':'s';
        const icon = cr.pass===true?'PASS':cr.pass===false?'FAIL':'-';
        const rc = cc?.upgraded?'urow':'';
        rh += `<tr class="${rc}"><td style="font-family:monospace;font-size:11px">${cr.id}${cc?.upgraded?'<span class="utag">UPG</span>':''}</td>`;
        rh += `<td><span style="font-size:10px;padding:1px 4px;border-radius:2px;${cc?.type==='hard'?'background:#2d1b69;color:#a78bfa':'background:#1b4332;color:#6ee7b7'}">${cc?.type||''}</span></td>`;
        rh += `<td class="${cls}">${icon}</td>`;
        rh += `<td style="font-size:11px;color:#999">${esc(cc?.description||'')}${cr.reason?'<br><span style="color:#666">'+esc(cr.reason)+'</span>':''}</td></tr>`;
    });
    rh += '</tbody></table>';
    document.getElementById('rGrid').innerHTML = rh;
}

function switchTab(name) {
    document.querySelectorAll('#tabBar .tab').forEach(t => t.classList.toggle('active', t.dataset.t===name));
    ['prompt','compare','responses'].forEach(n => document.getElementById('tc-'+n).classList.toggle('active', n===name));
}

document.getElementById('closeBtn').addEventListener('click', () => {
    selCase=null;
    document.getElementById('dp').classList.remove('vis');
    renderList();
});

renderList();
</script>
</body>
</html>"""


def build_html(api_data):
    data_json = json.dumps(api_data, ensure_ascii=False)
    return HTML_TEMPLATE.replace("__DATA__", data_json)


class ViewerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, html_content=None, **kwargs):
        self.html_content = html_content
        super().__init__(*args, **kwargs)
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.html_content.encode("utf-8"))
        else:
            super().do_GET()
    def log_message(self, fmt, *args):
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18924)
    args = parser.parse_args()
    cases, constraints, responses, scores = load_data()
    api_data = build_api_data(cases, constraints, responses, scores)
    html = build_html(api_data)
    handler = lambda *a, **kw: ViewerHandler(*a, html_content=html, **kw)
    server = HTTPServer(("0.0.0.0", args.port), handler)
    print(f"FinIF Benchmark Viewer: http://0.0.0.0:{args.port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
