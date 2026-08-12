#!/usr/bin/env bash
# COMPILE 入口：打包 EasyAIoT EDGE 边缘采集模块
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$REPO/EDGE/pack_linux.sh" "$@"
