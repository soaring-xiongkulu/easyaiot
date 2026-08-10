from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Sequence

import httpx

from .dahua_cgi import (
    DahuaCgiResult,
    fetch_dahua_cgi,
    parse_dahua_device_class,
    parse_dahua_table_rows,
)
from .fingerprint import parse_dahua_cgi, parse_isapi_xml
from .isapi import fetch_device_info, fetch_isapi_path
from .models import Credential, Device
from .rtsp import build_camera_direct_rtsp, build_nvr_channel_rtsp
from .scanner import PROBE_TIMEOUT, USER_AGENT, _make_ssl_context, _scheme_for_port, scan_one
from .vendors import VENDOR_DAHUA, VENDOR_HIKVISION

INPUT_PROXY_CHANNELS = "/ISAPI/ContentMgmt/InputProxy/channels"
INPUT_PROXY_STATUS = "/ISAPI/ContentMgmt/InputProxy/channels/status"
VIDEO_INPUT_CHANNELS = "/ISAPI/System/Video/inputs/channels"

DAHUA_DEVICE_CLASS = "/cgi-bin/magicBox.cgi?action=getDeviceClass"
DAHUA_SYSTEM_INFO = "/cgi-bin/magicBox.cgi?action=getSystemInfo"
DAHUA_DEVICE_TYPE = "/cgi-bin/magicBox.cgi?action=getDeviceType"

_GENERIC_CAMERA_NAME = re.compile(r'^camera\s*0*\d+\s*$', re.IGNORECASE)


def _effective_channel_name(
    name: str | None,
    channel_id: int,
    camera_ip: str | None = None,
) -> str | None:
    """海康 VideoInput 等接口常返回重复的 Camera 01，改为带通道号/IPC IP 的可区分名称。"""
    n = (name or '').strip()
    if n and not _GENERIC_CAMERA_NAME.match(n):
        return n
    if camera_ip:
        return f'CH{channel_id}-{camera_ip}'
    return f'CH{channel_id}'


DAHUA_CHANNEL_CONFIGS = (
    "RemoteDevice",
    "RemoteVideoInput",
    "NetCamera",
    "LogicDevice",
)

_CHANNEL_LIST_TAGS = (
    "InputProxyChannel",
    "VideoInputChannel",
    "InputProxyChannelStatus",
)


def _xml_text(block: str, tag: str) -> str | None:
    m = re.search(
        rf"<(?:[\w-]+:)?{tag}>\s*([^<]*?)\s*</(?:[\w-]+:)?{tag}>",
        block,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    return m.group(1).strip() or None


def _split_channel_blocks(xml_text: str) -> list[str]:
    for tag in _CHANNEL_LIST_TAGS:
        parts = re.split(rf"<{tag}\b", xml_text, flags=re.IGNORECASE)
        if len(parts) > 1:
            return parts[1:]
    return []


def _parse_channel_block(block: str) -> dict[str, Any]:
    port_raw = _xml_text(block, "managePortNo") or _xml_text(block, "srcInputPort")
    port = int(port_raw) if port_raw and port_raw.isdigit() else None
    online_raw = _xml_text(block, "online")
    online: bool | None = None
    if online_raw is not None:
        online = online_raw.lower() == "true"
    enabled_raw = _xml_text(block, "enabled")
    enabled: bool | None = None
    if enabled_raw is not None:
        enabled = enabled_raw.lower() == "true"
    channel_id_raw = (
        _xml_text(block, "id")
        or _xml_text(block, "videoInputChannelID")
        or _xml_text(block, "srcInputPort")
        or _xml_text(block, "inputPort")
    )
    camera_ip = _xml_text(block, "ipAddress")
    raw_name = _xml_text(block, "name") or _xml_text(block, "channelName")
    try:
        cid = int(channel_id_raw) if channel_id_raw else None
    except ValueError:
        cid = None
    display_name = (
        _effective_channel_name(raw_name, cid, camera_ip)
        if cid is not None
        else raw_name
    )
    return {
        "channel_id": channel_id_raw,
        "name": display_name,
        "ip": camera_ip,
        "port": port,
        "protocol": _xml_text(block, "proxyProtocol"),
        "username": _xml_text(block, "userName"),
        "device_id": _xml_text(block, "deviceID"),
        "stream_type": _xml_text(block, "streamType"),
        "online": online,
        "enabled": enabled,
        "connection_status": _xml_text(block, "chanDetectResult"),
    }


_OFFLINE_CONN_MARKERS = (
    'netunreachable',
    'offline',
    'notconnected',
    'disconnect',
    'loginfailed',
    'networkerror',
    'streamlimit',
    'userlocked',
    'maxconnect',
)


def is_mounted_channel_row(row: dict[str, Any]) -> bool:
    """判断通道是否已挂载且可用（过滤空槽位 / 离线通道）。"""
    online = row.get('online')
    if online is False:
        return False

    conn = (row.get('connection_status') or '').strip().lower()
    if conn and any(marker in conn for marker in _OFFLINE_CONN_MARKERS):
        return False

    if online is True:
        return True

    # 无在线状态时（如部分大华接口）回退到配置字段判断
    ip = (row.get('ip') or row.get('camera_ip') or '').strip()
    if ip:
        return True
    device_id = (row.get('device_id') or '').strip()
    if device_id:
        return True
    return False


def filter_mounted_channel_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """仅保留已挂载摄像头的通道。"""
    return [row for row in rows if is_mounted_channel_row(row)]


def is_registerable_channel_row(row: dict[str, Any]) -> bool:
    """登记挂载时判断通道是否有效（比预览宽松：含暂离线但有 IP 的通道）。"""
    try:
        cid = int(row.get('channel_id') or 0)
    except (TypeError, ValueError):
        return False
    if cid <= 0:
        return False

    ip = (row.get('ip') or row.get('camera_ip') or '').strip()
    device_id = (row.get('device_id') or '').strip()
    if ip or device_id:
        return True
    if row.get('online') is True:
        return True

    name = (row.get('name') or '').strip()
    if name and not _GENERIC_CAMERA_NAME.match(name):
        return True
    return False


def filter_registerable_channel_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """登记 NVR 时保留已配置通道，过滤空槽位。"""
    return [row for row in rows if is_registerable_channel_row(row)]


def filter_channel_rows(
    rows: list[dict[str, Any]],
    *,
    mode: str = 'mounted',
) -> list[dict[str, Any]]:
    """按场景过滤通道：mounted=仅在线可用，registerable=登记挂载，all=不过滤。"""
    if mode == 'all':
        return list(rows)
    if mode == 'registerable':
        return filter_registerable_channel_rows(rows)
    return filter_mounted_channel_rows(rows)


def parse_input_proxy_channels(xml_text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for block in _split_channel_blocks(xml_text):
        row = _parse_channel_block(block)
        cid = row.get("channel_id")
        if cid is None:
            continue
        try:
            row["channel_id"] = int(cid)
        except ValueError:
            continue
        out.append(row)
    return out


def merge_channel_status(
    channels: list[dict[str, Any]], status_xml: str | None
) -> list[dict[str, Any]]:
    if not status_xml:
        return channels
    status_by_id: dict[int, dict[str, Any]] = {}
    for block in _split_channel_blocks(status_xml):
        row = _parse_channel_block(block)
        cid = row.get("channel_id")
        if cid is None:
            continue
        try:
            status_by_id[int(cid)] = row
        except ValueError:
            continue
    merged: list[dict[str, Any]] = []
    for ch in channels:
        cid = ch.get("channel_id")
        st = status_by_id.get(cid) if isinstance(cid, int) else None
        row = dict(ch)
        if st:
            for key in (
                "online",
                "enabled",
                "connection_status",
                "ip",
                "port",
                "protocol",
                "username",
                "device_id",
            ):
                if st.get(key) is not None:
                    row[key] = st[key]
        merged.append(row)
    return merged


@dataclass
class NvrChannel:
    channel_id: int
    name: str | None = None
    camera_ip: str | None = None
    camera_port: int | None = None
    protocol: str | None = None
    username: str | None = None
    device_id: str | None = None
    stream_type: str | None = None
    online: bool | None = None
    enabled: bool | None = None
    connection_status: str | None = None
    model: str | None = None
    serial: str | None = None
    firmware: str | None = None
    mac: str | None = None
    vendor: str | None = None
    probe_error: str | None = None
    rtsp_url: str | None = None
    rtsp_direct: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NvrInventory:
    nvr_ip: str
    nvr_port: int
    scheme: str
    nvr_vendor: str = VENDOR_HIKVISION
    nvr_model: str | None = None
    nvr_serial: str | None = None
    nvr_firmware: str | None = None
    nvr_device_name: str | None = None
    nvr_device_type: str | None = None
    channels: list[NvrChannel] = field(default_factory=list)
    error: str | None = None
    auth_username: str | None = None
    scanned_at: datetime = field(default_factory=datetime.now)

    @property
    def url(self) -> str:
        return f"{self.scheme}://{self.nvr_ip}:{self.nvr_port}"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["scanned_at"] = self.scanned_at.isoformat()
        d["channels"] = [c.to_dict() for c in self.channels]
        return d


def _rows_to_channels(rows: list[dict[str, Any]]) -> list[NvrChannel]:
    channels: list[NvrChannel] = []
    for row in rows:
        cid = row["channel_id"]
        cam_ip = row.get("ip")
        channels.append(
            NvrChannel(
                channel_id=cid,
                name=_effective_channel_name(row.get("name"), cid, cam_ip),
                camera_ip=row.get("ip"),
                camera_port=row.get("port"),
                protocol=row.get("protocol"),
                username=row.get("username"),
                device_id=row.get("device_id"),
                stream_type=row.get("stream_type"),
                online=row.get("online"),
                enabled=row.get("enabled"),
                connection_status=row.get("connection_status"),
            )
        )
    return channels


def _parse_dahua_channel_rows(
    remote_rows: dict[int, dict[str, str]],
    title_rows: dict[int, dict[str, str]],
) -> list[dict[str, Any]]:
    indices = sorted(set(remote_rows) | set(title_rows))
    out: list[dict[str, Any]] = []
    for idx in indices:
        remote = remote_rows.get(idx, {})
        title = title_rows.get(idx, {})
        enable_raw = remote.get("Enable") or remote.get("enable")
        enabled: bool | None = None
        if enable_raw is not None:
            enabled = enable_raw.lower() == "true"
        online: bool | None = None
        if enabled is not None:
            online = enabled
        port_raw = remote.get("Port") or remote.get("HttpPort") or remote.get("ManagePort")
        port = int(port_raw) if port_raw and str(port_raw).isdigit() else 37777
        out.append(
            {
                "channel_id": idx + 1,
                "name": title.get("Name") or remote.get("Name") or f"Channel {idx + 1}",
                "ip": remote.get("Address") or remote.get("HostName") or remote.get("IP"),
                "port": port if remote.get("Address") or remote.get("HostName") else None,
                "protocol": remote.get("Protocol") or remote.get("DeviceType"),
                "username": remote.get("UserName") or remote.get("User"),
                "device_id": remote.get("SerialNo") or remote.get("SerialNumber"),
                "online": online,
                "enabled": enabled,
                "connection_status": None,
            }
        )
    return out


async def _fetch_hikvision_channels(
    client: httpx.AsyncClient,
    base_url: str,
    credentials: Sequence[Credential],
    timeout: float,
) -> tuple[list[dict[str, Any]], str | None]:
    errors: list[str] = []
    proxy_rows: list[dict[str, Any]] = []
    video_rows: list[dict[str, Any]] = []

    proxy_res = await fetch_isapi_path(
        client, base_url, INPUT_PROXY_CHANNELS, credentials, timeout
    )
    if proxy_res.status == 200 and proxy_res.body:
        proxy_rows = parse_input_proxy_channels(proxy_res.body)
    elif proxy_res.error:
        errors.append(f"{INPUT_PROXY_CHANNELS}: {proxy_res.error}")
    elif proxy_res.status:
        errors.append(f"{INPUT_PROXY_CHANNELS}: HTTP {proxy_res.status}")

    if not proxy_rows:
        video_res = await fetch_isapi_path(
            client, base_url, VIDEO_INPUT_CHANNELS, credentials, timeout
        )
        if video_res.status == 200 and video_res.body:
            video_rows = parse_input_proxy_channels(video_res.body)
        elif video_res.error:
            errors.append(f"{VIDEO_INPUT_CHANNELS}: {video_res.error}")
        elif video_res.status:
            errors.append(f"{VIDEO_INPUT_CHANNELS}: HTTP {video_res.status}")

    rows = proxy_rows or video_rows
    if not rows:
        return [], "; ".join(errors) if errors else "channel list unavailable (auth?)"

    if proxy_rows:
        status_res = await fetch_isapi_path(
            client, base_url, INPUT_PROXY_STATUS, credentials, timeout
        )
        status_xml = status_res.body if status_res.status == 200 else None
        rows = merge_channel_status(proxy_rows, status_xml)
    return rows, None


async def _fetch_dahua_channels(
    client: httpx.AsyncClient,
    base_url: str,
    credentials: Sequence[Credential],
    timeout: float,
) -> tuple[list[dict[str, Any]], str | None]:
    errors: list[str] = []
    remote_rows: dict[int, dict[str, str]] = {}

    for cfg_name in DAHUA_CHANNEL_CONFIGS:
        path = f"/cgi-bin/configManager.cgi?action=getConfig&name={cfg_name}"
        res = await fetch_dahua_cgi(client, base_url, path, credentials, timeout)
        if res.status == 200 and res.body and "table." in res.body:
            rows = parse_dahua_table_rows(res.body, cfg_name)
            if rows:
                remote_rows = rows
                break
        if res.error:
            errors.append(f"{cfg_name}: {res.error}")
        elif res.status and res.status != 200:
            errors.append(f"{cfg_name}: HTTP {res.status}")

    title_res = await fetch_dahua_cgi(
        client,
        base_url,
        "/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle",
        credentials,
        timeout,
    )
    title_rows = (
        parse_dahua_table_rows(title_res.body, "ChannelTitle")
        if title_res.status == 200 and title_res.body
        else {}
    )

    if not remote_rows and not title_rows:
        return [], "; ".join(errors) if errors else "no channel config (auth or firmware?)"

    if not remote_rows and title_rows:
        remote_rows = {idx: {} for idx in title_rows}

    return _parse_dahua_channel_rows(remote_rows, title_rows), None


async def detect_nvr_vendor(
    client: httpx.AsyncClient,
    ip: str,
    port: int,
    credentials: Sequence[Credential],
    timeout: float,
) -> str | None:
    """Detect whether target is Hikvision or Dahua NVR."""
    scheme = _scheme_for_port(port)
    base_url = f"{scheme}://{ip}:{port}"

    isapi = await fetch_device_info(client, base_url, credentials, timeout)
    server = (isapi.server or "").upper()
    if isapi.status == 200 and isapi.body and "<deviceType>" in isapi.body.lower():
        return VENDOR_HIKVISION
    if "DNVRS" in server or isapi.status in (200, 401, 403):
        if isapi.status != 404:
            return VENDOR_HIKVISION

    for path in (DAHUA_DEVICE_CLASS, DAHUA_DEVICE_TYPE, DAHUA_SYSTEM_INFO):
        res = await fetch_dahua_cgi(client, base_url, path, credentials, timeout)
        if res.status == 200 and res.body:
            dc = parse_dahua_device_class(res.body) or ""
            body_u = res.body.upper()
            if dc.upper() in ("NVR", "DVR", "XVR", "HCVR", "SDVR") or "NVR" in body_u:
                return VENDOR_DAHUA
            parsed = parse_dahua_cgi(res.body)
            model = parsed.get("model") or parsed.get("type") or ""
            if any(k in model.upper() for k in ("NVR", "XVR", "DVR", "HCVR")):
                return VENDOR_DAHUA
    return None


async def _probe_camera(
    client: httpx.AsyncClient,
    channel: NvrChannel,
    credentials: Sequence[Credential],
    timeout: float,
) -> None:
    if not channel.camera_ip:
        channel.probe_error = "no_camera_ip"
        return
    ports: list[int] = []
    if channel.camera_port:
        ports.append(channel.camera_port)
    for p in (80, 8000, 443, 8443, 37777):
        if p not in ports:
            ports.append(p)

    best: Device | None = None
    last_err: str | None = None
    for port in ports:
        try:
            d = await scan_one(client, channel.camera_ip, port, credentials, timeout)
        except Exception as e:
            last_err = str(e)
            continue
        if d.error and d.error != "tcp_closed":
            last_err = d.error
        if d.error == "tcp_closed":
            continue
        if best is None or (d.is_recognized and not best.is_recognized) or (
            d.confidence > best.confidence
        ):
            best = d

    if best is None:
        channel.probe_error = last_err or "tcp_closed"
        return

    channel.model = best.model
    channel.serial = best.serial
    channel.firmware = best.firmware
    channel.mac = best.mac
    channel.vendor = best.vendor
    if best.error:
        channel.probe_error = best.error


def _fill_channel_rtsp(
    inv: NvrInventory,
    credentials: Sequence[Credential],
    preferred: Credential | None = None,
) -> None:
    cred_list = list(credentials)
    for ch in inv.channels:
        ch.rtsp_url = build_nvr_channel_rtsp(
            inv.nvr_vendor,
            inv.nvr_ip,
            ch.channel_id,
            cred_list,
            preferred=preferred,
            channel_username=ch.username,
        )
        if ch.camera_ip:
            vendor = ch.vendor or inv.nvr_vendor
            ch.rtsp_direct = build_camera_direct_rtsp(
                ch.camera_ip,
                vendor,
                cred_list,
                channel_username=ch.username,
            )


async def inventory_nvr(
    ip: str,
    port: int = 80,
    credentials: Sequence[Credential] = (),
    timeout: float = PROBE_TIMEOUT,
    probe_cameras: bool = True,
    camera_concurrency: int = 20,
    vendor: str | None = None,
    only_mounted: bool = True,
    channel_filter: str | None = None,
) -> NvrInventory:
    """List cameras under a Hikvision or Dahua NVR."""
    scheme = _scheme_for_port(port)
    base_url = f"{scheme}://{ip}:{port}"
    inv = NvrInventory(nvr_ip=ip, nvr_port=port, scheme=scheme)

    limits = httpx.Limits(max_connections=50, max_keepalive_connections=20)
    ssl_ctx = _make_ssl_context()
    client = httpx.AsyncClient(
        verify=ssl_ctx,
        follow_redirects=False,
        headers={"User-Agent": USER_AGENT},
        limits=limits,
        trust_env=False,
    )

    try:
        nvr_vendor = vendor or await detect_nvr_vendor(
            client, ip, port, credentials, timeout
        )
        if not nvr_vendor:
            inv.error = "unable to detect NVR vendor (need valid -c credentials)"
            return inv
        inv.nvr_vendor = nvr_vendor
        auth_cred: Credential | None = None

        if nvr_vendor == VENDOR_HIKVISION:
            info = await fetch_device_info(client, base_url, credentials, timeout)
            auth_cred = info.used_credential
            if auth_cred:
                inv.auth_username = auth_cred.username
            if info.status == 200 and info.body:
                parsed = parse_isapi_xml(info.body)
                inv.nvr_model = parsed.get("model")
                inv.nvr_serial = parsed.get("serialNumber")
                inv.nvr_firmware = parsed.get("firmwareVersion")
                inv.nvr_device_name = parsed.get("deviceName")
                inv.nvr_device_type = parsed.get("deviceType")
            rows, err = await _fetch_hikvision_channels(
                client, base_url, credentials, timeout
            )
        else:
            for path in (DAHUA_SYSTEM_INFO, DAHUA_DEVICE_TYPE, DAHUA_DEVICE_CLASS):
                res = await fetch_dahua_cgi(client, base_url, path, credentials, timeout)
                if res.used_credential and not inv.auth_username:
                    inv.auth_username = res.used_credential.username
                    auth_cred = res.used_credential
                if res.status == 200 and res.body:
                    parsed = parse_dahua_cgi(res.body)
                    inv.nvr_model = inv.nvr_model or parsed.get("model") or parsed.get("type")
                    inv.nvr_serial = inv.nvr_serial or parsed.get("serial")
                    inv.nvr_firmware = inv.nvr_firmware or parsed.get("firmware")
                    inv.nvr_device_name = inv.nvr_device_name or parsed.get("device_name")
                    inv.nvr_device_type = (
                        inv.nvr_device_type
                        or parse_dahua_device_class(res.body)
                        or parsed.get("deviceType")
                    )
            rows, err = await _fetch_dahua_channels(
                client, base_url, credentials, timeout
            )

        if err:
            inv.error = err
            if not rows:
                return inv
        filter_mode = channel_filter
        if filter_mode is None:
            filter_mode = 'mounted' if only_mounted else 'all'
        rows = filter_channel_rows(rows, mode=filter_mode)
        inv.channels = _rows_to_channels(rows)

        if probe_cameras and inv.channels:
            sem = asyncio.Semaphore(camera_concurrency)

            async def run(ch: NvrChannel) -> None:
                async with sem:
                    await _probe_camera(client, ch, credentials, timeout)

            await asyncio.gather(*(run(ch) for ch in inv.channels if ch.camera_ip))

        _fill_channel_rtsp(inv, credentials, auth_cred)
    finally:
        await client.aclose()

    return inv


def nvr_vendor_label(vendor: str) -> str:
    from .vendors import vendor_label

    if vendor == VENDOR_HIKVISION:
        return "海康NVR"
    if vendor == VENDOR_DAHUA:
        return "大华NVR"
    return vendor_label(vendor)


def format_channel_row(inv: NvrInventory, ch: NvrChannel) -> str:
    online = (
        "在线"
        if ch.online is True
        else ("离线" if ch.online is False else "?")
    )
    cam = f"{ch.camera_ip}:{ch.camera_port or '-'}" if ch.camera_ip else "-"
    detail = ch.model or ch.serial or ch.probe_error or ""
    rtsp = ch.rtsp_url or ch.rtsp_direct or ""
    return (
        f"  D{ch.channel_id:02d}  {online:<4}  {cam:<22}  "
        f"{(ch.name or ''):<16}  {(detail):<28}\n"
        f"       RTSP: {rtsp}"
    )
