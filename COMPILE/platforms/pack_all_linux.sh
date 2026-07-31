#!/usr/bin/env bash
# 依次打包 Ubuntu(x86/arm/kylin) deb + CentOS rpm
#
# 用法:
#   bash COMPILE/platforms/pack_all_linux.sh
#   bash COMPILE/install_linux.sh pack-all
#   bash COMPILE/build.sh all-linux
#
# 日志写到 COMPILE/work/logs/（work/ 为构建缓存，gitignore）
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
cd "$ROOT"

LOG_DIR="${COMPILE_ROOT}/work/logs"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/pack_all_$(date +%Y%m%d_%H%M%S).log"
echo "$LOG" > "${LOG_DIR}/pack_all_latest.path"

exec > >(tee -a "$LOG") 2>&1

fail=0
run() {
  local rc
  echo ""
  echo "================================================================"
  echo "[$(date -Is)] START: $*"
  echo "================================================================"
  "$@"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[$(date -Is)] OK: $*"
  else
    echo "[$(date -Is)] FAIL(${rc}): $*"
    fail=1
  fi
  return "$rc"
}

echo "[$(date -Is)] pack_all_linux start root=${ROOT}"
echo "panel-version-before=$(cat COMPILE/.panel-version 2>/dev/null || echo none)"

# 确保前端可写（避免 root 残留导致 vite 失败）
if [ -d PANEL/ui/dist ] && [ ! -w PANEL/ui/dist ]; then
  echo "PANEL/ui/dist 不可写，尝试 docker chown"
  docker run --rm -v "${ROOT}/PANEL/ui:/ui" alpine chown -R "$(id -u):$(id -g)" /ui/dist || true
fi

run bash COMPILE/build.sh ubuntu-x86 --deb || true
run bash COMPILE/build.sh ubuntu-arm --deb || true
run bash COMPILE/build.sh ubuntu-kylin --deb || true
run bash COMPILE/build.sh centos || true

echo ""
echo "================================================================"
echo "[$(date -Is)] ALL DONE fail=${fail}"
echo "=== artifacts (latest) ==="
ls -lt COMPILE/dist/ubuntu/*.deb 2>/dev/null | head -3
ls -lt COMPILE/dist/ubuntu-arm/*.deb 2>/dev/null | head -3
ls -lt COMPILE/dist/ubuntu-kylin/*.deb 2>/dev/null | head -3
ls -lt COMPILE/dist/centos/*.rpm 2>/dev/null | head -3
ls -lh COMPILE/dist/ubuntu/easyaiot-panel COMPILE/dist/ubuntu-arm/easyaiot-panel \
  COMPILE/dist/ubuntu-kylin/easyaiot-panel COMPILE/dist/centos/easyaiot-panel 2>/dev/null || true
echo "panel-version-after=$(cat COMPILE/.panel-version 2>/dev/null || echo none)"
echo "log=${LOG}"
exit "$fail"
