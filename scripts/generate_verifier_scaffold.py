from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_TABLE = REPO_ROOT / "docs" / "constraint_reference_table.csv"
RULES_DIR = REPO_ROOT / "verifier" / "rules"
RUBRICS_DIR = REPO_ROOT / "verifier" / "rubrics"


RULE_IMPLS = {
    "GV-1": ("check_max_chars", ["n"]),
    "GV-2": ("check_min_sentences", ["n"]),
    "GV-3": ("check_paragraphs", ["n"]),
    "GV-4a": ("check_markdown_format", []),
    "GV-4b": ("check_heading_levels", ["n"]),
    "GV-5": ("check_numbered_list", []),
    "GV-6": ("check_markdown_table", []),
    "GV-7": ("check_json_format", []),
    "GV-8": ("check_keywords_exist", ["kw1", "kw2"]),
    "GV-9": ("check_forbidden_word", ["forbidden_word"]),
    "GV-10": ("check_first_word", ["word"]),
    "GV-11": ("check_checkbox", []),
    "GV-12": ("check_code_or_formula", []),
    "GV-13": ("check_first_last_line", ["first_line", "last_line"]),
    "GV-14": ("check_bullet_prefix", ["prefix"]),
    "FV-1": ("check_last_line_equals", ["risk_line"]),
    "FV-2": ("check_contains_phrase", ["disclaimer"]),
    "FV-3": ("check_conditional_followup", ["trigger", "followup"]),
    "FV-4": ("check_descending_order", ["order_field"]),
    "FV-5": ("check_currency_rule", ["currency_rule"]),
    "FV-6": ("check_risk_level", []),
    "FV-7": ("check_rating_word", []),
}


RUBRIC_SPECS = {
    "GV-15": {
        "focus": "判断回答是否真正做到先给结论，再展开分析或理由。",
        "score_2": "第一句话立刻、纯粹地给出结论，后文再展开理由或分析。",
        "score_1": "整体仍是先结论后分析，但开头夹杂了少量背景铺垫，或结论与第一条分析略有混杂。",
        "score_0": "明显先铺垫数据、条件或背景，结论没有真正前置。",
        "checklist": ["结论是否出现在回答前段", "后文是否有理由或分析", "整体顺序是否是结论在前"],
    },
    "GV-16": {
        "focus": "判断回答末尾是否包含独立总结段，而不是自然结束。",
        "score_2": "末尾有清晰总结，能收束全文并提炼核心观点。",
        "score_1": "末尾有一定总结意味，但不够独立或过于简略。",
        "score_0": "末尾没有总结性收束。",
        "checklist": ["最后一段是否明显承担总结功能", "总结是否复盘核心内容", "是否只是简单停在分析中途"],
    },
    "GN-3": {
        "focus": "判断文风是否正式、书面，避免口语化和聊天式表达。",
        "score_2": "整体正式克制，无明显口语化词汇或聊天语气。",
        "score_1": "大体正式，但夹杂少量口语化表达。",
        "score_0": "明显口语化、聊天化或随意。",
        "checklist": ["是否出现 好的/当然/其实/你可以 这类口语", "句式是否偏书面", "整体是否像正式报告或说明"],
    },
    "GN-4": {
        "focus": "判断语气是否客观中立，避免主观煽动或情绪化措辞。",
        "score_2": "措辞克制客观，结论基于条件或证据，不带明显主观倾向。",
        "score_1": "大体中立，但存在轻微主观色彩。",
        "score_0": "明显带有主观倾向、情绪性判断或煽动性措辞。",
        "checklist": ["是否有绝对化断言", "是否有情绪化褒贬", "是否保持分析式、中性式表达"],
    },
    "GN-5": {
        "focus": "判断段落之间是否有逻辑推进和过渡，而不是堆砌信息。",
        "score_2": "段落承接清晰，有明显逻辑顺序或过渡提示。",
        "score_1": "基本有逻辑，但个别段落切换生硬。",
        "score_0": "段落之间缺少承接，像信息拼接。",
        "checklist": ["段落是否围绕同一主线推进", "是否有过渡句或过渡词", "是否存在明显跳跃"],
    },
    "GN-6": {
        "focus": "判断每段是否提供新信息，避免重复表述同一点。",
        "score_2": "各段信息增量明显，几乎无实质重复。",
        "score_1": "有少量重复，但整体仍有新增信息。",
        "score_0": "多段反复表达同一意思，信息增量弱。",
        "checklist": ["段落之间是否重复观点", "是否每段有新增角度/事实/建议", "重复是否影响阅读价值"],
    },
    "GN-7": {
        "focus": "判断是否真的使用了类比或具体例子辅助解释。",
        "score_2": "明确给出类比或实例，并且确实帮助理解。",
        "score_1": "有例子/类比雏形，但较弱或不够贴切。",
        "score_0": "没有类比，也没有具体例子。",
        "checklist": ["是否出现例如/比如/可类比为 等信号", "例子是否具体", "例子是否服务于解释"],
    },
    "FN-1": {
        "focus": "判断分析是否主要从风险管理视角展开。",
        "score_2": "核心关注点是风险识别、暴露、控制和缓释。",
        "score_1": "提到风险，但主视角不稳定或不够突出。",
        "score_0": "基本不是从风险管理视角作答。",
        "checklist": ["是否讨论风险来源", "是否讨论控制/缓释措施", "风险视角是否主导全文"],
    },
    "FN-2": {
        "focus": "判断回答是否体现监管机构立场，而不是投资者或营销立场。",
        "score_2": "关注合规、稳健、信息披露、系统性风险等监管关切。",
        "score_1": "部分体现监管视角，但不够稳定。",
        "score_0": "主要还是从市场参与者立场出发。",
        "checklist": ["是否强调合规与审慎", "是否关注市场稳定/投资者保护", "是否避免营销式立场"],
    },
    "FN-3": {
        "focus": "判断回答是否真正站在零售投资者视角，而非机构或监管视角。",
        "score_2": "重点讨论普通投资者可理解、可执行的风险收益权衡。",
        "score_1": "有部分零售投资者关切，但不够充分。",
        "score_0": "明显不是零售投资者视角。",
        "checklist": ["是否考虑门槛/流动性/本金安全", "是否表达清晰易懂", "是否避免机构化视角主导"],
    },
    "FV-8": {
        "focus": "判断评价是否从 ESG 角度展开，而不只是一般财务分析。",
        "score_2": "明确覆盖环境、社会、治理中的一个或多个维度，并与评价结论关联。",
        "score_1": "提到 ESG，但较表面。",
        "score_0": "没有体现 ESG 评价框架。",
        "checklist": ["是否讨论 E/S/G 相关因素", "是否将 ESG 因素纳入结论", "是否超出普通财务评价"],
    },
    "FN-5": {
        "focus": "判断分析是否从宏观经济角度展开。",
        "score_2": "明显基于利率、通胀、增长、政策、周期等宏观变量分析。",
        "score_1": "有宏观因素，但不是主线。",
        "score_0": "几乎没有宏观经济视角。",
        "checklist": ["是否讨论宏观变量", "是否体现经济周期或政策环境", "宏观视角是否主导分析"],
    },
    "FV-9": {
        "focus": "判断回答是否注明信息来源，而不是无来源断言。",
        "score_2": "明确指出数据、材料、公告、报告或给定信息来源，并且来源指向具体。",
        "score_1": "有模糊来源指向，例如“据公告称”“据资料显示”，但来源不够精确。",
        "score_0": "完全未说明来源。",
        "checklist": ["是否出现 来源/根据/据…显示", "来源是否具体", "来源是否支撑关键结论"],
    },
    "FV-10": {
        "focus": "判断专业术语缩写是否给出全称解释。",
        "score_2": "关键缩写首次出现时都给出全称或完整解释。",
        "score_1": "部分缩写有解释，部分没有。",
        "score_0": "缩写直接使用，未解释。",
        "checklist": ["是否出现 ROE/PE/PB 等缩写", "首次出现时是否解释", "解释是否完整"],
    },
    "FN-8": {
        "focus": "判断语言是否通俗易懂，尽量避免密集专业术语。",
        "score_2": "表达面向非专业读者，术语少且必要时有解释。",
        "score_1": "总体可懂，但仍有较多未解释术语。",
        "score_0": "术语密集、生硬专业，不够通俗。",
        "checklist": ["术语密度是否偏高", "复杂概念是否被解释", "普通读者是否容易理解"],
    },
    "FN-9": {
        "focus": "判断回答是否严格基于给定材料，不额外编造材料外事实。",
        "score_2": "结论和证据都能在材料中找到依据，没有越界扩展。",
        "score_1": "大体基于材料，但有轻微外推。",
        "score_0": "明显引入材料外事实或臆断。",
        "checklist": ["是否出现材料未提供的事实", "外推是否过度", "结论是否受材料支撑"],
    },
    "FV-11": {
        "focus": "判断是否引用了具体财务指标和具体数值。",
        "score_2": "明确出现财务指标名及对应数值。",
        "score_1": "有指标或有数值，但结合不完整。",
        "score_0": "没有具体财务指标数据。",
        "checklist": ["是否有指标名称", "是否有对应数字", "指标与分析是否相关"],
    },
    "FV-12": {
        "focus": "判断是否存在定量分析，而不只是定性描述。",
        "score_2": "有明确数值比较、趋势推演、比例或量化论证。",
        "score_1": "有少量量化成分，但较弱。",
        "score_0": "几乎完全是定性描述。",
        "checklist": ["是否使用数值/比例/变化幅度", "是否基于数值做比较或推理", "量化内容是否支撑结论"],
    },
    "FN-12": {
        "focus": "判断是否避免对非金融领域术语使用英文。",
        "score_2": "仅保留必要金融术语英文，其他表达基本中文化。",
        "score_1": "大体满足，但仍有少量无必要英文。",
        "score_0": "存在明显可替换的非金融英文表达。",
        "checklist": ["英文是否主要是金融领域术语", "非金融表达能否中文替换", "英文使用是否克制"],
    },
    "FN-13": {
        "focus": "判断回答是否达到一定专业金融术语密度。",
        "score_2": "金融术语数量充足，且使用自然贴切。",
        "score_1": "有一定术语，但数量或专业性偏弱。",
        "score_0": "术语数量明显不足。",
        "checklist": ["金融术语是否足够多", "术语是否为真实专业术语", "术语使用是否和任务相关"],
    },
    "FN-14": {
        "focus": "判断分析是否真正建立在指定市场环境前提下。",
        "score_2": "回答明确把给定市场环境作为分析前提，并影响结论或推理。",
        "score_1": "提到市场环境，但没有充分嵌入分析。",
        "score_0": "几乎忽略给定市场环境。",
        "checklist": ["是否提及该市场环境", "环境是否影响分析逻辑", "是否只是机械复述环境"],
    },
    "FN-15": {
        "focus": "判断回答是否以指定目标为首要考量，而非泛泛兼顾一切。",
        "score_2": "目标优先级清晰，建议和分析明显围绕该目标组织。",
        "score_1": "提到目标，但优先级不够突出。",
        "score_0": "没有体现该目标是首要考量。",
        "checklist": ["是否明确优先级", "建议是否围绕该目标", "是否把所有目标平均对待"],
    },
    "FN-16": {
        "focus": "判断回答是否接近指定文档类型的风格。",
        "score_2": "结构、语气、表达方式明显符合指定文档类型。",
        "score_1": "有一定风格模仿，但不够稳定。",
        "score_0": "看不出指定文档风格。",
        "checklist": ["结构是否符合文档体裁", "语气是否匹配受众", "术语和格式是否贴近指定文体"],
    },
    "FN-17": {
        "focus": "判断分析是否真正建立在指定附加条件成立的前提下。",
        "score_2": "回答明确吸收该条件，并据此调整分析或建议。",
        "score_1": "提到条件，但条件对分析影响较弱。",
        "score_0": "忽略该条件或与条件无关。",
        "checklist": ["是否识别并使用给定条件", "条件是否改变推理链条", "是否只是机械重复条件"],
    },
}


RULE_TEMPLATE = """from verifier.rules._shared import {impl}


CONSTRAINT_ID = "{constraint_id}"
PARAM_NAMES = {param_names}


def check(response_text, params, context=None, meta=None):
    return {impl}(CONSTRAINT_ID, response_text, params)
"""


RUBRIC_TEMPLATE = """# {constraint_id}

- constraint_text: {constraint_text}
- description: {description}
- source: {source}
- verifiability: {verifiability}
- check_mode: {check_mode}
- score_type: {score_type}

## Judge Focus

{focus}

## {score_section_title}

- `10`: {score_2}
- `5`: {score_1}
- `0`: {score_0}

{score_section_note}

## Checklist

{checklist}
"""


def load_reference_rows():
    with REFERENCE_TABLE.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def ensure_dirs():
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    RUBRICS_DIR.mkdir(parents=True, exist_ok=True)


def rubric_section_meta(score_type: str) -> tuple[str, str]:
    if score_type == "ternary_10":
        return "Ternary 10 Rubric", ""
    if score_type == "continuous_10":
        return "Continuous 10 Anchors", "允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。"
    if score_type == "binary_10":
        return "Binary 10 Rubric", "只允许 `0` 或 `10`；`5` 仅作为保底占位，不应实际使用。"
    raise ValueError(f"未知 score_type: {score_type}")


def write_rule_file(row: dict[str, str]):
    constraint_id = row["constraint_id"]
    impl, param_names = RULE_IMPLS[constraint_id]
    content = RULE_TEMPLATE.format(
        impl=impl,
        constraint_id=constraint_id,
        param_names=param_names,
    )
    (RULES_DIR / f"{constraint_id}.py").write_text(content, encoding="utf-8")


def write_rubric_file(row: dict[str, str]):
    constraint_id = row["constraint_id"]
    spec = RUBRIC_SPECS[constraint_id]
    checklist = "\n".join(f"- {item}" for item in spec["checklist"])
    score_section_title, score_section_note = rubric_section_meta(row["score_type"])
    content = RUBRIC_TEMPLATE.format(
        constraint_id=constraint_id,
        constraint_text=row["constraint_text"],
        description=row["description"],
        source=row["source"],
        verifiability=row["verifiability"],
        check_mode=row["check_mode"],
        score_type=row["score_type"],
        focus=spec["focus"],
        score_section_title=score_section_title,
        score_2=spec["score_2"],
        score_1=spec["score_1"],
        score_0=spec["score_0"],
        score_section_note=score_section_note,
        checklist=checklist,
    )
    (RUBRICS_DIR / f"{constraint_id}.md").write_text(content, encoding="utf-8")


def main():
    ensure_dirs()
    rows = load_reference_rows()
    generated_rules = 0
    generated_rubrics = 0
    for row in rows:
        if row["check_mode"] == "rule":
            write_rule_file(row)
            generated_rules += 1
        elif row["check_mode"] == "rubric":
            write_rubric_file(row)
            generated_rubrics += 1
        else:
            raise ValueError(f"未知 check_mode: {row['check_mode']}")
    print(f"generated {generated_rules} rule files and {generated_rubrics} rubric files")


if __name__ == "__main__":
    main()
