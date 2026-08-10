"""
RTSP/FFmpeg 拉流共用工具（realtime / snapshot 算法服务对齐）。
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import cv2


def build_opencv_ffmpeg_capture_options(rtsp_transport: str) -> str:
    transport = (rtsp_transport or "udp").strip().lower()
    if transport not in ("tcp", "udp"):
        transport = "udp"
    return (
        f"rtsp_transport;{transport}"
        "|timeout;10000000"
        "|rw_timeout;5000000"
        "|max_delay;500000"
        "|fflags;nobuffer+discardcorrupt+genpts"
        "|flags;low_delay"
        "|err_detect;ignore_err"
    )


def effective_rtsp_transport(url: str, default: str = "udp") -> str:
    """根据 URL/环境变量选择 rtsp_transport；HEVC/国标场景倾向 tcp。"""
    env = (
        os.getenv("AI_RTSP_TRANSPORT")
        or os.getenv("OPENCV_FFMPEG_RTSP_TRANSPORT")
        or os.getenv("FFMPEG_RTSP_TRANSPORT")
        or ""
    ).strip().lower()
    if env in ("tcp", "udp"):
        return env

    u = (url or "").lower()
    if is_gb28181_source(url) or "hevc" in u or "h265" in u or "h.265" in u:
        return "tcp"
    return (default or "udp").strip().lower() if (default or "udp").strip().lower() in ("tcp", "udp") else "udp"


def gb28181_async_queue_max() -> int:
    try:
        return max(1, min(int((os.getenv("AI_GB28181_ASYNC_QUEUE_MAX", "10") or "10").strip()), 600))
    except ValueError:
        return 10


def is_gb28181_source(source: Optional[str]) -> bool:
    return bool(source and str(source).strip().lower().startswith("gb28181://"))


def task_streams_prefer_tcp(device_streams: Dict[str, Any]) -> bool:
    """任务含 GB28181 或 HEVC 线索时建议 tcp 拉流。"""
    for info in (device_streams or {}).values():
        if info.get("is_gb28181"):
            return True
        url = (info.get("rtsp_url") or "").lower()
        if "hevc" in url or "h265" in url or "h.265" in url:
            return True
        orig = (info.get("original_source") or "")
        if is_gb28181_source(orig):
            return True
    return False


def apply_videocapture_stream_timeouts(
    cap: cv2.VideoCapture,
    url: str,
    *,
    open_timeout_msec: int,
    read_timeout_msec: int,
) -> None:
    """
    仅为 RTSP 设置 OpenCV 连接/读取超时。

    对 RTMP 设置 CAP_PROP_OPEN_TIMEOUT_MSEC 时，部分 OpenCV/FFmpeg 组合会把超时误解析为
    rtmp listen 模式（日志形如 tcp://host:port?listen&listen_timeout=...），导致无法拉流。
    """
    if not (url or "").startswith("rtsp://"):
        return
    try:
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, open_timeout_msec)
    except (AttributeError, cv2.error):
        pass
    try:
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, read_timeout_msec)
    except (AttributeError, cv2.error):
        pass


def open_network_videocapture(
    url: str,
    *,
    open_timeout_msec: int = 5000,
    read_timeout_msec: int = 2500,
) -> cv2.VideoCapture:
    """打开 RTSP/RTMP 网络流；超时属性仅作用于 RTSP。"""
    if url.startswith("rtmp://") or url.startswith("rtsp://"):
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    else:
        cap = cv2.VideoCapture(url)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except (AttributeError, cv2.error):
        pass
    apply_videocapture_stream_timeouts(
        cap, url,
        open_timeout_msec=open_timeout_msec,
        read_timeout_msec=read_timeout_msec,
    )
    return cap


def is_likely_rtsp_flat_corrupt_frame(
    frame,
    std_max: float = 4.0,
    mean_lo: float = 80.0,
    mean_hi: float = 180.0,
) -> bool:
    """判断整帧是否像解码失败后的典型「中灰塌缩」屏。"""
    if frame is None or getattr(frame, "size", 0) == 0:
        return True
    try:
        if len(frame.shape) == 2:
            gray = frame
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _mean, _std = cv2.meanStdDev(gray)
        m, s = float(_mean[0][0]), float(_std[0][0])
        return bool(mean_lo <= m <= mean_hi and s < std_max)
    except Exception:
        return False


def capture_rtsp_frame(
    source: str,
    *,
    max_attempts: int = 5,
    skip_gray: bool = True,
    std_max: float = 4.0,
    mean_lo: float = 80.0,
    mean_hi: float = 180.0,
):
    """从 RTSP 读取可用帧：减小缓冲并多次读取，跳过疑似灰屏/花屏帧。"""
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        cap.release()
        return False, None
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame = None
    for _ in range(max(1, max_attempts)):
        ret, candidate = cap.read()
        if not ret or candidate is None:
            continue
        if skip_gray and is_likely_rtsp_flat_corrupt_frame(
            candidate, std_max, mean_lo, mean_hi
        ):
            continue
        frame = candidate
        break
    cap.release()
    return frame is not None, frame
