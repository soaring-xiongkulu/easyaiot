#!/usr/bin/env bash
# ============================================
# 确保 RUNTIME 矩阵构建所需的 ONNX Runtime C++ SDK（按架构）
#
# 用法:
#   bash RUNTIME/scripts/ensure_ort_deps.sh              # x64 + aarch64
#   bash RUNTIME/scripts/ensure_ort_deps.sh x86_64
#   bash RUNTIME/scripts/ensure_ort_deps.sh arm64
# ============================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT/scripts/runtime_os_matrix.sh"

ORT_VER="${ORT_VERSION:-$(runtime_matrix_ort_version "${RUNTIME_OS_FAMILY:-}")}"
DEPS="$REPO/.deps"

log() { echo "[ensure-ort] $*"; }
warn() { echo "[ensure-ort] WARN: $*" >&2; }

download_ort() {
  local arch_tag="$1"   # x64 | aarch64
  local dest_root="$DEPS/onnxruntime-linux-${arch_tag}-${ORT_VER}"
  if [[ -d "$dest_root/include" && -d "$dest_root/lib" ]]; then
    log "已有 ORT (${arch_tag}): $dest_root"
    return 0
  fi

  local tarball="onnxruntime-linux-${arch_tag}-${ORT_VER}.tgz"
  local url="https://github.com/microsoft/onnxruntime/releases/download/v${ORT_VER}/${tarball}"
  local dest="$DEPS/${tarball}"

  mkdir -p "$DEPS"
  log "下载 ${arch_tag}: $url"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 --connect-timeout 30 -o "$dest" "$url"
  else
    wget -O "$dest" "$url"
  fi

  log "解压到 $dest_root"
  rm -rf "$dest_root"
  tar -xzf "$dest" -C "$DEPS"
  local found
  found="$(find "$DEPS" -maxdepth 1 -type d -name "onnxruntime-linux-${arch_tag}-${ORT_VER}" | head -1 || true)"
  if [[ -n "$found" && "$found" != "$dest_root" ]]; then
    mv "$found" "$dest_root"
  fi
  if [[ ! -d "$dest_root/include" || ! -d "$dest_root/lib" ]]; then
    warn "解压后仍缺少 include/lib: $dest_root"
    return 1
  fi
  log "ORT (${arch_tag}) 就绪: $dest_root"
}

archs=()
if [[ $# -eq 0 ]]; then
  archs=(x86_64 arm64)
else
  for a in "$@"; do
    case "$a" in
      x86_64|amd64|x64) archs+=(x86_64) ;;
      arm64|aarch64) archs+=(arm64) ;;
      *) warn "未知架构: $a"; exit 1 ;;
    esac
  done
fi

fail=0
for arch in "${archs[@]}"; do
  tag="$(runtime_matrix_ort_arch_tag "$arch")"
  download_ort "$tag" || fail=1
done
exit "$fail"
