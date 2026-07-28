#!/usr/bin/env bash
# TRANSFORM e2e 便捷入口
set -euo pipefail
cd "$(dirname "$0")"
exec python3 run_all.py "$@"
