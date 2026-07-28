#!/usr/bin/env bash
# 容器内入口：支持 SERVER_PORT / TRANSFORM_* / KAFKA / POSTGRES 环境变量
set -euo pipefail
JAR="/opt/easyaiot/TRANSFORM/transform-runtime.jar"
exec java ${JAVA_OPTS:-} -jar "$JAR" \
  --spring.profiles.active="${SPRING_PROFILES_ACTIVE:-local}" \
  --server.port="${SERVER_PORT:-${PORT:-48096}}" \
  --spring.kafka.bootstrap-servers="${KAFKA_BOOTSTRAP:-127.0.0.1:9092}" \
  --spring.datasource.dynamic.datasource.master.url="${POSTGRES_URL:-jdbc:postgresql://127.0.0.1:5432/iot-transform20}" \
  --spring.datasource.dynamic.datasource.master.username="${POSTGRES_USERNAME:-postgres}" \
  --spring.datasource.dynamic.datasource.master.password="${POSTGRES_PASSWORD:-iot45722414822}" \
  --transform.node-id="${TRANSFORM_NODE_ID:-}" \
  --transform.role="${TRANSFORM_ROLE:-full}" \
  --transform.instance-id="${TRANSFORM_INSTANCE_ID:-}" \
  --transform.backup-dir="${TRANSFORM_BACKUP_DIR:-/opt/easyaiot/TRANSFORM/data/transform-backup}" \
  "$@"
