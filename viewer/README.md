# Viewer Index

本目录保存 query pool 与 track 的静态 HTML viewer。当前目录中同时存在主线 viewer 和历史 viewer，使用前建议先区分。

## 当前主线 viewer

### `query_pool_v2_viewer.html`

- 对应当前最新 query pool
- 口径为：先对裸 `query input` 去重，再注入角色前缀
- 通常由 `scripts/generate_query_pool_v2.py` 生成

### `id_heldout_tracks_viewer.html`

- 对应当前最新占位符版 tracks
- 展示的是 `5500` 样本口径下的 placeholder tracks
- 通常由 `scripts/build_id_heldout_tracks.py` 生成

## 条件性主线 viewer

### `id_heldout_tracks_viewer_filled.html`

- 由 `scripts/materialize_tracks_with_llm_params.py` 生成
- 只有在当前参数结果已经完成 post-check / bad-case rerun 后，才适合视为当前主线 filled viewer
- 如果尚未基于最新 `5500` 主线重新物化，则它更可能是历史 filled viewer

## 历史 clean viewer

### `id_heldout_tracks_viewer_clean.html`

- 对应较早一轮 clean 流程
- 主要服务于历史 `GV-9` 冲突清理后的样本查看
- 不应直接当作当前 `5500` 主线的 clean viewer

## 推荐使用顺序

如果只是查看当前主线状态，建议按下面顺序打开：

1. `query_pool_v2_viewer.html`
2. `id_heldout_tracks_viewer.html`
3. 在 post-check 完成后，再看 `id_heldout_tracks_viewer_filled.html`

## 与脚本的对应关系

- `generate_query_pool_v2.py` -> `query_pool_v2_viewer.html`
- `build_id_heldout_tracks.py` -> `id_heldout_tracks_viewer.html`
- `materialize_tracks_with_llm_params.py` -> `id_heldout_tracks_viewer_filled.html`
- `filter_constraint_conflicts.py` -> `id_heldout_tracks_viewer_clean.html`
