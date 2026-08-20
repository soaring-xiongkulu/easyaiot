#!/usr/bin/env bash
# ============================================
# RUNTIME 离线包构建/分发前预检（减少「编完才发现缺包」）
#
# 用法:
#   bash RUNTIME/scripts/preflight_runtime_bundle.sh
#       # 预检 COMPILE pack_all_linux 对应的 RUNTIME 覆盖（矩阵+ORT+可选 tarball）
#   bash RUNTIME/scripts/preflight_runtime_bundle.sh openeuler24 x86_64
#   bash RUNTIME/scripts/preflight_runtime_bundle.sh --node 5   # 需 Gateway
#   bash RUNTIME/scripts/preflight_runtime_bundle.sh --compile-coverage
# ============================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT/scripts/os_family.sh"
# shellcheck disable=SC1091
source "$ROOT/scripts/runtime_os_matrix.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
ok() { echo -e "${GREEN}[preflight]${NC} $*"; }
warn() { echo -e "${YELLOW}[preflight]${NC} $*"; }
fail() { echo -e "${RED}[preflight]${NC} $*" >&2; exit 1; }

ORT_VER="${ORT_VERSION:-1.23.2}"
ENSURE_ORT="$ROOT/scripts/ensure_ort_deps.sh"

check_common() {
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    fail "需要可用 Docker（容器内按 OS 编译 RUNTIME）"
  fi
  ok "Docker 可用"

  if [[ -x "$ENSURE_ORT" ]]; then
    bash "$ENSURE_ORT" x86_64 arm64 || warn "部分 ORT SDK 未就绪，见上方日志"
  fi

  if [[ -f "$ROOT/build/CMakeCache.txt" ]]; then
    local cached
    cached="$(grep -m1 '^CMAKE_HOME_DIRECTORY:' "$ROOT/build/CMakeCache.txt" 2>/dev/null | sed 's/.*=//' || true)"
    if [[ -n "$cached" && "$cached" != "$ROOT" ]]; then
      warn "检测到 build/ 缓存路径与当前源码不一致（$cached），容器编译前会自动清理"
    fi
  fi
}

check_ort_for_arch() {
  local arch="$1"
  local ort_dir
  ort_dir="$(runtime_matrix_ort_deps_dir "$REPO" "$arch")"
  if [[ -d "$ort_dir/include" && -d "$ort_dir/lib" ]]; then
    ok "ORT SDK (${arch}): $ort_dir"
    return 0
  fi
  warn "缺少 ORT SDK (${arch}): $ort_dir"
  return 1
}

check_ort_for_keys() {
  local keys="$1" arch rc=0 seen=""
  for item in $keys; do
    arch="${item##*:}"
    case " $seen " in
      *" $arch "*) continue ;;
    esac
    seen+="$arch "
    check_ort_for_arch "$arch" || rc=1
  done
  return "$rc"
}

check_tarball() {
  local os_family="$1" arch="$2"
  local tar="$ROOT/.bundle-runtime/${os_family}/${arch}/easyaiot-runtime-${os_family}-${arch}.tar.gz"
  local img
  img="$(runtime_matrix_image "$os_family" "$arch")"

  echo ""
  echo "── ${os_family}/${arch} ──"
  if [[ -z "$img" ]]; then
    if [[ "$os_family" == kylin* ]]; then
      warn "麒麟 RUNTIME 需单独配置 Docker 镜像，例如:"
      warn "  export RUNTIME_KYLIN10_ARM64_IMAGE=<kylin-v10-sp3-arm64-image>"
      warn "  bash RUNTIME/scripts/export_runtime_os_container.sh ${os_family}"
      warn "或在实机麒麟上: bash RUNTIME/export_runtime_cpp.sh"
    else
      warn "矩阵未登记 Docker 镜像，需设置 RUNTIME_OS_CONTAINER_IMAGE"
    fi
  else
    ok "构建镜像: $img (platform=$(runtime_matrix_docker_platform "$arch"))"
  fi

  check_ort_for_arch "$arch" || true

  if [[ -f "$tar" ]]; then
    ok "已有离线包: $tar ($(du -h "$tar" | awk '{print $1}'))"
    if tar -tzf "$tar" 2>/dev/null | grep -q 'libcblas\.so'; then
      ok "包内含 libcblas（blas 依赖已收集）"
    else
      warn "包内未见 libcblas，节点上可能 SMOKE_FAIL"
    fi
    return 0
  fi
  warn "缺少离线包: $tar"
  echo "  构建: RUNTIME_OS_FAMILY=${os_family} RUNTIME_ARCH=${arch} bash RUNTIME/scripts/export_runtime_os_container.sh ${os_family}"
  return 1
}

check_compile_coverage() {
  local keys rc=0 item os arch
  keys="$(runtime_matrix_compile_coverage_keys)"
  echo ""
  echo "COMPILE pack_all_linux 对应 RUNTIME 覆盖预检:"
  check_ort_for_keys "$keys" || rc=1
  for item in $keys; do
    os="${item%%:*}"
    arch="${item##*:}"
    check_tarball "$os" "$arch" || rc=1
  done
  return "$rc"
}

check_node() {
  local node_id="$1"
  local gw="${EASYAIOT_GATEWAY:-http://127.0.0.1:48080}"
  local resp os arch ready
  resp="$(curl -sf -X POST "${gw}/admin-api/node/workload-bundle/runtime-cpp/check-ssh?nodeId=${node_id}" 2>/dev/null || true)"
  if [[ -z "$resp" ]]; then
    fail "无法访问 Gateway ${gw} 或节点 ${node_id} SSH 检测失败"
  fi
  os="$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('osFamily',''))" 2>/dev/null || true)"
  arch="$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('arch','x86_64'))" 2>/dev/null || true)"
  ready="$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('runtimeReady',False))" 2>/dev/null || true)"
  echo ""
  echo "── 节点 ${node_id} ──"
  ok "远程 os_family=${os} arch=${arch} runtimeReady=${ready}"
  if [[ -n "$os" ]]; then
    check_tarball "$os" "${arch:-x86_64}" || return 1
  fi
}

main() {
  local rc=0
  check_common

  if [[ "${1:-}" == "--node" && -n "${2:-}" ]]; then
    check_node "$2" || rc=1
    exit "$rc"
  fi

  if [[ "${1:-}" == "--compile-coverage" ]]; then
    check_compile_coverage || rc=1
    exit "$rc"
  fi

  if [[ -n "${1:-}" ]]; then
    check_tarball "$1" "${2:-x86_64}" || rc=1
    exit "$rc"
  fi

  check_compile_coverage || rc=1
  exit "$rc"
}

main "$@"
