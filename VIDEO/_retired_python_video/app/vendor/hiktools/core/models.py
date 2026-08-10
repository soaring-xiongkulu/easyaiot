from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class Credential:
    username: str
    password: str

    def __repr__(self) -> str:
        return f"Credential({self.username!r}, ***)"


@dataclass
class Device:
    ip: str
    port: int
    scheme: str = "http"
    vendor: str | None = None
    device_role: str | None = None
    is_hikvision: bool = False
    confidence: int = 0
    model: str | None = None
    serial: str | None = None
    firmware: str | None = None
    device_name: str | None = None
    device_type: str | None = None
    mac: str | None = None
    rtsp_url: str | None = None
    source: str = "http"
    evidence: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    scanned_at: datetime = field(default_factory=datetime.now)

    @property
    def url(self) -> str:
        return f"{self.scheme}://{self.ip}:{self.port}"

    @property
    def is_recognized(self) -> bool:
        return self.vendor is not None and self.confidence >= 60

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["scanned_at"] = self.scanned_at.isoformat()
        return d
