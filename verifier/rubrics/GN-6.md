# GN-6

- constraint_text: 避免重复内容，每段应提供新信息
- description: 要求信息增量明显，避免段落内容重复
- source: 通用写作质量规范
- verifiability: non_verifiable
- check_mode: rubric
- score_type: continuous_10

## Judge Focus

判断每段是否提供新信息，避免重复表述同一点。

## Continuous 10 Anchors

- `10`: 各段信息增量明显，几乎无实质重复。
- `5`: 有少量重复，但整体仍有新增信息。
- `0`: 多段反复表达同一意思，信息增量弱。

允许在 `0-10` 之间给出连续分数，以上 `10/5/0` 作为 anchor。

## Checklist

- 段落之间是否重复观点
- 是否每段有新增角度/事实/建议
- 重复是否影响阅读价值
