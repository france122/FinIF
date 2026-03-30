# FN-3

- constraint_text: 从零售投资者的视角分析
- description: 要求回答面向普通投资者的决策关切
- source: FollowBench Content Constraint + FollowSoftConstraint Situation: Specify Role
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断回答是否真正站在零售投资者视角，而非机构或监管视角。

## Continuous 10 Anchors

- `10`: 重点讨论普通投资者可理解、可执行的风险收益权衡。
- `5`: 有部分零售投资者关切，但不够充分。
- `0`: 明显不是零售投资者视角。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 是否考虑门槛/流动性/本金安全
- 是否表达清晰易懂
- 是否避免机构化视角主导
