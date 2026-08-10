#!/usr/bin/env bash
# ============================================
# RUNTIME (C++ 高性能执行器) 一键安装 / 编译
# ============================================
# 用法:
#   ./install_linux.sh              # 安装依赖并编译
#   ./install_linux.sh build        # 仅编译（依赖已就绪）
#   ./install_linux.sh status       # 检查二进制与依赖
#
# 环境变量:
#   EASYAIOT_RUNTIME_SKIP=1         # 跳过（供上层脚本探测）
#   EASYAIOT_RUNTIME_REQUIRED=1     # 失败时以非 0 退出（默认失败仅告警式由调用方决定）
#   ORT_ROOT                        # ONNX Runtime C++ SDK 根目录
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
REPO="$(cd "$ROOT/.." && pwd)"
ORT_VERSION="${ORT_VERSION:-1.23.2}"
CONDA_ENV_NAME="${EASYAIOT_RUNTIME_CONDA_ENV:-easyaiot-runtime}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[RUNTIME]${NC} $1"; }
print_success() { echo -e "${GREEN}[RUNTIME]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[RUNTIME]${NC} $1"; }
print_error() { echo -e "${RED}[RUNTIME]${NC} $1"; }

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) echo "x64" ;;
    aarch64|arm64) echo "aarch64" ;;
    *) echo "unknown" ;;
  esac
}

find_conda_sh() {
  local candidates=(
    "${CONDA_EXE%/*}/../etc/profile.d/conda.sh"
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    /opt/conda/etc/profile.d/conda.sh
    /usr/local/miniconda3/etc/profile.d/conda.sh
    /home/ubuntu/miniconda3/etc/profile.d/conda.sh
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -f "$c" ]]; then
      echo "$c"
      return 0
    fi
  done
  if command -v conda >/dev/null 2>&1; then
    local base
    base="$(conda info --base 2>/dev/null || true)"
    if [[ -n "$base" && -f "$base/etc/profile.d/conda.sh" ]]; then
      echo "$base/etc/profile.d/conda.sh"
      return 0
    fi
  fi
  return 1
}

activate_runtime_env() {
  local conda_sh
  if ! conda_sh="$(find_conda_sh)"; then
    print_error "未找到 conda，请先安装 Miniconda/Anaconda"
    return 1
  fi
  # shellcheck disable=SC1090
  source "$conda_sh"
  if ! conda env list | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"; then
    print_info "创建 conda 环境: $CONDA_ENV_NAME"
    conda create -y -n "$CONDA_ENV_NAME" -c conda-forge \
      python=3.11 cmake cxx-compiler pkg-config \
      "sysroot_linux-64=2.28" \
      "opencv=5" ffmpeg glog gflags jsoncpp libcurl \
      libjpeg-turbo libtiff openexr imath openjph libavif \
      libxml2 libxml2-16 openh264 libstdcxx-ng libgcc-ng \
      libdovi vulkan-loader libva libdeflate libpng
  fi
  conda activate "$CONDA_ENV_NAME"
  # 补齐运行期常见缺失库（已存在则 conda 会跳过）
  # gflags 是 glog CMake package 的 find_dependency；缺了会导致 find_package(glog) 失败
  # sysroot 2.28：使二进制可在 Ubuntu 22.04（glibc 2.35）VIDEO 容器中运行
  # opencv=5：RUNTIME 依赖 opencv2/geometry.hpp（OpenCV 4 无此头）
  conda install -y -c conda-forge \
    "sysroot_linux-64=2.28" \
    "opencv=5" \
    glog gflags \
    libxml2 libxml2-16 openh264 libstdcxx-ng libgcc-ng \
    libdovi vulkan-loader libva libdeflate libpng \
    libjpeg-turbo libtiff openexr imath openjph libavif >/dev/null 2>&1 || true
  # conda 的 libstdc++ 常在 gcc 子目录；挂载到容器时需出现在 $CONDA_PREFIX/lib（相对链接）
  local gcc_rel
  gcc_rel="$(ls -d "${CONDA_PREFIX}/lib/gcc/"*/*/ 2>/dev/null | tail -1 | sed "s|^${CONDA_PREFIX}/lib/||" || true)"
  if [[ -n "$gcc_rel" && -f "${CONDA_PREFIX}/lib/${gcc_rel}libstdc++.so.6" ]]; then
    ln -sfn "${gcc_rel}libstdc++.so.6" "${CONDA_PREFIX}/lib/libstdc++.so.6"
    [[ -f "${CONDA_PREFIX}/lib/${gcc_rel}libgcc_s.so.1" ]] && \
      ln -sfn "${gcc_rel}libgcc_s.so.1" "${CONDA_PREFIX}/lib/libgcc_s.so.1"
  fi
  export PATH="$CONDA_PREFIX/bin:$PATH"
}

has_nvidia_gpu() {
  if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

cuda_lib_paths() {
  # Host-side search path for linking/running RUNTIME.
  # Prefer CUDA toolkit dirs; allow multiarch dirs only when libcudart is present
  # (driver-only libcuda.so stubs are NOT enough and must not be mounted into
  # containers — see ensure_runtime_cpp.sh).
  local paths=() p d
  _has_cudart() {
    [[ -d "$1" ]] && compgen -G "${1}/libcudart.so*" >/dev/null 2>&1
  }
  for p in /usr/local/cuda/lib64 /usr/local/cuda/lib; do
    if _has_cudart "$p"; then
      paths+=("$p")
    fi
  done
  for d in /usr/local/cuda-*/lib64 /usr/local/cuda-*/lib; do
    if _has_cudart "$d"; then
      paths+=("$d")
    fi
  done
  for p in /usr/lib/x86_64-linux-gnu /usr/lib/aarch64-linux-gnu /usr/lib64; do
    if _has_cudart "$p"; then
      paths+=("$p")
    fi
  done
  local out="" s
  for s in "${paths[@]}"; do
    case ":$out:" in
      *":$s:"*) ;;
      *) out="${out:+$out:}$s" ;;
    esac
  done
  echo "$out"
}

# Paths safe to bind-mount into the VIDEO container as /opt/easyaiot/cuda-lib.
# Never return generic system lib dirs (they contain libc and break /bin/sh).
cuda_toolkit_mount_paths() {
  local paths=() p d
  _has_cudart() {
    [[ -d "$1" ]] && compgen -G "${1}/libcudart.so*" >/dev/null 2>&1
  }
  for p in /usr/local/cuda/lib64 /usr/local/cuda/lib; do
    if _has_cudart "$p"; then
      paths+=("$p")
    fi
  done
  for d in /usr/local/cuda-*/lib64 /usr/local/cuda-*/lib; do
    if _has_cudart "$d"; then
      paths+=("$d")
    fi
  done
  local out="" s
  for s in "${paths[@]}"; do
    case ":$out:" in
      *":$s:"*) ;;
      *) out="${out:+$out:}$s" ;;
    esac
  done
  echo "$out"
}

ensure_ort_sdk() {
  local arch
  arch="$(detect_arch)"
  if [[ "$arch" == "unknown" ]]; then
    print_error "不支持的 CPU 架构: $(uname -m)"
    return 1
  fi

  local want_gpu=0
  if has_nvidia_gpu; then
    want_gpu=1
    print_info "检测到 NVIDIA GPU，优先使用 ONNX Runtime GPU 包"
  else
    print_info "未检测到可用 NVIDIA GPU，使用 ONNX Runtime CPU 包"
  fi

  local cpu_root="$REPO/.deps/onnxruntime-linux-${arch}-${ORT_VERSION}"
  local gpu_root="$REPO/.deps/onnxruntime-linux-${arch}-gpu-${ORT_VERSION}"
  local default_root="$cpu_root"
  if [[ "$want_gpu" -eq 1 ]]; then
    default_root="$gpu_root"
  fi

  # Explicit ORT_ROOT wins if valid
  if [[ -n "${ORT_ROOT:-}" && -d "$ORT_ROOT/include" && -d "$ORT_ROOT/lib" ]]; then
    print_info "ONNX Runtime SDK (ORT_ROOT): $ORT_ROOT"
    export ORT_ROOT
    return 0
  fi

  # Prefer already-downloaded GPU SDK when GPU present
  if [[ "$want_gpu" -eq 1 && -d "$gpu_root/include" && -d "$gpu_root/lib" ]]; then
    ORT_ROOT="$gpu_root"
    export ORT_ROOT
    print_info "ONNX Runtime GPU SDK: $ORT_ROOT"
    return 0
  fi
  if [[ -d "$cpu_root/include" && -d "$cpu_root/lib" && "$want_gpu" -eq 0 ]]; then
    ORT_ROOT="$cpu_root"
    export ORT_ROOT
    print_info "ONNX Runtime CPU SDK: $ORT_ROOT"
    return 0
  fi

  mkdir -p "$REPO/.deps"
  download_and_extract_ort() {
    local variant="$1"  # "" or "gpu"
    local suffix=""
    local root="$cpu_root"
    if [[ "$variant" == "gpu" ]]; then
      suffix="-gpu"
      root="$gpu_root"
    fi
    local tarball="onnxruntime-linux-${arch}${suffix}-${ORT_VERSION}.tgz"
    local url="https://github.com/microsoft/onnxruntime/releases/download/v${ORT_VERSION}/${tarball}"
    local dest="$REPO/.deps/${tarball}"
    print_info "下载 ONNX Runtime C++ SDK: $url"
    if command -v curl >/dev/null 2>&1; then
      curl -fL --retry 3 -o "$dest" "$url" || return 1
    else
      wget -O "$dest" "$url" || return 1
    fi
    print_info "解压到 $root"
    rm -rf "$root"
    tar -xzf "$dest" -C "$REPO/.deps"
    # tarball may extract to expected folder name
    if [[ ! -d "$root/include" ]]; then
      # find freshly extracted dir
      local found
      found="$(find "$REPO/.deps" -maxdepth 1 -type d -name "onnxruntime-linux-${arch}${suffix}-${ORT_VERSION}" | head -1 || true)"
      if [[ -n "$found" && "$found" != "$root" ]]; then
        mv "$found" "$root"
      fi
    fi
    [[ -d "$root/include" && -d "$root/lib" ]]
  }

  if [[ "$want_gpu" -eq 1 ]]; then
    if download_and_extract_ort gpu; then
      ORT_ROOT="$gpu_root"
      export ORT_ROOT
      print_success "ORT GPU SDK 就绪: $ORT_ROOT"
      return 0
    fi
    print_warning "GPU ORT 包下载失败，回退 CPU 包"
  fi

  if [[ -d "$cpu_root/include" && -d "$cpu_root/lib" ]]; then
    ORT_ROOT="$cpu_root"
    export ORT_ROOT
    print_info "ONNX Runtime CPU SDK: $ORT_ROOT"
    return 0
  fi
  if download_and_extract_ort ""; then
    ORT_ROOT="$cpu_root"
    export ORT_ROOT
    print_success "ORT CPU SDK 就绪: $ORT_ROOT"
    return 0
  fi
  print_error "无法获取 ONNX Runtime SDK"
  return 1
}

write_deploy_env() {
  local bin="$ROOT/build/RUNTIME"
  local deploy_env="$ROOT/deploy.env"
  local conda_lib="${CONDA_PREFIX}/lib"
  local ort_lib="${ORT_ROOT}/lib"
  local cuda_libs cuda_mount
  cuda_libs="$(cuda_lib_paths)"
  # Container bind-mount must be toolkit-only (never /usr/lib/*)
  cuda_mount="$(cuda_toolkit_mount_paths)"
  local ld_path="$conda_lib:$ort_lib"
  if [[ -n "$cuda_libs" ]]; then
    ld_path="$ld_path:$cuda_libs"
  fi
  cat > "$deploy_env" <<EOF
# Auto-generated by RUNTIME/install_linux.sh — do not edit by hand
RUNTIME_BIN=$bin
RUNTIME_HOST_DIR=$ROOT
RUNTIME_CONDA_LIB_HOST=$conda_lib
RUNTIME_ORT_LIB_HOST=$ort_lib
RUNTIME_CUDA_LIB_HOST=$cuda_mount
LD_LIBRARY_PATH=$ld_path
CONDA_PREFIX=$CONDA_PREFIX
ORT_ROOT=$ORT_ROOT
RUNTIME_PREFER_GPU=true
USE_GPU=true
EOF
  print_success "已写入 $deploy_env"
}

build_runtime() {
  activate_runtime_env
  ensure_ort_sdk
  export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${ORT_ROOT}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  local cuda_libs
  cuda_libs="$(cuda_lib_paths)"
  if [[ -n "$cuda_libs" ]]; then
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:$cuda_libs"
  fi
  export PKG_CONFIG_PATH="${CONDA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
  export CMAKE_PREFIX_PATH="${CONDA_PREFIX}${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
  # Prefer GPU at runtime by default
  export RUNTIME_PREFER_GPU="${RUNTIME_PREFER_GPU:-true}"
  export USE_GPU="${USE_GPU:-true}"

  local build_dir="$ROOT/build"
  mkdir -p "$build_dir"
  # Prefer workspace TMPDIR (some sandboxes block /tmp)
  export TMPDIR="${TMPDIR:-$REPO/.tmp}"
  mkdir -p "$TMPDIR"

  print_info "cmake 配置..."
  cmake "$ROOT" \
    -B "$build_dir" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
    -DOpenCV_DIR="$CONDA_PREFIX/lib/cmake/opencv5" \
    -DONNXRUNTIME_ROOT="$ORT_ROOT" \
    -DCMAKE_CXX_FLAGS="-I$CONDA_PREFIX/include/opencv5"

  print_info "编译中..."
  cmake --build "$build_dir" -j"$(nproc 2>/dev/null || echo 4)"

  if [[ ! -x "$build_dir/RUNTIME" ]]; then
    print_error "编译完成但未找到可执行文件: $build_dir/RUNTIME"
    return 1
  fi
  write_deploy_env
  print_success "编译成功: $build_dir/RUNTIME"
}

status_runtime() {
  local bin="$ROOT/build/RUNTIME"
  if [[ -x "$bin" ]]; then
    print_success "二进制存在: $bin"
    if [[ -f "$ROOT/deploy.env" ]]; then
      print_info "deploy.env:"
      cat "$ROOT/deploy.env"
    fi
    return 0
  fi
  print_warning "二进制不存在: $bin（请运行 ./install_linux.sh）"
  return 1
}

main() {
  if [[ "${EASYAIOT_RUNTIME_SKIP:-0}" == "1" ]]; then
    print_warning "EASYAIOT_RUNTIME_SKIP=1，跳过 RUNTIME 安装"
    exit 0
  fi

  local cmd="${1:-install}"
  case "$cmd" in
    install|build)
      build_runtime
      ;;
    status)
      status_runtime
      ;;
    help|-h|--help)
      sed -n '2,20p' "$0"
      ;;
    *)
      print_error "未知命令: $cmd"
      exit 1
      ;;
  esac
}

main "$@"
