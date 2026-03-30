# 主线文件清单

这份清单的目的，是把当前项目里三类文件明确区分开：

1. **已跑通主线**：已经在当前 `550 query / 5500 tracks / 4420 requests` 流程里实际使用并跑通
2. **主线下一步 / 条件性文件**：属于当前主线，但还要等 `post-check / rerun` 完成后才进入正式结果
3. **尝试过但当前不采用 / 历史遗留**：保留参考价值，但不应默认当作当前主线入口或结果

---

## 1. 已跑通主线

这些文件属于**当前已经实际跑通**的主线 pipeline。

### 入口与索引

- `README.md`
- `data/tracks/README.md`
- `scripts/README.md`
- `viewer/README.md`

### 主线脚本

- `scripts/generate_query_pool_v2.py`
- `scripts/build_id_heldout_tracks.py`
- `scripts/constraint_parameterization.py`
- `scripts/build_constraint_parameterization_jobs.py`
- `scripts/fill_constraint_parameters.py`

### 主线数据产物

- `data/query_pool/query_pool_v2_final.json`
- `data/splits/id_heldout_train_queries.json`
- `data/splits/id_heldout_test_queries.json`
- `data/tracks/id_heldout_v_track.json`
- `data/tracks/id_heldout_nv_track.json`
- `data/tracks/id_heldout_mixed_track.json`
- `data/tracks/id_heldout_all_tracks.json`
- `data/tracks/llm_constraint_parameterization_jobs.json`
- `data/tracks/llm_constraint_parameters_ds_5500_run1.json`
- `data/tracks/llm_constraint_parameters_ds_5500_run1.failures.json`

### 当前主线 viewer

- `viewer/query_pool_v2_viewer.html`
- `viewer/id_heldout_tracks_viewer.html`

### 当前主线文档基座

- `docs/constraint_reference_table.csv`
- `docs/verifier_reference_table.md`
- `docs/constraint_pool.md`
- `docs/FIFE_template_candidates.md`
- `docs/CFinBench_role_mapping.md`

### 说明

其中当前已经跑通的主线阶段是：

1. `generate_query_pool_v2.py`
2. `build_id_heldout_tracks.py`
3. `build_constraint_parameterization_jobs.py`
4. `fill_constraint_parameters.py`

当前已确认首轮 run 状态：

- `total_requests = 4420`
- `completed_records = 4420`
- `failures = 162`
- `manual_filled = 162`

这意味着“**首轮填参已完成**”，但还没有进入最终结果定版阶段。

---

## 2. 主线下一步 / 条件性文件

这些文件**不是没采用**，而是属于当前主线的下一步，或只有在 `post-check / bad-case rerun` 完成后才应被当作正式主线结果。

### 下一步会用到的脚本

- `scripts/materialize_tracks_with_llm_params.py`

### 条件性主线 viewer

- `viewer/id_heldout_tracks_viewer_filled.html`

### 条件性主线产物

- `data/tracks/id_heldout_v_track_filled.json`
- `data/tracks/id_heldout_nv_track_filled.json`
- `data/tracks/id_heldout_mixed_track_filled.json`
- `data/tracks/id_heldout_all_tracks_filled.json`
- `data/tracks/llm_parameterization_manifest.json`
- `data/tracks/quality_review_summary.json`

### 为什么暂时不算“已跑通主线”

因为当前最新 `5500` 主线还处在：

- 首轮 DS 跑批已完成
- `post-check` 尚未完成
- 坏样本 `rerun` 尚未完成

所以上面这些 filled / manifest / quality 文件，**只有在基于最新主线重新物化后**，才能升级成当前正式主线结果。

---

## 3. 尝试过但当前不采用 / 历史遗留

这些文件或流程曾经有用，但**当前不应默认作为主线入口、主线结果或主线评估对象**。

### 历史主结果 / 旧口径结果

- `data/tracks/llm_constraint_parameters.json`
- `data/tracks/cleaned/`
- `data/tracks/constraint_conflict_data/`

这些基本对应：

- 更早的 `2022` 样本口径
- 或更早一轮 clean 流程
- 或更早一轮 filled / manifest 结果

### 历史 clean / 专项脚本

- `scripts/filter_constraint_conflicts.py`
- `scripts/fill_remaining_conflicts.py`

说明：

- `filter_constraint_conflicts.py` 对应较早一轮 `GV-9` 冲突清洗流程
- `fill_remaining_conflicts.py` 属于专项修补脚本，不是当前已跑通主线的一部分
- 它们可以作为后处理参考，但**当前不应默认视为主线 pipeline 的标准步骤**

### 调试 / 冒烟文件

- `data/tracks/llm_constraint_parameters_ds_smoke.json`
- `data/tracks/llm_constraint_parameters_ds_smoke_5500_tmp.json`
- `data/tracks/manual_constraint_parameters_gold_20.json`

这些文件的作用是：

- 冒烟测试
- 小样本人工核验
- 调试对照

它们不是当前正式主结果。

### 历史 viewer

- `viewer/id_heldout_tracks_viewer_clean.html`

说明：

- 它对应较早 clean 流程
- 不应直接当作当前 `5500` 主线的 clean viewer

---

## 4. 一句话判别规则

如果后续有人接手这个项目，可以按下面的简单规则判断：

- **当前主线先看**：`README.md` -> `data/tracks/README.md` -> 本文件
- **当前主线数据先用**：`query_pool_v2_final.json`、`id_heldout_all_tracks.json`、`llm_constraint_parameterization_jobs.json`、`llm_constraint_parameters_ds_5500_run1.json`
- **看到 `cleaned/`、旧 `llm_constraint_parameters.json`、`viewer_clean.html` 时**：默认先按“历史流程/非当前主线”理解
- **看到 `filled` / `manifest` / `quality_review_summary` 时**：先确认它们是否已经基于最新 `5500` 主线重新生成，确认前不要默认当正式结果
