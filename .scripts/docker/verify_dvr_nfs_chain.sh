#!/bin/bash
# ============================================
# DVR 链路验收（NFS 写盘 → iot-sink Hook → MinIO → playback/record_path）
# ============================================
# 契约：
#   - NFS 为唯一媒体根（basiclab.media.mount-root / ALERT_IMAGES 同根）
#   - SRS/ZLM 写 /data/playbacks → sink 映射到 NFS mount-root
#   - VIDEO 仅转发 Hook 到 sink（/video/media/hook/srs/on_dvr）
#
# 用法：
#   NFS_MOUNT_ROOT=/tmp/easyaiot-nfs-mount ./verify_dvr_nfs_chain.sh
#   ./verify_dvr_nfs_chain.sh --gateway-only
#
# 环境变量：
#   NFS_MOUNT_ROOT     默认 /tmp/easyaiot-nfs-mount 或 /mnt/easyaiot-media
#   VERIFY_DEVICE_ID   默认 camera_atomic_001
#   SINK_HOOK_URL      默认 http://127.0.0.1:48092/media/hook/srs/on_dvr
#   GATEWAY_HOOK_URL   默认 http://127.0.0.1:48080/admin-api/sink/media/hook/srs/on_dvr
#   VIDEO_HOOK_URL     默认 http://127.0.0.1:6000/video/media/hook/srs/on_dvr
#   DOCKER_PG_CONTAINER 默认 postgres-server
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0

print_ok() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS + 1)); }
print_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL + 1)); }
print_skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; SKIP=$((SKIP + 1)); }
print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

NFS_MOUNT_ROOT="${NFS_MOUNT_ROOT:-}"
if [ -z "$NFS_MOUNT_ROOT" ]; then
    if mountpoint -q /mnt/easyaiot-media 2>/dev/null; then
        NFS_MOUNT_ROOT=/mnt/easyaiot-media
    elif [ -d /tmp/easyaiot-nfs-mount ]; then
        NFS_MOUNT_ROOT=/tmp/easyaiot-nfs-mount
    else
        NFS_MOUNT_ROOT=/mnt/easyaiot-media
    fi
fi

VERIFY_DEVICE_ID="${VERIFY_DEVICE_ID:-camera_atomic_001}"
SINK_HOOK_URL="${SINK_HOOK_URL:-http://127.0.0.1:48092/media/hook/srs/on_dvr}"
GATEWAY_HOOK_URL="${GATEWAY_HOOK_URL:-http://127.0.0.1:48080/admin-api/sink/media/hook/srs/on_dvr}"
VIDEO_HOOK_URL="${VIDEO_HOOK_URL:-http://127.0.0.1:6000/video/media/hook/srs/on_dvr}"
PG_CTR="${DOCKER_PG_CONTAINER:-postgres-server}"
MIN_BYTES=4096

GATEWAY_ONLY=0
while [ $# -gt 0 ]; do
    case "$1" in
        --gateway-only) GATEWAY_ONLY=1 ;;
        -h|--help)
            sed -n '2,22p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "未知参数: $1" >&2; exit 2 ;;
    esac
    shift
done

post_dvr() {
    local label="$1"
    local url="$2"
    local fn="$3"
    local payload
    payload=$(python3 - <<PY
import json
print(json.dumps({
    "stream": "${VERIFY_DEVICE_ID}",
    "device_id": "${VERIFY_DEVICE_ID}",
    "file_path": "/data/playbacks/live/${VERIFY_DEVICE_ID}/2026/08/11/${fn}",
    "cwd": "/data",
}))
PY
)
    local resp code
    resp=$(curl -sS -w '\n%{http_code}' -X POST "$url" -H 'Content-Type: application/json' -d "$payload" 2>/dev/null || echo "curl_error\n000")
    code=$(echo "$resp" | tail -1)
    body=$(echo "$resp" | sed '$d')
    if [ "$code" = "200" ] && echo "$body" | grep -q '"code":0'; then
        print_ok "${label} DVR Hook HTTP 200 code=0"
        return 0
    fi
    print_fail "${label} DVR Hook 失败 HTTP=${code} body=${body:0:120}"
    return 1
}

playback_count_before=0
if docker inspect -f '{{.State.Running}}' "$PG_CTR" 2>/dev/null | grep -q true; then
    playback_count_before=$(docker exec "$PG_CTR" psql -U postgres -d iot-video20 -t -A -c \
        "SELECT count(*) FROM playback WHERE device_id='${VERIFY_DEVICE_ID}';" 2>/dev/null | tr -d '[:space:]' || echo 0)
fi

print_section "NFS 挂载与 playbacks 目录"
if [ -d "${NFS_MOUNT_ROOT}/playbacks" ]; then
    print_ok "playbacks 目录存在: ${NFS_MOUNT_ROOT}/playbacks"
else
    print_fail "缺少 ${NFS_MOUNT_ROOT}/playbacks"
fi

if touch "${NFS_MOUNT_ROOT}/playbacks/.dvr_probe_$$" 2>/dev/null; then
    rm -f "${NFS_MOUNT_ROOT}/playbacks/.dvr_probe_$$"
    print_ok "playbacks 可写"
else
    print_fail "playbacks 不可写"
fi

print_section "iot-sink Media Hook 可达"
if curl -sf -X POST http://127.0.0.1:48092/media/hook/health >/dev/null 2>&1; then
    print_ok "sink /media/hook/health"
else
    print_fail "sink Media Hook 不可用（需新 jar 且 -Dbasiclab.media.mount-root=${NFS_MOUNT_ROOT}）"
fi

if curl -sf -X POST http://127.0.0.1:48080/admin-api/sink/media/hook/health >/dev/null 2>&1; then
    print_ok "Gateway → sink /media/hook/health"
else
    print_skip "Gateway Media Hook 不可达"
fi

print_section "DVR 上传 E2E"
PROBE_DIR="${NFS_MOUNT_ROOT}/playbacks/live/${VERIFY_DEVICE_ID}/2026/08/11"
mkdir -p "$PROBE_DIR"

run_one() {
    local label="$1"
    local url="$2"
    local fn="verify_${label}_$(date +%s)_${RANDOM}.flv"
    local fpath="${PROBE_DIR}/${fn}"
    dd if=/dev/urandom of="$fpath" bs=4096 count=4 status=none 2>/dev/null || return 1
    if [ ! -f "$fpath" ] || [ "$(stat -c%s "$fpath" 2>/dev/null || echo 0)" -lt "$MIN_BYTES" ]; then
        print_fail "${label} 探针文件创建失败"
        return 1
    fi
    post_dvr "$label" "$url" "$fn" || return 1
    sleep 2
    if [ ! -f "$fpath" ]; then
        print_ok "${label} NFS 本地文件已清理（上传后删除）"
    else
        print_skip "${label} NFS 文件仍在（可能上传失败或未开启 remove-local-after-upload）"
    fi
}

if [ "$GATEWAY_ONLY" -eq 0 ]; then
    run_one "sink_direct" "$SINK_HOOK_URL" || true
fi
run_one "gateway" "$GATEWAY_HOOK_URL" || true
run_one "video_forward" "$VIDEO_HOOK_URL" || true

print_section "playback 表断言"
if docker inspect -f '{{.State.Running}}' "$PG_CTR" 2>/dev/null | grep -q true; then
    playback_count_after=$(docker exec "$PG_CTR" psql -U postgres -d iot-video20 -t -A -c \
        "SELECT count(*) FROM playback WHERE device_id='${VERIFY_DEVICE_ID}';" 2>/dev/null | tr -d '[:space:]' || echo 0)
    if [ "${playback_count_after:-0}" -gt "${playback_count_before:-0}" ]; then
        print_ok "playback 新增 $((playback_count_after - playback_count_before)) 条 (total=${playback_count_after})"
        docker exec "$PG_CTR" psql -U postgres -d iot-video20 -c \
            "SELECT id, left(file_path,70) fp, file_size FROM playback WHERE device_id='${VERIFY_DEVICE_ID}' ORDER BY id DESC LIMIT 3;" 2>/dev/null || true
    else
        print_fail "playback 无新增 (before=${playback_count_before} after=${playback_count_after})"
    fi
else
    print_skip "postgres 容器未运行，跳过 playback 断言"
fi

echo ""
echo "汇总: PASS=${PASS} FAIL=${FAIL} SKIP=${SKIP}"
[ "$FAIL" -eq 0 ]
