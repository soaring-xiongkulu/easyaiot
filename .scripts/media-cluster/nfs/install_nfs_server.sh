#!/usr/bin/env bash
# NFS 服务端：export 共享媒体根（唯一存储方式）
set -euo pipefail

MOUNT_ROOT="${MOUNT_ROOT:-/mnt/easyaiot-media}"
NFS_EXPORT="${NFS_EXPORT:-${MOUNT_ROOT}}"

export DEBIAN_FRONTEND=noninteractive
if ! command -v exportfs >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq nfs-kernel-server rpcbind keyutils
fi

mkdir -p "${NFS_EXPORT}"/{alert_images,playbacks,snaps,playbacks/live,playbacks/ai,playbacks/gb28181,logs}
chmod -R 0777 "${NFS_EXPORT}" || true

LINE="${NFS_EXPORT} *(rw,sync,no_subtree_check,no_root_squash,insecure)"
if ! grep -Fq "${NFS_EXPORT}" /etc/exports 2>/dev/null; then
  echo "${LINE}" >> /etc/exports
fi

exportfs -ra
systemctl enable --now rpcbind nfs-server 2>/dev/null || systemctl restart nfs-kernel-server
sleep 1
exportfs -v | head -n 5 || true
echo NFS_SERVER_OK
