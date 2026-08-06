"""流管理服务。"""

from __future__ import annotations

from typing import Any

from app.services.go2rtc_client import Go2RtcClient
from app.services.platform_registry import build_stream_url, get_platform


class StreamService:
    def __init__(self, client: Go2RtcClient | None = None):
        self.client = client or Go2RtcClient()

    def register_platform_stream(
        self,
        name: str,
        platform_id: str,
        params: dict[str, Any],
        *,
        update: bool = False,
    ) -> dict[str, Any]:
        platform = get_platform(platform_id)
        if not platform:
            raise ValueError(f"不支持的平台: {platform_id}")

        source = build_stream_url(platform_id, params)
        if update:
            self.client.update_stream(name, source)
        else:
            self.client.create_stream(name, source)

        return {
            "name": name,
            "platform": platform_id,
            "source": source,
            "play_urls": self.client.play_urls(name),
        }

    def register_raw_stream(self, name: str, source: str, *, update: bool = False) -> dict[str, Any]:
        if update:
            self.client.update_stream(name, source)
        else:
            self.client.create_stream(name, source)
        return {"name": name, "source": source, "play_urls": self.client.play_urls(name)}

    def list_streams(self) -> dict[str, Any]:
        return self.client.list_streams()

    def delete_stream(self, name: str) -> None:
        self.client.delete_stream(name)

    def get_play_urls(self, name: str) -> dict[str, str]:
        return self.client.play_urls(name)

    def go2rtc_info(self) -> dict[str, Any]:
        return self.client.health()
