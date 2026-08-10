"""FFmpeg 硬件解码 + 帧队列 + 共享内存（解码/推理解耦）。"""
from .frame_queue import FrameQueue, FrameQueueStats, QueuedFrame
from .shared_memory import (
    FrameHeader,
    MemoryNotCreatedError,
    SharedMemoryError,
    SharedMemoryManager,
    VersionMismatchError,
    create_shared_memory,
    open_shared_memory,
)
from .video_decoder import DecoderConfig, VideoDecoder, create_decoder, detect_hwaccel, probe_stream_size
from .stream_adapter import (
    FfmpegVideoStream,
    ffmpeg_decode_enabled,
    is_async_stream,
    open_device_stream,
    stream_mode_label,
)

__all__ = [
    "DecoderConfig",
    "FfmpegVideoStream",
    "FrameHeader",
    "FrameQueue",
    "FrameQueueStats",
    "MemoryNotCreatedError",
    "QueuedFrame",
    "SharedMemoryError",
    "SharedMemoryManager",
    "VersionMismatchError",
    "VideoDecoder",
    "create_decoder",
    "create_shared_memory",
    "detect_hwaccel",
    "ffmpeg_decode_enabled",
    "is_async_stream",
    "open_device_stream",
    "open_shared_memory",
    "probe_stream_size",
    "stream_mode_label",
]
