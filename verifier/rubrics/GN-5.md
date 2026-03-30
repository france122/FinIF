# GN-5

- constraint_text: 段落间必须逻辑连贯，有明确过渡
- description: 要求段落衔接自然并具有清晰过渡
- source: FollowBench Content Constraint
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断段落之间是否有逻辑推进和过渡，而不是堆砌信息。

## Continuous 10 Anchors

- `10`: 段落承接清晰，有明显逻辑顺序或过渡提示。
- `5`: 基本有逻辑，但个别段落切换生硬。
- `0`: 段落之间缺少承接，像信息拼接。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 段落是否围绕同一主线推进
- 是否有过渡句或过渡词
- 是否存在明显跳跃
