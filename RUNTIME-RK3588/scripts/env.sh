#!/usr/bin/env bash
set -euo pipefail

RUNTIME_RK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export RUNTIME_BIN="${RUNTIME_BIN:-$RUNTIME_RK_ROOT/build/RUNTIME}"
export RUNTIME_BENCH_BIN="${RUNTIME_BENCH_BIN:-$RUNTIME_RK_ROOT/build/RUNTIME-RK3588-BENCH}"
export LD_LIBRARY_PATH="${ROCKCHIP_SDK_ROOT:-/usr}/lib:${ROCKCHIP_SDK_ROOT:-/usr}/lib64:${LD_LIBRARY_PATH:-}"
