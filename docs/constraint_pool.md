# 约束池 v2（审查后）

> 更新时间：2026-03-28
> 审查记录：constraint_review_decisions.md
> 总计：46 条（GV 15 + GN 7 + FV 7 + FN 17）

> 说明：本文件保留的是约束池设计阶段的原始 v2 叙述；**当前 verifier v3 的实际评测口径请以 `docs/constraint_reference_table.csv` 为准**。
> 已在 verifier v3 中迁移编号的约束：
> - `GN-1 -> GV-15`
> - `GN-2 -> GV-16`
> - `FN-4 -> FV-8`
> - `FN-6 -> FV-9`
> - `FN-7 -> FV-10`
> - `FN-10 -> FV-11`
> - `FN-11 -> FV-12`

---

## 总览

|  | Verifiable（规则评） | Non-verifiable（LLM-as-judge） |
|---|---|---|
| **通用** | GV × 15 | GN × 7 |
| **金融** | FV × 7 | FN × 17 |

---

## 一、GV — 通用 Verifiable（15 条）

> 验证方式：regex / 计数 / 精确匹配，确定性可复现

| ID | 约束内容 | 主要来源 | 验证方式 |
|---|---|---|---|
| GV-1 | 回答不超过{N}个字 | IFEval `length_constraints:number_words` | 字符计数 |
| GV-2 | 至少包含{N}个句子 | IFEval `length_constraints:number_sentences` | 句号计数 |
| GV-3 | 回答分为{N}个段落 | IFEval `length_constraints:number_paragraphs` | 段落分隔符计数 |
| GV-4a | 使用 Markdown 格式 | IFEval `detectable_format:title` | 检测 `#` 标记 |
| GV-4b | 包含至少{N}级标题层级 | FIFE L1-7 Heading/Section | 检测 `#`/`##`/`###` 层级 |
| GV-5 | 使用编号列表组织回答 | IFEval `detectable_format:number_bullet_lists` | 检测 `1.` `2.` 格式 |
| GV-6 | 使用表格形式呈现关键信息 | FIFE L1-1 表格约束 | 检测 Markdown 表格语法 |
| GV-7 | 以 JSON 格式输出 | IFEval `detectable_format:json_format` | JSON parse 验证 |
| GV-8 | 必须包含关键词{kw1}、{kw2} | IFEval `keywords:existence` | 关键词匹配 |
| GV-9 | 不得出现"{forbidden_word}" | IFEval `keywords:forbidden_words` | 关键词排除检测 |
| GV-10 | 开头第一个词必须是"{word}" | IFEval `startend:end_checker` | 首词匹配 |
| GV-11 | 使用 Checkbox 格式 `[ ]`/`[x]` | FIFE L1-6 Checkbox（24 entries） | regex 检测 `[ ]`/`[x]` |
| GV-12 | 输出必须包含代码块/公式块 | FIFE L1-11 代码块（10 entries） | 检测 ``` 标记 |
| GV-13 | 精确首行/末行必须为指定文本 | FIFE L1-2 精确文本匹配（37 entries） | 首末行精确匹配 |
| GV-14 | 每个 Bullet 以指定词/符号开头 | FIFE L1-5.4 指定前缀 | regex 逐项检测 |

---

## 二、GN — 通用 Non-verifiable（7 条）

> 验证方式：LLM-as-judge
> 分类学框架：FollowSoftConstraint (Ren et al., ACL 2025 Findings) Content / Style 分类

| ID | 约束内容 | 主要来源 | Soft Constraint 类别 |
|---|---|---|---|
| GN-1 | 先给出结论，再给出分析过程 | FollowBench Content Constraint | Content: Specifying Sequence |
| GN-2 | 回答末尾必须包含一段总结 | FollowBench Content Constraint | Content: Mandate Structure |
| GN-3 | 使用正式书面语，不得口语化 | FollowBench Style Constraint | Style: Tone |
| GN-4 | 使用客观中立的语气，不带主观倾向 | FollowBench Style Constraint | Style: Tone/Emotion |
| GN-5 | 段落间必须逻辑连贯，有明确过渡 | FollowBench Content Constraint | Content: Mandate Structure |
| GN-6 | 避免重复内容，每段应提供新信息 | 通用写作质量规范 | Content: Set Higher Standard |
| GN-7 | 使用类比或举例来辅助解释 | FollowBench Content Constraint | Content: Introduce Specific Criteria |

**互斥关系**：无（全部可任意组合）
**推荐组合**：GN-1 + GN-2 → "总-分-总"结构；GN-3 + GN-4 → 正式+中立

---

## 三、FV — 金融 Verifiable（7 条）

> 验证方式：regex / 规则检测，金融领域特有

| ID | 约束内容 | 主要来源 | 验证方式 |
|---|---|---|---|
| FV-1 | 末尾必须包含风险提示声明 | FIFE L1-2.2 免责声明 + 中国金融合规 | regex 匹配"风险提示"/"投资有风险" |
| FV-2 | 必须声明"不构成投资建议" | FIFE L1-2.4 精确引用 + 中国监管要求 | 精确短语匹配 |
| FV-3 | 条件触发：若出现X则必须追加Y | FIFE L1-12 条件逻辑（6 entries） | regex 先检测X，再检测Y |
| FV-4 | 按指定字段排序输出 | FIFE L1-10 排序/过滤（11 entries） | 解析数值 + 检查排序 |
| FV-5 | 货币符号规范化（¥→CNY, $→USD） | FIFE L1-9 货币格式（6 entries） | regex 检测残留 ¥/$ 符号 |
| FV-6 | 必须标注风险等级（R1-R5） | 中国银行理财产品说明书规范 | regex 检测 R1-R5 |
| FV-7 | 必须包含投资评级词 | 券商研报行业惯例 | regex 匹配"买入/增持/中性/减持/卖出" |

---

## 四、FN — 金融 Non-verifiable（17 条）

> 验证方式：LLM-as-judge
> 分类学框架：FollowBench + SciIF + FollowSoftConstraint (ACL 2025)

### 4.1 视角/立场类（5 条）

来源：FollowBench Content Constraint + FollowSoftConstraint Situation: Specify Role

| ID | 约束内容 | 备注 |
|---|---|---|
| FN-1 | 从风险管理的角度分析 | |
| FN-2 | 站在监管机构的立场回答 | |
| FN-3 | 从零售投资者的视角分析 | |
| FN-4 | 从 ESG 角度评价 | |
| FN-5 | 从宏观经济的角度分析 | |

### 4.2 规范/质量类（4 条）

来源：SciIF + FollowBench

| ID | 约束内容 | 主要来源 | 备注 |
|---|---|---|---|
| FN-6 | 注明所引用信息的来源 | SciIF Generate-then-Audit | |
| FN-7 | 专业术语缩写需给全称 | SciIF Terminology 族 | **与 FN-8 互斥** |
| FN-8 | 用通俗语言，避免专业术语 | FollowBench Style Constraint | **与 FN-7 互斥** |
| FN-9 | 仅基于提供的材料作答 | SciIF Boundary Conditions | |

### 4.3 定量/证据类（2 条）

来源：SciIF Numerical Methods

| ID | 约束内容 | 备注 |
|---|---|---|
| FN-10 | 必须引用具体财务指标数据 | 如"ROE为15.3%" |
| FN-11 | 必须包含定量分析 | 比 FN-10 更宽泛，含趋势/比较等 |

### 4.4 语言规范类（2 条，从其他模块转入）

| ID | 约束内容 | 原 ID | 转入原因 |
|---|---|---|---|
| FN-12 | 非金融领域术语不得使用英文 | 原 GV-11 | 领域术语边界模糊，需 LLM 判断 |
| FN-13 | 至少包含{N}个专业金融术语 | 原 FV-3 | 术语识别需 LLM 判断 |

### 4.5 场景/风格类（4 条，从 FollowSoftConstraint 吸收）

来源：Ren et al., "Step-by-Step Mastery", ACL 2025 Findings

| ID | 约束内容 | Soft Constraint 类别 | 金融场景参数举例 |
|---|---|---|---|
| FN-14 | 假设当前处于{市场环境}下进行分析 | Situation: Define Context | 熊市 / 牛市 / 加息周期 / 流动性紧缩 |
| FN-15 | 以{目标}为首要考量 | Situation: Prioritize Outcomes | 资本保全 / 收益最大化 / 风险最小化 / 合规优先 |
| FN-16 | 以{文档类型}的风格撰写 | Style: Writing Mimicry | 券商研报 / 财经新闻 / 投资备忘录 / 监管公告 |
| FN-17 | 在假设{条件}的前提下进行分析 | Situation: Add Dependencies | 利率上升50bp / GDP增速降至3% / 人民币贬值5% |

---

## 互斥约束对

组合时不可同时出现在一个 prompt 中：

| 约束 A | 约束 B | 冲突原因 |
|---|---|---|
| FN-7 专业术语缩写给全称 | FN-8 用通俗语言避免术语 | 要求相反 |

---

## 约束来源引用

| 来源 | 文献 | 贡献 |
|---|---|---|
| IFEval | Zhou et al., 2023 (Google) | GV 基础约束（长度/格式/关键词/语言） |
| FIFE | Georgia Tech, NeurIPS 2025 | GV 高级格式 + FV 金融格式约束 |
| FollowBench | Jiang et al., 2023 | GN 内容/风格约束 + FN 视角约束 |
| SciIF | Wang et al., 2025 | FN 规范/质量/定量约束 |
| FollowSoftConstraint | Ren et al., ACL 2025 Findings | Soft Constraint 三分类学 + FN 场景/风格约束 |
| 中国金融监管规范 | 证监会/银保监会 | FV 合规约束（风险等级/投资建议免责） |
