#!/usr/bin/env bash
# Build RUNTIME against conda env `easyaiot-runtime` (or active env).
# Invoked directly or via ../build.sh (one-click compile).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
_ARCH="$(uname -m)"
case "$_ARCH" in
  x86_64|amd64) _ARCH_TAG=x64 ;;
  aarch64|arm64) _ARCH_TAG=aarch64 ;;
  *) _ARCH_TAG=x64 ;;
esac
_ORT_VER="${ORT_VERSION:-1.23.2}"

# Auto-detect conda + ORT for any user (see env.sh)
if [[ -f "$ROOT/scripts/env.sh" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/scripts/env.sh"
fi

ORT_ROOT="${ORT_ROOT:-$REPO/.deps/onnxruntime-linux-${_ARCH_TAG}-${_ORT_VER}}"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "ERROR: 未找到 conda 环境 ${EASYAIOT_RUNTIME_CONDA_ENV:-easyaiot-runtime}" >&2
  echo "请先创建环境，例如:" >&2
  echo "  ./RUNTIME/install_linux.sh install   # 或 EASYAIOT_RUNTIME_BUILD_MODE=host" >&2
  echo "或手动: conda create -n easyaiot-runtime && conda activate easyaiot-runtime" >&2
  exit 1
fi

if [[ ! -d "$ORT_ROOT/include" || ! -d "$ORT_ROOT/lib" ]]; then
  echo "[RUNTIME] ONNX Runtime SDK 缺失，尝试下载: $ORT_ROOT"
  if [[ -x "$ROOT/scripts/ensure_ort_deps.sh" ]]; then
    bash "$ROOT/scripts/ensure_ort_deps.sh" "$_ARCH" || {
      echo "ERROR: 下载 ORT 失败，请检查网络或设置 ORT_ROOT" >&2
      exit 1
    }
  else
    echo "ERROR: ONNX Runtime C++ SDK not found at $ORT_ROOT" >&2
    exit 1
  fi
fi

export PATH="$CONDA_PREFIX/bin:$PATH"
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${ORT_ROOT}/lib:${LD_LIBRARY_PATH:-}"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX:${CMAKE_PREFIX_PATH:-}"

BUILD_DIR="$ROOT/build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# shellcheck disable=SC1091
source "$ROOT/scripts/version_meta.sh"
runtime_resolve_version_meta "$ROOT" "$REPO"

echo "[RUNTIME] CONDA_PREFIX=$CONDA_PREFIX"
echo "[RUNTIME] ORT_ROOT=$ORT_ROOT"
echo "[RUNTIME] cmake 配置 (Release)..."

cmake "$ROOT" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
  -DOpenCV_DIR="$CONDA_PREFIX/lib/cmake/opencv5" \
  -DONNXRUNTIME_ROOT="$ORT_ROOT" \
  -DRUNTIME_VERSION_STR="${RUNTIME_VERSION}" \
  -DCMAKE_CXX_FLAGS="-I$CONDA_PREFIX/include/opencv5"

echo "[RUNTIME] 编译中 (-j$(nproc 2>/dev/null || echo 4))..."
cmake --build . -j"$(nproc 2>/dev/null || echo 4)"

runtime_write_version_file "$BUILD_DIR/VERSION" "local-build" "$BUILD_DIR/RUNTIME" "$ORT_ROOT" "host"
runtime_write_version_file "$ROOT/VERSION" "local-build" "$BUILD_DIR/RUNTIME" "$ORT_ROOT" "host"

echo ""
echo "OK: $BUILD_DIR/RUNTIME (version=${RUNTIME_VERSION})"
echo "Run with:"
echo "  export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$ORT_ROOT/lib:\$LD_LIBRARY_PATH"
echo "  $BUILD_DIR/RUNTIME $ROOT/config/config.example.ini"
echo "  $BUILD_DIR/RUNTIME --version"
