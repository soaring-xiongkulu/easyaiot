#!/usr/bin/env bash
# ============================================
# x86_64 宿主机上启用 Docker ARM64 等跨架构仿真（与 COMPILE centos-arm 交叉构建一致）
#
# 用法:
#   bash RUNTIME/scripts/ensure_docker_cross_arch.sh
#   bash RUNTIME/scripts/ensure_docker_cross_arch.sh arm64
# ============================================
set -euo pipefail

need_arm64=0
if [[ $# -eq 0 ]]; then
  need_arm64=1
else
  for a in "$@"; do
    case "$a" in arm64|aarch64) need_arm64=1 ;; esac
  done
fi

if [[ "$need_arm64" -eq 0 ]]; then
  exit 0
fi

host="$(uname -m 2>/dev/null || echo unknown)"
if [[ "$host" == "aarch64" || "$host" == "arm64" ]]; then
  exit 0
fi

if docker run --rm --platform linux/arm64 ubuntu:24.04 uname -m 2>/dev/null | grep -q aarch64; then
  echo "[ensure-cross-arch] ARM64 仿真已可用"
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[ensure-cross-arch] 需要 Docker" >&2
  exit 1
fi

echo "[ensure-cross-arch] 安装 qemu binfmt（支持 linux/arm64 容器）..."
docker run --privileged --rm tonistiigi/binfmt --install all >/dev/null

if docker run --rm --platform linux/arm64 ubuntu:24.04 uname -m 2>/dev/null | grep -q aarch64; then
  echo "[ensure-cross-arch] ARM64 仿真就绪"
  exit 0
fi

echo "[ensure-cross-arch] ARM64 仿真仍不可用，请在 ARM 机器上构建 arm64 包" >&2
exit 1
