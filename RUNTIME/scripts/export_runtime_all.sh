#!/usr/bin/env bash
# ============================================
# 批量导出 RUNTIME 离线包（矩阵与 COMPILE/platforms/pack_all_linux.sh 对齐）
#
# 用法:
#   bash RUNTIME/scripts/export_runtime_all.sh
#       # 默认：COMPILE pack_all_linux 全覆盖（--compile-target all-linux）
#   bash RUNTIME/scripts/export_runtime_all.sh --all
#   bash RUNTIME/scripts/export_runtime_all.sh --compile-target openeuler
#   bash RUNTIME/scripts/export_runtime_all.sh openeuler24 el9 ubuntu26
#   RUNTIME_MATRIX_JOBS=2 bash RUNTIME/scripts/export_runtime_all.sh
# ============================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT/scripts/runtime_os_matrix.sh"

EXPORT="$ROOT/scripts/export_runtime_os_container.sh"
PREFLIGHT="$ROOT/scripts/preflight_runtime_bundle.sh"
VERIFY="$ROOT/scripts/verify_runtime_compile_matrix.sh"
LOG_DIR="${RUNTIME_MATRIX_LOG_DIR:-$REPO/.tmp/runtime-matrix-logs}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/export_all_$(date +%Y%m%d_%H%M%S).log"

JOBS="${RUNTIME_MATRIX_JOBS:-1}"
# 多目标并行会争用同一 /src/RUNTIME/build，默认串行；需并行时请用独立仓库副本
if [[ "$JOBS" -gt 1 ]]; then
  echo "警告: RUNTIME_MATRIX_JOBS=$JOBS 时多容器共享 build/，建议设为 1 或使用独立工作副本" >&2
fi
MODE="compile"
COMPILE_TARGET="all-linux"
MISSING_ONLY=0
TARGETS=()

usage() {
  cat <<EOF
用法: $0 [--all|--compile-target <name>] [os_family ...]

  （无参数）             COMPILE pack_all_linux 全覆盖（同 --compile-target all-linux）
  --missing-only         仅构建 COMPILE 覆盖范围内尚缺 tarball 的目标
  --all                  打 runtime_os_matrix.sh 登记的全部目标（含 openeuler22 等扩展项）
  --compile-target NAME  与 COMPILE/build.sh 同名目标，如 centos-el9 / openeuler / all-linux
  os_family ...          显式列表，如 openeuler24 el9 ubuntu26

环境变量:
  RUNTIME_MATRIX_JOBS=1  并行容器数（Miniconda 按 os 分卷，可安全并行）
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) MODE="all"; shift ;;
    --missing-only) MISSING_ONLY=1; shift ;;
    --compile-target)
      MODE="compile"
      COMPILE_TARGET="${2:?}"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) TARGETS+=("$1"); shift ;;
  esac
done

resolve_keys() {
  local keys="" item
  if [[ ${#TARGETS[@]} -gt 0 ]]; then
    for item in "${TARGETS[@]}"; do
      if [[ "$item" == *:* ]]; then
        keys+="$item "
      else
        keys+="${item}:x86_64 "
      fi
    done
  elif [[ "$MODE" == "all" ]]; then
    keys="$(runtime_matrix_all_keys | tr '\n' ' ')"
  else
    keys="$(runtime_matrix_for_compile_target "$COMPILE_TARGET")"
    if [[ -z "$keys" ]]; then
      echo "未知 COMPILE 目标: $COMPILE_TARGET" >&2
      exit 1
    fi
  fi
  echo "$keys"
}

build_one() {
  local os_family="$1" arch="$2"
  local tar_path="$ROOT/.bundle-runtime/${os_family}/${arch}/easyaiot-runtime-${os_family}-${arch}.tar.gz"
  if [[ "$MISSING_ONLY" -eq 1 && -f "$tar_path" ]]; then
    echo "[$(date -Is)] SKIP ${os_family}/${arch} (已有 $tar_path)" | tee -a "$LOG"
    return 0
  fi
  local img
  img="$(runtime_matrix_image "$os_family" "$arch")"
  if [[ -z "$img" && "$os_family" == kylin* ]]; then
    echo "[$(date -Is)] SKIP ${os_family}/${arch} (未配置麒麟 Docker 镜像，请设置 RUNTIME_KYLIN10_ARM64_IMAGE 等)" | tee -a "$LOG"
    return 0
  fi
  local log="$LOG_DIR/${os_family}-${arch}.log"
  echo "[$(date -Is)] START ${os_family}/${arch}" | tee -a "$LOG"
  if RUNTIME_OS_FAMILY="$os_family" RUNTIME_ARCH="$arch" \
     RUNTIME_OS_CONTAINER_IMAGE="$(runtime_matrix_image "$os_family" "$arch")" \
     bash "$EXPORT" "$os_family" >>"$log" 2>&1; then
    echo "[$(date -Is)] OK ${os_family}/${arch}" | tee -a "$LOG"
    return 0
  fi
  echo "[$(date -Is)] FAIL ${os_family}/${arch} (see $log)" | tee -a "$LOG"
  return 1
}

main() {
  if [[ -x "$ROOT/scripts/ensure_ort_deps.sh" ]]; then
    bash "$ROOT/scripts/ensure_ort_deps.sh" x86_64 arm64 || true
  fi
  bash "$VERIFY" || true
  bash "$PREFLIGHT" --compile-coverage || true
  echo "日志: $LOG"

  local keys fail=0
  keys="$(resolve_keys)"
  # shellcheck disable=SC2206
  local items=($keys)

  if [[ ${#items[@]} -eq 0 ]]; then
    echo "无构建目标" >&2
    exit 1
  fi

  echo "将构建 ${#items[@]} 个目标 (jobs=$JOBS): ${items[*]}"

  if [[ "$JOBS" -le 1 ]]; then
    local item os arch
    for item in "${items[@]}"; do
      os="${item%%:*}"
      arch="${item##*:}"
      build_one "$os" "$arch" || fail=1
    done
  else
    local item os arch pids=() pid
    for item in "${items[@]}"; do
      os="${item%%:*}"
      arch="${item##*:}"
      while [[ $(jobs -rp | wc -l) -ge $JOBS ]]; do
        sleep 2
      done
      build_one "$os" "$arch" &
      pids+=($!)
    done
    for pid in "${pids[@]}"; do
      wait "$pid" || fail=1
    done
  fi

  echo ""
  bash "$PREFLIGHT" --compile-coverage || fail=1
  bash "$VERIFY" --check-tarballs || true
  exit "$fail"
}

main
