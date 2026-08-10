"""
FFmpeg 硬件加速视频解码器 — RTSP/文件 → BGR24 → 帧队列 → 共享内存。

相对 OpenCV VideoCapture 的优势：
- 独立子进程解码，不阻塞推理线程
- 可选 CUDA/VAAPI/QSV 硬件解码
- 帧队列解耦解码与推理；共享内存供跨进程零拷贝读取
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional

import numpy as np

from app.utils.ffmpeg_compat import ffmpeg_rtsp_timeout_args

from .frame_queue import FrameQueue
from .shared_memory import FrameHeader, SharedMemoryManager, create_shared_memory

logger = logging.getLogger(__name__)


class DecoderError(Exception):
    pass


@dataclass
class DecoderConfig:
    rtsp_url: str = ""  # RTSP/RTMP 流地址
    video_file: str = ""
    width: int = 0  # 0 = 保持源流分辨率
    height: int = 0
    pixel_format: str = "bgr24"
    hwaccel: str = "auto"  # auto, cuda, vaapi, qsv, none
    rtsp_transport: str = "tcp"
    reconnect: bool = True
    reconnect_delay: float = 5.0
    read_buffer_size: int = 1024 * 1024
    frame_queue_size: int = 8
    shm_name: str = "yolo_detection_channel"
    enable_shared_memory: bool = True
    low_latency: bool = True
    realtime_pacing: bool = False  # 文件源按帧率限速；-re


def probe_stream_size(url: str, timeout: float = 10.0) -> Optional[tuple]:
    """ffprobe 探测视频流分辨率；失败返回 None。"""
    if not url or not shutil.which("ffprobe"):
        return None
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        url,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False,
        )
        if result.returncode != 0:
            return None
        parts = result.stdout.strip().split("x")
        if len(parts) != 2:
            return None
        w, h = int(parts[0]), int(parts[1])
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    return None


def detect_hwaccel(preferred: str = "auto") -> str:
    pref = (preferred or "auto").strip().lower()
    if pref not in ("auto", ""):
        return pref

    env = (os.getenv("AI_DECODE_HWACCEL") or "").strip().lower()
    if env:
        return env

    if shutil.which("nvidia-smi"):
        return "cuda"
    if os.path.exists("/dev/dri/renderD128"):
        return "vaapi"
    return "none"


def build_ffmpeg_decode_cmd(config: DecoderConfig) -> List[str]:
    hw = detect_hwaccel(config.hwaccel)
    cmd: List[str] = ["ffmpeg", "-hide_banner", "-loglevel", "warning"]

    if config.low_latency:
        cmd.extend(["-fflags", "+nobuffer+flush_packets+genpts", "-flags", "low_delay"])

    if config.video_file:
        if config.realtime_pacing:
            cmd.extend(["-re"])
        cmd.extend(["-i", config.video_file])
    else:
        stream_url = config.rtsp_url
        stream_lower = (stream_url or "").lower()
        if stream_lower.startswith("rtsp://"):
            transport = (config.rtsp_transport or "tcp").strip().lower()
            if transport not in ("tcp", "udp"):
                transport = "tcp"
            cmd.extend(["-rtsp_transport", transport])
            cmd.extend(ffmpeg_rtsp_timeout_args(10_000_000, 10_000_000))
            cmd.extend([
                "-analyzeduration", "1000000",
                "-probesize", "1000000",
            ])
        elif stream_lower.startswith("rtmp://"):
            cmd.extend([
                "-analyzeduration", "1000000",
                "-probesize", "1000000",
            ])

        if hw == "cuda":
            cmd.extend([
                "-hwaccel", "cuda",
                "-hwaccel_output_format", "cuda",
                "-extra_hw_frames", "8",
            ])
        elif hw == "vaapi":
            render = os.getenv("AI_VAAPI_DEVICE", "/dev/dri/renderD128")
            cmd.extend([
                "-hwaccel", "vaapi",
                "-hwaccel_device", render,
                "-hwaccel_output_format", "vaapi",
            ])
        elif hw == "qsv":
            cmd.extend(["-hwaccel", "qsv", "-hwaccel_output_format", "qsv"])

        cmd.extend(["-i", stream_url])

    vf_parts: List[str] = []
    if hw == "cuda":
        vf_parts.append("hwdownload,format=nv12")
    elif hw in ("vaapi", "qsv"):
        vf_parts.append("hwdownload,format=nv12")

    if config.width > 0 and config.height > 0:
        vf_parts.append(f"scale={config.width}:{config.height}")
    if config.pixel_format == "bgr24":
        vf_parts.append("format=bgr24")
    elif config.pixel_format == "yuv420p":
        vf_parts.append("format=yuv420p")

    if vf_parts:
        cmd.extend(["-an", "-vf", ",".join(vf_parts)])
    else:
        cmd.extend(["-an", "-pix_fmt", "bgr24"])
    cmd.extend(["-f", "rawvideo", "pipe:1"])
    return cmd


class VideoDecoder:
    """
    解码线程：FFmpeg stdout → numpy 帧 → FrameQueue → SharedMemory。

    推理侧从 frame_queue 或 shared_memory 取帧；队列持续有剩余说明解码快于推理。
    """

    def __init__(self, config: DecoderConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.shared_memory: Optional[SharedMemoryManager] = None
        self.frame_queue: Optional[FrameQueue] = None
        self.is_running = False
        self.read_failed = False
        self.sequence_num = 0
        self._thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._stderr_lines: List[str] = []
        self._stderr_lock = threading.Lock()
        self._width = max(0, int(config.width))
        self._height = max(0, int(config.height))
        self.ffmpeg_args = build_ffmpeg_decode_cmd(config)
        self.stats: Dict[str, Any] = {
            "frames_decoded": 0,
            "decode_errors": 0,
            "reconnect_count": 0,
            "hwaccel_failures": 0,
            "start_time": None,
            "last_frame_time": None,
            "hwaccel": detect_hwaccel(config.hwaccel),
        }

    @property
    def frame_width(self) -> int:
        return self._width

    @property
    def frame_height(self) -> int:
        return self._height

    @property
    def frame_byte_size(self) -> int:
        w, h = self._width, self._height
        if w <= 0 or h <= 0:
            raise DecoderError("帧尺寸未确定，请先调用 start()")
        if self.config.pixel_format == "bgr24":
            return w * h * 3
        if self.config.pixel_format in ("yuv420p", "nv12"):
            return w * h + (w * h) // 2
        raise DecoderError(f"unsupported pixel_format: {self.config.pixel_format}")

    def isOpened(self) -> bool:
        if not self.is_running:
            return False
        if self.read_failed:
            return False
        # reconnect 模式下由解码线程负责拉起 FFmpeg，避免瞬时退出触发上层整路重连
        if self.config.reconnect:
            return True
        if self.process is not None and self.process.poll() is not None:
            return False
        return True

    def start(self) -> bool:
        if self.is_running:
            return True
        if not shutil.which("ffmpeg"):
            raise DecoderError("未找到 ffmpeg，请先安装")

        if self._width <= 0 or self._height <= 0:
            source = self.config.rtsp_url or self.config.video_file
            probed = probe_stream_size(source) if source else None
            if probed:
                self._width, self._height = probed
            else:
                raise DecoderError(f"无法探测流分辨率: {source}")

        self.read_failed = False
        if self.config.enable_shared_memory:
            self.shared_memory = create_shared_memory(
                name=self.config.shm_name,
                width=self._width,
                height=self._height,
                pixel_format=self.config.pixel_format,
            )
        self.frame_queue = FrameQueue(max_size=self.config.frame_queue_size)

        if not self._start_ffmpeg():
            return False

        self.is_running = True
        self.stats["start_time"] = time.time()
        self._thread = threading.Thread(target=self._decode_loop, name="video-decode", daemon=True)
        self._thread.start()
        logger.info(
            "VideoDecoder 已启动 %dx%d hwaccel=%s queue=%s shm=%s",
            self._width,
            self._height,
            self.stats["hwaccel"],
            self.config.frame_queue_size,
            self.config.shm_name if self.config.enable_shared_memory else "off",
        )
        return True

    def stop(self) -> None:
        self.is_running = False
        self._terminate_ffmpeg()
        self._join_stderr_thread()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

        if self.frame_queue:
            self.frame_queue.clear()
            self.frame_queue = None
        if self.shared_memory:
            self.shared_memory.close()
            self.shared_memory = None
        logger.info("VideoDecoder 已停止")

    def get_frame(self, *, latest: bool = False) -> Optional[tuple]:
        """推理侧取帧：(header, bgr_frame)。"""
        if not self.frame_queue:
            return None
        qf = self.frame_queue.dequeue_latest() if latest else self.frame_queue.dequeue()
        if qf is None:
            return None
        return qf.header, qf.frame

    def read_from_shm(self) -> Optional[tuple]:
        if not self.shared_memory or not self.shared_memory.is_open:
            return None
        header, frame = self.shared_memory.read_frame_bgr24()
        return header, frame

    def get_stats(self) -> Dict[str, Any]:
        out = dict(self.stats)
        elapsed = time.time() - (out["start_time"] or time.time())
        out["elapsed_seconds"] = max(0.0, elapsed)
        out["fps"] = out["frames_decoded"] / elapsed if elapsed > 0 else 0.0
        if self.frame_queue:
            qs = self.frame_queue.get_stats()
            out["frame_queue"] = {
                "size": qs.current_size,
                "max_size": qs.max_capacity,
                "total_frames": qs.total_frames,
                "dropped_frames": qs.dropped_frames,
                "avg_delay_ms": qs.avg_queue_delay_ms,
            }
        return out

    def _start_ffmpeg(self) -> bool:
        try:
            self._join_stderr_thread()
            with self._stderr_lock:
                self._stderr_lines.clear()
            self.process = subprocess.Popen(
                self.ffmpeg_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=self.config.read_buffer_size,
            )
            self._start_stderr_reader()
            time.sleep(0.3)
            if self.process.poll() is not None:
                err = self._tail_stderr(20)
                logger.error(
                    "FFmpeg 启动失败 rc=%s err=%s",
                    self.process.returncode,
                    err[:500],
                )
                self._terminate_ffmpeg()
                return False
            return True
        except Exception as exc:
            raise DecoderError(f"启动 FFmpeg 失败: {exc}") from exc

    def _start_stderr_reader(self) -> None:
        stderr = self.process.stderr if self.process else None
        if stderr is None:
            return

        def _read_loop() -> None:
            try:
                for line in iter(stderr.readline, b""):
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace").strip()
                    if not text:
                        continue
                    with self._stderr_lock:
                        self._stderr_lines.append(text)
                        if len(self._stderr_lines) > 100:
                            self._stderr_lines.pop(0)
            except Exception:
                pass
            finally:
                try:
                    stderr.close()
                except Exception:
                    pass

        self._stderr_thread = threading.Thread(
            target=_read_loop, name="ffmpeg-stderr", daemon=True,
        )
        self._stderr_thread.start()

    def _join_stderr_thread(self) -> None:
        thread = self._stderr_thread
        self._stderr_thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

    def _tail_stderr(self, max_lines: int = 10) -> str:
        with self._stderr_lock:
            lines = self._stderr_lines[-max(1, max_lines):]
        return "\n".join(lines)

    def _terminate_ffmpeg(self) -> None:
        if not self.process:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                self.process.kill()
            except Exception:
                pass
        except Exception:
            pass
        self.process = None
        self._join_stderr_thread()

    def _maybe_downgrade_hwaccel(self) -> bool:
        hw = (self.stats.get("hwaccel") or "none").strip().lower()
        if hw in ("", "none"):
            return False
        failures = int(self.stats.get("hwaccel_failures") or 0) + 1
        self.stats["hwaccel_failures"] = failures
        if failures < 3:
            return False
        logger.warning(
            "FFmpeg 硬件解码连续失败 %d 次，回退软件解码 hwaccel=none",
            failures,
        )
        self.config = replace(self.config, hwaccel="none")
        self.stats["hwaccel"] = "none"
        self.stats["hwaccel_failures"] = 0
        self.ffmpeg_args = build_ffmpeg_decode_cmd(self.config)
        return True

    def _restart_ffmpeg(self) -> bool:
        self._terminate_ffmpeg()
        self.stats["reconnect_count"] += 1
        if self._maybe_downgrade_hwaccel():
            logger.info("已切换 FFmpeg 软件解码，重试拉流")
        return self._start_ffmpeg()

    def _decode_loop(self) -> None:
        frame_size = self.frame_byte_size
        buffer = bytearray()
        stdout = self.process.stdout if self.process else None

        while self.is_running:
            try:
                if not self.process or self.process.poll() is not None:
                    rc = self.process.returncode if self.process else -1
                    err = self._tail_stderr(12)
                    if err:
                        logger.warning("FFmpeg 退出 rc=%s err=%s", rc, err[:800])
                    else:
                        logger.warning("FFmpeg 退出 rc=%s", rc)
                    self.read_failed = not self.config.reconnect
                    if self.config.reconnect:
                        time.sleep(self.config.reconnect_delay)
                        if not self._restart_ffmpeg():
                            continue
                        stdout = self.process.stdout if self.process else None
                        buffer.clear()
                        continue
                    break

                if stdout is None:
                    time.sleep(0.05)
                    continue

                chunk = stdout.read(frame_size)
                if not chunk:
                    time.sleep(0.01)
                    continue

                buffer.extend(chunk)
                while len(buffer) >= frame_size:
                    frame_bytes = bytes(buffer[:frame_size])
                    del buffer[:frame_size]
                    self._on_frame_decoded(frame_bytes)

            except Exception as exc:
                self.stats["decode_errors"] += 1
                logger.error("解码循环异常: %s", exc)
                if self.config.reconnect:
                    time.sleep(self.config.reconnect_delay)
                    if self._restart_ffmpeg():
                        stdout = self.process.stdout if self.process else None
                        buffer.clear()
                else:
                    break

    def _on_frame_decoded(self, frame_bytes: bytes) -> None:
        w, h = self._width, self._height
        if self.config.pixel_format == "bgr24":
            frame = np.frombuffer(frame_bytes, dtype=np.uint8).reshape((h, w, 3))
        else:
            raise DecoderError("当前仅 bgr24 入队路径已实现")

        now_ns = time.time_ns()
        header = FrameHeader(
            sequence_num=self.sequence_num,
            timestamp_ns=now_ns,
            write_time_ns=now_ns,
            width=w,
            height=h,
            pixel_format=self.config.pixel_format,
        )
        if self.frame_queue:
            self.frame_queue.enqueue(header, frame)
        if self.shared_memory:
            try:
                self.shared_memory.write_complete_frame_bgr24(header, frame)
            except Exception as exc:
                logger.debug("写入共享内存失败: %s", exc)
        self.sequence_num += 1
        self.stats["frames_decoded"] += 1
        self.stats["last_frame_time"] = time.time()


def create_decoder(
    rtsp_url: str,
    width: int = 640,
    height: int = 640,
    *,
    hwaccel: str = "auto",
    frame_queue_size: int = 8,
    shm_name: str = "yolo_detection_channel",
) -> VideoDecoder:
    config = DecoderConfig(
        rtsp_url=rtsp_url,
        width=width,
        height=height,
        hwaccel=hwaccel,
        frame_queue_size=frame_queue_size,
        shm_name=shm_name,
    )
    return VideoDecoder(config)
