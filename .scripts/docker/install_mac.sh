#!/usr/bin/env bash
# ============================================
# EasyAIoT 统一安装脚本 (macOS · 仅镜像部署)
# ============================================
# 使用方法：
#   ./install_mac.sh              # 交互引导
#   ./install_mac.sh install      # 拉取预构建镜像并安装启动
#   ./install_mac.sh pull         # 仅拉取预构建镜像
#   ./install_mac.sh start|stop|restart|status|logs|update|verify|check
#
# 说明：
#   - 仅支持通过远程预构建镜像部署，不支持本地编译（build / build-runtime）
#   - 需要 Docker Desktop；建议 bash 4+（Homebrew: brew install bash）
# ============================================

# 确保 bash 执行
if [ -z "${BASH_VERSION:-}" ]; then
  if command -v bash >/dev/null 2>&1; then
    exec bash "$0" "$@"
  fi
  echo "错误: 需要 bash 环境" >&2
  exit 1
fi

# macOS 自带 bash 3.2；runtime_image 等脚本需要 bash 4+（关联数组）
if [ -z "${EASYAIOT_BASH_REEXEC:-}" ]; then
  _need_bash4=0
  if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    _need_bash4=1
  fi
  if [ "$_need_bash4" -eq 1 ]; then
    for _b in /opt/homebrew/bin/bash /usr/local/bin/bash; do
      if [ -x "$_b" ] && "$_b" -c '[[ ${BASH_VERSINFO[0]} -ge 4 ]]' 2>/dev/null; then
        export EASYAIOT_BASH_REEXEC=1
        export PATH="$(dirname "$_b"):${PATH}"
        exec "$_b" "$0" "$@"
      fi
    done
    echo "错误: macOS 部署需要 bash 4+（当前: ${BASH_VERSION}）" >&2
    echo "请安装: brew install bash" >&2
    echo "然后重新执行本脚本（或确保 /opt/homebrew/bin/bash 在 PATH 中）" >&2
    exit 1
  fi
fi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

if [[ "${OSTYPE:-}" != darwin* ]] && [ "${EASYAIOT_FORCE_MACOS:-0}" != "1" ]; then
  echo "错误: install_mac.sh 仅支持 macOS（当前: ${OSTYPE:-unknown}）" >&2
  echo "Windows 请使用: .scripts/docker/install_windows.ps1 或 install_windows.sh" >&2
  echo "Linux 请使用:  .scripts/docker/install_linux.sh" >&2
  exit 1
fi

export EASYAIOT_DESKTOP_OS=mac
export EASYAIOT_INSTALL_LABEL="${EASYAIOT_INSTALL_LABEL:-EasyAIoT 统一安装脚本 (macOS · 仅镜像部署)}"

# shellcheck source=install_desktop_common.sh
source "${SCRIPT_DIR}/install_desktop_common.sh"

desktop_main "$@"
