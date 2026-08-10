"""Pure-Python Hikvision SADP discovery (LAN only).

SADP uses UDP multicast 239.255.255.250:37020 with XML payloads. This module
implements a minimal listener + inquiry sender. It only works in the local
broadcast domain — routers do not forward multicast by default.

Reference protocol: https://sergei.nz/reverse-engineering-hikvision-sadp-tool/
"""

from __future__ import annotations

import asyncio
import re
import socket
import struct
import uuid
from collections.abc import AsyncIterator

from .models import Device

SADP_MCAST_ADDR = "239.255.255.250"
SADP_PORT = 37020


def _build_inquiry_xml() -> str:
    uid = str(uuid.uuid4()).upper()
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Probe>\n'
        f'<Uuid>{uid}</Uuid>\n'
        '<Types>inquiry</Types>\n'
        '</Probe>'
    )


def _parse_announce(xml_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    fields = (
        "DeviceType",
        "DeviceDescription",
        "DeviceSN",
        "CommandPort",
        "HttpPort",
        "MAC",
        "IPv4Address",
        "IPv4SubnetMask",
        "IPv4Gateway",
        "SoftwareVersion",
        "DSPVersion",
        "BootTime",
        "Activated",
        "PasswordResetAbility",
        "SupportHCPlatform",
    )
    for f in fields:
        m = re.search(rf"<{f}>\s*([^<]+?)\s*</{f}>", xml_text)
        if m:
            out[f] = m.group(1).strip()
    return out


def _build_socket() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except (AttributeError, OSError):
        pass
    s.bind(("", SADP_PORT))
    mreq = struct.pack("=4sl", socket.inet_aton(SADP_MCAST_ADDR), socket.INADDR_ANY)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.setblocking(False)
    return s


async def discover(duration: float = 6.0) -> AsyncIterator[Device]:
    """Listen for SADP announces and send an inquiry. Yields Device records."""
    loop = asyncio.get_running_loop()
    sock = _build_socket()
    seen: set[str] = set()

    inquiry = _build_inquiry_xml().encode("utf-8")
    try:
        sock.sendto(inquiry, (SADP_MCAST_ADDR, SADP_PORT))
    except OSError:
        pass

    deadline = loop.time() + duration
    try:
        while loop.time() < deadline:
            timeout = max(0.0, deadline - loop.time())
            try:
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(sock, 8192), timeout=timeout
                )
            except (asyncio.TimeoutError, ConnectionError):
                continue

            try:
                text = data.decode("utf-8", errors="replace")
            except Exception:
                continue
            if "<DeviceType>" not in text and "<DeviceSN>" not in text:
                continue
            parsed = _parse_announce(text)
            sn = parsed.get("DeviceSN") or addr[0]
            if sn in seen:
                continue
            seen.add(sn)

            ip = parsed.get("IPv4Address") or addr[0]
            http_port_raw = parsed.get("HttpPort") or "80"
            try:
                http_port = int(http_port_raw)
            except ValueError:
                http_port = 80

            device = Device(
                ip=ip,
                port=http_port,
                scheme="http",
                is_hikvision=True,
                confidence=95,
                model=parsed.get("DeviceType"),
                serial=parsed.get("DeviceSN"),
                firmware=parsed.get("SoftwareVersion"),
                device_name=parsed.get("DeviceDescription"),
                device_type=parsed.get("DeviceType"),
                mac=parsed.get("MAC"),
                source="sadp",
                evidence={"sadp": parsed},
            )
            yield device
    finally:
        try:
            sock.close()
        except OSError:
            pass
