#!/usr/bin/env bash
# 一键业务价值演示：不启动 iot-sink，模拟投喂 Kafka → TRANSFORM → MES/ERP/WMS
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
E2E="$ROOT/scripts/e2e"
JAR="$ROOT/transform-runtime/target/transform-runtime-1.0.0.jar"
API="${TRANSFORM_API:-http://127.0.0.1:48096}"
KAFKA="${KAFKA_BOOTSTRAP:-127.0.0.1:9092}"
RECEIVER_PORT="${RECEIVER_PORT:-18080}"
BACKUP_DIR="${TRANSFORM_BACKUP_DIR:-$ROOT/data/transform-backup}"
PG_CONTAINER="${PG_CONTAINER:-postgres-server}"
PG_USER="${POSTGRES_USERNAME:-postgres}"
PG_PASS="${POSTGRES_PASSWORD:-iot45722414822}"

mkdir -p "$BACKUP_DIR" "$E2E"
cd "$E2E"

echo "==> [1/6] Python 依赖（venv）"
if [[ ! -d "$E2E/.venv" ]]; then
  python3 -m venv "$E2E/.venv"
fi
# shellcheck disable=SC1091
source "$E2E/.venv/bin/activate"
pip install -q -r requirements.txt
PY=python

echo "==> [2/6] 初始化 PostgreSQL 库 iot-transform20（已存在则跳过建库）"
if docker ps --format '{{.Names}}' | grep -qx "$PG_CONTAINER"; then
  docker exec -e PGPASSWORD="$PG_PASS" "$PG_CONTAINER" \
    psql -U "$PG_USER" -tc "SELECT 1 FROM pg_database WHERE datname='iot-transform20'" | grep -q 1 \
    || docker exec -e PGPASSWORD="$PG_PASS" "$PG_CONTAINER" \
         psql -U "$PG_USER" -c 'CREATE DATABASE "iot-transform20";'
  TMP_SQL="$(mktemp)"
  sed '/^CREATE DATABASE/d;/^\\c /d' "$ROOT/transform-runtime/src/main/resources/sql/iot-transform20.sql" > "$TMP_SQL"
  docker exec -i -e PGPASSWORD="$PG_PASS" "$PG_CONTAINER" \
    psql -U "$PG_USER" -d 'iot-transform20' < "$TMP_SQL" >/dev/null 2>&1 || true
  rm -f "$TMP_SQL"
  echo "    DB ready"
else
  echo "    WARN: 未找到容器 $PG_CONTAINER，请确认 PostgreSQL 可用"
fi

echo "==> [3/6] 检查 / 编译 transform-runtime"
if [[ ! -f "$JAR" ]]; then
  mvn -f "$ROOT/pom.xml" -pl transform-runtime -am package -DskipTests -q
fi

echo "==> [4/6] 启动 mock 外部系统（MES/ERP/WMS/Webhook）:18080"
if ! curl -sf "http://127.0.0.1:${RECEIVER_PORT}/health" >/dev/null 2>&1; then
  "$PY" mock_receiver.py --port "$RECEIVER_PORT" >"$E2E/mock_receiver.log" 2>&1 &
  echo $! >"$E2E/mock_receiver.pid"
  for _ in $(seq 1 30); do
    curl -sf "http://127.0.0.1:${RECEIVER_PORT}/health" >/dev/null 2>&1 && break
    sleep 0.3
  done
fi
curl -sf "http://127.0.0.1:${RECEIVER_PORT}/health" >/dev/null
echo "    mock OK"

echo "==> [5/6] 启动 transform-runtime :48096 （role=full）"
if ! curl -sf "${API}/transform/overview" >/dev/null 2>&1; then
  nohup java -jar "$JAR" \
    --spring.profiles.active=local \
    --server.port=48096 \
    --spring.kafka.bootstrap-servers="$KAFKA" \
    --transform.role=full \
    --transform.backup-dir="$BACKUP_DIR" \
    >"$E2E/transform-runtime.log" 2>&1 &
  echo $! >"$E2E/transform-runtime.pid"
  echo "    runtime pid=$(cat "$E2E/transform-runtime.pid") 日志: $E2E/transform-runtime.log"
  for _ in $(seq 1 90); do
    if curl -sf "${API}/transform/overview" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi
curl -sf "${API}/transform/overview" >/dev/null
echo "    runtime OK"

echo "==> [6/6] 跑业务价值演示（脚本模拟 iot-sink 投喂）"
"$PY" demo_value.py --api "$API" --kafka "$KAFKA" --timeout 60 "$@"

echo
echo "提示: 完整场景可再执行: $PY simulate_iot_sink.py"
echo "      停止演示进程: bash $E2E/stop_demo.sh"
