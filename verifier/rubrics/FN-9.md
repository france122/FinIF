# FN-9

- constraint_text: 仅基于提供的材料作答
- description: 要求回答不越界，不引入材料外事实
- source: SciIF Boundary Conditions
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断回答是否严格基于给定材料，不额外编造材料外事实。

## Continuous 10 Anchors

- `10`: 结论和证据都能在材料中找到依据，没有越界扩展。
- `5`: 大体基于材料，但有轻微外推。
- `0`: 明显引入材料外事实或臆断。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 是否出现材料未提供的事实
- 外推是否过度
- 结论是否受材料支撑
