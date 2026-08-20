#!/usr/bin/env bash
# ============================================
# 验证 RUNTIME 矩阵与 COMPILE pack_all_linux 覆盖一致（不启动容器构建）
#
# 用法:
#   bash RUNTIME/scripts/verify_runtime_compile_matrix.sh
#   bash RUNTIME/scripts/verify_runtime_compile_matrix.sh --check-tarballs
# ============================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT/scripts/os_family.sh"
# shellcheck disable=SC1091
source "$ROOT/scripts/runtime_os_matrix.sh"

CHECK_TARBALLS=0
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
failures=0
warnings=0

ok() { echo -e "${GREEN}[verify]${NC} $*"; }
warn() { echo -e "${YELLOW}[verify]${NC} $*"; warnings=$((warnings + 1)); }
bad() { echo -e "${RED}[verify]${NC} $*"; failures=$((failures + 1)); }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-tarballs) CHECK_TARBALLS=1; shift ;;
    -h|--help)
      echo "用法: $0 [--check-tarballs]"
      exit 0
      ;;
    *) bad "未知参数: $1"; exit 1 ;;
  esac
done

echo "=== COMPILE pack_all_linux → RUNTIME 映射 ==="
coverage="$(runtime_matrix_compile_coverage_keys)"
if [[ -z "$coverage" ]]; then
  bad "compile coverage 为空"
else
  ok "全覆盖 $(echo "$coverage" | wc -w) 个 os_family:arch:"
  for item in $coverage; do
    echo "  - $item"
  done
fi

echo ""
echo "=== 各 COMPILE 目标映射 ==="
for target in "${RUNTIME_COMPILE_PACK_ALL_ORDER[@]}"; do
  keys="$(runtime_matrix_for_compile_target "$target")"
  if [[ -z "$keys" ]]; then
    bad "COMPILE 目标无 RUNTIME 映射: $target"
    continue
  fi
  ok "$target → $keys"
done

if [[ -z "${RUNTIME_COMPILE_TARGET_MAP[all-linux]:-}" && -n "$coverage" ]]; then
  ok "all-linux → $(echo "$coverage" | wc -w) 项（经 runtime_matrix_compile_coverage_keys 展开）"
fi

echo ""
echo "=== 矩阵镜像 / ORT / tarball（COMPILE 覆盖范围）==="
for item in $coverage; do
  os="${item%%:*}"
  arch="${item##*:}"
  img="$(runtime_matrix_image "$os" "$arch")"
  ort_dir="$(runtime_matrix_ort_deps_dir "$REPO" "$arch")"

  echo ""
  echo "── ${os}/${arch} ──"
  if [[ -z "$img" ]]; then
    if [[ "$os" == kylin* ]]; then
      warn "麒麟需配置 RUNTIME_${os^^}_ARM64_IMAGE 或实机编译"
    else
      bad "缺少 Docker 镜像登记"
    fi
  else
    ok "镜像: $img (platform=$(runtime_matrix_docker_platform "$arch"))"
  fi

  if [[ -d "$ort_dir/include" && -d "$ort_dir/lib" ]]; then
    ok "ORT SDK: $ort_dir"
  else
    warn "缺少 ORT SDK: $ort_dir"
  fi

  if [[ "$CHECK_TARBALLS" -eq 1 ]]; then
    tar="$ROOT/.bundle-runtime/${os}/${arch}/easyaiot-runtime-${os}-${arch}.tar.gz"
    if [[ -f "$tar" ]]; then
      ok "离线包: $tar"
    else
      warn "缺少离线包: $tar"
    fi
  fi
done

echo ""
echo "=== os_family 映射抽样（部署按节点 OS 选包）==="
assert_os_family() {
  local id="$1" like="$2" ver="$3" expect="$4"
  local got
  got="$(runtime_os_family_from "$id" "$like" "$ver")"
  if [[ "$got" == "$expect" ]]; then
    ok "${id} ${ver} → ${got}"
  else
    bad "${id} ${ver} 期望 ${expect}，实际 ${got}"
  fi
}

assert_os_family ubuntu "" "24.04" "ubuntu24"
assert_os_family ubuntu "" "26.04" "ubuntu26"
assert_os_family openeuler "" "24.03" "openeuler24"
assert_os_family openeuler "" "22.03" "openeuler22"
assert_os_family rocky "" "9.4" "el9"
assert_os_family centos "" "7" "el7"
assert_os_family kylin "" "10" "kylin10"

echo ""
echo "=== Java 侧 osFamily 对照（bash vs RuntimeCppDeployUtil 规则应一致）==="
# 仅文档性提示；Java 单测不在此脚本范围
ok "节点 Ubuntu 24 → ubuntu24；openEuler 24.03 → openeuler24；RHEL9 → el9"

echo ""
if [[ "$failures" -gt 0 ]]; then
  bad "失败 ${failures} 项，警告 ${warnings} 项"
  exit 1
fi
if [[ "$warnings" -gt 0 ]]; then
  warn "通过（含 ${warnings} 项警告，多为麒麟镜像 / 未构建 tarball / 缺 ORT）"
  exit 0
fi
ok "全部通过"
exit 0
