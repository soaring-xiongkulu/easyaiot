#!/usr/bin/env python3
"""
EasyAIoT 云平台侧 MQTT 联调模拟器：
  - 订阅 Edge 属性上报、子设备代报、属性设置回执
  - 下发 config push 与 property desired set
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("请先安装: pip install paho-mqtt")
    sys.exit(1)

DEMO_DIR = Path(__file__).resolve().parent


def topic_property_report(product: str, device: str) -> str:
    return f"/iot/{product}/{device}/property/upstream/report"


def topic_sub_property_report(product: str, device: str) -> str:
    return f"/iot/{product}/{device}/sub/property/upstream/report"


def topic_config_push(product: str, device: str) -> str:
    return f"/iot/{product}/{device}/config/downstream/push"


def topic_property_set(product: str, device: str) -> str:
    return f"/iot/{product}/{device}/property/downstream/desired/set"


def topic_property_set_ack(product: str, device: str) -> str:
    return f"/iot/{product}/{device}/property/upstream/desired/set/ack"


class CloudSimulator:
    def __init__(self, host: str, port: int, product: str, gateway: str):
        self.host = host
        self.port = port
        self.product = product
        self.gateway = gateway
        self.uplink_count = 0
        self.ack_received = False
        self.ack_success = False
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"easyaiot-cloud-sim-{int(time.time())}",
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            print(f"[cloud] MQTT connect failed: {reason_code}")
            return
        topics = [
            topic_property_report(self.product, self.gateway),
            topic_sub_property_report(self.product, self.gateway),
            topic_property_set_ack(self.product, self.gateway),
        ]
        for t in topics:
            client.subscribe(t, qos=1)
            print(f"[cloud] subscribed: {t}")

    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8", errors="replace")
        print(f"\n[cloud] << {msg.topic}")
        try:
            print(json.dumps(json.loads(payload), ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(payload)

        if msg.topic.endswith("/property/upstream/report") or msg.topic.endswith("/sub/property/upstream/report"):
            self.uplink_count += 1
        if msg.topic.endswith("/property/upstream/desired/set/ack"):
            self.ack_received = True
            try:
                body = json.loads(payload)
                self.ack_success = body.get("code") == 0
            except json.JSONDecodeError:
                self.ack_success = False

    def connect(self):
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

    def publish_file(self, topic: str, path: Path):
        body = path.read_text(encoding="utf-8")
        self.client.publish(topic, body, qos=1)
        print(f"[cloud] >> {topic}")
        print(json.dumps(json.loads(body), ensure_ascii=False, indent=2))

    def run_scenario(self, wait_uplink: int, wait_ack: int):
        time.sleep(2)
        print("\n=== Step 1: 下发 config push ===")
        self.publish_file(
            topic_config_push(self.product, self.gateway),
            DEMO_DIR / "payloads" / "config_push.json",
        )

        print(f"\n=== Step 2: 等待 Edge 属性上报 (>={wait_uplink} 条) ===")
        deadline = time.time() + 45
        while time.time() < deadline and self.uplink_count < wait_uplink:
            time.sleep(0.5)
        print(f"[cloud] uplink messages received: {self.uplink_count}")

        print("\n=== Step 3: 下发 property desired set ===")
        self.publish_file(
            topic_property_set(self.product, self.gateway),
            DEMO_DIR / "payloads" / "property_set.json",
        )

        print(f"\n=== Step 4: 等待 set ack (timeout {wait_ack}s) ===")
        deadline = time.time() + wait_ack
        while time.time() < deadline and not self.ack_received:
            time.sleep(0.5)

        ok_uplink = self.uplink_count >= wait_uplink
        ok_ack = self.ack_received and self.ack_success
        print("\n=== 结果 ===")
        print(f"  属性上报: {'PASS' if ok_uplink else 'FAIL'} ({self.uplink_count}/{wait_uplink})")
        print(f"  属性下发回执: {'PASS' if ok_ack else 'FAIL'}")
        self.client.loop_stop()
        self.client.disconnect()
        return 0 if ok_uplink and ok_ack else 1


def main():
    parser = argparse.ArgumentParser(description="EasyAIoT Cloud MQTT E2E simulator")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18883)
    parser.add_argument("--product", default="edge-gateway-product")
    parser.add_argument("--gateway", default="gateway-demo-001")
    parser.add_argument("--wait-uplink", type=int, default=2)
    parser.add_argument("--wait-ack", type=int, default=15)
    args = parser.parse_args()

    sim = CloudSimulator(args.host, args.port, args.product, args.gateway)
    sim.connect()
    sys.exit(sim.run_scenario(args.wait_uplink, args.wait_ack))


if __name__ == "__main__":
    main()
