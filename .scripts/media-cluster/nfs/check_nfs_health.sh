#!/usr/bin/env bash
# NFS 共享媒体健康探测（iot-node SSH 检测 / 验收脚本）
set -euo pipefail

MOUNT_ROOT="${MOUNT_ROOT:-/mnt/easyaiot-media}"
NFS_SERVER="${NFS_SERVER:-127.0.0.1}"
NFS_EXPORT="${NFS_EXPORT:-${MOUNT_ROOT}}"

if command -v exportfs >/dev/null 2>&1; then
  echo NFS_SERVER_CLI_OK
  if exportfs -v 2>/dev/null | grep -q "${NFS_EXPORT}"; then
    echo NFS_EXPORT_OK
    exportfs -v 2>/dev/null | grep "${NFS_EXPORT}" | head -n 3 || true
  else
    echo NFS_EXPORT_MISSING
  fi
  if ss -ltn 2>/dev/null | grep -q ':2049'; then
    echo NFS_PORT_OK
  else
    echo NFS_PORT_MISSING
  fi
else
  echo NFS_SERVER_CLI_MISSING
fi

if mountpoint -q "${MOUNT_ROOT}" 2>/dev/null; then
  echo MOUNT_ROOT_OK
  df -h "${MOUNT_ROOT}" 2>/dev/null || true
  findmnt "${MOUNT_ROOT}" 2>/dev/null | head -n 2 || true
else
  echo MOUNT_ROOT_MISSING
fi

for sub in alert_images playbacks snaps; do
  if [[ -d "${MOUNT_ROOT}/${sub}" ]]; then
    echo "MOUNT_${sub^^}_OK"
  else
    echo "MOUNT_${sub^^}_MISSING"
  fi
done

echo CHECK_NFS_DONE
