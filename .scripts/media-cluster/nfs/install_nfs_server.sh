#!/usr/bin/env bash
# NFS 服务端：export 共享媒体根（唯一存储方式）
set -euo pipefail

MOUNT_ROOT="${MOUNT_ROOT:-/mnt/easyaiot-media}"
NFS_EXPORT="${NFS_EXPORT:-${MOUNT_ROOT}}"
NFS_SERVER_READY_TIMEOUT="${NFS_SERVER_READY_TIMEOUT:-30}"

_run_with_timeout() {
  local secs="$1"
  shift
  if ! command -v timeout >/dev/null 2>&1; then
    "$@"
    return $?
  fi
  if timeout --help 2>&1 | grep -q -- '--foreground'; then
    timeout --foreground -k 5 "${secs}" "$@"
  else
    timeout -k 5 "${secs}" "$@"
  fi
}

_port_listening() {
  local port="${1:-2049}"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -qE ":${port}[[:space:]]"
    return $?
  fi
  if command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | grep -qE ":${port}[[:space:]]"
    return $?
  fi
  return 1
}

_wait_nfs_port() {
  local waited=0
  while [ "$waited" -lt "$NFS_SERVER_READY_TIMEOUT" ]; do
    if _port_listening 2049; then
      echo "NFS_PORT_READY waited=${waited}s"
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  echo "错误: nfs-server 在 ${NFS_SERVER_READY_TIMEOUT}s 内未监听 2049" >&2
  return 1
}

export DEBIAN_FRONTEND=noninteractive
if ! command -v exportfs >/dev/null 2>&1; then
  _run_with_timeout 180 apt-get update -qq || true
  _run_with_timeout 300 apt-get install -y -qq nfs-kernel-server rpcbind keyutils
fi

mkdir -p "${NFS_EXPORT}"/{alert_images,playbacks,snaps,playbacks/live,playbacks/ai,playbacks/gb28181,logs}
chmod -R 0777 "${NFS_EXPORT}" || true

LINE="${NFS_EXPORT} *(rw,sync,no_subtree_check,no_root_squash,insecure)"
if ! grep -Fq "${NFS_EXPORT}" /etc/exports 2>/dev/null; then
  echo "${LINE}" >> /etc/exports
fi

exportfs -ra
systemctl enable --now rpcbind 2>/dev/null || true
systemctl enable --now nfs-server 2>/dev/null \
  || systemctl enable --now nfs-kernel-server 2>/dev/null \
  || systemctl restart nfs-kernel-server 2>/dev/null \
  || systemctl restart nfs-server 2>/dev/null \
  || true

# 等端口就绪，避免客户端立刻 mount 时硬阻塞
_wait_nfs_port

exportfs -v | head -n 5 || true
echo NFS_SERVER_OK
