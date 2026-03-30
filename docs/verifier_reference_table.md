# Verifier Reference Table

本文件用于以更适合人工阅读的 Markdown 方式展示当前 verifier 全貌。

- 权威来源：`docs/constraint_reference_table.csv`
- 代码入口：`verifier/registry.py`
- 分发原则：**只按 `check_mode` 分发**，不再由 `verifiability` 推导

## Summary

| item | count | note |
| --- | --- | --- |
| total constraints | 46 | 当前全部约束 |
| rule | 22 | 规则检查，统一 `binary_10` |
| rubric | 24 | LLM-as-judge，含 `ternary_10` / `continuous_10` |
| GV | 17 | 通用可验证约束 |
| FV | 12 | 金融可验证约束 |
| GN | 5 | 通用不可验证约束 |
| FN | 12 | 金融不可验证约束 |

## Mapping Notes

| field | 含义 |
| --- | --- |
| `verifiability` | 约束本体是否属于可验证范畴 |
| `check_mode` | 实现层走 `rule` 还是 `rubric` |
| `score_type` | 统一 `0-10` 评分框架下的打分离散度 |

| check_mode | implementation path |
| --- | --- |
| `rule` | `verifier/rules/<constraint_id>.py` |
| `rubric` | `verifier/rubrics/<constraint_id>.md` |

| score_type | 说明 |
| --- | --- |
| `binary_10` | 只允许 `0/10` |
| `ternary_10` | 只允许 `0/5/10` |
| `continuous_10` | 允许 `0-10` 连续打分，`10/5/0` 为 anchor |

## Rule Constraints

| constraint_id | module | verifiability | check_mode | score_type | implementation | constraint_text |
| --- | --- | --- | --- | --- | --- | --- |
| `GV-1` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-1.py` | 回答不超过`{N}`个字 |
| `GV-2` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-2.py` | 至少包含`{N}`个句子 |
| `GV-3` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-3.py` | 回答分为`{N}`个段落 |
| `GV-4a` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-4a.py` | 使用 Markdown 格式 |
| `GV-4b` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-4b.py` | 包含至少`{N}`级标题层级 |
| `GV-5` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-5.py` | 使用编号列表组织回答 |
| `GV-6` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-6.py` | 使用表格形式呈现关键信息 |
| `GV-7` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-7.py` | 以 JSON 格式输出 |
| `GV-8` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-8.py` | 必须包含关键词：`{kw1}`、`{kw2}` |
| `GV-9` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-9.py` | 不得出现“`{forbidden_word}`” |
| `GV-10` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-10.py` | 开头第一个词必须是“`{word}`” |
| `GV-11` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-11.py` | 使用 Checkbox 格式 `[ ]/[x]` |
| `GV-12` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-12.py` | 输出必须包含代码块/公式块 |
| `GV-13` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-13.py` | 第一行必须为“`{first_line}`”，最后一行为“`{last_line}`” |
| `GV-14` | `GV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/GV-14.py` | 每个 bullet 必须以“`{prefix}`”开头 |
| `FV-1` | `FV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/FV-1.py` | 末尾必须包含风险提示声明：`{risk_line}` |
| `FV-2` | `FV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/FV-2.py` | 必须声明“`{disclaimer}`” |
| `FV-3` | `FV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/FV-3.py` | 若提到“`{trigger}`”，必须同时补充“`{followup}`” |
| `FV-4` | `FV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/FV-4.py` | 按`{order_field}`从高到低排序输出 |
| `FV-5` | `FV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/FV-5.py` | 若出现金额，统一使用 `{currency_rule}` 表示 |
| `FV-6` | `FV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/FV-6.py` | 必须标注风险等级（R1-R5） |
| `FV-7` | `FV` | `verifiable` | `rule` | `binary_10` | `verifier/rules/FV-7.py` | 必须包含投资评级词 |

## Rubric Constraints

| constraint_id | module | verifiability | check_mode | score_type | implementation | constraint_text | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GV-15` | `GV` | `verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/GV-15.md` | 先给出结论，再给出分析过程 | 原 `GN-1` |
| `GV-16` | `GV` | `verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/GV-16.md` | 回答末尾必须包含一段总结 | 原 `GN-2` |
| `GN-3` | `GN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/GN-3.md` | 使用正式书面语，不得口语化 | |
| `GN-4` | `GN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/GN-4.md` | 使用客观中立的语气，不带主观倾向 | |
| `GN-5` | `GN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/GN-5.md` | 段落间必须逻辑连贯，有明确过渡 | |
| `GN-6` | `GN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/GN-6.md` | 避免重复内容，每段应提供新信息 | |
| `GN-7` | `GN` | `non_verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/GN-7.md` | 使用类比或举例来辅助解释 | |
| `FV-8` | `FV` | `verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FV-8.md` | 从 ESG 角度评价 | 原 `FN-4` |
| `FV-9` | `FV` | `verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FV-9.md` | 注明所引用信息的来源 | 原 `FN-6` |
| `FV-10` | `FV` | `verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FV-10.md` | 专业术语缩写需给全称 | 原 `FN-7` |
| `FV-11` | `FV` | `verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FV-11.md` | 必须引用具体财务指标数据 | 原 `FN-10` |
| `FV-12` | `FV` | `verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FV-12.md` | 必须包含定量分析 | 原 `FN-11` |
| `FN-1` | `FN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/FN-1.md` | 从风险管理的角度分析 | |
| `FN-2` | `FN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/FN-2.md` | 站在监管机构的立场回答 | |
| `FN-3` | `FN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/FN-3.md` | 从零售投资者的视角分析 | |
| `FN-5` | `FN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/FN-5.md` | 从宏观经济的角度分析 | |
| `FN-8` | `FN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/FN-8.md` | 用通俗语言，避免专业术语 | |
| `FN-9` | `FN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/FN-9.md` | 仅基于提供的材料作答 | |
| `FN-12` | `FN` | `non_verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FN-12.md` | 非金融领域术语不得使用英文 | |
| `FN-13` | `FN` | `non_verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FN-13.md` | 至少包含`{N}`个专业金融术语 | |
| `FN-14` | `FN` | `non_verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FN-14.md` | 假设当前处于`{市场环境}`下进行分析 | |
| `FN-15` | `FN` | `non_verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FN-15.md` | 以`{目标}`为首要考量 | |
| `FN-16` | `FN` | `non_verifiable` | `rubric` | `continuous_10` | `verifier/rubrics/FN-16.md` | 以`{文档类型}`的风格撰写 | |
| `FN-17` | `FN` | `non_verifiable` | `rubric` | `ternary_10` | `verifier/rubrics/FN-17.md` | 在`{条件}`这一假设下进行分析 | |

## Maintenance Note

如果后续新增、删除或调整约束，优先更新 `docs/constraint_reference_table.csv`；本文件应视为更适合人工浏览的镜像视图。

