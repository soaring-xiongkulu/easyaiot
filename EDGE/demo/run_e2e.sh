#!/usr/bin/env bash
# EasyAIoT EDGE 云—边 MQTT 全链路联调
#
# 用法:
#   bash EDGE/demo/run_e2e.sh
#   EDGE_MQTT_PORT=1883 bash EDGE/demo/run_e2e.sh --skip-mqtt   # 使用平台已有 EMQX
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$ROOT/demo"
REPO="$(cd "$ROOT/.." && pwd)"
HOST_PROJECT="$ROOT/src/EasyAIoT.Edge.Host/EasyAIoT.Edge.Host.csproj"
PUBLISH_DIR="$ROOT/src/EasyAIoT.Edge.Host/bin/Release/net8.0"

MQTT_HOST="${EDGE_MQTT_HOST:-127.0.0.1}"
MQTT_PORT="${EDGE_MQTT_PORT:-18883}"
PRODUCT="${EDGE_PRODUCT:-edge-gateway-product}"
GATEWAY="${EDGE_GATEWAY:-gateway-demo-001}"
SKIP_MQTT=0
SKIP_BUILD=0

for arg in "$@"; do
  case "$arg" in
    --skip-mqtt) SKIP_MQTT=1 ;;
    --skip-build) SKIP_BUILD=1 ;;
  esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'
info() { echo -e "${BLUE}[e2e]${NC} $*"; }
ok() { echo -e "${GREEN}[pass]${NC} $*"; }
fail() { echo -e "${RED}[fail]${NC} $*"; exit 1; }

if ! command -v dotnet >/dev/null 2>&1; then
  fail "未找到 dotnet SDK"
fi

if [[ "$SKIP_BUILD" != "1" ]]; then
  info "编译 EDGE..."
  dotnet build "$ROOT/EasyAIoT.Edge.sln" -c Release
fi

mkdir -p "$PUBLISH_DIR/data"
cp "$DEMO/data/device-jobs.e2e.json" "$PUBLISH_DIR/data/device-jobs.json"
cp "$DEMO/appsettings.e2e.json" "$PUBLISH_DIR/appsettings.E2E.json"

# 按联调端口覆盖 MQTT 配置
python3 - <<PY
import json
from pathlib import Path
p = Path("$PUBLISH_DIR/appsettings.E2E.json")
cfg = json.loads(p.read_text())
cfg["Edge"]["Mqtt"]["Host"] = "$MQTT_HOST"
cfg["Edge"]["Mqtt"]["Port"] = int("$MQTT_PORT")
p.write_text(json.dumps(cfg, indent=2))
PY

MQTT_STARTED=0
if [[ "$SKIP_MQTT" != "1" ]]; then
  if command -v docker >/dev/null 2>&1; then
    info "启动 demo Mosquitto (port $MQTT_PORT)..."
    export MQTT_PORT
    docker compose -f "$DEMO/docker-compose.yml" up -d
    MQTT_STARTED=1
    sleep 2
  else
    fail "未安装 docker，请使用 --skip-mqtt 并确保 $MQTT_HOST:$MQTT_PORT 可连"
  fi
else
  info "使用已有 MQTT Broker: $MQTT_HOST:$MQTT_PORT"
fi

# 检测 Broker
if command -v python3 >/dev/null 2>&1; then
  python3 - <<PY || fail "MQTT $MQTT_HOST:$MQTT_PORT 不可达"
import socket
s = socket.socket()
s.settimeout(3)
s.connect(("$MQTT_HOST", int("$MQTT_PORT")))
s.close()
print("mqtt reachable")
PY
fi

EDGE_PID=""
CLOUD_PID=""
cleanup() {
  if [[ -n "$EDGE_PID" ]]; then kill "$EDGE_PID" 2>/dev/null || true; fi
  if [[ -n "$CLOUD_PID" ]]; then kill "$CLOUD_PID" 2>/dev/null || true; fi
  if [[ "$MQTT_STARTED" == "1" ]]; then
    docker compose -f "$DEMO/docker-compose.yml" down 2>/dev/null || true
  fi
}
trap cleanup EXIT

pkill -f "EasyAIoT.Edge.Host.dll" 2>/dev/null || true
sleep 1

info "启动 Edge Host (DOTNET_ENVIRONMENT=E2E)..."
export DOTNET_ENVIRONMENT=E2E
export PATH="${HOME}/.dotnet:${PATH}"
(cd "$PUBLISH_DIR" && dotnet EasyAIoT.Edge.Host.dll > "$DEMO/logs/edge.stdout" 2>&1) &
EDGE_PID=$!
sleep 3

if ! kill -0 "$EDGE_PID" 2>/dev/null; then
  fail "Edge 进程退出，日志: $DEMO/logs/edge.stdout"
  tail -50 "$DEMO/logs/edge.stdout" || true
fi

mkdir -p "$DEMO/logs"
info "启动云平台模拟器..."
if python3 -c "import paho.mqtt.client" 2>/dev/null; then
  PYTHON=python3
else
  VENV="$DEMO/.venv"
  if [[ ! -x "$VENV/bin/python" ]]; then
    info "创建 demo Python venv 并安装 paho-mqtt..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -q paho-mqtt
  fi
  PYTHON="$VENV/bin/python"
fi

"$PYTHON" "$DEMO/cloud_simulator.py" \
  --host "$MQTT_HOST" \
  --port "$MQTT_PORT" \
  --product "$PRODUCT" \
  --gateway "$GATEWAY" \
  --wait-uplink 2 \
  --wait-ack 15 \
  | tee "$DEMO/logs/cloud_simulator.log"

if grep -q "属性上报: PASS" "$DEMO/logs/cloud_simulator.log" \
  && grep -q "属性下发回执: PASS" "$DEMO/logs/cloud_simulator.log"; then
  ok "云—Edge 链路联调通过"
  exit 0
fi

fail "联调未通过，见 $DEMO/logs/"
tail -30 "$DEMO/logs/edge.stdout" || true
exit 1
