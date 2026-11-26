#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${EASYAIOT_BM1688_BUILD_DIR:-${ROOT}/build}"
BUILD_TYPE="${CMAKE_BUILD_TYPE:-Release}"
JOBS="${EASYAIOT_BUILD_JOBS:-$(nproc)}"
VERSION="${RUNTIME_BM1688_VERSION:-$(git -C "$ROOT" describe --always --dirty 2>/dev/null || echo dev)}"

bash "$ROOT/scripts/bm1688_preflight.sh" --build
cmake -S "$ROOT" -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DSOPHON_SDK_ROOT="${SOPHON_SDK_ROOT:-}" \
  -DRUNTIME_VERSION_STR="$VERSION" \
  -DBUILD_TESTING=ON
cmake --build "$BUILD_DIR" --parallel "$JOBS"
ctest --test-dir "$BUILD_DIR" --output-on-failure

cat > "$BUILD_DIR/VERSION" <<EOF
version=$VERSION
arch=$(uname -m)
build_mode=$BUILD_TYPE
source=RUNTIME-BM1688
built_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
sdk=sophon-bm1688
EOF

cat > "$ROOT/deploy.env" <<EOF
EASYAIOT_RUNTIME_TARGET=bm1688
RUNTIME_BM1688_BIN=$BUILD_DIR/RUNTIME
RUNTIME_BM1688_CONFIG_DIR=$ROOT/config
RUNTIME_BM1688_CLASSES_PATH=$ROOT/models/coco.names
LD_LIBRARY_PATH=/opt/sophon/libsophon-current/lib:/opt/sophon/sophon-opencv-latest/lib:/usr/lib/aarch64-linux-gnu
EOF
echo "[BM1688] 构建完成: $BUILD_DIR/RUNTIME"
