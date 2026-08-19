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
#   EASYAIOT_RUNTIME_SKIP=1              # 跳过（供上层脚本探测）
#   EASYAIOT_RUNTIME_REQUIRED=1          # 失败时以非 0 退出（由调用方决定）
#   ORT_ROOT                             # ONNX Runtime C++ SDK 根目录
#   EASYAIOT_RUNTIME_BUILD_MODE=docker|host
#       默认 docker：在 VIDEO 同源容器内用系统 g++ 编译（推荐，免 sysroot 降级）
#       host：本机 conda 编译（新 glibc 主机上产物可能无法进 VIDEO 容器）
#   EASYAIOT_RUNTIME_BUILD_IMAGE         # 覆盖构建镜像（默认优先 video-service:latest）
#   VIDEO_BASE_URL / EASYAIOT_VIDEO_BASE_URL
#       原子模式必填：汇聚面 VIDEO 根地址，如 http://192.168.1.10:6000
#   EASYAIOT_RUNTIME_INSTALL_DIR         # 原子模式安装目录（默认 /opt/easyaiot/RUNTIME）
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
REPO="$(cd "$ROOT/.." && pwd)"
ORT_VERSION="${ORT_VERSION:-1.23.2}"
CONDA_ENV_NAME="${EASYAIOT_RUNTIME_CONDA_ENV:-easyaiot-runtime}"
BUILD_MODE="${EASYAIOT_RUNTIME_BUILD_MODE:-docker}"

# shellcheck disable=SC1091
source "$ROOT/scripts/version_meta.sh"
# shellcheck disable=SC1091
source "$ROOT/scripts/os_family.sh"

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

# 宿主机 conda 仅提供运行/链接依赖（OpenCV5、glog…），不强制使用其 cxx-compiler sysroot
activate_runtime_env() {
  local conda_sh
  if ! conda_sh="$(find_conda_sh)"; then
    print_error "未找到 conda，请先安装 Miniconda/Anaconda"
    return 1
  fi
  # shellcheck disable=SC1090
  source "$conda_sh"
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
  # conda 的 libstdc++ 常在 gcc 子目录；挂载到 VIDEO 容器时需出现在 $CONDA_PREFIX/lib（相对链接）
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

build_runtime_on_host() {
  print_warning "EASYAIOT_RUNTIME_BUILD_MODE=host：本机 conda 编译；新 glibc 主机产物可能无法在 VIDEO(22.04) 容器内运行"
  export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${ORT_ROOT}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  local cuda_libs
  cuda_libs="$(cuda_lib_paths)"
  if [[ -n "$cuda_libs" ]]; then
    export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:$cuda_libs"
  fi
  export PKG_CONFIG_PATH="${CONDA_PREFIX}/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
  export CMAKE_PREFIX_PATH="${CONDA_PREFIX}${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"

  local build_dir="$ROOT/build"
  mkdir -p "$build_dir"
  export TMPDIR="${TMPDIR:-$REPO/.tmp}"
  mkdir -p "$TMPDIR"

  runtime_resolve_version_meta "$ROOT" "$REPO"
  print_info "cmake 配置（host, version=${RUNTIME_VERSION}）..."
  if ! cmake "$ROOT" \
    -B "$build_dir" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
    -DOpenCV_DIR="$CONDA_PREFIX/lib/cmake/opencv5" \
    -DONNXRUNTIME_ROOT="$ORT_ROOT" \
    -DRUNTIME_VERSION_STR="${RUNTIME_VERSION}" \
    -DCMAKE_CXX_FLAGS="-I$CONDA_PREFIX/include/opencv5"; then
    print_error "cmake 配置失败"
    return 1
  fi

  print_info "编译中..."
  if ! cmake --build "$build_dir" -j"$(nproc 2>/dev/null || echo 4)"; then
    print_error "cmake 编译失败"
    return 1
  fi

  if [[ ! -x "$build_dir/RUNTIME" ]]; then
    print_error "编译完成但未找到可执行文件: $build_dir/RUNTIME"
    return 1
  fi
}

build_runtime() {
  # 部署前检查/自动补齐（仅 RUNTIME；失败给出详细诊断）
  if ! prepare_runtime_build_env; then
    return 1
  fi

  activate_runtime_env
  ensure_ort_sdk
  # Prefer GPU at runtime by default
  export RUNTIME_PREFER_GPU="${RUNTIME_PREFER_GPU:-true}"
  export USE_GPU="${USE_GPU:-true}"

  case "$BUILD_MODE" in
    docker|container)
      BUILD_MODE=docker
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

resolve_video_base_url() {
  local raw="${VIDEO_BASE_URL:-${EASYAIOT_VIDEO_BASE_URL:-${1:-}}}"
  if [[ -z "$raw" ]]; then
    return 1
  fi
  normalize_video_base_url "$raw"
}

write_atomic_node_env() {
  local install_dir="$1"
  local video_base="$2"
  local node_env="$install_dir/node.env"
  local hb_realtime="${video_base}/video/algorithm/heartbeat/realtime"
  local hb_patrol="${video_base}/video/algorithm/heartbeat/patrol"
  # 可选媒体面：手工调试推检测流时用；正式任务由 VIDEO 下发 ini 自带 ai_rtmp
  local srs_base="${SRS_RTMP_BASE:-${EASYAIOT_SRS_RTMP_BASE:-}}"
  local ai_rtmp="${AI_RTMP_URL:-${EASYAIOT_AI_RTMP_URL:-}}"
  if [[ -z "$ai_rtmp" && -n "$srs_base" ]]; then
    ai_rtmp="${srs_base%/}/ai/atomic_demo"
  fi
  local enable_rtmp="false"
  if [[ -n "$ai_rtmp" ]]; then
    enable_rtmp="true"
  fi

  cat > "$node_env" <<EOF
# Auto-generated by RUNTIME atomic mode — compute node aggregation endpoints
# 本节点不部署 VIDEO；心跳回中心 HTTP；告警经 MQTT → iot-sink。
VIDEO_BASE_URL=${video_base}
ALGO_BUS_TRANSPORT=mqtt
MQTT_BROKER_URLS=${MQTT_BROKER_URLS:-}
MQTT_ALGO_TENANT=${MQTT_ALGO_TENANT:-default}
MQTT_ALGO_USERNAME=${MQTT_ALGO_USERNAME:-}
MQTT_ALGO_PASSWORD=${MQTT_ALGO_PASSWORD:-}
MQTT_ALGO_CLIENT_ID=${MQTT_ALGO_CLIENT_ID:-algo-runtime-atomic}
ALERT_IMAGES_DIR=${ALERT_IMAGES_DIR:-${install_dir}/cache/alerts}
HEARTBEAT_URL=${hb_realtime}
HEARTBEAT_URL_PATROL=${hb_patrol}
RUNTIME_BIN=${install_dir}/bin/RUNTIME
RUNTIME_PREFER_GPU=true
USE_GPU=true
# 可选：手工调试推带框检测流（非原子安装必填）
SRS_RTMP_BASE=${srs_base}
AI_RTMP_URL=${ai_rtmp}
EOF

  # 覆盖/增强 env.sh，供 Agent 或手工 source
  cat > "$install_dir/env.sh" <<EOF
#!/usr/bin/env bash
# Sourced on compute nodes (atomic / iot-node install)
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
export VIDEO_BASE_URL="\${VIDEO_BASE_URL:-}"
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
# 原子节点示例任务配置（手工调试用）
# 正式任务由 VIDEO/Agent 生成 task_*.ini（realtime 默认 enable_rtmp + 独立 ai/ 地址）
# 手工推检测流：安装前设置 SRS_RTMP_BASE=rtmp://<SRS>:1935 或 AI_RTMP_URL=rtmp://…/ai/<id>

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
mqtt_broker_urls=${MQTT_BROKER_URLS:-}
mqtt_tenant=${MQTT_ALGO_TENANT:-default}
headless=true

[mqtt]
broker_urls=${MQTT_BROKER_URLS:-}
tenant=${MQTT_ALGO_TENANT:-default}
transport=mqtt

[features]
enable_rtmp=${enable_rtmp}
enable_draw=true
enable_alarm=true
EOF

  print_success "已写入汇聚面配置: $node_env"
  print_info "告警: MQTT → iot-sink (MQTT_BROKER_URLS=\${MQTT_BROKER_URLS:-unset})"
  print_info "心跳: $hb_realtime"
  if [[ -n "$ai_rtmp" ]]; then
    print_info "可选检测推流 AI_RTMP_URL=$ai_rtmp (enable_rtmp=$enable_rtmp)"
  else
    print_info "未设置 SRS_RTMP_BASE/AI_RTMP_URL：示例 ini 不推流；正式任务仍由 VIDEO 下发 ai_rtmp"
  fi
}

# 原子模式：只部署 RUNTIME 到本机计算节点目录（不装 VIDEO/WEB 等）
# 用法:
#   VIDEO_BASE_URL=http://<中心VIDEO>:6000 ./install_linux.sh atomic
#   ./install_linux.sh atomic http://192.168.1.10:6000
atomic_install_runtime() {
  local video_base
  if ! video_base="$(resolve_video_base_url "${1:-}")"; then
    print_error "原子模式必须指定汇聚面 VIDEO 地址"
    print_info "示例: VIDEO_BASE_URL=http://192.168.1.10:6000 $0 atomic"
    print_info "  或: $0 atomic http://192.168.1.10:6000"
    print_info "结果上报: alert → MQTT(iot-sink) ；heartbeat → …/video/algorithm/heartbeat/*"
    return 1
  fi

  local install_dir="${EASYAIOT_RUNTIME_INSTALL_DIR:-/opt/easyaiot/RUNTIME}"
  print_info "===== RUNTIME 原子模式 ====="
  print_info "只安装高性能执行器，不部署 VIDEO/WEB/DEVICE 等业务面"
  print_info "汇聚面 VIDEO_BASE_URL=$video_base"
  print_info "安装目录: $install_dir"

  build_runtime

  local export_sh="$ROOT/export_runtime_cpp.sh"
  if [[ ! -f "$export_sh" ]]; then
    print_error "缺少 $export_sh"
    return 1
  fi
  print_info "导出离线包..."
  # 已编译则跳过 export 内二次 install
  RUNTIME_AUTO_INSTALL=0 bash "$export_sh"

  local bundle_arch bundle_os
  bundle_arch="$(runtime_arch_key)"
  bundle_os="$(runtime_detect_os_family)"
  local tar_path="$ROOT/.bundle-runtime/${bundle_os}/${bundle_arch}/easyaiot-runtime-${bundle_os}-${bundle_arch}.tar.gz"
  if [[ ! -f "$tar_path" ]]; then
    tar_path="$ROOT/.bundle-runtime/${bundle_arch}/easyaiot-runtime-${bundle_arch}.tar.gz"
  fi
  if [[ ! -f "$tar_path" ]]; then
    tar_path="$(find "$ROOT/.bundle-runtime" -name "easyaiot-runtime-${bundle_os}-${bundle_arch}.tar.gz" 2>/dev/null | head -1 || true)"
  fi
  if [[ -z "${tar_path:-}" || ! -f "$tar_path" ]]; then
    print_error "未找到导出包（export_runtime_cpp.sh 未产出 tar.gz）"
    return 1
  fi

  local install_sh="$ROOT/install_runtime_cpp.sh"
  if [[ ! -f "$install_sh" ]]; then
    print_error "缺少 $install_sh"
    return 1
  fi

  print_info "安装离线包到 $install_dir ..."
  bash "$install_sh" "$install_dir" "$tar_path"

  if [[ -w "$install_dir" ]]; then
    write_atomic_node_env "$install_dir" "$video_base"
  else
    local tmp_env
    tmp_env="$(mktemp -d)"
    write_atomic_node_env "$tmp_env" "$video_base"
    sudo cp -f "$tmp_env/node.env" "$install_dir/node.env"
    sudo cp -f "$tmp_env/env.sh" "$install_dir/env.sh"
    sudo mkdir -p "$install_dir/config"
    sudo cp -f "$tmp_env/config/atomic.example.ini" "$install_dir/config/atomic.example.ini"
    sudo chmod +x "$install_dir/env.sh"
    rm -rf "$tmp_env"
  fi

  cat > "$ROOT/atomic.env" <<EOF
# Local pointer after atomic install
EASYAIOT_RUNTIME_INSTALL_DIR=$install_dir
VIDEO_BASE_URL=$video_base
RUNTIME_BIN=$install_dir/bin/RUNTIME
EOF

  print_success "原子模式部署完成"
  print_info "二进制: $install_dir/bin/RUNTIME"
  print_info "汇聚: 告警/心跳 → $video_base （本节点不落库）"
  print_info "调试: source $install_dir/env.sh && \$RUNTIME_BIN $install_dir/config/atomic.example.ini"
  print_info "正式任务仍由中心 VIDEO + Agent 下发 ini 并拉起本二进制"
}

main() {
  if [[ "${EASYAIOT_RUNTIME_SKIP:-0}" == "1" ]]; then
    print_warning "EASYAIOT_RUNTIME_SKIP=1，跳过 RUNTIME 安装"
    exit 0
  fi

  local cmd="${1:-install}"
  case "$cmd" in
    install|build|update)
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
    atomic|node|runtime-only|atomic-install)
      shift || true
      atomic_install_runtime "${1:-}"
      ;;
    help|-h|--help)
      sed -n '2,30p' "$0"
      echo ""
      echo "命令:"
      echo "  install|build|update - 编译 RUNTIME（默认 docker 同源容器）"
      echo "  start|status|restart  - 查看编译/原子安装状态"
      echo "  stop|clean|logs       - 空操作（无独立容器）"
      echo "  atomic [VIDEO_BASE_URL] - 原子模式：只装 RUNTIME 到计算节点目录"
      echo ""
      echo "原子模式示例:"
      echo "  VIDEO_BASE_URL=http://192.168.1.10:6000 $0 atomic"
      ;;
    *)
      print_error "未知命令: $cmd"
      exit 1
      ;;
  esac
}

main "$@"
