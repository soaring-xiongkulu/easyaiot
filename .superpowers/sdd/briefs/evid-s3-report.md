# EVID-S3 Report — Real RUNTIME.exe for P0 start/stop (no stub launcher)

## STATUS
**DONE** — P0 fixture + DB `runtime_bin_path` point at built `RUNTIME.exe`; `vj_p0_task_start_stop` lifecycle goldens show `executor_bin=RUNTIME.exe` (not `stub_runtime.bat`); certify `--phase 0` exit **0**, `--phase 1` exit **0**.

## Commit
`fix(video-java): EVID-S3 real RUNTIME.exe P0 launcher + lifecycle gate`

## Build
| Item | Value |
|------|-------|
| **RUNTIME.exe** | `F:\acme\.worktrees\video-java\RUNTIME\build-win\Release\RUNTIME.exe` (650240 bytes, VS2019 x64 Release) |
| ORT | `fetch_deps_windows.ps1 -Execute` → `RUNTIME/vendor/win-x64/onnxruntime` |
| Deps | `conda create -p RUNTIME/vendor/conda-env -c conda-forge libopencv=4.6 ffmpeg=5.1 jsoncpp glog libcurl` |
| CMake fix | `GLOG_USE_GLOG_EXPORT` for glog 0.7 (conda-forge) |

## Wiring
1. **`seed_p0_fixture.py`** — `runtime_bin_path()` requires real `RUNTIME.exe`; updates fixture + DB (no stub).
2. **`fixtures/vj_p0.json`** — `runtime_bin_path` → `...\RUNTIME\build-win\Release\RUNTIME.exe`; `crash_runtime_bin_path` still `stub_runtime_exit.bat` for restart-only crash.
3. **`thresholds.json` + `diff_layers.py`** — `vj_p0_task_start_stop`: absolute `process_alive=true`, `executor_bin` must contain `RUNTIME.exe`, reject `stub_runtime*`; `vj_p0_restart`: `process_alive_after_restart_required` only.
4. **`record_python.py` / `run_java.py`** — lifecycle captures `executor_bin` + optional `process_image`; wait-until-running + 90s start timeout for real RUNTIME load.
5. **`doctor.py`** — fails structural check if `RUNTIME.exe` missing.

## Proof stub not used (P0 launcher)
- Fixture: `runtime_bin_path` = `...\RUNTIME.exe` (not `.bat`).
- Golden lifecycle (py/java `vj_p0_task_start_stop`): `"executor_bin": "RUNTIME.exe"`.
- API golden `runtime_bin_path` ends with `RUNTIME\build-win\Release\RUNTIME.exe`.
- Certify fails if `executor_bin` contains `stub_runtime` (`reject_stub_launcher`).

## Verify
```text
python tools/video_java/seed_p0_fixture.py
python tools/video_java/doctor.py
python tools/video_java/certify.py --phase 0 --no-record
python tools/video_java/certify.py --phase 1 --no-record
```

| gate | exit |
|------|------|
| Phase 0 | **0** |
| Phase 1 | **0** |

## Concerns
- `RUNTIME.exe` + `vendor/conda-env/` are local build artifacts (gitignored); doctor enforces exe presence before certify.
- Real RUNTIME start can take ~60s (model load); record/certify use 90s HTTP timeout + wait-until-running.
- `process_image` often null (PID probe timing); gate relies on `executor_bin` + configured path.
- `vj_p0_restart` remains flaky on java re-record (crash stub loop); re-run `run_java.py vj_p0_restart` if lifecycle false negative.
- Oracle full certify re-record still slow; `--no-record` recommended when goldens fresh.
