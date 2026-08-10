"""
解码帧共享内存 — 解码进程与推理进程之间的零拷贝通道。

布局（BGR24 示例，640×640）：
  0..27   FrameHeader（sequence_num, timestamp_ns, write_time_ns, width, height）
  28..    帧像素数据
"""
from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from multiprocessing import shared_memory
from typing import Optional, Tuple

import numpy as np

HEADER_FMT = "<IQQII"
HEADER_SIZE = struct.calcsize(HEADER_FMT)


@dataclass
class FrameHeader:
    sequence_num: int
    timestamp_ns: int
    write_time_ns: int
    width: int = 640
    height: int = 640
    pixel_format: str = "bgr24"

    @property
    def timestamp_ms(self) -> float:
        return self.timestamp_ns / 1_000_000

    @property
    def write_time_ms(self) -> float:
        return self.write_time_ns / 1_000_000


class SharedMemoryError(Exception):
    pass


class MemoryNotCreatedError(SharedMemoryError):
    pass


class VersionMismatchError(SharedMemoryError):
    pass


def frame_data_size(width: int, height: int, pixel_format: str) -> int:
    pf = (pixel_format or "bgr24").lower()
    if pf == "bgr24":
        return width * height * 3
    if pf == "yuv420p":
        return width * height + (width * height) // 2
    if pf == "nv12":
        return width * height + (width * height) // 2
    raise ValueError(f"unsupported pixel_format: {pixel_format}")


class SharedMemoryManager:
    """基于 multiprocessing.shared_memory 的帧共享内存（Linux 友好）。"""

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        pixel_format: str = "bgr24",
        *,
        create: bool = False,
    ):
        self.name = name
        self.width = width
        self.height = height
        self.pixel_format = (pixel_format or "bgr24").lower()
        self.frame_bytes = frame_data_size(width, height, self.pixel_format)
        self.total_size = HEADER_SIZE + self.frame_bytes
        self.create = create
        self._shm: Optional[shared_memory.SharedMemory] = None
        self.is_open = False

        if create:
            self._create()
        else:
            self._open()

    def _create(self) -> None:
        try:
            self._shm = shared_memory.SharedMemory(
                name=self.name, create=True, size=self.total_size
            )
            self.is_open = True
        except FileExistsError:
            self._open()
        except Exception as exc:
            raise SharedMemoryError(f"创建共享内存失败: {exc}") from exc

    def _open(self) -> None:
        try:
            self._shm = shared_memory.SharedMemory(name=self.name, create=False)
            if self._shm.size < self.total_size:
                raise SharedMemoryError(
                    f"共享内存大小不足: {self._shm.size} < {self.total_size}"
                )
            self.is_open = True
        except FileNotFoundError as exc:
            raise MemoryNotCreatedError(f"共享内存未创建: {self.name}") from exc
        except Exception as exc:
            raise SharedMemoryError(f"打开共享内存失败: {exc}") from exc

    def close(self) -> None:
        if not self._shm:
            return
        try:
            self._shm.close()
            if self.create:
                try:
                    self._shm.unlink()
                except FileNotFoundError:
                    pass
        finally:
            self._shm = None
            self.is_open = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def buf(self) -> memoryview:
        if not self._shm or not self.is_open:
            raise MemoryNotCreatedError("共享内存未打开")
        return self._shm.buf

    def write_header(self, header: FrameHeader) -> None:
        packed = struct.pack(
            HEADER_FMT,
            header.sequence_num,
            header.timestamp_ns,
            header.write_time_ns,
            header.width,
            header.height,
        )
        self.buf[:HEADER_SIZE] = packed

    def read_header(self) -> FrameHeader:
        sequence_num, timestamp_ns, write_time_ns, width, height = struct.unpack(
            HEADER_FMT, bytes(self.buf[:HEADER_SIZE])
        )
        return FrameHeader(
            sequence_num=sequence_num,
            timestamp_ns=timestamp_ns,
            write_time_ns=write_time_ns,
            width=width,
            height=height,
            pixel_format=self.pixel_format,
        )

    def write_frame_bgr24(self, frame: np.ndarray) -> None:
        if frame.shape[:2] != (self.height, self.width):
            raise ValueError(f"帧尺寸不匹配: {frame.shape} vs ({self.height}, {self.width})")
        data = np.ascontiguousarray(frame, dtype=np.uint8)
        offset = HEADER_SIZE
        self.buf[offset : offset + self.frame_bytes] = data.reshape(-1)

    def write_complete_frame_bgr24(self, header: FrameHeader, frame: np.ndarray) -> None:
        self.write_frame_bgr24(frame)
        header.write_time_ns = time.time_ns()
        self.write_header(header)

    def read_frame_bgr24(self, max_retries: int = 3) -> Tuple[FrameHeader, np.ndarray]:
        for attempt in range(max_retries):
            header1 = self.read_header()
            offset = HEADER_SIZE
            raw = np.frombuffer(
                self.buf[offset : offset + self.frame_bytes], dtype=np.uint8
            )
            frame = raw.reshape((self.height, self.width, 3)).copy()
            header2 = self.read_header()
            if header1.sequence_num == header2.sequence_num:
                return header1, frame
            if attempt == max_retries - 1:
                raise VersionMismatchError("读取帧时序列号不一致（可能读到半帧）")
        raise SharedMemoryError("读取帧失败")


def create_shared_memory(
    name: str = "yolo_detection_channel",
    width: int = 640,
    height: int = 640,
    pixel_format: str = "bgr24",
) -> SharedMemoryManager:
    return SharedMemoryManager(
        name=name, width=width, height=height, pixel_format=pixel_format, create=True
    )


def open_shared_memory(
    name: str = "yolo_detection_channel",
    width: int = 640,
    height: int = 640,
    pixel_format: str = "bgr24",
) -> SharedMemoryManager:
    return SharedMemoryManager(
        name=name, width=width, height=height, pixel_format=pixel_format, create=False
    )
