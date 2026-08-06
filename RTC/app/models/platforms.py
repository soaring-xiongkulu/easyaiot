"""支持的摄像头平台定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AuthMode(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    OAUTH = "oauth"
    WEBUI = "webui"


@dataclass(frozen=True)
class PlatformField:
    name: str
    label: str
    required: bool = True
    secret: bool = False
    placeholder: str = ""
    description: str = ""


@dataclass(frozen=True)
class CameraPlatform:
    id: str
    name: str
    vendor: str
    schema: str
    auth_mode: AuthMode
    description: str
    fields: tuple[PlatformField, ...] = field(default_factory=tuple)
    supports_two_way_audio: bool = False
    supports_substream: bool = False
    docs_url: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "vendor": self.vendor,
            "schema": self.schema,
            "auth_mode": self.auth_mode.value,
            "description": self.description,
            "fields": [
                {
                    "name": f.name,
                    "label": f.label,
                    "required": f.required,
                    "secret": f.secret,
                    "placeholder": f.placeholder,
                    "description": f.description,
                }
                for f in self.fields
            ],
            "supports_two_way_audio": self.supports_two_way_audio,
            "supports_substream": self.supports_substream,
            "docs_url": self.docs_url,
            "notes": self.notes,
        }
