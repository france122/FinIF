# GN-3

- constraint_text: 使用正式书面语，不得口语化
- description: 要求整体文风保持正式书面表达
- source: FollowBench Style Constraint
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断文风是否正式、书面，避免口语化和聊天式表达。

## Continuous 10 Anchors

- `10`: 整体正式克制，无明显口语化词汇或聊天语气。
- `5`: 大体正式，但夹杂少量口语化表达。
- `0`: 明显口语化、聊天化或随意。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 是否出现 好的/当然/其实/你可以 这类口语
- 句式是否偏书面
- 整体是否像正式报告或说明
