from __future__ import annotations

import asyncio
import hashlib
import re
import socket
from typing import Any
from urllib.parse import quote

from .rtsp import RTSP_PORT, JOVISION_RTSP_PORT, get_rtsp_candidate_urls
from .vendors import (
    VENDOR_UNIVIEW,
    VENDOR_TIANDY,
    VENDOR_TPLINK,
    VENDOR_JOOAN,
    VENDOR_JOVISION,
    normalize_vendor,
)


_RTSP_PORT_MAP: dict[str, int] = {
    VENDOR_JOVISION: JOVISION_RTSP_PORT,
}


def default_rtsp_port_for(vendor: str | None) -> int:
    """返回指定品牌的默认 RTSP 端口（中维世纪 8554，其他 554）。"""
    vendor = normalize_vendor(vendor)
    if not vendor:
        return RTSP_PORT
    return _RTSP_PORT_MAP.get(vendor, RTSP_PORT)


def _quote_userinfo(value: str) -> str:
    return quote(value, safe="")


def _build_auth_header(
    www_authenticate: str | None,
    method: str,
    uri: str,
    username: str | None,
    password: str | None,
) -> str | None:
    if not username:
        return None
    if not www_authenticate:
        pw = password or ""
        import base64
        token = base64.b64encode(f"{username}:{pw}".encode()).decode()
        return f"Basic {token}"

    digest_match = re.search(
        r'Digest\s+.*?realm="([^"]*)".*?nonce="([^"]*)"',
        www_authenticate,
        re.IGNORECASE,
    )
    if digest_match:
        realm = digest_match.group(1)
        nonce = digest_match.group(2)
        pw = password or ""
        ha1 = hashlib.md5(f"{username}:{realm}:{pw}".encode()).hexdigest()
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
        response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()
        return (
            f'Digest username="{username}", realm="{realm}", nonce="{nonce}", '
            f'uri="{uri}", response="{response}"'
        )

    pw = password or ""
    import base64
    token = base64.b64encode(f"{username}:{pw}".encode()).decode()
    return f"Basic {token}"


def _strip_auth_from_url(url: str) -> tuple[str, str | None, str | None]:
    m = re.match(r"rtsp://([^:@]+):([^@]*)@(.+)", url)
    if m:
        return f"rtsp://{m.group(3)}", m.group(1), m.group(2)
    return url, None, None


async def _rtsp_describe(
    rtsp_url: str,
    username: str | None = None,
    password: str | None = None,
    timeout: float = 3.0,
) -> tuple[int, str | None, str | None]:
    """发送 RTSP DESCRIBE 请求，返回 (status, sdp, www_authenticate)。"""
    base_url, url_user, url_pass = _strip_auth_from_url(rtsp_url)
    user = username or url_user
    pw = password or url_pass if password is None else password

    parsed = re.match(r"rtsp://([^:/]+)(?::(\d+))?(/.*)?", base_url)
    if not parsed:
        return -1, None, None
    host = parsed.group(1)
    port = int(parsed.group(2) or 554)
    path = parsed.group(3) or "/"

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except (asyncio.TimeoutError, OSError, socket.error):
        return -1, None, None

    cseq = 1

    async def _send_describe(uri: str, auth: str | None) -> tuple[int, str]:
        nonlocal cseq
        req = f"DESCRIBE {uri} RTSP/1.0\r\n"
        req += f"CSeq: {cseq}\r\n"
        req += "Accept: application/sdp\r\n"
        if auth:
            req += f"Authorization: {auth}\r\n"
        req += "User-Agent: EasyAIoT-RTSP-Probe/1.0\r\n"
        req += "\r\n"
        cseq += 1
        try:
            writer.write(req.encode())
            await asyncio.wait_for(writer.drain(), timeout=timeout)
            data = await asyncio.wait_for(reader.read(4096), timeout=timeout)
            return 0, data.decode("utf-8", errors="replace")
        except (asyncio.TimeoutError, OSError, socket.error):
            return -1, ""

    try:
        status_code = 0
        www_auth: str | None = None

        ret, resp = await _send_describe(base_url, None)
        if ret != 0:
            writer.close()
            await writer.wait_closed()
            return -1, None, None

        first_line = resp.split("\r\n", 1)[0] if resp else ""
        m = re.match(r"RTSP/\d+\.\d+\s+(\d+)\s+", first_line)
        if m:
            status_code = int(m.group(1))

        if status_code == 401:
            auth_match = re.search(r'WWW-Authenticate:\s*(.+?)\r\n', resp, re.IGNORECASE)
            if auth_match:
                www_auth = auth_match.group(1).strip()

        if status_code == 401 and www_auth and user:
            auth_header = _build_auth_header(www_auth, "DESCRIBE", base_url, user, pw)
            if auth_header:
                ret, resp = await _send_describe(base_url, auth_header)
                if ret == 0:
                    first_line = resp.split("\r\n", 1)[0] if resp else ""
                    m = re.match(r"RTSP/\d+\.\d+\s+(\d+)\s+", first_line)
                    if m:
                        status_code = int(m.group(1))

        sdp = None
        if status_code == 200 and "\r\n\r\n" in resp:
            sdp = resp.split("\r\n\r\n", 1)[1]

        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return status_code, sdp, www_auth

    except Exception:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        return -1, None, None


async def enumerate_rtsp_channels(
    vendor: str | None,
    ip: str,
    *,
    port: int | None = None,
    username: str | None = None,
    password: str | None = None,
    max_channels: int = 32,
    timeout: float = 3.0,
    concurrency: int = 8,
) -> tuple[list[dict[str, Any]], str | None]:
    """逐通道 RTSP DESCRIBE 探测，返回 [{channel_id, name, ip}, ...] 列表。

    对每个候选通道号（1..max_channels），用对应品牌的 RTSP URL 模板生成
    主码流 URL，发送 DESCRIBE，能返回 200 即视为通道存在。
    """
    vendor = normalize_vendor(vendor)
    if port is None:
        port = default_rtsp_port_for(vendor)

    from .models import Credential
    creds = [Credential(username or "", password or "")] if username else []

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    sem = asyncio.Semaphore(concurrency)

    async def _probe(ch: int) -> None:
        async with sem:
            urls = get_rtsp_candidate_urls(
                vendor, ip, creds, channel=ch, subtype=0, port=port,
                username=username, password=password,
            )
            for url in urls:
                status, sdp, _ = await _rtsp_describe(
                    url, username=username, password=password, timeout=timeout
                )
                if status == 200:
                    name = None
                    if sdp:
                        m = re.search(r"^s=(.+)$", sdp, re.MULTILINE)
                        if m:
                            name = m.group(1).strip()
                    rows.append({
                        "channel_id": ch,
                        "name": name or f"CH{ch}",
                        "ip": None,
                    })
                    return
                if status > 0 and status not in (404, 401):
                    errors.append(f"ch{ch}: RTSP {status}")

    tasks = [_probe(ch) for ch in range(1, max_channels + 1)]
    await asyncio.gather(*tasks)

    rows.sort(key=lambda r: r["channel_id"])
    err = "; ".join(errors[:3]) if errors and not rows else None
    return rows, err
