#!/usr/bin/env bash
# 全量 Linux 重打包 + 各目标耗时统计
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

LOG_DIR="${ROOT}/COMPILE/work/logs"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="${LOG_DIR}/pack_all_${STAMP}.log"
TIMING="${LOG_DIR}/pack_all_timing_${STAMP}.log"
echo "$LOG" > "${LOG_DIR}/pack_all_latest.path"

exec > >(tee -a "$LOG") 2>&1

export COMPILE_CN_MIRROR="${COMPILE_CN_MIRROR:-huawei}"

echo "[$(date -Is)] FULL REPACK start root=${ROOT}"
echo "COMPILE_CN_MIRROR=${COMPILE_CN_MIRROR}"
echo "panel-version-before=$(cat COMPILE/.panel-version 2>/dev/null || echo none)"
: > "$TIMING"

fail=0
run() {
  local start end elapsed rc
  echo ""
  echo "================================================================"
  echo "[$(date -Is)] START: $*"
  echo "================================================================"
  start=$(date +%s)
  "$@"
  rc=$?
  end=$(date +%s)
  elapsed=$((end - start))
  if [ "$rc" -eq 0 ]; then
    echo "[$(date -Is)] OK (${elapsed}s): $*"
    echo "OK ${elapsed}s $*" >> "$TIMING"
  else
    echo "[$(date -Is)] FAIL(${rc}, ${elapsed}s): $*"
    echo "FAIL ${elapsed}s $*" >> "$TIMING"
    fail=1
  fi
  return 0
}

if [ -d PANEL/ui/dist ] && [ ! -w PANEL/ui/dist ]; then
  echo "PANEL/ui/dist 不可写，尝试 docker chown"
  docker run --rm -v "${ROOT}/PANEL/ui:/ui" alpine chown -R "$(id -u):$(id -g)" /ui/dist || true
fi

run bash COMPILE/build.sh ubuntu-x86 --deb
run bash COMPILE/build.sh ubuntu-arm --deb
run bash COMPILE/build.sh ubuntu-kylin --deb
run bash COMPILE/build.sh centos-el7
run bash COMPILE/build.sh centos-el8
run bash COMPILE/build.sh centos-el9
run bash COMPILE/build.sh centos-arm-el7
run bash COMPILE/build.sh centos-arm-el8
run bash COMPILE/build.sh centos-arm-el9
run bash COMPILE/build.sh openeuler

echo ""
echo "================================================================"
echo "[$(date -Is)] ALL DONE fail=${fail}"
echo "=== timing summary ==="
cat "$TIMING"
echo "=== artifacts (latest) ==="
ls -lt COMPILE/dist/ubuntu/*.deb 2>/dev/null | head -2
ls -lt COMPILE/dist/ubuntu-arm/*.deb 2>/dev/null | head -2
ls -lt COMPILE/dist/ubuntu-kylin/*.deb 2>/dev/null | head -2
ls -lt COMPILE/dist/centos-el7/*.rpm 2>/dev/null | head -2
ls -lt COMPILE/dist/centos-el8/*.rpm 2>/dev/null | head -2
ls -lt COMPILE/dist/centos-el9/*.rpm 2>/dev/null | head -2
ls -lt COMPILE/dist/centos-arm-el7/*.rpm 2>/dev/null | head -2
ls -lt COMPILE/dist/centos-arm-el8/*.rpm 2>/dev/null | head -2
ls -lt COMPILE/dist/centos-arm-el9/*.rpm 2>/dev/null | head -2
ls -lt COMPILE/dist/openeuler/*.rpm 2>/dev/null | head -2
echo "panel-version-after=$(cat COMPILE/.panel-version 2>/dev/null || echo none)"
echo "timing=${TIMING}"
echo "log=${LOG}"
exit "$fail"
