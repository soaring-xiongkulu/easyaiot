# FR-B40 Report — 收口 contract_regression 38×404 假阳性

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Root cause

FR-B39 `VideoApiResponseAdvice.businessCodeToHttpStatus` maps business `code=404` → **HTTP 404** (Python-first: `patrol.py` L45). All 39 probe fails were **mapped routes** returning VIDEO API envelope `{"code":404,"msg":…}` — not Spring unmapped 404 (`timestamp/status/error/path`).

Probe used literal `id=1` for `{param}` routes; resources do not exist → business 404. Inventory diff=0 was already correct.

## Before / after

| Metric | Before (FR-B39) | After (FR-B40) |
|--------|-----------------|----------------|
| Inventory diff | 0 | 0 |
| Probes | 265 | 265 |
| Pass | 226–227 | **265** |
| Fail | **38–39** | **0** |
| Skip | 0 | 0 |

Artifact: `logs/fr-b40-contract-latest.json` / `.md`

## Python-first cites (representative fails → mapped business 404)

| Probe route | Python cite | Java handler | Fix |
|-------------|-------------|--------------|-----|
| `GET /video/patrol/session/{param}` | `patrol.py` **L41-45** `jsonify({'code':404}), 404` | `PatrolController` L32-34 | Probe: envelope 404 = pass |
| `GET /video/face/libraries/{param}` | `face_library_service.py` **L184** `get_or_404` | `FaceLibraryService` L39 `VideoBusinessException(404)` | Probe: envelope 404 = pass |
| `DELETE /video/camera/nvr/{param}` | `camera.py` NVR delete | `CameraController` L404-406 | Probe: envelope 404 = pass |
| `GET /video/algorithm/task/{param}/post-process/ide-url` | `algorithm_task.py` `get_or_404` | `AlgorithmTaskController` L160 | Probe: envelope 404 = pass |
| `POST /video/camera/device/{param}/ensure-spaces` | `camera.py` device ensure | `CameraController` L191 | Probe: envelope 404 = pass |
| `POST /video/face/libraries/{param}/match` | `face.py` library routes | `FaceController` L293 | Probe: envelope 404 = pass |
| `PUT /video/plate/libraries/{param}/auto-enroll` | `plate.py` auto-enroll | `PlateController` | Probe: envelope 404 = pass |

Full 39-route list in `logs/fr-b40-contract-latest.json` (all classified `HTTP 404 (mapped, resource not found)` after fix).

## Java / tool fix

**`tools/video_java/contract_regression.py`**

1. `is_video_api_envelope()` — detect `code` + `msg`/`message` JSON body.
2. `classify_http_status()` — HTTP 404 + envelope → **pass** (mapped); bare Spring 404 → fail.
3. `--artifact-stem` flag for `fr-b40-contract` artifacts.

No Java controller changes required — routes were already registered.

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb40-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — probes verify path liveness only; behavior parity / prod soak still open.
- Spring unmapped 404 still correctly fails (verified: `/video/nonexistent-route-xyz`).
- FR-B39 HTTP 404 mapping intentionally preserved; probe now distinguishes envelope vs unmapped.

## Files touched (FR-B40 only)

- `tools/video_java/contract_regression.py`
- `logs/fr-b40-contract-latest.*`, `logs/certify-frb40-phase0.log`
- `docs/video-java/FULL_REPLACEMENT_GAP.md`, `docs/video-java/HANDOFF.md`, `.superpowers/sdd/progress.md`
- `fr-b40-report.md`
