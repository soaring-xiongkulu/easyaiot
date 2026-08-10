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

### P3-S2 drill detail (historical — pre-CLOSE-S2)

> **Superseded:** drill used `video-server-java` ↔ `video-server` YAML flip. After CLOSE-S2, Java production name is `video-server`; rollback is process swap, not URI revert.

**Environment:** `F:/acme/.worktrees/video-java`, branch `feat/video-java`. No live `iot-gateway` on `:48080` at drill time — config edit only.

**Measured:** YAML edit elapsed **40 ms** (2026-08-10).

Template row:

```text
YYYY-MM-DD | symptom (e.g. hook 5xx spike) | stop Java, restore Python archive, start :6000 as video-server | N min | restored | name
```
