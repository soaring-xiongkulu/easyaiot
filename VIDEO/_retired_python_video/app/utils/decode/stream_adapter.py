"""
拉流适配层 — 三个算法/推流服务共用。

AI_DECODE_USE_FFMPEG=1（默认）时 RTSP/RTMP 走 FFmpeg 硬件解码 + 帧队列；
失败或未启用时回退 OpenCV + AsyncVideoStream。
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Optional, Union

import cv2

from app.utils.async_video_stream import AsyncVideoStream, async_rtsp_queue_max, async_rtsp_read_enabled
from app.utils.rtsp_stream_utils import effective_rtsp_transport, open_network_videocapture

from .video_decoder import DecoderConfig, VideoDecoder, probe_stream_size

logger = logging.getLogger(__name__)

StreamHandle = Union[cv2.VideoCapture, AsyncVideoStream, "FfmpegVideoStream"]


def ffmpeg_decode_enabled() -> bool:
    return (os.getenv("AI_DECODE_USE_FFMPEG", "1") or "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def decode_frame_queue_size(queue_max_override: Optional[int] = None) -> int:
    if queue_max_override is not None:
        return max(1, int(queue_max_override))
    try:
        return max(1, min(int((os.getenv("AI_DECODE_FRAME_QUEUE_SIZE", "8") or "8").strip()), 600))
    except ValueError:
        return 8


def _resolve_queue_max(queue_max_override: Optional[int]) -> int:
    if queue_max_override is not None:
        return max(1, int(queue_max_override))
    if async_rtsp_read_enabled():
        return async_rtsp_queue_max()
    return 1


def _shm_name(task_id: Optional[str], device_id: str) -> str:
    raw = f"{task_id or 'svc'}_{device_id}"
    return "d_" + hashlib.md5(raw.encode()).hexdigest()[:20]


class FfmpegVideoStream:
    """兼容 VideoCapture / AsyncVideoStream 的 FFmpeg 解码包装。"""

    def __init__(self, decoder: VideoDecoder, *, queue_max: int = 1):
        self._decoder = decoder
        self.queue_max = max(1, int(queue_max))
        self.read_failed = False

    def isOpened(self) -> bool:
        return self._decoder.isOpened()

    def start(self) -> "FfmpegVideoStream":
        return self

    def read(self):
        if self._decoder.read_failed or not self._decoder.is_running:
            self.read_failed = True
            return False, None
        item = self._decoder.get_frame(latest=(self.queue_max <= 1))
        if item is None:
            if self._decoder.read_failed:
                self.read_failed = True
            return False, None
        _header, frame = item
        return True, frame

    def get(self, prop):
        if prop == cv2.CAP_PROP_FPS:
            return 0.0
        return 0.0

    def release(self) -> None:
        self._decoder.stop()


def is_async_stream(cap) -> bool:
    return isinstance(cap, (AsyncVideoStream, FfmpegVideoStream))


def stream_mode_label(cap) -> str:
    if isinstance(cap, FfmpegVideoStream):
        fifo = cap.queue_max
        return (
            f"FFmpeg 硬件解码（AI_DECODE_USE_FFMPEG），FIFO {fifo} 帧"
            if fifo > 1
            else "FFmpeg 硬件解码（AI_DECODE_USE_FFMPEG），仅保留最新帧"
        )
    if isinstance(cap, AsyncVideoStream):
        fifo = getattr(cap, "queue_max", 1)
        return (
            f"OpenCV 异步拉流，FIFO {fifo} 帧（AI_RTSP_ASYNC_QUEUE_MAX）"
            if fifo > 1
            else "OpenCV 异步拉流，仅保留最新帧（AI_RTSP_ASYNC_READ）"
        )
    return "OpenCV 同步拉流"


def _open_opencv_stream(
    url: str,
    *,
    open_timeout_msec: int,
    read_timeout_msec: int,
    queue_max_override: Optional[int],
) -> StreamHandle:
    cap = open_network_videocapture(
        url,
        open_timeout_msec=open_timeout_msec,
        read_timeout_msec=read_timeout_msec,
    )
    url_lower = (url or "").lower()
    if async_rtsp_read_enabled() and (
        url_lower.startswith("rtsp://") or url_lower.startswith("rtmp://")
    ):
        qm = _resolve_queue_max(queue_max_override)
        cap = AsyncVideoStream(cap, queue_max=qm).start()
    return cap


def _open_ffmpeg_stream(
    url: str,
    device_id: str,
    *,
    task_id: Optional[str],
    queue_max_override: Optional[int],
) -> Optional[FfmpegVideoStream]:
    queue_max = decode_frame_queue_size(_resolve_queue_max(queue_max_override))
    config = DecoderConfig(
        rtsp_url=url,
        width=0,
        height=0,
        hwaccel="auto",
        rtsp_transport=effective_rtsp_transport(url),
        frame_queue_size=queue_max,
        shm_name=_shm_name(task_id, device_id),
        enable_shared_memory=False,
        reconnect=True,
    )
    decoder = VideoDecoder(config)
    try:
        if not decoder.start():
            decoder.stop()
            return None
    except Exception as exc:
        logger.warning("设备 %s FFmpeg 解码启动失败: %s", device_id, exc)
        try:
            decoder.stop()
        except Exception:
            pass
        return None
    return FfmpegVideoStream(decoder, queue_max=queue_max).start()


def open_device_stream(
    url: str,
    device_id: str,
    *,
    task_id: Optional[str] = None,
    open_timeout_msec: int = 5000,
    read_timeout_msec: int = 2500,
    queue_max_override: Optional[int] = None,
) -> StreamHandle:
    """
    打开网络流。优先 FFmpeg 解码（可硬件加速 + 帧队列），失败回退 OpenCV。
    """
    url_lower = (url or "").lower()
    is_network = url_lower.startswith("rtsp://") or url_lower.startswith("rtmp://")

    if ffmpeg_decode_enabled() and is_network:
        ff = _open_ffmpeg_stream(
            url, device_id, task_id=task_id, queue_max_override=queue_max_override,
        )
        if ff is not None and ff.isOpened():
            return ff
        logger.warning("设备 %s FFmpeg 解码不可用，回退 OpenCV 拉流", device_id)

    return _open_opencv_stream(
        url,
        open_timeout_msec=open_timeout_msec,
        read_timeout_msec=read_timeout_msec,
        queue_max_override=queue_max_override,
    )
