# Scripts Index

本目录包含当前主线脚本、生成辅助脚本和历史清洗相关脚本。为了避免混用，建议先按“当前主线流水线”理解。

## 当前主线流水线

当前 `550 query / 5500 tracks` 主线推荐按以下顺序使用：

1. `generate_query_pool_v2.py`
2. `build_id_heldout_tracks.py`
3. `build_constraint_parameterization_jobs.py`
4. `fill_constraint_parameters.py`
5. `materialize_tracks_with_llm_params.py`

## 各脚本作用

### `generate_query_pool_v2.py`

- 生成最新 query pool
- 当前口径是：先对裸 `query input` 去重，再注入约 `1/3` 的角色前缀
- 同时生成 `viewer/query_pool_v2_viewer.html`

### `build_id_heldout_tracks.py`

- 基于 query pool 构建 `ID-heldout` 划分和三类 track
- 当前主线比例为 `5 : 3 : 2`
- 产出占位符版 track 与 `viewer/id_heldout_tracks_viewer.html`

### `constraint_parameterization.py`

- 定义参数化约束元信息、prompt 构造和参数校验逻辑
- 是 LLM 填参与后续回填流程共用的基础模块
- 如果修改参数规则，通常需要同步关注这个文件

### `build_constraint_parameterization_jobs.py`

- 从占位符版 track 中导出逐条参数化 job
- 当前主线输出为 `data/tracks/llm_constraint_parameterization_jobs.json`

### `fill_constraint_parameters.py`

- 调用 LLM 为参数化约束填写参数
- 支持 `openai_compatible` 与 `minimax_proxy`
- 当前最新首轮 run 对应输出是 `data/tracks/llm_constraint_parameters_ds_5500_run1.json`

### `materialize_tracks_with_llm_params.py`

- 将 LLM 参数结果回填到占位符版 track 中
- 产出 filled tracks、manifest、quality summary 和 filled viewer
- 在当前主线中，建议放在 post-check / bad-case rerun 之后再运行

## 生成辅助脚本

### `generate_verifier_scaffold.py`

- 根据约束表生成 verifier scaffold / rubric 文件
- 主要用于 verifier 体系维护，不属于每次数据重建都要跑的日常主线

## 历史或专项处理脚本

### `filter_constraint_conflicts.py`

- 对已回填样本做规则化冲突筛查与 clean 版导出
- 当前保留的是较早一轮 `GV-9` 冲突清理流程
- 更适合视为历史 clean 方案，而不是当前 `5500` 主线默认步骤

### `fill_remaining_conflicts.py`

- 用于补处理或修补剩余冲突记录
- 更偏专项修复脚本，不建议当作主线入口

## 推荐入口

如果是新 session 接手，建议按下面顺序阅读：

1. 根目录 `README.md`
2. `data/tracks/README.md`
3. 本文件 `scripts/README.md`
4. 再决定是否进入具体脚本源码
