#!/usr/bin/env bash
# NFS 客户端挂载（唯一存储方式；未指定 NFS_SERVER 时默认本机 export）
set -euo pipefail

MOUNT_ROOT="${MOUNT_ROOT:-/mnt/easyaiot-media}"
NFS_SERVER="${NFS_SERVER:-127.0.0.1}"
NFS_EXPORT="${NFS_EXPORT:-${MOUNT_ROOT}}"
NFS_MOUNT_OPTS="${NFS_MOUNT_OPTS:-vers=3,tcp,nolock,_netdev}"

export DEBIAN_FRONTEND=noninteractive
if ! command -v mount.nfs >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq nfs-common rpcbind
fi

mkdir -p "${MOUNT_ROOT}" "${MOUNT_ROOT}/playbacks" "${MOUNT_ROOT}/snaps" "${MOUNT_ROOT}/logs"
mkdir -p \
  "${MOUNT_ROOT}/playbacks/live" \
  "${MOUNT_ROOT}/playbacks/ai" \
  "${MOUNT_ROOT}/playbacks/gb28181" \
  "${MOUNT_ROOT}/snaps" \
  "${MOUNT_ROOT}/alert_images"

EXPECTED_SRC="${NFS_SERVER}:${NFS_EXPORT}"
if mountpoint -q "${MOUNT_ROOT}" 2>/dev/null; then
  CURRENT_SRC="$(findmnt -n -o SOURCE "${MOUNT_ROOT}" 2>/dev/null || true)"
  if [ -n "${CURRENT_SRC}" ] && [[ "${CURRENT_SRC}" == *":${NFS_EXPORT}" ]]; then
    df -h "${MOUNT_ROOT}"
    echo CLIENT_MOUNT_ALREADY_OK
    exit 0
  fi
  umount "${MOUNT_ROOT}" || true
fi

mount -t nfs -o "${NFS_MOUNT_OPTS}" "${EXPECTED_SRC}" "${MOUNT_ROOT}"

df -h "${MOUNT_ROOT}"
echo CLIENT_MOUNT_OK
