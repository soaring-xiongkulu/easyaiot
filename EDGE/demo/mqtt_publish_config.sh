#!/usr/bin/env bash
# 手动：向 Edge 下发 config push
set -euo pipefail
DEMO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${EDGE_MQTT_HOST:-127.0.0.1}"
PORT="${EDGE_MQTT_PORT:-1883}"
PRODUCT="${EDGE_PRODUCT:-edge-gateway-product}"
GATEWAY="${EDGE_GATEWAY:-gateway-demo-001}"
TOPIC="/iot/${PRODUCT}/${GATEWAY}/config/downstream/push"
PAYLOAD="$DEMO/payloads/config_push.json"

echo "发布到 $TOPIC"
if command -v mosquitto_pub >/dev/null 2>&1; then
  mosquitto_pub -h "$HOST" -p "$PORT" -t "$TOPIC" -f "$PAYLOAD" -q 1
else
  python3 - <<PY
import paho.mqtt.client as mqtt
from pathlib import Path
body = Path("$PAYLOAD").read_text()
c = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
c.connect("$HOST", int("$PORT"), 60)
c.publish("$TOPIC", body, qos=1)
c.loop()
print("published")
PY
fi
