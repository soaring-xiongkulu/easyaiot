"""摄像头平台注册表与流 URL 构建。"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlencode

from app.models.platforms import AuthMode, CameraPlatform, PlatformField

# ---------------------------------------------------------------------------
# 平台定义（对应 go2rtc internal/* 模块）
# ---------------------------------------------------------------------------

PLATFORMS: dict[str, CameraPlatform] = {
    "tapo": CameraPlatform(
        id="tapo",
        name="TP-Link Tapo",
        vendor="TP-Link",
        schema="tapo",
        auth_mode=AuthMode.LOCAL,
        description="TP-Link Tapo 私有协议，支持双向对讲",
        fields=(
            PlatformField("host", "摄像头 IP", placeholder="192.168.1.123"),
            PlatformField("password", "云密码", secret=True, description="Tapo App 云密码，非 RTSP 密码"),
            PlatformField("username", "用户名", required=False, placeholder="admin"),
            PlatformField("password_hash", "密码哈希", required=False, secret=True,
                          description="MD5/SHA256 大写哈希，与 username 配合使用"),
        ),
        supports_two_way_audio=True,
        supports_substream=True,
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/tapo/README.md",
        notes="使用 Tapo App 云密码；新固件可能需要 SHA256 哈希",
    ),
    "tuya": CameraPlatform(
        id="tuya",
        name="Tuya 涂鸦",
        vendor="Tuya",
        schema="tuya",
        auth_mode=AuthMode.CLOUD,
        description="Tuya Smart API / Cloud API，支持双向对讲",
        fields=(
            PlatformField("endpoint", "API 端点", placeholder="protect-us.ismartlife.me 或 openapi.tuyaus.com"),
            PlatformField("device_id", "设备 ID"),
            PlatformField("email", "Tuya Smart 邮箱", required=False),
            PlatformField("password", "Tuya Smart 密码", required=False, secret=True),
            PlatformField("client_id", "Client ID", required=False),
            PlatformField("client_secret", "Client Secret", required=False, secret=True),
            PlatformField("uid", "UID", required=False),
        ),
        supports_two_way_audio=True,
        supports_substream=True,
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/tuya/README.md",
        notes="Smart Life 账号不支持，需使用 Tuya Smart App；Cloud API 需订阅 IoT Video Live Stream",
    ),
    "ring": CameraPlatform(
        id="ring",
        name="Ring",
        vendor="Amazon Ring",
        schema="ring",
        auth_mode=AuthMode.OAUTH,
        description="Ring 门铃/摄像头，支持双向对讲",
        fields=(
            PlatformField("device_id", "设备 ID"),
            PlatformField("refresh_token", "Refresh Token", secret=True),
        ),
        supports_two_way_audio=True,
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/ring/README.md",
        notes="可通过 go2rtc WebUI > Add > Ring 完成 OAuth 授权",
    ),
    "nest": CameraPlatform(
        id="nest",
        name="Google Nest",
        vendor="Google",
        schema="nest",
        auth_mode=AuthMode.OAUTH,
        description="Google Nest 门铃/摄像头（WebRTC）",
        fields=(
            PlatformField("client_id", "Client ID", secret=True),
            PlatformField("client_secret", "Client Secret", secret=True),
            PlatformField("refresh_token", "Refresh Token", secret=True),
            PlatformField("project_id", "Project ID"),
            PlatformField("device_id", "Device ID"),
        ),
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/nest/README.md",
        notes="需 Google Device Access 付费 API；也可通过 Home Assistant 桥接",
    ),
    "xiaomi": CameraPlatform(
        id="xiaomi",
        name="小米米家",
        vendor="Xiaomi",
        schema="xiaomi",
        auth_mode=AuthMode.WEBUI,
        description="小米 Mi Home 生态摄像头 P2P 协议",
        fields=(
            PlatformField("account_id", "账号 ID", description="go2rtc 登录后生成的账号标识"),
            PlatformField("region", "区域", placeholder="cn"),
            PlatformField("host", "摄像头 IP", placeholder="192.168.1.123"),
            PlatformField("did", "设备 DID"),
            PlatformField("model", "设备型号", placeholder="isa.camera.hlc7"),
        ),
        supports_two_way_audio=True,
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/xiaomi/README.md",
        notes="需 go2rtc WebUI > Add > Xiaomi 完成账号绑定；连接需互联网获取加密密钥",
    ),
    "wyze": CameraPlatform(
        id="wyze",
        name="Wyze",
        vendor="Wyze",
        schema="wyze",
        auth_mode=AuthMode.WEBUI,
        description="Wyze 原生 P2P 协议，支持双向对讲",
        fields=(
            PlatformField("host", "摄像头 IP", placeholder="192.168.1.123"),
            PlatformField("uid", "P2P UID"),
            PlatformField("enr", "ENR", secret=True),
            PlatformField("mac", "MAC 地址", placeholder="AABBCCDDEEFF"),
            PlatformField("model", "型号", placeholder="HL_CAM4"),
            PlatformField("api_id", "API ID", required=False),
            PlatformField("api_key", "API Key", required=False, secret=True),
        ),
        supports_two_way_audio=True,
        supports_substream=True,
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/wyze/README.md",
        notes="需 Wyze Developer Portal API Key；WebUI 登录后自动生成流 URL",
    ),
    "doorbird": CameraPlatform(
        id="doorbird",
        name="DoorBird",
        vendor="DoorBird",
        schema="doorbird",
        auth_mode=AuthMode.LOCAL,
        description="DoorBird 门铃，支持 MJPEG/音频/双向对讲",
        fields=(
            PlatformField("host", "设备 IP", placeholder="192.168.1.123"),
            PlatformField("username", "用户名", placeholder="admin"),
            PlatformField("password", "密码", secret=True),
            PlatformField("media", "媒体类型", required=False, placeholder="video",
                          description="video | audio | 留空为双向对讲"),
        ),
        supports_two_way_audio=True,
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/doorbird/README.md",
        notes="建议创建专用 API 用户，权限：Watch always + API operator",
    ),
    "gopro": CameraPlatform(
        id="gopro",
        name="GoPro",
        vendor="GoPro",
        schema="gopro",
        auth_mode=AuthMode.LOCAL,
        description="GoPro HERO9-12 USB/Wi-Fi 直播",
        fields=(
            PlatformField("host", "相机 IP", placeholder="172.20.100.51"),
        ),
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/gopro/README.md",
        notes="支持 HERO9/10/11/12；WebUI > Add > GoPro 自动发现",
    ),
    "roborock": CameraPlatform(
        id="roborock",
        name="Roborock 石头",
        vendor="Roborock",
        schema="roborock",
        auth_mode=AuthMode.WEBUI,
        description="Roborock 带摄像头扫地机",
        fields=(
            PlatformField("source", "完整 roborock:// URL", description="从 go2rtc WebUI 复制"),
        ),
        supports_two_way_audio=True,
        docs_url="https://github.com/AlexxIT/go2rtc/blob/master/internal/roborock/README.md",
        notes="支持 S6 MaxV / S7 MaxV / Qrevo MaxV；WebUI > Add 登录 Roborock 账号",
    ),
}


def list_platforms() -> list[dict[str, Any]]:
    return [p.to_dict() for p in PLATFORMS.values()]


def get_platform(platform_id: str) -> CameraPlatform | None:
    return PLATFORMS.get(platform_id)


def build_stream_url(platform_id: str, params: dict[str, Any]) -> str:
    """根据平台与参数构建 go2rtc 源流 URL。"""
    platform = PLATFORMS.get(platform_id)
    if not platform:
        raise ValueError(f"不支持的平台: {platform_id}")

    stream_type = params.get("stream", "main")
    subtype = params.get("subtype")

    if platform_id == "tapo":
        host = params["host"]
        password = params.get("password", "")
        username = params.get("username", "")
        password_hash = params.get("password_hash", "")
        if username and password_hash:
            cred = f"{quote(username)}:{password_hash}"
        elif password:
            cred = quote(password)
        else:
            raise ValueError("tapo 需要 password 或 username+password_hash")
        url = f"tapo://{cred}@{host}"
        if subtype is not None:
            url += f"?subtype={subtype}"
        elif stream_type == "sub":
            url += "?subtype=1"
        return url

    if platform_id == "tuya":
        endpoint = params["endpoint"]
        query: dict[str, str] = {"device_id": params["device_id"]}
        if params.get("email"):
            query["email"] = params["email"]
        if params.get("password"):
            query["password"] = params["password"]
        if params.get("client_id"):
            query["client_id"] = params["client_id"]
        if params.get("client_secret"):
            query["client_secret"] = params["client_secret"]
        if params.get("uid"):
            query["uid"] = params["uid"]
        if stream_type == "sub":
            query["resolution"] = "sd"
        return f"tuya://{endpoint}?{urlencode(query)}"

    if platform_id == "ring":
        query = {"device_id": params["device_id"], "refresh_token": params["refresh_token"]}
        if params.get("snapshot"):
            query["snapshot"] = "1"
        return f"ring:?{urlencode(query)}"

    if platform_id == "nest":
        query = {
            "client_id": params["client_id"],
            "client_secret": params["client_secret"],
            "refresh_token": params["refresh_token"],
            "project_id": params["project_id"],
            "device_id": params["device_id"],
        }
        return f"nest:?{urlencode(query)}"

    if platform_id == "xiaomi":
        account_id = params["account_id"]
        region = params.get("region", "cn")
        host = params["host"]
        did = params["did"]
        model = params["model"]
        url = f"xiaomi://{account_id}:{region}@{host}?did={did}&model={model}"
        quality = params.get("quality")
        if quality is not None:
            url += f"&quality={quality}"
        return url

    if platform_id == "wyze":
        host = params["host"]
        query = {
            "uid": params["uid"],
            "enr": params["enr"],
            "mac": params["mac"],
            "model": params["model"],
            "dtls": params.get("dtls", "true"),
        }
        if stream_type == "sub":
            query["subtype"] = "sd"
        else:
            query["subtype"] = "hd"
        return f"wyze://{host}?{urlencode(query)}"

    if platform_id == "doorbird":
        username = quote(params.get("username", "admin"))
        password = quote(params["password"])
        host = params["host"]
        media = params.get("media")
        url = f"doorbird://{username}:{password}@{host}"
        if media:
            url += f"?media={media}"
        return url

    if platform_id == "gopro":
        return f"gopro://{params['host']}"

    if platform_id == "roborock":
        source = params.get("source") or params.get("url")
        if not source:
            raise ValueError("roborock 需要提供完整 roborock:// URL")
        if not source.startswith("roborock://"):
            source = f"roborock://{source}"
        return source

    raise ValueError(f"平台 {platform_id} 暂未实现 URL 构建")
