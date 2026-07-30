#!/usr/bin/env bash
# 兼容旧入口：macOS 中间件脚本已合并为桌面端镜像部署脚本
exec "$(cd "$(dirname "$0")" && pwd)/install_middleware_desktop.sh" "$@"
