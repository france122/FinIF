# Constraint Pool v3

> 更新时间：2026-04-11
> 权威元数据：`docs/constraint_reference_table.csv`
> 总计：60 条（GH 19 + GS 8 + FH 9 + FS 24）
> 评分：全部 binary 1/0
> 每条约束标注 InfoBench Type（Content / Format / Style / Number / Linguistic），支持多标签

---

## 总览

|  | Hard（规则验证） | Soft（LLM judge） | 合计 |
|---|---|---|---|
| **通用 (G)** | GH × 19 | GS × 8 | 27 |
| **金融 (F)** | FH × 9 | FS × 24 | 33 |
| **合计** | 28 | 32 | **60** |

---

## 一、GH — 通用 Hard（19 条）

> 验证方式：regex / 计数 / 精确匹配

| ID | 约束内容 | 验证方式 | Type |
|---|---|---|---|
| GH-1 | 回答不超过{N}个字 | 字符计数 | Number |
| GH-2 | 至少包含{N}个句子 | 句号计数 | Number |
| GH-3 | 回答分为{N}个段落 | 段落分隔符计数 | Format, Number |
| GH-4 | 使用 Markdown 格式 | 检测 `#` 标记 | Format |
| GH-5 | 包含至少{N}级标题层级 | 检测 Markdown `#` 标题 + 中文编号层级（一、/1.1/1.1.1） | Format, Number |
| GH-6 | 使用编号列表组织回答 | 检测 `1.` `2.` 格式 | Format |
| GH-7 | 使用表格形式呈现关键信息 | 检测 Markdown 表格语法 | Format |
| GH-8 | 以 JSON 格式输出 | JSON parse 验证 | Format |
| GH-9 | 必须包含关键词{kw1}、{kw2} | 关键词匹配 | Linguistic, Content |
| GH-10 | 不得出现"{forbidden_word}" | 关键词排除检测 | Linguistic |
| GH-11 | 开头第一个词必须是"{word}" | 首词匹配 | Linguistic, Format |
| GH-12 | 使用 Checkbox 格式 `[ ]`/`[x]` | regex 检测 | Format |
| GH-13 | 输出必须包含代码块/公式块 | 检测 ``` 标记 | Format |
| GH-14 | 精确首行/末行必须为指定文本 | 首末行精确匹配 | Linguistic, Format |
| GH-16 | 控制在{N}分钟的演讲/汇报时长 | 估算字数换算时长 | Number |
| GH-17 | 包含完整文档要素（封面/目录/附件清单/签章位置等） | regex 检测关键文档要素 | Format |
| GH-18 | 不得使用任何表格 ⚡ | regex 检测 Markdown 表格语法 | Format, Linguistic |
| GH-19 | 不得使用任何列表（编号或项目符号）⚡ | regex 检测列表标记 | Format, Linguistic |
| GH-20 | 以第一人称叙事，不得使用"本报告""本文"等 ⚡ | regex 检测第三人称表述 | Style, Linguistic |

> ⚡ = 反直觉约束（Inverse Instruction）

---

## 二、GS — 通用 Soft（8 条）

> 验证方式：LLM-as-a-judge，binary 1/0

| ID | 约束内容 | Type |
|---|---|---|
| GS-1 | 先给出结论，再给出分析过程 | Format, Content |
| GS-2 | 回答末尾必须包含一段总结 | Format, Content |
| GS-3 | 使用正式书面语，不得口语化 | Style, Linguistic |
| GS-4 | 使用客观中立的语气，不带主观倾向 | Style |
| GS-5 | 段落间必须逻辑连贯，有明确过渡 | Style |
| GS-7 | 使用类比或举例来辅助解释 | Content, Style |
| GS-8 | 适合{目标受众}阅读 | Style |
| GS-9 | 语气{tone} | Style |

---

## 三、FH — 金融 Hard（9 条）

> 验证方式：regex / 规则检测

| ID | 约束内容 | 验证方式 | Type |
|---|---|---|---|
| FH-1 | 末尾必须包含风险提示声明：{risk_line} | regex 匹配 | Content, Format |
| FH-2 | 必须声明"{disclaimer}" | 精确短语匹配 | Content, Linguistic |
| FH-3 | 若提到"{trigger}"，必须同时补充"{followup}" | regex 条件检测 | Linguistic, Content |
| FH-4 | 回答中的数值数据统一保留{N}位小数 | regex 提取数值+检查小数位 | Number, Format |
| FH-5 | 若出现金额，统一使用{currency_rule}表示 | regex 检测 | Linguistic |
| FH-6 | 必须标注风险等级（R1-R5） | regex 检测 R1-R5 | Content |
| FH-7 | 必须包含投资评级词 | regex 匹配买入/增持/中性/减持/卖出 | Content, Linguistic |
| FH-8 | 全文不得出现百分号（%）符号 ⚡ | regex 检测 % | Linguistic, Number |
| FH-9 | 全文不得出现任何阿拉伯数字 ⚡ | regex 检测 [0-9] | Linguistic, Number |

---

## 四、FS — 金融 Soft（24 条）

> 验证方式：LLM-as-a-judge，binary 1/0

### 4.1 视角/立场类（5 条）

| ID | 约束内容 | Type |
|---|---|---|
| FS-1 | 从 ESG 角度评价 | Style, Content |
| FS-6 | 从风险管理的角度分析 | Style, Content |
| FS-7 | 站在监管机构的立场回答 | Style |
| FS-8 | 从零售投资者的视角分析 | Style |
| FS-9 | 从宏观经济的角度分析 | Style, Content |

### 4.2 规范/质量类（4 条）

| ID | 约束内容 | Type | 备注 |
|---|---|---|---|
| FS-2 | 注明所引用信息的来源 | Content, Format | |
| FS-3 | 专业术语缩写需给全称 | Linguistic | **与 FS-10 互斥** |
| FS-10 | 用通俗语言，避免专业术语 | Style, Linguistic | **与 FS-3 互斥** |
| FS-11 | 仅基于提供的材料作答 | Content | |

### 4.3 定量/证据类（2 条）

| ID | 约束内容 | Type |
|---|---|---|
| FS-4 | 必须引用具体财务指标数据 | Content, Number |
| FS-5 | 必须包含定量分析 | Content |

### 4.4 场景/风格类（4 条）

| ID | 约束内容 | Type |
|---|---|---|
| FS-14 | 假设当前处于{市场环境}下进行分析 | Content |
| FS-15 | 以{目标}为首要考量 | Content |
| FS-16 | 以{文档类型}的风格撰写 | Style |
| FS-17 | 在假设{条件}的前提下进行分析 | Content |

### 4.5 内容要求类（7 条，从 WritingBench/DISC/FIFE 提取）

| ID | 约束内容 | Type |
|---|---|---|
| FS-12 | 按{order_field}从高到低排序输出 | Format, Content |
| FS-18 | 重点包含/分析{指定内容} | Content |
| FS-19 | 包含{分析/评估/建议/对比}等多类型内容板块 | Content, Format |
| FS-20 | 需详细说明/列明{具体要素} | Content |
| FS-21 | 包含竞品/同业对比分析 | Content |
| FS-22 | 包含趋势预测/未来展望 | Content |
| FS-23 | 包含预算/成本分析 | Content |

### 4.6 反直觉（2 条）

| ID | 约束内容 | Type |
|---|---|---|
| FS-13 | 不得使用金融术语英文缩写（ROE/PE/EBITDA等）⚡ | Linguistic |
| FS-24 | 风险因素按重要性从低到高排列 ⚡ | Format, Content |

---

## 互斥约束对

组合时不可同时出现：

| 约束 A | 约束 B | 冲突原因 |
|---|---|---|
| FS-3 术语缩写给全称 | FS-10 避免专业术语 | 要求相反 |
| GH-7 使用表格 | GH-18 禁止表格 | 正反矛盾 |
| GH-6 使用列表 | GH-19 禁止列表 | 正反矛盾 |
| FH-8 禁百分号 | FS-4 引用具体财务指标 | 指标通常含% |
| FH-9 禁阿拉伯数字 | FS-4 引用具体财务指标 | 指标含数字 |
| FH-9 禁阿拉伯数字 | FS-5 包含定量分析 | 定量需数字 |

---

## 约束来源

| 来源 | 贡献 |
|---|---|
| IFEval (Zhou et al., 2023) | GH 基础约束（长度/格式/关键词） |
| FIFE (NeurIPS 2025) | GH 高级格式 + FH 金融格式 |
| FollowBench (Jiang et al., 2023) | GS 内容/风格 + FS 视角 |
| SciIF (Wang et al., 2025) | FS 规范/质量/定量 |
| FollowSoftConstraint (Ren et al., ACL 2025) | FS 场景/风格 |
| WritingBench (X-PLUG) | GH/GS/FS 文档/受众/内容要求 |
| InfoBench (Song et al.) | Type 分类体系 |
| Inverse IFEval | 反直觉约束设计思路 |
| 中国金融监管规范 | FH 合规约束 |
