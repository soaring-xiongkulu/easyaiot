"""RTSP URL 用户信息与解析工具（支持密码中的特殊字符）。"""
from __future__ import annotations

from urllib.parse import quote, unquote, urlparse, urlsplit, urlunsplit


def quote_rtsp_userinfo(value: str) -> str:
    """对 RTSP URL 用户名/密码做百分号编码。"""
    return quote(value or "", safe="")


def build_rtsp_auth_prefix(username: str | None, password: str | None) -> str:
    if not username:
        return ""
    user = quote_rtsp_userinfo(username)
    pw = quote_rtsp_userinfo(password or "")
    return f"{user}:{pw}@"


def redact_url_credentials(value: str | None) -> str:
    """移除 URL 中的用户信息，避免日志泄露用户名或密码。"""
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        parsed = urlsplit(text)
        if not parsed.scheme or "@" not in parsed.netloc:
            return text
        safe_netloc = parsed.netloc.rsplit("@", 1)[-1]
        return urlunsplit(parsed._replace(netloc=safe_netloc))
    except (TypeError, ValueError):
        # 即使 URL 不完全合法，也尽量去掉 scheme 后、首个路径前的 userinfo。
        if "://" in text and "@" in text:
            scheme, remainder = text.split("://", 1)
            authority_end = len(remainder)
            for separator in ("/", "?", "#"):
                index = remainder.find(separator)
                if index >= 0:
                    authority_end = min(authority_end, index)
            authority = remainder[:authority_end]
            if "@" in authority:
                remainder = authority.rsplit("@", 1)[-1] + remainder[authority_end:]
                return f"{scheme}://{remainder}"
        return text


def parse_rtsp_auth(source: str) -> dict[str, str | int | None]:
    """从 RTSP URL 解析认证信息与主机（自动解码百分号编码）。"""
    text = (source or "").strip()
    if not text.lower().startswith("rtsp://"):
        return {
            "username": None,
            "password": None,
            "hostname": None,
            "port": None,
        }

    parsed = urlparse(text)
    username = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    hostname = (parsed.hostname or "").strip() or None
    port = parsed.port
    if port is None and hostname:
        port = 554
    return {
        "username": username,
        "password": password,
        "hostname": hostname,
        "port": port,
    }
