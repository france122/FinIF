"""
FinIF Benchmark — Code Checker Library
所有 checker 函数签名统一：def check_xxx(output: str, params: dict = None) -> bool
"""
import re
import json


# ============================================================
# Format Checkers
# ============================================================

def check_markdown_table(output, params=None):
    lines = [l.strip() for l in output.strip().splitlines() if l.strip()]
    for line in lines:
        if re.match(r'^\|.*\|$', line) and '---' not in line:
            return True
    return False


def check_json_format(output, params=None):
    text = output.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def check_json_structure(output, params=None):
    text = output.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return all(isinstance(k, str) for k in obj.keys())
        if isinstance(obj, list):
            return len(obj) > 0 and all(isinstance(item, dict) for item in obj)
        return False
    except (json.JSONDecodeError, ValueError):
        return False


def check_list_format(output, params=None):
    lines = [l.strip() for l in output.strip().splitlines() if l.strip()]
    list_lines = [l for l in lines if re.match(r'^(\d+[.、)）]|-|\*)\s', l)]
    return len(list_lines) >= 2


def check_numbered_list(output, params=None):
    params = params or {}
    min_items = params.get('min_items', 1)
    lines = [l.strip() for l in output.strip().splitlines() if l.strip()]
    numbered = [l for l in lines if re.match(r'^\d+[.、)）]\s', l)]
    return len(numbered) >= min_items


def check_two_tables(output, params=None):
    table_blocks = re.findall(r'(\|[^\n]+\|\n(?:\|[^\n]+\|\n?)+)', output)
    return len(table_blocks) >= 2


def check_qa_format(output, params=None):
    has_q = bool(re.search(r'(Q[:：]|问[:：]|问题[:：])', output))
    has_a = bool(re.search(r'(A[:：]|答[:：]|回[复答][:：])', output))
    return has_q and has_a


def check_markdown_format(output, params=None):
    patterns = [
        r'^#{1,4}\s',
        r'\*\*.+?\*\*',
        r'^\|.+\|',
        r'^[-*]\s',
        r'^\d+[.、)]\s',
    ]
    for line in output.strip().splitlines():
        for pat in patterns:
            if re.search(pat, line.strip()):
                return True
    return False


def check_checkbox_format(output, params=None):
    checked = len(re.findall(r'\[x\]|\[X\]', output))
    unchecked = len(re.findall(r'\[ \]|\[\]', output))
    return (checked + unchecked) >= 1


# ============================================================
# Content Checkers
# ============================================================

def check_no_extra(output, params=None):
    text = output.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()
    non_content_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('|') or line.startswith('{') or line.startswith('[') or line.startswith('}') or line.startswith(']'):
            continue
        if re.match(r'^[\-\|:]+$', line):
            continue
        if line.startswith('```'):
            continue
        if line.startswith('"') and (line.endswith('"') or line.endswith(',')):
            continue
        non_content_lines.append(line)
    return len(non_content_lines) == 0


def check_field_coverage(output, params=None):
    params = params or {}
    if 'required_fields' in params:
        for field in params['required_fields']:
            if field not in output:
                return False
        return True
    if 'min_rows' in params:
        rows = re.findall(r'^\|(?!\s*[-:]+\s*\|)', output, re.MULTILINE)
        header_count = 1
        return len(rows) - header_count >= params['min_rows']
    return True


def _normalize_value_to_number(val_str):
    """Normalize a value string with Chinese units to a raw number.
    '1,856万' → 18560000.0, '3.5亿' → 350000000.0, '8500' → 8500.0
    Returns (float, True) on success, (None, False) on failure.
    """
    s = val_str.replace(',', '').replace('，', '').replace('%', '').replace('％', '')
    multiplier = 1
    if '万亿' in s:
        multiplier = 1e12
        s = s.replace('万亿', '')
    elif '百万' in s:
        multiplier = 1e6
        s = s.replace('百万', '')
    elif '亿' in s:
        multiplier = 1e8
        s = s.replace('亿', '')
    elif '万' in s:
        multiplier = 1e4
        s = s.replace('万', '')
    s = re.sub(r'[元股份]', '', s).strip()
    try:
        return float(s) * multiplier, True
    except ValueError:
        return None, False


def check_value_exact(output, params=None):
    """Check key-value pairs appear together in the output.
    For each (key, value) in expected_values, finds a line (or nearby text)
    where both the key (or a recognizable variant) and the value co-occur.
    Supports numeric normalization: '1,856万' matches '18,560,000'.
    """
    params = params or {}
    expected = params.get('expected_values', {})
    output_no_comma = output.replace(',', '').replace('，', '')
    lines = output_no_comma.split('\n')

    for key, val in expected.items():
        val_str = str(val).replace(',', '')
        val_bare = val_str.replace('%', '').replace('％', '')
        val_candidates = {val_str, val_bare} - {''}

        expected_num, has_num = _normalize_value_to_number(str(val))

        key_clean = key.replace(',', '')
        key_variants = {key_clean}
        m = re.match(r'^(.+?)(CPI|收益率|涨跌幅|涨幅|基金|指数|净利润|营收)$', key_clean)
        if m:
            key_variants.add(m.group(1).strip())
        m2 = re.search(r'(\d{4})[年\-/](\d{1,2})[月]?', key_clean)
        if m2:
            y, mo = m2.group(1), m2.group(2)
            key_variants.add(f"{y}-{mo.zfill(2)}")
            key_variants.add(f"{y}年{mo.zfill(2)}月")
            key_variants.add(f"{y}年{mo}月")
        m3 = re.search(r'(\d{4})', key_clean)
        if m3:
            key_variants.add(m3.group(1))

        found = False

        def _check_val_in_text(text):
            if any(vc in text for vc in val_candidates):
                return True
            if has_num and expected_num is not None:
                abs_expected = abs(expected_num)
                nums = re.findall(r'[-+]?[\d]+\.?\d*', text)
                for n_str in nums:
                    try:
                        n_val = float(n_str)
                        if expected_num != 0:
                            if abs(n_val - expected_num) / abs(expected_num) < 0.001:
                                return True
                            if abs(abs(n_val) - abs_expected) / abs_expected < 0.001:
                                return True
                        elif abs(n_val) < 0.001:
                            return True
                    except ValueError:
                        continue
            return False

        for line in lines:
            line_lower = line.strip()
            if not line_lower:
                continue
            key_hit = any(kv in line_lower for kv in key_variants)
            if not key_hit:
                key_chars = set(key_clean) - set(' \t')
                if key_chars and all(c in line_lower for c in key_chars):
                    key_hit = True
            if key_hit and _check_val_in_text(line_lower):
                found = True
                break

        if not found:
            for i in range(len(lines) - 1):
                block = lines[i] + ' ' + lines[i + 1]
                key_hit = any(kv in block for kv in key_variants)
                if key_hit and _check_val_in_text(block):
                    found = True
                    break

        if not found:
            return False
    return True


def check_keyword_presence(output, params=None):
    params = params or {}
    keywords = params.get('required_keywords', [])
    match_all = params.get('match_all', True)
    if match_all:
        return all(kw in output for kw in keywords)
    else:
        return any(kw in output for kw in keywords)


def check_keyword_absence(output, params=None):
    params = params or {}
    forbidden = params.get('forbidden_keywords', [])
    return not any(kw in output for kw in forbidden)


def check_filter(output, params=None):
    params = params or {}
    exclude = params.get('exclude_keywords', [])
    for kw in exclude:
        if kw in output:
            return False
    return True


# ============================================================
# Structure Checkers
# ============================================================

def check_header_row(output, params=None):
    params = params or {}
    expected = params.get('expected_header', [])
    lines = output.strip().splitlines()
    for line in lines:
        if line.strip().startswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(h in cells for h in expected):
                return True
    return False


def check_section_count(output, params=None):
    params = params or {}
    min_sections = params.get('min_sections', 1)
    section_patterns = [
        r'^#{1,4}\s',
        r'^[一二三四五六七八九十]+[、.]\s',
        r'^\d+[.、]\s+\S',
        r'^【.+】',
    ]
    count = 0
    for line in output.strip().splitlines():
        line = line.strip()
        for pat in section_patterns:
            if re.match(pat, line):
                count += 1
                break
    return count >= min_sections


def check_section_titles(output, params=None):
    params = params or {}
    required = params.get('required_titles', [])
    return all(title in output for title in required)


def check_table_row_count(output, params=None):
    params = params or {}
    rows = re.findall(r'^\|(?!\s*[-:]+\s*\|)', output, re.MULTILINE)
    data_rows = max(0, len(rows) - 1)
    if 'exact_rows' in params:
        return data_rows == params['exact_rows']
    if 'min_rows' in params:
        return data_rows >= params['min_rows']
    return True


def check_table_column_names(output, params=None):
    params = params or {}
    required = params.get('required_columns', [])
    lines = output.strip().splitlines()
    for line in lines:
        if line.strip().startswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if all(col in cells for col in required):
                return True
    return False


def check_table_sort_alpha(output, params=None):
    params = params or {}
    col_idx = params.get('column_index', 0)
    lines = output.strip().splitlines()
    table_lines = [l for l in lines if l.strip().startswith('|')]
    if len(table_lines) < 3:
        return False
    sep_idx = None
    for i, l in enumerate(table_lines):
        if re.match(r'^\|\s*[-:]+', l.strip()):
            sep_idx = i
            break
    if sep_idx is None:
        return False
    data_lines = []
    for l in table_lines[sep_idx + 1:]:
        if re.match(r'^\|\s*[-:]+', l.strip()):
            break
        data_lines.append(l)
    if len(data_lines) > 1 and not any(c.isdigit() for c in data_lines[0].split('|')[1].strip() if c):
        data_lines = data_lines[1:]
    values = []
    for line in data_lines:
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if col_idx < len(cells) and cells[col_idx]:
            values.append(cells[col_idx])
    if not values:
        return False
    return values == sorted(values)


# ============================================================
# Sorting Checkers
# ============================================================

def check_sort_date(output, params=None):
    params = params or {}
    order = params.get('order', 'asc')
    date_pattern = r'(\d{4})[-/年](\d{1,2})[-/月]?(\d{0,2})[日]?'
    dates_raw = re.findall(date_pattern, output)
    if len(dates_raw) < 2:
        return True
    date_tuples = []
    for y, m, d in dates_raw:
        date_tuples.append((int(y), int(m), int(d) if d else 1))
    if order == 'desc':
        return all(date_tuples[i] >= date_tuples[i+1] for i in range(len(date_tuples)-1))
    return all(date_tuples[i] <= date_tuples[i+1] for i in range(len(date_tuples)-1))


def check_sort_value_desc(output, params=None):
    params = params or {}
    col_idx = params.get('column_index', None)
    if col_idx is not None:
        lines = output.strip().splitlines()
        table_lines = [l for l in lines if l.strip().startswith('|')]
        if len(table_lines) < 3:
            return False
        data_lines = [l for l in table_lines[2:] if not re.match(r'^\|\s*[-:]+', l)]
        values = []
        for line in data_lines:
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if col_idx < len(cells):
                nums = re.findall(r'[-+]?\d[\d,]*\.?\d*', cells[col_idx])
                if nums:
                    values.append(float(nums[0].replace(',', '')))
        if len(values) < 2:
            return True
        return all(values[i] >= values[i+1] for i in range(len(values)-1))
    numbers = re.findall(r'[-+]?\d[\d,]*\.?\d*', output)
    nums = [float(n.replace(',', '')) for n in numbers if n.replace(',', '').replace('.', '').replace('-', '').replace('+', '').isdigit() or '.' in n]
    if len(nums) < 2:
        return True
    return all(nums[i] >= nums[i+1] for i in range(len(nums)-1))


# ============================================================
# Text Checkers
# ============================================================

def check_word_limit(output, params=None):
    params = params or {}
    max_words = params.get('max_words', 99999)
    cn_chars = len(re.findall(r'[一-鿿]', output))
    en_words = len(re.findall(r'[a-zA-Z]+', output))
    word_count = cn_chars + en_words
    return word_count <= max_words


def check_word_range(output, params=None):
    params = params or {}
    min_words = params.get('min_words', 0)
    max_words = params.get('max_words', 99999)
    cn_chars = len(re.findall(r'[一-鿿]', output))
    en_words = len(re.findall(r'[a-zA-Z]+', output))
    word_count = cn_chars + en_words
    return min_words <= word_count <= max_words


def check_lang_cn(output, params=None):
    cn_chars = len(re.findall(r'[一-鿿]', output))
    total_alpha = len(re.findall(r'[a-zA-Z]', output))
    if cn_chars + total_alpha == 0:
        return False
    return cn_chars / (cn_chars + total_alpha + 0.001) > 0.5


def check_bold_values(output, params=None):
    return bool(re.search(r'\*\*\d+', output))


def check_first_row(output, params=None):
    params = params or {}
    keyword = params.get('keyword', '')
    lines = output.strip().splitlines()
    table_lines = [l for l in lines if l.strip().startswith('|') and '---' not in l]
    if len(table_lines) >= 2:
        return keyword in table_lines[1]
    return False


def check_last_row(output, params=None):
    params = params or {}
    keyword = params.get('keyword', '')
    lines = output.strip().splitlines()
    table_lines = [l for l in lines if l.strip().startswith('|') and '---' not in l]
    if len(table_lines) >= 2:
        return keyword in table_lines[-1]
    return False


def check_direction_label(output, params=None):
    return bool(re.search(r'(上升|上涨|增长|下降|下跌|减少|持平|不变|流入|流出|买入|卖出|增加|降低)', output))


# ============================================================
# Conclusion / Label Checkers
# ============================================================

def check_conclusion_label(output, params=None):
    params = params or {}
    labels = params.get('labels', [])
    if not labels:
        return True
    found = sum(1 for label in labels if label in output)
    return found >= 1


def check_ordered_list_count(output, params=None):
    params = params or {}
    exact = params.get('exact_count', None)
    min_count = params.get('min_count', None)
    max_count = params.get('max_count', None)
    items = re.findall(r'^\d+[.、)）]\s', output, re.MULTILINE)
    count = len(items)
    if exact is not None:
        return count == exact
    ok = True
    if min_count is not None:
        ok = ok and count >= min_count
    if max_count is not None:
        ok = ok and count <= max_count
    return ok


def check_item_word_limit(output, params=None):
    params = params or {}
    max_chars = params.get('max_chars', 9999)
    items = re.findall(r'^\d+[.、)）]\s*(.+)$', output, re.MULTILINE)
    if not items:
        return True
    return all(len(item.strip()) <= max_chars for item in items)


def check_json_field_count(output, params=None):
    params = params or {}
    field = params.get('field', None)
    exact_count = params.get('exact_count', None)
    text = output.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()
    try:
        obj = json.loads(text)
        if field and isinstance(obj, dict) and field in obj:
            target = obj[field]
            if isinstance(target, list) and exact_count is not None:
                return len(target) == exact_count
        elif isinstance(obj, list) and exact_count is not None:
            return len(obj) == exact_count
        elif isinstance(obj, dict) and exact_count is not None:
            return len(obj) == exact_count
    except (json.JSONDecodeError, ValueError):
        return False
    return True


def check_json_field_item_limit(output, params=None):
    params = params or {}
    field = params.get('field', None)
    max_chars = params.get('max_chars', 9999)
    text = output.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()
    try:
        obj = json.loads(text)
        if field and isinstance(obj, dict) and field in obj:
            items = obj[field]
            if isinstance(items, list):
                return all(len(str(item)) <= max_chars for item in items)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def check_json_field_word_limit(output, params=None):
    params = params or {}
    field = params.get('field', '')
    max_chars = params.get('max_chars', 9999)
    text = output.strip()
    if text.startswith('```'):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and field in obj:
            return len(str(obj[field])) <= max_chars
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def check_email_in_last_line(output, params=None):
    lines = [l.strip() for l in output.strip().splitlines() if l.strip()]
    if not lines:
        return False
    return bool(re.search(r'[\w.-]+@[\w.-]+\.\w+', lines[-1]))


def check_has_calculation(output, params=None):
    calc_patterns = [
        r'\d+\s*[+\-×÷*/]\s*\d+',
        r'\d+\s*=\s*\d+',
        r'[\d,.]+\s*[-/]\s*[\d,.]+\s*=',
        r'(计算|差额|差值|合计|累计|总计)',
    ]
    return any(re.search(p, output) for p in calc_patterns)


# ============================================================
# Evidence-based Verification Checkers
# ============================================================

def _normalize_number(s):
    """Remove commas/spaces/units from a number string, return float."""
    s = re.sub(r'[,，\s]', '', s)
    s = re.sub(r'[%％万亿元股份]', '', s)
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return None


def _extract_numbers(text):
    """Extract all numbers (with optional commas/decimals/signs) from text."""
    return re.findall(r'[-+]?[\d,]+\.?\d*', text)


def check_arithmetic_correct(output, params=None):
    """Verify model shows correct arithmetic. Two modes:
    1. expressions mode: check specific expressions exist with correct results
    2. auto mode: find all 'A op B = C' patterns and verify each
    """
    params = params or {}
    expressions = params.get('expressions', [])

    if expressions:
        output_clean = output.replace(',', '').replace('，', '')
        all_pass = True
        for expr in expressions:
            left = str(expr.get('left', ''))
            expected = str(expr.get('expected', ''))
            expected_val = _normalize_number(expected)
            if expected_val is None:
                continue
            if expected not in output_clean and str(int(expected_val)) not in output_clean:
                all_pass = False
                continue
            try:
                computed = eval(left)
                if abs(computed - expected_val) > 0.01:
                    all_pass = False
            except Exception:
                pass
        return all_pass

    # Auto mode: find "A ± B = C" patterns and verify
    patterns = [
        r'([\d,]+\.?\d*)\s*[-－]\s*([\d,]+\.?\d*)\s*[=＝]\s*([\d,]+\.?\d*)',
        r'([\d,]+\.?\d*)\s*[+＋]\s*([\d,]+\.?\d*)\s*[=＝]\s*([\d,]+\.?\d*)',
    ]
    found = False
    all_correct = True
    for pat in patterns:
        for m in re.finditer(pat, output):
            found = True
            a = _normalize_number(m.group(1))
            b = _normalize_number(m.group(2))
            c = _normalize_number(m.group(3))
            if a is None or b is None or c is None:
                continue
            if '-' in pat or '－' in pat:
                if abs((a - b) - c) > 0.5:
                    all_correct = False
            else:
                if abs((a + b) - c) > 0.5:
                    all_correct = False
    if not found:
        return False
    return all_correct


def check_value_derivation(output, params=None):
    """Verify derived values (percentages, ratios) are correctly computed.
    params.checks: list of {formula, expected, tolerance, label}
    - formula: Python expression to evaluate (e.g., "(156823-132456)/132456")
    - expected: expected result (e.g., 0.1841)
    - tolerance: acceptable deviation (e.g., 0.005)
    - label: the string to look for in output (e.g., "18.41%")
    """
    params = params or {}
    checks = params.get('checks', [])
    if not checks:
        return False

    all_pass = True
    for check in checks:
        label = check.get('label', '')
        formula = check.get('formula', '')
        expected = check.get('expected', 0)
        tolerance = check.get('tolerance', 0.01)

        label_clean = label.replace('%', '').replace('％', '').strip()
        output_clean = output.replace(',', '').replace('，', '')
        if label_clean not in output_clean:
            all_pass = False
            continue

        if formula:
            try:
                computed = eval(formula)
                if abs(computed - expected) > tolerance:
                    all_pass = False
            except Exception:
                pass

    return all_pass


def check_source_fidelity(output, params=None):
    """Check that numbers in output trace back to source context.
    Extracts all numbers from output, verifies most exist in context_values
    or can be derived from them (sums, differences, percentages).
    """
    params = params or {}
    context_values = params.get('context_values', [])
    allow_derived = params.get('allow_derived', True)
    max_foreign_ratio = params.get('max_foreign_ratio', 0.3)

    if not context_values:
        return True

    ctx_nums = set()
    for v in context_values:
        n = _normalize_number(str(v))
        if n is not None:
            ctx_nums.add(n)

    if allow_derived:
        derived = set()
        ctx_list = list(ctx_nums)
        for i in range(len(ctx_list)):
            for j in range(len(ctx_list)):
                if i == j:
                    continue
                derived.add(round(ctx_list[i] + ctx_list[j], 4))
                derived.add(round(ctx_list[i] - ctx_list[j], 4))
                if ctx_list[j] != 0:
                    derived.add(round(ctx_list[i] / ctx_list[j], 4))
                    derived.add(round(ctx_list[i] / ctx_list[j] * 100, 4))
        ctx_nums.update(derived)

    output_nums = _extract_numbers(output)
    if not output_nums:
        return True

    significant_nums = []
    for n_str in output_nums:
        n = _normalize_number(n_str)
        if n is not None and abs(n) >= 1:
            significant_nums.append(n)

    if not significant_nums:
        return True

    foreign = 0
    for n in significant_nums:
        matched = False
        for ctx_n in ctx_nums:
            if abs(ctx_n) < 0.001:
                continue
            if abs(n - ctx_n) / max(abs(ctx_n), 1) < 0.01:
                matched = True
                break
        if not matched:
            foreign += 1

    foreign_ratio = foreign / len(significant_nums)
    return foreign_ratio <= max_foreign_ratio


# ============================================================
# Computation & Reasoning Checkers
# ============================================================

def check_computation_result(output, params=None):
    """Verify output contains specific computed results within tolerance.
    Searches the entire output for expected numeric values, independent of labels.
    Also tries unit-scaled variants (×10000 for 万, ×1e8 for 亿).
    params.results: list of {label, expected, tolerance, unit}
    """
    params = params or {}
    results = params.get('results', [])
    if not results:
        return False

    output_clean = output.replace(',', '').replace('，', '')
    all_nums = re.findall(r'[-+]?\d+\.?\d*', output_clean)
    all_vals = []
    for n_str in all_nums:
        try:
            all_vals.append(float(n_str))
        except ValueError:
            continue

    for item in results:
        expected = float(item.get('expected', 0))
        tolerance = float(item.get('tolerance', 0.5))
        candidates = [expected]
        if expected != 0:
            candidates.append(expected * 10000)
            candidates.append(expected / 10000)
            candidates.append(expected * 1e8)
            candidates.append(expected / 1e8)
        scaled_tolerances = [tolerance, tolerance * 10000, tolerance / 10000, tolerance * 1e8, tolerance / 1e8]

        found = False
        for exp, tol in zip(candidates, scaled_tolerances):
            if any(abs(v - exp) <= tol for v in all_vals):
                found = True
                break
        if not found:
            return False

    return True


def check_ranking(output, params=None):
    """Verify items appear in a specific order in the output.
    params.ranking: list of strings in expected order
    params.criterion: description of the ranking criterion (for documentation)
    """
    params = params or {}
    ranking = params.get('ranking', [])
    if len(ranking) < 2:
        return True

    positions = []
    for item in ranking:
        pos = output.find(item)
        if pos == -1:
            return False
        positions.append(pos)

    for i in range(len(positions) - 1):
        if positions[i] >= positions[i + 1]:
            return False
    return True


def check_judgment(output, params=None):
    """Verify output contains expected judgment conclusions.
    params.expected_conclusions: list of {keyword, context, alternatives}
    - keyword: primary keyword to look for
    - context: optional context near which keyword should appear
    - alternatives: optional list of alternative acceptable keywords
    """
    params = params or {}
    conclusions = params.get('expected_conclusions', [])
    if not conclusions:
        return True

    all_pass = True
    for item in conclusions:
        keyword = item.get('keyword', '')
        alternatives = item.get('alternatives', [])
        context = item.get('context', '')

        candidates = [keyword] + alternatives
        found = False
        for cand in candidates:
            if not cand:
                continue
            if context:
                for line in output.split('\n'):
                    if context in line and cand in line:
                        found = True
                        break
                if not found:
                    block_size = 200
                    idx = output.find(context)
                    if idx >= 0:
                        region = output[max(0, idx - block_size):idx + len(context) + block_size]
                        if cand in region:
                            found = True
            else:
                if cand in output:
                    found = True
            if found:
                break

        if not found:
            all_pass = False

    return all_pass


def check_comparison(output, params=None):
    """Verify output compares two values and reaches the correct conclusion.
    params.comparisons: list of {larger, smaller, label}
    - larger: the item that should be identified as larger/higher
    - smaller: the item that should be identified as smaller/lower
    - label: what is being compared (for documentation)
    """
    params = params or {}
    comparisons = params.get('comparisons', [])
    if not comparisons:
        return True

    all_pass = True
    for comp in comparisons:
        larger = comp.get('larger', '')
        smaller = comp.get('smaller', '')
        if not larger or not smaller:
            continue
        larger_pos = output.find(larger)
        smaller_pos = output.find(smaller)
        if larger_pos == -1 or smaller_pos == -1:
            all_pass = False
            continue
        comparison_words = ['大于', '高于', '超过', '超出', '多于', '优于', '领先',
                          '小于', '低于', '不及', '落后', '少于', '弱于']
        region_start = min(larger_pos, smaller_pos)
        region_end = max(larger_pos, smaller_pos) + max(len(larger), len(smaller)) + 50
        region = output[region_start:region_end]
        if not any(w in region for w in comparison_words):
            all_pass = False

    return all_pass
