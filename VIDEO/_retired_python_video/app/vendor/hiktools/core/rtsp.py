from __future__ import annotations

from urllib.parse import quote

from .device_role import ROLE_NVR_DAHUA, ROLE_NVR_HIK, is_nvr_role
from .models import Credential, Device
from .vendors import (
    VENDOR_DAHUA,
    VENDOR_EZVIZ,
    VENDOR_HIKVISION,
    VENDOR_HUAWEI,
    VENDOR_LANPARTIX,
    VENDOR_JOVISION,
    VENDOR_TIANDY,
    VENDOR_TP_LINK,
    VENDOR_TVT,
    VENDOR_UNIVIEW,
    normalize_vendor,
)

RTSP_PORT = 554
JOVISION_RTSP_PORT = 8554


def _quote_userinfo(value: str) -> str:
    return quote(value, safe="")


def _auth_prefix(username: str | None, password: str | None) -> str:
    if not username:
        return ""
    user = _quote_userinfo(username)
    pw = _quote_userinfo(password or "")
    return f"{user}:{pw}@"


def _pick_credential(
    credentials: list[Credential] | tuple[Credential, ...],
    preferred: Credential | None = None,
    username: str | None = None,
) -> Credential | None:
    if preferred:
        return preferred
    if username:
        for c in credentials:
            if c.username == username:
                return c
    if credentials:
        return credentials[0]
    return None


def build_hikvision_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    """Hikvision RTSP: channel 1 main stream -> /Streaming/Channels/101."""
    stream_id = channel * 100 + (1 + subtype)
    auth = _auth_prefix(username, password)
    return f"rtsp://{auth}{host}:{port}/Streaming/Channels/{stream_id}"


def build_dahua_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    """Dahua RTSP: /cam/realmonitor?channel=1&subtype=0 (0=主码流)."""
    auth = _auth_prefix(username, password)
    return (
        f"rtsp://{auth}{host}:{port}/cam/realmonitor"
        f"?channel={channel}&subtype={subtype}"
    )


def build_huawei_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    auth = _auth_prefix(username, password)
    return (
        f"rtsp://{auth}{host}:{port}/rtsp/streaming"
        f"?channel={channel}&subtype={subtype}"
    )


def build_tiandy_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    stream = 1 if subtype == 0 else 2
    auth = _auth_prefix(username, password)
    return f"rtsp://{auth}{host}:{port}/{channel}/{stream}"


def build_uniview_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    stream = 1 if subtype == 0 else 2
    auth = _auth_prefix(username, password)
    return f"rtsp://{auth}{host}:{port}/media/video{stream}"


def build_tp_link_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    stream = 1 if subtype == 0 else 2
    auth = _auth_prefix(username, password)
    if channel > 1:
        return f"rtsp://{auth}{host}:{port}/stream{stream}&channel={channel}"
    return f"rtsp://{auth}{host}:{port}/stream{stream}"


def build_lanpartix_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = JOVISION_RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    profile = 0 if subtype == 0 else 1
    auth = _auth_prefix(username, password)
    return f"rtsp://{auth}{host}:{port}/profile{profile}"


def build_tvt_rtsp(
    host: str,
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int = RTSP_PORT,
    username: str | None = None,
    password: str | None = None,
) -> str:
    path = "mpeg4" if subtype == 0 else "mpeg4cif"
    auth = _auth_prefix(username, password)
    return f"rtsp://{auth}{host}:{port}/{path}"


def build_device_rtsp_url(
    device: Device,
    credentials: list[Credential] | tuple[Credential, ...] = (),
    *,
    preferred: Credential | None = None,
    channel: int = 1,
    subtype: int = 0,
) -> str | None:
    """Build RTSP URL for a scanned device (IPC or NVR preview on channel 1)."""
    if not device.is_recognized or not device.vendor:
        return None

    cred = _pick_credential(list(credentials), preferred)
    user = cred.username if cred else None
    pw = cred.password if cred else None
    host = device.ip

    if is_nvr_role(device.device_role):
        if device.device_role == ROLE_NVR_HIK or device.vendor == VENDOR_HIKVISION:
            return build_hikvision_rtsp(
                host, channel=channel, subtype=subtype, username=user, password=pw
            )
        if device.device_role == ROLE_NVR_DAHUA or device.vendor == VENDOR_DAHUA:
            return build_dahua_rtsp(
                host, channel=channel, subtype=subtype, username=user, password=pw
            )

    if device.vendor in (VENDOR_HIKVISION, VENDOR_EZVIZ):
        return build_hikvision_rtsp(
            host, channel=1, subtype=subtype, username=user, password=pw
        )
    if device.vendor == VENDOR_DAHUA:
        return build_dahua_rtsp(
            host, channel=1, subtype=subtype, username=user, password=pw
        )
    return None


def build_nvr_channel_rtsp(
    nvr_vendor: str,
    nvr_host: str,
    channel_id: int,
    credentials: list[Credential] | tuple[Credential, ...] = (),
    *,
    preferred: Credential | None = None,
    channel_username: str | None = None,
    subtype: int = 0,
    port: int = RTSP_PORT,
) -> str | None:
    """RTSP via NVR (use NVR IP + channel number)."""
    cred = _pick_credential(
        list(credentials), preferred, username=channel_username
    )
    user = cred.username if cred else None
    pw = cred.password if cred else None
    vendor_key = normalize_vendor(nvr_vendor) or nvr_vendor

    if vendor_key in (VENDOR_HIKVISION, VENDOR_EZVIZ):
        return build_hikvision_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port,
            username=user,
            password=pw,
        )
    if vendor_key == VENDOR_DAHUA:
        return build_dahua_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port,
            username=user,
            password=pw,
        )
    if vendor_key == VENDOR_HUAWEI:
        return build_huawei_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port,
            username=user,
            password=pw,
        )
    if vendor_key == VENDOR_TIANDY:
        return build_tiandy_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port,
            username=user,
            password=pw,
        )
    if vendor_key == VENDOR_UNIVIEW:
        return build_uniview_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port,
            username=user,
            password=pw,
        )
    if vendor_key == VENDOR_TP_LINK:
        return build_tp_link_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port,
            username=user,
            password=pw,
        )
    if vendor_key in (VENDOR_LANPARTIX, VENDOR_JOVISION):
        return build_lanpartix_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port or JOVISION_RTSP_PORT,
            username=user,
            password=pw,
        )
    if vendor_key == VENDOR_TVT:
        return build_tvt_rtsp(
            nvr_host,
            channel=channel_id,
            subtype=subtype,
            port=port,
            username=user,
            password=pw,
        )
    return None


def build_camera_direct_rtsp(
    camera_ip: str,
    vendor: str | None,
    credentials: list[Credential] | tuple[Credential, ...] = (),
    *,
    channel_username: str | None = None,
    subtype: int = 0,
    port: int = RTSP_PORT,
) -> str | None:
    """RTSP directly to camera IP (when reachable)."""
    cred = _pick_credential(list(credentials), username=channel_username)
    user = cred.username if cred else None
    pw = cred.password if cred else None

    if vendor in (VENDOR_HIKVISION, VENDOR_EZVIZ):
        return build_hikvision_rtsp(
            camera_ip, channel=1, subtype=subtype, port=port, username=user, password=pw
        )
    if vendor == VENDOR_DAHUA:
        return build_dahua_rtsp(
            camera_ip, channel=1, subtype=subtype, port=port, username=user, password=pw
        )
    return None


def get_rtsp_candidate_urls(
    vendor: str | None,
    host: str,
    credentials: list[Credential] | tuple[Credential, ...] = (),
    *,
    channel: int = 1,
    subtype: int = 0,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
) -> list[str]:
    """返回某通道的 RTSP 候选 URL 列表（用于 DESCRIBE 探测）。"""
    vendor_key = normalize_vendor(vendor)
    rtsp_port = port or (JOVISION_RTSP_PORT if vendor_key in (VENDOR_LANPARTIX, VENDOR_JOVISION) else RTSP_PORT)
    cred = _pick_credential(list(credentials), username=username)
    user = username or (cred.username if cred else None)
    pw = password if password is not None else (cred.password if cred else None)

    url = build_nvr_channel_rtsp(
        vendor_key or vendor or '',
        host,
        channel,
        credentials,
        preferred=cred,
        channel_username=user,
        subtype=subtype,
        port=rtsp_port,
    )
    if url:
        return [url]

    if user is not None or pw:
        cred_part = _auth_prefix(user or '', pw or '')
        return [f"rtsp://{cred_part}{host}:{rtsp_port}/"]
    return [f"rtsp://{host}:{rtsp_port}/"]
