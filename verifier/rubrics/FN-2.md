# FN-2

- constraint_text: 站在监管机构的立场回答
- description: 要求采用监管者立场关注合规与稳定性
- source: FollowBench Content Constraint + FollowSoftConstraint Situation: Specify Role
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断回答是否体现监管机构立场，而不是投资者或营销立场。

## Continuous 10 Anchors

- `10`: 关注合规、稳健、信息披露、系统性风险等监管关切。
- `5`: 部分体现监管视角，但不够稳定。
- `0`: 主要还是从市场参与者立场出发。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 是否强调合规与审慎
- 是否关注市场稳定/投资者保护
- 是否避免营销式立场
