from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import httpx

from .fingerprint import parse_dahua_cgi
from .models import Credential

_TABLE_ROW_RE = re.compile(
    r"table\.(\w+)\[(\d+)\]\.([^=]+)=(.*)",
    re.IGNORECASE,
)


@dataclass
class DahuaCgiResult:
    status: int | None
    body: str | None
    www_authenticate: str | None = None
    used_credential: Credential | None = None
    error: str | None = None


async def fetch_dahua_cgi(
    client: httpx.AsyncClient,
    base_url: str,
    path: str,
    credentials: Iterable[Credential] = (),
    timeout: float = 5.0,
) -> DahuaCgiResult:
    """GET a Dahua CGI path with optional Digest auth."""
    url = f"{base_url.rstrip('/')}{path}"
    try:
        r = await client.get(url, timeout=timeout)
    except (httpx.TimeoutException, httpx.TransportError) as e:
        return DahuaCgiResult(None, None, None, None, str(e))

    challenge = r.headers.get("WWW-Authenticate")
    last = DahuaCgiResult(r.status_code, r.text, challenge, None)

    if r.status_code != 401:
        return last

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
            return DahuaCgiResult(
                ra.status_code,
                ra.text,
                challenge,
                cred,
            )
        last = DahuaCgiResult(
            ra.status_code,
            ra.text,
            ra.headers.get("WWW-Authenticate") or challenge,
            cred,
        )
    return last


def parse_dahua_table_rows(
    text: str, table_name: str | None = None
) -> dict[int, dict[str, str]]:
    """Parse table.Section[index].Field=value lines into {index: {field: value}}."""
    rows: dict[int, dict[str, str]] = {}
    for line in text.splitlines():
        line = line.strip()
        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        tname, idx_s, field, val = m.groups()
        if table_name and tname.lower() != table_name.lower():
            continue
        try:
            idx = int(idx_s)
        except ValueError:
            continue
        rows.setdefault(idx, {})[field] = val.strip().strip('"')
    return rows


def parse_dahua_device_class(body: str | None) -> str | None:
    if not body:
        return None
    parsed = parse_dahua_cgi(body)
    return parsed.get("class") or parsed.get("device_class") or parsed.get("type")
