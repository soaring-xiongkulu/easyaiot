# Retired Python VIDEO serving surface (P3-S3)

Archived 2026-08-10 via `tools/runtime_parity/safe_fsops.py` dry-run → execute.

## Contents

| Path | Role |
|------|------|
| `app/` | Flask blueprints + services (serving hot path) |
| `run.py` | `video-server` entry (`:6000`) |
| `models.py` | SQLAlchemy models used by Flask app |
| `services/` | Background worker processes |
| `start_prod.sh`, `docker-entrypoint.sh` | Production entry scripts |

## Not archived (remain under `VIDEO/`)

Models (`*.onnx`, `*.pt`), docker-compose, requirements, install scripts, test media, docs, data.

## Future oracle / parity

| Need | Path |
|------|------|
| External oracle (tag baseline) | `F:/acme/VIDEO` on `main`, tag `video-java-oracle-baseline` |
| In-repo archived copy | this directory — run `python run.py` from here if needed |
| Certify without live oracle | `python tools/video_java/certify.py --phase N --no-record` (uses existing golden) |
| Java-only smoke | gateway `lb://video-server-java` + direct `:48096` certify |

Gateway default traffic is **Java** (`video-server-java`). Do not re-register Python `video-server` without rollback runbook.
