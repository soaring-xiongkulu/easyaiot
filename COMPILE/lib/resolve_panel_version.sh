#!/usr/bin/env bash
# PANEL 打包版本解析：自动递增，不再依赖仓库根 VERSION 文件。
#
# 用法（由各平台 pack/build 脚本 source）:
#   source "${COMPILE_ROOT}/lib/resolve_panel_version.sh"
#   PANEL_VER="$(resolve_panel_version)"   # 纯数字，如 105
#
# 规则:
#   1) 若设置 PANEL_VERSION（如 V105 / 105），直接使用并回写状态
#   2) 否则取 max(状态文件 COMPILE/.panel-version, dist 已有包版本) + 1
#   3) 若均无记录，从 PANEL_VERSION_BASE（默认 100）起
#
# shellcheck shell=bash

_COMPILE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_COMPILE_ROOT_FOR_VER="$(cd "${_COMPILE_LIB_DIR}/.." && pwd)"
PANEL_VERSION_STATE="${PANEL_VERSION_STATE:-${_COMPILE_ROOT_FOR_VER}/.panel-version}"
PANEL_VERSION_BASE="${PANEL_VERSION_BASE:-100}"

normalize_panel_version() {
  local raw="${1:-}"
  raw="$(printf '%s' "$raw" | tr -d '[:space:]')"
  [ -n "$raw" ] || return 1
  if [[ "$raw" =~ ^[Vv]([0-9]+([.][0-9]+)*)$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "$raw" =~ ^[0-9]+([.][0-9]+)*$ ]]; then
    printf '%s\n' "$raw"
    return 0
  fi
  return 1
}

_version_rank() {
  # 把 1.2.3 转成可比较的整串；纯整数直接输出
  local v="$1"
  if [[ "$v" =~ ^[0-9]+$ ]]; then
    printf '%s\n' "$v"
    return 0
  fi
  local IFS='.'
  # shellcheck disable=SC2086
  set -- $v
  printf '%d%03d%03d\n' "${1:-0}" "${2:-0}" "${3:-0}"
}

_max_version() {
  local a="$1" b="$2"
  if [ -z "$a" ]; then
    printf '%s\n' "$b"
    return 0
  fi
  if [ -z "$b" ]; then
    printf '%s\n' "$a"
    return 0
  fi
  local ra rb
  ra="$(_version_rank "$a")"
  rb="$(_version_rank "$b")"
  if [ "$ra" -ge "$rb" ] 2>/dev/null; then
    printf '%s\n' "$a"
  else
    printf '%s\n' "$b"
  fi
}

_read_state_version() {
  local v=""
  if [ -f "$PANEL_VERSION_STATE" ]; then
    v="$(awk 'NF{print; exit}' "$PANEL_VERSION_STATE" 2>/dev/null || true)"
    normalize_panel_version "$v" 2>/dev/null || true
  fi
}

_scan_dist_max_version() {
  local dist_root="${_COMPILE_ROOT_FOR_VER}/dist"
  local max_v="" f base ver

  [ -d "$dist_root" ] || {
    printf '%s\n' ""
    return 0
  }

  shopt -s nullglob
  for f in \
    "${dist_root}"/ubuntu/easyaiot-panel_*.deb \
    "${dist_root}"/ubuntu-arm/easyaiot-panel_*.deb \
    "${dist_root}"/ubuntu-kylin/easyaiot-panel_*.deb \
    "${dist_root}"/ubuntu/easyaiot-panel-*.deb \
    "${dist_root}"/ubuntu-arm/easyaiot-panel-*.deb \
    "${dist_root}"/ubuntu-kylin/easyaiot-panel-*.deb \
    "${dist_root}"/centos/easyaiot-panel-*.rpm \
    "${dist_root}"/windows/easyaiot-panel-*-setup.exe \
    "${dist_root}"/macos/easyaiot-panel-*.dmg
  do
    base="$(basename "$f")"
    ver=""
    if [[ "$base" =~ ^easyaiot-panel_([0-9]+([.][0-9]+)*)_ ]]; then
      # deb：easyaiot-panel_<ver>_amd64.deb / _arm_arm64.deb / _kylin_arm64.deb
      ver="${BASH_REMATCH[1]}"
    elif [[ "$base" =~ ^easyaiot-panel-([0-9]+([.][0-9]+)*)-setup\.exe$ ]]; then
      ver="${BASH_REMATCH[1]}"
    elif [[ "$base" =~ ^easyaiot-panel-([0-9]+([.][0-9]+)*)-(arm64|amd64)\.dmg$ ]]; then
      # macOS：easyaiot-panel-<ver>-arm64.dmg / -amd64.dmg
      ver="${BASH_REMATCH[1]}"
    elif [[ "$base" =~ ^easyaiot-panel-([0-9]+([.][0-9]+)*)\.dmg$ ]]; then
      # 兼容旧 macOS 命名（无架构后缀）
      ver="${BASH_REMATCH[1]}"
    elif [[ "$base" =~ ^easyaiot-panel-([0-9]+([.][0-9]+)*)- ]]; then
      # rpm / 兼容曾用中横线的 deb、windows 命名
      ver="${BASH_REMATCH[1]}"
    fi
    if [ -n "$ver" ]; then
      max_v="$(_max_version "$max_v" "$ver")"
    fi
  done
  shopt -u nullglob
  printf '%s\n' "$max_v"
}

_write_state_version() {
  local v="$1"
  mkdir -p "$(dirname "$PANEL_VERSION_STATE")"
  printf 'V%s\n' "$v" > "$PANEL_VERSION_STATE"
}

# 解析并（默认）递增版本号；输出纯数字字符串
resolve_panel_version() {
  local forced="" current="" scanned="" next=""
  if [ -n "${PANEL_VERSION:-}" ]; then
    if ! forced="$(normalize_panel_version "$PANEL_VERSION")"; then
      echo "[COMPILE] 无效 PANEL_VERSION=${PANEL_VERSION}（期望如 105 或 V105）" >&2
      return 1
    fi
    _write_state_version "$forced"
    printf '%s\n' "$forced"
    return 0
  fi

  current="$(_read_state_version)"
  scanned="$(_scan_dist_max_version)"
  current="$(_max_version "$current" "$scanned")"

  if [ -z "$current" ]; then
    next="$PANEL_VERSION_BASE"
  elif [[ "$current" =~ ^[0-9]+$ ]]; then
    next="$((current + 1))"
  else
    # 非纯整数（如 1.2.3）时，在末段 +1
    local major minor patch
    IFS='.' read -r major minor patch <<<"${current}.0.0"
    patch="${patch:-0}"
    next="${major}.${minor}.$((patch + 1))"
  fi

  _write_state_version "$next"
  printf '%s\n' "$next"
}
