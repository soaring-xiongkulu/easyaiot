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

setup_el_repos() {
  local setup="${REPO}/COMPILE/platforms/centos/setup_cn_mirrors.sh"
  [[ -f "$setup" ]] || return 0
  local el=""
  case "$OS_FAMILY" in
    el7) el=7 ;;
    el8) el=8 ;;
    el9) el=9 ;;
    *) return 0 ;;
  esac
  log "配置 EL${el} 国内 yum/dnf 源（与 COMPILE 一致）..."
  EL_RELEASE="$el" COMPILE_CN_MIRROR="${COMPILE_CN_MIRROR:-huawei}" bash "$setup"
}

pkg_install() {
  local pm="$1"
  shift
  local pkgs=("$@") extra=()
  command -v curl >/dev/null 2>&1 || extra+=(curl)
  command -v wget >/dev/null 2>&1 || extra+=(wget)
  "$pm" install -y "${pkgs[@]}" "${extra[@]}"
  "$pm" install -y patchelf >/dev/null 2>&1 || true
}

install_build_deps() {
  setup_el_repos
  if command -v dnf >/dev/null 2>&1; then
    pkg_install dnf \
      gcc gcc-c++ make cmake pkgconfig \
      tar gzip bzip2 xz \
      glibc-devel libstdc++-devel \
      patch which findutils \
      ca-certificates
    return 0
  fi
  if command -v yum >/dev/null 2>&1; then
    pkg_install yum \
      gcc gcc-c++ make cmake pkgconfig \
      tar gzip bzip2 xz \
      glibc-devel libstdc++-devel \
      patch which findutils \
      ca-certificates
    yum install -y cmake3 >/dev/null 2>&1 || true
    if [[ "$OS_FAMILY" == "el7" ]]; then
      log "安装 devtoolset-9（EL7 系统 gcc 4.8 不支持 C++17）..."
      yum install -y devtoolset-9-gcc devtoolset-9-gcc-c++ devtoolset-9-make >/dev/null 2>&1 || \
        yum install -y devtoolset-8-gcc devtoolset-8-gcc-c++ devtoolset-8-make
    fi
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
  # CentOS 7 / glibc 2.17 无法使用最新 Miniconda（要求 GLIBC>=2.28；aarch64 安装器要求 GLIBC>=2.25）
  local url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${arch}.sh"
  if [[ "$OS_FAMILY" == "el7" ]]; then
    if [[ "$arch" == "aarch64" ]]; then
      install_micromamba_bootstrap
      return 0
    fi
    url="https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh"
    log "EL7 使用兼容 glibc 2.17 的 Miniconda: $url"
  fi
  local installer="/tmp/miniconda.sh"
  curl -fsSL "$url" -o "$installer"
  if [[ -d "$prefix" ]]; then
    bash "$installer" -u -b -p "$prefix"
  else
    bash "$installer" -b -p "$prefix"
  fi
  rm -f "$installer"
  "$prefix/bin/conda" config --set auto_update_conda false
  ok "Miniconda 就绪: $prefix"
}

install_micromamba_bootstrap() {
  local prefix="${MINICONDA_PREFIX:-/opt/miniconda3}"
  local mm_dir="/opt/micromamba"
  local mm="$mm_dir/bin/micromamba"
  if [[ -x "$mm" ]]; then
    log "Micromamba 已存在: $mm"
    write_micromamba_conda_sh "$prefix"
    return 0
  fi
  log "EL7 aarch64：安装 micromamba（Miniconda 安装器不兼容 glibc 2.17）..."
  mkdir -p "$mm_dir"
  curl -fsSL "https://micro.mamba.pm/api/micromamba/linux-aarch64/latest" -o /tmp/micromamba.tar.bz2
  tar -xjf /tmp/micromamba.tar.bz2 -C "$mm_dir"
  rm -f /tmp/micromamba.tar.bz2
  [[ -x "$mm" ]] || fail "micromamba 安装失败"
  write_micromamba_conda_sh "$prefix"
  ok "Micromamba 就绪: $mm"
}

write_micromamba_conda_sh() {
  local prefix="${1:-/opt/miniconda3}"
  mkdir -p "$prefix/etc/profile.d"
  cat > "$prefix/etc/profile.d/conda.sh" <<'EOF'
# EL7 aarch64：micromamba 兼容层，供 install_linux.sh 使用
export MAMBA_EXE="${MAMBA_EXE:-/opt/micromamba/bin/micromamba}"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-/opt/micromamba-root}"
EOF
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

enable_el7_devtoolset() {
  [[ "$OS_FAMILY" == "el7" ]] || return 0
  local dts
  for dts in /opt/rh/devtoolset-9/enable /opt/rh/devtoolset-8/enable; do
    if [[ -f "$dts" ]]; then
      # devtoolset enable 脚本在 set -u 下可能引用未定义的 MANPATH
      set +u
      # shellcheck disable=SC1090
      source "$dts"
      set -u
      log "已启用 $(basename "$(dirname "$dts")")：$(g++ --version | head -1)"
      return 0
    fi
  done
  fail "EL7 需要 devtoolset-8/9 以支持 C++17"
}

install_build_deps
install_miniconda
verify_ort
clean_stale_build
enable_el7_devtoolset

export PATH="/opt/miniconda3/bin:$PATH"
if [[ -f /opt/miniconda3/etc/profile.d/conda.sh ]]; then
  # shellcheck disable=SC1091
  source /opt/miniconda3/etc/profile.d/conda.sh
fi

if command -v conda >/dev/null 2>&1; then
  # 新 Miniconda 非交互环境需接受 ToS；并优先 conda-forge 避免 defaults 通道
  conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main >/dev/null 2>&1 || true
  conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r >/dev/null 2>&1 || true
  if [[ "$OS_FAMILY" == "el7" ]]; then
    conda config --set channel_priority flexible >/dev/null 2>&1 || true
  else
    conda config --set channel_priority strict >/dev/null 2>&1 || true
  fi
  conda config --add channels conda-forge >/dev/null 2>&1 || true
  conda config --set channels conda-forge >/dev/null 2>&1 || true
fi

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
