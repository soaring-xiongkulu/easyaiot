#!/usr/bin/env bash
# EasyAIoT 集群模式一键启用：CephFS 挂载 + 目录初始化 + 环境变量模板
#
# 用法（在已加入 Ceph 集群的节点上）:
#   export CEPH_MON=storage-ceph
#   bash .scripts/media-cluster/enable_cluster_mode.sh
#
# 可选：仅生成 env 片段而不挂载
#   GENERATE_ENV_ONLY=1 bash .scripts/media-cluster/enable_cluster_mode.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MOUNT_ROOT="${MOUNT_ROOT:-/mnt/easyaiot-media}"
CEPH_MON="${CEPH_MON:-storage-ceph}"
CEPHFS_NAME="${CEPHFS_NAME:-easyaiot}"

print_step() { echo ">>> $*"; }
print_ok() { echo "[OK] $*"; }

if [[ "${GENERATE_ENV_ONLY:-0}" != "1" ]]; then
  print_step "挂载 CephFS 到 ${MOUNT_ROOT}"
  bash "${SCRIPT_DIR}/ceph/mount-all.sh"
  print_ok "CephFS 挂载完成"
fi

print_step "创建集群目录结构"
mkdir -p \
  "${MOUNT_ROOT}/playbacks/live" \
  "${MOUNT_ROOT}/playbacks/ai" \
  "${MOUNT_ROOT}/playbacks/gb28181" \
  "${MOUNT_ROOT}/snaps" \
  "${MOUNT_ROOT}/staging" \
  "${MOUNT_ROOT}/ai/datasets/uploads" \
  "${MOUNT_ROOT}/ai/models" \
  "${MOUNT_ROOT}/ai/train" \
  "${MOUNT_ROOT}/alert_images" \
  "${MOUNT_ROOT}/logs"
print_ok "目录结构就绪"

ENV_SNIPPET="${REPO_ROOT}/.scripts/media-cluster/cluster.env.snippet"
cat > "${ENV_SNIPPET}" <<EOF
# EasyAIoT 集群模式环境变量（由 enable_cluster_mode.sh 生成）
# 将以下内容合并到 VIDEO/.env.prod、AI/.env.prod 或 docker compose env
CLUSTER_MODE=true
MEDIA_HOST_DATA_ROOT=${MOUNT_ROOT}
MEDIA_RECORD_DIR=${MOUNT_ROOT}/playbacks
MEDIA_SNAP_DIR=${MOUNT_ROOT}/snaps
MEDIA_STAGING_DIR=${MOUNT_ROOT}/staging
SRS_HOST_DATA_ROOT=${MOUNT_ROOT}
SRS_RECORD_DIR=${MOUNT_ROOT}/playbacks
SRS_DVR_DURATION_SECONDS=60
MEDIA_UPLOAD_MODE=kafka
MEDIA_NODE_POOL_ENABLED=true
AI_DATASETS_DIR=${MOUNT_ROOT}/ai/datasets
AI_MODELS_DIR=${MOUNT_ROOT}/ai/models
ALERT_IMAGES_DIR=${MOUNT_ROOT}/alert_images
CEPH_MOUNT_ROOT=${MOUNT_ROOT}
CEPH_MON=${CEPH_MON}
CEPHFS_NAME=${CEPHFS_NAME}
EOF
print_ok "环境变量片段已写入 ${ENV_SNIPPET}"

echo ""
echo "下一步："
echo "  1. 在 Ceph 管理节点执行: bash ${SCRIPT_DIR}/ceph/pool-create.sh"
echo "  2. 各业务/计算/媒体节点执行: bash ${SCRIPT_DIR}/ceph/mount-all.sh"
echo "  3. 合并 ${ENV_SNIPPET} 到 VIDEO/AI 配置并重启服务"
echo "  4. 启动 Upload Worker: python -m services.media_upload_worker (VIDEO 目录)"
echo "  5. 在 iot-node 控制台完成节点 Ceph 纳管与媒体栈部署"
