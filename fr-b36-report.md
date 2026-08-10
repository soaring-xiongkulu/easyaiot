# FR-B36 Report — POST keys-matrix ≥100 inventoried POST routes

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Summary

Expanded `--post-keys-matrix` from **63 → 131** curated POST samples and added an **inventoried POST coverage table** (112 routes = **109 sampled + 3 destructive skip**). Fixed Java validation bugs for multipart-missing and batch-delete empty body.

## POST route coverage table

| Metric | Count |
|--------|------:|
| Inventoried POST | **112** |
| Sampled (unique routes) | **109** |
| Skipped (documented) | **3** |
| Uncovered | **0** |

**Skipped with reason:**

| Route | Reason |
|-------|--------|
| `/video/snap/device/{param}/storage/cleanup` | destructive storage purge |
| `/video/snap/space/{param}/images/cleanup` | destructive image purge |
| `/video/record/space/{param}/videos/cleanup` | destructive video purge |

Artifact coverage section: `logs/fr-b36-post-keys-matrix-latest.md` (full 112-row table).

## Matrix counts

| Metric | Value |
|--------|------:|
| POST samples | **131** |
| Pass | **131/131** |
| Asserts | **457** (pass 457 / fail 0) |
| success_key samples | 40 |
| envelope_only / envelope_success | 91 |
| Key asserts | pass **40** / fail **0** |

## Java fixes

1. **`FaceController.addEntry`** — validate `person_name` + multipart `file` before service; `400` not `500` (Python `face.py` L265-283).
2. **`FaceController.addLegacyLibrary` / `recognizeImage`** — optional params + `400` when label/image missing (Python `face.py` L589-591).
3. **`FaceController.batchDeletePersons`** — empty `person_ids` → `400` (Python L237-238).
4. **`PlateController.recognizeImage`** — missing file → `400`.
5. **`ScenarioPoseLibraryService.reExtractEntry`** — not found → `400` not `500` (Python `ValueError` → 400).

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb36-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — curated samples ≠ per-field POST parity; multipart **success** paths (face/plate entry upload) not green on JSON-only probes.
- **mini honest 500** — device snapshot / recognize / GB28181 sync / metadata sync when fixture bucket `certify-vj_p2_*` violates S3 naming or capture stub absent.
- prod soak checklist still mostly open.

## Files touched

- `tools/video_java/post_keys_matrix_b36_specs.py` (new)
- `tools/video_java/field_contract.py` (b36 import, coverage table, prerequisite `{id}` path materialize)
- `DEVICE/iot-video/.../FaceController.java`, `PlateController.java`, `ScenarioPoseLibraryService.java`
- `docs/video-java/HANDOFF.md`, `docs/video-java/FULL_REPLACEMENT_GAP.md`, `.superpowers/sdd/progress.md`
- `logs/fr-b36-post-keys-matrix-latest.*`, `logs/certify-frb36-phase0.log`
