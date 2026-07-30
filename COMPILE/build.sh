#!/usr/bin/env bash
# EasyAIoT COMPILE — 将 PANEL 等模块打包为各平台可执行文件 / 安装包
#
# 用法:
#   bash COMPILE/build.sh                 # 默认：ubuntu 单文件
#   bash COMPILE/build.sh ubuntu          # Ubuntu 单文件 easyaiot-panel
#   bash COMPILE/build.sh ubuntu --local  # 不经 Docker，宿主机直编
#   bash COMPILE/build.sh ubuntu --deb    # 生成 .deb 安装包（无二进制时先构建）
#   bash COMPILE/build.sh windows         # Windows 主机产出 .exe
#   bash COMPILE/build.sh macos           # macOS 主机产出可执行文件
#   bash COMPILE/build.sh centos          # CentOS/RHEL 主机产出二进制 + .rpm
#   bash COMPILE/build.sh deb             # 同上
#   bash COMPILE/build.sh list            # 列出可用目标
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-ubuntu}"
shift || true

list_targets() {
  echo "可用目标:"
  echo "  - ubuntu          单文件 easyaiot-panel"
  echo "  - ubuntu --deb    Ubuntu/Debian .deb 安装包"
  echo "  - ubuntu-x86      x86/amd64（分开打包：deploy 调用 install_linux.sh）"
  echo "  - ubuntu-arm      ARM64（分开打包：deploy 调用 install_linux_arm.sh）"
  echo "  - ubuntu-kylin    麒麟 ARM64（分开打包：deploy 调用 install_linux_kylin.sh）"
  echo "  - windows         Windows 主机打包 .exe"
  echo "  - macos           macOS 主机打包可执行文件"
  echo "  - centos          CentOS/RHEL 主机打包二进制 + .rpm"
  echo "  - deb             同 ubuntu --deb"
}

case "$TARGET" in
  list|-l|--list)
    list_targets
    ;;
  deb|package|ubuntu-deb)
    bash "${SCRIPT_DIR}/platforms/ubuntu/build.sh" --deb "$@"
    ;;
  ubuntu|linux|linux-ubuntu)
    bash "${SCRIPT_DIR}/platforms/ubuntu/build.sh" "$@"
    ;;
  ubuntu-x86|ubuntu-amd64|amd64-ubuntu)
    bash "${SCRIPT_DIR}/platforms/ubuntu/build.sh" "$@"
    ;;
  ubuntu-arm|arm-ubuntu|linux-arm|ubuntuarm)
    bash "${SCRIPT_DIR}/platforms/ubuntu/build.sh" --arm "$@"
    ;;
  ubuntu-kylin|kylin-ubuntu|linux-kylin|ubuntu-kylin)
    bash "${SCRIPT_DIR}/platforms/ubuntu/build.sh" --kylin "$@"
    ;;
  windows|win)
    bash "${SCRIPT_DIR}/platforms/windows/build.sh" "$@"
    ;;
  macos|mac|darwin)
    bash "${SCRIPT_DIR}/platforms/macos/build.sh" "$@"
    ;;
  centos|rhel|rpm)
    bash "${SCRIPT_DIR}/platforms/centos/build.sh" "$@"
    ;;
  *)
    echo "[COMPILE] 未知目标: ${TARGET}" >&2
    list_targets
    exit 1
    ;;
esac
