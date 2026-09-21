#!/usr/bin/env bash
# 导入 VISUALIZE 演示种子数据到 iot-visualize20
# 用法：bash .scripts/go-view/seed_visualize_demo.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEED_SQL="${ROOT_DIR}/.scripts/go-view/patches/visualize_demo_seed.sql"
TYPE_PATCH_SQL="${ROOT_DIR}/.scripts/go-view/patches/visualize_project_type.sql"
TWIN_SEED_SQL="${ROOT_DIR}/.scripts/go-view/patches/visualize_twin_seed.sql"
DB_NAME="iot-visualize20"
PG_USER="${POSTGRES_USER:-postgres}"
PG_PASSWORD="${POSTGRES_PASSWORD:-iot45722414822}"
PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
CONTAINER="${POSTGRES_CONTAINER:-postgres-server}"

if [[ ! -f "${SEED_SQL}" ]]; then
  echo "[ERROR] 找不到种子文件: ${SEED_SQL}"
  exit 1
fi

echo "[INFO] 导入 VISUALIZE 演示数据 -> ${DB_NAME}"
echo "[INFO] 种子文件: ${SEED_SQL}"

run_sql_docker() {
  local sql_file="$1"
  docker exec -i "${CONTAINER}" psql -U "${PG_USER}" -d "${DB_NAME}" < "${sql_file}"
}

run_sql_psql() {
  local sql_file="$1"
  PGPASSWORD="${PG_PASSWORD}" psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${DB_NAME}" -f "${sql_file}"
}

run_via_docker() {
  if [[ -f "${TYPE_PATCH_SQL}" ]]; then
    echo "[INFO] 先应用增量补丁: visualize_project_type.sql"
    run_sql_docker "${TYPE_PATCH_SQL}"
  fi
  run_sql_docker "${SEED_SQL}"
  run_sql_docker "${TWIN_SEED_SQL}"
}

run_via_psql() {
  if [[ -f "${TYPE_PATCH_SQL}" ]]; then
    echo "[INFO] 先应用增量补丁: visualize_project_type.sql"
    run_sql_psql "${TYPE_PATCH_SQL}"
  fi
  run_sql_psql "${SEED_SQL}"
  run_sql_psql "${TWIN_SEED_SQL}"
}

if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "${CONTAINER}"; then
  echo "[INFO] 使用 Docker 容器: ${CONTAINER}"
  run_via_docker
elif command -v psql >/dev/null 2>&1; then
  echo "[INFO] 使用本机 psql: ${PG_HOST}:${PG_PORT}"
  run_via_psql
else
  echo "[ERROR] 未找到可用的 postgres-server 容器，且本机无 psql。"
  echo "        请先启动 PostgreSQL，再执行本脚本。"
  exit 1
fi

echo "[OK] 演示数据导入完成。"
echo "     大屏×4：智慧工厂综合态势 / 智慧园区运行监测 / 设备运维健康看板 / 能源能耗分析大屏"
echo "     组态×4：水厂工艺总貌 / 产线运行看板 / 厂区管网组态 / 配电室电力监视"
echo "     数字孪生×4：工业园区 / 智慧校园 / 智慧港口 / 零碳能源基地"
echo "     封面：/resource/visualize-demo/dash-*-cover.svg 、 scada-*-cover.svg"
echo "     重新生成大屏：python3 .scripts/go-view/gen_visualize_dashboard_demo.py"
echo "     若 FUXA 画面尚未导入：bash .scripts/fuxa/seed_fuxa_demo.sh"
