#!/usr/bin/env bash
# 手动：仅订阅 Edge 上行（需平台 EMQX 或 demo Mosquitto）
set -euo pipefail
HOST="${EDGE_MQTT_HOST:-127.0.0.1}"
PORT="${EDGE_MQTT_PORT:-1883}"
PRODUCT="${EDGE_PRODUCT:-edge-gateway-product}"
GATEWAY="${EDGE_GATEWAY:-gateway-demo-001}"

TOPIC="/iot/${PRODUCT}/${GATEWAY}/#"
echo "订阅: $TOPIC @ $HOST:$PORT"

if command -v mosquitto_sub >/dev/null 2>&1; then
  mosquitto_sub -h "$HOST" -p "$PORT" -t "$TOPIC" -v
else
  python3 - <<PY
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    print(f"{msg.topic}\n{msg.payload.decode()}\n")

c = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
c.on_message = on_message
c.connect("$HOST", int("$PORT"), 60)
c.subscribe("$TOPIC", qos=1)
print("listening...")
c.loop_forever()
PY
fi
