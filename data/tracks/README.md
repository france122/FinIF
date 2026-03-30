# Track Artifacts Index

本目录同时保留了当前主线产物、历史口径产物和少量临时调试文件。为了避免后续 session 误用，建议优先按下面的优先级理解。

## 当前主线

以下文件对应当前 `550 query / 5500 tracks / 4420 parameterization requests` 口径：

- `id_heldout_v_track.json`
- `id_heldout_nv_track.json`
- `id_heldout_mixed_track.json`
- `id_heldout_all_tracks.json`
- `llm_constraint_parameterization_jobs.json`
- `llm_constraint_parameters_ds_5500_run1.json`
- `llm_constraint_parameters_ds_5500_run1.failures.json`

其中：

- `id_heldout_*_track.json` 与 `id_heldout_all_tracks.json` 是当前占位符版 track
- `llm_constraint_parameterization_jobs.json` 是当前逐条 LLM 填参请求
- `llm_constraint_parameters_ds_5500_run1.json` 是当前最新一轮 DeepSeek 首轮填参结果
- `llm_constraint_parameters_ds_5500_run1.failures.json` 保存了首轮失败记录，供后处理和 targeted rerun 使用

## 当前状态说明

当前 `llm_constraint_parameters_ds_5500_run1.json` 的 meta 显示：

- `total_requests = 4420`
- `completed_records = 4420`
- `failures = 162`
- `manual_filled = 162`

因此当前状态应理解为：

- 首轮 DS 跑批已经完成
- 但结果还没有经过最终的 `post-check`
- 也还没有完成坏样本重跑
- 在 post-check / rerun 完成前，不建议直接把它当作最终正式版本覆盖历史稳定文件

## 历史或待降级文件

以下文件保留历史意义，但不应默认当作当前主线结果：

- `llm_constraint_parameters.json`
- `id_heldout_v_track_filled.json`
- `id_heldout_nv_track_filled.json`
- `id_heldout_mixed_track_filled.json`
- `id_heldout_all_tracks_filled.json`
- `llm_parameterization_manifest.json`
- `quality_review_summary.json`

这些文件大多对应：

- 更早的 `2022` 样本口径
- 或更早一轮回填/清洗结果
- 或尚未基于当前 `5500` 口径重新物化

如果要生成当前正式 filled 版本，建议下一步流程是：

1. 对 `llm_constraint_parameters_ds_5500_run1.json` 做 `post-check`
2. 仅对坏样本做 targeted rerun
3. 产出新的正式参数文件
4. 再运行 `materialize_tracks_with_llm_params.py`

## 历史 clean 口径

以下目录对应旧 clean 训练版流程，保留作参考：

- `cleaned/`
- `constraint_conflict_data/`

它们基于更早一轮 `GV-9` 冲突清理逻辑，不应直接视为当前 `5500` 主线的 clean 结果。

## 临时 / 冒烟文件

以下文件主要用于本轮调试和冒烟：

- `llm_constraint_parameters_ds_smoke.json`
- `llm_constraint_parameters_ds_smoke_5500_tmp.json`
- `manual_constraint_parameters_gold_20.json`

其中：

- `llm_constraint_parameters_ds_smoke_5500_tmp.json` 是当前 `5500` 口径的 DS 冒烟结果
- `manual_constraint_parameters_gold_20.json` 是人工金标小样本，不是主结果

## 推荐读取顺序

如果是新 session 接手，建议按以下顺序理解本目录：

1. 先看 `README.md`
2. 再看 `llm_constraint_parameters_ds_5500_run1.json`
3. 再看 `llm_constraint_parameters_ds_5500_run1.failures.json`
4. 再决定是否需要读取历史 `filled` / `cleaned` 文件
