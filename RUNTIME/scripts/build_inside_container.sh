#!/usr/bin/env bash
# ============================================
# 在 VIDEO 同源容器内编译 RUNTIME（系统 g++ / 同源 glibc）
# 由 RUNTIME/install_linux.sh 以 docker run 方式调用，勿直接当宿主机入口。
#
# 约定环境变量:
#   RUNTIME_SRC   - RUNTIME 源码目录（容器内路径）
#   CONDA_PREFIX  - 已挂载的依赖前缀（OpenCV5/glog/ffmpeg 等）
#   ORT_ROOT      - ONNX Runtime C++ SDK 根目录
# ============================================
set -euo pipefail

RUNTIME_SRC="${RUNTIME_SRC:-/src/RUNTIME}"
CONDA_PREFIX="${CONDA_PREFIX:?CONDA_PREFIX required}"
ORT_ROOT="${ORT_ROOT:?ORT_ROOT required}"

echo "[RUNTIME/container] src=$RUNTIME_SRC"
echo "[RUNTIME/container] conda=$CONDA_PREFIX"
echo "[RUNTIME/container] ort=$ORT_ROOT"

# 强制使用容器系统编译器，避免 conda cxx-compiler/sysroot 把 glibc 要求抬高
if [[ -x /usr/bin/g++ ]]; then
  export CC=/usr/bin/gcc
  export CXX=/usr/bin/g++
elif command -v g++ >/dev/null 2>&1; then
  export CC="$(command -v gcc)"
  export CXX="$(command -v g++)"
else
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y --no-install-recommends g++ gcc make pkg-config ca-certificates
    export CC=/usr/bin/gcc
    export CXX=/usr/bin/g++
  else
    echo "[RUNTIME/container] ERROR: 未找到 g++，且无法 apt 安装" >&2
    exit 1
  fi
fi

if [[ ! -d "$CONDA_PREFIX/include" || ! -d "$CONDA_PREFIX/lib" ]]; then
  echo "[RUNTIME/container] ERROR: CONDA_PREFIX 无效: $CONDA_PREFIX" >&2
  exit 1
fi
if [[ ! -d "$ORT_ROOT/include" || ! -d "$ORT_ROOT/lib" ]]; then
  echo "[RUNTIME/container] ERROR: ORT_ROOT 无效: $ORT_ROOT" >&2
  exit 1
fi

# 优先容器自带 cmake（与 VIDEO 同源）；勿优先跑宿主机 conda 的 cmake（可能要求更高 glibc）
CMAKE_BIN=""
for c in /opt/conda/bin/cmake /usr/bin/cmake "$CONDA_PREFIX/bin/cmake"; do
  if [[ -x "$c" ]]; then
    CMAKE_BIN="$c"
    break
  fi
done
if [[ -z "$CMAKE_BIN" ]]; then
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y --no-install-recommends cmake pkg-config
    CMAKE_BIN=/usr/bin/cmake
  else
    echo "[RUNTIME/container] ERROR: 未找到 cmake" >&2
    exit 1
  fi
fi

# /usr/bin 必须优先：系统 g++ 通过 PATH 找 ld；conda 在前会误用 conda sysroot 的 ld
export PATH="/usr/bin:/bin"
export PKG_CONFIG_PATH="$CONDA_PREFIX/lib/pkgconfig"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:$ORT_ROOT/lib"
export CMAKE_PREFIX_PATH="$CONDA_PREFIX"
unset CFLAGS CXXFLAGS LDFLAGS LIBRARY_PATH CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH || true

BUILD_DIR="$RUNTIME_SRC/build"
# 清掉可能缓存了错误 linker 的旧配置
rm -rf "$BUILD_DIR/CMakeCache.txt" "$BUILD_DIR/CMakeFiles" 2>/dev/null || true
mkdir -p "$BUILD_DIR"

JOBS="$(nproc 2>/dev/null || echo 4)"
SYSTEM_LD=/usr/bin/ld

echo "[RUNTIME/container] CC=$CC CXX=$CXX"
"$CXX" --version | head -1
echo "[RUNTIME/container] cmake=$CMAKE_BIN ld=$SYSTEM_LD"
RUNTIME_VERSION_STR="${RUNTIME_VERSION_STR:-unknown}"
echo "[RUNTIME/container] version=$RUNTIME_VERSION_STR"
echo "[RUNTIME/container] cmake 配置..."
"$CMAKE_BIN" "$RUNTIME_SRC" \
  -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$CC" \
  -DCMAKE_CXX_COMPILER="$CXX" \
  -DCMAKE_LINKER="$SYSTEM_LD" \
  -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
  -DOpenCV_DIR="$CONDA_PREFIX/lib/cmake/opencv5" \
  -DONNXRUNTIME_ROOT="$ORT_ROOT" \
  -DRUNTIME_VERSION_STR="${RUNTIME_VERSION_STR}" \
  -DCMAKE_CXX_FLAGS="-I$CONDA_PREFIX/include/opencv5"

echo "[RUNTIME/container] 编译中 (-j$JOBS)..."
"$CMAKE_BIN" --build "$BUILD_DIR" -j"$JOBS"

if [[ ! -x "$BUILD_DIR/RUNTIME" ]]; then
  echo "[RUNTIME/container] ERROR: 未生成 $BUILD_DIR/RUNTIME" >&2
  exit 1
fi

echo "[RUNTIME/container] OK: $BUILD_DIR/RUNTIME (version=${RUNTIME_VERSION_STR})"
