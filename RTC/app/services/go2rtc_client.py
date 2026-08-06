"""go2rtc HTTP API 客户端。"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote, urlencode

import requests


class Go2RtcClient:
    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = (base_url or os.getenv("GO2RTC_API_URL", "http://127.0.0.1:1984")).rstrip("/")
        self.username = username or os.getenv("GO2RTC_USERNAME", "")
        self.password = password or os.getenv("GO2RTC_PASSWORD", "")
        self.timeout = timeout
        self._auth = (self.username, self.password) if self.username else None

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        kwargs.setdefault("timeout", self.timeout)
        if self._auth:
            kwargs.setdefault("auth", self._auth)
        resp = requests.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp

    def health(self) -> dict[str, Any]:
        resp = self._request("GET", "/api")
        return resp.json()

    def list_streams(self) -> dict[str, Any]:
        resp = self._request("GET", "/api/streams")
        return resp.json()

    def create_stream(self, name: str, source: str) -> None:
        params = urlencode({"name": name, "src": source})
        self._request("PUT", f"/api/streams?{params}")

    def update_stream(self, name: str, source: str) -> None:
        params = urlencode({"name": name, "src": source})
        self._request("PATCH", f"/api/streams?{params}")

    def delete_stream(self, name: str) -> None:
        params = urlencode({"src": name})
        self._request("DELETE", f"/api/streams?{params}")

    def get_config(self) -> str:
        resp = self._request("GET", "/api/config")
        return resp.text

    def patch_config(self, yaml_fragment: str) -> None:
        self._request("PATCH", "/api/config", data=yaml_fragment,
                      headers={"Content-Type": "text/yaml"})

    def play_urls(self, stream_name: str) -> dict[str, str]:
        """返回常用播放地址。"""
        encoded = quote(stream_name, safe="")
        base = self.base_url
        return {
            "webrtc": f"{base}/api/webrtc?src={encoded}",
            "hls": f"{base}/api/stream.m3u8?src={encoded}",
            "mjpeg": f"{base}/api/frame.jpeg?src={encoded}",
            "mp4": f"{base}/api/stream.mp4?src={encoded}",
            "rtsp": f"rtsp://{os.getenv('RTC_RTSP_HOST', '127.0.0.1')}:{os.getenv('RTC_RTSP_PORT', '8554')}/{stream_name}",
            "flv": f"{base}/api/stream.flv?src={encoded}",
        }
