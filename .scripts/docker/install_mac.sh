#!/usr/bin/env bash
# ============================================
# EasyAIoT 统一安装脚本 (macOS · 仅镜像部署)
# ============================================
# 使用方法：
#   ./install_mac.sh bootstrap    # 一键安装前置依赖（bash4 + Docker Desktop）
#   ./install_mac.sh check        # 前置环境自检（打印前置操作清单）
#   ./install_mac.sh install      # 拉取预构建镜像并安装启动
#   ./install_mac.sh pull         # 仅拉取预构建镜像
#   ./install_mac.sh start|stop|restart|status|logs|update|verify
#
# 首次部署建议顺序：
#   bootstrap → check → install
#
# 说明：
#   - 仅支持通过远程预构建镜像部署，不支持本地编译（build / build-runtime）
#   - 部署前会做前置环境检测；不满足时打印安装指引并中止
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
# bootstrap 允许在 bash 3.2 下先装 Homebrew bash，再自动用 bash4 重入
if [ -z "${EASYAIOT_BASH_REEXEC:-}" ]; then
  _need_bash4=0
  if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    _need_bash4=1
  fi
  if [ "$_need_bash4" -eq 1 ]; then
    export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"
    for _b in /opt/homebrew/bin/bash /usr/local/bin/bash; do
      if [ -x "$_b" ] && "$_b" -c '[[ ${BASH_VERSINFO[0]} -ge 4 ]]' 2>/dev/null; then
        export EASYAIOT_BASH_REEXEC=1
        export PATH="$(dirname "$_b"):${PATH}"
        exec "$_b" "$0" "$@"
      fi
    done

    # 尚未有 bash4：若是 bootstrap，先 brew install bash 再重入
    _cmd="${1:-}"
    if [ "$_cmd" = "bootstrap" ] || [ "$_cmd" = "deps" ]; then
      echo "========================================="
      echo "  macOS 前置：检测到系统 Bash ${BASH_VERSION}"
      echo "  部署脚本需要 Bash 4+，正在通过 Homebrew 安装..."
      echo "========================================="
      if ! command -v brew >/dev/null 2>&1; then
        echo "错误: 未找到 Homebrew，请先安装: https://brew.sh" >&2
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"" >&2
        exit 1
      fi
      if ! HOMEBREW_NO_AUTO_UPDATE=1 brew install bash; then
        echo "错误: brew install bash 失败" >&2
        exit 1
      fi
      for _b in /opt/homebrew/bin/bash /usr/local/bin/bash; do
        if [ -x "$_b" ] && "$_b" -c '[[ ${BASH_VERSINFO[0]} -ge 4 ]]' 2>/dev/null; then
          export EASYAIOT_BASH_REEXEC=1
          export PATH="$(dirname "$_b"):${PATH}"
          echo "已安装 Bash 4+，继续 bootstrap..."
          exec "$_b" "$0" "$@"
        fi
      done
      echo "错误: brew install bash 后仍未找到 bash 4+" >&2
      exit 1
    fi

    echo "错误: macOS 部署需要 bash 4+（当前: ${BASH_VERSION}）" >&2
    echo "" >&2
    echo "前置操作：" >&2
    echo "  1) 一键安装依赖:  bash .scripts/docker/install_mac.sh bootstrap" >&2
    echo "  2) 或手动:        brew install bash" >&2
    echo "  3) 然后用:        /opt/homebrew/bin/bash .scripts/docker/install_mac.sh check" >&2
    echo "" >&2
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
