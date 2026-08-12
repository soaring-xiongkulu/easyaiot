#!/usr/bin/env bash
# 对接 EasyAIoT 平台 EMQX 的冒烟联调（不启动独立 Mosquitto）
#
# 前置：
#   1. 平台 EMQX 已运行（默认 1883）
#   2. iot-sink protocol.emqx.enabled=true
#   3. WEB 已创建 GATEWAY 产品/设备、SUBSET 产品（见 EDGE/docs/PLATFORM_INTEGRATION.md）
#
# 用法：
#   export EDGE_PRODUCT=edge-gateway-product
#   export EDGE_GATEWAY=gateway-demo-001
#   export EDGE_SUBSET_PRODUCT=edge-subset-product
#   bash EDGE/demo/run_platform_smoke.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO="$ROOT/demo"
HOST_PROJECT="$ROOT/src/EasyAIoT.Edge.Host/EasyAIoT.Edge.Host.csproj"
PUBLISH_DIR="$ROOT/src/EasyAIoT.Edge.Host/bin/Release/net8.0"

MQTT_HOST="${EDGE_MQTT_HOST:-127.0.0.1}"
MQTT_PORT="${EDGE_MQTT_PORT:-1883}"
PRODUCT="${EDGE_PRODUCT:-edge-gateway-product}"
GATEWAY="${EDGE_GATEWAY:-gateway-demo-001}"
SUBSET_PRODUCT="${EDGE_SUBSET_PRODUCT:-edge-subset-product}"
SUB_DEVICE="${EDGE_SUB_DEVICE:-sensor-demo-001}"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'
info() { echo -e "${BLUE}[platform-smoke]${NC} $*"; }
ok() { echo -e "${GREEN}[pass]${NC} $*"; }
fail() { echo -e "${RED}[fail]${NC} $*"; exit 1; }

if ! command -v dotnet >/dev/null 2>&1; then
  fail "未找到 dotnet SDK"
fi

info "编译 EDGE..."
dotnet build "$ROOT/EasyAIoT.Edge.sln" -c Release -v q

mkdir -p "$PUBLISH_DIR/data" "$DEMO/logs"
cp "$DEMO/data/device-jobs.e2e.json" "$PUBLISH_DIR/data/device-jobs.json"

# 生成平台联调 appsettings
python3 - <<PY
import json
from pathlib import Path
cfg = {
  "Logging": {"LogLevel": {"Default": "Information"}},
  "Edge": {
    "Gateway": {
      "ProductIdentification": "$PRODUCT",
      "DeviceIdentification": "$GATEWAY"
    },
    "Mqtt": {
      "Host": "$MQTT_HOST",
      "Port": int("$MQTT_PORT"),
      "ClientId": "easyaiot-edge-platform-smoke",
      "UseTls": False
    }
  }
}
Path("$PUBLISH_DIR/appsettings.E2E.json").write_text(json.dumps(cfg, indent=2))

push = {
  "id": "platform-config-push",
  "method": "thing.config.push",
  "params": {
    "edgeJobs": [{
      "jobId": "platform-demo-simulator",
      "deviceIdentification": "$SUB_DEVICE",
      "subDeviceIdentification": "$SUB_DEVICE",
      "subProductIdentification": "$SUBSET_PRODUCT",
      "collectorId": "demo-simulator",
      "enabled": True,
      "intervalSeconds": 5,
      "protocolConfig": {"type": "demo", "pollIntervalMs": 5000, "points": []}
    }]
  }
}
Path("$DEMO/payloads/config_push_platform.json").write_text(json.dumps(push, indent=2))

prop_set = {
  "id": "platform-property-set",
  "method": "thing.property.set",
  "params": {
    "productIdentification": "$SUBSET_PRODUCT",
    "deviceIdentification": "$SUB_DEVICE",
    "input": {"temperature": 26.5, "humidity": 55}
  }
}
Path("$DEMO/payloads/property_set_platform.json").write_text(json.dumps(prop_set, indent=2))
PY

python3 -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('$MQTT_HOST', int('$MQTT_PORT'))); s.close()" \
  || fail "无法连接 MQTT $MQTT_HOST:$MQTT_PORT（请确认 EMQX 已启动）"

EDGE_PID=""
cleanup() { [[ -n "$EDGE_PID" ]] && kill "$EDGE_PID" 2>/dev/null || true; }
trap cleanup EXIT

pkill -f "EasyAIoT.Edge.Host.dll" 2>/dev/null || true
sleep 1

info "启动 Edge → 平台 Broker $MQTT_HOST:$MQTT_PORT"
export DOTNET_ENVIRONMENT=E2E
export PATH="${HOME}/.dotnet:${PATH}"
(cd "$PUBLISH_DIR" && dotnet EasyAIoT.Edge.Host.dll > "$DEMO/logs/edge-platform.stdout" 2>&1) &
EDGE_PID=$!
sleep 4

if ! kill -0 "$EDGE_PID" 2>/dev/null; then
  fail "Edge 启动失败，见 $DEMO/logs/edge-platform.stdout"
fi

if python3 -c "import paho.mqtt.client" 2>/dev/null; then
  PYTHON=python3
else
  VENV="$DEMO/.venv"
  [[ -x "$VENV/bin/python" ]] || { python3 -m venv "$VENV" && "$VENV/bin/pip" install -q paho-mqtt; }
  PYTHON="$VENV/bin/python"
fi

info "运行云侧模拟器（配置字段已按平台 SUBSET 产品生成）"
# 临时替换 config payload
cp "$DEMO/payloads/config_push_platform.json" "$DEMO/payloads/config_push.json"
cp "$DEMO/payloads/property_set_platform.json" "$DEMO/payloads/property_set.json"

"$PYTHON" "$DEMO/cloud_simulator.py" \
  --host "$MQTT_HOST" \
  --port "$MQTT_PORT" \
  --product "$PRODUCT" \
  --gateway "$GATEWAY" \
  --wait-uplink 2 \
  --wait-ack 20 \
  | tee "$DEMO/logs/platform_smoke.log"

if grep -q "属性上报: PASS" "$DEMO/logs/platform_smoke.log" \
  && grep -q "属性下发回执: PASS" "$DEMO/logs/platform_smoke.log"; then
  ok "Edge ↔ 平台 MQTT 冒烟通过"
  info "请在 WEB 查看子设备 $SUB_DEVICE 实时属性；iot-sink 日志应出现 storeDeviceData"
  exit 0
fi

fail "冒烟未通过，见 $DEMO/logs/platform_smoke.log 与 edge-platform.stdout"
tail -40 "$DEMO/logs/edge-platform.stdout" || true
exit 1
