#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${EASYAIOT_NVIDIA_BUILD_DIR:-${ROOT}/build}"
BUILD_TYPE="${CMAKE_BUILD_TYPE:-Release}"
JOBS="${EASYAIOT_BUILD_JOBS:-$(nproc)}"
VERSION="${RUNTIME_NVIDIA_VERSION:-$(git -C "$ROOT" describe --always --dirty 2>/dev/null || echo dev)}"

bash "$ROOT/scripts/nvidia_preflight.sh" --build

cuda_arch="${EASYAIOT_NVIDIA_CUDA_ARCH:-}"
if [[ -z "$cuda_arch" ]] && command -v nvidia-smi >/dev/null 2>&1; then
  cuda_arch="$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -n1 | tr -d '.[:space:]')"
fi
if [[ -z "$cuda_arch" && -r /proc/device-tree/compatible ]]; then
  if tr '\0' ' ' < /proc/device-tree/compatible | grep -qi 'tegra234'; then cuda_arch=87; fi
  if tr '\0' ' ' < /proc/device-tree/compatible | grep -qi 'tegra194'; then cuda_arch=72; fi
fi

cmake_args=(
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE"
  -DTENSORRT_ROOT="${TENSORRT_ROOT:-}"
  -DRUNTIME_VERSION_STR="$VERSION"
  -DBUILD_TESTING=ON
)
if [[ -n "$cuda_arch" ]]; then cmake_args+=("-DCMAKE_CUDA_ARCHITECTURES=$cuda_arch"); fi
cmake -S "$ROOT" -B "$BUILD_DIR" "${cmake_args[@]}"
cmake --build "$BUILD_DIR" --parallel "$JOBS"
ctest --test-dir "$BUILD_DIR" --output-on-failure

{
  echo "version=$VERSION"
  echo "arch=$(uname -m)"
  echo "build_mode=$BUILD_TYPE"
  echo "cuda_arch=${cuda_arch:-cmake-default}"
  echo "source=RUNTIME-NVIDIA"
  echo "built_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "sdk=cuda-tensorrt-nvcodec"
} > "$BUILD_DIR/VERSION"

{
  echo "EASYAIOT_RUNTIME_TARGET=nvidia"
  echo "RUNTIME_NVIDIA_BIN=$BUILD_DIR/RUNTIME"
  echo "RUNTIME_NVIDIA_CONFIG_DIR=$ROOT/config"
  echo "RUNTIME_NVIDIA_CLASSES_PATH=$ROOT/models/coco.names"
  echo "LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib/$(uname -m)-linux-gnu"
} > "$ROOT/deploy.env"
echo "[NVIDIA] 构建完成: $BUILD_DIR/RUNTIME"
