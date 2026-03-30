import json
import random
from pathlib import Path
from textwrap import dedent
from typing import Optional


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
VIEWER_DIR = BASE_DIR / "viewer"
FINEVAL_ROOT = DATA_DIR / "fineval_raw"

FINAL_JSON = DATA_DIR / "query_pool" / "query_pool_v2_final.json"
FINAL_HTML = VIEWER_DIR / "query_pool_v2_viewer.html"

RNG = random.Random(42)
TEMPLATE_IDS = ["T1", "T2", "T4", "T5", "T7", "T9", "T10", "T11"]
PER_TEMPLATE = 111


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pick(seq, idx, step=1, offset=0):
    return seq[(idx * step + offset) % len(seq)]


def shorten(text: str, limit: int = 28) -> str:
    text = " ".join(text.split())
    return text[:limit] + ("..." if len(text) > limit else "")


def role_prefix(template_id: str, origin_task: Optional[str], role: str) -> str:
    template_style = {
        "T1": f"你是一名{role}。请基于专业研究视角完成以下任务。\n\n",
        "T2": f"你是一名{role}。请在对客沟通场景下完成以下任务。\n\n",
        "T4": f"你是一名{role}。请基于职责边界完成以下风险诊断任务。\n\n",
        "T5": f"你是一名{role}。请阅读以下材料并给出专业判断。\n\n",
        "T7": f"你是一名{role}。请按金融数据分析场景完成以下任务。\n\n",
        "T9": f"你是一名{role}。请按实际业务执行文档的要求完成以下任务。\n\n",
        "T10": f"你是一名{role}。请在合规对客场景下完成以下任务。\n\n",
        "T11": f"你是一名{role}。请面向客户完成以下说明任务。\n\n",
    }
    if template_id in template_style:
        return template_style[template_id]
    source_style = {
        "finsuggestion": f"你是一名{role}。请专业、清晰地回答以下问题。\n\n",
        "findiag": f"你是一名{role}。请阅读以下材料并回答问题。\n\n",
        "apiutil": f"你是一名{role}。请在金融数据工作场景中完成以下任务。\n\n",
        "finsales": f"你是一名{role}。请从对客解释或培训场景出发完成以下任务。\n\n",
    }
    return source_style.get(origin_task, f"你是一名{role}。\n\n")


def build_t1(idx: int):
    markets = ["A股", "港股", "美股", "跨境市场", "新兴市场"]
    sectors = ["创新药", "新能源", "半导体", "消费电子", "高端制造", "互联网平台", "物流科技", "金融科技", "游戏传媒"]
    timings = ["盘前", "盘后", "收盘后", "晨会前"]
    angles = [
        "订单增长",
        "毛利率修复",
        "海外收入提升",
        "资本开支上行",
        "产品结构优化",
        "渠道扩张",
        "研发投入增加",
        "客户集中度变化",
    ]
    market = pick(markets, idx, 3)
    sector = pick(sectors, idx, 5)
    timing = pick(timings, idx, 7)
    angle_a = pick(angles, idx, 2)
    angle_b = pick(angles, idx, 4, 1)
    revenue = round(18 + (idx * 1.7) % 140, 1)
    rev_yoy = round(6 + (idx * 2.3) % 34, 1)
    profit = round(2.6 + (idx * 0.9) % 18, 1)
    profit_yoy = round(3 + (idx * 1.9) % 28, 1)
    margin = round(12 + (idx * 1.4) % 18, 1)
    ratio = round(10 + (idx * 2.1) % 35, 1)
    prompt = dedent(
        f"""\
        请基于以下事实，为机构客户写一段简明的{timing}点评，概括核心观点、主要利多因素、主要风险点，并避免编造数据。

        已知事实：
        - 某{market}{sector}企业2025年第三季度营业收入{revenue}亿元，同比增长{rev_yoy}%。
        - 归母净利润{profit}亿元，同比增长{profit_yoy}%。
        - 毛利率为{margin}%，较上季度改善。
        - 与“{angle_a}”相关的业务收入占比提升至{ratio}%。
        - 管理层强调“{angle_b}”仍是未来两个季度的重要变量。
        - 市场当前同时关注需求节奏、估值消化和行业竞争格局变化。
        """
    )
    roles = ["证券分析师", "券商行业分析师", "宏观研究员"]
    return {
        "template_id": "T1",
        "template_name": "财报点评 Brief",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{market}{sector}企业{timing}点评{idx + 1}",
        "input": prompt,
        "material_type": "财报事实包",
        "source_basis": {"fife_template": "#1 财报/市场点评 brief"},
        "role_candidates": roles,
    }


def build_t2(idx: int):
    client_types = ["年轻白领", "高净值家庭", "中小企业主", "三口之家", "临近退休客户", "自由职业者", "留学家庭", "创业者"]
    goals = ["长期增值", "教育储备", "退休规划", "现金管理", "资产分散", "稳健增值"]
    risks = ["偏保守", "中低", "中等", "中等偏上"]
    horizons = ["18个月", "3年", "5年以上", "6至8年", "2年", "1年内"]
    contexts = [
        "短端利率相对稳定，债券类资产配置吸引力提升。",
        "权益市场波动较大，但高股息板块受到稳健资金关注。",
        "海外科技资产中长期趋势较强，但短期估值扰动明显。",
        "黄金在大类资产配置中的对冲价值仍被关注。",
        "银行理财、债券基金和存款类工具各有适用边界。",
        "跨境资产配置可以增强分散性，但汇率波动不可忽视。",
    ]
    family = pick(client_types, idx, 3)
    goal = pick(goals, idx, 5)
    risk = pick(risks, idx, 7)
    horizon = pick(horizons, idx, 2)
    cash = 20 + (idx * 11) % 580
    context_a = pick(contexts, idx, 4)
    context_b = pick(contexts, idx, 5, 2)
    prompt = dedent(
        f"""\
        某客户提供了如下信息：风险承受能力为{risk}，主要目标是{goal}，可投资期限为{horizon}，希望在兼顾流动性的前提下做好资金安排。

        客户信息：
        - 客户类型：{family}
        - 可投资资金：{cash}万元
        - 风险偏好：{risk}
        - 核心目标：{goal}

        市场背景：
        - {context_a}
        - {context_b}

        请写一份面向客户的配置建议说明，比较至少两种可选方案，并说明主要风险与适用边界。
        """
    )
    roles = ["银行客户经理", "财富管理顾问", "投资顾问"]
    return {
        "template_id": "T2",
        "template_name": "资产配置建议 Memo",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{family}{goal}配置建议{idx + 1}",
        "input": prompt,
        "material_type": "客户画像+市场背景",
        "source_basis": {"fife_template": "#7 风险收益权衡 memo"},
        "role_candidates": roles,
    }


def build_t4(idx: int):
    entities = ["制造企业", "外贸企业", "消费电子企业", "医药公司", "电商平台", "银行分支机构", "资管产品", "供应链公司"]
    themes = ["发票与合同不一致", "存货库龄异常", "应收账款回款延迟", "估值更新滞后", "供应商集中新增", "报关与台账不一致", "费用先付款后签约", "授信资料前后口径不一"]
    actions = ["开展内部自查", "准备年末审计", "准备授信审批", "准备监管报送", "启动流程复盘", "准备风险排查"]
    entity = pick(entities, idx, 3)
    theme = pick(themes, idx, 5)
    action = pick(actions, idx, 7)
    ratio = 8 + (idx * 3) % 31
    days = 30 + (idx * 19) % 420
    amount = 120 + (idx * 37) % 860
    prompt = dedent(
        f"""\
        请根据以下材料，识别其中最关键的风险点或异常点，分析原因，并提出后续处理建议。回答应只基于给定材料，不要补充未提供的事实。

        材料：
        - 某{entity}近期出现“{theme}”相关异常。
        - 相关金额约为{amount}万元，较历史水平明显提升。
        - 部分记录与内部台账或合同节点存在时间差。
        - 有资料显示个别业务环节已延迟{days}天仍未完成补充说明。
        - 管理层表示将于近期{action}，希望先形成初步诊断意见。
        - 当前已知材料不足以完全还原全部事实链条，需要明确指出仍待核实部分。
        """
    )
    roles = ["税务顾问", "初级审计人员", "风控专员", "初级会计人员"]
    return {
        "template_id": "T4",
        "template_name": "风险诊断 Memo",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{entity}{theme}诊断{idx + 1}",
        "input": prompt,
        "material_type": "风险异常材料",
        "source_basis": {"fife_template": "#35 风险缺陷总结 / #48 red flags"},
        "role_candidates": roles,
    }


def build_t5(idx: int):
    topics = [
        ("理财净值波动", "客户担心净值下跌后是否应立即赎回"),
        ("保险续保", "客户担心保费上涨和续保条件变化"),
        ("贷款申请", "客户担心流水波动影响审批"),
        ("量化策略", "团队担心模型在高波动环境下失效"),
        ("基金定投", "客户疑惑市场下跌时是否应暂停"),
        ("企业报销", "员工想在票据未齐的情况下先付款"),
        ("房地产投资", "客户不确定地区选择和风险管理"),
        ("外汇风险", "团队担心汇率波动影响投资组合"),
    ]
    asks = [
        ("用户: 最近产品净值有些回撤，我是不是应该马上赎回？", "BOT: 是否赎回需要结合产品属性、持有期限和你的流动性需求综合判断。"),
        ("用户: 保费涨了不少，我还需要继续续保吗？", "BOT: 是否续保需要结合你的保障缺口、预算和现有保障情况综合看。"),
        ("用户: 我们公司流水最近波动比较大，会不会影响贷款审批？", "BOT: 银行通常会综合看企业经营、流水、纳税和还款能力。"),
        ("用户: 我们的模型在高波动市场表现不好，可能是什么原因？", "BOT: 高波动环境下，历史模式的稳定性下降，传统模型容易失效。"),
    ]
    followups = [
        ("用户: 那我现在最该先看什么？", "BOT: 建议先明确你的目标、关键约束以及当前最需要补充的信息。"),
        ("用户: 如果情况继续变化，我应该怎么调整？", "BOT: 可以根据新的信息重新评估，并适时调整策略或方案。"),
        ("用户: 这件事里最大的风险是什么？", "BOT: 目前最大的风险在于信息不足导致判断偏差，因此需要先补足关键事实。"),
        ("用户: 我现在应该补哪些材料？", "BOT: 一般需要先补充能证明业务真实性、资金流和责任边界的核心材料。"),
    ]
    topic, desc = pick(topics, idx, 3)
    ask_a, ans_a = pick(asks, idx, 5)
    ask_b, ans_b = pick(followups, idx, 7)
    prompt = dedent(
        f"""\
        阅读以下对话后，请总结当前暴露出的核心问题，说明原因，并给出下一步建议。若信息不足，请明确指出。

        对话背景：{topic}，{desc}

        对话记录：
        {ask_a}
        {ans_a}
        用户: 我理解了一部分，但还是担心自己判断失误。
        BOT: 你的担心是合理的，很多决策都需要结合更多背景信息来判断。
        {ask_b}
        {ans_b}
        """
    )
    roles = ["银行客户经理", "税务顾问", "初级会计人员", "合规专员", "证券分析师"]
    return {
        "template_id": "T5",
        "template_name": "对话后问题诊断与建议",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{topic}对话诊断{idx + 1}",
        "input": prompt,
        "material_type": "多轮对话",
        "source_basis": {"fife_template": "diagnosis shell + FinEval findiag style"},
        "role_candidates": roles,
    }


def build_t7(idx: int):
    libs = [
        ("yfinance", "用于获取股票、ETF、指数、债券和大宗商品等历史行情数据"),
        ("Tushare", "提供 A 股、基金、指数、财务和宏观等数据接口"),
        ("akshare", "提供股票、期货、宏观和行业等多种中文财经数据接口"),
        ("pandas_datareader", "可读取部分公开市场和宏观数据源"),
    ]
    tasks = [
        "获取指定股票过去两年的日线行情并计算月度收益率",
        "拉取某指数过去一年的历史价格并计算最大回撤",
        "抓取两只 ETF 的价格序列并比较波动率表现",
        "获取某货币对的历史数据并计算滚动波动率",
        "下载宏观时间序列并计算滚动相关系数",
        "获取商品期货历史价格并计算滚动收益",
        "抓取股息和拆股数据并整理成事件表",
        "拉取基金净值数据并计算年化收益与回撤",
    ]
    lib_name, lib_desc = pick(libs, idx, 3)
    task = pick(tasks, idx, 5)
    prompt = dedent(
        f"""\
        现在需要完成如下金融数据任务。请根据给定 API 能力说明，写出分步骤的实现方案，并在需要时给出 Markdown 格式的示例代码，但不要执行代码。

        任务描述：
        {task}

        API 说明：
        {lib_name} 是一个{lib_desc}的 Python 工具。常见实现流程包括导入库、获取原始数据、清洗整理、计算指标，并输出结果或图表。
        """
    )
    roles = ["初级统计分析人员", "数据分析师", "证券分析师"]
    return {
        "template_id": "T7",
        "template_name": "API 操作方案说明",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{lib_name}{shorten(task, 16)}{idx + 1}",
        "input": prompt,
        "material_type": "API 文档+任务描述",
        "source_basis": {"fife_template": "workflow / 伪代码说明"},
        "role_candidates": roles,
    }


def build_t9(idx: int):
    processes = [
        "晨报发布前检查",
        "基金持仓月度更新",
        "公告摘要入库",
        "净值披露前核对",
        "估值偏差复核",
        "跨境晨报发布",
        "研究报告归档",
        "产品周报分发",
    ]
    systems = ["研究共享盘", "估值系统", "披露后台", "邮件系统", "内容发布系统", "投研数据库", "知识库", "运营工单系统"]
    deadlines = ["当日17:30前", "当日20:30前", "交易日8:30前", "月初第一个交易日收盘前", "当天18:00前"]
    process = pick(processes, idx, 3)
    sys_a = pick(systems, idx, 5)
    sys_b = pick(systems, idx, 7, 2)
    deadline = pick(deadlines, idx, 11)
    prompt = dedent(
        f"""\
        请根据以下任务背景，写一份操作 runbook / checklist，覆盖准备、执行、核对和异常处理四个阶段，确保他人可以按文档完成任务。

        任务背景：
        业务场景为“{process}”，需要协调多个系统与检查环节，确保流程留痕完整、时间节点可控。

        相关输入：
        - 主要系统涉及：{sys_a}、{sys_b}。
        - 若发现字段缺失、时间滞后或版本不一致，需要人工复核并升级处理。
        - 最终结果需要在{deadline}前提交或发布。
        """
    )
    roles = ["数据分析师", "银行科技与运营支持人员", "研究运营专员"]
    return {
        "template_id": "T9",
        "template_name": "运营/分析 Runbook",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{process}Runbook{idx + 1}",
        "input": prompt,
        "material_type": "流程背景+检查项",
        "source_basis": {"fife_template": "#20 timed checklist / #59 runsheet / #73 runbook"},
        "role_candidates": roles,
    }


def build_t10(idx: int):
    products = [
        "养老目标FOF",
        "黄金ETF联接基金",
        "中低波动固收增强产品",
        "公募REIT",
        "可转债基金",
        "分红型保险产品",
        "红利低波策略基金",
        "跨境债券基金",
    ]
    users = [
        "希望稳健增值的客户",
        "关注长期养老储备的客户",
        "希望分散单一资产风险的客户",
        "关注现金流与分红潜力的客户",
        "希望兼顾弹性和回撤控制的客户",
    ]
    risks = [
        "净值会波动，短期表现可能受市场影响",
        "收益不确定，不承诺保本保收益",
        "二级市场价格波动和流动性变化都可能影响表现",
        "汇率、利率或权益市场变化可能带来波动",
        "产品更适合中长期持有，不适合短期停放资金",
    ]
    product = pick(products, idx, 3)
    user = pick(users, idx, 5)
    risk = pick(risks, idx, 7)
    prompt = dedent(
        f"""\
        请根据以下产品信息，写一段面向客户的卖点说明，突出产品特点、适合人群和主要风险，避免夸大收益或做出不当承诺。

        产品信息：
        - 产品类型：{product}
        - 适合人群：{user}
        - 主要特点：可作为组合配置工具，帮助客户在既定目标下进行资产安排。
        - 风险提示：{risk}
        """
    )
    roles = ["银行客户经理", "基金销售", "保险顾问"]
    return {
        "template_id": "T10",
        "template_name": "产品卖点说明",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{product}卖点说明{idx + 1}",
        "input": prompt,
        "material_type": "产品事实包",
        "source_basis": {"fife_template": "#14 / #15 / #77 product brief"},
        "role_candidates": roles,
    }


def build_t11(idx: int):
    topics = [
        "大额存单提前支取",
        "医疗险免赔额",
        "公募REIT基础认知",
        "跨境理财通产品认知",
        "指数基金定投",
        "净值型理财波动",
        "分红型保险红利机制",
        "债券基金久期与波动",
    ]
    cautions = [
        "需要强调不同产品规则可能存在差异，应以具体合同约定为准。",
        "需要用通俗方式解释，但仍需保留必要风险提示。",
        "不要让客户误以为历史表现代表未来收益。",
        "应提醒客户关注流动性安排、费用和适用边界。",
        "解释应清晰，但不要把制度细节说得过满或超出已知范围。",
    ]
    topic = pick(topics, idx, 3)
    caution = pick(cautions, idx, 5)
    prompt = dedent(
        f"""\
        请围绕以下主题，为客户整理一份简明 FAQ，帮助客户快速理解核心问题、常见误区和需要注意的事项。

        主题：
        {topic}

        材料：
        - 客户通常会围绕定义、适用人群、收益风险、持有周期和常见误解进行提问。
        - 希望回答既通俗又保留专业性，便于客户快速建立正确认知。
        - {caution}
        """
    )
    roles = ["银行客户经理", "保险顾问", "证券投教专员", "基金销售"]
    return {
        "template_id": "T11",
        "template_name": "客户 FAQ",
        "source_type": "fife_template",
        "origin_task": None,
        "title": f"{topic}FAQ{idx + 1}",
        "input": prompt,
        "material_type": "主题+FAQ素材",
        "source_basis": {"fife_template": "#44 FAQ"},
        "role_candidates": roles,
    }


TEMPLATE_BUILDERS = {
    "T1": build_t1,
    "T2": build_t2,
    "T4": build_t4,
    "T5": build_t5,
    "T7": build_t7,
    "T9": build_t9,
    "T10": build_t10,
    "T11": build_t11,
}


def load_fineval_records():
    files = {
        "finsuggestion": FINEVAL_ROOT / "industry" / "finsuggestion-eval.json",
        "findiag": FINEVAL_ROOT / "agent" / "findiag-eval.json",
        "apiutil": FINEVAL_ROOT / "agent" / "apiutil-eval.json",
        "finsales": FINEVAL_ROOT / "industry" / "finsales-eval.json",
    }
    title_prefix = {
        "finsuggestion": "FinEval建议题",
        "findiag": "FinEval诊断题",
        "apiutil": "FinEval工具题",
        "finsales": "FinEval营销术语题",
    }
    role_candidates = {
        "finsuggestion": ["证券分析师", "银行客户经理", "财富管理顾问"],
        "findiag": ["税务顾问", "银行客户经理", "初级会计人员", "合规专员"],
        "apiutil": ["初级统计分析人员", "数据分析师", "证券分析师"],
        "finsales": ["基金销售", "银行客户经理", "保险顾问", "营销培训专员"],
    }
    records = []
    for task, path in files.items():
        data = read_json(path)
        for example in data:
            base_input = example["input"].strip()
            if task == "finsales":
                base_input = f"请解释下面金融营销术语，并结合金融业务场景说明它的含义、常见使用场景和注意事项：\n{base_input}"
            record = {
                "template_id": None,
                "template_name": "FinEval 原题",
                "source_type": "fineval_original",
                "origin_task": task,
                "title": f"{title_prefix[task]}-{shorten(example['input'], 18)}",
                "input": base_input,
                "material_type": "FinEval原始材料",
                "source_basis": {"fineval_task": task},
                "role_candidates": role_candidates[task],
            }
            records.append(record)
    return records


def generate_template_records():
    records = []
    for template_id in TEMPLATE_IDS:
        builder = TEMPLATE_BUILDERS[template_id]
        for i in range(PER_TEMPLATE):
            records.append(builder(i))
    return records


def inject_roles(records):
    roleable_indices = [i for i, item in enumerate(records) if item.get("role_candidates")]
    target = len(records) // 3
    selected = set(RNG.sample(roleable_indices, target))
    for idx, item in enumerate(records):
        item["base_input"] = item["input"]
        if idx in selected:
            role = RNG.choice(item["role_candidates"])
            item["role_mode"] = "with_role"
            item["role"] = role
            item["input"] = role_prefix(item["template_id"], item.get("origin_task"), role) + item["input"]
        else:
            item["role_mode"] = "no_role"
            item["role"] = None
        item.pop("role_candidates", None)
    return records


def assign_ids(records):
    for i, item in enumerate(records, start=1):
        item["id"] = f"qpv2-{i:04d}"
    return records


def deduplicate_records(records):
    deduped = []
    seen_inputs = set()
    removed = 0
    for item in records:
        if item["input"] in seen_inputs:
            removed += 1
            continue
        seen_inputs.add(item["input"])
        deduped.append(item)
    return deduped, removed


def build_viewer(records):
    data_json = json.dumps(records, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Query Pool v2 Final Viewer</title>
  <style>
    :root {{
      --bg: #0b1020; --panel: #121a2b; --panel2: #18233a; --line: #283554;
      --text: #ebf1ff; --muted: #9fb0d3; --chip: #243452;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    .wrap {{ max-width: 1360px; margin: 0 auto; padding: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .sub {{ color: var(--muted); line-height: 1.7; margin-bottom: 20px; }}
    .stats {{ display:grid; grid-template-columns: repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-bottom:18px; }}
    .stat {{ background: var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px 16px; }}
    .k {{ color: var(--muted); font-size:13px; margin-bottom:8px; }}
    .v {{ font-size:24px; font-weight:700; }}
    .toolbar {{ display:grid; grid-template-columns: 1.3fr 1fr 1fr 1fr 1fr 1fr; gap:12px; margin-bottom:18px; }}
    input, select {{ width:100%; border:1px solid var(--line); border-radius:12px; padding:12px 14px; background:var(--panel); color:var(--text); font-size:14px; }}
    .hint {{ color: var(--muted); margin-bottom: 18px; font-size: 13px; }}
    .list {{ display:grid; gap:14px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:16px; overflow:hidden; }}
    .card-head {{ padding:16px 18px 10px; border-bottom:1px solid rgba(255,255,255,0.05); }}
    .title {{ font-size:18px; font-weight:700; margin-bottom:10px; }}
    .meta {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .chip {{ background:var(--chip); border-radius:999px; padding:5px 10px; font-size:12px; }}
    .body {{ padding:16px 18px 18px; display:grid; gap:14px; }}
    .section {{ font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px; }}
    pre {{ margin:0; white-space:pre-wrap; word-break:break-word; background:var(--panel2); border:1px solid var(--line); border-radius:12px; padding:14px; line-height:1.6; font-size:13px; }}
    .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .src {{ color:#95e0c3; font-size:13px; line-height:1.7; }}
    .empty {{ padding:32px 18px; color:var(--muted); text-align:center; background:var(--panel); border:1px solid var(--line); border-radius:16px; }}
    @media (max-width: 1080px) {{ .toolbar,.grid2 {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Query Pool v2 Final Viewer</h1>
    <div class="sub">当前展示的是最终 query 总池：包含 `FinEval` 四类原题与 `FIFE 中文化模板` 生成题；在 query pool 构建阶段先按裸 `query input` 做文本去重，再按约 1/3 注入 `CFinBench role` 作为 query 层增强。`FinEval` 原题保留原始四类来源标记，`FIFE` 生成题不再强行挂到这四类下面，只保留模板语义。</div>
    <div class="stats" id="stats"></div>
    <div class="toolbar">
      <input id="search" type="text" placeholder="搜索标题、模板、来源、query 文本" />
      <select id="sourceType"></select>
      <select id="originTask"></select>
      <select id="templateId"></select>
      <select id="roleMode"></select>
      <select id="role"></select>
    </div>
    <div class="hint" id="hint"></div>
    <div class="list" id="list"></div>
  </div>
  <script>
    const DATA = {data_json};
    const $ = (id) => document.getElementById(id);
    const ids = ["search","sourceType","originTask","templateId","roleMode","role"];
    function uniq(arr) {{
      return [...new Set(arr)].sort((a, b) => String(a).localeCompare(String(b), "zh-CN"));
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
        fineval: DATA.filter(x => x.source_type === "fineval_original").length,
        template: DATA.filter(x => x.source_type === "fife_template").length,
        withRole: DATA.filter(x => x.role_mode === "with_role").length,
        noRole: DATA.filter(x => x.role_mode === "no_role").length,
      }};
      $("stats").innerHTML = `
        <div class="stat"><div class="k">总 Query 数</div><div class="v">${{stats.total}}</div></div>
        <div class="stat"><div class="k">FinEval 原题</div><div class="v">${{stats.fineval}}</div></div>
        <div class="stat"><div class="k">模板生成题</div><div class="v">${{stats.template}}</div></div>
        <div class="stat"><div class="k">带角色</div><div class="v">${{stats.withRole}}</div></div>
        <div class="stat"><div class="k">不带角色</div><div class="v">${{stats.noRole}}</div></div>
      `;
    }}
    function render() {{
      const q = $("search").value.trim().toLowerCase();
      const sourceType = $("sourceType").value;
      const originTask = $("originTask").value;
      const templateId = $("templateId").value;
      const roleMode = $("roleMode").value;
      const role = $("role").value;
      const rows = DATA.filter(item => {{
        const hay = [
          item.id, item.title, item.template_id || "", item.template_name,
          item.source_type, item.origin_task || "", item.role_mode, item.role || "",
          item.input, item.material_type
        ].join("\\n").toLowerCase();
        return (!q || hay.includes(q))
          && (!sourceType || item.source_type === sourceType)
          && (!originTask || item.origin_task === originTask)
          && (!templateId || item.template_id === templateId)
          && (!roleMode || item.role_mode === roleMode)
          && (!role || item.role === role);
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
              <span class="chip">${{esc(item.id)}}</span>
              <span class="chip">${{esc(item.source_type)}}</span>
              ${{item.origin_task ? `<span class="chip">${{esc(item.origin_task)}}</span>` : ""}}
              ${{item.template_id ? `<span class="chip">${{esc(item.template_id)}}</span>` : ""}}
              <span class="chip">${{esc(item.role_mode)}}</span>
              <span class="chip">${{esc(item.role || "无角色")}}</span>
              <span class="chip">${{esc(item.material_type)}}</span>
            </div>
          </div>
          <div class="body">
            <div>
              <div class="section">Query</div>
              <pre>${{esc(item.input)}}</pre>
            </div>
            <div class="grid2">
              <div>
                <div class="section">Template Name</div>
                <div class="src">${{esc(item.template_name)}}</div>
              </div>
              <div>
                <div class="section">Source Basis</div>
                <div class="src">${{esc(JSON.stringify(item.source_basis, null, 0))}}</div>
              </div>
            </div>
          </div>
        </div>
      `).join("");
    }}
    fill($("sourceType"), uniq(DATA.map(x => x.source_type)), "来源类型");
    fill($("originTask"), uniq(DATA.map(x => x.origin_task).filter(Boolean)), "FinEval来源任务");
    fill($("templateId"), uniq(DATA.map(x => x.template_id).filter(Boolean)), "模板");
    fill($("roleMode"), uniq(DATA.map(x => x.role_mode)), "角色模式");
    fill($("role"), uniq(DATA.map(x => x.role || "无角色")), "角色");
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
    return html


def main():
    FINAL_JSON.parent.mkdir(parents=True, exist_ok=True)
    FINAL_HTML.parent.mkdir(parents=True, exist_ok=True)
    fineval_records = load_fineval_records()
    template_records = generate_template_records()
    records = fineval_records + template_records
    candidate_total = len(records)
    records, removed = deduplicate_records(records)
    inject_roles(records)
    assign_ids(records)
    FINAL_JSON.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    FINAL_HTML.write_text(build_viewer(records), encoding="utf-8")
    print("candidate records", candidate_total)
    print("deduplicated records", len(records))
    print("removed duplicates", removed)
    print("json", FINAL_JSON)
    print("html", FINAL_HTML)


if __name__ == "__main__":
    main()
