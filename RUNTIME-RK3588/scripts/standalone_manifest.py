#!/usr/bin/env python3
"""Validate an RK3588 standalone task manifest and compile per-stream INI files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class ManifestError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def clean_text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    require(isinstance(value, str), f"{label} 必须是字符串")
    value = value.strip()
    require(allow_empty or bool(value), f"{label} 不能为空")
    require("\n" not in value and "\r" not in value and "\t" not in value,
            f"{label} 不能包含换行或制表符")
    return value


def safe_id(value: Any, label: str) -> str:
    value = clean_text(value, label)
    require(bool(ID_RE.fullmatch(value)),
            f"{label}={value!r} 只能使用字母、数字、下划线和连字符，且最长 64 位")
    return value


def integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    require(not isinstance(value, bool), f"{label} 必须是整数")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"{label} 必须是整数") from exc
    require(minimum <= result <= maximum,
            f"{label} 必须位于 {minimum}–{maximum}，当前为 {result}")
    return result


def number(value: Any, label: str, minimum: float, maximum: float) -> float:
    require(not isinstance(value, bool), f"{label} 必须是数字")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"{label} 必须是数字") from exc
    require(minimum <= result <= maximum,
            f"{label} 必须位于 {minimum}–{maximum}，当前为 {result}")
    return result


def boolean(value: Any, label: str) -> bool:
    require(isinstance(value, bool), f"{label} 必须是 true 或 false")
    return value


def resolve_file(value: Any, label: str, manifest_dir: Path, suffix: str | None = None) -> Path:
    raw = clean_text(value, label)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = manifest_dir / path
    path = path.resolve()
    require(path.is_file(), f"{label} 不存在或不是文件: {path}")
    require(path.stat().st_size > 0, f"{label} 是空文件: {path}")
    if suffix:
        require(path.suffix.lower() == suffix, f"{label} 必须是 {suffix} 文件: {path}")
    return path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def merged(base: dict[str, Any], override: Any, label: str) -> dict[str, Any]:
    if override is None:
        return dict(base)
    require(isinstance(override, dict), f"{label} 必须是对象")
    result = dict(base)
    result.update(override)
    return result


def compile_manifest(
    manifest_path: Path,
    output_dir: Path,
    prefix: Path,
    log_dir: Path,
    default_classes: Path,
) -> dict[str, Any]:
    require(manifest_path.is_file(), f"任务清单不存在: {manifest_path}")
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"无法读取 JSON 任务清单 {manifest_path}: {exc}") from exc

    require(isinstance(document, dict), "任务清单根节点必须是 JSON 对象")
    require(document.get("version") == 1, "任务清单 version 必须为 1")
    manifest_dir = manifest_path.resolve().parent
    prefix = prefix.resolve()
    log_dir = log_dir.resolve()
    default_classes = default_classes.resolve()

    runtime_defaults = {
        "width": 1920,
        "height": 1080,
        "fps": 25,
        "frame_skip": 1,
        "npu_workers": 3,
        "task_queue_depth": 2,
        "frame_pool_size": 6,
        "mpp_buffer_count": 8,
        "use_sram": True,
        "enable_perf_query": False,
    }
    runtime_defaults = merged(runtime_defaults, document.get("runtime"), "runtime")

    mqtt_defaults = {
        "broker_urls": "",
        "username": "",
        "password": "",
        "tenant": "default",
        "transport": "off",
    }
    mqtt_defaults = merged(mqtt_defaults, document.get("mqtt"), "mqtt")

    control_plane = merged({
        "enabled": False,
        "url": "",
        "join_token": "",
        "node_name": "",
        "heartbeat_interval_seconds": 10,
        "agent_port": 9100,
    }, document.get("control_plane"), "control_plane")
    control_enabled = boolean(control_plane.get("enabled"), "control_plane.enabled")
    control_url = clean_text(control_plane.get("url", ""), "control_plane.url", allow_empty=True).rstrip("/")
    join_token = clean_text(control_plane.get("join_token", ""), "control_plane.join_token", allow_empty=True)
    node_name = clean_text(control_plane.get("node_name", ""), "control_plane.node_name", allow_empty=True)
    heartbeat_interval = integer(
        control_plane.get("heartbeat_interval_seconds"),
        "control_plane.heartbeat_interval_seconds", 5, 300,
    )
    agent_port = integer(control_plane.get("agent_port"), "control_plane.agent_port", 1024, 65535)
    if control_enabled:
        require(control_url.startswith(("http://", "https://")),
                "control_plane.url 必须使用 http:// 或 https://")

    remote_access = merged({
        "enabled": False,
        "provider": "frp",
        "server_addr": "",
        "server_port": 7000,
        "auth_token": "",
        "frp_version": "0.71.1",
        "frpc_binary": "",
        "download_url": "",
        "sha256": "",
        "service": {"enabled": True, "remote_port": 19100, "public_url": ""},
        "ssh": {"enabled": False, "remote_port": 16022, "public_host": "", "username": "root"},
    }, document.get("remote_access"), "remote_access")
    remote_enabled = boolean(remote_access.get("enabled"), "remote_access.enabled")
    provider = clean_text(remote_access.get("provider", "frp"), "remote_access.provider")
    require(provider == "frp", "remote_access.provider 当前只支持 frp")
    server_addr = clean_text(remote_access.get("server_addr", ""), "remote_access.server_addr", allow_empty=True)
    server_port = integer(remote_access.get("server_port"), "remote_access.server_port", 1, 65535)
    auth_token = clean_text(remote_access.get("auth_token", ""), "remote_access.auth_token", allow_empty=True)
    frp_version = clean_text(remote_access.get("frp_version", "0.71.1"), "remote_access.frp_version")
    frpc_binary = clean_text(remote_access.get("frpc_binary", ""), "remote_access.frpc_binary", allow_empty=True)
    download_url = clean_text(remote_access.get("download_url", ""), "remote_access.download_url", allow_empty=True)
    frp_sha256 = clean_text(remote_access.get("sha256", ""), "remote_access.sha256", allow_empty=True).lower()
    if frp_sha256:
        require(bool(re.fullmatch(r"[0-9a-f]{64}", frp_sha256)),
                "remote_access.sha256 必须是 64 位十六进制")
    service_tunnel = merged(
        {"enabled": True, "remote_port": 19100, "public_url": ""},
        remote_access.get("service"), "remote_access.service",
    )
    ssh_tunnel = merged(
        {"enabled": False, "remote_port": 16022, "public_host": "", "username": "root"},
        remote_access.get("ssh"), "remote_access.ssh",
    )
    service_enabled = boolean(service_tunnel.get("enabled"), "remote_access.service.enabled")
    ssh_enabled = boolean(ssh_tunnel.get("enabled"), "remote_access.ssh.enabled")
    service_remote_port = integer(
        service_tunnel.get("remote_port"), "remote_access.service.remote_port", 1, 65535,
    )
    ssh_remote_port = integer(ssh_tunnel.get("remote_port"), "remote_access.ssh.remote_port", 1, 65535)
    service_public_url = clean_text(
        service_tunnel.get("public_url", ""), "remote_access.service.public_url", allow_empty=True,
    )
    ssh_public_host = clean_text(
        ssh_tunnel.get("public_host", ""), "remote_access.ssh.public_host", allow_empty=True,
    )
    ssh_username = clean_text(ssh_tunnel.get("username", "root"), "remote_access.ssh.username")
    if service_public_url:
        require(service_public_url.startswith(("http://", "https://")),
                "remote_access.service.public_url 必须使用 http:// 或 https://")
    if ssh_public_host:
        require(bool(re.fullmatch(r"[A-Za-z0-9.:[\]_-]+", ssh_public_host)),
                "remote_access.ssh.public_host 不是有效的主机名或 IP")
    require(bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,31}", ssh_username)),
            "remote_access.ssh.username 不是有效的 Linux 用户名")
    if remote_enabled:
        require(control_enabled, "启用 FRP 前必须先启用 control_plane，才能在平台呈现入口状态")
        require(bool(server_addr), "remote_access.server_addr 不能为空")
        require(bool(auth_token), "remote_access.auth_token 不能为空")
        require(service_enabled or ssh_enabled, "FRP 至少启用 service 或 ssh 一条隧道")
        require(not (service_enabled and ssh_enabled and service_remote_port == ssh_remote_port),
                "service 与 ssh 的 FRP remote_port 不能相同")
        if not frpc_binary and not download_url:
            download_url = (
                f"https://github.com/fatedier/frp/releases/download/v{frp_version}/"
                f"frp_{frp_version}_linux_arm64.tar.gz"
            )
        if frp_version == "0.71.1" and not frp_sha256 and not frpc_binary:
            frp_sha256 = "8edf590b0c396fa42f9c147121a76af83cfc2002b08f5aef0ea1008c43482019"

    raw_models = document.get("models")
    require(isinstance(raw_models, dict) and raw_models, "models 必须是非空对象")
    models: dict[str, dict[str, Any]] = {}
    model_rows: list[list[str]] = []
    normalized_models: dict[str, dict[str, Any]] = {}
    for raw_key, raw_model in raw_models.items():
        key = safe_id(raw_key, "模型键")
        require(isinstance(raw_model, dict), f"models.{key} 必须是对象")
        source = resolve_file(raw_model.get("path"), f"models.{key}.path", manifest_dir, ".rknn")
        classes_value = raw_model.get("classes") or str(default_classes)
        classes = resolve_file(classes_value, f"models.{key}.classes", manifest_dir)
        expected_sha = raw_model.get("sha256")
        if expected_sha:
            expected_sha = clean_text(expected_sha, f"models.{key}.sha256").lower()
            require(bool(re.fullmatch(r"[0-9a-f]{64}", expected_sha)),
                    f"models.{key}.sha256 必须是 64 位十六进制")
            require(file_sha256(source) == expected_sha,
                    f"models.{key} 的 SHA256 校验失败: {source}")
        business_id = raw_model.get("business_model_id")
        if business_id is not None:
            business_id = integer(business_id, f"models.{key}.business_model_id", 1, 2_147_483_647)

        installed_model = prefix / "models" / f"{key}.rknn"
        installed_classes = prefix / "models" / f"{key}.names"
        models[key] = {
            "path": installed_model,
            "classes": installed_classes,
            "business_model_id": business_id,
        }
        model_rows.append([
            key, str(source), str(installed_model), str(classes), str(installed_classes)
        ])
        normalized = {"path": str(installed_model), "classes": str(installed_classes)}
        if business_id is not None:
            normalized["business_model_id"] = business_id
        if expected_sha:
            normalized["sha256"] = expected_sha
        normalized_models[key] = normalized

    raw_tasks = document.get("tasks")
    require(isinstance(raw_tasks, list) and raw_tasks, "tasks 必须是非空数组")
    task_rows: list[list[str]] = []
    normalized_tasks: list[dict[str, Any]] = []
    task_ids: set[str] = set()
    ports: set[int] = set()
    output_dir.mkdir(parents=True, exist_ok=True)
    configs_dir = output_dir / "tasks"
    configs_dir.mkdir(parents=True, exist_ok=True)

    for index, raw_task in enumerate(raw_tasks):
        label = f"tasks[{index}]"
        require(isinstance(raw_task, dict), f"{label} 必须是对象")
        task_id = safe_id(raw_task.get("id"), f"{label}.id")
        require(task_id not in task_ids, f"任务 ID 重复: {task_id}")
        task_ids.add(task_id)

        rtsp_url = clean_text(raw_task.get("rtsp_url"), f"{label}.rtsp_url")
        require(rtsp_url.startswith(("rtsp://", "rtsps://")),
                f"{label}.rtsp_url 必须使用 rtsp:// 或 rtsps://")
        model_keys = raw_task.get("models")
        require(isinstance(model_keys, list) and model_keys, f"{label}.models 必须是非空数组")
        selected: list[str] = []
        for model_index, raw_model_key in enumerate(model_keys):
            model_key = safe_id(raw_model_key, f"{label}.models[{model_index}]")
            require(model_key in models, f"{label} 引用了未定义模型: {model_key}")
            require(model_key not in selected, f"{label} 重复引用模型: {model_key}")
            selected.append(model_key)

        port = integer(raw_task.get("control_port", 8200 + index),
                       f"{label}.control_port", 8000, 9000)
        require(port not in ports, f"控制端口重复: {port}")
        ports.add(port)

        device_id = safe_id(raw_task.get("device_id", task_id), f"{label}.device_id")
        device_name = clean_text(raw_task.get("device_name", device_id),
                                 f"{label}.device_name")
        algorithm_name = clean_text(raw_task.get("algorithm_name", "detection"),
                                    f"{label}.algorithm_name")
        rtmp_url = clean_text(raw_task.get("rtmp_url", ""), f"{label}.rtmp_url", allow_empty=True)
        if rtmp_url:
            require(rtmp_url.startswith(("rtmp://", "rtmps://")),
                    f"{label}.rtmp_url 必须使用 rtmp:// 或 rtmps://")
        heartbeat_url = clean_text(raw_task.get("heartbeat_url", ""),
                                   f"{label}.heartbeat_url", allow_empty=True)

        runtime = merged(runtime_defaults, raw_task.get("runtime"), f"{label}.runtime")
        width = integer(runtime.get("width"), f"{label}.runtime.width", 64, 8192)
        height = integer(runtime.get("height"), f"{label}.runtime.height", 64, 8192)
        fps = integer(runtime.get("fps"), f"{label}.runtime.fps", 1, 240)
        frame_skip = integer(runtime.get("frame_skip"), f"{label}.runtime.frame_skip", 1, 120)
        npu_workers = integer(runtime.get("npu_workers"), f"{label}.runtime.npu_workers", 1, 3)
        queue_depth = integer(runtime.get("task_queue_depth"),
                              f"{label}.runtime.task_queue_depth", 1, 16)
        frame_pool = integer(runtime.get("frame_pool_size"),
                             f"{label}.runtime.frame_pool_size", 3, 32)
        mpp_buffers = integer(runtime.get("mpp_buffer_count"),
                              f"{label}.runtime.mpp_buffer_count", 4, 32)
        use_sram = boolean(runtime.get("use_sram"), f"{label}.runtime.use_sram")
        perf_query = boolean(runtime.get("enable_perf_query"),
                             f"{label}.runtime.enable_perf_query")

        alarm = merged({
            "enabled": False,
            "confidence_threshold": 0.5,
            "cooldown_time": 30,
            "alert_hook_url": "",
        }, raw_task.get("alarm"), f"{label}.alarm")
        alarm_enabled = boolean(alarm.get("enabled"), f"{label}.alarm.enabled")
        confidence = number(alarm.get("confidence_threshold"),
                            f"{label}.alarm.confidence_threshold", 0.01, 1.0)
        cooldown = integer(alarm.get("cooldown_time"), f"{label}.alarm.cooldown_time", 0, 86400)
        alert_hook = clean_text(alarm.get("alert_hook_url", ""),
                                f"{label}.alarm.alert_hook_url", allow_empty=True)

        mqtt = merged(mqtt_defaults, raw_task.get("mqtt"), f"{label}.mqtt")
        broker_urls = clean_text(mqtt.get("broker_urls", ""),
                                 f"{label}.mqtt.broker_urls", allow_empty=True)
        mqtt_username = clean_text(mqtt.get("username", ""),
                                   f"{label}.mqtt.username", allow_empty=True)
        mqtt_password = clean_text(mqtt.get("password", ""),
                                   f"{label}.mqtt.password", allow_empty=True)
        mqtt_tenant = clean_text(mqtt.get("tenant", "default"), f"{label}.mqtt.tenant")
        transport = clean_text(mqtt.get("transport", "off"), f"{label}.mqtt.transport")
        require(transport in {"off", "mqtt", "http"},
                f"{label}.mqtt.transport 只能是 off、mqtt 或 http")

        model_lines: list[str] = []
        for model_index, model_key in enumerate(selected):
            spec = models[model_key]
            suffix = "" if model_index == 0 else f"_{model_key}"
            model_lines.append(f"model_path{suffix}={spec['path']}")
            model_lines.append(f"classes_path{suffix}={spec['classes']}")
            if spec["business_model_id"] is not None:
                model_lines.append(f"model_id{suffix}={spec['business_model_id']}")

        regions = raw_task.get("regions", {})
        require(isinstance(regions, dict), f"{label}.regions 必须是对象")
        region_lines: list[str] = []
        for raw_region_id, points in regions.items():
            region_id = safe_id(raw_region_id, f"{label}.regions 的键")
            require(isinstance(points, list) and len(points) >= 3,
                    f"{label}.regions.{region_id} 至少需要三个点")
            region_lines.append(
                f"{region_id}={json.dumps(points, ensure_ascii=False, separators=(',', ':'))}"
            )

        task_log_dir = log_dir / task_id
        devices_json = json.dumps([{
            "device_id": device_id,
            "device_name": device_name,
            "rtsp_url": rtsp_url,
        }], ensure_ascii=False, separators=(",", ":"))
        ini = f"""# 由 RUNTIME-RK3588 任务清单生成；一路视频一份配置、一个独立进程。
[video]
rtsp_url={rtsp_url}
rtmp_url={rtmp_url}
width={width}
height={height}
fps={fps}

[ai]
enable=true
{chr(10).join(model_lines)}
threads={npu_workers}
frame_skip={frame_skip}

[rk3588]
npu_workers={npu_workers}
task_queue_depth={queue_depth}
frame_pool_size={frame_pool}
mpp_buffer_count={mpp_buffers}
use_sram={'true' if use_sram else 'false'}
enable_perf_query={'true' if perf_query else 'false'}

[alarm]
enable={'true' if alarm_enabled else 'false'}
confidence_threshold={confidence:g}
cooldown_time={cooldown}
image_dir={task_log_dir / 'alerts'}

[task]
id={task_id}
control_port={port}

[video_task]
device_id={device_id}
device_name={device_name}
task_type=realtime
algorithm_name={algorithm_name}
heartbeat_url={heartbeat_url}
heartbeat_interval_sec=10
log_path={task_log_dir}
alert_image_dir={task_log_dir / 'alerts'}
alert_hook_url={alert_hook}
algo_bus_transport={transport}
mqtt_broker_urls={broker_urls}
mqtt_username={mqtt_username}
mqtt_password={mqtt_password}
mqtt_client_id=algo-rk3588-{task_id}
mqtt_tenant={mqtt_tenant}
headless=true
frame_skip={frame_skip}
devices_json={devices_json}

[mqtt]
broker_urls={broker_urls}
username={mqtt_username}
password={mqtt_password}
client_id=algo-rk3588-{task_id}
tenant={mqtt_tenant}
transport={transport}

[features]
enable_rtmp={'true' if bool(rtmp_url) else 'false'}
enable_draw={'true' if bool(rtmp_url) else 'false'}
enable_alarm={'true' if alarm_enabled else 'false'}

[regions]
{chr(10).join(region_lines)}
"""
        (configs_dir / f"{task_id}.ini").write_text(ini, encoding="utf-8")
        task_rows.append([task_id, str(port)])

        normalized_task = dict(raw_task)
        normalized_task.update({
            "id": task_id,
            "device_id": device_id,
            "device_name": device_name,
            "rtsp_url": rtsp_url,
            "models": selected,
            "control_port": port,
        })
        normalized_tasks.append(normalized_task)

    def write_tsv(path: Path, rows: list[list[str]]) -> None:
        path.write_text("".join("\t".join(row) + "\n" for row in rows), encoding="utf-8")

    write_tsv(output_dir / "models.tsv", model_rows)
    write_tsv(output_dir / "tasks.tsv", task_rows)
    service_public_url = service_public_url or (
        f"http://{server_addr}:{service_remote_port}" if remote_enabled and service_enabled else ""
    )
    ssh_public_host = ssh_public_host or (server_addr if remote_enabled and ssh_enabled else "")
    edge_agent_config = {
        "spec_version": "easyaiot.edge.telemetry/v1",
        "enabled": control_enabled,
        "control_plane_url": control_url,
        "join_token": join_token,
        "node_name": node_name,
        "heartbeat_interval_seconds": heartbeat_interval,
        "agent_port": agent_port,
        "remote_access": {
            "enabled": remote_enabled,
            "provider": provider,
            "status": "configured" if remote_enabled else "disabled",
            "serviceEnabled": service_enabled if remote_enabled else False,
            "serviceAccessUrl": service_public_url,
            "sshEnabled": ssh_enabled if remote_enabled else False,
            "sshAccessHost": ssh_public_host,
            "sshAccessPort": ssh_remote_port if remote_enabled and ssh_enabled else None,
            "sshUsername": ssh_username if remote_enabled and ssh_enabled else None,
        },
    }
    (output_dir / "edge-agent.json").write_text(
        json.dumps(edge_agent_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if remote_enabled:
        def toml_string(value: str) -> str:
            return json.dumps(value, ensure_ascii=False)

        frpc_lines = [
            f"serverAddr = {toml_string(server_addr)}",
            f"serverPort = {server_port}",
            f"user = {toml_string('easyaiot-rk3588')}",
            "auth.method = \"token\"",
            f"auth.token = {toml_string(auth_token)}",
            "loginFailExit = false",
            "",
        ]
        if service_enabled:
            frpc_lines.extend([
                "[[proxies]]",
                "name = \"easyaiot-edge-service\"",
                "type = \"tcp\"",
                "localIP = \"127.0.0.1\"",
                f"localPort = {agent_port}",
                f"remotePort = {service_remote_port}",
                "",
            ])
        if ssh_enabled:
            frpc_lines.extend([
                "[[proxies]]",
                "name = \"easyaiot-edge-ssh\"",
                "type = \"tcp\"",
                "localIP = \"127.0.0.1\"",
                "localPort = 22",
                f"remotePort = {ssh_remote_port}",
                "",
            ])
        (output_dir / "frpc.toml").write_text("\n".join(frpc_lines), encoding="utf-8")
        (output_dir / "frpc-source.tsv").write_text(
            "\t".join((frpc_binary, download_url, frp_sha256, frp_version)) + "\n",
            encoding="utf-8",
        )
    normalized_document = {
        "version": 1,
        "runtime": runtime_defaults,
        "mqtt": mqtt_defaults,
        "control_plane": {
            "enabled": control_enabled,
            "url": control_url,
            "join_token": join_token,
            "node_name": node_name,
            "heartbeat_interval_seconds": heartbeat_interval,
            "agent_port": agent_port,
        },
        "remote_access": remote_access,
        "models": normalized_models,
        "tasks": normalized_tasks,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(normalized_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "tasks": len(task_rows),
        "models": len(model_rows),
        "bindings": sum(len(task["models"]) for task in normalized_tasks),
        "task_ids": [row[0] for row in task_rows],
        "control_plane": control_enabled,
        "remote_access": remote_enabled,
    }


def create_legacy_manifest(args: argparse.Namespace) -> None:
    document = {
        "version": 1,
        "models": {
            "default": {
                "path": str(Path(args.model).expanduser().resolve()),
                "classes": str(Path(args.classes).expanduser().resolve()),
            }
        },
        "tasks": [{
            "id": "camera-001",
            "device_id": args.device_id,
            "device_name": args.device_name,
            "rtsp_url": args.rtsp,
            "models": ["default"],
            "control_port": args.control_port,
        }],
    }
    Path(args.output).write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    compile_parser = subparsers.add_parser("compile", help="校验清单并生成逐路 INI")
    compile_parser.add_argument("--manifest", required=True, type=Path)
    compile_parser.add_argument("--output", required=True, type=Path)
    compile_parser.add_argument("--prefix", required=True, type=Path)
    compile_parser.add_argument("--log-dir", required=True, type=Path)
    compile_parser.add_argument("--default-classes", required=True, type=Path)

    legacy_parser = subparsers.add_parser("legacy", help="把旧单流参数转换为任务清单")
    legacy_parser.add_argument("--output", required=True)
    legacy_parser.add_argument("--rtsp", required=True)
    legacy_parser.add_argument("--model", required=True)
    legacy_parser.add_argument("--classes", required=True)
    legacy_parser.add_argument("--device-id", default="rk3588-camera-001")
    legacy_parser.add_argument("--device-name", default="RK3588独立摄像头")
    legacy_parser.add_argument("--control-port", type=int, default=8123)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "legacy":
            create_legacy_manifest(args)
            return 0
        summary = compile_manifest(
            args.manifest.resolve(), args.output.resolve(), args.prefix,
            args.log_dir, args.default_classes,
        )
        print(
            f"清单有效：{summary['tasks']} 路 RTSP、{summary['models']} 个 RKNN 模型、"
            f"{summary['bindings']} 个任务模型绑定；任务={','.join(summary['task_ids'])}"
        )
        return 0
    except ManifestError as exc:
        print(f"任务清单无效：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
