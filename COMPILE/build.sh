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
#   bash COMPILE/build.sh centos-el9      # CentOS/RHEL el9（默认；centos 同义）
#   bash COMPILE/build.sh centos-el8      # CentOS/RHEL el8
#   bash COMPILE/build.sh centos-el7      # CentOS/RHEL el7
#   bash COMPILE/build.sh centos-arm-el9  # CentOS ARM el9（centos-arm 同义）
#   bash COMPILE/build.sh openeuler       # openEuler 24.x 主机产出二进制 + .rpm
#   bash COMPILE/build.sh all-linux       # Ubuntu×3 deb + CentOS el9 x86/arm + openEuler rpm
#   bash COMPILE/build.sh list            # 列出可用目标
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-ubuntu}"
shift || true

list_targets() {
  echo "可用目标:"
  echo "  - ubuntu          单文件 easyaiot-panel"
  echo "  - ubuntu --deb    Ubuntu/Debian .deb 安装包"
  echo "  - ubuntu-x86      x86/amd64（deploy: install_linux.sh）"
  echo "  - ubuntu-arm      ARM64（deploy: install_linux_arm.sh）"
  echo "  - ubuntu-kylin    麒麟 ARM64（deploy: install_linux_kylin.sh）"
  echo "  - windows         Windows 主机打包 .exe"
  echo "  - macos           macOS 主机打包可执行文件"
  echo "  - centos-el7      CentOS/RHEL el7 二进制 + .rpm"
  echo "  - centos-el8      CentOS/RHEL el8 二进制 + .rpm"
  echo "  - centos-el9      CentOS/RHEL el9 二进制 + .rpm（centos / rhel 同义）"
  echo "  - centos-arm-el7  CentOS/RHEL ARM64 el7 交叉打包"
  echo "  - centos-arm-el8  CentOS/RHEL ARM64 el8 交叉打包"
  echo "  - centos-arm-el9  CentOS/RHEL ARM64 el9 交叉打包（centos-arm 同义）"
  echo "  - openeuler       openEuler 24.x 主机打包二进制 + .rpm"
  echo "  - all-linux       Ubuntu×3 deb + centos-el{7,8,9} x86/arm + openeuler"
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
  ubuntu-kylin|kylin-ubuntu|linux-kylin)
    bash "${SCRIPT_DIR}/platforms/ubuntu/build.sh" --kylin "$@"
    ;;
  windows|win)
    bash "${SCRIPT_DIR}/platforms/windows/build.sh" "$@"
    ;;
  macos|mac|darwin)
    bash "${SCRIPT_DIR}/platforms/macos/build.sh" "$@"
    ;;
  centos-el7|centos7|el7)
    bash "${SCRIPT_DIR}/platforms/centos/build.sh" --el7 "$@"
    ;;
  centos-el8|centos8|el8)
    bash "${SCRIPT_DIR}/platforms/centos/build.sh" --el8 "$@"
    ;;
  centos-el9|centos9|el9|centos|rhel|rpm)
    bash "${SCRIPT_DIR}/platforms/centos/build.sh" --el9 "$@"
    ;;
  centos-arm-el7|centos_arm_el7|rhel-arm-el7)
    bash "${SCRIPT_DIR}/platforms/centos-arm/build.sh" --el7 "$@"
    ;;
  centos-arm-el8|centos_arm_el8|rhel-arm-el8)
    bash "${SCRIPT_DIR}/platforms/centos-arm/build.sh" --el8 "$@"
    ;;
  centos-arm-el9|centos_arm_el9|centos-arm|centos_arm|rhel-arm|centosarm)
    bash "${SCRIPT_DIR}/platforms/centos-arm/build.sh" --el9 "$@"
    ;;
  openeuler|openEuler|oe|euler)
    bash "${SCRIPT_DIR}/platforms/openeuler/build.sh" "$@"
    ;;
  all-linux|linux-all|pack-all|pack_all)
    bash "${SCRIPT_DIR}/platforms/pack_all_linux.sh" "$@"
    ;;
  *)
    echo "[COMPILE] 未知目标: ${TARGET}" >&2
    list_targets
    exit 1
    ;;
esac
