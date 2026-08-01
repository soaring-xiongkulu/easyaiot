#!/usr/bin/env bash
# EasyAIoT COMPILE 交互式打包管理脚本
#
# 用法：
#   cd easyaiot && bash COMPILE/interactive_pack.sh
#   # 或：bash COMPILE/install_linux.sh
#
# 交互选择：
#   1) 操作类型：部署操作 / 安装操作
#   2) 部署操作：目标平台（Ubuntu/CentOS/Windows/全量Linux）+ 输出类型
#   3) 安装操作：安装 / 卸载 / 状态（deb/rpm）
#
# 默认构建方式（Linux 目标）：
#   - docker（不再交互询问）
#   - 如需本地构建，可在执行前导出：COMPILE_BUILD_MODE=local
# 快捷命令：
#   bash COMPILE/install_linux.sh pack-all
#   bash COMPILE/install_linux.sh windows [--installer]
#   bash COMPILE/build.sh all-linux

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

is_windows_host() {
  [[ "${OS:-}" == "Windows_NT" ]] && return 0
  case "$(uname -s 2>/dev/null || true)" in
    MINGW*|MSYS*|CYGWIN*) return 0 ;;
  esac
  return 1
}

choose_one() {
  local prompt="$1"
  shift
  local options=("$@")

  echo "" >&2
  echo "== ${prompt} ==" >&2
  local i=1
  for opt in "${options[@]}"; do
    echo "  ${i}) ${opt}" >&2
    i=$((i + 1))
  done
  echo "  0) 退出" >&2

  local choice=""
  read -r -p "请选择 [0-${#options[@]}]: " choice
  if [[ -z "${choice}" ]]; then
    echo "未选择，退出。" >&2
    exit 0
  fi
  if [[ "${choice}" == "0" ]]; then
    exit 0
  fi
  if ! [[ "${choice}" =~ ^[0-9]+$ ]]; then
    echo "输入无效：${choice}" >&2
    exit 1
  fi
  if (( choice < 1 || choice > ${#options[@]} )); then
    echo "选择越界：${choice}" >&2
    exit 1
  fi
  echo "${options[$((choice - 1))]}"
}

target_to_dist_dir() {
  local target="$1"
  case "$target" in
    ubuntu-x86|ubuntu-amd64) echo "${REPO_ROOT}/COMPILE/dist/ubuntu" ;;
    ubuntu-arm)              echo "${REPO_ROOT}/COMPILE/dist/ubuntu-arm" ;;
    ubuntu-kylin)            echo "${REPO_ROOT}/COMPILE/dist/ubuntu-kylin" ;;
    centos)                  echo "${REPO_ROOT}/COMPILE/dist/centos" ;;
    windows)                 echo "${REPO_ROOT}/COMPILE/dist/windows" ;;
    macos)                   echo "${REPO_ROOT}/COMPILE/dist/macos" ;;
    *) echo "${REPO_ROOT}/COMPILE/dist/ubuntu" ;;
  esac
}

build_once() {
  local target="$1"
  local mode="$2"   # docker|local（windows 忽略）
  local want_pkg="$3" # 0/1  （ubuntu: deb；centos: rpm；windows: NSIS）

  local cmd=(bash "${REPO_ROOT}/COMPILE/build.sh" "${target}")
  if [[ "$target" == "windows" ]]; then
    if [[ "${want_pkg}" == "1" ]]; then
      cmd+=("--installer")
    fi
  else
    if [[ "${mode}" == "local" ]]; then
      cmd+=("--local")
    fi
    if [[ "${want_pkg}" == "1" ]]; then
      case "$target" in
        centos) ;; # centos 默认打 rpm；--no-rpm 才跳过
        *) cmd+=("--deb") ;;
      esac
    elif [[ "$target" == "centos" ]]; then
      cmd+=("--no-rpm")
    fi
  fi

  echo ""
  echo "将执行："
  printf '  %q ' "${cmd[@]}"
  echo ""

  (cd "${REPO_ROOT}" && "${cmd[@]}")
}

run_pack_all_linux() {
  echo ""
  echo "将执行：bash COMPILE/platforms/pack_all_linux.sh"
  echo "（依次：ubuntu-x86/arm/kylin --deb + centos；日志在 COMPILE/work/logs/）"
  (cd "${REPO_ROOT}" && bash COMPILE/platforms/pack_all_linux.sh)
}

run_windows_flow() {
  if ! is_windows_host; then
    echo "[pack] Windows 打包须在 Windows 主机执行（Git Bash / PowerShell / CMD）。" >&2
    echo "  请在 Windows 上运行：bash COMPILE/install_linux.sh windows [--installer]" >&2
    exit 1
  fi

  local out
  out="$(choose_one "选择输出类型（Windows）" \
    "仅.exe+runtime" ".exe+runtime+NSIS安装包")"
  case "$out" in
    仅.exe+runtime) build_once windows local 0 ;;
    .exe+runtime+NSIS安装包) build_once windows local 1 ;;
    *) echo "未知输出类型：$out"; exit 1 ;;
  esac

  local dist_dir
  dist_dir="$(target_to_dist_dir windows)"
  echo ""
  echo "产物目录：${dist_dir}"
  ls -lh "${dist_dir}/easyaiot-panel.exe" 2>/dev/null || true
  ls -ld "${dist_dir}/runtime" 2>/dev/null || true
  ls -lh "${dist_dir}"/*.exe 2>/dev/null || true
  echo "Windows 打包完成。运行：${dist_dir}/run.bat"
}

run_macos_flow() {
  if [[ "$(uname -s 2>/dev/null || true)" != "Darwin" ]]; then
    echo "[pack] macOS 打包须在 macOS 主机执行。" >&2
    echo "  请运行：bash COMPILE/build.sh macos --dmg" >&2
    exit 1
  fi

  local out dist_dir
  out="$(choose_one "选择输出类型（macOS）" \
    "仅二进制+runtime" ".app" ".app+.dmg安装包")"
  case "$out" in
    仅二进制+runtime)
      (cd "${REPO_ROOT}" && bash COMPILE/build.sh macos)
      ;;
    .app)
      (cd "${REPO_ROOT}" && bash COMPILE/build.sh macos --app)
      ;;
    .app+.dmg安装包)
      (cd "${REPO_ROOT}" && bash COMPILE/build.sh macos --dmg)
      ;;
    *) echo "未知输出类型：$out"; exit 1 ;;
  esac

  dist_dir="$(target_to_dist_dir macos)"
  echo ""
  echo "产物目录：${dist_dir}"
  ls -lh "${dist_dir}/easyaiot-panel" 2>/dev/null || true
  ls -ld "${dist_dir}/runtime" 2>/dev/null || true
  ls -ld "${dist_dir}/EasyAIoT Panel.app" 2>/dev/null || true
  ls -lh "${dist_dir}"/easyaiot-panel-*.dmg 2>/dev/null || true
  echo "macOS 打包完成。图标为圆形白底（与 Linux 一致）。"
}

run_deploy_flow() {
  local target mode out dist_dir
  target="$(choose_one "选择打包目标" \
    "ubuntu-x86" "ubuntu-arm" "ubuntu-kylin" "centos" "windows" "macos" \
    "全量Linux(ubuntu×3 deb + centos rpm)")"

  if [[ "$target" == "全量Linux(ubuntu×3 deb + centos rpm)" ]]; then
    run_pack_all_linux
    return
  fi
  if [[ "$target" == "windows" ]]; then
    run_windows_flow
    return
  fi
  if [[ "$target" == "macos" ]]; then
    run_macos_flow
    return
  fi

  mode="${COMPILE_BUILD_MODE:-docker}"
  if [[ "${mode}" != "docker" && "${mode}" != "local" ]]; then
    echo "无效 COMPILE_BUILD_MODE=${mode}，已回退为 docker。" >&2
    mode="docker"
  fi
  echo "构建方式：${mode}（默认不交互；可通过 COMPILE_BUILD_MODE 覆盖）" >&2

  if [[ "$target" == "centos" ]]; then
    out="$(choose_one "选择输出类型（CentOS）" \
      "仅二进制" "二进制+rpm安装包")"
    case "$out" in
      仅二进制) build_once "$target" "$mode" "0" ;;
      二进制+rpm安装包) build_once "$target" "$mode" "1" ;;
      *) echo "未知输出类型：$out"; exit 1 ;;
    esac
  else
    out="$(choose_one "选择输出类型" \
      "仅二进制" "仅deb安装包" "二进制+deb安装包")"
    case "$out" in
      仅二进制) build_once "$target" "$mode" "0" ;;
      仅deb安装包) build_once "$target" "$mode" "1" ;;
      二进制+deb安装包)
        build_once "$target" "$mode" "0"
        build_once "$target" "$mode" "1"
        ;;
      *) echo "未知输出类型：$out"; exit 1 ;;
    esac
  fi

  dist_dir="$(target_to_dist_dir "$target")"
  echo ""
  echo "产物目录：${dist_dir}"
  echo "二进制："
  ls -lh "${dist_dir}/easyaiot-panel" 2>/dev/null || true
  if [[ "$target" == "centos" ]]; then
    echo "rpm："
    ls -lh "${dist_dir}"/easyaiot-panel-*.rpm 2>/dev/null || true
  else
    echo "deb："
    ls -lh "${dist_dir}"/easyaiot-panel_*.deb 2>/dev/null || true
  fi
  echo "部署打包完成。"
}

run_install_flow() {
  local action target_hint
  action="$(choose_one "选择安装操作" \
    "安装/覆盖安装" "卸载" "查看状态")"

  case "$action" in
    安装/覆盖安装)
      target_hint="$(choose_one "选择安装包目标" \
        "自动识别" "x86" "arm" "麒麟")"
      case "$target_hint" in
        自动识别) target_hint="auto" ;;
        麒麟) target_hint="kylin" ;;
      esac
      echo ""
      echo "将执行：bash COMPILE/install_linux.sh install ${target_hint}"
      (cd "${REPO_ROOT}" && bash COMPILE/install_linux.sh install "${target_hint}")
      ;;
    卸载)
      echo ""
      echo "将执行：bash COMPILE/install_linux.sh uninstall"
      (cd "${REPO_ROOT}" && bash COMPILE/install_linux.sh uninstall)
      ;;
    查看状态)
      echo ""
      echo "将执行：bash COMPILE/install_linux.sh status"
      (cd "${REPO_ROOT}" && bash COMPILE/install_linux.sh status)
      ;;
    *)
      echo "未知安装操作: ${action}" >&2
      exit 1
      ;;
  esac
  echo "安装管理操作完成。"
}

main_op="$(choose_one "选择操作类型" \
  "部署操作" "安装操作")"

case "$main_op" in
  部署操作)
    run_deploy_flow
    ;;
  安装操作)
    run_install_flow
    ;;
  *)
    echo "未知操作类型: ${main_op}" >&2
    exit 1
    ;;
esac
