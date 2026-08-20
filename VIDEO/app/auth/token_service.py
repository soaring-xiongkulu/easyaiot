"""访问令牌：HMAC 签名 JSON（仅用标准库，Flask 环境同样可用）。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_lock = threading.RLock()
_refresh_registry: Dict[str, Dict[str, Any]] = {}
_revoked_access: Dict[str, float] = {}

ACCESS_MAX_AGE = int(os.environ.get("VIDEO_AUTH_ACCESS_TTL", "86400"))
REFRESH_MAX_AGE = int(os.environ.get("VIDEO_AUTH_REFRESH_TTL", "604800"))


def _secret() -> bytes:
    raw = (
        os.environ.get("VIDEO_AUTH_SECRET")
        or os.environ.get("SECRET_KEY")
        or "easyaiot-video-auth-edge"
    )
    return raw.encode("utf-8")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign_payload(payload: Dict[str, Any]) -> str:
    body = _b64url(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    sig = _b64url(hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def _unsign(token: str, max_age: int) -> Optional[Dict[str, Any]]:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None
    expect = _b64url(hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(expect, sig):
        return None
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    iat = int(payload.get("iat") or 0)
    if iat <= 0 or (time.time() - iat) > max_age:
        return None
    return payload


def create_token_pair(user_id: int, username: str, role: str) -> Dict[str, Any]:
    now = int(time.time())
    access_payload = {
        "uid": user_id,
        "username": username,
        "role": role,
        "jti": secrets.token_urlsafe(16),
        "typ": "access",
        "iat": now,
    }
    refresh_payload = {
        "uid": user_id,
        "username": username,
        "role": role,
        "jti": secrets.token_urlsafe(16),
        "typ": "refresh",
        "iat": now,
    }
    access_token = _sign_payload(access_payload)
    refresh_token = _sign_payload(refresh_payload)
    with _lock:
        _refresh_registry[refresh_token] = {
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": now + REFRESH_MAX_AGE,
        }
    return {
        "userId": user_id,
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresTime": (now + ACCESS_MAX_AGE) * 1000,
    }


def verify_access_token(authorization: str) -> Optional[Dict[str, Any]]:
    raw = (authorization or "").strip()
    if not raw:
        return None
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    if not raw:
        return None
    payload = _unsign(raw, ACCESS_MAX_AGE)
    if not payload or payload.get("typ") != "access":
        return None
    jti = payload.get("jti")
    with _lock:
        if jti and jti in _revoked_access and _revoked_access[jti] > time.time():
            return None
    return payload


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    token = (refresh_token or "").strip()
    if not token:
        return None
    with _lock:
        meta = _refresh_registry.get(token)
        if meta and meta.get("exp", 0) < time.time():
            _refresh_registry.pop(token, None)
            meta = None
    payload = _unsign(token, REFRESH_MAX_AGE)
    if not payload or payload.get("typ") != "refresh":
        return None
    return create_token_pair(
        int(payload["uid"]),
        str(payload.get("username") or ""),
        str(payload.get("role") or "user"),
    )


def revoke_token(access_authorization: str = "", refresh_token: str = "") -> None:
    payload = verify_access_token(access_authorization) if access_authorization else None
    with _lock:
        if payload and payload.get("jti"):
            _revoked_access[payload["jti"]] = time.time() + ACCESS_MAX_AGE
        if refresh_token:
            _refresh_registry.pop(refresh_token.strip(), None)


def extract_bearer(req_headers) -> str:
    return (
        req_headers.get("Authorization")
        or req_headers.get("X-Authorization")
        or ""
    ).strip()
