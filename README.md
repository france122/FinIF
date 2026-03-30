# Chinese Financial Instruction-Following Benchmark

本仓库用于构建中文金融垂类 `Instruction Following` 基准，重点关注模型在金融场景下对多类约束的遵循能力。

当前版本提供：

- 面向开放式金融任务的 `query pool`
- 按可验证性划分的 `V / NV / Mixed` 三类评测 track
- 数据生成与划分脚本
- 约束池、模板迁移与角色映射文档

## Project Overview

本项目将中文金融 IF 评测拆分为两个层面：

- `Query`：开放式金融任务，覆盖建议、诊断、工具使用、对客解释等场景
- `Constraint`：附加在 query 上的输出要求，分为可自动验证与需主观评判两类

query 的主要来源与构造方式如下：

- 保留 `FinEval` 中更开放的 4 类任务：`finsuggestion`、`findiag`、`apiutil`、`finsales`
- 参考 `FIFE` 抽取可迁移的开放式任务模板，并改写为中文金融语境
- 借助 `CFinBench` 提供角色、岗位与法规语境，用于部分 query 的角色增强

## Current Release

- `550` 条去重后的 query
- `5500` 条 track 样本
- `440 / 110` 的 query 级 `ID held-out` 划分

其中：

- `113` 条来自 `FinEval` 原始开放任务
- `437` 条来自 `FIFE` 中文化模板实例化
- `183` 条带角色设定，`367` 条不带角色设定
- query pool 构建阶段先生成 `1002` 条候选 query，先按裸 `query input` 文本去重，再注入角色前缀

三类 track 为：

- `V-track`：以可验证约束为主
- `NV-track`：以非可验证约束为主
- `Mixed-track`：混合可验证与非可验证约束

当前 track 生成比例为 `5 : 3 : 2`，即每条 query 生成：

- `5` 条 `V-track`
- `3` 条 `NV-track`
- `2` 条 `Mixed-track`

当前参数化阶段的最新状态：

- 参数化请求总数：`4420`
- 最新 DeepSeek 跑批结果：`data/tracks/llm_constraint_parameters_ds_5500_run1.json`
- 该结果文件的最新 meta 显示：`completed_records = 4420`
- 同时显示：`failures = 162`、`manual_filled = 162`
- 因此当前结果可视为**已完成首轮跑批**，但**post-check / bad-case rerun 尚未完成**

## Repository Structure

```text
.
├── docs/      # constraint pool, template notes, role mapping
├── scripts/   # query generation, track construction, parameter filling
├── data/      # raw inputs, final query pool, splits, tracks
└── viewer/    # standalone HTML viewers for inspection
```

## Data Files

核心数据文件包括：

- `data/tracks/README.md`（当前主线产物、历史产物与临时文件的总索引，建议先读）
- `data/query_pool/query_pool_v2_final.json`
- `data/splits/id_heldout_train_queries.json`
- `data/splits/id_heldout_test_queries.json`
- `data/tracks/id_heldout_v_track.json`
- `data/tracks/id_heldout_nv_track.json`
- `data/tracks/id_heldout_mixed_track.json`
- `data/tracks/id_heldout_all_tracks.json`（占位符版参数化约束）
- `data/tracks/llm_constraint_parameterization_jobs.json`（逐条 LLM 填参 job）
- `data/tracks/llm_constraint_parameters_ds_5500_run1.json`（当前 `5500` 口径的 DS 首轮填参结果）
- `data/tracks/llm_constraint_parameters_ds_5500_run1.failures.json`（首轮失败 / 待后处理记录）
- `data/tracks/llm_constraint_parameters.json`（旧版或历史稳定结果，不再默认代表当前 `5500` 口径）
- `data/tracks/id_heldout_all_tracks_filled.json`（历史回填结果，当前不默认代表最新 `5500` 口径）
- `data/tracks/cleaned/id_heldout_all_tracks_filled.json`（旧 clean 训练版结果，基于历史口径）
- `data/tracks/constraint_conflict_data/`（历史被移出的冲突样本归档）

建议：

- 如果要确认“当前最新主线结果”，先看 `data/tracks/README.md`
- 如果要追溯历史 clean 流程，再看 `data/tracks/cleaned/` 与 `data/tracks/constraint_conflict_data/`

## Current Mainline Workflow

建议按当前主线顺序理解和复现：

1. 生成 query pool

```bash
python scripts/generate_query_pool_v2.py
```

2. 构建 `ID-heldout` 划分与 placeholder tracks

```bash
python scripts/build_id_heldout_tracks.py --param-mode placeholders
```

3. 导出参数化约束 jobs

```bash
python scripts/build_constraint_parameterization_jobs.py
```

4. 调用 LLM 填写参数

```bash
python scripts/fill_constraint_parameters.py --model deepseek-chat --base-url https://api.deepseek.com/v1
```

5. 对填参结果做 `post-check` 与坏样本重跑

- 当前项目中，这一步还没有被完全整理成最终主线脚本
- 当前最新首轮 run 是 `data/tracks/llm_constraint_parameters_ds_5500_run1.json`
- 当前最新失败记录是 `data/tracks/llm_constraint_parameters_ds_5500_run1.failures.json`

6. 在 post-check 完成后，再回填 filled tracks

```bash
python scripts/materialize_tracks_with_llm_params.py
```

## Entry Points

建议新接手时先读这些索引文件：

- `data/tracks/README.md`
- `scripts/README.md`
- `viewer/README.md`

生成结果会分别写入 `data/` 与 `viewer/`。当前 viewer 的理解方式为：

- `viewer/query_pool_v2_viewer.html`：当前 query pool viewer
- `viewer/id_heldout_tracks_viewer.html`：当前 placeholder tracks viewer
- `viewer/id_heldout_tracks_viewer_filled.html`：filled viewer，只有在最新参数结果完成 post-check 后才适合作为主线结果
- `viewer/id_heldout_tracks_viewer_clean.html`：历史 clean viewer

## Documentation

- `docs/constraint_pool.md`：当前约束池定义
- `docs/FIFE_template_candidates.md`：FIFE 模板迁移说明
- `docs/CFinBench_role_mapping.md`：CFinBench 角色与法规语境映射
- `docs/mainline_file_map.md`：当前主线文件、条件性主线文件与历史/未采用文件的区分清单
- `scripts/README.md`：脚本职责索引
- `viewer/README.md`：viewer 用途索引

## Notes

- 角色信息当前作为 `query` 层数据增强变量，而非核心约束指标
- query pool 在构建阶段已先按裸 `query input` 做文本级去重，再注入角色前缀
- 训练/测试划分先在 `query` 级完成，再分别混合 constraint，以减少数据泄漏
- 当前测试集定位为 `in-domain held-out`
- 当前项目同时保留“最新 `5500` 口径”与“历史 `2022` / clean 口径”文件，使用时需注意区分
- `GV-9`、`GV-8`、`GV-10`、`FV-5` 的参数质量后处理已被明确列为下一步任务
