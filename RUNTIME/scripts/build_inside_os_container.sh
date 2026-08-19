#!/usr/bin/env bash
# ============================================
# 容器内：安装编译依赖 → host 模式编译 RUNTIME → export_runtime_cpp.sh
# 由 export_runtime_os_container.sh 调用；勿在 Ubuntu 宿主机直接当入口。
# ============================================
set -euo pipefail

ROOT="/src/RUNTIME"
REPO="/src"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'
log() { echo -e "${BLUE}[RUNTIME/inner]${NC} $1"; }
ok() { echo -e "${GREEN}[RUNTIME/inner]${NC} $1"; }
fail() { echo -e "${RED}[RUNTIME/inner]${NC} $1" >&2; exit 1; }

OS_FAMILY="${RUNTIME_OS_FAMILY:?RUNTIME_OS_FAMILY required}"
ORT_ROOT="${ORT_ROOT:-/opt/ort}"

log "os_family=$OS_FAMILY ORT_ROOT=$ORT_ROOT"
if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  log "容器发行版: ${PRETTY_NAME:-${ID:-?} ${VERSION_ID:-}}"
fi

install_build_deps() {
  if command -v dnf >/dev/null 2>&1; then
    dnf install -y \
      gcc gcc-c++ make cmake pkgconfig \
      curl wget tar gzip bzip2 xz \
      glibc-devel libstdc++-devel \
      patch which findutils \
      ca-certificates patchelf \
      >/dev/null
    return 0
  fi
  if command -v yum >/dev/null 2>&1; then
    yum install -y \
      gcc gcc-c++ make cmake pkgconfig \
      curl wget tar gzip bzip2 xz \
      glibc-devel libstdc++-devel \
      patch which findutils \
      ca-certificates \
      >/dev/null
    return 0
  fi
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y --no-install-recommends \
      g++ gcc make cmake pkg-config \
      curl wget ca-certificates bzip2 \
      >/dev/null
    return 0
  fi
  fail "未识别的包管理器，无法安装编译依赖"
}

install_miniconda() {
  local prefix="${MINICONDA_PREFIX:-/opt/miniconda3}"
  if [[ -x "$prefix/bin/conda" ]]; then
    log "Miniconda 已存在: $prefix"
    return 0
  fi
  log "安装 Miniconda 到 $prefix ..."
  local arch="x86_64"
  case "$(uname -m)" in
    aarch64|arm64) arch="aarch64" ;;
  esac
  local installer="/tmp/miniconda.sh"
  curl -fsSL "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${arch}.sh" -o "$installer"
  if [[ -d "$prefix" ]]; then
    bash "$installer" -u -b -p "$prefix"
  else
    bash "$installer" -b -p "$prefix"
  fi
  rm -f "$installer"
  "$prefix/bin/conda" config --set auto_update_conda false
  ok "Miniconda 就绪: $prefix"
}

verify_ort() {
  if [[ -d "$ORT_ROOT/include" && -d "$ORT_ROOT/lib" ]]; then
    log "ORT SDK: $ORT_ROOT"
    return 0
  fi
  fail "ORT SDK 未挂载到 $ORT_ROOT（宿主机需先 download ORT 到 .deps/）"
}

clean_stale_build() {
  log "清理宿主机遗留 build 缓存（路径/bind 与容器内 /src 不一致会导致 CMake 失败）..."
  rm -rf "$ROOT/build" "$ROOT/deploy.env"
  mkdir -p "$ROOT/build"
}

install_build_deps
install_miniconda
verify_ort
clean_stale_build

export PATH="/opt/miniconda3/bin:$PATH"
# shellcheck disable=SC1091
source /opt/miniconda3/etc/profile.d/conda.sh

# 新 Miniconda 非交互环境需接受 ToS；并优先 conda-forge 避免 defaults 通道
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main >/dev/null 2>&1 || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r >/dev/null 2>&1 || true
conda config --set channel_priority strict >/dev/null 2>&1 || true
conda config --add channels conda-forge >/dev/null 2>&1 || true
conda config --set channels conda-forge >/dev/null 2>&1 || true

export EASYAIOT_RUNTIME_BUILD_MODE=host
export EASYAIOT_AUTO_INSTALL_DEPS=0
export ORT_ROOT
export RUNTIME_OS_FAMILY="$OS_FAMILY"
export RUNTIME_AUTO_INSTALL=1
export TMPDIR="${TMPDIR:-/tmp}"

log "执行 install_linux.sh install ..."
bash "$ROOT/install_linux.sh" install

# 导出前必须带上 conda/ORT 路径，否则 collect_libs 会漏 blas 且 smoke 失败
if [[ -f "$ROOT/deploy.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ROOT/deploy.env"
  set +a
fi
export RUNTIME_ORT_LIB_HOST="${RUNTIME_ORT_LIB_HOST:-${ORT_ROOT}/lib}"
export RUNTIME_CONDA_LIB_HOST="${RUNTIME_CONDA_LIB_HOST:-${CONDA_PREFIX}/lib}"

log "执行 export_runtime_cpp.sh ..."
bash "$ROOT/export_runtime_cpp.sh"

ok "容器内构建与导出完成 (os_family=$OS_FAMILY)"
