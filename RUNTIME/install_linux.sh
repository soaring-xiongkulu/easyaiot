#!/usr/bin/env bash
# ============================================
# RUNTIME (C++ 高性能执行器) 一键安装 / 编译
# ============================================
# 用法:
#   ./install_linux.sh              # 交互式菜单（TTY）或安装并编译（非 TTY）
#   ./install_linux.sh build        # 编译（TTY 下可选本机 conda / Docker）
#   ./install_linux.sh status       # 检查二进制与依赖
#
# 环境变量:
#   EASYAIOT_RUNTIME_SKIP=1              # 跳过（供上层脚本探测）
#   EASYAIOT_RUNTIME_REQUIRED=1          # 失败时以非 0 退出（由调用方决定）
#   ORT_ROOT                             # ONNX Runtime C++ SDK 根目录
#   EASYAIOT_RUNTIME_BUILD_MODE=docker|host
#       默认 docker：在 VIDEO 同源容器内用系统 g++ 编译（推荐，免 sysroot 降级）
#       host：本机 conda 编译（新 glibc 主机上产物可能无法进 VIDEO 容器）
#   EASYAIOT_RUNTIME_BUILD_IMAGE         # 覆盖构建镜像（默认优先 video-service:latest）
#   EASYAIOT_RUNTIME_DEPLOY_MODE=integrated
#       云边一体：需 VIDEO/Gateway/MQTT/SRS 地址，本机只装 RUNTIME
#       纯边缘形态请用平台安装：bash .scripts/docker/install_linux.sh install（选 edge → standalone）
#   VIDEO_BASE_URL / EASYAIOT_VIDEO_BASE_URL
#       云边一体必填：VIDEO 根地址，如 http://192.168.1.10:6000（本机合装则为本机 :6000）
#   GATEWAY_URL / EASYAIOT_GATEWAY_URL
#       云边一体可选：Gateway，如 http://192.168.1.10:48080
#   EASYAIOT_RUNTIME_INSTALL_DIR         # 节点安装目录（默认 /opt/easyaiot/RUNTIME）
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
REPO="$(cd "$ROOT/.." && pwd)"
ORT_VERSION="${ORT_VERSION:-1.23.2}"
CONDA_ENV_NAME="${EASYAIOT_RUNTIME_CONDA_ENV:-easyaiot-runtime}"
# 未显式指定时由交互菜单或非 TTY 默认值填充
BUILD_MODE="${EASYAIOT_RUNTIME_BUILD_MODE:-}"

# shellcheck disable=SC1091
source "$ROOT/scripts/version_meta.sh"
# shellcheck disable=SC1091
source "$ROOT/scripts/os_family.sh"
# shellcheck disable=SC1091
source "$ROOT/scripts/runtime_os_matrix.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[RUNTIME]${NC} $1"; }
print_success() { echo -e "${GREEN}[RUNTIME]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[RUNTIME]${NC} $1"; }
print_error() { echo -e "${RED}[RUNTIME]${NC} $1"; }

# 交互：主菜单（无子命令 + TTY）
prompt_main_command() {
  echo ""
  print_info "RUNTIME — 请选择操作:"
  echo "  1) 编译 RUNTIME"
  echo "  2) 查看编译/安装状态"
  echo "  3) 云边一体算力节点安装 (integrated)"
  echo "  4) 帮助"
  echo "  5) 退出"
  local choice
  read -r -p "请输入选项 [1]: " choice || choice="1"
  choice="${choice:-1}"
  case "$choice" in
    1|build|install|compile|update) echo "build" ;;
    2|status|start|restart) echo "status" ;;
    3|integrated|atomic|node) echo "integrated" ;;
    4|help|-h|--help) echo "help" ;;
    5|q|Q|exit|cancel) echo "exit" ;;
    *)
      print_warning "无效选项，默认：编译 RUNTIME"
      echo "build"
      ;;
  esac
}

# 交互：编译方式（install/build/update + TTY + 未设 EASYAIOT_RUNTIME_BUILD_MODE）
prompt_build_mode_if_needed() {
  if [[ -n "${EASYAIOT_RUNTIME_BUILD_MODE:-}" ]]; then
    BUILD_MODE="$EASYAIOT_RUNTIME_BUILD_MODE"
    return 0
  fi
  if [[ -n "${BUILD_MODE:-}" ]]; then
    return 0
  fi
  if [[ ! -t 0 ]]; then
    BUILD_MODE=docker
    export BUILD_MODE
    return 0
  fi
  echo ""
  print_info "请选择 RUNTIME 编译方式:"
  echo "  1) 本机 conda 一键编译（开发联调，自动识别用户 conda/ORT 路径）"
  echo "  2) Docker 同源容器编译（与 VIDEO 容器 glibc 一致，生产推荐）"
  echo "  3) 取消"
  local choice
  read -r -p "请输入选项 [1]: " choice || choice="1"
  choice="${choice:-1}"
  case "$choice" in
    1|host|conda|native)
      BUILD_MODE=host
      ;;
    2|docker|container)
      BUILD_MODE=docker
      ;;
    3|q|Q|cancel)
      print_info "已取消"
      exit 0
      ;;
    *)
      print_warning "无效选项，默认：本机 conda 编译"
      BUILD_MODE=host
      ;;
  esac
  export BUILD_MODE EASYAIOT_RUNTIME_BUILD_MODE="$BUILD_MODE"
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) echo "x64" ;;
    aarch64|arm64) echo "aarch64" ;;
    *) echo "unknown" ;;
  esac
}

find_conda_sh() {
  local candidates=()
  if [[ -n "${CONDA_EXE:-}" ]]; then
    candidates+=("${CONDA_EXE%/*}/../etc/profile.d/conda.sh")
  fi
  candidates+=(
    "${MINICONDA_PREFIX:-/opt/miniconda3}/etc/profile.d/conda.sh"
    "$HOME/miniconda3/etc/profile.d/conda.sh"
    "$HOME/anaconda3/etc/profile.d/conda.sh"
    /opt/conda/etc/profile.d/conda.sh
    /opt/miniconda3/etc/profile.d/conda.sh
    /usr/local/miniconda3/etc/profile.d/conda.sh
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

runtime_needs_glibc217_env() {
  if [[ "${RUNTIME_OS_FAMILY:-}" == "el7" ]]; then
    return 0
  fi
  local glibc_ver
  glibc_ver="$(ldd --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1 || true)"
  [[ "$glibc_ver" == "2.17" ]]
}

finalize_runtime_env_links() {
  # conda 的 libstdc++ 常在 gcc 子目录；挂载到 VIDEO 容器时需出现在 $CONDA_PREFIX/lib
  # 勿链到 gcc/.../libstdc++.so.6（其常指回 lib/libstdc++.so.6，形成环导致 cmake 落到系统 libstdc++）
  local gcc_rel ver real
  shopt -s nullglob
  for real in "${CONDA_PREFIX}/lib/libstdc++.so.6.0."*; do
    ver="$(basename "$real")"
    ln -sfn "$ver" "${CONDA_PREFIX}/lib/libstdc++.so.6"
    break
  done
  if [[ ! -e "${CONDA_PREFIX}/lib/libstdc++.so.6" ]]; then
    gcc_rel="$(ls -d "${CONDA_PREFIX}/lib/gcc/"*/*/ 2>/dev/null | tail -1 | sed "s|^${CONDA_PREFIX}/lib/||" || true)"
    for real in "${CONDA_PREFIX}/lib/${gcc_rel}"libstdc++.so.6.0.*; do
      ver="$(basename "$real")"
      ln -sfn "${gcc_rel}${ver}" "${CONDA_PREFIX}/lib/libstdc++.so.6"
      break
    done
  fi
  gcc_rel="$(ls -d "${CONDA_PREFIX}/lib/gcc/"*/*/ 2>/dev/null | tail -1 | sed "s|^${CONDA_PREFIX}/lib/||" || true)"
  if [[ -n "$gcc_rel" && -f "${CONDA_PREFIX}/lib/${gcc_rel}libgcc_s.so.1" ]]; then
    ln -sfn "${gcc_rel}libgcc_s.so.1" "${CONDA_PREFIX}/lib/libgcc_s.so.1"
  fi
  shopt -u nullglob
  export PATH="$CONDA_PREFIX/bin:$PATH"
}

activate_runtime_env_el7_x86() {
  # gxx 包的 activate/deactivate 脚本会引用可能未设置的 CONDA_BACKUP_*，与 set -u 冲突
  set +u
  trap 'set -u' RETURN
  conda config --set channel_priority flexible >/dev/null 2>&1 || true
  if ! conda env list | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"; then
    print_info "创建 EL7 x86_64 conda 环境（分步安装，兼容 glibc 2.17）"
    conda create -y -n "$CONDA_ENV_NAME" python=3.9
    conda activate "$CONDA_ENV_NAME"
    # 先装 gxx/libstdc++，再装 opencv；避免 opencv 已带入 gxx16 后再降级触发 200+ 包重求解
    conda install -y -c conda-forge \
      "gxx_linux-64=12.*" "libstdcxx-ng=12.*" "libgcc-ng=12.*" \
      "cmake=3.26.*" pkg-config
    conda install -y -c conda-forge "libopencv=5.0.0=qt6_hbf336e1_606" || \
      conda install -y -c conda-forge "opencv=5"
    conda install -y -c conda-forge \
      "glog=0.6.0" "gflags=2.2.2" "jsoncpp=1.9.5" \
      libcurl libjpeg-turbo libtiff libxml2 openh264 libva libdeflate libpng
  else
    conda activate "$CONDA_ENV_NAME"
  fi
  if [[ ! -x "${CONDA_PREFIX}/bin/x86_64-conda-linux-gnu-g++" ]]; then
    conda install -y -c conda-forge \
      "gxx_linux-64=12.*" "libstdcxx-ng=12.*" "libgcc-ng=12.*" "cmake=3.26.*" pkg-config
  fi
  if [[ ! -f "${CONDA_PREFIX}/lib/libopencv_core.so" ]]; then
    conda install -y -c conda-forge "libopencv=5.0.0=qt6_hbf336e1_606" || \
      conda install -y -c conda-forge "opencv=5"
    conda install -y -c conda-forge \
      "glog=0.6.0" "gflags=2.2.2" "jsoncpp=1.9.5" \
      libcurl libjpeg-turbo libtiff libxml2 openh264 libva libdeflate libpng
  fi
  finalize_runtime_env_links
}

activate_runtime_env_el7_arm() {
  set +u
  trap 'set -u' RETURN
  local mm="${MAMBA_EXE:-/opt/micromamba/bin/micromamba}"
  local root="${MAMBA_ROOT_PREFIX:-/opt/micromamba-root}"
  local env_prefix="${MINICONDA_PREFIX:-/opt/miniconda3}/envs/${CONDA_ENV_NAME}"
  if [[ ! -x "$mm" ]]; then
    print_error "EL7 aarch64 需要 micromamba（Miniconda 安装器要求 glibc>=2.25）"
    return 1
  fi
  export MAMBA_EXE="$mm"
  export MAMBA_ROOT_PREFIX="$root"
  eval "$("$mm" shell hook -s bash)"
  if [[ ! -x "$env_prefix/bin/python" ]]; then
    print_info "创建 EL7 aarch64 micromamba 环境（兼容 glibc 2.17）"
    "$mm" create -y -p "$env_prefix" python=3.11 -c conda-forge
  fi
  micromamba activate "$env_prefix"
  if [[ ! -f "${CONDA_PREFIX}/lib/libopencv_core.so" ]]; then
    micromamba install -y -p "$CONDA_PREFIX" -c conda-forge \
      "opencv=5" glog gflags jsoncpp cmake pkg-config "gxx_linux-aarch64=12.*" \
      ffmpeg libcurl libjpeg-turbo libtiff libxml2 openh264 libva libdeflate libpng
  elif [[ ! -x "${CONDA_PREFIX}/bin/aarch64-conda-linux-gnu-g++" ]]; then
    micromamba install -y -p "$CONDA_PREFIX" -c conda-forge "gxx_linux-aarch64=12.*"
  fi
  finalize_runtime_env_links
}

# 宿主机 conda 仅提供运行/链接依赖（OpenCV5、glog…），不强制使用其 cxx-compiler sysroot
activate_runtime_env() {
  local conda_sh
  if ! conda_sh="$(find_conda_sh)"; then
    print_error "未找到 conda，请先安装 Miniconda/Anaconda"
    return 1
  fi
  # shellcheck disable=SC1090
  source "$conda_sh"

  if runtime_needs_glibc217_env; then
    case "$(uname -m)" in
      aarch64|arm64) activate_runtime_env_el7_arm ;;
      *) activate_runtime_env_el7_x86 ;;
    esac
    return 0
  fi

  if ! conda env list | awk '{print $1}' | grep -qx "$CONDA_ENV_NAME"; then
    print_info "创建 conda 环境: $CONDA_ENV_NAME（依赖库；编译默认走 VIDEO 同源容器）"
    conda create -y -n "$CONDA_ENV_NAME" -c conda-forge \
      python=3.11 cmake pkg-config \
      "opencv=5" ffmpeg glog gflags jsoncpp libcurl \
      libjpeg-turbo libtiff openexr imath openjph libavif \
      libxml2 libxml2-16 openh264 libstdcxx-ng libgcc-ng \
      libdovi vulkan-loader libva libdeflate libpng
  fi
  conda activate "$CONDA_ENV_NAME"
  # 补齐运行期常见缺失库（已存在则 conda 会跳过）
  # gflags：glog CMake package 的 find_dependency
  # opencv=5：RUNTIME 依赖 opencv2/geometry.hpp
  conda install -y -c conda-forge \
    "opencv=5" \
    glog gflags \
    libxml2 libxml2-16 openh264 libstdcxx-ng libgcc-ng \
    libdovi vulkan-loader libva libdeflate libpng \
    libjpeg-turbo libtiff openexr imath openjph libavif >/dev/null 2>&1 || true
  finalize_runtime_env_links
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
  if ((${#paths[@]})); then
    for s in "${paths[@]}"; do
      case ":$out:" in
        *":$s:"*) ;;
        *) out="${out:+$out:}$s" ;;
      esac
    done
  fi
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
  if ((${#paths[@]})); then
    for s in "${paths[@]}"; do
      case ":$out:" in
        *":$s:"*) ;;
        *) out="${out:+$out:}$s" ;;
      esac
    done
  fi
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

write_version_and_deploy_env() {
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

  runtime_resolve_version_meta "$ROOT" "$REPO"
  runtime_write_version_file "$ROOT/build/VERSION" "local-build" "$bin" "$ORT_ROOT" "$BUILD_MODE"
  # 源码树根也放一份，便于控制面/VIDEO 快速读取
  runtime_write_version_file "$ROOT/VERSION" "local-build" "$bin" "$ORT_ROOT" "$BUILD_MODE"
  print_success "已写入版本: ${RUNTIME_VERSION} → $ROOT/build/VERSION"

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
RUNTIME_BUILD_MODE=$BUILD_MODE
RUNTIME_VERSION=${RUNTIME_VERSION}
RUNTIME_GIT=${RUNTIME_GIT}
RUNTIME_BUILT_AT=${RUNTIME_BUILT_AT}
EOF
  print_success "已写入 $deploy_env"
}

# 向后兼容旧调用名
write_deploy_env() {
  write_version_and_deploy_env
}

resolve_build_image() {
  if [[ -n "${EASYAIOT_RUNTIME_BUILD_IMAGE:-}" ]]; then
    echo "$EASYAIOT_RUNTIME_BUILD_IMAGE"
    return 0
  fi
  # Prefer local VIDEO runtime image (same Ubuntu/glibc as deploy target)
  if docker image inspect video-service:latest >/dev/null 2>&1; then
    echo "video-service:latest"
    return 0
  fi
  # Same base family as VIDEO/Dockerfile
  if docker image inspect pytorch/pytorch:2.9.0-cuda12.8-cudnn9-devel >/dev/null 2>&1; then
    echo "pytorch/pytorch:2.9.0-cuda12.8-cudnn9-devel"
    return 0
  fi
  echo "ubuntu:22.04"
}

docker_available() {
  command -v docker >/dev/null 2>&1 || return 1
  docker info >/dev/null 2>&1 || return 1
}

# RUNTIME 编译失败时的详细诊断（仅 VIDEO/RUNTIME 链路使用）
dump_runtime_build_failure() {
  local context="${1:-build}"
  echo ""
  print_error "========================================"
  print_error "  RUNTIME 编译失败 — 详细诊断 (${context})"
  print_error "========================================"
  print_error "时间: $(date '+%Y-%m-%d %H:%M:%S')"
  print_error "系统: $(uname -s) $(uname -m) $(uname -r 2>/dev/null || true)"
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    print_error "发行版: ${PRETTY_NAME:-${ID:-?} ${VERSION_ID:-}}"
  fi
  print_error "构建模式: ${BUILD_MODE:-?}  ORT_ROOT=${ORT_ROOT:-?}  CONDA_ENV=${CONDA_ENV_NAME:-?}"
  print_error "用户: $(id -un 2>/dev/null || echo ?) uid=$(id -u)"

  if command -v docker >/dev/null 2>&1; then
    print_error "docker: $(command -v docker) — $(docker --version 2>/dev/null || echo '?')"
    while IFS= read -r line; do
      print_error "  ${line}"
    done < <(docker info 2>&1 | head -n 30 || true)
  else
    print_error "docker: 未安装或不在 PATH"
  fi

  if command -v conda >/dev/null 2>&1; then
    print_error "conda: $(conda --version 2>/dev/null || true)"
  else
    print_error "conda: 未检测到（host 模式需要）"
  fi

  if [[ -d "$ROOT/build" ]]; then
    print_error "build 目录:"
    ls -la "$ROOT/build" 2>/dev/null | tail -n 25 | while IFS= read -r line; do
      print_error "  ${line}"
    done || true
  fi
  print_error "可尝试: EASYAIOT_RUNTIME_BUILD_MODE=host $0 install"
  print_error "或跳过: EASYAIOT_RUNTIME_SKIP=1"
  echo ""
}

_runtime_try_install_pkgs() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    return 1
  fi
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    print_warning "自动安装软件包需要 root（sudo），当前非 root，跳过"
    return 1
  fi
  local pkgs=("$@")
  if command -v apt-get >/dev/null 2>&1; then
    print_info "apt-get 安装: ${pkgs[*]}"
    DEBIAN_FRONTEND=noninteractive apt-get update -qq >/dev/null 2>&1 || true
    DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}"
  elif command -v dnf >/dev/null 2>&1; then
    print_info "dnf 安装: ${pkgs[*]}"
    dnf install -y "${pkgs[@]}"
  elif command -v yum >/dev/null 2>&1; then
    print_info "yum 安装: ${pkgs[*]}"
    yum install -y "${pkgs[@]}"
  else
    print_warning "无 apt/dnf/yum，无法自动安装: ${pkgs[*]}"
    return 1
  fi
}

_runtime_auto_install_docker() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    print_error "非 Linux，请安装 Docker Desktop 后重试"
    return 1
  fi
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    print_error "自动安装 Docker 需要 root：sudo $0 install"
    print_error "  或: curl -fsSL https://get.docker.com | sudo sh"
    return 1
  fi
  if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
    _runtime_try_install_pkgs curl ca-certificates || true
  fi
  print_info "开始自动安装 Docker（get.docker.com）..."
  local log="${REPO}/.scripts/docker/logs/runtime_docker_install_$(date +%Y%m%d_%H%M%S).log"
  mkdir -p "$(dirname "$log")" 2>/dev/null || true
  {
    echo "==== runtime auto-install docker $(date '+%Y-%m-%d %H:%M:%S') ===="
  } >>"$log" 2>/dev/null || true
  if command -v curl >/dev/null 2>&1; then
    if ! curl -fsSL https://get.docker.com 2>>"$log" | sh 2>>"$log"; then
      print_error "Docker 自动安装失败，日志: $log"
      tail -n 40 "$log" 2>/dev/null | while IFS= read -r line; do print_error "  $line"; done || true
      return 1
    fi
  else
    if ! wget -qO- https://get.docker.com 2>>"$log" | sh 2>>"$log"; then
      print_error "Docker 自动安装失败，日志: $log"
      tail -n 40 "$log" 2>/dev/null | while IFS= read -r line; do print_error "  $line"; done || true
      return 1
    fi
  fi
  systemctl enable docker >/dev/null 2>&1 || true
  systemctl start docker >/dev/null 2>&1 || service docker start >/dev/null 2>&1 || true
  if ! command -v docker >/dev/null 2>&1; then
    print_error "安装脚本已执行，但 docker 命令仍不可用（详见 $log）"
    return 1
  fi
  print_success "Docker 已安装: $(docker --version 2>/dev/null || echo ok)"
  return 0
}

# VIDEO→RUNTIME 部署前：检查并尽量自动补齐本机编译依赖（仅 RUNTIME，不波及其他模块）
prepare_runtime_build_env() {
  print_info "===== RUNTIME 部署前环境检查 ====="
  local fail=0
  local mode="${BUILD_MODE:-docker}"

  # 基础工具
  local missing=()
  command -v tar >/dev/null 2>&1 || missing+=(tar)
  if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
    missing+=(curl)
  fi
  if [[ ${#missing[@]} -gt 0 ]]; then
    print_warning "缺少工具: ${missing[*]}，尝试自动安装..."
    if [[ "${EASYAIOT_AUTO_INSTALL_DEPS:-1}" == "1" ]]; then
      _runtime_try_install_pkgs "${missing[@]}" || fail=1
    else
      fail=1
    fi
  else
    print_success "基础工具就绪 (curl/wget + tar)"
  fi

  case "$mode" in
    docker|container)
      if docker_available; then
        print_success "Docker 可用: $(docker --version 2>/dev/null || true)"
      else
        if command -v docker >/dev/null 2>&1; then
          print_warning "已安装 docker 但 daemon 不可用，尝试启动..."
          if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
            systemctl start docker >/dev/null 2>&1 || service docker start >/dev/null 2>&1 || true
          fi
        fi
        if ! docker_available; then
          print_warning "Docker 不可用，尝试自动安装..."
          if [[ "${EASYAIOT_AUTO_INSTALL_DEPS:-1}" == "1" ]]; then
            _runtime_auto_install_docker || true
          else
            print_error "Docker 不可用且 EASYAIOT_AUTO_INSTALL_DEPS=0"
          fi
        fi
        if docker_available; then
          print_success "Docker 已就绪"
        else
          print_error "Docker 仍不可用（docker 模式编译需要）"
          fail=1
        fi
      fi
      ;;
    host|native)
      if find_conda_sh >/dev/null 2>&1; then
        print_success "conda 可用（host 编译）"
      else
        print_error "host 模式需要 Miniconda/Anaconda，未找到 conda"
        print_error "  安装: https://docs.conda.io/en/latest/miniconda.html"
        print_error "  或改用: EASYAIOT_RUNTIME_BUILD_MODE=docker"
        fail=1
      fi
      ;;
  esac

  if [[ "$fail" -ne 0 ]]; then
    dump_runtime_build_failure prepare
    return 1
  fi
  print_success "RUNTIME 环境检查通过"
  return 0
}

build_runtime_in_docker() {
  if ! docker_available; then
    print_error "docker 不可用，无法使用同源容器编译。可设 EASYAIOT_RUNTIME_BUILD_MODE=host 回退本机编译"
    return 1
  fi

  local image
  image="$(resolve_build_image)"
  print_info "构建镜像: $image（系统 g++，与 VIDEO 同源 glibc）"
  if [[ "$image" == "ubuntu:22.04" ]] || [[ "$image" == ubuntu:22.04* ]]; then
    print_info "拉取/确保基础镜像可用: $image"
    docker pull "$image" >/dev/null || true
  fi

  local inner="$ROOT/scripts/build_inside_container.sh"
  if [[ ! -f "$inner" ]]; then
    print_error "缺少容器内编译脚本: $inner"
    return 1
  fi
  chmod +x "$inner" || true

  mkdir -p "$ROOT/build"
  # Prefer workspace TMPDIR (some sandboxes block /tmp)
  export TMPDIR="${TMPDIR:-$REPO/.tmp}"
  mkdir -p "$TMPDIR"

  local uid gid
  uid="$(id -u)"
  gid="$(id -g)"

  # Avoid NVIDIA CDI/NVML failures on hosts without working driver
  local -a docker_opts=(
    --rm
    --runtime=runc
    -e NVIDIA_VISIBLE_DEVICES=
    -e CONDA_PREFIX=/opt/conda-runtime
    -e ORT_ROOT=/opt/ort
    -e RUNTIME_SRC=/src/RUNTIME
    -v "$REPO:/src:rw"
    -v "$CONDA_PREFIX:/opt/conda-runtime:ro"
    -v "$ORT_ROOT:/opt/ort:ro"
    -w /src/RUNTIME
  )

  # video-service / pytorch images already have g++(+cmake)；用当前用户写出产物
  # ubuntu:22.04 需 root 装编译器，结束后 chown
  local use_root=0
  case "$image" in
    ubuntu:22.04|ubuntu:22.04*) use_root=1 ;;
  esac

  if [[ "$use_root" -eq 0 ]]; then
    docker_opts+=(-u "${uid}:${gid}")
  fi

  runtime_resolve_version_meta "$ROOT" "$REPO"
  docker_opts+=(-e "RUNTIME_VERSION_STR=${RUNTIME_VERSION}")

  print_info "在容器内编译 RUNTIME（version=${RUNTIME_VERSION}）..."
  if ! docker run "${docker_opts[@]}" "$image" bash /src/RUNTIME/scripts/build_inside_container.sh; then
    print_error "容器内编译失败"
    return 1
  fi

  if [[ "$use_root" -eq 1 ]]; then
    docker run --rm --runtime=runc -e NVIDIA_VISIBLE_DEVICES= \
      -v "$ROOT:/src/RUNTIME:rw" \
      "$image" \
      chown -R "${uid}:${gid}" /src/RUNTIME/build || true
  fi

  if [[ ! -x "$ROOT/build/RUNTIME" ]]; then
    print_error "编译完成但未找到可执行文件: $ROOT/build/RUNTIME"
    return 1
  fi
}

runtime_el7_conda_cxx() {
  local c
  for c in \
    "${CONDA_PREFIX}/bin/x86_64-conda-linux-gnu-g++" \
    "${CONDA_PREFIX}/bin/aarch64-conda-linux-gnu-g++"; do
    if [[ -x "$c" ]]; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

build_runtime_on_host() {
  if ! runtime_needs_glibc217_env; then
    print_info "本机 conda 一键编译（自动识别 conda/ORT 路径）..."
    bash "$ROOT/scripts/build_linux.sh"
    return $?
  fi

  print_warning "EASYAIOT_RUNTIME_BUILD_MODE=host：本机 conda 编译；新 glibc 主机产物可能无法在 VIDEO(22.04) 容器内运行"
  export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${ORT_ROOT}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  local cuda_libs
  cuda_libs="$(cuda_lib_paths)"
  if [[ -n "$cuda_libs" ]]; then
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:$cuda_libs"
  fi
  export PKG_CONFIG_PATH="${CONDA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
  export CMAKE_PREFIX_PATH="${CONDA_PREFIX}${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"

  local el7_link_flags=""
  if runtime_needs_glibc217_env; then
    local conda_cxx conda_cc
    if ! conda_cxx="$(runtime_el7_conda_cxx)"; then
      print_error "EL7 需要 conda gxx（与 conda OpenCV/jsoncpp ABI 一致；devtoolset 默认旧 ABI 无法链接）"
      return 1
    fi
    conda_cc="${conda_cxx/g++/gcc}"
    export CC="$conda_cc"
    export CXX="$conda_cxx"
    el7_link_flags="-L${CONDA_PREFIX}/lib -Wl,-rpath-link,${CONDA_PREFIX}/lib"
    export LDFLAGS="${el7_link_flags}${LDFLAGS:+ $LDFLAGS}"
    print_info "EL7 使用 conda 编译器: $CXX"
  fi

  local build_dir="$ROOT/build"
  mkdir -p "$build_dir"
  export TMPDIR="${TMPDIR:-$REPO/.tmp}"
  mkdir -p "$TMPDIR"

  runtime_resolve_version_meta "$ROOT" "$REPO"
  print_info "cmake 配置（host, version=${RUNTIME_VERSION}）..."
  local cmake_bin="cmake"
  if runtime_needs_glibc217_env && [[ -x "${CONDA_PREFIX}/bin/cmake" ]]; then
    cmake_bin="${CONDA_PREFIX}/bin/cmake"
  fi
  local -a cmake_extra=()
  if [[ -n "$el7_link_flags" ]]; then
    cmake_extra+=(-DCMAKE_EXE_LINKER_FLAGS="$el7_link_flags")
    cmake_extra+=(-DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX")
  fi
  if ! "$cmake_bin" "$ROOT" \
    -B "$build_dir" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
    -DOpenCV_DIR="$CONDA_PREFIX/lib/cmake/opencv5" \
    -DONNXRUNTIME_ROOT="$ORT_ROOT" \
    -DRUNTIME_VERSION_STR="${RUNTIME_VERSION}" \
    -DCMAKE_CXX_FLAGS="-I$CONDA_PREFIX/include/opencv5" \
    "${cmake_extra[@]}"; then
    print_error "cmake 配置失败"
    return 1
  fi

  print_info "编译中..."
  if ! "$cmake_bin" --build "$build_dir" -j"$(nproc 2>/dev/null || echo 4)"; then
    print_error "cmake 编译失败"
    return 1
  fi

  if [[ ! -x "$build_dir/RUNTIME" ]]; then
    print_error "编译完成但未找到可执行文件: $build_dir/RUNTIME"
    return 1
  fi
}

build_runtime() {
  prompt_build_mode_if_needed

  # 部署前检查/自动补齐（仅 RUNTIME；失败给出详细诊断）
  if ! prepare_runtime_build_env; then
    return 1
  fi

  ensure_ort_sdk
  export RUNTIME_PREFER_GPU="${RUNTIME_PREFER_GPU:-true}"
  export USE_GPU="${USE_GPU:-true}"

  case "$BUILD_MODE" in
    docker|container)
      BUILD_MODE=docker
      if ! activate_runtime_env; then
        return 1
      fi
      if ! build_runtime_in_docker; then
        dump_runtime_build_failure docker
        return 1
      fi
      ;;
    host|native)
      BUILD_MODE=host
      if ! build_runtime_on_host; then
        dump_runtime_build_failure host
        return 1
      fi
      # shellcheck disable=SC1091
      source "$ROOT/scripts/env.sh" >/dev/null 2>&1 || true
      ;;
    *)
      print_error "未知 EASYAIOT_RUNTIME_BUILD_MODE=$BUILD_MODE（可选 docker|host）"
      return 1
      ;;
  esac

  write_version_and_deploy_env
  print_success "编译成功: $ROOT/build/RUNTIME (mode=$BUILD_MODE, version=${RUNTIME_VERSION})"
}

status_runtime() {
  local bin="$ROOT/build/RUNTIME"
  local install_dir="${EASYAIOT_RUNTIME_INSTALL_DIR:-/opt/easyaiot/RUNTIME}"
  if [[ -x "$bin" ]]; then
    print_success "编译产物: $bin"
  elif [[ -x "$install_dir/bin/RUNTIME" ]]; then
    print_success "原子安装: $install_dir/bin/RUNTIME"
    bin="$install_dir/bin/RUNTIME"
  else
    print_warning "二进制不存在（请运行 ./install_linux.sh 或 ./install_linux.sh atomic）"
    return 1
  fi
  if [[ -f "$ROOT/build/VERSION" ]]; then
    print_info "build/VERSION:"
    cat "$ROOT/build/VERSION"
  elif [[ -f "$install_dir/VERSION" ]]; then
    print_info "安装目录 VERSION:"
    cat "$install_dir/VERSION"
  fi
  if [[ -x "$bin" ]]; then
    print_info "二进制 --version:"
    "$bin" --version 2>/dev/null || true
  fi
  if [[ -f "$ROOT/deploy.env" ]]; then
    print_info "deploy.env:"
    cat "$ROOT/deploy.env"
  fi
  if [[ -f "$install_dir/node.env" ]]; then
    print_info "原子节点 node.env:"
    cat "$install_dir/node.env"
  fi
  return 0
}

normalize_video_base_url() {
  local raw="${1:-}"
  raw="${raw%%/}"
  if [[ -z "$raw" ]]; then
    return 1
  fi
  case "$raw" in
    http://*|https://*) echo "$raw" ;;
    *) echo "http://${raw}" ;;
  esac
}

normalize_gateway_url() {
  local raw="${1:-}"
  raw="${raw%%/}"
  if [[ -z "$raw" ]]; then
    return 1
  fi
  case "$raw" in
    http://*|https://*) echo "$raw" ;;
    *) echo "http://${raw}" ;;
  esac
}

resolve_video_base_url() {
  local raw="${VIDEO_BASE_URL:-${EASYAIOT_VIDEO_BASE_URL:-${1:-}}}"
  if [[ -z "$raw" ]]; then
    return 1
  fi
  normalize_video_base_url "$raw"
}

resolve_gateway_url() {
  local raw="${GATEWAY_URL:-${EASYAIOT_GATEWAY_URL:-${CONTROL_PLANE_URL:-${1:-}}}}"
  if [[ -z "$raw" ]]; then
    return 1
  fi
  normalize_gateway_url "$raw"
}

runtime_detect_local_ip() {
  if [[ -n "${EDGE_HOST:-${EASYAIOT_EDGE_HOST:-}}" ]]; then
    echo "${EDGE_HOST:-${EASYAIOT_EDGE_HOST}}"
    return 0
  fi
  local ip
  ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  if [[ -n "$ip" && "$ip" != "127.0.0.1" ]]; then
    echo "$ip"
    return 0
  fi
  ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' || true)"
  [[ -n "$ip" ]] && echo "$ip" || echo "127.0.0.1"
}

runtime_assert_os_supported() {
  local os_family arch
  os_family="$(runtime_detect_os_family)"
  arch="$(runtime_arch_key)"
  print_info "检测操作系统: os_family=${os_family} arch=${arch}"
  if ! runtime_matrix_assert_supported "$os_family" "$arch"; then
    print_error "当前操作系统不在 RUNTIME 覆盖矩阵内，无法部署"
    print_info "支持的 os_family:arch 见 RUNTIME/scripts/runtime_os_matrix.sh"
    return 1
  fi
  print_success "操作系统已支持: ${os_family}:${arch}"
  return 0
}

runtime_find_bundle_tarball() {
  local os_family="$1"
  local arch="$2"
  local candidates=(
    "$ROOT/.bundle-runtime/${os_family}/${arch}/easyaiot-runtime-${os_family}-${arch}.tar.gz"
    "$ROOT/.bundle-runtime/${arch}/easyaiot-runtime-${arch}.tar.gz"
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -f "$c" ]]; then
      echo "$c"
      return 0
    fi
  done
  find "$ROOT/.bundle-runtime" -name "easyaiot-runtime-${os_family}-${arch}.tar.gz" 2>/dev/null | head -1 || true
}

runtime_ensure_bundle_tarball() {
  local -n _out_ref="${1:?output variable name required}"
  local os_family arch tar_path export_sh
  os_family="$(runtime_detect_os_family)"
  arch="$(runtime_arch_key)"
  tar_path="$(runtime_find_bundle_tarball "$os_family" "$arch")"
  if [[ -n "$tar_path" && -f "$tar_path" ]]; then
    print_success "已有离线包: $tar_path"
    _out_ref="$tar_path"
    return 0
  fi

  print_info "未找到 ${os_family}/${arch} 离线包，开始按本机 OS 编译导出..."
  build_runtime

  export_sh="$ROOT/export_runtime_cpp.sh"
  if [[ ! -f "$export_sh" ]]; then
    print_error "缺少 $export_sh"
    return 1
  fi
  RUNTIME_AUTO_INSTALL=0 RUNTIME_OS_FAMILY="$os_family" bash "$export_sh"

  tar_path="$(runtime_find_bundle_tarball "$os_family" "$arch")"
  if [[ -z "${tar_path:-}" || ! -f "$tar_path" ]]; then
    print_error "编译导出后仍未找到 offline tarball（os=${os_family} arch=${arch}）"
    print_info "可尝试容器内导出: bash RUNTIME/scripts/export_runtime_os_container.sh ${os_family}"
    return 1
  fi
  print_success "已生成离线包: $tar_path"
  _out_ref="$tar_path"
  return 0
}

write_node_env() {
  local mode="$1"
  local install_dir="$2"
  local video_base="$3"
  local gateway_base="${4:-}"
  local edge_host="${5:-}"
  local node_env="$install_dir/node.env"
  local hb_realtime="${video_base}/video/algorithm/heartbeat/realtime"
  local hb_patrol="${video_base}/video/algorithm/heartbeat/patrol"
  local srs_base="${SRS_RTMP_BASE:-${EASYAIOT_SRS_RTMP_BASE:-}}"
  local ai_rtmp="${AI_RTMP_URL:-${EASYAIOT_AI_RTMP_URL:-}}"
  local mqtt_urls="${MQTT_BROKER_URLS:-}"
  local enable_rtmp="false"
  local deploy_mode="$mode"
  local mode_comment=""

  case "$mode" in
    integrated|atomic|edge-integrated|cloud-edge|"")
      deploy_mode="integrated"
      mode_comment="云边一体 — 本机只装 RUNTIME，汇聚面指向 VIDEO/Gateway（可在远端或本机）"
      ;;
    *)
      print_error "未知部署形态: $mode（仅支持 integrated / atomic）"
      print_info "纯边缘形态请用: bash .scripts/docker/install_linux.sh install（选 edge → standalone）"
      return 1
      ;;
  esac

  if [[ -z "$ai_rtmp" && -n "$srs_base" ]]; then
    ai_rtmp="${srs_base%/}/ai/atomic_demo"
  fi
  if [[ -n "$ai_rtmp" ]]; then
    enable_rtmp="true"
  fi

  cat > "$node_env" <<EOF
# Auto-generated by RUNTIME ${deploy_mode} mode — ${mode_comment}
EASYAIOT_RUNTIME_DEPLOY_MODE=${deploy_mode}
VIDEO_BASE_URL=${video_base}
GATEWAY_URL=${gateway_base}
EDGE_HOST=${edge_host}
ALGO_BUS_TRANSPORT=mqtt
MQTT_BROKER_URLS=${mqtt_urls}
MQTT_ALGO_TENANT=${MQTT_ALGO_TENANT:-default}
MQTT_ALGO_USERNAME=${MQTT_ALGO_USERNAME:-}
MQTT_ALGO_PASSWORD=${MQTT_ALGO_PASSWORD:-}
MQTT_ALGO_CLIENT_ID=${MQTT_ALGO_CLIENT_ID:-algo-runtime-${deploy_mode}}
ALERT_IMAGES_DIR=${ALERT_IMAGES_DIR:-${install_dir}/cache/alerts}
HEARTBEAT_URL=${hb_realtime}
HEARTBEAT_URL_PATROL=${hb_patrol}
RUNTIME_BIN=${install_dir}/bin/RUNTIME
RUNTIME_PREFER_GPU=true
USE_GPU=true
SRS_RTMP_BASE=${srs_base}
AI_RTMP_URL=${ai_rtmp}
CONTROL_PLANE_URL=${CONTROL_PLANE_URL:-${gateway_base}/admin-api/node/agent}
EOF

  cat > "$install_dir/env.sh" <<EOF
#!/usr/bin/env bash
# Sourced on compute nodes (${deploy_mode} / iot-node install)
RUNTIME_ROOT="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
export RUNTIME_ROOT
export EASYAIOT_RUNTIME_INSTALL_DIR="\${EASYAIOT_RUNTIME_INSTALL_DIR:-\$RUNTIME_ROOT}"
# shellcheck disable=SC1091
[[ -f "\${RUNTIME_ROOT}/node.env" ]] && set -a && source "\${RUNTIME_ROOT}/node.env" && set +a
export RUNTIME_BIN="\${RUNTIME_BIN:-\${RUNTIME_ROOT}/bin/RUNTIME}"
export LD_LIBRARY_PATH="\${RUNTIME_ROOT}/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
for _cuda in /usr/local/cuda/lib64 /usr/local/cuda/lib; do
  if [[ -d "\$_cuda" ]]; then
    export LD_LIBRARY_PATH="\${LD_LIBRARY_PATH}:\$_cuda"
  fi
done
export RUNTIME_PREFER_GPU="\${RUNTIME_PREFER_GPU:-true}"
export USE_GPU="\${USE_GPU:-true}"
export EASYAIOT_RUNTIME_DEPLOY_MODE="\${EASYAIOT_RUNTIME_DEPLOY_MODE:-${deploy_mode}}"
export VIDEO_BASE_URL="\${VIDEO_BASE_URL:-}"
export GATEWAY_URL="\${GATEWAY_URL:-}"
export EDGE_HOST="\${EDGE_HOST:-}"
export ALGO_BUS_TRANSPORT="\${ALGO_BUS_TRANSPORT:-mqtt}"
export MQTT_BROKER_URLS="\${MQTT_BROKER_URLS:-}"
export HEARTBEAT_URL="\${HEARTBEAT_URL:-\${VIDEO_BASE_URL}/video/algorithm/heartbeat/realtime}"
export SRS_RTMP_BASE="\${SRS_RTMP_BASE:-}"
export AI_RTMP_URL="\${AI_RTMP_URL:-}"
# .pt→onnx：有 ultralytics 时设置，例如 export RUNTIME_PYTHON=/usr/bin/python3
EOF
  chmod +x "$install_dir/env.sh"

  mkdir -p "$install_dir/config"
  cat > "$install_dir/config/atomic.example.ini" <<EOF
# ${deploy_mode} 节点示例任务配置（手工调试用）
# 正式任务由 VIDEO/Agent 生成 task_*.ini（realtime 默认 enable_rtmp + 独立 ai/ 地址）

[video]
rtsp_url=rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101
rtmp_url=${ai_rtmp}
width=1920
height=1080
fps=25

[ai]
enable=true
model_path=${install_dir}/models/yolo11n.onnx
classes_path=${install_dir}/models/coco.names
threads=2
prefer_gpu=true
force_cpu=false
gpu_device_id=0
prefer_hwaccel=true
force_soft_av=false
hwaccel_device_id=0
nvenc_preset=p3

[alarm]
enable=true
confidence_threshold=0.5
cooldown_time=30
image_dir=${ALERT_IMAGES_DIR:-${install_dir}/cache/alerts}

[task]
id=atomic_demo
control_port=8123

[video_task]
device_id=camera_atomic_001
device_name=atomic-demo
task_type=realtime
algorithm_name=detection
heartbeat_url=${hb_realtime}
heartbeat_interval_sec=10
log_path=${install_dir}/cache/atomic_demo
alert_image_dir=${ALERT_IMAGES_DIR:-${install_dir}/cache/alerts}
algo_bus_transport=mqtt
mqtt_broker_urls=${mqtt_urls}
mqtt_tenant=${MQTT_ALGO_TENANT:-default}
headless=true

[mqtt]
broker_urls=${mqtt_urls}
tenant=${MQTT_ALGO_TENANT:-default}
transport=mqtt

[features]
enable_rtmp=${enable_rtmp}
enable_draw=true
enable_alarm=true
EOF

  print_success "已写入节点配置 (${deploy_mode}): $node_env"
  print_info "告警: MQTT → iot-sink (MQTT_BROKER_URLS=${mqtt_urls:-unset})"
  print_info "心跳: $hb_realtime"
  if [[ -n "$ai_rtmp" ]]; then
    print_info "检测推流 AI_RTMP_URL=$ai_rtmp (enable_rtmp=$enable_rtmp)"
  fi
}

write_atomic_node_env() {
  write_node_env "integrated" "$1" "$2" "${GATEWAY_URL:-}" ""
}

install_node_env_files() {
  local mode="$1"
  local install_dir="$2"
  local video_base="$3"
  local gateway_base="${4:-}"
  local edge_host="${5:-}"

  if [[ -w "$install_dir" ]]; then
    write_node_env "$mode" "$install_dir" "$video_base" "$gateway_base" "$edge_host"
    return 0
  fi
  local tmp_env
  tmp_env="$(mktemp -d)"
  write_node_env "$mode" "$tmp_env" "$video_base" "$gateway_base" "$edge_host"
  sudo cp -f "$tmp_env/node.env" "$install_dir/node.env"
  sudo cp -f "$tmp_env/env.sh" "$install_dir/env.sh"
  sudo mkdir -p "$install_dir/config"
  sudo cp -f "$tmp_env/config/atomic.example.ini" "$install_dir/config/atomic.example.ini"
  sudo chmod +x "$install_dir/env.sh"
  rm -rf "$tmp_env"
}

deploy_runtime_common() {
  local mode="$1"
  local install_dir="${EASYAIOT_RUNTIME_INSTALL_DIR:-/opt/easyaiot/RUNTIME}"
  local tar_path install_sh

  if ! runtime_assert_os_supported; then
    return 1
  fi

  if ! runtime_ensure_bundle_tarball tar_path; then
    return 1
  fi

  install_sh="$ROOT/install_runtime_cpp.sh"
  if [[ ! -f "$install_sh" ]]; then
    print_error "缺少 $install_sh"
    return 1
  fi

  print_info "安装离线包到 $install_dir ..."
  bash "$install_sh" "$install_dir" "$tar_path"
  return 0
}

# 云边一体：本机仅部署边缘算力，汇聚面指向中心平台
# 用法:
#   VIDEO_BASE_URL=http://<中心>:6000 GATEWAY_URL=http://<中心>:48080 ./install_linux.sh integrated
#   ./install_linux.sh integrated http://192.168.1.10:6000
integrated_install_runtime() {
  local video_base gateway_base
  if ! video_base="$(resolve_video_base_url "${1:-}")"; then
    print_error "云边一体部署必须指定中心汇聚面地址"
    print_info "示例: VIDEO_BASE_URL=http://192.168.1.10:6000 $0 integrated"
    print_info "  或: $0 integrated http://192.168.1.10:6000"
    print_info "可选: GATEWAY_URL MQTT_BROKER_URLS SRS_RTMP_BASE CONTROL_PLANE_URL"
    print_info "纯边缘形态（同机闭环）请用: bash ../.scripts/docker/install_linux.sh install（选 edge → standalone）"
    return 1
  fi
  gateway_base="$(resolve_gateway_url "${2:-}" || true)"
  if [[ -z "$gateway_base" ]]; then
    # 从汇聚面地址推断网关（同主机不同端口）
    local host
    host="$(echo "$video_base" | sed -E 's#^https?://([^:/]+).*#\1#')"
    gateway_base="http://${host}:48080"
    print_info "未指定 GATEWAY_URL，默认推断为 $gateway_base"
  fi

  local install_dir="${EASYAIOT_RUNTIME_INSTALL_DIR:-/opt/easyaiot/RUNTIME}"
  print_info "===== 云边一体部署（算力节点）====="
  print_info "本机仅部署边缘算力；汇聚面接入中心平台"
  print_info "汇聚面地址=$video_base"
  print_info "网关地址=$gateway_base"
  print_info "安装目录: $install_dir"

  if ! deploy_runtime_common "integrated"; then
    return 1
  fi

  install_node_env_files "integrated" "$install_dir" "$video_base" "$gateway_base" ""

  cat > "$ROOT/atomic.env" <<EOF
# Local pointer after integrated install
EASYAIOT_RUNTIME_DEPLOY_MODE=integrated
EASYAIOT_RUNTIME_INSTALL_DIR=$install_dir
VIDEO_BASE_URL=$video_base
GATEWAY_URL=$gateway_base
RUNTIME_BIN=$install_dir/bin/RUNTIME
EOF

  print_success "云边一体形态部署完成"
  print_info "二进制: $install_dir/bin/RUNTIME"
  print_info "正式任务由中心 VIDEO + SENTINEL/Agent 下发 ini 并拉起本二进制"
  print_info "也可通过 WEB「业务运行时分发 → RUNTIME(C++)」远程安装（需预打 OS 离线包）"
}

# 原子模式（云边一体别名，向后兼容）
# 用法:
#   VIDEO_BASE_URL=http://<中心VIDEO>:6000 ./install_linux.sh atomic
#   ./install_linux.sh atomic http://192.168.1.10:6000
atomic_install_runtime() {
  integrated_install_runtime "${1:-}"
}

main() {
  if [[ "${EASYAIOT_RUNTIME_SKIP:-0}" == "1" ]]; then
    print_warning "EASYAIOT_RUNTIME_SKIP=1，跳过 RUNTIME 安装"
    exit 0
  fi

  local cmd="${1:-}"
  if [[ -z "$cmd" ]]; then
    if [[ -t 0 ]]; then
      cmd="$(prompt_main_command)"
      [[ "$cmd" == "exit" ]] && exit 0
    else
      cmd="install"
    fi
  fi

  case "$cmd" in
    install|build|update|compile)
      if [[ "$cmd" == "compile" ]]; then
        BUILD_MODE=host
        export BUILD_MODE EASYAIOT_RUNTIME_BUILD_MODE=host
      fi
      if ! build_runtime; then
        print_error "RUNTIME 编译失败"
        dump_runtime_build_failure "$cmd"
        exit 1
      fi
      ;;
    start|status|restart)
      # 非常驻服务：start/restart 等同状态检查，失败不阻断上层继续部署
      status_runtime || true
      ;;
    stop|clean|logs)
      print_info "RUNTIME 无独立容器服务，${cmd} 为空操作"
      ;;
    atomic|node|runtime-only|atomic-install|integrated|edge-integrated|cloud-edge)
      shift || true
      integrated_install_runtime "${1:-}"
      ;;
    standalone|edge|pure-edge|edge-standalone|runtime-standalone)
      print_error "纯边缘形态请通过平台 install 规格菜单部署，本模块仅提供云边一体形态算力节点入口"
      print_info "纯边缘形态: bash ../.scripts/docker/install_linux.sh install（选 edge → standalone）"
      print_info "云边一体形态: $0 integrated <中心汇聚地址>（或平台 install → edge → integrated）"
      exit 1
      ;;
    help|-h|--help)
      sed -n '2,35p' "$0"
      echo ""
      echo "命令:"
      echo "  (无参数)               - 交互式菜单（TTY）"
      echo "  install|build|update   - 编译（TTY 下交互选择 conda / Docker）"
      echo "  compile                - 本机 conda 编译（等同 build + host，非交互）"
      echo "  start|status|restart   - 查看编译/节点安装状态"
      echo "  stop|clean|logs          - 空操作（无独立容器）"
      echo ""
      echo "云边一体形态（本机仅部署算力节点，汇聚面在中心）:"
      echo "  integrated [汇聚面URL]   - 安装并写入 node.env"
      echo "  atomic [汇聚面URL]       - integrated 别名（向后兼容）"
      echo ""
      echo "示例:"
      echo "  VIDEO_BASE_URL=http://192.168.1.10:6000 GATEWAY_URL=http://192.168.1.10:48080 \\"
      echo "    MQTT_BROKER_URLS=192.168.1.10:1883 $0 integrated"
      echo ""
      echo "纯边缘形态（汇聚面与算力同机）请用平台 install："
      echo "  bash ../.scripts/docker/install_linux.sh install   # 选 edge → standalone"
      echo ""
      echo "支持的操作系统见 RUNTIME/scripts/runtime_os_matrix.sh（不在矩阵内会拒绝部署）"
      ;;
    *)
      print_error "未知命令: $cmd"
      exit 1
      ;;
  esac
}

main "$@"
