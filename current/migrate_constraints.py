"""One-time migration: convert low-discrimination hard constraints to soft."""

import json

CHECKERS_TO_CONVERT = {
    'check_has_calculation',
    'check_arithmetic_correct',
    'check_field_coverage',
    'check_keyword_presence',
    'check_markdown_table',
}

RUBRIC_TEMPLATES = {
    'check_has_calculation': (
        "检查输出是否完整展示了{desc_core}，包括："
        "1）引用了context中的原始数据；"
        "2）列出了计算公式或步骤；"
        "3）计算结果数值正确。"
        "仅出现最终数字而无推导过程应判FAIL。"
    ),
    'check_arithmetic_correct': (
        "检查输出中的算术运算是否正确，包括："
        "1）加减乘除运算结果准确；"
        "2）百分比、比率等计算无误。"
        "{desc_core}。"
    ),
    'check_field_coverage': (
        "检查输出是否覆盖了所有必需的信息字段。{desc_core}。"
        "遗漏关键字段应判FAIL。"
    ),
    'check_keyword_presence': (
        "检查输出中是否包含必要的关键术语或概念。{desc_core}。"
        "缺少核心关键词应判FAIL。"
    ),
    'check_markdown_table': (
        "检查输出是否以清晰的表格形式呈现数据。{desc_core}。"
        "数据应结构化展示，便于阅读和对比。"
    ),
}


def extract_desc_core(description):
    """Extract the core part of the description for rubric generation."""
    for prefix in ['展示了', '包含了', '输出包含', '使用了', '输出为']:
        if description.startswith(prefix):
            return description[len(prefix):]
    return description


def migrate(config_path):
    with open(config_path) as f:
        config = json.load(f)

    converted = 0
    for cid, c in config['constraints'].items():
        if c.get('type') != 'hard':
            continue
        checker = c.get('checker', '')
        if checker not in CHECKERS_TO_CONVERT:
            continue

        desc = c.get('description', '')
        desc_core = extract_desc_core(desc)
        template = RUBRIC_TEMPLATES[checker]
        rubric = template.format(desc_core=desc_core)

        c['type'] = 'soft'
        c['rubric'] = rubric
        c.pop('checker', None)
        c.pop('params', None)
        converted += 1

    with open(config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write('\n')

    hard = sum(1 for c in config['constraints'].values() if c['type'] == 'hard')
    soft = sum(1 for c in config['constraints'].values() if c['type'] == 'soft')
    print(f"Converted {converted} hard → soft")
    print(f"New distribution: {hard} hard / {soft} soft (total {hard + soft})")


if __name__ == '__main__':
    migrate('eval_config_all.json')
