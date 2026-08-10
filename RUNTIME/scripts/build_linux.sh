#!/usr/bin/env bash
# Build RUNTIME against conda env `easyaiot-runtime` (or active env).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# Prefer shared env activator
if [[ -f "$ROOT/scripts/env.sh" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/scripts/env.sh"
fi

ORT_ROOT="${ORT_ROOT:-$REPO/.deps/onnxruntime-linux-x64-1.23.2}"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "ERROR: activate conda env easyaiot-runtime first (source RUNTIME/scripts/env.sh)"
  exit 1
fi

export PATH="$CONDA_PREFIX/bin:$PATH"
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${ORT_ROOT}/lib:${LD_LIBRARY_PATH:-}"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:${CMAKE_PREFIX_PATH:-}"
if [[ ! -d "$ORT_ROOT" ]]; then
  echo "ERROR: ONNX Runtime C++ SDK not found at $ORT_ROOT"
  echo "Download: https://github.com/microsoft/onnxruntime/releases"
  exit 1
fi

BUILD_DIR="$ROOT/build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# shellcheck disable=SC1091
source "$ROOT/scripts/version_meta.sh"
runtime_resolve_version_meta "$ROOT" "$REPO"

cmake "$ROOT" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
  -DOpenCV_DIR="$CONDA_PREFIX/lib/cmake/opencv5" \
  -DONNXRUNTIME_ROOT="$ORT_ROOT" \
  -DRUNTIME_VERSION_STR="${RUNTIME_VERSION}" \
  -DCMAKE_CXX_FLAGS="-I$CONDA_PREFIX/include/opencv5"

cmake --build . -j"$(nproc)"

runtime_write_version_file "$BUILD_DIR/VERSION" "local-build" "$BUILD_DIR/RUNTIME" "$ORT_ROOT" "host"
runtime_write_version_file "$ROOT/VERSION" "local-build" "$BUILD_DIR/RUNTIME" "$ORT_ROOT" "host"

echo ""
echo "OK: $BUILD_DIR/RUNTIME (version=${RUNTIME_VERSION})"
echo "Run with:"
echo "  export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$ORT_ROOT/lib:\$LD_LIBRARY_PATH"
echo "  $BUILD_DIR/RUNTIME $ROOT/config/config.example.ini"
echo "  $BUILD_DIR/RUNTIME --version"
