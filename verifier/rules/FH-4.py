from __future__ import annotations

import re

from verifier.base import result_pass, result_fail


CONSTRAINT_ID = "FH-4"
PARAM_NAMES = ['N']

# 匹配数值：整数或小数（含负号、逗号千分位）
# 排除：年份(19xx/20xx后跟"年")、日期、纯序号(第N)
NUMBER_RE = re.compile(
    r"(?<![.\d])"           # 前面不是数字或小数点
    r"-?"                   # 可选负号
    r"\d[\d,]*"             # 整数部分（含千分位逗号）
    r"(?:\.\d+)?"           # 可选小数部分
    r"(?![.\d])"            # 后面不是数字或小数点
)

# 需要排除的模式
YEAR_RE = re.compile(r"(?:19|20)\d{2}(?=\s*[年/\-.])")   # 年份
ORDINAL_RE = re.compile(r"第\s*\d+")                       # 第N
DATE_COMPONENT_RE = re.compile(                             # 日期组件: X月/X日/X号
    r"\d{1,2}(?=\s*[月日号])"
)
REF_NUM_RE = re.compile(r"[编号第条款项]\s*\d+")            # 编号/条款号


def _is_excluded(text: str, match: re.Match) -> bool:
    """判断匹配到的数字是否应被排除（年份、日期、序号、列表编号、时间、品牌名等）"""
    start = match.start()
    end = match.end()
    val = match.group()

    # 年份: 19xx/20xx 后跟"年"或日期分隔符
    if YEAR_RE.match(text, start):
        return True

    # "第N" 序号
    if start >= 1 and text[start-1] == "第":
        return True
    if start >= 2 and text[start-2:start] == "第 ":
        return True

    # X月/X日/X号
    if end < len(text) and text[end] in "月日号":
        try:
            v = int(val.replace(",", ""))
            if 1 <= v <= 31:
                return True
        except ValueError:
            pass

    # 时间格式: HH:MM 中的数字（如 10:00、22:30）
    if end < len(text) and text[end] == ":":
        try:
            v = int(val)
            if 0 <= v <= 23:
                return True
        except ValueError:
            pass
    if start >= 1 and text[start-1] == ":":
        try:
            v = int(val)
            if 0 <= v <= 59:
                return True
        except ValueError:
            pass

    # 英文字母紧邻的数字（品牌名如 in77、R1-R5、ISO4217 等）
    if start >= 1 and text[start-1].isalpha():
        return True
    if end < len(text) and text[end].isalpha():
        return True

    # 列表编号: 行首的 "1." "2)" "3）" "3、" "(1)" "（2）" 等
    line_start = text.rfind("\n", 0, start) + 1
    prefix = text[line_start:start].strip()
    suffix_char = text[end] if end < len(text) else ""
    if not prefix or prefix in ("- ", "* ", "• "):
        if suffix_char in ".)）、":
            return True
    # （N）(N) 格式
    if start >= 1 and text[start-1] in "（(" and end < len(text) and text[end] in "）)":
        return True

    # 连续12年、第3季度 等修饰性数字（"连续N年"）
    if end < len(text) and text[end] in "年季个条项份次篇章节步家天周场位人名":
        try:
            v = int(val.replace(",", ""))
            if v <= 100:
                return True
        except ValueError:
            pass

    return False


def _decimal_places(num_str: str) -> int:
    """返回数字字符串的小数位数"""
    if "." in num_str:
        return len(num_str.split(".")[-1])
    return 0


def check(response_text: str, params: dict, context=None, meta=None):
    n = int(params["N"])
    numbers = []
    violations = []

    for m in NUMBER_RE.finditer(response_text):
        if _is_excluded(response_text, m):
            continue
        raw = m.group()
        # 去掉千分位逗号
        clean = raw.replace(",", "")
        try:
            float(clean)
        except ValueError:
            continue
        numbers.append(raw)
        dp = _decimal_places(clean)
        if dp != n:
            violations.append(f"{raw}({dp}位)")

    if not numbers:
        return result_fail(
            CONSTRAINT_ID,
            f"未找到数值，无法验证小数位数",
            actual="无数值",
            expected=f"保留{n}位小数",
        )

    if violations:
        shown = violations[:5]
        extra = f"...等{len(violations)}处" if len(violations) > 5 else ""
        return result_fail(
            CONSTRAINT_ID,
            f"小数位数不符: {', '.join(shown)}{extra}",
            actual=f"{len(violations)}/{len(numbers)}不符",
            expected=f"全部保留{n}位小数",
        )

    return result_pass(
        CONSTRAINT_ID,
        f"全部{len(numbers)}个数值均保留{n}位小数",
        actual=f"{n}位小数",
        expected=f"{n}位小数",
    )
