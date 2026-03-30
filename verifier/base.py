from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any


SENTENCE_SEP_RE = re.compile(r"[。！？!?；;]+")
HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+\S")
NUMBER_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?%?")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$")
CHECKBOX_RE = re.compile(r"(?m)^\s*[-*+]?\s*\[(?: |x|X)\]\s+")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")


@dataclass
class CheckResult:
    constraint_id: str
    status: str
    passed: bool | None
    score: float | None
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def result_pass(constraint_id: str, message: str, **evidence: Any) -> CheckResult:
    return CheckResult(
        constraint_id=constraint_id,
        status="pass",
        passed=True,
        score=10.0,
        message=message,
        evidence=evidence,
    )


def result_fail(constraint_id: str, message: str, **evidence: Any) -> CheckResult:
    return CheckResult(
        constraint_id=constraint_id,
        status="fail",
        passed=False,
        score=0.0,
        message=message,
        evidence=evidence,
    )


def result_inconclusive(constraint_id: str, message: str, **evidence: Any) -> CheckResult:
    return CheckResult(
        constraint_id=constraint_id,
        status="inconclusive",
        passed=None,
        score=None,
        message=message,
        evidence=evidence,
    )


def nonempty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def char_count_no_space(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def sentence_count(text: str) -> int:
    parts = [part.strip() for part in SENTENCE_SEP_RE.split(text) if part.strip()]
    return len(parts)


def paragraph_count(text: str) -> int:
    parts = [part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()]
    return len(parts)


def first_word(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    match = re.match(r"([A-Za-z]+|[\u4e00-\u9fff]{1,8})", stripped)
    return match.group(1) if match else stripped.split()[0]


def markdown_heading_levels(text: str) -> set[int]:
    return {len(match.group(1)) for match in HEADING_RE.finditer(text)}


def has_markdown_table(text: str) -> bool:
    lines = text.splitlines()
    for idx in range(len(lines) - 1):
        if "|" in lines[idx] and TABLE_SEPARATOR_RE.match(lines[idx + 1].strip()):
            return True
    return False


def has_checkbox(text: str) -> bool:
    return CHECKBOX_RE.search(text) is not None


def has_code_or_formula_block(text: str) -> bool:
    return "```" in text or "$$" in text


def bullet_items(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        match = BULLET_RE.match(line)
        if match:
            items.append(match.group(1).strip())
    return items


def load_json_if_possible(text: str) -> tuple[bool, Any]:
    try:
        return True, json.loads(text)
    except Exception:
        return False, None


def extract_numbers(text: str) -> list[float]:
    values: list[float] = []
    for token in NUMBER_RE.findall(text):
        clean = token.replace(",", "").replace("%", "")
        try:
            values.append(float(clean))
        except ValueError:
            continue
    return values


def last_nonempty_line(text: str) -> str:
    lines = nonempty_lines(text)
    return lines[-1] if lines else ""


def first_nonempty_line(text: str) -> str:
    lines = nonempty_lines(text)
    return lines[0] if lines else ""
