# FN-8

- constraint_text: 用通俗语言，避免专业术语
- description: 要求尽量降低专业术语密度并提高可读性
- source: FollowBench Style Constraint
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断语言是否通俗易懂，尽量避免密集专业术语。

## Continuous 10 Anchors

- `10`: 表达面向非专业读者，术语少且必要时有解释。
- `5`: 总体可懂，但仍有较多未解释术语。
- `0`: 术语密集、生硬专业，不够通俗。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 术语密度是否偏高
- 复杂概念是否被解释
- 普通读者是否容易理解
