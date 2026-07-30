#!/usr/bin/env bash
# 兼容上级 install_*.sh 统一委托（与 DEVICE/AI/WEB 等模块同名入口）
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install.sh" "$@"
