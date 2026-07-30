#!/usr/bin/env bash
# ============================================
# EasyAIoT 统一安装脚本 (Windows · 仅镜像部署)
# ============================================
# 推荐在 Git Bash 中运行，或通过 install_windows.ps1 启动：
#   ./install_windows.sh              # 交互引导
#   ./install_windows.sh install      # 拉取预构建镜像并安装启动
#   ./install_windows.sh pull         # 仅拉取预构建镜像
#   ./install_windows.sh start|stop|restart|status|logs|update|verify|check
#
# 若本机尚未安装 Docker Desktop / WSL2，请先用 PowerShell：
#   .\.scripts\docker\install_windows.ps1 bootstrap
# 然后再执行 install / check。
#
# 前置条件：
#   - Docker Desktop for Windows（启用 WSL2 后端更佳）
#   - Git for Windows（提供 bash）或 WSL
# ============================================

if [ -z "${BASH_VERSION:-}" ]; then
  if command -v bash >/dev/null 2>&1; then
    exec bash "$0" "$@"
  fi
  echo "错误: 需要 bash 环境（请安装 Git for Windows 或在 WSL 中运行）" >&2
  exit 1
fi

if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
  echo "错误: 需要 bash 4+（当前: ${BASH_VERSION}）" >&2
  echo "请升级 Git for Windows，或在 WSL 中运行本脚本" >&2
  exit 1
fi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

# 允许：MSYS/Cygwin/Git Bash，或显式声明在 Windows 上跑（含 WSL）
_is_windows=0
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) _is_windows=1 ;;
esac
if [ "${EASYAIOT_FORCE_WINDOWS:-0}" = "1" ]; then
  _is_windows=1
fi
# WSL：uname 为 Linux，但存在 /mnt/c 且用户通过 install_windows 进入
if [ "$_is_windows" -eq 0 ] && [ -n "${WSL_DISTRO_NAME:-}" ]; then
  _is_windows=1
fi
if [ "$_is_windows" -eq 0 ] && grep -qi microsoft /proc/version 2>/dev/null; then
  _is_windows=1
fi

if [ "$_is_windows" -eq 0 ]; then
  echo "错误: install_windows.sh 仅支持 Windows（Git Bash / MSYS / WSL）" >&2
  echo "macOS 请使用: .scripts/docker/install_mac.sh" >&2
  echo "Linux 请使用: .scripts/docker/install_linux.sh" >&2
  echo "若确在 Windows 上，可: EASYAIOT_FORCE_WINDOWS=1 bash install_windows.sh ..." >&2
  exit 1
fi

export EASYAIOT_DESKTOP_OS=windows
export EASYAIOT_INSTALL_LABEL="${EASYAIOT_INSTALL_LABEL:-EasyAIoT 统一安装脚本 (Windows · 仅镜像部署)}"

# shellcheck source=install_desktop_common.sh
source "${SCRIPT_DIR}/install_desktop_common.sh"

desktop_main "$@"
