#!/usr/bin/env bash
# 停止 run_value_demo.sh 拉起的 mock / runtime
set -euo pipefail
E2E="$(cd "$(dirname "$0")" && pwd)"
for name in mock_receiver transform-runtime; do
  pidfile="$E2E/${name}.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" || true
      echo "stopped $name pid=$pid"
    fi
    rm -f "$pidfile"
  fi
done
