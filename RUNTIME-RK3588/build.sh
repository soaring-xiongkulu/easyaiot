#!/usr/bin/env bash
# 已合并至 install_linux.sh — 请使用统一入口
echo "[RUNTIME-RK3588] 请使用: ./RUNTIME-RK3588/install_linux.sh" >&2
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/install_linux.sh" build
