#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${1:-$ROOT/build/RUNTIME}"
BENCH="$(dirname "$BIN")/RUNTIME-RK3588-BENCH"
bash "$ROOT/scripts/rk3588_preflight.sh"
[[ -x "$BIN" ]] || { echo "SMOKE_FAIL: binary missing: $BIN" >&2; exit 1; }
[[ -x "$BENCH" ]] || { echo "SMOKE_FAIL: benchmark missing: $BENCH" >&2; exit 1; }
if ldd "$BIN" | awk '/not found/{bad=1} END{exit !bad}'; then
  echo "SMOKE_FAIL: missing shared libraries" >&2
  ldd "$BIN" | awk '/not found/' >&2
  exit 1
fi
"$BIN" --version
echo "SMOKE_OK: RK3588 strict runtime and benchmark are executable"
