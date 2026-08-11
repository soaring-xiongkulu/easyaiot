#!/bin/bash
# ============================================
# EasyAIoT 节点 Ceph/共享媒体目录管理与验收
# ============================================
# 契约（与 RUNTIME / VIDEO / iot-sink / 节点 Agent 一致）：
#   媒体根（优先 tags.ceph_mount_path / media_mount_path，否则 /mnt/easyaiot-media）：
#     单机 = 本机 NFS export（127.0.0.1），集群 = NFS_SERVER 远程挂载
#   子目录：
#     <root>/alert_images  — 告警图片（MQTT 只带路径，sink 同路径读取）
#     <root>/playbacks     — 告警/SRS 录像落盘
#     <root>/snaps         — 抓拍（可选）
#
# 命令：
#   list                         列出 compute_node + Ceph 心跳字段
#   status [id|host|all]         节点详情（DB + 本机路径 / Agent 探活）
#   probe  [id|host|all]         在节点媒体根写入 alert_images + playbacks 探针
#   verify                       全量：列表 + 探针 + 控制面共享挂载 + 告警入库 E2E
#   verify --mount-only          只做挂载/探针，不跑 MQTT 入库
#   help
#
# 统一入口：
#   .scripts/docker/install_linux.sh ceph list
#   .scripts/docker/install_linux.sh ceph status 1
#   .scripts/docker/install_linux.sh ceph probe all
#   .scripts/docker/install_linux.sh ceph verify
#   .scripts/docker/install_linux.sh verify-ceph   # = ceph verify
#
# 环境变量：
#   DOCKER_PG_CONTAINER   默认 postgres-server
#   NODE_DB_NAME          默认 iot-node20
#   CEPH_MOUNT_ROOT       强制媒体根
#   ALERT_IMAGES_DIR      控制面告警图目录覆盖
#   PLAYBACKS_DIR         控制面录像目录覆盖
#   CEPH_SSH_USER         远程探针 SSH 用户（默认 ubuntu）
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

PASS=0
FAIL=0
SKIP=0
WARN=0

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_ok() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS + 1)); }
print_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL + 1)); }
print_skip() { echo -e "${YELLOW}[SKIP]${NC} $1"; SKIP=$((SKIP + 1)); }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARN=$((WARN + 1)); }
print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

PG_CTR="${DOCKER_PG_CONTAINER:-postgres-server}"
NODE_DB="${NODE_DB_NAME:-iot-node20}"
SSH_USER="${CEPH_SSH_USER:-ubuntu}"
VIDEO_CTR="${VIDEO_CONTAINER:-video-service}"

usage() {
    sed -n '2,40p' "$0" | sed 's/^# \?//'
}

psql_node() {
    local sql="$1"
    docker exec -i "$PG_CTR" psql -U postgres -d "$NODE_DB" -t -A -F $'\t' -c "$sql" 2>/dev/null
}

psql_node_pretty() {
    local sql="$1"
    docker exec -i "$PG_CTR" psql -U postgres -d "$NODE_DB" -c "$sql" 2>/dev/null
}

local_ips() {
    {
        hostname -I 2>/dev/null || true
        ip -4 addr show 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 || true
        echo "127.0.0.1"
    } | tr -s ' \t' '\n' | sed '/^$/d' | sort -u
}

is_local_host() {
    local host="$1"
    host="$(echo "$host" | tr -d '[:space:]')"
    [ -z "$host" ] && return 1
    case "$host" in
        127.0.0.1|localhost|::1) return 0 ;;
    esac
    local_ips | grep -Fxq "$host"
}

trim() { echo "$1" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'; }

agent_ok() {
    local host="$1"
    local port="${2:-9100}"
    curl -sf --connect-timeout 2 --max-time 3 "http://${host}:${port}/health" >/dev/null 2>&1
}

# 解析节点媒体根：优先 DB tags，再环境，默认 NFS 挂载点
resolve_media_root_for_row() {
    local host="$1"
    local ceph_path="$2"
    local media_path="$3"
    if [ -n "${CEPH_MOUNT_ROOT:-}" ]; then
        echo "${CEPH_MOUNT_ROOT}"
        return
    fi
    if [ -n "$ceph_path" ]; then
        echo "$ceph_path"
        return
    fi
    if [ -n "$media_path" ]; then
        echo "$media_path"
        return
    fi
    echo "${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}"
}

alert_dir_for_root() {
    local root="$1"
    local host="$2"
    if is_local_host "$host" && [ -n "${ALERT_IMAGES_DIR:-}" ]; then
        echo "$ALERT_IMAGES_DIR"
        return
    fi
    echo "${root}/alert_images"
}

playbacks_dir_for_root() {
    local root="$1"
    local host="$2"
    if is_local_host "$host" && [ -n "${PLAYBACKS_DIR:-}" ]; then
        echo "$PLAYBACKS_DIR"
        return
    fi
    echo "${root}/playbacks"
}

# 输出 TSV: id host name role status agent_port ceph_ready ceph_path media_path edge_ceph hb
fetch_nodes_tsv() {
    psql_node "
SELECT c.id,
       c.host,
       c.name,
       c.node_role,
       c.status,
       COALESCE(c.agent_port, 9100),
       COALESCE(c.tags->>'ceph_mount_ready', ''),
       COALESCE(c.tags->>'ceph_mount_path', ''),
       COALESCE(c.tags->>'media_mount_path', ''),
       COALESCE(e.ceph_mount_ready::text, ''),
       COALESCE(to_char(c.last_heartbeat_at, 'YYYY-MM-DD HH24:MI:SS'), '')
FROM compute_node c
LEFT JOIN edge_node e ON e.compute_node_id = c.id AND e.deleted = 0
WHERE c.deleted = 0
ORDER BY c.id;
"
}

find_node_row() {
    local key="$1"
    fetch_nodes_tsv | while IFS=$'\t' read -r id host name role status aport ready cpath mpath edge_ceph hb; do
        if [ "$key" = "all" ] || [ "$key" = "$id" ] || [ "$key" = "$host" ] || [ "$key" = "$name" ]; then
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
                "$id" "$host" "$name" "$role" "$status" "$aport" "$ready" "$cpath" "$mpath" "$edge_ceph" "$hb"
        fi
    done
}

cmd_list() {
    print_section "节点 Ceph / 共享媒体目录清单"
    if ! docker inspect -f '{{.State.Running}}' "$PG_CTR" 2>/dev/null | grep -q true; then
        print_fail "Postgres 容器 ${PG_CTR} 未运行，无法读 compute_node"
        return 1
    fi
    echo ""
    psql_node_pretty "
SELECT c.id AS id,
       c.name AS name,
       c.host AS host,
       c.node_role AS role,
       c.status AS status,
       COALESCE(c.agent_port, 9100) AS agent,
       COALESCE(c.tags->>'ceph_mount_ready', CASE WHEN e.ceph_mount_ready THEN 'true' ELSE '' END) AS ceph_ready,
       COALESCE(NULLIF(c.tags->>'ceph_mount_path',''), c.tags->>'media_mount_path', '') AS mount_path,
       COALESCE(to_char(c.last_heartbeat_at, 'MM-DD HH24:MI'), '-') AS heartbeat
FROM compute_node c
LEFT JOIN edge_node e ON e.compute_node_id = c.id AND e.deleted = 0
WHERE c.deleted = 0
ORDER BY c.id;
"
    echo ""
    print_info "说明: ceph_ready 来自 Agent 心跳 tags.ceph_mount_ready / edge_node.ceph_mount_ready"
    print_info "媒体子目录: <mount>/alert_images  告警图 | <mount>/playbacks  录像 | <mount>/snaps  抓拍"
    print_info "详查: $0 status <id|host|all>   探针: $0 probe <id|host|all>"
}

check_dir_rw() {
    local dir="$1"
    local label="$2"
    mkdir -p "$dir" 2>/dev/null || true
    if [ ! -d "$dir" ]; then
        print_fail "${label} 目录不存在且无法创建: ${dir}"
        return 1
    fi
    local probe="${dir}/.easyaiot_ceph_probe_$$"
    if printf 'ok' >"$probe" 2>/dev/null; then
        local got
        got="$(cat "$probe" 2>/dev/null || true)"
        rm -f "$probe" 2>/dev/null || true
        if [ "$got" = "ok" ]; then
            print_ok "${label} 可读写 — ${dir}"
            return 0
        fi
    fi
    print_fail "${label} 不可写 — ${dir}"
    return 1
}

probe_local_media() {
    local host="$1"
    local root="$2"
    local alert_d playbacks_d
    alert_d="$(alert_dir_for_root "$root" "$host")"
    playbacks_d="$(playbacks_dir_for_root "$root" "$host")"
    print_info "媒体根=${root}"
    print_info "告警图=${alert_d}"
    print_info "录像=${playbacks_d}"
    check_dir_rw "$alert_d" "告警图片 alert_images" || true
    check_dir_rw "$playbacks_d" "告警/SRS 录像 playbacks" || true
    # snaps optional
    if [ -d "${root}/snaps" ] || mkdir -p "${root}/snaps" 2>/dev/null; then
        check_dir_rw "${root}/snaps" "抓拍 snaps" || true
    else
        print_skip "snaps 目录不可用（可选）: ${root}/snaps"
    fi

    # 控制面：VIDEO 容器应能看到告警图探针
    if is_local_host "$host"; then
        local token="ceph-biz-$(date +%s)-$RANDOM"
        local alert_probe="${alert_d}/.ceph_biz_${token}"
        local play_probe="${playbacks_d}/.ceph_biz_${token}"
        printf '%s' "$token" >"$alert_probe"
        printf '%s' "$token" >"$play_probe"
        if docker inspect -f '{{.State.Running}}' "$VIDEO_CTR" 2>/dev/null | grep -q true; then
            if docker exec "$VIDEO_CTR" sh -c "test -f /app/alert_images/.ceph_biz_${token}" 2>/dev/null; then
                print_ok "VIDEO 容器可见告警图探针（共享挂载贯通）"
            else
                print_warn "VIDEO 容器未见 /app/alert_images 探针（检查 compose 挂载 VIDEO/alert_images）"
            fi
            # playbacks 常见挂载到 /data 或 host 路径，尽力探测
            if docker exec "$VIDEO_CTR" sh -c "test -f /data/playbacks/.ceph_biz_${token} -o -f /app/data/playbacks/.ceph_biz_${token}" 2>/dev/null; then
                print_ok "VIDEO 容器可见录像探针"
            else
                print_skip "VIDEO 容器内未匹配到 playbacks 探针路径（录像目录可能仅宿主机/SRS 使用）"
            fi
        else
            print_skip "${VIDEO_CTR} 未运行 — 跳过容器可见性"
        fi
        rm -f "$alert_probe" "$play_probe" 2>/dev/null || true
    fi
}

probe_remote_ssh() {
    local host="$1"
    local root="$2"
    local alert_d="${root}/alert_images"
    local play_d="${root}/playbacks"
    if ! command -v ssh >/dev/null 2>&1; then
        print_skip "无 ssh 命令，无法远程探针 ${host}"
        return 1
    fi
    local remote="
set -e
root='${root}'
mkdir -p \"\$root/alert_images\" \"\$root/playbacks\" \"\$root/snaps\"
token='remote-$$'
echo \"\$token\" > \"\$root/alert_images/.ceph_probe\"
echo \"\$token\" > \"\$root/playbacks/.ceph_probe\"
test -f \"\$root/alert_images/.ceph_probe\" && test -f \"\$root/playbacks/.ceph_probe\"
rm -f \"\$root/alert_images/.ceph_probe\" \"\$root/playbacks/.ceph_probe\"
echo PROBE_OK
"
    if ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=4 \
        "${SSH_USER}@${host}" "bash -s" <<<"$remote" 2>/dev/null | grep -q PROBE_OK; then
        print_ok "远程 SSH 探针成功 ${SSH_USER}@${host} root=${root}"
        return 0
    fi
    print_warn "远程 SSH 探针失败（无免密/密钥或路径不可写）: ${SSH_USER}@${host}"
    print_info "可配置 CEPH_SSH_USER，或在节点管理录入 SSH 后重试；当前以 DB ceph_ready 为准"
    return 1
}

inspect_one_node() {
    local id host name role status aport ready cpath mpath edge_ceph hb do_probe
    id="$(trim "${1:-}")"
    host="$(trim "${2:-}")"
    name="$(trim "${3:-}")"
    role="$(trim "${4:-}")"
    status="$(trim "${5:-}")"
    aport="$(trim "${6:-9100}")"
    ready="$(trim "${7:-}")"
    cpath="$(trim "${8:-}")"
    mpath="$(trim "${9:-}")"
    edge_ceph="$(trim "${10:-}")"
    hb="$(trim "${11:-}")"
    do_probe="${12:-0}"

    echo ""
    echo -e "${YELLOW}── 节点 #${id} ${name} (${host}) ──${NC}"
    print_info "role=${role} status=${status} agent=${aport} heartbeat=${hb:-none}"

    local eff_ready="$ready"
    if [ -z "$eff_ready" ] && [ -n "$edge_ceph" ]; then
        eff_ready="$edge_ceph"
    fi
    case "$(echo "$eff_ready" | tr 'A-Z' 'a-z')" in
        true|1|yes|on) print_ok "DB/心跳 ceph_mount_ready=${eff_ready}" ;;
        false|0|no|off) print_fail "DB/心跳 ceph_mount_ready=${eff_ready}" ;;
        *)
            if is_local_host "$host"; then
                print_warn "未上报 ceph_mount_ready（控制面可用本机共享目录，不强制 CephFS）"
            else
                print_warn "未上报 ceph_mount_ready — 集群调度可能拒绝该节点"
            fi
            ;;
    esac

    local root
    root="$(resolve_media_root_for_row "$host" "$cpath" "$mpath")"
    print_info "解析媒体根: ${root} (tags.path='${cpath:-${mpath:-}}')"

    if agent_ok "$host" "$aport"; then
        print_ok "Agent 探活 http://${host}:${aport}/health"
    else
        print_warn "Agent 探活失败 http://${host}:${aport}/health"
    fi

    if [ "$do_probe" = "1" ]; then
        if is_local_host "$host"; then
            probe_local_media "$host" "$root"
        else
            probe_remote_ssh "$host" "$root" || true
        fi
    else
        if is_local_host "$host"; then
            local ad pd
            ad="$(alert_dir_for_root "$root" "$host")"
            pd="$(playbacks_dir_for_root "$root" "$host")"
            [ -d "$ad" ] && print_ok "本机告警图目录存在: $ad" || print_warn "本机告警图目录不存在: $ad"
            [ -d "$pd" ] && print_ok "本机录像目录存在: $pd" || print_warn "本机录像目录不存在: $pd"
        fi
    fi
}

cmd_status() {
    local key="${1:-all}"
    print_section "节点 Ceph 状态 (${key})"
    local rows
    rows="$(find_node_row "$key")"
    if [ -z "$rows" ]; then
        print_fail "未找到节点: ${key}（先 list 查看）"
        return 1
    fi
    while IFS=$'\t' read -r id host name role status aport ready cpath mpath edge_ceph hb; do
        [ -z "$id" ] && continue
        inspect_one_node "$id" "$host" "$name" "$role" "$status" "$aport" "$ready" "$cpath" "$mpath" "$edge_ceph" "$hb" 0
    done <<<"$rows"
}

cmd_probe() {
    local key="${1:-all}"
    print_section "节点媒体目录探针 (${key})"
    local rows
    rows="$(find_node_row "$key")"
    if [ -z "$rows" ]; then
        print_fail "未找到节点: ${key}"
        return 1
    fi
    while IFS=$'\t' read -r id host name role status aport ready cpath mpath edge_ceph hb; do
        [ -z "$id" ] && continue
        inspect_one_node "$id" "$host" "$name" "$role" "$status" "$aport" "$ready" "$cpath" "$mpath" "$edge_ceph" "$hb" 1
    done <<<"$rows"
}

cmd_verify() {
    local mount_only=0
    local rest=()
    while [ $# -gt 0 ]; do
        case "$1" in
            --mount-only) mount_only=1 ;;
            *) rest+=("$1") ;;
        esac
        shift
    done

    print_section "Ceph/共享媒体 + 业务打通验收"
    cmd_list || true
    cmd_probe all

    # 控制面 compose 共享挂载（告警图）
    if [ -x "${SCRIPT_DIR}/verify_alert_mqtt_chain.sh" ]; then
        print_section "控制面告警图共享挂载"
        bash "${SCRIPT_DIR}/verify_alert_mqtt_chain.sh" --mount-only || true
    fi

    if [ "$mount_only" = "1" ]; then
        echo ""
        echo "汇总: PASS=${PASS} FAIL=${FAIL} WARN=${WARN} SKIP=${SKIP} (mount-only)"
        [ "$FAIL" -eq 0 ]
        return $?
    fi

    # 业务：告警图片 MQTT→sink→入库（含 MinIO）
    if [ -f "${PROJECT_ROOT}/VIDEO/tools/verify_alert_ingest_e2e.py" ]; then
        print_section "业务打通：告警图片 MQTT→iot-sink→入库"
        if (echo >/dev/tcp/127.0.0.1/48092) >/dev/null 2>&1 \
            || docker inspect -f '{{.State.Running}}' iot-sink 2>/dev/null | grep -q true; then
            export ALERT_IMAGES_DIR="${ALERT_IMAGES_DIR:-${PROJECT_ROOT}/VIDEO/alert_images}"
            export MQTT_BROKER_URLS="${MQTT_BROKER_URLS:-127.0.0.1:1883}"
            export E2E_TIMEOUT_SEC="${E2E_TIMEOUT_SEC:-30}"
            set +e
            python3 "${PROJECT_ROOT}/VIDEO/tools/verify_alert_ingest_e2e.py"
            local rc=$?
            set -e
            if [ "$rc" -eq 0 ]; then
                print_ok "告警图片业务链路通过"
            else
                print_fail "告警图片业务链路失败 (exit=${rc})"
            fi
        else
            print_skip "iot-sink 未就绪，跳过告警入库 E2E（启动后重跑 ceph verify）"
        fi
    fi

    # 业务：告警录像目录契约（写入可被读；完整录像生成依赖 SRS/任务，此处验路径契约）
    print_section "业务打通：告警录像目录契约 (playbacks)"
    local play_root play_dir
    play_root="$(resolve_media_root_for_row "$(hostname -I | awk '{print $1}')" "" "")"
    play_dir="$(playbacks_dir_for_root "$play_root" "$(hostname -I | awk '{print $1}')")"
    if check_dir_rw "$play_dir" "playbacks"; then
        print_ok "录像落盘目录可用 — 告警录像/SRS 可写此共享路径供中心读取"
    fi
    # 抽样：最近 alert.record_path 非空则说明历史上有录像归档
    if docker inspect -f '{{.State.Running}}' "$PG_CTR" 2>/dev/null | grep -q true; then
        local rec_cnt
        rec_cnt="$(docker exec "$PG_CTR" psql -U postgres -d iot-video20 -t -A -c \
            "select count(*) from alert where record_path is not null and record_path <> '' and time > now() - interval '7 days';" 2>/dev/null | tr -d '[:space:]' || echo 0)"
        if [ "${rec_cnt:-0}" -gt 0 ] 2>/dev/null; then
            print_ok "近 7 日已有 ${rec_cnt} 条告警含 record_path（录像归档曾打通）"
        else
            print_skip "近 7 日无告警 record_path — 目录契约已验，完整录像需任务产生片段后再查"
        fi
    fi

    echo ""
    echo "汇总: PASS=${PASS} FAIL=${FAIL} WARN=${WARN} SKIP=${SKIP}"
    [ "$FAIL" -eq 0 ]
}

main() {
    local cmd="${1:-help}"
    shift || true
    case "$cmd" in
        -h|--help|help) usage ;;
        list|ls) cmd_list "$@" ;;
        status|stat|show) cmd_status "$@" ;;
        probe|check-mount) cmd_probe "$@" ;;
        verify|verify-business|e2e) cmd_verify "$@" ;;
        *)
            echo "未知命令: $cmd" >&2
            usage
            exit 2
            ;;
    esac
}

main "$@"
