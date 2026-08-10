"""FFmpeg 版本兼容：二进制解析、H.264 编码器选择、RTSP 超时参数等。"""
from __future__ import annotations

import os
import subprocess
from typing import List, Optional, Set

# FFmpeg 8+：-stimeout/-rw_timeout 已移除，统一为 -timeout（单位仍为微秒）
_FFMPEG_RTSP_OPEN_TIMEOUT_FLAG: Optional[str] = None
_FFMPEG_SUPPORTS_RW_TIMEOUT: Optional[bool] = None
_RTSP_DEMUXER_HELP: Optional[str] = None
_FFMPEG_ENCODER_NAMES: Optional[Set[str]] = None
_RESOLVED_FFMPEG_BIN: Optional[str] = None


def _is_runnable_binary(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    lower = path.lower()
    if lower.endswith(('.exe', '.cmd', '.bat')):
        return True
    return os.access(path, os.X_OK)


def resolve_ffmpeg_binary() -> str:
    """优先 FFMPEG_PATH；否则 PATH 上的 ffmpeg。"""
    global _RESOLVED_FFMPEG_BIN
    if _RESOLVED_FFMPEG_BIN is not None:
        return _RESOLVED_FFMPEG_BIN
    explicit = (os.getenv('FFMPEG_PATH') or '').strip().strip('"')
    if _is_runnable_binary(explicit):
        _RESOLVED_FFMPEG_BIN = explicit
        return _RESOLVED_FFMPEG_BIN
    _RESOLVED_FFMPEG_BIN = 'ffmpeg'
    return _RESOLVED_FFMPEG_BIN


def ffmpeg_encoder_names() -> Set[str]:
    """探测当前 ffmpeg 可用的编码器名（缓存）。"""
    global _FFMPEG_ENCODER_NAMES
    if _FFMPEG_ENCODER_NAMES is not None:
        return _FFMPEG_ENCODER_NAMES
    names: Set[str] = set()
    try:
        probe = subprocess.run(
            [resolve_ffmpeg_binary(), '-hide_banner', '-encoders'],
            capture_output=True,
            timeout=8,
        )
        text = (probe.stdout or b'').decode(errors='replace')
        for line in text.splitlines():
            # e.g. " V..... libx264              libx264 H.264 ..."
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].startswith('V'):
                names.add(parts[1])
    except Exception:
        names = set()
    _FFMPEG_ENCODER_NAMES = names
    return _FFMPEG_ENCODER_NAMES


def resolve_view_h264_codec() -> str:
    """预览转推 H.264 编码器：环境变量覆盖，否则 libx264 → h264_nvenc → copy。"""
    forced = (
        os.getenv('VIEW_FFMPEG_CODEC')
        or os.getenv('FFMPEG_VIDEO_CODEC')
        or ''
    ).strip().lower()
    if forced in ('libx264', 'h264_nvenc', 'copy', 'h264_qsv', 'h264_amf'):
        return forced
    encoders = ffmpeg_encoder_names()
    if 'libx264' in encoders:
        return 'libx264'
    if 'h264_nvenc' in encoders:
        return 'h264_nvenc'
    if 'h264_qsv' in encoders:
        return 'h264_qsv'
    if 'h264_amf' in encoders:
        return 'h264_amf'
    return 'copy'


def ffmpeg_option_missing(stderr: bytes, option: str = "") -> bool:
    err = (stderr or b"").decode(errors="replace")
    if "Unrecognized option" in err or "Option not found" in err:
        return True
    if option and f"Option {option} not found" in err:
        return True
    return False


def _rtsp_demuxer_help_text() -> str:
    """读取 ffmpeg RTSP demuxer 帮助，用于判断各版本支持的超时参数。"""
    global _RTSP_DEMUXER_HELP
    if _RTSP_DEMUXER_HELP is not None:
        return _RTSP_DEMUXER_HELP
    try:
        probe = subprocess.run(
            [resolve_ffmpeg_binary(), "-hide_banner", "-h", "demuxer=rtsp"],
            capture_output=True,
            timeout=5,
        )
        _RTSP_DEMUXER_HELP = (probe.stdout or b"").decode(errors="replace")
    except Exception:
        _RTSP_DEMUXER_HELP = ""
    return _RTSP_DEMUXER_HELP


def _rtsp_demuxer_has_option(option: str) -> bool:
    name = option.lstrip("-")
    text = _rtsp_demuxer_help_text()
    return f"-{name}" in text


def ffmpeg_rtsp_open_timeout_flag() -> str:
    """返回当前 ffmpeg 支持的 RTSP 连接超时参数名。"""
    global _FFMPEG_RTSP_OPEN_TIMEOUT_FLAG
    if _FFMPEG_RTSP_OPEN_TIMEOUT_FLAG is not None:
        return _FFMPEG_RTSP_OPEN_TIMEOUT_FLAG
    if _rtsp_demuxer_has_option("stimeout"):
        _FFMPEG_RTSP_OPEN_TIMEOUT_FLAG = "-stimeout"
    else:
        _FFMPEG_RTSP_OPEN_TIMEOUT_FLAG = "-timeout"
    return _FFMPEG_RTSP_OPEN_TIMEOUT_FLAG


def ffmpeg_supports_rw_timeout() -> bool:
    """FFmpeg 8+ 已移除 -rw_timeout，仅保留 -timeout 覆盖 socket I/O。"""
    global _FFMPEG_SUPPORTS_RW_TIMEOUT
    if _FFMPEG_SUPPORTS_RW_TIMEOUT is not None:
        return _FFMPEG_SUPPORTS_RW_TIMEOUT
    if _rtsp_demuxer_has_option("rw_timeout"):
        _FFMPEG_SUPPORTS_RW_TIMEOUT = True
        return _FFMPEG_SUPPORTS_RW_TIMEOUT
    # 帮助文本不可用时，回退到运行时探测（lavfi 轻量输入）
    try:
        probe = subprocess.run(
            [
                resolve_ffmpeg_binary(),
                "-hide_banner",
                "-rw_timeout",
                "1",
                "-f",
                "lavfi",
                "-i",
                "nullsrc=s=1x1:d=0.01",
                "-frames:v",
                "1",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            timeout=8,
        )
        _FFMPEG_SUPPORTS_RW_TIMEOUT = not ffmpeg_option_missing(probe.stderr, "rw_timeout")
    except Exception:
        _FFMPEG_SUPPORTS_RW_TIMEOUT = False
    return _FFMPEG_SUPPORTS_RW_TIMEOUT


def ffmpeg_rtsp_timeout_args(open_us: int, io_us: int) -> List[str]:
    """按当前 ffmpeg 版本组装 RTSP 超时参数。"""
    open_flag = ffmpeg_rtsp_open_timeout_flag()
    if ffmpeg_supports_rw_timeout():
        return [open_flag, str(open_us), "-rw_timeout", str(io_us)]
    # FFmpeg 8：-timeout 同时覆盖连接与读写，取较大值
    return [open_flag, str(max(open_us, io_us))]
