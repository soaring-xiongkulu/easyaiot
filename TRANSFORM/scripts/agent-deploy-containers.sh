#!/usr/bin/env bash
# 通过 NODE Agent HTTP 在同一节点拉起 N 个 TRANSFORM 容器副本
# 前置：节点已 docker load 镜像；Agent 已启动（默认 :9100）
#
# 用法:
#   AGENT_URL=http://192.168.1.20:9100 bash scripts/agent-deploy-containers.sh --count 3
set -euo pipefail

AGENT_URL="${AGENT_URL:-http://127.0.0.1:9100}"
AGENT_TOKEN="${AGENT_TOKEN:-}"
IMAGE="${TRANSFORM_IMAGE:-easyaiot/transform-runtime:1.0.0}"
COUNT=2
START_PORT=48096
KAFKA="${KAFKA_BOOTSTRAP:-127.0.0.1:9092}"
POSTGRES_URL="${POSTGRES_URL:-jdbc:postgresql://127.0.0.1:5432/iot-transform20}"
NODE_ID="${TRANSFORM_NODE_ID:-}"
ROLE="${TRANSFORM_ROLE:-full}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --count) COUNT="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --start-port) START_PORT="$2"; shift 2 ;;
    --kafka) KAFKA="$2"; shift 2 ;;
    --node-id) NODE_ID="$2"; shift 2 ;;
    --agent) AGENT_URL="$2"; shift 2 ;;
    *) echo "unknown: $1" >&2; exit 1 ;;
  esac
done

HDR=(-H "Content-Type: application/json")
if [[ -n "$AGENT_TOKEN" ]]; then
  HDR+=(-H "X-Agent-Token: $AGENT_TOKEN")
fi

echo "Agent=$AGENT_URL image=$IMAGE count=$COUNT startPort=$START_PORT"
for i in $(seq 1 "$COUNT"); do
  wid="tr-${i}-$(date +%s)"
  port=$((START_PORT + i - 1))
  body=$(cat <<EOF
{
  "workloadType": "transform_runtime",
  "workloadId": "$wid",
  "runtime": "docker",
  "image": "$IMAGE",
  "env": {
    "RUNTIME": "docker",
    "IMAGE": "$IMAGE",
    "PORT": "$port",
    "START_PORT": "$START_PORT",
    "TRANSFORM_INSTANCE_ID": "$wid",
    "TRANSFORM_NODE_ID": "$NODE_ID",
    "TRANSFORM_ROLE": "$ROLE",
    "KAFKA_BOOTSTRAP": "$KAFKA",
    "POSTGRES_URL": "$POSTGRES_URL",
    "POSTGRES_USERNAME": "${POSTGRES_USERNAME:-postgres}",
    "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-iot45722414822}"
  }
}
EOF
)
  echo ">>> deploy #$i workloadId=$wid preferPort=$port"
  curl -sf "${HDR[@]}" -d "$body" "$AGENT_URL/workload/deploy" | tee /tmp/transform-deploy-$i.json
  echo
done
echo "完成。查看: curl $AGENT_URL/workload/list"
