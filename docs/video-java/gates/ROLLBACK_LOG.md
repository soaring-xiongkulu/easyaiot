# VIDEO Java — rollback log

Record each production or staged rollback after gateway cutover to Java (`video-server`).

## Naming reference (post CLOSE-S2)

| Role | Nacos name | Port | Notes |
|------|------------|------|-------|
| **Production (Java)** | `video-server` | `48096` | Gateway `video-admin-api` → `lb://video-server` |
| **Rollback (Python)** | `video-server` | `6000` | Archived at `VIDEO/_retired_python_video/` or external `F:/acme/VIDEO` |

Gateway URI **does not change** on rollback — stop Java, restore/start Python as `video-server`, Nacos resolves to Python.

## Log

| Date | Trigger | Steps | Duration | Outcome | Author |
|------|---------|-------|----------|---------|--------|
| 2026-08-10 | P3-S2 staged rollback drill (pre-CLOSE-S2 naming) | Config flip `video-server-java` ↔ `video-server` | **<1 min** (40 ms YAML edit) | Historical — superseded by CLOSE-S2 | P3-S2 agent |
| 2026-08-10 | EVID-S5 narrative fix (doc-only; no live drill) | Documented post-rename rollback: stop Java → restore Python archive → start `:6000` as `video-server` | — | docs updated | EVID-S5 |
| 2026-08-11 | FR-B7 full restore drill (in-repo archive) | safe_fsops dry-run→execute: restore `app/`+`services/`+`run.py`+`models.py` from `_retired_python_video/` → `VIDEO/`; verify tree; re-archive same paths | **restore 1.7s + re-archive 1.5s = 3.2s** | restored + re-archived | FR-B7 |
| 2026-08-11 | FR-B11 Nacos process-swap dry-run (no live flip) | Config verify `lb://video-server`; Java `:48096` UP; document stop-Java→restore-Python→start-`:6000` as `video-server` per CUTOVER.md; gateway URI unchanged; smoke skipped (no `:48080` gateway) | **8.2s** checklist | dry-run evidence only | FR-B11 |
| 2026-08-10 | EVID-S6 staged restore drill (in-repo archive) | safe_fsops dry-run→execute: restore `run.py`+`models.py`+`start_prod.sh` from `_retired_python_video/` → `VIDEO/`; `Test-Path VIDEO/run.py`=True; re-archive same paths | **restore 4.3s + re-archive 3.1s = 7.5s** | restored + re-archived | EVID-S6 |

### EVID-S5 rollback runbook (current)

**Environment:** `F:/acme/.worktrees/video-java`, branch `feat/video-java`. Production gateway `uri: lb://video-server` (Java).

**When Java fails — fast rollback:**

1. **Stop Java** — scale `video-server` (Java) to 0; confirm Nacos deregister.
2. **Restore Python serving surface** (pick one):
   - **In-repo:** move/copy from `VIDEO/_retired_python_video/` → `VIDEO/` (`app/`, `run.py`, `models.py`, `services/`, `start_prod.sh`, `docker-entrypoint.sh`).
   - **External:** checkout/run `F:/acme/VIDEO` (tag `video-java-oracle-baseline`).
3. **Start Python** on `:6000`, register Nacos as `video-server`.
4. **Gateway** — **no URI change** (`lb://video-server`); reload only if stale route cache.
5. **Background** — clear `VIDEO_SKIP_BACKGROUND_TASKS`; `auto_start_all_tasks` if needed.
6. **Smoke** — gateway `/admin-api/video/**` with token + `tenant-id`.

**Restore to Java (after incident):**

1. Stop Python; re-archive serving surface per P3-S3 `safe_fsops` if restoring in-repo layout.
2. Start Java `video-server` on `:48096`.
3. Gateway unchanged (`lb://video-server`).

**Prod rollback budget:** stop Java + restore Python + Nacos register + smoke typically **5–15 min** (archive restore adds time).

### EVID-S6 restore drill detail (2026-08-10)

**Environment:** `F:/acme/.worktrees/video-java`, branch `feat/video-java`. Java still running on `:48096` (no Nacos flip — file restore only).

**Steps (safe_fsops, `--allow-delete-prefix VIDEO/_retired_python_video` for restore direction):**

1. **Restore dry-run → execute** — move `run.py`, `models.py`, `start_prod.sh` from `VIDEO/_retired_python_video/` → `VIDEO/`.
2. **Verify** — `Test-Path VIDEO/run.py` → **True** (also `models.py`, `start_prod.sh`).
3. **Re-archive dry-run → execute** — move same three files back to `VIDEO/_retired_python_video/`.
4. **Post-check** — `VIDEO/run.py` absent; `_retired_python_video/run.py` present.

**Measured:** restore **4311 ms**, re-archive **3112 ms**, total **7530 ms**.

### FR-B7 full restore drill detail (2026-08-11)

**Environment:** `F:/acme/.worktrees/video-java`, branch `feat/video-java`. Java still running on `:48096` (no Nacos flip — file restore only).

**Steps (safe_fsops, `--allow-delete-prefix VIDEO/_retired_python_video` for restore direction):**

1. **Restore dry-run → execute** — move `app/`, `services/`, `run.py`, `models.py` from `VIDEO/_retired_python_video/` → `VIDEO/`.
2. **Verify** — `Test-Path VIDEO/run.py`, `models.py`, `app`, `services` → **True**.
3. **Re-archive dry-run → execute** — move same four paths back to `VIDEO/_retired_python_video/`.
4. **Post-check** — `VIDEO/run.py` absent; `_retired_python_video/run.py` present.

**Measured:** restore **1663 ms**, re-archive **1502 ms**, total **3165 ms**.

### FR-B11 Nacos process-swap dry-run detail (2026-08-11)

**Environment:** `F:/acme/.worktrees/video-java`, branch `feat/video-java`. Java candidate listening on `:48096` (**UP**). No live Nacos deregister or Python start — **dry-run only**.

**Pre-checks:**

1. Gateway `video-admin-api` → **`lb://video-server`** — **verified** in `DEVICE/iot-gateway/src/main/resources/application.yaml`.
2. Java `video-server` health — `127.0.0.1:48096` TCP **UP**.
3. Python rollback source — `VIDEO/_retired_python_video/` present (file restore path proven by FR-B7).

**Documented swap path (CUTOVER.md rollback — NOT executed):**

| Step | Action | FR-B11 status |
|------|--------|---------------|
| 1 | Stop Java `video-server` (scale 0; Nacos deregister) | NOT RUN |
| 2 | Restore Python serving surface from `_retired_python_video/` | NOT RUN (FR-B7 file restore **3165 ms**) |
| 3 | Start Python `:6000`, register Nacos as `video-server` | NOT RUN |
| 4 | Gateway — keep `lb://video-server` | CONFIG OK |
| 5 | Smoke `/admin-api/video/**` with token + `tenant-id` | NOT RUN (no gateway `:48080` in dev) |

**Restore-to-Java (post-incident):** stop Python → re-archive if needed → start Java `:48096` → gateway unchanged.

**Measured:** dry-run checklist **8212 ms**. Evidence file: `logs/fr-b11-nacos-dryrun.txt`.

### P3-S2 drill detail (historical — pre-CLOSE-S2)

> **Superseded:** drill used `video-server-java` ↔ `video-server` YAML flip. After CLOSE-S2, Java production name is `video-server`; rollback is process swap, not URI revert.

**Environment:** `F:/acme/.worktrees/video-java`, branch `feat/video-java`. No live `iot-gateway` on `:48080` at drill time — config edit only.

**Measured:** YAML edit elapsed **40 ms** (2026-08-10).

Template row:

```text
YYYY-MM-DD | symptom (e.g. hook 5xx spike) | stop Java, restore Python archive, start :6000 as video-server | N min | restored | name
```
