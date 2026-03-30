import json
import re
from typing import Any, Optional


SYSTEM_PROMPT = """\
你是一个中文金融 Instruction-Following (IF) benchmark 的高质量数据标注员。

## 你的唯一任务

为给定的约束模板填写参数值。你不需要回答 query，只需要为约束的占位符选择恰当的值。

## 核心机制

约束模板中有 {占位符}，你的值会被直接替换进去，形成最终约束文本。
例如：模板 = "回答不超过{n}个字"，你填 n=200，最终文本 = "回答不超过200个字"。

因此：你只填占位符本身的值，不要把模板中已有的词重复写进值里。

## 必须遵守的 8 条规则

1. **语义相关**：参数值必须和该条 query 的具体主题、行业、场景直接相关，而不是泛泛的金融通用词。
2. **不重复模板词**：你的值会被插入模板，所以不要在值里重复模板已有的前后文。
   - 模板 = "在{condition}这一假设下进行分析"
   - 错误: condition = "假设美联储加息50bp"（"假设"重复了）
   - 正确: condition = "美联储加息50bp"
3. **V 类可验证**：如果约束类型是 V（Verifiable），你填的值必须能被精确字符串匹配、正则表达式或计数规则直接验证。不能填模糊、歧义或需要语义判断的值。
4. **不泄露答案**：不要选择只有写出正确答案才会自然包含的内容。参数应该是对输出格式、结构或附加条件的要求，而非答案本身。
5. **有遵循难度**：选择有一定挑战性的参数值。不要选模型几乎一定会自然满足的值（太简单），也不要选明显不合理的值（太刁难）。
6. **具体而非宽泛**：每个参数都要足够具体，能被后续 verifier 直接使用。
   - 错误: currency_rule = "人民币"（太泛，无法做字符串检测）
   - 正确: currency_rule = "人民币元，格式为XX万元或XX亿元"
7. **简洁精确**：字符串参数控制在合理长度内，不要写成一整段话。
8. **仅输出 JSON**：只输出一个 JSON 对象，不要有任何解释、Markdown 格式、代码块或前后缀文字。
9. **禁止照抄示例**：如果下面出现示例，它们只用于说明“什么类型的值算好/算坏”，不是候选答案库。你必须根据当前 query 重新创作，不得直接复用示例中的名词、短语、文体名称或格式规则。
10. **优先场景化表达**：优先选择与当前 query 的具体资产类别、角色、业务流程、市场阶段直接相关的表达，而不是套用通用金融模板词。"""


# fmt: off
PARAMETRIC_CONSTRAINT_SPECS = {
    "GV-1": {
        "type": "V",
        "template": "回答不超过{n}个字",
        "params": ["n"],
        "prompt_guidance": """\
先判断这条 query 需要多长的回答才算充分但不冗余，然后给出一个有约束力的字数上限。
- 简单问答/单点建议：80-150
- 中等复杂度（多维度分析、含材料）：150-250
- 复杂多步骤任务：250-320

好的例子：{"n": 180}（对一条需要 3 个要点的建议题）
坏的例子：{"n": 300}（对一条"是否应该买入"的简单题——太宽松，几乎不构成约束）""",
        "int_ranges": {"n": (80, 320)},
    },
    "GV-2": {
        "type": "V",
        "template": "至少包含{n}个句子",
        "params": ["n"],
        "prompt_guidance": """\
根据 query 的复杂度判断回答至少需要几句话才算完整。
- 单点问题：2-3
- 多维度分析：4-5
- 不要给 1（太容易满足）也不要给 6 以上（对简单题不合理）

好的例子：{"n": 4}（对一条需要分析多个因素的建议题）
坏的例子：{"n": 2}（对一条明显需要展开论述的复杂题——太松）""",
        "int_ranges": {"n": (2, 6)},
    },
    "GV-3": {
        "type": "V",
        "template": "回答分为{n}个段落",
        "params": ["n"],
        "prompt_guidance": """\
根据 query 的输出结构需求决定段落数。
- 简短回答：2
- 标准分析（引言+主体+结论）：3
- 多角度/多步骤展开：4-5

好的例子：{"n": 3}（对一条投资建议题：开头概述+分析+结论）
坏的例子：{"n": 5}（对一条简单定义解释题——段落太多不自然）""",
        "int_ranges": {"n": (2, 5)},
    },
    "GV-4b": {
        "type": "V",
        "template": "包含至少{n}级标题层级",
        "params": ["n"],
        "prompt_guidance": """\
标题层级指 Markdown 中 #、##、### 等不同级别的使用。
- 大多数分析性任务：2 级就够（如 ## 和 ###）
- 内容复杂、需要多层组织的任务：3 级
- 极少给 4（只有非常复杂的报告类任务才合理）

好的例子：{"n": 2}（大多数情况下）
坏的例子：{"n": 4}（对一条简单建议题——过度复杂）""",
        "int_ranges": {"n": (2, 4)},
    },
    "GV-8": {
        "type": "V",
        "template": "\u5fc5\u987b\u5305\u542b\u5173\u952e\u8bcd\uff1a{kw1}\u3001{kw2}",
        "params": ["kw1", "kw2"],
        "prompt_guidance": """\
选择两个与该 query 主题直接相关的具体关键词。

选词原则：
- 必须是具体的金融概念、行业术语、产品名或分析维度，而非泛词
- 两个词应覆盖 query 的不同方面（如一个关于资产类型，一个关于分析角度）
- 不能是 query 文本中已经出现的原词（太容易满足）
- 不能是"分析""建议""风险""总结"这类几乎任何回答都会包含的万能词

形式参考（禁止直接复用其中的具体词语）：query="供应链金融和商业智能投资建议" -> {"kw1": "某个供应链金融子概念", "kw2": "某个数据分析相关概念"}
坏的例子：{"kw1": "金融", "kw2": "建议"}（太泛，任何回答都会包含）
坏的例子：{"kw1": "供应链金融", "kw2": "商业智能"}（直接复制 query 原词，太容易满足）""",
    },
    "GV-9": {
        "type": "V",
        "template": "\u4e0d\u5f97\u51fa\u73b0\u201c{word}\u201d",
        "params": ["word"],
        "prompt_guidance": """\
选择一个该 query 场景下模型很可能会自然使用、但按要求需要刻意规避的词或短语。

选词原则：
- 应该是模型回答该 query 时"顺手就会写"的高频词
- 但不能是无法绕开的核心概念（否则约束不合理）
- 填写的禁词不得与 query 题干中的关键词、实体名、产品名或核心任务词重合，否则会与题干直接冲突，导致约束失效
- 2-6 个字为宜

形式参考（禁止直接复用其中的具体词语）：选择一个模型高概率会自然写出、但仍可被其他近义表达替代的词。
坏的例子：{"word": "投资"}（query 本身就在讨论投资，完全无法回避）
坏的例子：{"word": "基金"}（如果 query 题干本身就在问基金配置，这会和 query 关键词直接冲突）
坏的例子：{"word": "的"}（语法虚词，没有遵循意义）""",
    },
    "GV-10": {
        "type": "V",
        "template": "\u5f00\u5934\u7b2c\u4e00\u4e2a\u8bcd\u5fc5\u987b\u662f\u201c{word}\u201d",
        "params": ["word"],
        "prompt_guidance": """\
选择一个作为回答第一个词自然合理、但不是模型默认首选的词。

选词原则：
- 必须是一个独立的中文词语（2-4 个字）
- 要与该 query 的任务类型匹配（建议题用"建议/结论"，诊断题用"问题/发现"，工具题用"步骤/方案"，销售题用"亮点/说明"）
- 不要选"首先""好的""当然"这类口语化开头
- 不同 query 之间应有变化，不要所有题都用同一个词

形式参考（禁止直接复用其中的具体词语）：工具类更适合“步骤/方案/实现”，分析类更适合“概览/结论/判断”这一类首词。
坏的例子：{"word": "好的"}（口语化，不符合正式书面语场景）
坏的例子：{"word": "首先"}（口语化套话）""",
    },
    "GV-13": {
        "type": "V",
        "template": "\u7b2c\u4e00\u884c\u5fc5\u987b\u4e3a\u201c{first_line}\u201d\uff0c\u6700\u540e\u4e00\u884c\u4e3a\u201c{last_line}\u201d",
        "params": ["first_line", "last_line"],
        "prompt_guidance": """\
为回答指定精确的首行文本和末行文本。Verifier 会做精确字符串匹配。

填写原则：
- first_line：应像文档标题或章节开头，与 query 任务类型匹配
  - 建议类：如 "## 投资配置建议"、"## 核心观点"
  - 诊断类：如 "## 风险诊断结果"、"## 问题分析"
  - 工具类：如 "## 实现方案"、"## 操作步骤"
- last_line：应是文档自然结尾，如免责提示或总结性收尾
  - 如 "以上分析仅供参考，不构成投资建议。"、"请结合实际情况审慎判断。"
- first_line 和 last_line 不能相同
- 不要太长（各 5-30 个字符为宜）
- 不要泄露具体答案内容

形式参考（禁止直接复用其中的具体文本）：first_line 应像该任务对应的文档标题；last_line 应像自然的合规收尾或执行收尾。
坏的例子：{"first_line": "你好", "last_line": "再见"}（太随意，与金融场景不匹配）""",
    },
    "GV-14": {
        "type": "V",
        "template": "\u6bcf\u4e2a bullet \u5fc5\u987b\u4ee5\u201c{prefix}\u201d\u5f00\u5934",
        "params": ["prefix"],
        "prompt_guidance": """\
指定列表中每个条目的统一前缀。Verifier 会检查每个 bullet 是否以该前缀开头。

填写原则：
- 前缀应以中文冒号结尾，如 "建议：""风险点：""步骤：""要点：""提示："
- 要与 query 任务类型匹配：
  - 建议类: "建议：" 或 "要点："
  - 诊断类: "发现：" 或 "风险点："
  - 工具类: "步骤：" 或 "操作："
  - 销售类: "亮点：" 或 "说明："
- 前缀长度 2-5 个字 + 冒号

形式参考（禁止直接复用其中的具体词语）：prefix 应是与任务类型匹配的短前缀，并以中文冒号结尾。
坏的例子：{"prefix": "1."}（编号不算内容前缀）""",
    },
    "FV-1": {
        "type": "V",
        "template": "\u672b\u5c3e\u5fc5\u987b\u5305\u542b\u98ce\u9669\u63d0\u793a\u58f0\u660e\uff1a{risk_line}",
        "params": ["risk_line"],
        "prompt_guidance": """\
为该 query 定制一句风险提示声明，会被 verifier 在回答末尾做精确字符串匹配。

填写原则：
- 必须是一句完整的、可独立成行的风险提示
- 应包含"风险""仅供参考""不构成...建议"中的至少一个要素
- 要与 query 涉及的具体金融场景适配（投资/贷款/保险/税务等）
- 长度 15-50 个字

形式参考（禁止直接复用其中的具体文本）：风险提示应是完整一句话，并且把场景风险写进去，而不是只写“注意风险”。
坏的例子：{"risk_line": "注意风险"}（太短太泛，不像正式合规声明）""",
    },
    "FV-2": {
        "type": "V",
        "template": "\u5fc5\u987b\u58f0\u660e\u201c{disclaimer}\u201d",
        "params": ["disclaimer"],
        "prompt_guidance": """\
为该 query 定制一句免责声明，verifier 做精确字符串匹配。

填写原则：
- 必须是一句完整的免责声明短句
- 典型格式："以上内容不构成XX建议""本分析仅供参考，不作为XX依据"
- 要与 query 场景匹配（投资建议/税务意见/信贷决策等）
- 长度 10-40 个字

形式参考（禁止直接复用其中的具体文本）：免责声明应根据任务类型变化，例如投资类、税务类、信贷类应分别有不同声明口径。
坏的例子：{"disclaimer": "仅供参考"}（太短，不是完整声明）""",
    },
    "FV-3": {
        "type": "V",
        "template": "\u82e5\u63d0\u5230\u201c{trigger}\u201d\uff0c\u5fc5\u987b\u540c\u65f6\u8865\u5145\u201c{followup}\u201d",
        "params": ["trigger", "followup"],
        "prompt_guidance": """\
设计一对"触发词 -> 必须补充的说明"规则。Verifier 先检测 trigger 是否出现，若出现则检测 followup 是否也出现。

填写原则：
- trigger：该 query 主题下回答中很可能出现的一个金融概念或产品名（2-6 个字）
- followup：与 trigger 配套的风险提醒或补充说明（10-35 个字）
- trigger 和 followup 不能相同
- followup 必须是自然、合规的补充，不能是废话

形式参考（禁止直接复用其中的具体词语）：trigger 应是回答里较可能出现的具体金融概念；followup 应是与之配套的风险提醒或补充说明。
坏的例子：{"trigger": "投资", "followup": "投资有风险"}（trigger 太泛，followup 太笼统）""",
    },
    "FV-4": {
        "type": "V",
        "template": "\u6309{order_field}\u4ece\u9ad8\u5230\u4f4e\u6392\u5e8f\u8f93\u51fa",
        "params": ["order_field"],
        "prompt_guidance": """\
指定回答中列表或表格的排序维度。Verifier 会检查输出是否按该字段降序排列。

填写原则：
- 排序字段必须是该 query 场景下有意义的量化或可比较维度
- 要足够具体，不能是"重要性"这种万能词（除非 query 确实在讨论优先级排序）
- 与 query 涉及的分析角度直接相关

形式参考（禁止直接复用其中的具体字段名）：排序字段应是与该 query 直接相关的可比较维度，而不是万能词。
坏的例子：{"order_field": "重要性"}（太泛，几乎对任何题都能用，没有针对性）""",
    },
    "FV-5": {
        "type": "V",
        "template": "\u82e5\u51fa\u73b0\u8d27\u5e01\u91d1\u989d\uff0c\u7edf\u4e00\u4f7f\u7528 {currency_rule} \u8868\u793a",
        "params": ["currency_rule"],
        "prompt_guidance": """\
指定回答中所有货币金额的统一表示规则。Verifier 会检测是否有不符合规则的金额表示。

填写原则：
- 必须是一条明确的、可用正则检测的格式规则，而不是单纯的币种名称
- 应包含：货币符号/代码 + 数字格式说明
- 要与 query 涉及的市场/币种匹配

形式参考（禁止直接复用其中的具体文本）：货币规则应写成“币种表示方式 + 数字格式要求”，必须是一条可检测的格式规则。
坏的例子：{"currency_rule": "人民币"}（太泛，不是格式规则，无法做字符串检测）
坏的例子：{"currency_rule": "美元"}（同上，只给了币种名）""",
    },
    "FN-13": {
        "type": "NV",
        "template": "\u81f3\u5c11\u5305\u542b{n}\u4e2a\u4e13\u4e1a\u91d1\u878d\u672f\u8bed",
        "params": ["n"],
        "prompt_guidance": """\
根据 query 的专业深度和所需回答的复杂度，决定至少需要多少个金融术语。
- 面向零售客户的简单解释：2-3
- 专业分析/诊断/研报类：4-5
- 高度技术性任务（量化/风控模型）：5-6

形式参考：面向零售客户的解释型任务通常术语数量更少，专业诊断/研报类任务通常术语数量更多。
坏的例子：{"n": 2}（对一条需要深度分析的复杂题——太松）""",
        "int_ranges": {"n": (2, 6)},
    },
    "FN-14": {
        "type": "NV",
        "template": "\u5047\u8bbe\u5f53\u524d\u5904\u4e8e{market_env}\u4e0b\u8fdb\u884c\u5206\u6790",
        "params": ["market_env"],
        "prompt_guidance": """\
为该 query 设定一个具体的市场环境假设。你的值会被插入"假设当前处于___下进行分析"。

关键规则：
- 不要在值中包含"假设""当前处于""下进行分析"等模板已有的词！
- 环境描述要具体、有画面感，不能太泛
- 要与 query 涉及的资产类别、行业或宏观背景匹配

形式参考（禁止直接复用其中的具体文本）：market_env 应写成某个具体市场阶段、板块环境或宏观流动性环境，最好是名词性短语。
坏的例子：{"market_env": "当前处于熊市"}（重复了模板中的"当前处于"）
坏的例子：{"market_env": "市场波动"}（太泛，几乎永远正确）""",
    },
    "FN-15": {
        "type": "NV",
        "template": "\u4ee5{goal}\u4e3a\u9996\u8981\u8003\u91cf",
        "params": ["goal"],
        "prompt_guidance": """\
为该 query 指定分析或建议的首要目标。你的值会被插入"以___为首要考量"。

关键规则：
- 不要在值中包含"以""为首要考量"等模板已有的词！
- 目标要具体且与 query 任务直接相关
- 应是一个明确的优先级方向，而非泛泛的"做好投资"

形式参考（禁止直接复用其中的具体文本）：goal 应是一个清晰的优先目标短语，不要写成模板句。
坏的例子：{"goal": "以风险最小化为首要考量"}（重复了模板词"以...为首要考量"）
坏的例子：{"goal": "做好投资"}（太泛，无实际指导意义）""",
    },
    "FN-16": {
        "type": "NV",
        "template": "\u4ee5{doc_style}\u7684\u98ce\u683c\u64b0\u5199",
        "params": ["doc_style"],
        "prompt_guidance": """\
为该 query 指定输出的文体风格。你的值会被插入"以___的风格撰写"。

关键规则：
- 不要在值中包含"以""的风格撰写"等模板已有的词！
- 文体要与 query 的角色和任务类型自然匹配
- 应是一个明确的文档类型名称

可选范围及适用场景：
- 券商研报 -> 证券分析类
- 客户说明函 / 投资顾问信 -> 面向客户的解释类
- 风控审查备忘录 -> 风险诊断类
- 内部合规提示 -> 合规/监管类
- 晨会纪要 -> 市场点评类
- 产品说明书 -> 产品介绍/销售类
- 投资备忘录 -> 内部决策类

形式参考（禁止直接复用其中的具体文体名）：doc_style 应是与任务目标和受众匹配的文档类型名称，而不是抽象形容词。
坏的例子：{"doc_style": "正式"}（不是文档类型，太泛）
坏的例子：{"doc_style": "以券商研报的风格撰写"}（重复了模板词）""",
    },
    "FN-17": {
        "type": "NV",
        "template": "\u5728{condition}\u8fd9\u4e00\u5047\u8bbe\u4e0b\u8fdb\u884c\u5206\u6790",
        "params": ["condition"],
        "prompt_guidance": """\
为该 query 设定一个具体的分析前提条件。你的值会被插入"在___这一假设下进行分析"。

关键规则（极其重要）：
- 绝对不要在值中包含"假设""在...前提下""进行分析"等模板已有的词！
- 条件要与 query 的具体场景直接相关，不能是万能条件
- 应是一个具体的宏观变量变化、监管政策调整、市场事件或经营假设
- 8-25 个字为宜

形式参考（禁止直接复用其中的具体文本）：condition 应写成一个具体事件、政策变化、经营变化或市场冲击，最好是名词性条件短语。
坏的例子：{"condition": "假设美联储加息50bp"}（包含了"假设"，会导致最终文本变成"在假设假设..."）
坏的例子：{"condition": "市场不好"}（太泛，没有具体信息）
坏的例子：{"condition": "在经济下行的前提下"}（包含了"前提下"，重复模板词）""",
    },
}
# fmt: on


PARAMETRIC_CONSTRAINT_IDS = set(PARAMETRIC_CONSTRAINT_SPECS)


def is_parametric_constraint(constraint_id: str) -> bool:
    return constraint_id in PARAMETRIC_CONSTRAINT_SPECS


def build_parameterization_prompt(sample: dict[str, Any], constraint_id: str) -> str:
    spec = PARAMETRIC_CONSTRAINT_SPECS[constraint_id]
    schema = {}
    for param_name in spec["params"]:
        if param_name in spec.get("int_ranges", {}):
            schema[param_name] = 1
        else:
            schema[param_name] = "..."
    schema_text = json.dumps(schema, ensure_ascii=False, indent=2)

    role = sample.get("role") or "无角色"
    origin_task = sample.get("origin_task") or "无"
    template_id = sample.get("template_id") or "无"

    placeholder_demo = spec["template"]
    for pn in spec["params"]:
        placeholder_demo = placeholder_demo.replace("{" + pn + "}", "<<<你填的值>>>")

    return f"""\
## 任务

为下面这条 query 的一个参数化约束填写具体参数值。

## Query 信息

- sample_id: {sample["sample_id"]}
- query_id: {sample["query_id"]}
- split: {sample["split"]}  |  track: {sample["track"]}
- source_type: {sample["source_type"]}  |  origin_task: {origin_task}
- template: {template_id} ({sample["template_name"]})
- role_mode: {sample["role_mode"]}  |  role: {role}

### Query 全文
{sample["query_input"]}

## 需要填写的约束

- constraint_id: {constraint_id}
- constraint_type: {spec["type"]}
- 约束模板: {spec["template"]}
- 需要填写的参数: {", ".join(spec["params"])}

你填的值会被直接替换进模板。替换后的效果示意：
  {placeholder_demo}

## 该约束的填写规则与示例

{spec["prompt_guidance"]}

强制要求：
- 上面的示例只用于说明“值应该长什么样”，不是候选答案库。
- 不得直接复用示例里的名词、短语、文体名、格式规则或数字写法。
- 你必须基于当前这条 query 重新创作一个新的值。

## 输出格式

只输出一个 JSON 对象，严格按照以下 schema，不要有任何其他文字：
{schema_text}"""


def parse_llm_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("LLM 输出中没有可解析的 JSON 对象")
        data = json.loads(cleaned[start : end + 1])

    if not isinstance(data, dict):
        raise ValueError("LLM 输出不是 JSON 对象")
    return data


def _normalize_text(value: Any, *, max_len: int = 64) -> str:
    if not isinstance(value, str):
        raise ValueError("字符串参数类型错误")
    text = value.strip()
    text = text.strip("\"'\u201c\u201d")
    text = re.sub(r"\s+", " ", text)
    if not text:
        raise ValueError("字符串参数不能为空")
    if "\n" in text or "\r" in text:
        raise ValueError("字符串参数不能包含换行")
    if len(text) > max_len:
        raise ValueError(f"字符串参数过长：{text}")
    return text


def _repair_currency_rule_text(text: str) -> str:
    repaired = text
    if repaired.count("“") == repaired.count("”") + 1:
        repaired += "”"
    if repaired.count("‘") == repaired.count("’") + 1:
        repaired += "’"
    if repaired.count('"') % 2 == 1:
        repaired += '"'
    if repaired.count("'") % 2 == 1:
        repaired += "'"
    if "XX.X%" in repaired and "亿元" in repaired:
        repaired = repaired.replace("XX.X%", "XX.X亿元")
    repaired = re.sub(r"(\d+(?:\.\d+)?)%", r"\1亿元", repaired)
    return repaired


def _normalize_int(value: Any, *, low: int, high: int) -> int:
    if isinstance(value, bool):
        raise ValueError("布尔值不能作为整数参数")
    if isinstance(value, str):
        if not value.strip().isdigit():
            raise ValueError(f"整数参数无法解析：{value}")
        value = int(value.strip())
    if not isinstance(value, int):
        raise ValueError(f"整数参数类型错误：{value!r}")
    if value < low or value > high:
        raise ValueError(f"整数参数超出范围：{value} not in [{low}, {high}]")
    return value


def validate_and_normalize_params(
    constraint_id: str,
    raw_params: dict[str, Any],
    *,
    query_input: Optional[str] = None,
) -> dict[str, Any]:
    spec = PARAMETRIC_CONSTRAINT_SPECS[constraint_id]
    expected = set(spec["params"])
    actual = set(raw_params)
    missing = expected - actual
    extra = actual - expected
    if missing:
        raise ValueError(f"缺少参数：{sorted(missing)}")
    if extra:
        raise ValueError(f"出现多余参数：{sorted(extra)}")

    normalized = {}
    for param_name in spec["params"]:
        if param_name in spec.get("int_ranges", {}):
            low, high = spec["int_ranges"][param_name]
            normalized[param_name] = _normalize_int(raw_params[param_name], low=low, high=high)
        else:
            normalized[param_name] = _normalize_text(raw_params[param_name])

    if constraint_id == "FV-5":
        normalized["currency_rule"] = _repair_currency_rule_text(normalized["currency_rule"])

    if constraint_id == "GV-8":
        if normalized["kw1"] == normalized["kw2"]:
            raise ValueError("GV-8 的两个关键词不能相同")
    if constraint_id == "GV-13":
        if normalized["first_line"] == normalized["last_line"]:
            raise ValueError("GV-13 的首行和末行不能相同")
    if constraint_id == "FV-3":
        if normalized["trigger"] == normalized["followup"]:
            raise ValueError("FV-3 的 trigger 和 followup 不能相同")

    if query_input is not None:
        _check_query_conflict(constraint_id, normalized, query_input)

    return normalized


def _check_query_conflict(
    constraint_id: str,
    params: dict[str, Any],
    query_input: str,
) -> None:
    """硬校验：参数值不得与 query 题干直接冲突。"""
    if constraint_id == "GV-9":
        word = params.get("word", "")
        if word and word in query_input:
            raise ValueError(
                f"GV-9 禁词'{word}'出现在 query 题干中，请换一个不在题干里的词"
            )
    elif constraint_id == "GV-8":
        for key in ("kw1", "kw2"):
            kw = params.get(key, "")
            if kw and kw in query_input:
                raise ValueError(
                    f"GV-8 关键词 {key}='{kw}'直接出现在 query 题干中，请换一个不在题干里的词"
                )


def render_parametric_constraint(constraint_id: str, params: dict[str, Any]) -> str:
    normalized = validate_and_normalize_params(constraint_id, params)
    template = PARAMETRIC_CONSTRAINT_SPECS[constraint_id]["template"]
    return template.format(**normalized)
