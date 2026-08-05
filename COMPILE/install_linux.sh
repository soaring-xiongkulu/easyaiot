#!/usr/bin/env bash
# COMPILE 统一入口（Linux 安装包管理 + 多平台打包入口）：
# - 默认：交互式打包（Ubuntu / CentOS / openEuler / Windows / 全量 Linux）
# - pack-all：一次打 Ubuntu×3 deb + centos-el9 + centos-arm-el9 + openEuler rpm
# - windows：Windows 主机打包 .exe（可选 --installer）
# - install：安装/覆盖本地产物包（自动识别 deb/rpm）
# - uninstall：卸载系统已安装 easyaiot-panel（自动识别 deb/rpm）
# - status：查看是否已安装

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PKG_NAME="easyaiot-panel"

usage() {
  cat <<'EOF'
用法:
  bash COMPILE/install_linux.sh
    # 默认进入交互式打包

  bash COMPILE/install_linux.sh pack-all
    # 一次打包 Ubuntu(x86/arm/kylin) deb + CentOS(x86/arm)/openEuler rpm

  bash COMPILE/install_linux.sh windows
  bash COMPILE/install_linux.sh windows --installer
    # Windows 主机打包 .exe + runtime/（可选 NSIS 安装包；须在 Windows 上执行）

  bash COMPILE/install_linux.sh install [auto|x86|arm|kylin|centos-el7|centos-el8|centos-el9|centos-arm-el9|openeuler|--file <pkg-path>]
    # 安装/覆盖安装本地包（自动识别 deb/rpm；centos / centos-arm 同义 el9）

  bash COMPILE/install_linux.sh uninstall
    # 卸载系统中已安装的 easyaiot-panel（自动识别 deb/rpm）

  bash COMPILE/install_linux.sh status
    # 查看安装状态与版本
EOF
}

detect_pm() {
  if command -v dpkg >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1; then
    echo "deb"
    return 0
  fi
  if command -v rpm >/dev/null 2>&1; then
    echo "rpm"
    return 0
  fi
  echo "unknown"
}

is_openeuler() {
  if [ -f /etc/openEuler-release ]; then
    return 0
  fi
  if [ -f /etc/os-release ] && grep -Eiq '^ID=["'\'']?openeuler' /etc/os-release 2>/dev/null; then
    return 0
  fi
  return 1
}

is_kylin_like() {
  if [ -f /etc/kylin-release ] || [ -f /etc/neokylin-release ]; then
    return 0
  fi
  # 注意：openEuler 走 RPM，不在此匹配
  if [ -f /etc/os-release ] && tr '[:upper:]' '[:lower:]' < /etc/os-release | awk '/kylin|neokylin|uos|uniontech/{f=1} END{exit(f?0:1)}'; then
    return 0
  fi
  return 1
}

pick_latest_by_pattern() {
  local pattern="$1"
  local min_bytes="${2:-0}"
  local files=()
  # 必须在函数内再做 glob；调用方若直接展开，只会把第一个文件传给 $1
  shopt -s nullglob
  # shellcheck disable=SC2206
  files=(${pattern})
  shopt -u nullglob
  if [ "${#files[@]}" -eq 0 ]; then
    return 1
  fi
  # 优先按包名中的版本号取最大（兼容 mawk）；同版本再按修改时间
  local f base ver size
  local best_file=""
  local best_ver=-1
  local best_mtime=-1
  local mtime
  local skipped=0
  for f in "${files[@]}"; do
    [ -f "$f" ] || continue
    size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
    # 跳过明显损坏的空包/残包（例如打包中断留下的 1KB deb）
    if [ "$min_bytes" -gt 0 ] && [ "$size" -lt "$min_bytes" ]; then
      echo "[install] 跳过异常小包: $(basename "$f") (${size} bytes)" >&2
      skipped=$((skipped + 1))
      continue
    fi
    base="$(basename "$f")"
    ver="$(printf '%s' "$base" | sed -n 's/.*_\([0-9][0-9]*\)_.*/\1/p')"
    if [ -z "$ver" ]; then
      ver="$(printf '%s' "$base" | sed -n 's/.*-\([0-9][0-9]*\)[-.].*/\1/p')"
    fi
    ver="${ver:-0}"
    mtime="$(stat -c '%Y' "$f" 2>/dev/null || echo 0)"
    if [ "$ver" -gt "$best_ver" ] || { [ "$ver" -eq "$best_ver" ] && [ "$mtime" -gt "$best_mtime" ]; }; then
      best_ver="$ver"
      best_mtime="$mtime"
      best_file="$f"
    fi
  done
  [ -n "$best_file" ] || return 1
  echo "[install] 候选 ${#files[@]} 个包（跳过 ${skipped}），选用版本 ${best_ver}: $(basename "$best_file")" >&2
  printf '%s\n' "$best_file"
}

pick_deb_file() {
  local variant="${1:-auto}"
  # 正常 PANEL deb 约数百 MB；小于 1MB 基本是损坏产物
  local min_bytes=1000000
  case "$variant" in
    x86|amd64)
      # 整段作为 pattern 字符串传入，避免调用前 glob 展开
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/ubuntu/${PKG_NAME}_*_amd64.deb" "$min_bytes"
      return $?
      ;;
    arm|arm64)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/ubuntu-arm/${PKG_NAME}_*_arm_arm64.deb" "$min_bytes"
      return $?
      ;;
    kylin)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/ubuntu-kylin/${PKG_NAME}_*_kylin_arm64.deb" "$min_bytes"
      return $?
      ;;
    auto)
      local arch
      arch="$(uname -m)"
      if [[ "$arch" == "x86_64" || "$arch" == "amd64" ]]; then
        pick_deb_file x86
        return $?
      fi
      if is_kylin_like; then
        pick_deb_file kylin || pick_deb_file arm
        return $?
      fi
      pick_deb_file arm
      return $?
      ;;
    *)
      return 1
      ;;
  esac
}

pick_rpm_file() {
  local variant="${1:-auto}"
  local min_bytes=1000000
  case "$variant" in
    centos-el7|centos7|el7)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-el7/${PKG_NAME}-*-*.el7.*.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-el7/${PKG_NAME}-*.rpm" "$min_bytes"
      return $?
      ;;
    centos-el8|centos8|el8)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-el8/${PKG_NAME}-*-*.el8.*.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-el8/${PKG_NAME}-*.rpm" "$min_bytes"
      return $?
      ;;
    centos|rhel|centos-el9|centos9|el9)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-el9/${PKG_NAME}-*-*.el9.*.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-el9/${PKG_NAME}-*.rpm" "$min_bytes"
      return $?
      ;;
    centos-arm-el7)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-arm-el7/${PKG_NAME}-*-*.el7.aarch64.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-arm-el7/${PKG_NAME}-*.rpm" "$min_bytes"
      return $?
      ;;
    centos-arm-el8)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-arm-el8/${PKG_NAME}-*-*.el8.aarch64.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-arm-el8/${PKG_NAME}-*.rpm" "$min_bytes"
      return $?
      ;;
    centos-arm|centos_arm|rhel-arm|centos-arm-el9)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-arm-el9/${PKG_NAME}-*-*.el9.aarch64.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/centos-arm-el9/${PKG_NAME}-*.rpm" "$min_bytes"
      return $?
      ;;
    openeuler|oe|euler)
      pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/openeuler/${PKG_NAME}-*-*.oe2403.*.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/openeuler/${PKG_NAME}-*-*.openeuler.*.rpm" "$min_bytes" \
        || pick_latest_by_pattern "${REPO_ROOT}/COMPILE/dist/openeuler/${PKG_NAME}-*.rpm" "$min_bytes"
      return $?
      ;;
    auto)
      local arch major
      arch="$(uname -m)"
      major=""
      if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        major="${VERSION_ID%%.*}"
      fi
      if is_openeuler; then
        pick_rpm_file openeuler \
          || pick_rpm_file centos \
          || pick_rpm_file centos-arm
        return $?
      fi
      if [[ "$arch" == "aarch64" || "$arch" == "arm64" ]]; then
        case "$major" in
          7) pick_rpm_file centos-arm-el7 || pick_rpm_file centos-arm || pick_rpm_file openeuler ;;
          8) pick_rpm_file centos-arm-el8 || pick_rpm_file centos-arm || pick_rpm_file openeuler ;;
          *) pick_rpm_file centos-arm || pick_rpm_file centos-arm-el8 || pick_rpm_file centos-arm-el7 || pick_rpm_file openeuler ;;
        esac
        return $?
      fi
      case "$major" in
        7) pick_rpm_file centos-el7 || pick_rpm_file centos || pick_rpm_file openeuler ;;
        8) pick_rpm_file centos-el8 || pick_rpm_file centos || pick_rpm_file openeuler ;;
        *) pick_rpm_file centos || pick_rpm_file centos-el8 || pick_rpm_file centos-el7 || pick_rpm_file openeuler ;;
      esac
      return $?
      ;;
    *)
      return 1
      ;;
  esac
}

install_deb() {
  local pkg_file="$1"
  local before=""
  local pkg_ver=""
  before="$(dpkg-query -W -f='${Version}' "${PKG_NAME}" 2>/dev/null || true)"
  pkg_ver="$(dpkg-deb -f "$pkg_file" Version 2>/dev/null || true)"
  echo "[install] 当前已安装版本: ${before:-无}"
  echo "[install] 待安装包版本: ${pkg_ver:-未知} ← $(basename "$pkg_file")"
  if [ -n "$before" ] && [ -n "$pkg_ver" ] && dpkg --compare-versions "$pkg_ver" lt "$before"; then
    if [ "${PANEL_ALLOW_DOWNGRADE:-0}" != "1" ]; then
      echo "[install] 错误: 待安装包 (${pkg_ver}) 低于已安装版本 (${before})，已中止，避免降级。" >&2
      echo "[install] 如确需降级：PANEL_ALLOW_DOWNGRADE=1 bash COMPILE/install_linux.sh install" >&2
      echo "[install] 或指定包：bash COMPILE/install_linux.sh install --file <path.deb>" >&2
      exit 1
    fi
    echo "[install] 警告: 允许降级 ${before} → ${pkg_ver}（PANEL_ALLOW_DOWNGRADE=1）" >&2
  fi
  echo "[install] 使用 dpkg 覆盖安装: ${pkg_file}"
  dpkg -i "$pkg_file" || apt-get install -f -y
  systemctl daemon-reload >/dev/null 2>&1 || true
  # 覆盖安装后强制重启，避免仍跑旧进程/旧 UI
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable easyaiot-panel.service >/dev/null 2>&1 || true
    systemctl restart easyaiot-panel.service >/dev/null 2>&1 || systemctl try-restart easyaiot-panel.service >/dev/null 2>&1 || true
  fi
  local after=""
  after="$(dpkg-query -W -f='${Version}' "${PKG_NAME}" 2>/dev/null || true)"
  echo "[install] 安装后版本: ${after:-未知}"
  if [ -n "$before" ] && [ -n "$after" ] && [ "$before" = "$after" ]; then
    echo "[install] 警告: 版本号未变化（${after}）。若界面仍是旧的，请确认安装的是最新 .deb，并强制刷新浏览器缓存。" >&2
  fi
  echo "[install] 完成。请打开 http://127.0.0.1:9200/ 并强制刷新（Ctrl+Shift+R）"
}

install_rpm() {
  local pkg_file="$1"
  local before=""
  before="$(rpm -q --qf '%{VERSION}' "${PKG_NAME}" 2>/dev/null || true)"
  echo "[install] 当前已安装版本: ${before:-无}"
  echo "[install] 使用 rpm 覆盖安装: ${pkg_file}"
  rpm -Uvh --replacepkgs "$pkg_file"
  systemctl daemon-reload >/dev/null 2>&1 || true
  if command -v systemctl >/dev/null 2>&1; then
    systemctl enable easyaiot-panel.service >/dev/null 2>&1 || true
    systemctl restart easyaiot-panel.service >/dev/null 2>&1 || systemctl try-restart easyaiot-panel.service >/dev/null 2>&1 || true
  fi
  local after=""
  after="$(rpm -q --qf '%{VERSION}' "${PKG_NAME}" 2>/dev/null || true)"
  echo "[install] 安装后版本: ${after:-未知}"
  echo "[install] 完成。请打开 http://127.0.0.1:9200/ 并强制刷新（Ctrl+Shift+R）"
}

do_install() {
  local pm="$1"
  shift
  local mode="${1:-auto}"
  local file_arg="${2:-}"
  local pkg_file=""

  if [[ "$mode" == "--file" ]]; then
    if [ -z "${file_arg}" ]; then
      echo "缺少 --file 路径" >&2
      exit 1
    fi
    pkg_file="${file_arg}"
  else
    if [[ "$pm" == "deb" ]]; then
      pkg_file="$(pick_deb_file "$mode" || true)"
    else
      case "$mode" in
        centos|rhel|centos-el7|centos-el8|centos-el9|centos7|centos8|centos9|el7|el8|el9|\
        centos-arm|centos_arm|rhel-arm|centos-arm-el7|centos-arm-el8|centos-arm-el9|\
        openeuler|oe|euler|auto)
          pkg_file="$(pick_rpm_file "$mode" || true)"
          ;;
        *)
          pkg_file="$(pick_rpm_file auto || true)"
          ;;
      esac
    fi
  fi

  if [ -z "${pkg_file}" ] || [ ! -f "${pkg_file}" ]; then
    echo "[install] 未找到可安装包，请先打包。" >&2
    echo "  deb 产物: COMPILE/dist/ubuntu*/*.deb" >&2
    echo "  rpm 产物: COMPILE/dist/centos-el{7,8,9}/*.rpm  COMPILE/dist/centos-arm-el{7,8,9}/*.rpm  COMPILE/dist/openeuler/*.rpm" >&2
    exit 1
  fi

  case "$pm" in
    deb) install_deb "$pkg_file" ;;
    rpm) install_rpm "$pkg_file" ;;
    *) echo "当前系统不支持自动安装（未检测到 dpkg/rpm）" >&2; exit 1 ;;
  esac
}

do_uninstall() {
  local pm="$1"
  case "$pm" in
    deb)
      echo "[uninstall] 使用 apt remove 卸载 ${PKG_NAME}"
      apt-get remove -y "${PKG_NAME}" || true
      ;;
    rpm)
      echo "[uninstall] 使用 rpm -e 卸载 ${PKG_NAME}"
      rpm -e "${PKG_NAME}" || true
      ;;
    *)
      echo "当前系统不支持自动卸载（未检测到 dpkg/rpm）" >&2
      exit 1
      ;;
  esac
  systemctl daemon-reload >/dev/null 2>&1 || true
  echo "[uninstall] 完成"
}

do_status() {
  local pm="$1"
  case "$pm" in
    deb)
      dpkg -s "${PKG_NAME}" 2>/dev/null | awk '/^Package:|^Status:|^Version:/{print}' || echo "${PKG_NAME} 未安装"
      ;;
    rpm)
      rpm -qi "${PKG_NAME}" 2>/dev/null | awk '/^Name|^Version|^Release|^Architecture|^Install Date/{print}' || echo "${PKG_NAME} 未安装"
      ;;
    *)
      echo "未检测到 dpkg/rpm"
      ;;
  esac
}

main() {
  local cmd="${1:-}"
  local pm
  pm="$(detect_pm)"

  case "$cmd" in
    ""|build|package|pack)
      exec "${SCRIPT_DIR}/interactive_pack.sh"
      ;;
    pack-all|pack_all|all-linux|linux-all)
      exec bash "${SCRIPT_DIR}/platforms/pack_all_linux.sh"
      ;;
    windows|win|pack-windows)
      shift || true
      exec bash "${SCRIPT_DIR}/build.sh" windows "$@"
      ;;
    install)
      do_install "$pm" "${2:-auto}" "${3:-}"
      ;;
    uninstall|remove)
      do_uninstall "$pm"
      ;;
    status)
      do_status "$pm"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "未知命令: $cmd" >&2
      usage
      exit 1
      ;;
  esac
}

main "$@"

