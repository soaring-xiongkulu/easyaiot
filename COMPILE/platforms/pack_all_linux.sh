#!/usr/bin/env bash
# 依次打包全部 Linux 安装包：
#   Ubuntu(x86/arm/kylin) deb
#   CentOS/RHEL el7/el8/el9 x86 + ARM rpm
#   openEuler rpm
#
# 用法:
#   bash COMPILE/platforms/pack_all_linux.sh
#   bash COMPILE/install_linux.sh pack-all
#   bash COMPILE/build.sh all-linux
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

if [ -d PANEL/ui/dist ] && [ ! -w PANEL/ui/dist ]; then
  echo "PANEL/ui/dist 不可写，尝试 docker chown"
  docker run --rm -v "${ROOT}/PANEL/ui:/ui" alpine chown -R "$(id -u):$(id -g)" /ui/dist || true
fi

# Ubuntu deb
run bash COMPILE/build.sh ubuntu-x86 --deb || true
run bash COMPILE/build.sh ubuntu-arm --deb || true
run bash COMPILE/build.sh ubuntu-kylin --deb || true

# CentOS/RHEL x86：el7 / el8 / el9
run bash COMPILE/build.sh centos-el7 || true
run bash COMPILE/build.sh centos-el8 || true
run bash COMPILE/build.sh centos-el9 || true

# CentOS/RHEL ARM：el7 / el8 / el9（Docker linux/arm64 交叉）
run bash COMPILE/build.sh centos-arm-el7 || true
run bash COMPILE/build.sh centos-arm-el8 || true
run bash COMPILE/build.sh centos-arm-el9 || true

# openEuler
run bash COMPILE/build.sh openeuler || true

echo ""
echo "================================================================"
echo "[$(date -Is)] ALL DONE fail=${fail}"
echo "=== artifacts (latest) ==="
ls -lt COMPILE/dist/ubuntu/*.deb 2>/dev/null | head -3
ls -lt COMPILE/dist/ubuntu-arm/*.deb 2>/dev/null | head -3
ls -lt COMPILE/dist/ubuntu-kylin/*.deb 2>/dev/null | head -3
ls -lt COMPILE/dist/centos-el7/*.rpm 2>/dev/null | head -3
ls -lt COMPILE/dist/centos-el8/*.rpm 2>/dev/null | head -3
ls -lt COMPILE/dist/centos-el9/*.rpm 2>/dev/null | head -3
ls -lt COMPILE/dist/centos-arm-el7/*.rpm 2>/dev/null | head -3
ls -lt COMPILE/dist/centos-arm-el8/*.rpm 2>/dev/null | head -3
ls -lt COMPILE/dist/centos-arm-el9/*.rpm 2>/dev/null | head -3
ls -lt COMPILE/dist/openeuler/*.rpm 2>/dev/null | head -3
ls -lh \
  COMPILE/dist/ubuntu/easyaiot-panel \
  COMPILE/dist/ubuntu-arm/easyaiot-panel \
  COMPILE/dist/ubuntu-kylin/easyaiot-panel \
  COMPILE/dist/centos-el7/easyaiot-panel \
  COMPILE/dist/centos-el8/easyaiot-panel \
  COMPILE/dist/centos-el9/easyaiot-panel \
  COMPILE/dist/centos-arm-el7/easyaiot-panel \
  COMPILE/dist/centos-arm-el8/easyaiot-panel \
  COMPILE/dist/centos-arm-el9/easyaiot-panel \
  COMPILE/dist/openeuler/easyaiot-panel \
  2>/dev/null || true
echo "panel-version-after=$(cat COMPILE/.panel-version 2>/dev/null || echo none)"
echo "log=${LOG}"
exit "$fail"
