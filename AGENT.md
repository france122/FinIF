# AGENT.md — 项目导引

> 本文件供 AI agent 新 session 时快速了解项目结构和工作规范。

## 项目简介

**中文金融指令遵循（Instruction Following）Benchmark**，填补"中文 + 金融 + IF"的空白。

核心流程：`query 池 × constraint 池 → LLM 选约束组合 → 生成 track → 被评测模型生成 response → 评分 → SFT 训练数据`

## 快速上手

1. 先读本文件了解项目结构
2. 读 `../memory/project_overview.md` 了解当前状态
3. 读 `../memory/progress.md` 看 TODO 和接着做什么
4. 按需读 `../memory/query_pool_status.md`（数据/评分详情）或 `../memory/literature_and_benchmarks.md`（文献引用）

## 关键规范

| 规范 | 说明 |
|------|------|
| 语言 | 所有 query 必须是**中文** |
| 评分 | **binary 1/0**，`result_pass` score=1, `result_fail` score=0，半对算错 |
| Hard 约束 | 用 rule checker 本地验证（`verifier/rules/*.py`） |
| Soft 约束 | 用 LLM-as-a-judge 评分（GPT-5, temperature=0） |
| 约束 ID | `G/F × H/S`（GH=通用硬, GS=通用软, FH=金融硬, FS=金融软） |
| 反直觉约束 | 每条 track 最多选 1 个 |
| 互斥约束对 | FS-3↔FS-10, GH-7↔GH-18, GH-6↔GH-19, FH-8↔FS-4, FH-9↔FS-4, FH-9↔FS-5 |

## 目录结构

```
paper_for_financial_if_benchmark/
├── AGENT.md                          ← 本文件（项目导引）
│
├── data/
│   ├── fineval_raw/                  ← FinEval 原始考试题（4 个 JSON）
│   ├── query_pool/
│   │   ├── query_pool_v3.json        ← 502 条 query（权威版本）
│   │   └── expansion/
│   │       └── decoupled_queries.json← 外部 query 的 constraint 解耦结果
│   ├── tracks/
│   │   ├── all_tracks.jsonl          ← 全量 6,007 条 track（12 种 type）
│   │   ├── train_tracks.jsonl        ← Train 452q, 5,407t
│   │   ├── test_tracks.jsonl         ← Test 50q, 600t
│   │   ├── test_response_input.jsonl ← Test 集 response 生成输入（600 条）
│   │   ├── raw_gpt5_output.jsonl     ← GPT-5 track 生成原始输出
│   │   └── {all,train,test}_stats.*  ← 数据统计（JSON + PNG 图表）
│   └── scores/
│       ├── gpt{5,51,52,54}_responses.jsonl ← 各模型 test responses
│       ├── gpt{5,51,52,54}/          ← 各模型评分结果（hard_scores.jsonl + soft_scores.jsonl）
│       ├── hard_fail_review.json     ← Hard fail review 数据
│       └── all_fail_review.json      ← 全部 fail review 数据
│
├── docs/
│   ├── constraint_pool.md            ← 60 条约束池完整文档（分类/描述/互斥对/来源）
│   ├── constraint_reference_table.csv← 约束元数据权威表（ID/hardness/check_mode/text）
│   └── survey_scholarpeer.md         ← 文献综述
│
├── verifier/                         ← 评分系统
│   ├── base.py                       ← CheckResult 基类（score=1 pass / score=0 fail）
│   ├── registry.py                   ← 约束注册表（从 CSV 加载，校验 hardness/check_mode）
│   ├── rule_runner.py                ← Hard rule 执行器
│   ├── rubric_runner.py              ← Soft rubric prompt 构建（binary 1/0 system prompt）
│   ├── rules/*.py                    ← 28 个 Hard rule checker（每个文件对应一个约束 ID）
│   └── rubrics/*.md                  ← 32 个 Soft rubric（每个文件对应一个约束 ID）
│
├── scripts/
│   ├── gen_track_vulcan_input.py     ← 生成 Vulcan track 输入（502×3=1,506 行）
│   ├── score_all.py                  ← 统一评分脚本（hard rule + soft LLM judge）
│   ├── score_responses.py            ← 旧评分主脚本（保留参考）
│   ├── generate_verifier_scaffold.py ← 约束池变更时自动生成 checker/rubric 骨架
│   └── decouple_query_constraint.py  ← query-constraint 解耦（从外部 query 提取约束）
│
├── prompts/
│   ├── track_gen_system_prompt.md    ← Track 生成 system prompt（约束池全文 + 选约束规则）
│   └── track_gen_user_template.md    ← Track 生成 user prompt 模板
│
├── skills/vulcan_gen.md              ← Vulcan 平台任务配置（Track 生成 / Response 生成 / 评分）
├── ref_local_gpt.py                  ← Minimax 代理调 GPT/Gemini/Claude API
├── query_review.html                 ← Query 解耦审核前端（加载 decoupled_queries.json）
├── score_review.html                 ← 评分 review 前端（加载 review_data.json）
├── vulcan/                           ← Vulcan 平台任务数据
├── surveys/                          ← 文献调研笔记（InfoBench 等）
├── history/                          ← 已废弃的旧文件（仅供追溯，不参与当前流程）
└── logs/                             ← 运行日志
```

## 数据文件索引

### data/query_pool/ — Query 池

| 文件 | 内容 | 格式 | 条数 |
|------|------|------|------|
| `query_pool_v3.json` | 502 条中文金融 query，来自 FinEval/FIFE/DISC/WritingBench 四个来源 | JSON array，每条含 query_id / query / source_type | 502 |
| `expansion/decoupled_queries.json` | 从 DISC/WritingBench 的 250 条外部 query 中解耦出的 base_instruction + constraints | JSON array | 472 条约束 |

### data/tracks/ — Track 数据

| 文件 | 内容 | 格式 | 条数 |
|------|------|------|------|
| `all_tracks.jsonl` | 全量 track（12 种 type，1:2:3 约束均匀分布） | JSONL | 6,007 |
| `train_tracks.jsonl` | 训练集 track（452 个 query，与 test 零重叠） | JSONL | 5,407 |
| `test_tracks.jsonl` | 测试集 track（50 个 query） | JSONL | 600 |
| `test_response_input.jsonl` | 测试集 response 生成输入（送 Vulcan） | JSONL | 600 |
| `raw_gpt5_output.jsonl` | GPT-5 track 生成原始 Vulcan 输出 | JSONL | 1,504 |
| `{all,train,test}_stats.json` | 各切分的约束覆盖/分布统计 | JSON | — |
| `{all,train,test}_stats.png` | 统计可视化图表（含 InfoBench Type 饼图） | PNG | — |

### data/scores/ — 评分数据

| 文件 | 内容 |
|------|------|
| `gpt{5,51,52,54}_responses.jsonl` | 各模型的 test response（600 条/模型） |
| `gpt{5,51,52,54}/hard_scores.jsonl` | Hard 约束评分结果 |
| `gpt{5,51,52,54}/soft_scores.jsonl` | Soft 约束评分结果（待代理恢复后跑） |
| `hard_fail_review.json` | Hard fail 数据（供 `hard_fail_review.html`） |
| `all_fail_review.json` | Hard+Soft fail 数据（供前端 review） |
| `score_summary.json` | 各模型评分汇总统计 |

### data/fineval_raw/ — 原始数据源

| 文件 | 内容 |
|------|------|
| `agent/apiutil-eval.json` | FinEval API 工具类考试题（原始） |
| `agent/findiag-eval.json` | FinEval 金融诊断类考试题（原始） |
| `industry/finsales-eval.json` | FinEval 金融销售类考试题（原始） |
| `industry/finsuggestion-eval.json` | FinEval 金融建议类考试题（原始） |

## 约束池概览（60 条）

| 模块 | 数量 | 验证方式 | 示例 |
|------|------|----------|------|
| GH | 19 | rule checker | 字数限制、Markdown、关键词、JSON 格式 |
| GS | 8 | LLM judge | 先结论后分析、书面语、客观中立 |
| FH | 9 | rule checker | 风险提示、免责声明、小数位数、禁%/禁数字 |
| FS | 24 | LLM judge | ESG 视角、排序输出、通俗语言、竞品对比 |

权威定义见 `docs/constraint_reference_table.csv`（每行含 constraint_id / module / hardness / check_mode / score_type / constraint_text）

## 约束池完整列表

### GH — 通用 Hard（19 条）rule checker
| ID | 约束 |
|-----|------|
| GH-1 | 回答不超过{N}个字 |
| GH-2 | 至少包含{N}个句子 |
| GH-3 | 回答分为{N}个段落 |
| GH-4 | 使用 Markdown 格式 |
| GH-5 | 包含至少{N}级标题层级 |
| GH-6 | 使用编号列表组织回答 |
| GH-7 | 使用表格形式呈现关键信息 |
| GH-8 | 以 JSON 格式输出 |
| GH-9 | 必须包含关键词：{kw1}、{kw2} |
| GH-10 | 不得出现"{forbidden_word}" |
| GH-11 | 开头第一个词必须是"{word}" |
| GH-12 | 使用 Checkbox 格式 [ ]/[x] |
| GH-13 | 输出必须包含代码块/公式块 |
| GH-14 | 第一行必须为"{first_line}"，最后一行为"{last_line}" |
| GH-16 | 控制在{N}分钟的演讲/汇报时长 |
| GH-17 | 包含完整文档要素（封面/目录/附件清单/签章位置等） |
| GH-18 | 不得使用任何表格 |
| GH-19 | 不得使用任何列表 |
| GH-20 | 以第一人称叙事口吻撰写 |

### GS — 通用 Soft（8 条）LLM judge
| ID | 约束 |
|-----|------|
| GS-1 | 先给出结论，再给出分析过程 |
| GS-2 | 回答末尾必须包含一段总结 |
| GS-3 | 使用正式书面语，不得口语化 |
| GS-4 | 使用客观中立的语气，不带主观倾向 |
| GS-5 | 段落间必须逻辑连贯，有明确过渡 |
| GS-7 | 使用类比或举例来辅助解释 |
| GS-8 | 适合{目标受众}阅读 |
| GS-9 | 语气{诚恳/有感染力/有说服力} |

### FH — 金融 Hard（9 条）rule checker
| ID | 约束 |
|-----|------|
| FH-1 | 末尾必须包含风险提示声明：{risk_line} |
| FH-2 | 必须声明"{disclaimer}" |
| FH-3 | 若提到"{trigger}"，必须同时补充"{followup}" |
| FH-4 | 回答中的数值数据统一保留{N}位小数 |
| FH-5 | 若出现金额，统一使用{currency_rule}表示 |
| FH-6 | 必须标注风险等级（R1-R5） |
| FH-7 | 必须包含投资评级词 |
| FH-8 | 全文不得出现百分号（%）符号 |
| FH-9 | 全文不得出现任何阿拉伯数字 |

### FS — 金融 Soft（24 条）LLM judge
| ID | 约束 |
|-----|------|
| FS-1 | 从 ESG 角度评价 |
| FS-2 | 注明所引用信息的来源 |
| FS-3 | 专业术语缩写需给全称 |
| FS-4 | 必须引用具体财务指标数据 |
| FS-5 | 必须包含定量分析 |
| FS-6 | 从风险管理的角度分析 |
| FS-7 | 站在监管机构的立场回答 |
| FS-8 | 从零售投资者的视角分析 |
| FS-9 | 从宏观经济的角度分析 |
| FS-10 | 用通俗语言，避免专业术语 |
| FS-11 | 仅基于提供的材料作答 |
| FS-12 | 按{order_field}从高到低排序输出 |
| FS-13 | 不得使用金融术语英文缩写（ROE/PE/EBITDA等） |
| FS-14 | 假设当前处于{市场环境}下进行分析 |
| FS-15 | 以{目标}为首要考量 |
| FS-16 | 以{文档类型}的风格撰写 |
| FS-17 | 在{条件}这一假设下进行分析 |
| FS-18 | 重点包含/分析{指定内容} |
| FS-19 | 包含{分析/评估/建议/对比}等多类型内容板块 |
| FS-20 | 需详细说明/列明{具体要素} |
| FS-21 | 包含竞品/同业对比分析 |
| FS-22 | 包含趋势预测/未来展望 |
| FS-23 | 包含预算/成本分析 |
| FS-24 | 风险因素按重要性从低到高排列 |

## 各环节模型

| 环节 | 模型 | 平台 |
|------|------|------|
| Track 组合（选约束+参数化） | GPT-5 | Vulcan |
| Test Response 生成 | GPT-5.4 | Vulcan |
| Soft 评分 Judge | GPT-5 (gpt-5-2025-08-07) | 本地 `ref_local_gpt.py` 调 Minimax 代理 |
| Hard 评分 | rule checker | 本地 `verifier/` |

## 修改约束池的 checklist

新增/修改/删除约束时，需同步更新以下文件：

1. `docs/constraint_reference_table.csv` — 约束元数据（ID/module/hardness/check_mode/score_type/text）
2. `docs/constraint_pool.md` — 约束池文档（分类表格、条数统计）
3. Hard 约束 → `verifier/rules/{ID}.py`（rule checker）
4. Soft 约束 → `verifier/rubrics/{ID}.md`（rubric）
5. `prompts/track_gen_sp_{hard,soft,mixed}.md` — track 生成 prompt 中的约束池
6. 验证：`python3 -c "from verifier.registry import load_constraint_registry; r = load_constraint_registry(); print(len(r))"` 应无报错

## 评分命令

```bash
# 对某模型的 response 跑 hard + soft 评分（支持断点续跑）
python3 scripts/score_all.py \
  --response-file data/scores/gpt5_responses.jsonl \
  --output-dir data/scores/gpt5 \
  --judge-model gpt-5-2025-08-07 \
  --concurrency 10
```

## Vulcan 注意事项

- GPT 系列用 Responses API：前处理传 `input`（不是 `messages`），后处理从 `output[].type=="message" → content[].type=="output_text" → text` 提取
- Vulcan postprocess 通过 `data.steps['model_request'].output` 获取模型输出
- GPT-5 需要 `max_completion_tokens`（不是 `max_tokens`），且包含 reasoning tokens
- Vulcan handler 文件：`vulcan/track_gen/`（track 生成）、`vulcan/eval_response_test/`（response 生成）

## 已知问题

- Soft judge 宽判：LLM judge 对 soft constraint 可能偏宽，考虑双 judge 或更严格 prompt
- Minimax 代理不稳定：`ref_local_gpt.py` 调用 `thirdpart-proxy-prod.xaminim.com` 偶尔超时
