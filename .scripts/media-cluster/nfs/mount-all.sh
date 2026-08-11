#!/usr/bin/env bash
# 客户端挂载 NFS 并初始化子目录
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
bash "${SCRIPT_DIR}/install_nfs_client.sh"
echo "NFS ${NFS_SERVER:-127.0.0.1}:${NFS_EXPORT:-/mnt/easyaiot-media} mounted at ${MOUNT_ROOT:-/mnt/easyaiot-media}"
