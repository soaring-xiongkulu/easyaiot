#!/usr/bin/env bash
# 步骤 00：预检 Kafka / PG / schema / jar；自动建 Topic
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

MODE="${1:-${PIPELINE_MODE:-full}}"
ensure_python_deps
PY="$(resolve_python)"

log "=== [00] 预检 mode=$MODE ==="

# ---- Kafka + topics ----
"$PY" - "$KAFKA_BOOTSTRAP" <<'PY' || fail "Kafka 不可达: $KAFKA_BOOTSTRAP"
import sys
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
from kafka.errors import KafkaConfigurationError

bootstrap = sys.argv[1]
need = [
    "iot_transform_heartbeat",
    "iot_transform_telemetry",
    "iot_transform_command",
    "iot_transform_deliver",
    "iot_transform_dlq",
    "iot_transform_archive",
    # sink 输入（业务流程投喂）
    "iot_device_message",
    "iot-alert-notification",
    "iot-snapshot-alert",
    "iot-face-matching",
    "iot-plate-matching",
    "iot-post-process-result",
]
kwargs = dict(bootstrap_servers=bootstrap.split(","), request_timeout_ms=8000)
try:
    # 新版 kafka-python 支持该参数，探测超时更快。
    c = KafkaAdminClient(**kwargs, api_version_auto_timeout_ms=8000)
except KafkaConfigurationError:
    # 兼容旧版 kafka-python（不识别 api_version_auto_timeout_ms）。
    c = KafkaAdminClient(**kwargs)
existing = set(c.list_topics())
print(f"kafka_ok bootstrap={bootstrap} topics={len(existing)}")
missing = [t for t in need if t not in existing]
if missing:
    try:
        c.create_topics([NewTopic(t, num_partitions=1, replication_factor=1) for t in missing])
        print("created_topics", missing)
    except TopicAlreadyExistsError:
        pass
    except Exception as e:
        print("WARN create_topics:", e)
c.close()
PY
ok "Kafka 可用"

# ---- PostgreSQL：探测 + 尽量建库/建表 ----
ensure_pg_schema() {
  local sql="$ROOT/transform-runtime/src/main/resources/sql/iot-transform20.sql"
  if [[ ! -f "$sql" ]]; then
    log "WARN: 缺少 $sql"
    return 0
  fi
  # 1) docker 容器
  if docker_ok && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$PG_CONTAINER"; then
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$PG_CONTAINER" \
      psql -U "$POSTGRES_USERNAME" -tc "SELECT 1 FROM pg_database WHERE datname='iot-transform20'" | grep -q 1 \
      || docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$PG_CONTAINER" \
           psql -U "$POSTGRES_USERNAME" -c 'CREATE DATABASE "iot-transform20";'
    local tmp
    tmp="$(mktemp)"
    sed '/^CREATE DATABASE/d;/^\\c /d' "$sql" > "$tmp"
    docker exec -i -e PGPASSWORD="$POSTGRES_PASSWORD" "$PG_CONTAINER" \
      psql -U "$POSTGRES_USERNAME" -d 'iot-transform20' < "$tmp" >/dev/null 2>&1 || true
    rm -f "$tmp"
    ok "PG schema 已通过 docker@$PG_CONTAINER 确保"
    return 0
  fi
  # 2) 本机 psql
  if command -v psql >/dev/null 2>&1 && psql --version >/dev/null 2>&1; then
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USERNAME" -tc \
      "SELECT 1 FROM pg_database WHERE datname='iot-transform20'" 2>/dev/null | grep -q 1 \
      || PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USERNAME" -c 'CREATE DATABASE "iot-transform20";'
    local tmp
    tmp="$(mktemp)"
    sed '/^CREATE DATABASE/d;/^\\c /d' "$sql" > "$tmp"
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h 127.0.0.1 -U "$POSTGRES_USERNAME" -d 'iot-transform20' -f "$tmp" >/dev/null 2>&1 || true
    rm -f "$tmp"
    ok "PG schema 已通过本机 psql 确保"
    return 0
  fi
  log "WARN: 无可用 docker@$PG_CONTAINER / psql 客户端，仅做 TCP 探测（请预先建好 iot-transform20）"
}

"$PY" - <<'PY' || fail "PostgreSQL 不可达: $POSTGRES_URL"
import os, socket, sys
url = os.environ.get("POSTGRES_URL", "")
host, port = "127.0.0.1", 5432
if url.startswith("jdbc:postgresql://"):
    rest = url[len("jdbc:postgresql://"):]
    hostport, _, _db = rest.partition("/")
    if ":" in hostport:
        host, port_s = hostport.rsplit(":", 1)
        port = int(port_s)
    else:
        host = hostport
s = socket.create_connection((host, port), timeout=5)
s.close()
print(f"pg_tcp_ok {host}:{port}")
PY
ensure_pg_schema
ok "PostgreSQL 可达"

# ---- 制品 ----
case "$MODE" in
  docker)
    docker_ok || fail "Docker 不可用"
    ok "Docker 可用"
    ;;
  *)
    # full/local/auto/jar/workers：本机没有也会自动拉起，必须有 jar
    ensure_jar
    ok "jar 就绪"
    ;;
esac

ok "预检通过"
