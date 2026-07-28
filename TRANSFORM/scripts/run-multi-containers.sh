#!/usr/bin/env bash
# 在同一节点启动 N 个 TRANSFORM 容器副本（镜像已存在或可 pull）
# 用法:
#   bash scripts/run-multi-containers.sh --count 3 --kafka 192.168.1.10:9092
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ROOT}/.env.docker"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

IMAGE="${TRANSFORM_IMAGE:-easyaiot/transform-runtime:1.0.0}"
COUNT=2
BASE_PORT=48096
KAFKA="${KAFKA_BOOTSTRAP:-127.0.0.1:9092}"
POSTGRES_URL="${POSTGRES_URL:-jdbc:postgresql://127.0.0.1:5432/iot-transform20}"
POSTGRES_USERNAME="${POSTGRES_USERNAME:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-iot45722414822}"
NODE_ID="${TRANSFORM_NODE_ID:-}"
ROLE="${TRANSFORM_ROLE:-full}"
NAME_PREFIX="transform-runtime"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --count) COUNT="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --base-port) BASE_PORT="$2"; shift 2 ;;
    --kafka) KAFKA="$2"; shift 2 ;;
    --node-id) NODE_ID="$2"; shift 2 ;;
    --role) ROLE="$2"; shift 2 ;;
    --name-prefix) NAME_PREFIX="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "镜像不存在: $IMAGE ，请先 build-image.sh 或 docker load" >&2
  exit 1
fi

# 容器访问宿主机 Kafka/PG：Linux 用 host 网关；也可用 --network host
HOST_GATEWAY="$(docker network inspect bridge -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}' 2>/dev/null || echo 172.17.0.1)"
# 若用户传入的是 127.0.0.1，替换为网关以便容器可达
KAFKA_EFF="$KAFKA"
POSTGRES_EFF="$POSTGRES_URL"
if [[ "$KAFKA_EFF" == *"127.0.0.1"* ]]; then
  KAFKA_EFF="${KAFKA_EFF//127.0.0.1/$HOST_GATEWAY}"
fi
if [[ "$POSTGRES_EFF" == *"127.0.0.1"* ]]; then
  POSTGRES_EFF="${POSTGRES_EFF//127.0.0.1/$HOST_GATEWAY}"
fi

echo "启动 $COUNT 个容器 image=$IMAGE basePort=$BASE_PORT"
for i in $(seq 1 "$COUNT"); do
  port=$((BASE_PORT + i - 1))
  name="${NAME_PREFIX}-${i}"
  instance_id="${name}-$(hostname)-${port}"
  if docker ps -a --format '{{.Names}}' | grep -qx "$name"; then
    echo "已存在容器 $name，先移除"
    docker rm -f "$name" >/dev/null
  fi
  docker run -d \
    --name "$name" \
    --restart unless-stopped \
    -p "${port}:48096" \
    -e SERVER_PORT=48096 \
    -e TRANSFORM_INSTANCE_ID="$instance_id" \
    -e TRANSFORM_NODE_ID="$NODE_ID" \
    -e TRANSFORM_ROLE="$ROLE" \
    -e KAFKA_BOOTSTRAP="$KAFKA_EFF" \
    -e POSTGRES_URL="$POSTGRES_EFF" \
    -e POSTGRES_USERNAME="$POSTGRES_USERNAME" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    "$IMAGE" >/dev/null
  echo "  OK $name  hostPort=$port  instanceId=$instance_id"
done

echo "完成。系统对接页应陆续看到 $COUNT 个 ONLINE 实例。"
