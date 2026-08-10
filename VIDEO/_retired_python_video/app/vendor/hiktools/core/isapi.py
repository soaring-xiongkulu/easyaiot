from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Iterable

import httpx

from .models import Credential

DEVICE_INFO_PATH = "/ISAPI/System/deviceInfo"
_ISAPI_USER_AGENT = "hiktools/0.1"

_LOCK_STATUS_RE = re.compile(
    r"<lockStatus>\s*(\w+)\s*</lockStatus>",
    re.IGNORECASE,
)
_UNLOCK_TIME_RE = re.compile(
    r"<unlockTime>\s*(\d+)\s*</unlockTime>",
    re.IGNORECASE,
)


def describe_isapi_auth_failure(status: int | None, body: str | None) -> str | None:
    """将海康 ISAPI 401 / userCheck 响应转为可读错误（含账号锁定）。"""
    if status != 401:
        return None
    text = body or ""
    lock = _LOCK_STATUS_RE.search(text)
    if lock and lock.group(1).strip().lower() == "lock":
        unlock = _UNLOCK_TIME_RE.search(text)
        sec = int(unlock.group(1)) if unlock else 0
        mins = max(1, (sec + 59) // 60)
        return f"NVR 账号已锁定，请约 {mins} 分钟后重试或在 NVR Web 界面解除锁定"
    if "<userCheck>" in text or "Unauthorized" in text:
        return "NVR 凭证认证失败（401），请检查用户名和密码"
    return f"HTTP {status}"


@dataclass
class IsapiResult:
    status: int | None
    body: str | None
    www_authenticate: str | None
    server: str | None
    used_credential: Credential | None
    error: str | None = None


def _fetch_isapi_path_sync_requests(
    base_url: str,
    path: str,
    credentials: Iterable[Credential],
    timeout: float,
) -> IsapiResult:
    """requests + HTTPDigestAuth 兜底（部分海康固件与 httpx Digest 不兼容）。"""
    import requests
    from requests.auth import HTTPDigestAuth

    url = f"{base_url.rstrip('/')}{path}"
    headers = {"User-Agent": _ISAPI_USER_AGENT}
    cred_list = list(credentials)

    try:
        r = requests.get(url, timeout=timeout, verify=False, headers=headers)
    except requests.RequestException as e:
        return IsapiResult(None, None, None, None, None, error=str(e))

    challenge = r.headers.get("WWW-Authenticate")
    server = r.headers.get("Server")

    if r.status_code == 200:
        return IsapiResult(200, r.text, challenge, server, None)

    if r.status_code != 401:
        err = describe_isapi_auth_failure(r.status_code, r.text)
        return IsapiResult(r.status_code, r.text, challenge, server, None, error=err)

    last = IsapiResult(r.status_code, r.text, challenge, server, None)
    for cred in cred_list:
        try:
            ra = requests.get(
                url,
                auth=HTTPDigestAuth(cred.username, cred.password),
                timeout=timeout,
                verify=False,
                headers=headers,
            )
        except requests.RequestException as e:
            last = IsapiResult(None, None, challenge, server, cred, error=str(e))
            continue
        if ra.status_code == 200:
            return IsapiResult(
                200,
                ra.text,
                ra.headers.get("WWW-Authenticate") or challenge,
                ra.headers.get("Server") or server,
                cred,
            )
        last = IsapiResult(
            ra.status_code,
            ra.text,
            ra.headers.get("WWW-Authenticate") or challenge,
            ra.headers.get("Server") or server,
            cred,
        )
    if last.status == 401:
        last.error = describe_isapi_auth_failure(last.status, last.body)
    return last


async def fetch_isapi_path(
    client: httpx.AsyncClient,
    base_url: str,
    path: str,
    credentials: Iterable[Credential] = (),
    timeout: float = 5.0,
) -> IsapiResult:
    """GET an ISAPI path; tries Digest auth with each credential after 401."""
    url = f"{base_url.rstrip('/')}{path}"

    try:
        r = await client.get(url, timeout=timeout)
    except (httpx.TimeoutException, httpx.TransportError) as e:
        return IsapiResult(None, None, None, None, None, error=str(e))

    challenge = r.headers.get("WWW-Authenticate")
    server = r.headers.get("Server")
    last = IsapiResult(r.status_code, r.text, challenge, server, None)

    if r.status_code != 401:
        if r.status_code == 200:
            return last
        # 非 401 失败也尝试 requests 兜底
        if credentials:
            fb = await asyncio.to_thread(
                _fetch_isapi_path_sync_requests,
                base_url,
                path,
                credentials,
                timeout,
            )
            if fb.status == 200:
                return fb
        return last

    for cred in credentials:
        try:
            ra = await client.get(
                url,
                auth=httpx.DigestAuth(cred.username, cred.password),
                timeout=timeout,
            )
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = IsapiResult(None, None, challenge, server, cred, error=str(e))
            continue

        if ra.status_code == 200:
            return IsapiResult(
                ra.status_code,
                ra.text,
                challenge,
                ra.headers.get("Server") or server,
                cred,
            )
        last = IsapiResult(
            ra.status_code,
            ra.text,
            ra.headers.get("WWW-Authenticate") or challenge,
            ra.headers.get("Server") or server,
            cred,
        )

    # httpx Digest 与海康部分固件不兼容，401 时 requests 兜底
    if credentials:
        fb = await asyncio.to_thread(
            _fetch_isapi_path_sync_requests,
            base_url,
            path,
            credentials,
            timeout,
        )
        if fb.status == 200 or (last.status == 401 and fb.status not in (None, 401)):
            return fb

    if last.status == 401 and not last.error:
        last.error = describe_isapi_auth_failure(last.status, last.body)
    return last


async def fetch_device_info(
    client: httpx.AsyncClient,
    base_url: str,
    credentials: Iterable[Credential] = (),
    timeout: float = 5.0,
) -> IsapiResult:
    """Query /ISAPI/System/deviceInfo."""
    return await fetch_isapi_path(
        client, base_url, DEVICE_INFO_PATH, credentials, timeout
    )
