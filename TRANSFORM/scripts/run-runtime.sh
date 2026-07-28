#!/usr/bin/env bash
# 在工作节点启动 TRANSFORM runtime（由 iot-node Workload 分发后调用）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ROOT}/.env.docker"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
JAR="${ROOT}/transform-runtime/target/transform-runtime-1.0.0.jar"
if [[ ! -f "$JAR" ]]; then
  echo "missing $JAR, run: mvn -f ${ROOT}/pom.xml -pl transform-runtime -am package -DskipTests" >&2
  exit 1
fi
exec java -jar "$JAR" \
  --spring.profiles.active="${SPRING_PROFILES_ACTIVE:-local}" \
  --spring.kafka.bootstrap-servers="${KAFKA_BOOTSTRAP:-127.0.0.1:9092}" \
  --transform.node-id="${TRANSFORM_NODE_ID:-}" \
  --transform.role="${TRANSFORM_ROLE:-full}" \
  "$@"
