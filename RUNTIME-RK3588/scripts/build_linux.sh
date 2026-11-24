#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "$ROOT/scripts/rk3588_preflight.sh" --build

BUILD_DIR="${EASYAIOT_RK3588_BUILD_DIR:-$ROOT/build}"
ROCKCHIP_SDK_ROOT="${ROCKCHIP_SDK_ROOT:-/usr}"
cmake -S "$ROOT" -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE:-Release}" \
  -DROCKCHIP_SDK_ROOT="$ROCKCHIP_SDK_ROOT" \
  -DRUNTIME_VERSION_STR="${RUNTIME_VERSION:-rk3588-dev}"
cmake --build "$BUILD_DIR" --parallel "${BUILD_JOBS:-$(nproc)}"
echo "OK: $BUILD_DIR/RUNTIME"
echo "OK: $BUILD_DIR/RUNTIME-RK3588-BENCH"
