#!/usr/bin/env bash
# ============================================
# 将 /etc/os-release 映射为 RUNTIME 离线包的 os_family 键。
# 控制面按 {os_family}/{arch} 缓存制品，禁止把 Ubuntu 包发到 openEuler。
# ============================================

runtime_os_major() {
  local ver="${1:-}"
  ver="${ver#\"}"
  ver="${ver%\"}"
  ver="${ver#\'}"
  ver="${ver%\'}"
  if [[ "$ver" =~ ^([0-9]+) ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo "0"
  fi
}

# 用法: runtime_os_family_from <ID> <ID_LIKE> <VERSION_ID>
runtime_os_family_from() {
  local id="${1:-}"
  local like="${2:-}"
  local version_id="${3:-}"
  id="$(echo "$id" | tr '[:upper:]' '[:lower:]' | tr -d "\"'")"
  like="$(echo "$like" | tr '[:upper:]' '[:lower:]' | tr -d "\"'")"
  local major
  major="$(runtime_os_major "$version_id")"

  case "$id" in
    ubuntu)
      if [[ "$major" -gt 0 ]]; then echo "ubuntu${major}"; else echo "ubuntu"; fi
      return 0
      ;;
    debian)
      if [[ "$major" -gt 0 ]]; then echo "debian${major}"; else echo "debian"; fi
      return 0
      ;;
    openeuler)
      if [[ "$major" -gt 0 ]]; then echo "openeuler${major}"; else echo "openeuler"; fi
      return 0
      ;;
    kylin|kylinos|kylinsecos)
      if [[ "$major" -gt 0 ]]; then echo "kylin${major}"; else echo "kylin"; fi
      return 0
      ;;
  esac

  case "$id" in
    rhel|centos|rocky|almalinux|ol|alinux|opencloudos|anolis|tencentos)
      if [[ "$major" -ge 9 ]]; then echo "el9"
      elif [[ "$major" -eq 8 ]]; then echo "el8"
      elif [[ "$major" -eq 7 ]]; then echo "el7"
      else echo "el"; fi
      return 0
      ;;
  esac

  if [[ "$like" == *rhel* || "$like" == *centos* || "$like" == *fedora* ]]; then
    if [[ "$major" -ge 9 ]]; then echo "el9"
    elif [[ "$major" -eq 8 ]]; then echo "el8"
    elif [[ "$major" -eq 7 ]]; then echo "el7"
    else echo "el"; fi
    return 0
  fi

  local slug
  slug="$(echo "$id" | tr -cd 'a-z0-9')"
  if [[ -z "$slug" ]]; then
    echo "linux"
  elif [[ "$major" -gt 0 ]]; then
    echo "${slug}${major}"
  else
    echo "$slug"
  fi
}

runtime_detect_os_family() {
  if [[ -n "${RUNTIME_OS_FAMILY:-}" ]]; then
    echo "$RUNTIME_OS_FAMILY"
    return 0
  fi
  local id="" like="" version_id=""
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    id="${ID:-}"
    like="${ID_LIKE:-}"
    version_id="${VERSION_ID:-}"
  fi
  runtime_os_family_from "$id" "$like" "$version_id"
}

runtime_arch_key() {
  local m="${RUNTIME_ARCH:-$(uname -m)}"
  m="$(echo "$m" | tr '[:upper:]' '[:lower:]')"
  case "$m" in
    aarch64|arm64) echo "arm64" ;;
    *) echo "x86_64" ;;
  esac
}
