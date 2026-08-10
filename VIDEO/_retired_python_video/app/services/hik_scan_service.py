"""网段扫描与 NVR 通道枚举（基于 hiktoolno / hiktools core）。"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Sequence

from app.vendor.hiktools.core.device_role import is_nvr_role, role_label
from app.vendor.hiktools.core.models import Credential, Device
from app.vendor.hiktools.core.nvr import inventory_nvr
from app.vendor.hiktools.core.scanner import scan, scan_one_budget
from app.vendor.hiktools.core.targets import estimate_scan_tasks, parse_ports, parse_targets
from app.vendor.hiktools.core.vendors import vendor_label

DEFAULT_PORTS = "80,443,8000,8443"


def _parse_credentials(
    username: str | None = None,
    password: str | None = None,
    credentials: Sequence[dict[str, Any]] | None = None,
) -> list[Credential]:
    """解析凭证列表，按顺序尝试（与 hiktoolno -c 重复参数一致）。"""
    out: list[Credential] = []
    if credentials:
        for item in credentials:
            if not isinstance(item, dict):
                continue
            u = (item.get("username") or "").strip()
            if u:
                out.append(Credential(u, item.get("password") or ""))
    if not out:
        u = (username or "").strip()
        if u:
            out.append(Credential(u, password or ""))
    return out


def _device_row(d: Device) -> dict[str, Any]:
    return {
        "ip": d.ip,
        "port": d.port,
        "scheme": d.scheme,
        "vendor": d.vendor,
        "vendor_label": vendor_label(d.vendor),
        "device_role": d.device_role,
        "role_label": role_label(d.device_role),
        "is_nvr": is_nvr_role(d.device_role),
        "is_recognized": d.is_recognized,
        "confidence": d.confidence,
        "model": d.model,
        "serial": d.serial,
        "firmware": d.firmware,
        "device_name": d.device_name,
        "device_type": d.device_type,
        "mac": d.mac,
        "rtsp_url": d.rtsp_url,
        "source": d.source,
        "error": d.error,
        "url": d.url,
        "auth_username": d.evidence.get("authenticated_as"),
    }


def _aggregate_by_ip(devices: Sequence[Device]) -> list[dict[str, Any]]:
    by_ip: dict[str, list[Device]] = defaultdict(list)
    for d in devices:
        by_ip[d.ip].append(d)
    rows: list[dict[str, Any]] = []
    for ip, group in sorted(by_ip.items()):
        group.sort(key=lambda x: x.port)
        primary = next((d for d in group if d.is_recognized), group[0])
        auth_username = next(
            (d.evidence.get("authenticated_as") for d in group if d.evidence.get("authenticated_as")),
            None,
        )
        rows.append(
            {
                "ip": ip,
                "ports": [d.port for d in group],
                "port": primary.port,
                "auth_username": auth_username,
                "vendor": primary.vendor,
                "vendor_label": vendor_label(primary.vendor),
                "device_role": primary.device_role,
                "role_label": role_label(primary.device_role),
                "is_nvr": is_nvr_role(primary.device_role),
                "is_recognized": any(d.is_recognized for d in group),
                "confidence": max((d.confidence for d in group), default=0),
                "model": next((d.model for d in group if d.model), None),
                "serial": next((d.serial for d in group if d.serial), None),
                "device_name": next((d.device_name for d in group if d.device_name), None),
                "mac": next((d.mac for d in group if d.mac), None),
                "rtsp_url": next((d.rtsp_url for d in group if d.rtsp_url), None),
                "devices": [_device_row(d) for d in group],
            }
        )
    return rows


def estimate_scan_wall_timeout(
    targets_raw: str,
    *,
    ports_spec: str = DEFAULT_PORTS,
    concurrency: int = 200,
    timeout: float = 3.0,
) -> float:
    """估算整次网段扫描最长等待时间（秒）。"""
    task_count = max(1, estimate_scan_tasks(targets_raw, ports_spec))
    batches = (task_count + max(1, concurrency) - 1) // max(1, concurrency)
    per_task = scan_one_budget(timeout)
    return min(300.0, max(15.0, batches * per_task + 8.0))


async def _run_segment_scan(
    targets_raw: str,
    *,
    ports_spec: str = DEFAULT_PORTS,
    username: str | None = None,
    password: str | None = None,
    credentials: Sequence[dict[str, Any]] | None = None,
    concurrency: int = 200,
    timeout: float = 3.0,
    only_hits: bool = True,
    nvr_only: bool = False,
    exclude_nvr: bool = False,
) -> list[dict[str, Any]]:
    wall = estimate_scan_wall_timeout(
        targets_raw,
        ports_spec=ports_spec,
        concurrency=concurrency,
        timeout=timeout,
    )

    async def _inner() -> list[dict[str, Any]]:
        ports = parse_ports(ports_spec)
        targets = parse_targets(targets_raw, ports=ports)
        if not targets:
            raise ValueError("解析后目标列表为空，请填写有效网段或 IP")

        creds = _parse_credentials(username, password, credentials)
        devices: list[Device] = []
        async for item in scan(
            targets,
            credentials=creds,
            concurrency=concurrency,
            timeout=timeout,
            only_hits=only_hits,
        ):
            if nvr_only and not is_nvr_role(item.device_role):
                continue
            if exclude_nvr and is_nvr_role(item.device_role):
                continue
            devices.append(item)

        rows = _aggregate_by_ip(devices)
        if nvr_only:
            rows = [r for r in rows if r.get("is_nvr")]
        elif exclude_nvr:
            rows = [r for r in rows if not r.get("is_nvr")]
        return rows

    try:
        return await asyncio.wait_for(_inner(), timeout=wall)
    except asyncio.TimeoutError as exc:
        raise ValueError(
            f"扫描超时（约 {int(wall)} 秒），请缩小目标范围、减少端口或降低单点超时后重试"
        ) from exc


def scan_segment(
    targets_raw: str,
    *,
    ports_spec: str = DEFAULT_PORTS,
    username: str | None = None,
    password: str | None = None,
    credentials: Sequence[dict[str, Any]] | None = None,
    concurrency: int = 200,
    timeout: float = 3.0,
    only_hits: bool = True,
    nvr_only: bool = False,
    exclude_nvr: bool = False,
) -> list[dict[str, Any]]:
    return asyncio.run(
        _run_segment_scan(
            targets_raw,
            ports_spec=ports_spec,
            username=username,
            password=password,
            credentials=credentials,
            concurrency=concurrency,
            timeout=timeout,
            only_hits=only_hits,
            nvr_only=nvr_only,
            exclude_nvr=exclude_nvr,
        )
    )


async def _run_nvr_enumerate(
    ip: str,
    port: int,
    *,
    username: str | None = None,
    password: str | None = None,
    credentials: Sequence[dict[str, Any]] | None = None,
    timeout: float = 5.0,
    vendor: str | None = None,
    probe_cameras: bool = True,
    only_mounted: bool = True,
    channel_filter: str | None = None,
) -> dict[str, Any]:
    creds = _parse_credentials(username, password, credentials)
    if not creds:
        raise ValueError("枚举 NVR 通道需要至少一组用户名和密码")
    inv = await inventory_nvr(
        ip.strip(),
        int(port),
        credentials=creds,
        timeout=timeout,
        probe_cameras=probe_cameras,
        vendor=vendor,
        only_mounted=only_mounted,
        channel_filter=channel_filter,
    )
    result = inv.to_dict()
    if inv.auth_username:
        result["auth_username"] = inv.auth_username
    return result


def enumerate_nvr_channels(
    ip: str,
    port: int,
    *,
    username: str | None = None,
    password: str | None = None,
    credentials: Sequence[dict[str, Any]] | None = None,
    timeout: float = 5.0,
    vendor: str | None = None,
    probe_cameras: bool = True,
    only_mounted: bool = True,
    channel_filter: str | None = None,
) -> dict[str, Any]:
    return asyncio.run(
        _run_nvr_enumerate(
            ip,
            port,
            username=username,
            password=password,
            credentials=credentials,
            timeout=timeout,
            vendor=vendor,
            probe_cameras=probe_cameras,
            only_mounted=only_mounted,
            channel_filter=channel_filter,
        )
    )
