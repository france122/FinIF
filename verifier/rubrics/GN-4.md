# GN-4

- constraint_text: 使用客观中立的语气，不带主观倾向
- description: 要求避免情绪化和立场化表达
- source: FollowBench Style Constraint
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断语气是否客观中立，避免主观煽动或情绪化措辞。

## Continuous 10 Anchors

- `10`: 措辞克制客观，结论基于条件或证据，不带明显主观倾向。
- `5`: 大体中立，但存在轻微主观色彩。
- `0`: 明显带有主观倾向、情绪性判断或煽动性措辞。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 是否有绝对化断言
- 是否有情绪化褒贬
- 是否保持分析式、中性式表达
