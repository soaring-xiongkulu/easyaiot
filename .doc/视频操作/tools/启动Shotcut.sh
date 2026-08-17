#!/usr/bin/env bash
# 从本仓库文档目录启动本机已安装的 Shotcut
set -euo pipefail
if command -v shotcut >/dev/null 2>&1; then
  exec shotcut "$@"
fi
if [[ -x "$HOME/.local/bin/shotcut" ]]; then
  exec "$HOME/.local/bin/shotcut" "$@"
fi
echo "未找到 Shotcut，请先按 01-安装与启动.md 安装。" >&2
exit 1
