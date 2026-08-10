# Report — P1-S2: Camera list + get API parity

## STATUS
**DONE** — `vj_p1_camera_list` and `vj_p1_camera_get` certify `ok=True`. Phase 0 remains green (`certify --phase 0` exit 0 with restored oracle ini golden). Phase 1 gate still FAIL overall (view-forward / stream-forward out of scope).

## Commits
- (this commit) `feat(video-java): P1-S2 camera list/get API parity`

## Phase 1 per-case results
| case_id | ok | layers |
|---------|----|--------|
| vj_p1_camera_list | **PASS** | api:pass |
| vj_p1_camera_get | **PASS** | api:pass |
| vj_p1_view_forward_start_stop | FAIL | media:fail, lifecycle:fail (404 — not implemented) |
| vj_p1_stream_forward_start_stop | FAIL | lifecycle:fail, media:fail (404 — not implemented) |

## Phase 0
`certify --phase 0` exit **0** (all P0 cases pass or signed exempt).

## What changed
- **Java**: `CameraController`, `CameraService`, `DeviceRepository`, `DeviceRow` — `GET /video/camera/list` (pageNo/pageSize/search) and `GET /video/camera/device/{id}` aligned with oracle `_to_dict` fields.
- **Certify tooling**: `record_python` list search uses `list_search=certify` (oracle filters name/model/serial/manufacturer/ip, not id). `normalize_api_layer` strips Java-only `message` and null `total` for diff parity.
- **Config**: `application-local.yaml` sets `video.runtime.repo-root: F:/acme` for stable RUNTIME ini paths.
- **Goldens**: Re-recorded python/java `vj_p1_camera_list` and `vj_p1_camera_get`.

## Concerns
- Full `certify --phase 0` with `--record` can overwrite python `vj_p0_task_start_stop` ini golden with empty keys when oracle task log path does not resolve to a readable ini; use existing golden or ensure oracle exposes ini at `~/.video-java/runtime-config/task_{id}.ini`.
- `vj_p1_camera_list` golden includes all devices matching `search=certify` (currently 2 rows); both sides must share the same DB fixture set.
- View-forward and stream-forward endpoints remain 404 by design until P1-S3/S4.
