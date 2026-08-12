#!/bin/bash
# 从运行中的 iot-node20 导出、脱敏，并覆盖 .scripts/postgresql/iot-node10.sql 样例库。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-postgres-server}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-iot45722414822}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="iot-node20"

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
WORK_DIR="${SCRIPT_DIR}/backup/work_node_${TIMESTAMP}"
BACKUP_DIR="${SCRIPT_DIR}/backup/${TIMESTAMP}"
RAW_FILE="${WORK_DIR}/${DB_NAME}.raw.sql"
DESENS_FILE="${WORK_DIR}/${DB_NAME}.desens.sql"
SAMPLE_FILE="${SCRIPT_DIR}/iot-node10.sql"

mkdir -p "${WORK_DIR}" "${BACKUP_DIR}"

if ! docker ps --format '{{.Names}}' | grep -qx "${POSTGRES_CONTAINER}"; then
  echo "[ERROR] PostgreSQL 容器 ${POSTGRES_CONTAINER} 未运行"
  exit 1
fi

echo "[INFO] 导出 ${DB_NAME} ..."
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${POSTGRES_CONTAINER}" \
  pg_dump -U "${POSTGRES_USER}" -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -d "${DB_NAME}" \
  --clean --if-exists --create --format=plain --no-owner --no-privileges \
  > "${RAW_FILE}"

echo "[INFO] 脱敏处理 ..."
python3 "${SCRIPT_DIR}/desensitize_iot_node_dump.py" "${RAW_FILE}" -o "${DESENS_FILE}"

if [[ -f "${SAMPLE_FILE}" ]]; then
  cp -a "${SAMPLE_FILE}" "${BACKUP_DIR}/iot-node10.sql.bak"
fi

cp -a "${DESENS_FILE}" "${SAMPLE_FILE}"
cp -a "${DESENS_FILE}" "${BACKUP_DIR}/iot-node20.desens.sql"
cp -a "${RAW_FILE}" "${BACKUP_DIR}/iot-node20.raw.sql"

echo "[INFO] 样例库已更新: ${SAMPLE_FILE}"
echo "[INFO] 备份目录: ${BACKUP_DIR}"
ls -lh "${SAMPLE_FILE}" "${BACKUP_DIR}/iot-node20.desens.sql"
