#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# EasyAIoT 业务模块一键脚本（macOS / Windows · Docker Desktop · 仅镜像部署）
# 不含中间件；通过 EASYAIOT_DEPLOY_SCOPE=business 过滤 install_desktop_common。
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export EASYAIOT_DEPLOY_SCOPE=business

# 确保 bash 执行
if [ -z "${BASH_VERSION:-}" ]; then
  if command -v bash >/dev/null 2>&1; then
    exec bash "$0" "$@"
  fi
  echo "错误: 需要 bash 环境" >&2
  exit 1
fi

_os="$(uname -s 2>/dev/null || echo unknown)"
case "${_os}" in
  Darwin)
    exec bash "${SCRIPT_DIR}/install_mac.sh" "$@"
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    exec bash "${SCRIPT_DIR}/install_windows.sh" "$@"
    ;;
  *)
    # Linux 请使用 install_business_linux.sh；此处作兼容回退
    if [ -f "${SCRIPT_DIR}/install_business_linux.sh" ]; then
      exec bash "${SCRIPT_DIR}/install_business_linux.sh" "$@"
    fi
    echo "错误: 当前系统 ${_os} 请使用 install_business_linux.sh" >&2
    exit 1
    ;;
esac
