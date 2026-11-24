#!/usr/bin/env python3
"""RK3588 edge management agent: one-time enrollment, MQTT telemetry and safe commands."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SPEC_VERSION = "easyaiot.edge.telemetry/v1"
AGENT_VERSION = "1.0.0"


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sign_envelope(token: str, message_type: str, node_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    payload_text = compact_json(payload)
    message_id = uuid.uuid4().hex
    sent_at = int(time.time() * 1000)
    canonical = "\n".join((SPEC_VERSION, message_type, str(node_id), message_id, str(sent_at), payload_text))
    signature = hmac.new(token.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return {
        "specVersion": SPEC_VERSION,
        "messageType": message_type,
        "nodeId": node_id,
        "messageId": message_id,
        "sentAt": sent_at,
        "payload": payload_text,
        "signature": signature,
    }


def verify_envelope(envelope: dict[str, Any], token: str, node_id: int, message_type: str) -> dict[str, Any]:
    if envelope.get("specVersion") != SPEC_VERSION or envelope.get("messageType") != message_type:
        raise ValueError("协议版本或消息类型不匹配")
    if int(envelope.get("nodeId") or 0) != node_id:
        raise ValueError("nodeId 不匹配")
    sent_at = int(envelope.get("sentAt") or 0)
    if abs(int(time.time() * 1000) - sent_at) > 120_000:
        raise ValueError("命令已过期")
    payload_text = str(envelope.get("payload") or "")
    canonical = "\n".join((SPEC_VERSION, message_type, str(node_id), str(envelope.get("messageId") or ""),
                            str(sent_at), payload_text))
    expected = hmac.new(token.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, str(envelope.get("signature") or "")):
        raise ValueError("命令签名无效")
    payload = json.loads(payload_text)
    if not isinstance(payload, dict):
        raise ValueError("命令 payload 必须是对象")
    return payload


def read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return ""


def hardware_fingerprint() -> str:
    parts = [read_text("/etc/machine-id"), read_text("/sys/class/dmi/id/product_uuid")]
    cpuinfo = read_text("/proc/cpuinfo")
    serial = re.search(r"^Serial\s*:\s*(\S+)", cpuinfo, re.MULTILINE | re.IGNORECASE)
    if serial:
        parts.append(serial.group(1))
    parts.extend((platform.machine(), socket.gethostname()))
    return hashlib.sha256("|".join(filter(None, parts)).encode()).hexdigest()


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in read_text("/proc/meminfo").splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        match = re.search(r"\d+", raw)
        if match:
            values[key] = int(match.group()) * 1024
    return values


def cpu_sample() -> tuple[int, int]:
    fields = read_text("/proc/stat").splitlines()[0].split()[1:]
    values = [int(item) for item in fields]
    idle = values[3] + (values[4] if len(values) > 4 else 0)
    return sum(values), idle


def temperatures() -> list[float]:
    result: list[float] = []
    for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            value = float(path.read_text().strip())
            if value > 1000:
                value /= 1000.0
            if -20 <= value <= 150:
                result.append(value)
        except (OSError, ValueError):
            continue
    return result


def npu_snapshot() -> list[dict[str, Any]]:
    candidates = ("/sys/kernel/debug/rknpu/load", "/sys/kernel/debug/rknpu/load_info")
    raw = ""
    for path in candidates:
        raw = read_text(path)
        if raw:
            break
    loads = [int(item) for item in re.findall(r"(\d{1,3})%", raw)]
    if not loads:
        return [{"name": f"NPU-{index}", "core": index, "loadPercent": None} for index in range(3)]
    return [{"name": f"NPU-{index}", "core": index, "loadPercent": min(load, 100)}
            for index, load in enumerate(loads[:3])]


def service_active(name: str) -> bool:
    try:
        result = subprocess.run(["systemctl", "is-active", "--quiet", name], timeout=3, check=False)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def parse_broker(raw: str) -> tuple[str, int, bool]:
    parsed = urlparse(raw if "://" in raw else f"mqtt://{raw}")
    if not parsed.hostname:
        raise ValueError(f"MQTT Broker 地址无效: {raw}")
    secure = parsed.scheme in ("mqtts", "ssl", "tls")
    return parsed.hostname, parsed.port or (8883 if secure else 1883), secure


class Agent:
    def __init__(self, config_path: Path):
        self.config_path = config_path.resolve()
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.state_path = self.config_path.with_name("edge-agent-state.json")
        self.tasks_path = self.config_path.with_name("tasks.tsv")
        self.state: dict[str, Any] = {}
        self.client = None
        self.connected = threading.Event()
        self.stop_event = threading.Event()
        self.cpu_previous = cpu_sample()
        self.httpd: ThreadingHTTPServer | None = None
        self.latest_payload: dict[str, Any] = {}
        self.seen_command_messages: dict[str, float] = {}

    def load_state(self) -> None:
        if self.state_path.is_file():
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))

    def save_state(self) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(self.state_path)

    def enroll(self) -> None:
        self.load_state()
        if self.state.get("nodeId") and self.state.get("agentToken"):
            self.refresh_runtime_config()
            return
        base = str(self.config.get("control_plane_url") or "").rstrip("/")
        if not base:
            raise RuntimeError("control_plane_url 未配置")
        body = {
            "fingerprint": hardware_fingerprint(),
            "name": self.config.get("node_name") or socket.gethostname(),
            "host": local_ip(),
            "nodeKind": "edge_box",
            "hardwareProvider": "rockchip",
            "socModel": "RK3588",
            "acceleratorType": "npu",
            "acceleratorCount": 3,
            "runtimeTarget": "rknn-rk3588",
            "runtimeVersion": "rk3588-mpp-rga-rknn",
            "agentVersion": AGENT_VERSION,
            "agentPort": int(self.config.get("agent_port") or 9100),
            "maxTaskCount": len(self.task_rows()),
            "joinToken": self.config.get("join_token") or "",
        }
        request = urllib.request.Request(
            f"{base}/enroll",
            data=compact_json(body).encode(),
            headers={"Content-Type": "application/json", "X-Edge-Join-Token": body["joinToken"]},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                result = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"边缘节点纳管失败 HTTP {exc.code}: {exc.read().decode(errors='ignore')}") from exc
        if int(result.get("code", -1)) != 0 or not isinstance(result.get("data"), dict):
            raise RuntimeError(f"边缘节点纳管失败: {result}")
        self.state = result["data"]
        self.save_state()

    def refresh_runtime_config(self) -> None:
        """每次启动刷新 Broker 与 Topic，但不改变本地节点身份。"""
        base = str(self.config.get("control_plane_url") or "").rstrip("/")
        if not base:
            raise RuntimeError("control_plane_url 未配置")
        body = {
            "nodeId": self.state["nodeId"],
            "agentToken": self.state["agentToken"],
        }
        request = urllib.request.Request(
            f"{base}/runtime-config",
            data=compact_json(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                result = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"刷新边缘运行配置失败 HTTP {exc.code}: {exc.read().decode(errors='ignore')}") from exc
        if int(result.get("code", -1)) != 0 or not isinstance(result.get("data"), dict):
            raise RuntimeError(f"刷新边缘运行配置失败: {result}")
        self.state.update(result["data"])
        self.save_state()

    def task_rows(self) -> list[tuple[str, int]]:
        rows: list[tuple[str, int]] = []
        for line in read_text(str(self.tasks_path)).splitlines():
            fields = line.split("\t")
            if len(fields) >= 2:
                try:
                    rows.append((fields[0], int(fields[1])))
                except ValueError:
                    continue
        return rows

    def task_health(self) -> list[dict[str, Any]]:
        pipelines: list[dict[str, Any]] = []
        for task_id, port in self.task_rows():
            item: dict[str, Any] = {"id": task_id, "name": task_id, "status": "offline", "fps": 0}
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1.5) as response:
                    health = json.loads(response.read().decode())
                item.update({
                    "status": "online",
                    "fps": health.get("npu_throughput_fps") or health.get("fps") or 0,
                    "inferEndpoint": health.get("infer_ep"),
                    "decodeEndpoint": health.get("decode_ep"),
                    "dropped": health.get("dropped") or health.get("dropped_frames") or 0,
                })
            except Exception:
                pass
            pipelines.append(item)
        return pipelines

    def heartbeat_payload(self) -> dict[str, Any]:
        total_now, idle_now = cpu_sample()
        total_before, idle_before = self.cpu_previous
        self.cpu_previous = (total_now, idle_now)
        delta_total = max(1, total_now - total_before)
        cpu_percent = 100.0 * (1.0 - max(0, idle_now - idle_before) / delta_total)
        mem = read_meminfo()
        mem_total = mem.get("MemTotal", 0)
        mem_available = mem.get("MemAvailable", mem.get("MemFree", 0))
        mem_used = max(0, mem_total - mem_available)
        disk = shutil.disk_usage("/")
        temp_values = temperatures()
        pipelines = self.task_health()
        remote = dict(self.config.get("remote_access") or {})
        if remote.get("enabled"):
            remote["status"] = "online" if service_active("easyaiot-runtime-rk3588-frpc.service") else "offline"
        payload = {
            "name": self.config.get("node_name") or socket.gethostname(),
            "hostname": socket.gethostname(),
            "host": local_ip(),
            "nodeKind": "edge_box",
            "hardwareProvider": "rockchip",
            "socModel": "RK3588",
            "acceleratorType": "npu",
            "acceleratorCount": 3,
            "runtimeTarget": "rknn-rk3588",
            "runtimeVersion": "rk3588-mpp-rga-rknn",
            "agentVersion": AGENT_VERSION,
            "agentPort": int(self.config.get("agent_port") or 9100),
            "maxTaskCount": len(pipelines),
            "activeTasks": sum(item.get("status") == "online" for item in pipelines),
            "cpuPercent": round(max(0.0, min(cpu_percent, 100.0)), 2),
            "memPercent": round(mem_used * 100.0 / mem_total, 2) if mem_total else None,
            "memUsedBytes": mem_used,
            "memTotalBytes": mem_total,
            "diskPercent": round(disk.used * 100.0 / disk.total, 2) if disk.total else None,
            "diskUsedBytes": disk.used,
            "diskTotalBytes": disk.total,
            "temperatureC": round(max(temp_values), 1) if temp_values else None,
            "acceleratorInfo": npu_snapshot(),
            "pipelines": pipelines,
            "remoteAccess": remote,
        }
        self.latest_payload = payload
        return payload

    def publish(self, message_type: str, payload: dict[str, Any], retain: bool = False) -> None:
        if not self.client or not self.connected.is_set():
            return
        node_id = int(self.state["nodeId"])
        envelope = sign_envelope(self.state["agentToken"], message_type, node_id, payload)
        topic_key = "commandAck" if message_type == "command-ack" else message_type
        topic = self.state["topics"][topic_key]
        self.client.publish(topic, compact_json(envelope), qos=1, retain=retain)

    def on_connect(self, client, userdata, flags, rc, *args) -> None:
        if int(rc) != 0:
            print(f"[edge-agent] MQTT 连接失败 rc={rc}", flush=True)
            return
        self.connected.set()
        client.subscribe(self.state["topics"]["command"], qos=1)
        self.publish("status", {"online": True, "reason": "connected"}, retain=True)
        print("[edge-agent] MQTT 已连接，边缘遥测开始上报", flush=True)

    def on_disconnect(self, client, userdata, rc, *args) -> None:
        self.connected.clear()
        print(f"[edge-agent] MQTT 已断开 rc={rc}", flush=True)

    def on_message(self, client, userdata, message) -> None:
        command_id = "unknown"
        try:
            envelope = json.loads(message.payload.decode())
            payload = verify_envelope(envelope, self.state["agentToken"], int(self.state["nodeId"]), "command")
            message_id = str(envelope.get("messageId") or "")
            now = time.time()
            self.seen_command_messages = {
                key: timestamp for key, timestamp in self.seen_command_messages.items()
                if now - timestamp < 300
            }
            if not message_id:
                raise ValueError("命令缺少 messageId")
            if message_id in self.seen_command_messages:
                print(f"[edge-agent] 忽略重复命令消息 {message_id}", flush=True)
                return
            self.seen_command_messages[message_id] = now
            command_id = str(payload.get("commandId") or "")
            result = self.execute_command(str(payload.get("command") or ""))
            self.publish("command-ack", {"commandId": command_id, "status": "success", "result": result})
        except Exception as exc:
            self.publish("command-ack", {"commandId": command_id, "status": "failed", "error": str(exc)})

    def execute_command(self, command: str) -> str:
        if command in ("ping", "status"):
            return "pong" if command == "ping" else compact_json(self.heartbeat_payload())
        if command in ("runtime.restart", "runtime.reload"):
            for task_id, _ in self.task_rows():
                subprocess.run(["systemctl", "restart", f"easyaiot-runtime-rk3588@{task_id}.service"],
                               check=True, timeout=30)
            return "runtime restarted"
        if command == "frp.restart":
            if not (self.config.get("remote_access") or {}).get("enabled"):
                raise ValueError("FRP 未启用")
            subprocess.run(["systemctl", "restart", "easyaiot-runtime-rk3588-frpc.service"],
                           check=True, timeout=20)
            return "frp restarted"
        raise ValueError(f"不支持的命令: {command}")

    def start_http(self) -> None:
        agent = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path not in ("/health", "/api/v1/status"):
                    self.send_error(404)
                    return
                body = compact_json({
                    "status": "ok",
                    "platform": "rk3588",
                    "nodeId": agent.state.get("nodeId"),
                    "mqttConnected": agent.connected.is_set(),
                    "telemetry": agent.latest_payload,
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        self.httpd = ThreadingHTTPServer(("0.0.0.0", int(self.config.get("agent_port") or 9100)), Handler)
        threading.Thread(target=self.httpd.serve_forever, name="edge-agent-http", daemon=True).start()

    def run(self) -> None:
        if not self.config.get("enabled"):
            raise RuntimeError("edge-agent 未启用")
        self.enroll()
        import paho.mqtt.client as mqtt

        brokers = self.state.get("mqttBrokerUrls") or []
        if not brokers:
            raise RuntimeError("纳管响应没有 MQTT Broker")
        host, port, secure = parse_broker(str(brokers[0]))
        try:
            self.client = mqtt.Client(client_id=self.state["mqttClientId"], clean_session=True)
        except TypeError:
            self.client = mqtt.Client(client_id=self.state["mqttClientId"])
        self.client.username_pw_set(self.state["mqttUsername"], self.state["mqttPassword"])
        if secure:
            self.client.tls_set()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        self.start_http()
        self.client.connect(host, port, keepalive=30)
        self.client.loop_start()
        interval = int(self.config.get("heartbeat_interval_seconds") or 10)
        try:
            while not self.stop_event.wait(interval):
                if self.connected.is_set():
                    self.publish("heartbeat", self.heartbeat_payload())
        finally:
            if self.connected.is_set():
                self.publish("status", {"online": False, "reason": "shutdown"}, retain=True)
                time.sleep(0.2)
            self.client.loop_stop()
            self.client.disconnect()
            if self.httpd:
                self.httpd.shutdown()

    def stop(self, *_args) -> None:
        self.stop_event.set()


def main() -> int:
    parser = argparse.ArgumentParser(description="EasyAIoT RK3588 MQTT edge agent")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    agent = Agent(Path(args.config))
    signal.signal(signal.SIGTERM, agent.stop)
    signal.signal(signal.SIGINT, agent.stop)
    agent.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
