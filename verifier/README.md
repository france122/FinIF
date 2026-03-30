# Verifier Framework

本目录用于把约束评测拆成两条线：

- `rules/`: 能确定性判断的约束，尽量用代码规则检查
- `rubrics/`: 规则难以稳定覆盖的约束，改为 LLM-as-judge prompt/rubric

设计原则：

1. `verifiability` 和 `check_mode` 分开存储，统一以 `docs/constraint_reference_table.csv` 为权威来源
2. `registry.py` 只按 `check_mode` 分发，不再由 `verifiability` 推导
3. `constraint_id` 的 `G/F` 表示通用/金融，`V/N` 表示可验证/不可验证
4. `V` 不等于 `rule`，允许出现 `verifiable + rubric`
5. 评分统一走 `0-10` 框架：
   - `binary_10`
   - `ternary_10`
   - `continuous_10`
6. 规则与 rubric 分开维护，不混在一个大文件里
7. 文件按 `constraint_id` 拆开，后续可单独迭代

目录结构：

```text
verifier/
  base.py
  registry.py
  rule_runner.py
  rubric_runner.py
  rules/
    _shared.py
    GV-1.py
    ...
  rubrics/
    GV-15.md
    ...
```

常用入口：

- `verifier/rule_runner.py`: 运行某个 rule checker
- `verifier/rubric_runner.py`: 构造某个 rubric 的 judge prompt
- `scripts/generate_verifier_scaffold.py`: 批量生成 `rules/` 与 `rubrics/` 下的按约束拆分文件
- `docs/verifier_reference_table.md`: 以 Markdown 表格查看当前 verifier 全貌
