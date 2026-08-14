#!/usr/bin/env bash
# NFS 客户端挂载（唯一存储方式；未指定 NFS_SERVER 时默认本机 export）
# 挂载必须有超时：默认硬挂载在服务端不可达时会无限阻塞，导致一键部署卡死。
set -euo pipefail

MOUNT_ROOT="${MOUNT_ROOT:-/mnt/easyaiot-media}"
NFS_SERVER="${NFS_SERVER:-}"
NFS_EXPORT="${NFS_EXPORT:-${MOUNT_ROOT}}"
# soft + timeo/retrans/retry：挂载与短暂不可达时快速失败，避免部署卡死
# timeo 单位为 0.1 秒（50 = 5s）；retry 为分钟级重试上限（1 = 最多约 1 分钟）
NFS_MOUNT_OPTS="${NFS_MOUNT_OPTS:-vers=3,tcp,nolock,_netdev,soft,timeo=50,retrans=2,retry=1}"
NFS_MOUNT_TIMEOUT="${NFS_MOUNT_TIMEOUT:-45}"
NFS_PROBE_TIMEOUT="${NFS_PROBE_TIMEOUT:-8}"

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

_nfs_port_reachable() {
  local host="$1"
  local port="${2:-2049}"
  if command -v nc >/dev/null 2>&1; then
    _run_with_timeout "${NFS_PROBE_TIMEOUT}" nc -z -w "${NFS_PROBE_TIMEOUT}" "$host" "$port" >/dev/null 2>&1
    return $?
  fi
  if command -v bash >/dev/null 2>&1; then
    _run_with_timeout "${NFS_PROBE_TIMEOUT}" bash -c "echo >/dev/tcp/${host}/${port}" 2>/dev/null
    return $?
  fi
  return 0
}

_is_mountpoint_proc() {
  local path="$1"
  # 读 mountinfo，避免对僵死 NFS 做 stat（mountpoint -q 会卡死）
  if command -v findmnt >/dev/null 2>&1; then
    [ "$(findmnt -n -o TARGET "$path" 2>/dev/null || true)" = "$path" ]
    return $?
  fi
  awk -v p="$path" '$5 == p { found=1 } END { exit found ? 0 : 1 }' /proc/self/mountinfo 2>/dev/null
}

if [ -z "${NFS_SERVER}" ]; then
  echo "错误: NFS_SERVER 未设置。请先在「NFS 拓扑」分配主服务端，或 export NFS_SERVER=<主节点IP>" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
if ! command -v mount.nfs >/dev/null 2>&1; then
  _run_with_timeout 180 apt-get update -qq || true
  _run_with_timeout 300 apt-get install -y -qq nfs-common rpcbind
fi

EXPECTED_SRC="${NFS_SERVER}:${NFS_EXPORT}"

# 已正确挂载则直接成功（findmnt 不触盘）
if _is_mountpoint_proc "${MOUNT_ROOT}"; then
  CURRENT_SRC="$(findmnt -n -o SOURCE "${MOUNT_ROOT}" 2>/dev/null || true)"
  if [ -n "${CURRENT_SRC}" ] && [[ "${CURRENT_SRC}" == *":${NFS_EXPORT}" || "${CURRENT_SRC}" == "${EXPECTED_SRC}" ]]; then
    _run_with_timeout 10 df -h "${MOUNT_ROOT}" || true
    echo CLIENT_MOUNT_ALREADY_OK
    exit 0
  fi
  echo "NFS_UMOUNT_STALE ${MOUNT_ROOT} (current=${CURRENT_SRC:-unknown})"
  _run_with_timeout 20 umount -l "${MOUNT_ROOT}" 2>/dev/null || _run_with_timeout 20 umount -f "${MOUNT_ROOT}" 2>/dev/null || true
fi

# 挂载前探测 2049，避免 mount 在不可达服务端上硬阻塞
echo "NFS_PROBE ${NFS_SERVER}:2049 (timeout=${NFS_PROBE_TIMEOUT}s)"
if ! _nfs_port_reachable "${NFS_SERVER}" 2049; then
  echo "错误: NFS 服务端 ${NFS_SERVER}:2049 不可达（${NFS_PROBE_TIMEOUT}s 内无响应）。" >&2
  echo "  请确认 nfs-server/rpcbind 已启动，或检查 NFS_SERVER / 防火墙。" >&2
  exit 1
fi

mkdir -p "${MOUNT_ROOT}"

echo "NFS_MOUNT ${EXPECTED_SRC} -> ${MOUNT_ROOT} opts=${NFS_MOUNT_OPTS} timeout=${NFS_MOUNT_TIMEOUT}s"
if ! _run_with_timeout "${NFS_MOUNT_TIMEOUT}" \
  mount -t nfs -o "${NFS_MOUNT_OPTS}" "${EXPECTED_SRC}" "${MOUNT_ROOT}"; then
  echo "错误: NFS 挂载超时或失败（${NFS_MOUNT_TIMEOUT}s）: ${EXPECTED_SRC} -> ${MOUNT_ROOT}" >&2
  exit 1
fi

mkdir -p \
  "${MOUNT_ROOT}/playbacks" \
  "${MOUNT_ROOT}/playbacks/live" \
  "${MOUNT_ROOT}/playbacks/ai" \
  "${MOUNT_ROOT}/playbacks/gb28181" \
  "${MOUNT_ROOT}/snaps" \
  "${MOUNT_ROOT}/alert_images" \
  "${MOUNT_ROOT}/logs"

_run_with_timeout 10 df -h "${MOUNT_ROOT}" || true
echo CLIENT_MOUNT_OK
