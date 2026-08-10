from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .vendors import (
    ALL_VENDORS,
    VENDOR_DAHUA,
    VENDOR_EZVIZ,
    VENDOR_HIKVISION,
    VENDOR_HUAWEI,
    VENDOR_XIAOMI,
)

CONFIDENCE_THRESHOLD = 60

# --- Hikvision ---
_SERVER_HIK_RE = re.compile(r"app-webs|hikvision|dnvrs-webs", re.IGNORECASE)
_REALM_HIK_RE = re.compile(r"ip\s*camera|ipc|nvr|dvr|hik|streaming", re.IGNORECASE)
_TITLE_HIK_RE = re.compile(r"hikvision|网络摄像机", re.IGNORECASE)
_TITLE_HIK_WEB_SERVICE = re.compile(r"^web\s*service$", re.IGNORECASE)
_HIK_PATH_RE = re.compile(r"/doc/page/login\.asp|/ISAPI/|/SDK/", re.IGNORECASE)

# --- Dahua ---
_SERVER_DAHUA_RE = re.compile(
    r"dahua|dh-webs|gen\d+-webs|(?:^|\s)webs(?:/|\s|$)",
    re.IGNORECASE,
)
_TITLE_DAHUA_RE = re.compile(r"dahua|大华", re.IGNORECASE)
_TITLE_WEB_SERVICE = re.compile(r"^web\s*service$", re.IGNORECASE)
_DAHUA_PATH_RE = re.compile(
    r"/RPC2|RPC2_Login|magicBox\.cgi|configManager\.cgi|"
    r"/cgi-bin/snapshot\.cgi|/cgi-bin/mjpg/",
    re.IGNORECASE,
)
_DAHUA_BODY_RE = re.compile(
    r"dahua|大华|dahua\s*technology|global\.login|"
    r"RPC2_Login|Dahua3\.0|clientType[\"']?\s*:\s*[\"']?Dahua|"
    r"g_szUrl\s*=\s*[\"']/RPC2",
    re.IGNORECASE,
)
_DAHUA_CGI_RE = re.compile(
    r"(?:^|\n)(?:type|deviceType|serialNumber|hardwareVersion|machineName|deviceClass)=",
    re.IGNORECASE,
)
_REALM_DAHUA_LOGIN_RE = re.compile(
    r"login\s+to|dahua|device_cgi",
    re.IGNORECASE,
)
_DAHUA_WEBUI_RE = re.compile(
    r"@WebVersion@|jsBase/lib/m\.js|jsBase/common/extend\.js|"
    r"jsBase/lib/more\.js\?version=",
    re.IGNORECASE,
)

# --- Huawei ---
_SERVER_HUAWEI_RE = re.compile(r"huawei|hw-webs|eudemon", re.IGNORECASE)
_TITLE_HUAWEI_RE = re.compile(r"huawei|华为", re.IGNORECASE)
_HUAWEI_PATH_RE = re.compile(r"/cgi-bin/|/doc/page/|/Portal/", re.IGNORECASE)
_HUAWEI_CGI_RE = re.compile(r"manufacturer\s*=\s*HUAWEI|vendor\s*=\s*HUAWEI", re.IGNORECASE)

# --- Ezviz (萤石，海康消费品牌) ---
_EZVIZ_RE = re.compile(r"ezviz|萤石|ys7|open\.ys7", re.IGNORECASE)
_EZVIZ_PATH_RE = re.compile(r"/api/|/ezviz/|ezopen", re.IGNORECASE)

# --- Xiaomi ---
_XIAOMI_RE = re.compile(r"xiaomi|小米|mijia|米家|mi\s*home|chuangmi", re.IGNORECASE)
_XIAOMI_PATH_RE = re.compile(r"/miot/|/app/start\.html|/cgi-bin/status", re.IGNORECASE)


@dataclass
class FingerprintEvidence:
    score: int
    hits: dict[str, Any]
    vendor: str | None = None

    @property
    def is_hikvision(self) -> bool:
        return self.vendor == VENDOR_HIKVISION and self.score >= CONFIDENCE_THRESHOLD

    @property
    def is_recognized(self) -> bool:
        return self.vendor is not None and self.score >= CONFIDENCE_THRESHOLD


def score_server_header(server: str | None) -> tuple[int, str | None]:
    if not server:
        return 0, None
    m = _SERVER_HIK_RE.search(server)
    if m:
        return 60, server
    return 0, None


def score_www_authenticate(header: str | None) -> tuple[int, str | None]:
    if not header:
        return 0, None
    if "digest" not in header.lower():
        return 0, None
    realm_m = re.search(r'realm="([^"]+)"', header, re.IGNORECASE)
    realm = realm_m.group(1) if realm_m else None
    if realm and _REALM_HIK_RE.search(realm):
        return 30, realm
    return 0, realm


def score_isapi_xml(xml_text: str | None) -> tuple[int, dict[str, str]]:
    if not xml_text:
        return 0, {}
    parsed = _parse_isapi_xml(xml_text)
    if not parsed:
        return 0, {}
    hint_fields = {"deviceType", "deviceID", "serialNumber", "firmwareVersion", "model"}
    if hint_fields & set(parsed.keys()):
        return 90, parsed
    return 0, parsed


def _html_title(body: str | None) -> str | None:
    if not body:
        return None
    m = re.search(r"<title[^>]*>([^<]+)</title>", body, re.IGNORECASE)
    return m.group(1).strip() if m else None


def is_dahua_like(
    html_body: str | None = None,
    dahua_cgi: str | None = None,
    dahua_magicbox_status: int | None = None,
    dahua_www_authenticate: str | None = None,
) -> bool:
    """Heuristic: page/CGI looks like Dahua (used to suppress false Hikvision hits)."""
    if dahua_magicbox_status in (200, 401, 403):
        return True
    if dahua_cgi and _DAHUA_CGI_RE.search(dahua_cgi):
        return True
    if dahua_www_authenticate and _REALM_DAHUA_LOGIN_RE.search(dahua_www_authenticate):
        return True
    if not html_body:
        return False
    if _DAHUA_WEBUI_RE.search(html_body):
        return True
    return bool(_DAHUA_BODY_RE.search(html_body) or _DAHUA_PATH_RE.search(html_body))


def score_html_title(body: str | None) -> tuple[int, str | None]:
    if not body:
        return 0, None
    title = _html_title(body)
    score = 0
    if title and _TITLE_HIK_RE.search(title):
        score += 40
    # 大华大量机型也用 "WEB SERVICE" 标题，有大华特征时不计入海康
    elif (
        title
        and _TITLE_HIK_WEB_SERVICE.match(title)
        and not is_dahua_like(body)
    ):
        score += 40
    if _HIK_PATH_RE.search(body):
        score += 20
    return score, title


def score_isapi_status(status: int | None) -> tuple[int, int | None]:
    """ISAPI is a Hikvision-proprietary path. Any non-404 response is a strong signal."""
    if status is None:
        return 0, None
    if status == 401:
        return 50, status
    if status == 403:
        return 30, status
    if status == 200:
        return 0, status
    return 0, status


def _score_hikvision(
    server_header: str | None,
    www_authenticate: str | None,
    isapi_xml: str | None,
    html_body: str | None,
    isapi_status: int | None,
    *,
    suppress_isapi_status: bool = False,
) -> tuple[int, dict[str, Any]]:
    total = 0
    hits: dict[str, Any] = {}

    s, val = score_server_header(server_header)
    if s:
        hits["server"] = val
    total += s

    if not suppress_isapi_status:
        s, val = score_isapi_status(isapi_status)
        if s:
            hits["isapi_status"] = val
        total += s

    s, val = score_www_authenticate(www_authenticate)
    if s:
        hits["realm"] = val
    total += s

    s, val = score_isapi_xml(isapi_xml)
    if s:
        hits["isapi"] = val
    total += s

    s, val = score_html_title(html_body)
    if s:
        hits["html_title"] = val
    total += s

    return min(total, 100), hits


def _score_dahua(
    server_header: str | None,
    html_body: str | None,
    dahua_cgi: str | None,
    www_authenticate: str | None,
    dahua_magicbox_status: int | None = None,
    dahua_www_authenticate: str | None = None,
) -> tuple[int, dict[str, Any]]:
    total = 0
    hits: dict[str, Any] = {}

    if server_header and _SERVER_DAHUA_RE.search(server_header):
        total += 60
        hits["server"] = server_header

    if dahua_magicbox_status == 401:
        total += 55
        hits["magicbox_auth"] = 401
    elif dahua_magicbox_status == 403:
        total += 40
        hits["magicbox_auth"] = 403
    elif dahua_magicbox_status == 200 and dahua_cgi:
        total += 45
        hits["magicbox_ok"] = True

    if dahua_cgi:
        parsed = parse_dahua_cgi(dahua_cgi)
        if parsed:
            total += 90
            hits["dahua_cgi"] = parsed
        elif _DAHUA_CGI_RE.search(dahua_cgi):
            total += 70
            hits["dahua_cgi_raw"] = dahua_cgi[:200]

    if html_body:
        title = _html_title(html_body)
        if title and _TITLE_DAHUA_RE.search(title):
            total += 40
            hits["html_title"] = title
        if _DAHUA_WEBUI_RE.search(html_body):
            total += 50
            hits["dahua_webui"] = True
        elif "jsbase/" in html_body.lower() and (
            dahua_magicbox_status in (200, 401, 403) or _DAHUA_PATH_RE.search(html_body)
        ):
            total += 35
            hits["jsbase_shell"] = True
        if _DAHUA_BODY_RE.search(html_body):
            total += 50
            hits["dahua_body"] = True
        if _DAHUA_PATH_RE.search(html_body):
            total += 30
            hits["dahua_paths"] = True
        if (
            title
            and _TITLE_WEB_SERVICE.match(title)
            and _DAHUA_PATH_RE.search(html_body)
        ):
            total += 35
            hits["web_service_rpc2"] = True

    auth = dahua_www_authenticate or www_authenticate
    if auth and "digest" in auth.lower():
        if re.search(r'realm="[^"]*dahua', auth, re.IGNORECASE):
            total += 30
            hits["realm"] = "dahua"
        elif re.search(r'device_cgi', auth, re.IGNORECASE):
            total += 45
            hits["realm"] = "device_cgi"
        elif _REALM_DAHUA_LOGIN_RE.search(auth):
            total += 40
            hits["realm"] = "login_to"

    return min(total, 100), hits


def _score_huawei(
    server_header: str | None,
    html_body: str | None,
    huawei_cgi: str | None,
) -> tuple[int, dict[str, Any]]:
    total = 0
    hits: dict[str, Any] = {}

    if server_header and _SERVER_HUAWEI_RE.search(server_header):
        total += 60
        hits["server"] = server_header

    if huawei_cgi and _HUAWEI_CGI_RE.search(huawei_cgi):
        total += 80
        hits["huawei_cgi"] = True
    elif huawei_cgi and re.search(r"table\.\w+\.\w+=", huawei_cgi):
        total += 50
        hits["huawei_config"] = True

    if html_body:
        m = re.search(r"<title[^>]*>([^<]+)</title>", html_body, re.IGNORECASE)
        title = m.group(1).strip() if m else None
        if title and _TITLE_HUAWEI_RE.search(title):
            total += 45
            hits["html_title"] = title
        if _HUAWEI_PATH_RE.search(html_body) and _TITLE_HUAWEI_RE.search(html_body):
            total += 20
            hits["huawei_paths"] = True

    return min(total, 100), hits


def _score_ezviz(
    html_body: str | None,
    isapi_xml: str | None,
    isapi_status: int | None,
) -> tuple[int, dict[str, Any]]:
    total = 0
    hits: dict[str, Any] = {}

    if html_body and _EZVIZ_RE.search(html_body):
        total += 55
        hits["ezviz_brand"] = True
        if _EZVIZ_PATH_RE.search(html_body):
            total += 20
            hits["ezviz_paths"] = True

    if isapi_status in (401, 403) and html_body and _EZVIZ_RE.search(html_body):
        total += 40
        hits["isapi_with_ezviz"] = isapi_status

    if isapi_xml and _EZVIZ_RE.search(isapi_xml):
        total += 30
        hits["isapi_xml_ezviz"] = True

    return min(total, 100), hits


def _score_xiaomi(html_body: str | None) -> tuple[int, dict[str, Any]]:
    total = 0
    hits: dict[str, Any] = {}

    if not html_body:
        return 0, hits

    if _XIAOMI_RE.search(html_body):
        total += 55
        hits["xiaomi_brand"] = True
    m = re.search(r"<title[^>]*>([^<]+)</title>", html_body, re.IGNORECASE)
    title = m.group(1).strip() if m else None
    if title and _XIAOMI_RE.search(title):
        total += 40
        hits["html_title"] = title
    if _XIAOMI_PATH_RE.search(html_body):
        total += 25
        hits["xiaomi_paths"] = True

    return min(total, 100), hits


def evaluate(
    server_header: str | None = None,
    www_authenticate: str | None = None,
    isapi_xml: str | None = None,
    html_body: str | None = None,
    isapi_status: int | None = None,
    dahua_cgi: str | None = None,
    dahua_magicbox_status: int | None = None,
    dahua_www_authenticate: str | None = None,
    huawei_cgi: str | None = None,
) -> FingerprintEvidence:
    """Score all supported vendors and return the best match above threshold."""
    dahua_like = is_dahua_like(
        html_body, dahua_cgi, dahua_magicbox_status, dahua_www_authenticate
    )
    hik_score, hik_hits = _score_hikvision(
        server_header,
        www_authenticate,
        isapi_xml,
        html_body,
        isapi_status,
        suppress_isapi_status=dahua_like,
    )
    dahua_score, dahua_hits = _score_dahua(
        server_header,
        html_body,
        dahua_cgi,
        www_authenticate,
        dahua_magicbox_status,
        dahua_www_authenticate,
    )
    huawei_score, huawei_hits = _score_huawei(server_header, html_body, huawei_cgi)
    ezviz_score, ezviz_hits = _score_ezviz(html_body, isapi_xml, isapi_status)
    xiaomi_score, xiaomi_hits = _score_xiaomi(html_body)

    # Ezviz shares ISAPI with Hikvision; prefer ezviz when explicit branding wins.
    if ezviz_score >= CONFIDENCE_THRESHOLD and hik_score >= CONFIDENCE_THRESHOLD:
        if ezviz_score >= hik_score or (html_body and _EZVIZ_RE.search(html_body)):
            hik_score = max(0, hik_score - 30)

    candidates: list[tuple[str, int, dict[str, Any]]] = [
        (VENDOR_HIKVISION, hik_score, hik_hits),
        (VENDOR_DAHUA, dahua_score, dahua_hits),
        (VENDOR_HUAWEI, huawei_score, huawei_hits),
        (VENDOR_EZVIZ, ezviz_score, ezviz_hits),
        (VENDOR_XIAOMI, xiaomi_score, xiaomi_hits),
    ]

    best_vendor: str | None = None
    best_score = 0
    best_hits: dict[str, Any] = {}

    ranked = sorted(candidates, key=lambda x: x[1], reverse=True)
    for vendor, score, hits in ranked:
        if score >= CONFIDENCE_THRESHOLD and score > best_score:
            best_vendor = vendor
            best_score = score
            best_hits = hits

    if best_vendor is None:
        vendor, score, hits = ranked[0]
        return FingerprintEvidence(score=score, hits=hits, vendor=None)

    return FingerprintEvidence(score=best_score, hits=best_hits, vendor=best_vendor)


def _parse_isapi_xml(xml_text: str) -> dict[str, str]:
    """Extract Hikvision deviceInfo fields, tolerant of XML namespace."""
    out: dict[str, str] = {}
    fields = (
        "deviceName",
        "deviceID",
        "deviceDescription",
        "deviceLocation",
        "deviceType",
        "model",
        "serialNumber",
        "firmwareVersion",
        "firmwareReleasedDate",
        "macAddress",
        "encoderVersion",
    )
    for f in fields:
        m = re.search(
            rf"<(?:[\w-]+:)?{f}>\s*([^<]+?)\s*</(?:[\w-]+:)?{f}>",
            xml_text,
            re.IGNORECASE,
        )
        if m:
            out[f] = m.group(1).strip()
    return out


def parse_isapi_xml(xml_text: str) -> dict[str, str]:
    return _parse_isapi_xml(xml_text)


def parse_dahua_cgi(text: str) -> dict[str, str]:
    """Parse Dahua magicBox key=value response."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" not in line or line.startswith("<"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"')
        if key:
            out[key] = val
    key_map = {
        "type": "model",
        "deviceType": "model",
        "serialNumber": "serial",
        "serialNo": "serial",
        "updateSerial": "serial",
        "softwareVersion": "firmware",
        "version": "firmware",
        "hardwareVersion": "firmware",
        "deviceName": "device_name",
        "machineName": "device_name",
        "macAddress": "mac",
    }
    normalized: dict[str, str] = {}
    for k, v in out.items():
        nk = key_map.get(k, k)
        if nk not in normalized or len(v) > len(normalized.get(nk, "")):
            normalized[nk] = v
    return normalized


def parse_huawei_cgi(text: str) -> dict[str, str]:
    """Parse Huawei configManager table.Section.Key=value response."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" not in line or line.startswith("<"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"')
        short = key.rsplit(".", 1)[-1] if "." in key else key
        if short:
            out[short] = val
    key_map = {
        "SerialNumber": "serial",
        "DeviceType": "device_type",
        "SoftwareVersion": "firmware",
        "HardwareVersion": "firmware",
        "MachineName": "device_name",
        "DeviceName": "device_name",
        "Model": "model",
        "DeviceModel": "model",
        "MacAddress": "mac",
    }
    normalized: dict[str, str] = {}
    for k, v in out.items():
        nk = key_map.get(k, k)
        if nk not in normalized or len(v) > len(normalized.get(nk, "")):
            normalized[nk] = v
    return normalized
