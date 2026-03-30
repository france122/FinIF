from __future__ import annotations

import json
import re

from verifier.base import (
    bullet_items,
    char_count_no_space,
    extract_numbers,
    first_nonempty_line,
    first_word,
    has_checkbox,
    has_code_or_formula_block,
    has_markdown_table,
    last_nonempty_line,
    load_json_if_possible,
    markdown_heading_levels,
    nonempty_lines,
    paragraph_count,
    result_fail,
    result_inconclusive,
    result_pass,
    sentence_count,
)


RISK_LEVEL_RE = re.compile(r"\bR[1-5]\b")
RATING_WORDS = ("买入", "增持", "中性", "减持", "卖出")
NUMBERED_LINE_RE = re.compile(r"(?m)^\s*\d+\.\s+")
MONEY_SYMBOL_RE = re.compile(r"[¥$]")


def check_max_chars(constraint_id: str, response_text: str, params: dict):
    limit = int(params["n"])
    count = char_count_no_space(response_text)
    if count <= limit:
        return result_pass(constraint_id, f"字符数 {count} <= {limit}", count=count, limit=limit)
    return result_fail(constraint_id, f"字符数 {count} > {limit}", count=count, limit=limit)


def check_min_sentences(constraint_id: str, response_text: str, params: dict):
    need = int(params["n"])
    count = sentence_count(response_text)
    if count >= need:
        return result_pass(constraint_id, f"句子数 {count} >= {need}", count=count, need=need)
    return result_fail(constraint_id, f"句子数 {count} < {need}", count=count, need=need)


def check_paragraphs(constraint_id: str, response_text: str, params: dict):
    need = int(params["n"])
    count = paragraph_count(response_text)
    if count == need:
        return result_pass(constraint_id, f"段落数 {count} == {need}", count=count, need=need)
    return result_fail(constraint_id, f"段落数 {count} != {need}", count=count, need=need)


def check_markdown_format(constraint_id: str, response_text: str, params: dict):
    has_markdown = bool(markdown_heading_levels(response_text)) or bool(
        re.search(r"(?m)^\s*(?:[-*+]|\d+\.)\s+", response_text)
    ) or has_markdown_table(response_text) or "```" in response_text
    if has_markdown:
        return result_pass(constraint_id, "检测到 Markdown 结构")
    return result_fail(constraint_id, "未检测到明显 Markdown 结构")


def check_heading_levels(constraint_id: str, response_text: str, params: dict):
    need = int(params["n"])
    levels = markdown_heading_levels(response_text)
    if len(levels) >= need:
        return result_pass(constraint_id, f"检测到 {len(levels)} 级标题", levels=sorted(levels), need=need)
    return result_fail(constraint_id, f"仅检测到 {len(levels)} 级标题", levels=sorted(levels), need=need)


def check_numbered_list(constraint_id: str, response_text: str, params: dict):
    if NUMBERED_LINE_RE.search(response_text):
        return result_pass(constraint_id, "检测到编号列表")
    return result_fail(constraint_id, "未检测到编号列表")


def check_markdown_table(constraint_id: str, response_text: str, params: dict):
    if has_markdown_table(response_text):
        return result_pass(constraint_id, "检测到 Markdown 表格")
    return result_fail(constraint_id, "未检测到 Markdown 表格")


def check_json_format(constraint_id: str, response_text: str, params: dict):
    ok, payload = load_json_if_possible(response_text)
    if ok:
        payload_type = type(payload).__name__
        return result_pass(constraint_id, f"JSON 解析成功: {payload_type}")
    return result_fail(constraint_id, "JSON 解析失败")


def check_keywords_exist(constraint_id: str, response_text: str, params: dict):
    missing = [key for key in (params["kw1"], params["kw2"]) if key not in response_text]
    if not missing:
        return result_pass(constraint_id, "关键词齐全", kw1=params["kw1"], kw2=params["kw2"])
    return result_fail(constraint_id, "缺少关键词", missing=missing)


def check_forbidden_word(constraint_id: str, response_text: str, params: dict):
    word = params["word"]
    if word in response_text:
        return result_fail(constraint_id, f"出现禁用词: {word}", word=word)
    return result_pass(constraint_id, f"未出现禁用词: {word}", word=word)


def check_first_word(constraint_id: str, response_text: str, params: dict):
    expected = params["word"]
    actual = first_word(response_text)
    if actual == expected:
        return result_pass(constraint_id, f"首词匹配: {actual}", actual=actual, expected=expected)
    return result_fail(constraint_id, f"首词不匹配: {actual} != {expected}", actual=actual, expected=expected)


def check_checkbox(constraint_id: str, response_text: str, params: dict):
    if has_checkbox(response_text):
        return result_pass(constraint_id, "检测到 checkbox")
    return result_fail(constraint_id, "未检测到 checkbox")


def check_code_or_formula(constraint_id: str, response_text: str, params: dict):
    if has_code_or_formula_block(response_text):
        return result_pass(constraint_id, "检测到代码块或公式块")
    return result_fail(constraint_id, "未检测到代码块或公式块")


def check_first_last_line(constraint_id: str, response_text: str, params: dict):
    first_line = first_nonempty_line(response_text)
    last_line = last_nonempty_line(response_text)
    expected_first = params["first_line"]
    expected_last = params["last_line"]
    if first_line == expected_first and last_line == expected_last:
        return result_pass(constraint_id, "首末行均匹配", first_line=first_line, last_line=last_line)
    return result_fail(
        constraint_id,
        "首行或末行不匹配",
        first_line=first_line,
        expected_first=expected_first,
        last_line=last_line,
        expected_last=expected_last,
    )


def check_bullet_prefix(constraint_id: str, response_text: str, params: dict):
    prefix = params["prefix"]
    items = bullet_items(response_text)
    if not items:
        return result_fail(constraint_id, "未检测到 bullet 列表", prefix=prefix)
    bad = [item for item in items if not item.startswith(prefix)]
    if not bad:
        return result_pass(constraint_id, "所有 bullet 前缀匹配", prefix=prefix, bullet_count=len(items))
    return result_fail(constraint_id, "存在 bullet 未以指定前缀开头", prefix=prefix, bad_items=bad[:5])


def check_last_line_equals(constraint_id: str, response_text: str, params: dict):
    expected = params["risk_line"]
    actual = last_nonempty_line(response_text)
    if actual == expected:
        return result_pass(constraint_id, "末行风险提示匹配", expected=expected)
    return result_fail(constraint_id, "末行风险提示不匹配", actual=actual, expected=expected)


def check_contains_phrase(constraint_id: str, response_text: str, params: dict):
    expected = params["disclaimer"]
    if expected in response_text:
        return result_pass(constraint_id, "检测到免责声明", expected=expected)
    return result_fail(constraint_id, "未检测到免责声明", expected=expected)


def check_conditional_followup(constraint_id: str, response_text: str, params: dict):
    trigger = params["trigger"]
    followup = params["followup"]
    if trigger not in response_text:
        return result_pass(constraint_id, "未触发条件，按规则视为通过", trigger=trigger)
    if followup in response_text:
        return result_pass(constraint_id, "触发词与补充说明均出现", trigger=trigger, followup=followup)
    return result_fail(constraint_id, "出现 trigger 但缺少 followup", trigger=trigger, followup=followup)


def check_descending_order(constraint_id: str, response_text: str, params: dict):
    field = params["order_field"]
    lines = [line for line in nonempty_lines(response_text) if field in line or "|" in line]
    values = []
    for line in lines:
        nums = extract_numbers(line)
        if nums:
            values.append(nums[-1])
    if len(values) < 2:
        fallback_values = []
        for line in nonempty_lines(response_text):
            if re.match(r"^\s*(?:[-*+]|\d+\.|\|)", line):
                nums = extract_numbers(line)
                if nums:
                    fallback_values.append(nums[-1])
        values = fallback_values
    if len(values) < 2:
        return result_inconclusive(
            constraint_id,
            "未能稳定解析出可比较的排序数值，建议人工或 LLM 复核",
            order_field=field,
        )
    if all(values[idx] >= values[idx + 1] for idx in range(len(values) - 1)):
        return result_pass(constraint_id, "检测到降序排列", order_field=field, values=values[:10])
    return result_fail(constraint_id, "数值序列不是降序", order_field=field, values=values[:10])


def check_currency_rule(constraint_id: str, response_text: str, params: dict):
    rule = params["currency_rule"]
    money_like = bool(MONEY_SYMBOL_RE.search(response_text) or re.search(r"(人民币|美元|USD|CNY|元|万元|亿元)", response_text))
    if not money_like:
        return result_pass(constraint_id, "回答未出现金额表达，条件约束未触发")
    problems = []
    if "不使用逗号" in rule and re.search(r"\d,\d", response_text):
        problems.append("存在逗号分隔数字")
    if "不使用小数点" in rule and re.search(r"\d+\.\d+", response_text):
        problems.append("存在小数金额")
    if any(token in rule for token in ("人民币", "CNY")) and any(token in response_text for token in ("$", "USD", "美元")):
        problems.append("出现了美元表示")
    if any(token in rule for token in ("美元", "USD", "$")) and any(token in response_text for token in ("¥", "人民币", "CNY")):
        problems.append("出现了人民币表示")
    if problems:
        return result_fail(constraint_id, "金额格式不符合规则", currency_rule=rule, problems=problems)
    return result_pass(constraint_id, "未检测到明显金额格式冲突", currency_rule=rule)


def check_risk_level(constraint_id: str, response_text: str, params: dict):
    match = RISK_LEVEL_RE.search(response_text)
    if match:
        return result_pass(constraint_id, "检测到风险等级", risk_level=match.group(0))
    return result_fail(constraint_id, "未检测到 R1-R5 风险等级")


def check_rating_word(constraint_id: str, response_text: str, params: dict):
    for word in RATING_WORDS:
        if word in response_text:
            return result_pass(constraint_id, "检测到投资评级词", rating=word)
    return result_fail(constraint_id, "未检测到投资评级词")
