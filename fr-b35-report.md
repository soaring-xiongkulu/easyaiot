# FR-B35 Report — audio_talk POST + POST keys-matrix ≥60

**Status:** DONE (not COMPLETE)  
**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

## Summary

Expanded `--post-keys-matrix` from **42 → 63** curated POST samples (≥60 target), adding full `/video/camera/audio/talk` POST coverage (start/stop/send + validation/failure paths). Fixed Java `AudioTalkService` / `AudioTalkController` to return honest Python-aligned error bodies without leaking `hostname can't be null`.

## Python-first cites (audio_talk)

| Route | Python source | Asserted keys / mode |
|-------|---------------|-------------------|
| `POST /start` missing device | `audio_talk.py` L94-95 | envelope `{code,msg}` code=400 |
| `POST /start` invalid device | `audio_talk.py` L97-99 | envelope code=404 |
| `POST /start` backchannel fail | `audio_talk.py` L123-127 | `data.success` code=500 (no ONVIF / no camera IP) |
| `POST /stop` missing session | `audio_talk.py` L154-155 | envelope code=400 |
| `POST /stop` ok | `audio_talk.py` L157-158 | `success`, `session_id` |
| `POST /send` missing fields | `audio_talk.py` L169-170 | envelope code=400 |
| `POST /send` fail | `audio_talk.py` L174-175 | `data.success` code=500 |

## Matrix counts

| Metric | Value |
|--------|------:|
| POST samples | **63** |
| Pass | **63/63** |
| Asserts | **242** (pass 242 / fail 0) |
| success_key samples | 32 |
| envelope_only / envelope_success | 31 |
| Prefix coverage | **14/14** (audio_talk POST added) |

Artifact: `logs/fr-b35-post-keys-matrix-latest.json` / `.md`

## Java fixes

1. **`AudioTalkService.startSession`** — reject cameras with blank `ip` before ONVIF client; return `code=500`, `msg=Audio Back Channel 建立失败，设备可能不支持`, `data.success=false` (Python L124-127).
2. **`AudioTalkService` / `AudioTalkController`** — business errors (start/send fail) use HTTP **200** + body `code` (VideoApiResponse convention); stops `HTTP 500` leaking on send.

## phase0

`python tools/video_java/certify.py --phase 0` → **5/5 PASS**  
Log: `logs/certify-frb35-phase0.log`

## Remaining / concerns

- **NOT COMPLETE** — post-keys 63 ≠ ~112 inventoried POST routes; ONVIF backchannel success path not green on file-based `vj_p2_device` (expected honest 500).
- Face entry multipart POST not in matrix (Python requires upload bytes); used `POST /video/face/model/download` instead.
- Algorithm task start/restart sampled as honest **400** when RUNTIME binary absent (local mini).
- prod soak checklist still mostly open.

## Files touched

- `tools/video_java/post_keys_matrix_b35_specs.py` (new)
- `tools/video_java/field_contract.py` (b35 import + artifact prefix)
- `DEVICE/iot-video/.../AudioTalkService.java`
- `DEVICE/iot-video/.../AudioTalkController.java`
- `docs/video-java/HANDOFF.md`, `docs/video-java/FULL_REPLACEMENT_GAP.md`, `.superpowers/sdd/progress.md`
- `logs/fr-b35-post-keys-matrix-latest.*`, `logs/certify-frb35-phase0.log`
