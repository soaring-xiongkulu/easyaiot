from __future__ import annotations

import asyncio
import logging
import logging.handlers
import ssl
from collections.abc import AsyncIterator, Callable, Iterable, Sequence
from pathlib import Path

import httpx

from .fingerprint import (
    evaluate,
    parse_dahua_cgi,
    parse_huawei_cgi,
    parse_isapi_xml,
)
from .isapi import IsapiResult, fetch_device_info
from .models import Credential, Device
from .dahua_cgi import fetch_dahua_cgi, parse_dahua_device_class
from .device_role import infer_device_role
from .rtsp import build_device_rtsp_url
from .vendor_probes import VendorProbeResult, fetch_root_html, probe_vendors
from .vendors import VENDOR_DAHUA, VENDOR_EZVIZ, VENDOR_HIKVISION, VENDOR_HUAWEI

logger = logging.getLogger("hiktools.scanner")

_audit_logger_inited = False


def _ensure_audit_log() -> logging.Logger:
    global _audit_logger_inited
    audit = logging.getLogger("hiktools.audit")
    if _audit_logger_inited:
        return audit
    log_dir = Path.home() / ".hiktools"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        log_dir / "scan.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    audit.addHandler(handler)
    audit.setLevel(logging.INFO)
    audit.propagate = False
    _audit_logger_inited = True
    return audit

HTTPS_PORTS = {443, 8443}
PROBE_TIMEOUT = 5.0
USER_AGENT = "hiktools/0.1"


def _scheme_for_port(port: int) -> str:
    return "https" if port in HTTPS_PORTS else "http"


async def _tcp_open(ip: str, port: int, timeout: float) -> bool:
    try:
        fut = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except (ConnectionResetError, OSError):
            pass
        return True
    except (asyncio.TimeoutError, OSError):
        return False


def _make_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
    except ssl.SSLError:
        pass
    return ctx


async def _scan_one_probes(
    client: httpx.AsyncClient,
    ip: str,
    port: int,
    credentials: Sequence[Credential],
    timeout: float,
    device: Device,
) -> Device:
    scheme = _scheme_for_port(port)
    base_url = f"{scheme}://{ip}:{port}"
    device.scheme = scheme

    if not await _tcp_open(ip, port, timeout):
        device.error = "tcp_closed"
        return device

    server_header: str | None = None
    html_body: str | None = None
    root_status, html_body, server_header, root_err = await fetch_root_html(
        client, base_url, timeout
    )
    if root_status is not None:
        device.evidence["root_status"] = root_status
    if root_err:
        device.evidence["root_error"] = root_err

    isapi = await fetch_device_info(client, base_url, credentials, timeout)
    server_header = server_header or isapi.server
    device.evidence["isapi_status"] = isapi.status
    if isapi.www_authenticate:
        device.evidence["isapi_www_authenticate"] = isapi.www_authenticate
    if isapi.error:
        device.evidence["isapi_error"] = isapi.error

    vendor_probe = await probe_vendors(client, base_url, credentials, timeout)
    if vendor_probe.dahua_status is not None:
        device.evidence["dahua_cgi_status"] = vendor_probe.dahua_status
    if vendor_probe.huawei_status is not None:
        device.evidence["huawei_cgi_status"] = vendor_probe.huawei_status
    if vendor_probe.errors:
        device.evidence["vendor_probe_errors"] = vendor_probe.errors

    xml_body = isapi.body if isapi.status == 200 else None
    ev = evaluate(
        server_header=server_header,
        www_authenticate=isapi.www_authenticate,
        isapi_xml=xml_body,
        html_body=html_body,
        isapi_status=isapi.status,
        dahua_cgi=vendor_probe.dahua_body,
        dahua_magicbox_status=vendor_probe.dahua_status,
        dahua_www_authenticate=vendor_probe.dahua_www_authenticate,
        huawei_cgi=vendor_probe.huawei_body,
    )
    device.confidence = ev.score
    device.vendor = ev.vendor
    device.is_hikvision = ev.vendor == VENDOR_HIKVISION
    device.evidence["fingerprint_hits"] = ev.hits

    if credentials and ev.vendor == VENDOR_DAHUA:
        dc_res = await fetch_dahua_cgi(
            client,
            base_url,
            "/cgi-bin/magicBox.cgi?action=getDeviceClass",
            credentials,
            timeout,
        )
        if dc_res.status == 200 and dc_res.body:
            device.evidence["dahua_device_class"] = parse_dahua_device_class(
                dc_res.body
            )
            if dc_res.used_credential:
                device.evidence["authenticated_as"] = dc_res.used_credential.username

    _apply_vendor_device_info(device, ev.vendor, xml_body, isapi, vendor_probe)
    device.device_role = infer_device_role(device)
    preferred_cred = (
        isapi.used_credential
        or vendor_probe.dahua_used_credential
        or vendor_probe.huawei_used_credential
    )
    device.rtsp_url = build_device_rtsp_url(
        device,
        credentials,
        preferred=preferred_cred,
    )

    return device


def scan_one_budget(timeout: float) -> float:
    """单 (ip, port) 探测总时长上限，避免串行 HTTP 探测累积过久。"""
    t = max(0.5, float(timeout))
    return min(20.0, max(6.0, t * 4.0))


async def scan_one(
    client: httpx.AsyncClient,
    ip: str,
    port: int,
    credentials: Sequence[Credential],
    timeout: float,
) -> Device:
    scheme = _scheme_for_port(port)
    device = Device(ip=ip, port=port, scheme=scheme, source="http")
    budget = scan_one_budget(timeout)
    try:
        return await asyncio.wait_for(
            _scan_one_probes(client, ip, port, credentials, timeout, device),
            timeout=budget,
        )
    except asyncio.TimeoutError:
        device.error = "probe_timeout"
        return device


_ISAPI_VENDORS = frozenset({VENDOR_HIKVISION, VENDOR_EZVIZ})


def _apply_vendor_device_info(
    device: Device,
    vendor: str | None,
    xml_body: str | None,
    isapi: IsapiResult,
    vendor_probe: VendorProbeResult,
) -> None:
    if xml_body and vendor in _ISAPI_VENDORS:
        parsed = parse_isapi_xml(xml_body)
        device.model = parsed.get("model")
        device.serial = parsed.get("serialNumber")
        device.firmware = parsed.get("firmwareVersion")
        device.device_name = parsed.get("deviceName")
        device.device_type = parsed.get("deviceType")
        device.mac = parsed.get("macAddress")
        device.source = "isapi"
        if isapi.used_credential:
            device.evidence["authenticated_as"] = isapi.used_credential.username
    elif vendor_probe.dahua_body and vendor == VENDOR_DAHUA:
        parsed = parse_dahua_cgi(vendor_probe.dahua_body)
        device.model = parsed.get("model") or device.model
        device.serial = parsed.get("serial") or device.serial
        device.firmware = parsed.get("firmware") or device.firmware
        device.device_name = parsed.get("device_name") or device.device_name
        device.mac = parsed.get("mac") or device.mac
        device.source = "dahua_cgi"
        dahua_cred = vendor_probe.dahua_used_credential or isapi.used_credential
        if dahua_cred:
            device.evidence["authenticated_as"] = dahua_cred.username
    elif vendor_probe.huawei_body and vendor == VENDOR_HUAWEI:
        parsed = parse_huawei_cgi(vendor_probe.huawei_body)
        device.model = parsed.get("model") or device.model
        device.serial = parsed.get("serial") or device.serial
        device.firmware = parsed.get("firmware") or device.firmware
        device.device_name = parsed.get("device_name") or device.device_name
        device.device_type = parsed.get("device_type") or device.device_type
        device.mac = parsed.get("mac") or device.mac
        device.source = "huawei_cgi"
        if vendor_probe.huawei_used_credential:
            device.evidence["authenticated_as"] = vendor_probe.huawei_used_credential.username


ProgressCb = Callable[[int, int, Device], None]


async def scan(
    targets: Iterable[tuple[str, int]],
    credentials: Sequence[Credential] = (),
    concurrency: int = 200,
    timeout: float = PROBE_TIMEOUT,
    only_hits: bool = False,
    progress: ProgressCb | None = None,
) -> AsyncIterator[Device]:
    targets = list(targets)
    total = len(targets)
    if total == 0:
        return

    audit = _ensure_audit_log()
    audit.info(
        "scan_started targets=%d concurrency=%d timeout=%.1f sample=%s",
        total,
        concurrency,
        timeout,
        ",".join(f"{ip}:{p}" for ip, p in targets[:5]),
    )

    sem = asyncio.Semaphore(concurrency)
    queue: asyncio.Queue[Device | None] = asyncio.Queue()

    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=50)
    ssl_ctx = _make_ssl_context()
    client = httpx.AsyncClient(
        verify=ssl_ctx,
        follow_redirects=False,
        headers={"User-Agent": USER_AGENT},
        limits=limits,
        trust_env=False,
    )

    async def worker(ip: str, port: int) -> None:
        async with sem:
            try:
                d = await scan_one(client, ip, port, credentials, timeout)
            except Exception as e:
                d = Device(ip=ip, port=port, scheme=_scheme_for_port(port), error=f"{type(e).__name__}: {e}")
                logger.exception("scan_one crashed for %s:%s", ip, port)
            await queue.put(d)

    async def runner() -> None:
        tasks = [asyncio.create_task(worker(ip, port)) for ip, port in targets]
        try:
            await asyncio.gather(*tasks)
        finally:
            await queue.put(None)

    runner_task = asyncio.create_task(runner())

    try:
        done = 0
        while True:
            item = await queue.get()
            if item is None:
                break
            done += 1
            if progress:
                try:
                    progress(done, total, item)
                except Exception:
                    logger.exception("progress callback failed")
            if only_hits and not item.is_recognized:
                continue
            yield item
    finally:
        runner_task.cancel()
        try:
            await runner_task
        except (asyncio.CancelledError, Exception):
            pass
        await client.aclose()
