"""
手工填充 DS 无法自动修复的 GV-9/GV-8 冲突记录。
策略：根据 DS 反复选择的词（即 query 的核心概念），选一个语义相关、
模型回答时很可能使用、但不在 query 原文中的近义/关联词。
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FAIL_PATH = BASE_DIR / "data/tracks/llm_constraint_parameters_ds_5500_run1.failures.json"
OUTPUT_PATH = BASE_DIR / "data/tracks/llm_constraint_parameters_ds_5500_run1.json"
TRACKS_PATH = BASE_DIR / "data/tracks/id_heldout_all_tracks.json"

# ── GV-9 替代词池 ──
# key = DS 反复尝试的失败词
# value = 优先级从高到低的候选替代词列表，脚本会选第一个不在 query 中的
GV9_ALTERNATIVES = {
    "风险点":     ["隐患", "缺陷", "漏洞", "整改", "合规", "偏差", "敞口"],
    "异常点":     ["隐患", "缺陷", "偏差", "漏洞", "整改", "合规"],
    "风险排查":   ["隐患", "缺陷", "漏洞", "合规", "整改", "偏差"],
    "风险":       ["隐患", "波动", "敞口", "亏损", "回撤", "合规"],
    "稳健":       ["审慎", "保守", "均衡", "平稳", "适度", "低波动"],
    "稳健增值":   ["保本", "审慎", "低波动", "保守", "收益率"],
    "增长":       ["扩张", "回暖", "向好", "超预期", "盈利", "利润"],
    "流动性":     ["变现", "赎回", "久期", "周转", "到期", "存续期"],
    "改善":       ["修复", "回暖", "扭转", "优化", "好转", "向好"],
    "审计":       ["合规", "整改", "复核", "核查", "内控", "抽查"],
    "保险产品":   ["保障", "投保", "保费", "理赔", "核保", "免赔额"],
    "理财":       ["储蓄", "投资", "收益", "回报", "利率"],
    "数据":       ["接口", "参数", "变量", "函数", "调用", "指标"],
    "增值":       ["收益", "回报", "保值", "盈利", "复利"],
    "模型":       ["参数", "回测", "信号", "策略", "变量", "因子"],
    "获取":       ["调用", "接口", "请求", "抓取", "拉取", "导入"],
    "波动":       ["震荡", "回撤", "下行", "调整", "回调"],
    "客户":       ["投资者", "持有人", "用户", "委托人"],
    "资产配置":   ["仓位", "权重", "头寸", "敞口", "久期"],
    "衍生品":     ["对冲", "套期保值", "期权", "期货", "合约"],
    "配置":       ["仓位", "权重", "头寸", "敞口", "比例"],
    "红利":       ["分红", "股息", "派息", "收益率", "回报"],
    "银行":       ["金融机构", "信贷", "存款", "贷款", "网点"],
    "关注":       ["留意", "警惕", "重视", "注意", "聚焦"],
    "机器学习":   ["算法", "训练", "特征", "拟合", "过拟合"],
    "债券":       ["久期", "票息", "到期", "利差", "信用"],
    "风险敞口":   ["暴露", "头寸", "集中度", "限额", "阈值"],
    "估值":       ["市盈率", "溢价", "折价", "定价", "倍数"],
    "比例":       ["权重", "占比", "份额", "仓位", "敞口"],
    "标准差":     ["方差", "波动率", "离散度", "偏差", "回撤"],
    "修复":       ["回暖", "改善", "好转", "扭转", "优化"],
    "建议":       ["策略", "方案", "措施", "对策", "思路"],
    "分散":       ["集中", "均衡", "对冲", "权重", "仓位"],
    "收益":       ["回报", "盈利", "利润", "利差", "复利"],
}

# ── GV-8 替代关键词池 ──
# 需要两个关键词都不在 query 中
GV8_ALTERNATIVES = {
    "投资组合":    [("资产配比", "风险分散"), ("仓位管理", "收益归因"), ("头寸配置", "夏普比率")],
    "估值消化":    [("业绩兑现", "毛利改善"), ("产能释放", "渠道下沉"), ("库存去化", "毛利回升")],
    "风险承受能力": [("资产久期", "再平衡"), ("目标收益", "回撤控制"), ("现金比例", "定投策略")],
    "订单增长":    [("产能利用率", "渠道扩张"), ("毛利修复", "库存周转"), ("客户结构", "产品迭代")],
}


def pick_gv9_word(ds_word, query_text):
    """从候选池中选第一个不在 query 中的词。"""
    candidates = GV9_ALTERNATIVES.get(ds_word, [])
    for w in candidates:
        if w not in query_text:
            return w
    return None


def pick_gv8_keywords(ds_word, query_text):
    """从候选池中选第一组两个关键词都不在 query 中的。"""
    candidates = GV8_ALTERNATIVES.get(ds_word, [])
    for kw1, kw2 in candidates:
        if kw1 not in query_text and kw2 not in query_text:
            return kw1, kw2
    return None, None


def main():
    failures = json.loads(FAIL_PATH.read_text(encoding="utf-8"))
    tracks = json.loads(TRACKS_PATH.read_text(encoding="utf-8"))
    sid2query = {t["sample_id"]: t["query_input"] for t in tracks}

    output_data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    existing = {(r["sample_id"], r["constraint_id"]): r for r in output_data["records"]}

    filled = 0
    still_failed = []

    for f in failures:
        req = f["request"]
        sid = req["sample_id"]
        cid = req["constraint_id"]
        query = sid2query.get(sid, "")

        err = f["error"]
        m = re.search(r"禁词'(.+?)'", err) or re.search(r"kw\d='(.+?)'", err)
        ds_word = m.group(1) if m else ""

        if cid == "GV-9":
            word = pick_gv9_word(ds_word, query)
            if word is None:
                still_failed.append(f"[GV-9] {sid}: 无候选词可用 (DS尝试: {ds_word})")
                continue
            record = {
                "sample_id": sid,
                "query_id": req["query_id"],
                "split": req["split"],
                "track": req["track"],
                "constraint_id": cid,
                "params": {"word": word},
                "rendered_text": f'不得出现"{word}"',
                "model": "manual_fill",
                "attempts": 0,
                "raw_response": f'{{"word": "{word}"}}',
            }

        elif cid == "GV-8":
            kw1, kw2 = pick_gv8_keywords(ds_word, query)
            if kw1 is None:
                still_failed.append(f"[GV-8] {sid}: 无候选词可用 (DS尝试: {ds_word})")
                continue
            record = {
                "sample_id": sid,
                "query_id": req["query_id"],
                "split": req["split"],
                "track": req["track"],
                "constraint_id": cid,
                "params": {"kw1": kw1, "kw2": kw2},
                "rendered_text": f"必须包含关键词：{kw1}、{kw2}",
                "model": "manual_fill",
                "attempts": 0,
                "raw_response": f'{{"kw1": "{kw1}", "kw2": "{kw2}"}}',
            }
        else:
            still_failed.append(f"[{cid}] {sid}: 未知约束类型")
            continue

        # 最终 double-check
        if cid == "GV-9" and record["params"]["word"] in query:
            still_failed.append(f"[GV-9] {sid}: 选词'{record['params']['word']}'仍在query中!")
            continue
        if cid == "GV-8":
            for k in ("kw1", "kw2"):
                if record["params"][k] in query:
                    still_failed.append(f"[GV-8] {sid}: {k}='{record['params'][k]}'仍在query中!")
                    continue

        existing[(sid, cid)] = record
        filled += 1

    # 写回
    output_data["records"] = [existing[k] for k in sorted(existing)]
    output_data["meta"]["completed_records"] = len(existing)
    output_data["meta"]["manual_filled"] = filled
    OUTPUT_PATH.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"成功填充: {filled}")
    print(f"仍然失败: {len(still_failed)}")
    for msg in still_failed:
        print(f"  {msg}")


if __name__ == "__main__":
    main()
