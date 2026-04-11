请为以下 query 生成 4 条 track（约束组合）。

## Query

query_id: {query_id}

{query_text}

## 要求

按系统指令中定义的 4 种 track type，各生成 1 条 track。从约束池中选择与该 query 语义适配的约束，确保 4 条 track 之间约束覆盖尽可能多样化。对含参数的约束进行参数化填充。遵守互斥规则和多样性规则。严格输出 JSON 数组。
