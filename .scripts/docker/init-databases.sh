#!/bin/bash
# PostgreSQL 数据库初始化脚本
# 此脚本会创建所需的数据库并导入对应的 SQL 文件
# 注意：此脚本仅在 PostgreSQL 首次启动时执行（数据目录为空时）

set -e

SQL_DIR="/docker-entrypoint-initdb.d"
POSTGRES_USER="${POSTGRES_USER:-postgres}"

# 数据库清单按命名规约自动发现：<名字>10.sql -> 库 <名字>20
# （与 install_middleware_linux.sh init_databases() 及 schema-sync 同一规约）
# 新增模块只需在挂载目录放一个 *10.sql，无需再改本脚本的硬编码清单。
get_sql_file() {
    case "$1" in
        *20) echo "${1%20}10.sql" ;;
        *) echo "" ;;
    esac
}

# 清空 iot-node 仓库样例节点（与 install_middleware_linux.sh clear_iot_node_seed_data 对齐）
clear_iot_node_seed_data_initdb() {
    local db_name="iot-node20"
    if [ "${EASYAIOT_KEEP_NODE_SEED:-0}" = "1" ]; then
        echo "  · 保留 iot-node 样例数据（EASYAIOT_KEEP_NODE_SEED=1）"
        return 0
    fi
    if ! psql -U "$POSTGRES_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
        return 0
    fi
    if ! psql -U "$POSTGRES_USER" -d "$db_name" -tAc \
        "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='compute_node'" 2>/dev/null | grep -q 1; then
        return 0
    fi
    echo "  → 清空 iot-node 样例节点数据（compute_node / 指标 / NFS 拓扑）..."
    psql -U "$POSTGRES_USER" -d "$db_name" -v ON_ERROR_STOP=1 <<'EOSQL' >/dev/null
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
    echo "  ✓ 已清空 iot-node 样例节点（本机 Agent 纳管后会重新出现控制面节点）"
}

# 扫描 SQL_DIR 下所有 *10.sql 推导库名（兼容 bash 3.2，不依赖关联数组）
DATABASES=()
for _f in "$SQL_DIR"/*10.sql; do
    [ -e "$_f" ] || continue
    _base="$(basename "$_f" .sql)"
    case "$_base" in
        *10) DATABASES+=("${_base%10}20") ;;
    esac
done

echo "=========================================="
echo "开始初始化 PostgreSQL 数据库"
echo "=========================================="

# 等待 PostgreSQL 就绪（entrypoint init 完成且非 recovery 状态）
echo "等待 PostgreSQL 就绪..."
until psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1" >/dev/null 2>&1 \
    && [ "$(psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT pg_is_in_recovery();" 2>/dev/null || echo t)" = "f" ]; do
    sleep 1
done

echo "PostgreSQL 已就绪，开始创建数据库..."
echo ""

# 创建数据库并导入 SQL
success_count=0
total_count=${#DATABASES[@]}

for db_name in "${DATABASES[@]}"; do
    sql_file=$(get_sql_file "$db_name")
    
    if [ -z "$sql_file" ]; then
        echo "⚠️  警告: 数据库 $db_name 没有对应的 SQL 文件映射，跳过"
        continue
    fi
    
    echo "处理数据库: $db_name"
    echo "  SQL 文件: $sql_file"
    
    # 检查数据库是否已存在
    if psql -U "$POSTGRES_USER" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$db_name'" | grep -q 1; then
        echo "  ✓ 数据库 $db_name 已存在"
    else
        echo "  → 创建数据库: $db_name"
        if psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$db_name\";" 2>/dev/null; then
            echo "  ✓ 数据库创建成功"
        else
            echo "  ✗ 数据库创建失败"
            continue
        fi
    fi
    
    # 检查表是否已存在（判断是否已初始化）
    table_count=$(psql -U "$POSTGRES_USER" -d "$db_name" -tc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")
    
    if [ "$table_count" -gt 0 ]; then
        echo "  ✓ 数据库已包含 $table_count 个表，跳过 SQL 导入"
        success_count=$((success_count + 1))
        # 历史库可能已带样例节点（host 也可能被改写）：按指纹清理
        if [ "$db_name" = "iot-node20" ]; then
            seed_n=$(psql -U "$POSTGRES_USER" -d "$db_name" -tAc "
SELECT
  (SELECT COUNT(*) FROM compute_node WHERE deleted = 0 AND (
      host IN ('192.168.1.10','192.168.1.11','192.168.1.12')
      OR name IN ('NFS-Storage-01','NFS-Client-01')
      OR agent_token IN (
        'd92c6783e84b6c7c64ca378656fcb115',
        'cd3d4d946d7446a913f846b92ad94557',
        '0ec4652835ee5d457fd3e73d007c280a'
      )
      OR COALESCE(tags::text, '') LIKE '%demo-node%'
      OR COALESCE(tags::text, '') LIKE '%66009735168%'
      OR COALESCE(tags::text, '') LIKE '%1005867986944%'
  ))
  +
  (SELECT COUNT(*) FROM node_metric_snapshot WHERE deleted = 0
      AND mem_total_bytes = 66009735168
      AND disk_total_bytes = 1005867986944);
" 2>/dev/null | tr -d '[:space:]' || echo 0)
            if [ "${seed_n:-0}" -gt 0 ] 2>/dev/null; then
                clear_iot_node_seed_data_initdb
            fi
        fi
    else
        if [ -f "$SQL_DIR/$sql_file" ]; then
            echo "  → 导入 SQL 文件: $sql_file"
            if psql -U "$POSTGRES_USER" -d "$db_name" -f "$SQL_DIR/$sql_file" > /dev/null 2>&1; then
                echo "  ✓ SQL 文件导入成功"
                success_count=$((success_count + 1))
                if [ "$db_name" = "iot-node20" ]; then
                    clear_iot_node_seed_data_initdb
                fi
            else
                echo "  ✗ SQL 文件导入失败，请检查文件内容"
            fi
        else
            echo "  ✗ SQL 文件不存在: $SQL_DIR/$sql_file"
        fi
    fi
    echo ""
done

echo "=========================================="
if [ $success_count -eq $total_count ]; then
    echo "✓ 数据库初始化完成！($success_count/$total_count)"
else
    echo "⚠️  数据库初始化部分完成 ($success_count/$total_count)"
fi
echo "=========================================="
