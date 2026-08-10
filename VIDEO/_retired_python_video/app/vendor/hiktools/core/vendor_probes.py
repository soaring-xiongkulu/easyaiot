from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable
from urllib.parse import urljoin

import httpx

from .models import Credential

DAHUA_MAGICBOX_PATHS = (
    "/cgi-bin/magicBox.cgi?action=getDeviceType",
    "/cgi-bin/magicBox.cgi?action=getSystemInfo",
    "/cgi-bin/magicBox.cgi?action=getSerialNo",
    "/cgi-bin/magicBox.cgi?action=getMachineName",
)

DAHUA_HINT_PATHS = (
    "/RPC2_Login",
    "/",
)

HUAWEI_PATHS = (
    "/cgi-bin/magicBox.cgi?action=getDeviceType",
    "/cgi-bin/configManager.cgi?action=getConfig&name=General",
)

_DAHUA_CGI_HINT = re.compile(
    r"(?:^|\n)(?:type|deviceType|serialNumber|hardwareVersion|machineName|deviceClass)=",
    re.IGNORECASE,
)


@dataclass
class VendorProbeResult:
    dahua_body: str | None = None
    dahua_status: int | None = None
    dahua_www_authenticate: str | None = None
    dahua_used_credential: Credential | None = None
    huawei_body: str | None = None
    huawei_status: int | None = None
    huawei_used_credential: Credential | None = None
    errors: dict[str, str] = field(default_factory=dict)


async def _get_path(
    client: httpx.AsyncClient,
    url: str,
    credentials: Iterable[Credential],
    timeout: float,
) -> tuple[int | None, str | None, str | None, str | None, Credential | None]:
    """Returns status, body, error, www_authenticate, used_credential."""
    try:
        r = await client.get(url, timeout=timeout)
    except (httpx.TimeoutException, httpx.TransportError) as e:
        return None, None, str(e), None, None

    challenge = r.headers.get("WWW-Authenticate")
    if r.status_code == 401:
        for cred in credentials:
            try:
                ra = await client.get(
                    url,
                    auth=httpx.DigestAuth(cred.username, cred.password),
                    timeout=timeout,
                )
            except (httpx.TimeoutException, httpx.TransportError):
                continue
            if ra.status_code == 200:
                return (
                    ra.status_code,
                    ra.text,
                    None,
                    challenge or ra.headers.get("WWW-Authenticate"),
                    cred,
                )
        return r.status_code, r.text, None, challenge, None

    return r.status_code, r.text, None, challenge, None


def _dahua_cgi_hit(status: int | None, body: str | None) -> bool:
    if status is None or not body:
        return False
    if status == 200 and _DAHUA_CGI_HINT.search(body):
        return True
    return status in (401, 403) and bool(body.strip())


async def probe_vendors(
    client: httpx.AsyncClient,
    base_url: str,
    credentials: Iterable[Credential] = (),
    timeout: float = 5.0,
) -> VendorProbeResult:
    """Probe brand-specific HTTP endpoints (Dahua CGI, Huawei config)."""
    result = VendorProbeResult()
    base = base_url.rstrip("/")

    for path in DAHUA_MAGICBOX_PATHS:
        status, body, err, www_auth, used_cred = await _get_path(
            client, base + path, credentials, timeout
        )
        if err:
            result.errors[f"dahua:{path}"] = err
            continue
        if www_auth and not result.dahua_www_authenticate:
            result.dahua_www_authenticate = www_auth
        if used_cred and not result.dahua_used_credential:
            result.dahua_used_credential = used_cred
        if _dahua_cgi_hit(status, body):
            result.dahua_body = body
            result.dahua_status = status
            break
        if status in (200, 401, 403) and not result.dahua_body:
            result.dahua_body = body
            result.dahua_status = status
            if status in (401, 403):
                break

    for path in HUAWEI_PATHS:
        status, body, err, _www, used_cred = await _get_path(
            client, base + path, credentials, timeout
        )
        if err:
            result.errors[f"huawei:{path}"] = err
            continue
        if used_cred and not result.huawei_used_credential:
            result.huawei_used_credential = used_cred
        if status == 200 and body:
            result.huawei_body = body
            result.huawei_status = status
            if "HUAWEI" in body.upper() or "table." in body:
                break

    return result


async def fetch_root_html(
    client: httpx.AsyncClient,
    base_url: str,
    timeout: float,
    max_redirects: int = 3,
) -> tuple[int | None, str | None, str | None, str | None]:
    """GET / with limited redirects; returns status, body, server, error."""
    url = base_url.rstrip("/") + "/"
    server: str | None = None
    try:
        for _ in range(max_redirects + 1):
            r = await client.get(url, timeout=timeout)
            server = server or r.headers.get("Server")
            if r.status_code in (301, 302, 303, 307, 308):
                loc = r.headers.get("Location")
                if not loc:
                    break
                url = urljoin(url, loc)
                continue
            return r.status_code, r.text, server, None
        return r.status_code, r.text, server, None
    except (httpx.TimeoutException, httpx.TransportError) as e:
        return None, None, server, str(e)
