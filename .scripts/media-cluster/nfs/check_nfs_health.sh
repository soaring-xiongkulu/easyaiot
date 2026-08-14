#!/usr/bin/env bash
# NFS 共享媒体健康探测（iot-node SSH 检测 / 验收脚本）
# 输出 token 供 NodeStorageServiceImpl.probeHealth 解析
set -euo pipefail

MOUNT_ROOT="${MOUNT_ROOT:-/mnt/easyaiot-media}"
NFS_SERVER="${NFS_SERVER:-127.0.0.1}"
NFS_EXPORT="${NFS_EXPORT:-${MOUNT_ROOT}}"

_nfs_local_ips() {
  hostname -I 2>/dev/null | tr ' ' '\n' | grep -v '^$' || true
}

_is_local_nfs_server() {
  local server="$1"
  server="$(echo "$server" | tr -d '[:space:]')"
  [ -z "$server" ] && return 0
  case "$server" in
    127.0.0.1|localhost|::1) return 0 ;;
  esac
  _nfs_local_ips | grep -Fxq "$server"
}

if _is_local_nfs_server "${NFS_SERVER}"; then
  echo NFS_ROLE_SERVER
else
  echo NFS_ROLE_CLIENT
fi

if command -v exportfs >/dev/null 2>&1; then
  echo NFS_SERVER_CLI_OK
  if exportfs -v 2>/dev/null | grep -q "${NFS_EXPORT}"; then
    echo NFS_EXPORT_OK
    exportfs -v 2>/dev/null | grep "${NFS_EXPORT}" | head -n 3 || true
  else
    # 纯客户端节点通常无 export；本机角色才视为缺失
    if _is_local_nfs_server "${NFS_SERVER}"; then
      echo NFS_EXPORT_MISSING
    else
      echo NFS_EXPORT_SKIP_CLIENT
    fi
  fi
  if ss -ltn 2>/dev/null | grep -q ':2049'; then
    echo NFS_PORT_OK
  else
    if _is_local_nfs_server "${NFS_SERVER}"; then
      echo NFS_PORT_MISSING
    else
      echo NFS_PORT_SKIP_CLIENT
    fi
  fi
else
  if _is_local_nfs_server "${NFS_SERVER}"; then
    echo NFS_SERVER_CLI_MISSING
  else
    echo NFS_SERVER_CLI_SKIP_CLIENT
  fi
fi

_run_with_timeout() {
  local secs="$1"
  shift
  if ! command -v timeout >/dev/null 2>&1; then
    "$@"
    return $?
  fi
  if timeout --help 2>&1 | grep -q -- '--foreground'; then
    timeout --foreground -k 3 "${secs}" "$@"
  else
    timeout -k 3 "${secs}" "$@"
  fi
}

_is_mountpoint_safe() {
  local path="$1"
  if command -v findmnt >/dev/null 2>&1; then
    [ "$(findmnt -n -o TARGET "$path" 2>/dev/null || true)" = "$path" ]
    return $?
  fi
  awk -v p="$path" '$5 == p { found=1 } END { exit found ? 0 : 1 }' /proc/self/mountinfo 2>/dev/null
}

_probe_rw() {
  local probe_file="${MOUNT_ROOT}/.nfs_probe_$$"
  if _run_with_timeout 8 touch "${probe_file}" 2>/dev/null; then
    _run_with_timeout 5 rm -f "${probe_file}" 2>/dev/null || true
    echo MOUNT_RW_OK
  else
    echo MOUNT_RW_FAIL
  fi
}

EXPECTED_SRC="${NFS_SERVER}:${NFS_EXPORT}"
if _is_mountpoint_safe "${MOUNT_ROOT}"; then
  echo MOUNT_ROOT_OK
  _run_with_timeout 8 df -h "${MOUNT_ROOT}" 2>/dev/null || true
  findmnt "${MOUNT_ROOT}" 2>/dev/null | head -n 2 || true

  CURRENT_SRC="$(findmnt -n -o SOURCE "${MOUNT_ROOT}" 2>/dev/null || true)"
  CURRENT_FSTYPE="$(findmnt -n -o FSTYPE "${MOUNT_ROOT}" 2>/dev/null || true)"
  echo "MOUNT_SOURCE=${CURRENT_SRC}"

  case "${CURRENT_FSTYPE}" in
    nfs|nfs4) echo MOUNT_FSTYPE_OK ;;
    *)
      # 本机 bind / 本地目录：单机回退可接受
      if _is_local_nfs_server "${NFS_SERVER}"; then
        echo MOUNT_FSTYPE_LOCAL_OK
      else
        echo MOUNT_FSTYPE_OTHER
      fi
      ;;
  esac

  source_ok=0
  if [ -n "${CURRENT_SRC}" ]; then
    case "${CURRENT_SRC}" in
      "${EXPECTED_SRC}"|*":${NFS_EXPORT}")
        # 远端：要求 host 匹配或至少 export 路径一致且为本机角色
        if [[ "${CURRENT_SRC}" == "${EXPECTED_SRC}" ]]; then
          source_ok=1
        elif _is_local_nfs_server "${NFS_SERVER}"; then
          # 本机：127.0.0.1:/path 或任意本机 IP:/path 或本地设备
          source_ok=1
        else
          # 远端客户端：SOURCE 形如 host:export
          src_host="${CURRENT_SRC%%:*}"
          src_export="${CURRENT_SRC#*:}"
          if [ "${src_export}" = "${NFS_EXPORT}" ] && [ "${src_host}" = "${NFS_SERVER}" ]; then
            source_ok=1
          fi
        fi
        ;;
      *)
        if _is_local_nfs_server "${NFS_SERVER}"; then
          # bind mount / 本地块设备：单机可接受
          source_ok=1
        fi
        ;;
    esac
  elif _is_local_nfs_server "${NFS_SERVER}"; then
    source_ok=1
  fi

  if [ "${source_ok}" -eq 1 ]; then
    echo MOUNT_SOURCE_OK
  else
    echo MOUNT_SOURCE_MISMATCH
  fi

  _probe_rw
else
  echo MOUNT_ROOT_MISSING
  # 未挂载时：本机若目录可写且存在（local_bind 回退），仍给 LOCAL_BIND 提示
  if _is_local_nfs_server "${NFS_SERVER}" && [ -d "${MOUNT_ROOT}" ] && [ -w "${MOUNT_ROOT}" ]; then
    echo MOUNT_LOCAL_BIND_OK
    _probe_rw
  fi
fi

for sub in alert_images playbacks snaps; do
  sub_upper="$(echo "$sub" | tr '[:lower:]' '[:upper:]')"
  # 目录探测也加超时，避免僵死 NFS 卡住验收
  if _run_with_timeout 5 test -d "${MOUNT_ROOT}/${sub}"; then
    echo "MOUNT_${sub_upper}_OK"
  else
    echo "MOUNT_${sub_upper}_MISSING"
  fi
done

echo CHECK_NFS_DONE
