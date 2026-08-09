# Phase 5 Gate Evidence

> Candidate: `F:/acme/.worktrees/runtime-parity` (`feat/runtime-parity`)  
> Updated: 2026-08-10  
> **Note:** This file is implementer evidence only. Do **not** treat as Orchestrator ACCEPTED until the orchestrator writes acceptance.

## G-5.1 — `certify --profile linux_full`

| Item | Evidence |
|------|----------|
| Exit code | **0** |
| `ok` | `true` |
| Cases | 7/7 |
| Layers | pass=13 / fail=0 |
| Report SHA256 | `6A0D0A6C5BDC6AB6823C7882454A4000CF6D823C4956ED0BCAAB936F754F5B97` |
| Archive | `logs/certify_linux_full.json` |
| Status doc | [`../CERTIFY_STATUS.md`](../CERTIFY_STATUS.md) |

Command:

```powershell
$env:ACME_ORACLE_ROOT='F:\acme'
$env:ACME_CANDIDATE_ROOT='F:\acme\.worktrees\runtime-parity'
. .\RUNTIME\scripts\deploy.env.ps1
python tools/runtime_parity_gate.py certify --profile linux_full
```

## G-5.2 — `certify --profile win_cpp`

| Item | Evidence |
|------|----------|
| Exit code | **0** |
| `ok` | `true` |
| Cases | 12/12 |
| Layers | pass=24 / fail=0 |
| Report SHA256 | `83AE91D6A1E48E3185CE54A69EE3DCE43D5EE2B5789A8FE74D9EA0DE67510D55` |
| Archive | `logs/certify_win_cpp.json` |
| Status doc | [`../CERTIFY_STATUS.md`](../CERTIFY_STATUS.md) |

Command: same env + `certify --profile win_cpp`.

## G-5.3 — Quarantine Python three services (**dry-run only**)

**Policy:** Prefer quarantine `move` → `VIDEO/services/_retired/` (whitelist-safe). **No `--execute`.** Orchestrator must review then execute.

### Constraint for execute

Dry-runs used **candidate-only** allow-root (unset `ACME_ORACLE_ROOT` for the command).  
Reason: with both `ACME_ORACLE_ROOT=F:\acme` and candidate under `.worktrees/`, whitelist rel-path becomes `.worktrees/runtime-parity/VIDEO/services/...` and is refused.  
Execute must recreate the same allow-roots as the dry-run JSON (`allow_roots` = candidate only).

### Dry-run artifacts (canonical + alias)

| Service | Timestamped manifest | Alias copy | Token | plan_hash | bytes_hint |
|---------|----------------------|------------|-------|-----------|------------|
| realtime | `logs/safe_fsops_dryrun_20260810_002757.json` | `logs/safe_fsops_dryrun_realtime.json` | `74e8da0198727f6d56673a0955cdbe9d` | `0930d4df65546378df3b6ec6a4a8175ec3059d2989521cead8adf117787c8207` | 235196 |
| snapshot | `logs/safe_fsops_dryrun_20260810_002759.json` | `logs/safe_fsops_dryrun_snapshot.json` | `317addc405fddb58aa54f95a857961fc` | `fe91bf566af127089c81a0ecf7cd6ca5ee3a982f2bd38873e355c9eb81e90bc4` | 130040 |
| patrol | `logs/safe_fsops_dryrun_20260810_002801.json` | `logs/safe_fsops_dryrun_patrol.json` | `0f4adb03d893d696c92d8914cc67799a` | `6001bc2741aa232141a8f9d520c89de67e56ac44515c1166587f74acc7dc45ee` | 26629 |

### Full action list (3 moves)

1. **realtime**
   - op: `move`
   - src: `F:\acme\.worktrees\runtime-parity\VIDEO\services\realtime_algorithm_service`
   - dst: `F:\acme\.worktrees\runtime-parity\VIDEO\services\_retired\realtime_algorithm_service`
2. **snapshot**
   - op: `move`
   - src: `F:\acme\.worktrees\runtime-parity\VIDEO\services\snapshot_algorithm_service`
   - dst: `F:\acme\.worktrees\runtime-parity\VIDEO\services\_retired\snapshot_algorithm_service`
3. **patrol**
   - op: `move`
   - src: `F:\acme\.worktrees\runtime-parity\VIDEO\services\patrol_algorithm_service`
   - dst: `F:\acme\.worktrees\runtime-parity\VIDEO\services\_retired\patrol_algorithm_service`

### Suggested execute (orchestrator only)

Global flags (`--execute`, `--confirm-token`, `--dryrun-manifest`) must precede the `move` subcommand.

```powershell
# IMPORTANT: do NOT set ACME_ORACLE_ROOT for these executes (match dry-run allow_roots)
$env:ACME_CANDIDATE_ROOT='F:\acme\.worktrees\runtime-parity'
Remove-Item Env:ACME_ORACLE_ROOT -ErrorAction SilentlyContinue

python tools/runtime_parity/safe_fsops.py --allow-root $env:ACME_CANDIDATE_ROOT `
  --execute --confirm-token 74e8da0198727f6d56673a0955cdbe9d `
  --dryrun-manifest logs/safe_fsops_dryrun_20260810_002757.json `
  move --src VIDEO/services/realtime_algorithm_service --dst VIDEO/services/_retired/realtime_algorithm_service

python tools/runtime_parity/safe_fsops.py --allow-root $env:ACME_CANDIDATE_ROOT `
  --execute --confirm-token 317addc405fddb58aa54f95a857961fc `
  --dryrun-manifest logs/safe_fsops_dryrun_20260810_002759.json `
  move --src VIDEO/services/snapshot_algorithm_service --dst VIDEO/services/_retired/snapshot_algorithm_service

python tools/runtime_parity/safe_fsops.py --allow-root $env:ACME_CANDIDATE_ROOT `
  --execute --confirm-token 0f4adb03d893d696c92d8914cc67799a `
  --dryrun-manifest logs/safe_fsops_dryrun_20260810_002801.json `
  move --src VIDEO/services/patrol_algorithm_service --dst VIDEO/services/_retired/patrol_algorithm_service
```

### Orchestrator execute (2026-08-10)

- Reviewed three dry-run manifests: candidate-only `allow_roots`, whitelist moves to `_retired/`, oracle untouched.
- **EXECUTED** all three moves via `safe_fsops.py` (tokens matched).
- Verified: live paths absent; `VIDEO/services/_retired/{realtime,snapshot,patrol}_algorithm_service` present.
- Post-execute re-verify: `certify --profile win_cpp` exit **0** (12/12); `certify --profile linux_full` exit **0** (7/7).
- Oracle `F:/acme/VIDEO/services/*_algorithm_service` **unchanged** (still present).

## G-5.4 — Default cpp only; drop python selection

### Code / product

| Surface | Change |
|---------|--------|
| `VIDEO/app/services/runtime_config_service.py` | `normalize_executor`: empty→`cpp`; `python`/`py` → `ValueError` (no silent coerce) |
| `VIDEO/app/services/algorithm_task_daemon.py` | Non-cpp deploy path removed; refuses with ERROR log |
| `VIDEO/app/services/algorithm_task_launcher_service.py` | Local + remote launch refuse non-cpp; remote python bundle path removed |
| `VIDEO/app/services/alert_post_orchestrator.py` | Default executor assumption → `cpp` (stale python rows still skip) |
| `VIDEO/models.py` | Already `default='cpp'` (unchanged) |
| `WEB/.../AlgorithmTaskModal.vue` | UI options only `*_cpp`; `fromTaskMode` always `executor=cpp` |
| `VIDEO/README.md` / `README.md` | Document cpp-only |

### CI

Searched `.github/workflows/` and common CI scripts:

- Only workflow present: `.github/workflows/compile-packaging.yml` (COMPILE packaging; `setup-python` is for packaging tooling, **not** a python algorithm executor job).
- **No** dedicated `executor=python` / `*_algorithm_service` CI job found to remove.
- **No** existing parity-gate workflow to retain; gate remains local CLI (`tools/runtime_parity_gate.py`). Documented for orchestrator if a future CI job is added.

### Suggested commit (G-5.4)

`feat: default cpp executor and drop python selection` — landed as `4ea3164`.

## Orchestrator acceptance (2026-08-10)

| Gate | Verdict |
|------|---------|
| G-5.1 | **ACCEPTED** — linux_full green + CERTIFY_STATUS |
| G-5.2 | **ACCEPTED** — win_cpp green + CERTIFY_STATUS |
| G-5.3 | **ACCEPTED** — dry-run reviewed; quarantine execute done |
| G-5.4 | **ACCEPTED** — cpp-only selection + docs |

## Phase 5 verdict

**PASS** — Runtime parity Phase 5 complete. Python algorithm hot-path services quarantined under `VIDEO/services/_retired/` on candidate; default executor is cpp-only.
