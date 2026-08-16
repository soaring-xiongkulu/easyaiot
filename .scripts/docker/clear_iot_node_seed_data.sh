#!/usr/bin/env bash
# 清空 iot-node 仓库样例节点（iot-node10.sql 演示节点/指标/NFS 拓扑）
# Linux / macOS / Windows 中间件共用；可 source 后调用 clear_iot_node_seed_data [force|auto]
#
# 保留样例：EASYAIOT_KEEP_NODE_SEED=1
# $1=force 时无论是否检测到样例主机都清空（刚导入 *10.sql 后使用）

# shellcheck disable=SC2034
[[ -n "${CLEAR_IOT_NODE_SEED_LOADED:-}" ]] && return 0
CLEAR_IOT_NODE_SEED_LOADED=1

_clear_node_seed_msg() {
    local level="$1"
    shift
    case "$level" in
        info)
            if declare -F print_info >/dev/null 2>&1; then print_info "$*"
            elif declare -F info >/dev/null 2>&1; then info "$*"
            else echo "[node-seed][info] $*" >&2; fi
            ;;
        success)
            if declare -F print_success >/dev/null 2>&1; then print_success "$*"
            elif declare -F ok >/dev/null 2>&1; then ok "$*"
            else echo "[node-seed][ok] $*" >&2; fi
            ;;
        warning)
            if declare -F print_warning >/dev/null 2>&1; then print_warning "$*"
            elif declare -F warn >/dev/null 2>&1; then warn "$*"
            else echo "[node-seed][warn] $*" >&2; fi
            ;;
        error)
            if declare -F print_error >/dev/null 2>&1; then print_error "$*"
            elif declare -F err >/dev/null 2>&1; then err "$*"
            else echo "[node-seed][err] $*" >&2; fi
            ;;
        *)
            echo "[node-seed][$level] $*" >&2
            ;;
    esac
}

# 等待 Postgres 就绪，并尽量等到 iot-node20.compute_node 可读（首次 initdb 导入期间）
wait_postgres_for_node_seed_clear() {
    local i
    for i in $(seq 1 90); do
        if docker exec postgres-server pg_isready -U postgres >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
    if ! docker exec postgres-server pg_isready -U postgres >/dev/null 2>&1; then
        return 1
    fi
    for i in $(seq 1 60); do
        if docker exec postgres-server psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw 'iot-node20'; then
            if docker exec postgres-server psql -U postgres -d iot-node20 -tAc \
                "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='compute_node'" 2>/dev/null | grep -q 1; then
                return 0
            fi
        fi
        sleep 2
    done
    return 0
}

clear_iot_node_seed_data() {
    local mode="${1:-auto}"
    local db_name="iot-node20"

    if [ "${EASYAIOT_KEEP_NODE_SEED:-0}" = "1" ]; then
        _clear_node_seed_msg info "保留 iot-node 样例数据（EASYAIOT_KEEP_NODE_SEED=1）"
        return 0
    fi

    if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'postgres-server'; then
        return 0
    fi
    if ! docker exec postgres-server psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$db_name"; then
        return 0
    fi
    if ! docker exec postgres-server psql -U postgres -d "$db_name" -tAc \
        "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='compute_node'" 2>/dev/null | grep -q 1; then
        return 0
    fi

    local seed_count=0
    # 与 .scripts/postgresql/iot-node10.sql 样例主机一致
    seed_count=$(docker exec postgres-server psql -U postgres -d "$db_name" -tAc \
        "SELECT COUNT(*) FROM compute_node WHERE deleted = 0 AND host IN ('192.168.1.10','192.168.1.11','192.168.1.12');" 2>/dev/null | tr -d '[:space:]' || echo 0)
    seed_count="${seed_count:-0}"

    if [ "$mode" != "force" ] && [ "$seed_count" -eq 0 ] 2>/dev/null; then
        _clear_node_seed_msg info "iot-node 无仓库样例节点，跳过清空"
        return 0
    fi

    _clear_node_seed_msg info "清空 iot-node 样例/演示节点数据（避免集群概览显示非本机节点）..."
    local sql
    sql=$(cat <<'EOSQL'
DO $$
BEGIN
  IF to_regclass('public.node_metric_snapshot') IS NOT NULL THEN TRUNCATE TABLE public.node_metric_snapshot RESTART IDENTITY; END IF;
  IF to_regclass('public.node_storage_op_log') IS NOT NULL THEN TRUNCATE TABLE public.node_storage_op_log RESTART IDENTITY; END IF;
  IF to_regclass('public.node_workload_binding') IS NOT NULL THEN TRUNCATE TABLE public.node_workload_binding RESTART IDENTITY; END IF;
  IF to_regclass('public.node_ssh_credential') IS NOT NULL THEN TRUNCATE TABLE public.node_ssh_credential RESTART IDENTITY; END IF;
  IF to_regclass('public.nfs_cluster_bridge') IS NOT NULL THEN TRUNCATE TABLE public.nfs_cluster_bridge RESTART IDENTITY; END IF;
  IF to_regclass('public.nfs_cluster') IS NOT NULL THEN TRUNCATE TABLE public.nfs_cluster RESTART IDENTITY; END IF;
  IF to_regclass('public.device_media_binding') IS NOT NULL THEN TRUNCATE TABLE public.device_media_binding RESTART IDENTITY; END IF;
  IF to_regclass('public.edge_node') IS NOT NULL THEN TRUNCATE TABLE public.edge_node RESTART IDENTITY; END IF;
  IF to_regclass('public.control_plane_peer') IS NOT NULL THEN TRUNCATE TABLE public.control_plane_peer RESTART IDENTITY; END IF;
  IF to_regclass('public.compute_node') IS NOT NULL THEN TRUNCATE TABLE public.compute_node RESTART IDENTITY CASCADE; END IF;
END $$;
EOSQL
)
    if docker exec -i postgres-server psql -U postgres -d "$db_name" -v ON_ERROR_STOP=1 <<< "$sql" >/dev/null 2>&1; then
        _clear_node_seed_msg success "已清空 iot-node 节点相关样例数据（compute_node / 指标 / NFS 拓扑等）"
        _clear_node_seed_msg info "控制面节点将在本机 Agent 纳管后自动出现在集群概览"
        return 0
    fi
    _clear_node_seed_msg warning "清空 iot-node 样例数据失败（可稍后手动 TRUNCATE compute_node 等相关表）"
    return 0
}
