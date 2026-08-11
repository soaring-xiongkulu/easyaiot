#!/bin/bash
# ============================================
# 告警事件面链路验收（共享盘/Ceph 挂载 + MQTT→iot-sink→入库）
# ============================================
# 说明：
#   Ceph / 共享盘只保证 VIDEO 与 iot-sink 看到同一 ALERT_IMAGES_DIR；
#   业务正确性靠 MQTT 发布 + alert 表 correlation_id 断言（委托
#   VIDEO/tools/verify_alert_ingest_e2e.py）。
#
# 用法：
#   ./verify_alert_mqtt_chain.sh              # 共享盘探测 + 全量 E2E
#   ./verify_alert_mqtt_chain.sh --mount-only # 仅共享盘/挂载
#   ./verify_alert_mqtt_chain.sh --skip-media # E2E 不测 MinIO 归档
#   ./verify_alert_mqtt_chain.sh --contract-only
#
# 也可经统一入口：
#   .scripts/docker/install_linux.sh verify-alert
#
# 环境变量：
#   ALERT_IMAGES_DIR / MQTT_BROKER_URLS / VIDEO_BASE_URL / VERIFY_DEVICE_ID
#   DOCKER_PG_CONTAINER（默认 postgres-server）
#   EASYAIOT_VERIFY_ALERT_STRICT=1  — 前置缺失时失败（默认 soft：跳过并提示）
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"
ensure_deploy_profile >/dev/null 2>&1 || true

PASS=0
FAIL=0
SKIP=0

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_ok() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS + 1)); }
print_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL + 1)); }
print_skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; SKIP=$((SKIP + 1)); }
print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

STRICT="${EASYAIOT_VERIFY_ALERT_STRICT:-0}"
MOUNT_ONLY=0
E2E_ARGS=()

usage() {
    sed -n '2,25p' "$0" | sed 's/^# \?//'
}

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --mount-only) MOUNT_ONLY=1 ;;
        --skip-media|--contract-only) E2E_ARGS+=("$1") ;;
        --strict) STRICT=1 ;;
        *)
            echo "未知参数: $1" >&2
            usage
            exit 2
            ;;
    esac
    shift
done

_ALERT_CANDIDATE="${ALERT_IMAGES_DIR:-${PROJECT_ROOT}/VIDEO/alert_images}"
mkdir -p "${_ALERT_CANDIDATE}" 2>/dev/null || true
if [ -d "${_ALERT_CANDIDATE}" ]; then
    ALERT_HOST_DIR="$(cd "${_ALERT_CANDIDATE}" && pwd)"
else
    ALERT_HOST_DIR="${_ALERT_CANDIDATE}"
fi

VIDEO_CTR="${VIDEO_CONTAINER:-video-service}"
SINK_CTR="${SINK_CONTAINER:-iot-sink}"
PROBE_NAME=".easyaiot_alert_mount_probe_$$"
PROBE_CONTENT="easyaiot-alert-mount-$(date +%s)-$RANDOM"

container_running() {
    local name="$1"
    [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || echo false)" = "true" ]
}

container_mounts_alert() {
    local name="$1"
    docker inspect -f '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' "$name" 2>/dev/null \
        | grep -E 'alert_images|easyaiot-media|/mnt/easyaiot-media' >/dev/null 2>&1
}

check_shared_mount() {
    print_section "L-mount 共享告警目录（Ceph/本地盘同一契约）"
    print_info "宿主机 ALERT_IMAGES_DIR: ${ALERT_HOST_DIR}"
    print_info "部署形态: ${EASYAIOT_DEPLOY_PROFILE:-unknown}"

    mkdir -p "$ALERT_HOST_DIR" 2>/dev/null || true
    if [ -d "$ALERT_HOST_DIR" ] && [ -w "$ALERT_HOST_DIR" ]; then
        print_ok "宿主机告警目录可写"
    else
        print_fail "宿主机告警目录不可写: ${ALERT_HOST_DIR}"
        return 1
    fi

    local probe_host="${ALERT_HOST_DIR}/${PROBE_NAME}"
    printf '%s' "$PROBE_CONTENT" >"$probe_host"
    if [ -f "$probe_host" ]; then
        print_ok "宿主机写入探针文件成功"
    else
        print_fail "无法写入探针文件"
        return 1
    fi

    # VIDEO 容器：NFS 挂载 /mnt/easyaiot-media/alert_images
    local video_alert_in_ctr="/mnt/easyaiot-media/alert_images/${PROBE_NAME}"
    if container_running "$VIDEO_CTR"; then
        if container_mounts_alert "$VIDEO_CTR"; then
            print_ok "${VIDEO_CTR} 已挂载 NFS 媒体根"
        else
            print_fail "${VIDEO_CTR} 未发现 easyaiot-media 挂载"
        fi
        if docker exec "$VIDEO_CTR" sh -c "test -f ${video_alert_in_ctr}" 2>/dev/null; then
            local got
            got="$(docker exec "$VIDEO_CTR" sh -c "cat ${video_alert_in_ctr}" 2>/dev/null || true)"
            if [ "$got" = "$PROBE_CONTENT" ]; then
                print_ok "VIDEO 容器可读到同一探针（NFS 共享盘贯通）"
            else
                print_fail "VIDEO 容器能看到文件但内容不一致"
            fi
        else
            print_fail "VIDEO 容器内 ${video_alert_in_ctr} 不存在（NFS 挂载路径不一致）"
        fi
    else
        print_skip "${VIDEO_CTR} 未运行 — 跳过容器内读探针"
    fi

    # iot-sink：compose 挂 /mnt/easyaiot-media；本地 jar 用宿主机 NFS 路径
    local sink_alert_in_ctr="/mnt/easyaiot-media/alert_images/${PROBE_NAME}"
    if container_running "$SINK_CTR"; then
        if container_mounts_alert "$SINK_CTR"; then
            print_ok "${SINK_CTR} 已挂载 NFS 媒体根"
        else
            print_fail "${SINK_CTR} 未发现 easyaiot-media 挂载"
        fi
        if docker exec "$SINK_CTR" sh -c "test -f ${sink_alert_in_ctr}" 2>/dev/null; then
            local got_sink
            got_sink="$(docker exec "$SINK_CTR" sh -c "cat ${sink_alert_in_ctr}" 2>/dev/null || true)"
            if [ "$got_sink" = "$PROBE_CONTENT" ]; then
                print_ok "iot-sink 容器可读到同一探针（与 VIDEO 共享 NFS）"
            else
                print_fail "iot-sink 探针内容不一致"
            fi
        elif docker exec "$SINK_CTR" sh -c "test -f /app/alert_images/${PROBE_NAME}" 2>/dev/null; then
            print_skip "${SINK_CTR} 仍使用旧 /app/alert_images 挂载，请更新 compose 并重建容器"
        else
            if [ -f "$probe_host" ]; then
                print_skip "iot-sink 容器内无 NFS 探针；若为本地 jar，请保证 -Dalert.images.base-dir 指向 NFS alert_images"
            fi
        fi
    else
        # 本地进程监听 48092 也算 sink 在跑
        if ss -lntp 2>/dev/null | grep -q ':48092'; then
            print_skip "iot-sink 容器未运行，但 :48092 在听（本地 jar）— 共享盘以宿主机路径为准"
            print_ok "宿主机路径对本地 sink 可读（探针文件存在）"
        else
            print_skip "iot-sink 未运行 — 跳过 sink 挂载检查"
        fi
    fi

    rm -f "$probe_host" 2>/dev/null || true
    return 0
}

check_prereq_ports() {
    print_section "前置端口"
    local mqtt_host mqtt_port
    mqtt_host="$(echo "${MQTT_BROKER_URLS:-127.0.0.1:1883}" | cut -d, -f1 | cut -d: -f1)"
    mqtt_port="$(echo "${MQTT_BROKER_URLS:-127.0.0.1:1883}" | cut -d, -f1 | awk -F: '{print ($2==""?1883:$2)}')"

    if (echo >/dev/tcp/${mqtt_host}/${mqtt_port}) >/dev/null 2>&1; then
        print_ok "EMQX/MQTT ${mqtt_host}:${mqtt_port}"
    else
        print_fail "EMQX/MQTT ${mqtt_host}:${mqtt_port} 不可达"
    fi

    if (echo >/dev/tcp/127.0.0.1/6000) >/dev/null 2>&1; then
        print_ok "VIDEO :6000"
    else
        print_skip "VIDEO :6000 不可达（E2E 心跳项将 SKIP）"
    fi

    if (echo >/dev/tcp/127.0.0.1/48092) >/dev/null 2>&1 || container_running "$SINK_CTR"; then
        print_ok "iot-sink 可达（:48092 或容器）"
    else
        print_fail "iot-sink 未检测到（需要订阅 mqtt/iot-alert-notification）"
    fi
}

run_python_e2e() {
    print_section "L0/L1/L2 MQTT→入库（Python E2E）"
    local py="${PROJECT_ROOT}/VIDEO/tools/verify_alert_ingest_e2e.py"
    if [ ! -f "$py" ]; then
        print_fail "缺少 ${py}"
        return 1
    fi
    export ALERT_IMAGES_DIR="${ALERT_HOST_DIR}"
    export MQTT_BROKER_URLS="${MQTT_BROKER_URLS:-127.0.0.1:1883}"
    export VIDEO_BASE_URL="${VIDEO_BASE_URL:-http://127.0.0.1:6000}"
    export DOCKER_PG_CONTAINER="${DOCKER_PG_CONTAINER:-postgres-server}"

    set +e
    python3 "$py" "${E2E_ARGS[@]+"${E2E_ARGS[@]}"}"
    local rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
        print_ok "verify_alert_ingest_e2e.py 通过"
    else
        print_fail "verify_alert_ingest_e2e.py 失败 (exit=${rc})"
    fi
    return "$rc"
}

main() {
    print_section "EasyAIoT 告警事件面验收"
    print_info "项目根: ${PROJECT_ROOT}"

    check_shared_mount || true

    if [ "$MOUNT_ONLY" = "1" ]; then
        echo ""
        echo "结果: PASS=${PASS} FAIL=${FAIL} SKIP=${SKIP} (mount-only)"
        [ "$FAIL" -eq 0 ]
        return $?
    fi

    check_prereq_ports || true

    local sink_ok=1
    if ! (echo >/dev/tcp/127.0.0.1/48092) >/dev/null 2>&1 && ! container_running "$SINK_CTR"; then
        sink_ok=0
    fi
    if [ "$sink_ok" -eq 0 ]; then
        print_skip "iot-sink 未就绪，跳过入库 E2E（启动后重跑: install_linux.sh verify-alert）"
        echo ""
        echo "结果: PASS=${PASS} FAIL=${FAIL} SKIP=${SKIP}"
        if [ "$STRICT" = "1" ]; then
            return 1
        fi
        # soft：挂载失败仍计 FAIL
        [ "$FAIL" -eq 0 ]
        return $?
    fi

    set +e
    run_python_e2e
    local e2e_rc=$?
    set -e

    echo ""
    echo "汇总: mount/prereq PASS=${PASS} FAIL=${FAIL} SKIP=${SKIP}; e2e_exit=${e2e_rc}"
    if [ "$e2e_rc" -ne 0 ]; then
        return "$e2e_rc"
    fi
    [ "$FAIL" -eq 0 ]
}

main "$@"
