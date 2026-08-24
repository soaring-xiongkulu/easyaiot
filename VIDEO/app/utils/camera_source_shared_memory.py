"""摄像头共享帧环形缓冲区。"""
from __future__ import annotations

import errno
import hashlib
import mmap
import os
import secrets
import shutil
import struct
import tempfile
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


_MAGIC = b'EAIOTCAM'
_VERSION = 1
_HEADER_SIZE = 256
_HEADER_STRUCT = struct.Struct('<8sIIIIIIQQdII')
_SLOT_META_STRUCT = struct.Struct('<QQQQ')
_SLOT_META_SIZE = _SLOT_META_STRUCT.size
_ALLOCATION_LOCK = threading.Lock()


class SharedFrameCapacityError(ValueError):
    """帧大小超过当前共享内存槽位容量。"""


@dataclass(frozen=True)
class SharedFramePacket:
    """从共享帧环读取出的完整帧。"""

    sequence: int
    timestamp: float
    shape: Tuple[int, int, int]
    data: bytes


def _fallback_memory_root() -> str:
    """返回磁盘映射文件的受控回退目录。"""
    return os.path.join(tempfile.gettempdir(), 'easyaiot_camera_sources', 'shm')


def _shared_memory_root(required_bytes: int = 0) -> str:
    """优先使用 Linux tmpfs，容量不足时回退到系统临时目录。"""
    configured = (os.getenv('CAMERA_SOURCE_SHM_DIR') or '').strip()
    if configured:
        root = configured
    elif os.path.isdir('/dev/shm') and os.access('/dev/shm', os.W_OK):
        required_capacity = max(0, int(required_bytes))
        reserve_bytes = max(
            8 * 1024 * 1024,
            int(os.getenv('CAMERA_SOURCE_SHM_RESERVE_BYTES', str(8 * 1024 * 1024))),
        )
        try:
            available_bytes = shutil.disk_usage('/dev/shm').free
        except OSError:
            available_bytes = 0
        root = (
            '/dev/shm'
            if available_bytes >= required_capacity + reserve_bytes
            else _fallback_memory_root()
        )
    else:
        root = _fallback_memory_root()
    os.makedirs(root, mode=0o700, exist_ok=True)
    return root


def _build_memory_name(device_id: str) -> str:
    digest = hashlib.sha1(str(device_id).encode('utf-8')).hexdigest()[:16]
    return f'easyaiot_cam_{digest}_{os.getpid()}_{secrets.token_hex(4)}'


def cleanup_stale_shared_frame_files(min_age_seconds: float = 60.0) -> int:
    """清理已退出源管理进程遗留的共享帧文件。"""
    removed_count = 0
    now = time.time()
    configured = (os.getenv('CAMERA_SOURCE_SHM_DIR') or '').strip()
    candidate_roots = [configured] if configured else ['/dev/shm', _fallback_memory_root()]
    for root in dict.fromkeys(candidate_roots):
        if not root or not os.path.isdir(root):
            continue
        for file_name in os.listdir(root):
            if not file_name.startswith('easyaiot_cam_'):
                continue
            file_path = os.path.join(root, file_name)
            try:
                if now - os.path.getmtime(file_path) < max(0.0, float(min_age_seconds)):
                    continue
                owner_pid = int(file_name.rsplit('_', 2)[1])
                try:
                    os.kill(owner_pid, 0)
                    continue
                except ProcessLookupError:
                    pass
                except PermissionError:
                    # 无权探测并不代表进程不存在，不能删除可能仍在使用的映射文件。
                    continue
                except OSError:
                    continue
                os.unlink(file_path)
                removed_count += 1
            except (FileNotFoundError, PermissionError, ValueError, OSError):
                continue
    return removed_count


class SharedFrameRing:
    """单写多读的固定槽位共享帧环。"""

    def __init__(
            self,
            *,
            device_id: str,
            name: str,
            path: str,
            file_handle,
            mapping: mmap.mmap,
            slot_size: int,
            slot_count: int,
    ):
        self.device_id = str(device_id)
        self.name = name
        self.path = path
        self._file_handle = file_handle
        self._mapping = mapping
        self.slot_size = int(slot_size)
        self.slot_count = int(slot_count)
        self._sequence = 0
        self._write_lock = threading.Lock()
        self._closed = False
        self._width = 0
        self._height = 0
        self._channels = 0
        self._latest_timestamp = 0.0
        self._write_header(latest_index=0)

    @classmethod
    def create(cls, device_id: str, *, slot_size: int, slot_count: int = 2):
        """创建一个新的共享帧环。"""
        normalized_slot_size = max(1, int(slot_size))
        normalized_slot_count = max(2, int(slot_count))
        name = _build_memory_name(device_id)
        total_size = _HEADER_SIZE + normalized_slot_count * (_SLOT_META_SIZE + normalized_slot_size)
        configured_root = (os.getenv('CAMERA_SOURCE_SHM_DIR') or '').strip()

        with _ALLOCATION_LOCK:
            primary_root = _shared_memory_root(required_bytes=total_size)
            candidate_roots = [primary_root]
            fallback_root = _fallback_memory_root()
            if not configured_root and primary_root == '/dev/shm' and fallback_root != primary_root:
                candidate_roots.append(fallback_root)

            file_handle = None
            mapping = None
            path = ''
            allocation_error = None
            for root in candidate_roots:
                path = os.path.join(root, name)
                try:
                    file_handle = open(path, 'w+b', buffering=0)
                    os.chmod(path, 0o600)
                    file_handle.truncate(total_size)
                    # ftruncate 只改变长度，tmpfs/磁盘空间可能尚未实际预留。
                    if hasattr(os, 'posix_fallocate'):
                        os.posix_fallocate(file_handle.fileno(), 0, total_size)
                    mapping = mmap.mmap(
                        file_handle.fileno(),
                        total_size,
                        access=mmap.ACCESS_WRITE,
                    )
                    allocation_error = None
                    break
                except (OSError, ValueError) as exc:
                    allocation_error = exc
                    if mapping is not None:
                        mapping.close()
                        mapping = None
                    if file_handle is not None:
                        file_handle.close()
                        file_handle = None
                    try:
                        os.unlink(path)
                    except FileNotFoundError:
                        pass
                    if getattr(exc, 'errno', None) not in (errno.ENOSPC, errno.EDQUOT):
                        break

            if allocation_error is not None or file_handle is None or mapping is None:
                raise SharedFrameCapacityError(
                    f'无法为设备 {device_id} 预留 {total_size} 字节共享帧空间: '
                    f'{allocation_error}'
                )
        return cls(
            device_id=device_id,
            name=name,
            path=path,
            file_handle=file_handle,
            mapping=mapping,
            slot_size=normalized_slot_size,
            slot_count=normalized_slot_count,
        )

    def _write_header(self, *, latest_index: int) -> None:
        packed = _HEADER_STRUCT.pack(
            _MAGIC,
            _VERSION,
            self.slot_count,
            self.slot_size,
            self._width,
            self._height,
            self._channels,
            self._sequence,
            int(latest_index),
            self._latest_timestamp,
            os.getpid(),
            1,
        )
        self._mapping[0:_HEADER_STRUCT.size] = packed

    def _slot_offset(self, index: int) -> int:
        return _HEADER_SIZE + index * (_SLOT_META_SIZE + self.slot_size)

    def write_frame(self, frame, *, timestamp: Optional[float] = None) -> int:
        """写入完整帧并返回新序列号。"""
        if self._closed:
            raise RuntimeError('共享帧环已关闭')
        frame_size = int(frame.nbytes)
        if frame_size > self.slot_size:
            raise SharedFrameCapacityError(
                f'帧大小 {frame_size} 超过共享槽位容量 {self.slot_size}'
            )
        height, width = int(frame.shape[0]), int(frame.shape[1])
        channels = int(frame.shape[2]) if len(frame.shape) > 2 else 1
        raw_bytes = frame.tobytes()
        if len(raw_bytes) != frame_size:
            raise ValueError('帧字节数与 nbytes 不一致')
        frame_timestamp = float(timestamp if timestamp is not None else time.time())

        with self._write_lock:
            sequence = self._sequence + 1
            index = sequence % self.slot_count
            slot_offset = self._slot_offset(index)
            data_offset = slot_offset + _SLOT_META_SIZE
            timestamp_ns = int(frame_timestamp * 1_000_000_000)

            # 先将结束序列清零，再写帧，最后一次性发布完整元数据。
            self._mapping[slot_offset:slot_offset + _SLOT_META_SIZE] = _SLOT_META_STRUCT.pack(
                sequence, timestamp_ns, frame_size, 0
            )
            self._mapping[data_offset:data_offset + frame_size] = raw_bytes
            self._mapping[slot_offset:slot_offset + _SLOT_META_SIZE] = _SLOT_META_STRUCT.pack(
                sequence, timestamp_ns, frame_size, sequence
            )

            self._sequence = sequence
            self._width = width
            self._height = height
            self._channels = channels
            self._latest_timestamp = frame_timestamp
            self._write_header(latest_index=index)
            return sequence

    def descriptor(self) -> Dict:
        """返回订阅者附加共享帧环所需的描述信息。"""
        return {
            'source_id': f'source_{self.device_id}',
            'device_id': self.device_id,
            'shared_memory_name': self.name,
            'shared_memory_path': self.path,
            'frame_format': 'bgr24',
            'width': self._width,
            'height': self._height,
            'channels': self._channels,
            'slot_size': self.slot_size,
            'slot_count': self.slot_count,
            'latest_sequence': self._sequence,
            'latest_timestamp': self._latest_timestamp,
        }

    def close(self, *, unlink: bool = False) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._mapping.close()
        finally:
            self._file_handle.close()
        if unlink:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass


class SharedFrameRingReader:
    """共享帧环只读订阅者。"""

    def __init__(self, descriptor: Dict, file_handle, mapping: mmap.mmap):
        self.descriptor = dict(descriptor)
        self._file_handle = file_handle
        self._mapping = mapping
        self.slot_size = int(descriptor['slot_size'])
        self.slot_count = int(descriptor['slot_count'])
        self._closed = False

    @classmethod
    def attach(cls, descriptor: Dict):
        path = descriptor.get('shared_memory_path')
        if not path:
            raise ValueError('共享帧描述缺少 shared_memory_path')
        file_handle = open(path, 'rb', buffering=0)
        mapping = None
        try:
            mapping = mmap.mmap(file_handle.fileno(), 0, access=mmap.ACCESS_READ)
            reader = cls(descriptor, file_handle, mapping)
            reader._read_header()
            return reader
        except Exception:
            if mapping is not None:
                mapping.close()
            file_handle.close()
            raise

    def _read_header(self):
        values = _HEADER_STRUCT.unpack(self._mapping[0:_HEADER_STRUCT.size])
        if values[0] != _MAGIC or values[1] != _VERSION:
            raise ValueError('共享帧头格式不兼容')
        return values

    def _slot_offset(self, index: int) -> int:
        return _HEADER_SIZE + index * (_SLOT_META_SIZE + self.slot_size)

    def read_latest(self, *, after_sequence: int = 0) -> Optional[SharedFramePacket]:
        """读取最新完整帧，没有更新或检测到撕裂时返回空。"""
        if self._closed:
            return None
        header = self._read_header()
        width, height, channels = int(header[4]), int(header[5]), int(header[6])
        latest_sequence, latest_index = int(header[7]), int(header[8])
        if latest_sequence <= int(after_sequence) or latest_sequence <= 0:
            return None

        slot_offset = self._slot_offset(latest_index)
        metadata_before = _SLOT_META_STRUCT.unpack(
            self._mapping[slot_offset:slot_offset + _SLOT_META_SIZE]
        )
        sequence_start, timestamp_ns, frame_size, sequence_end = metadata_before
        if sequence_start != latest_sequence or sequence_end != latest_sequence:
            return None
        if frame_size <= 0 or frame_size > self.slot_size:
            return None
        expected_size = width * height * channels
        if expected_size != frame_size:
            return None

        data_offset = slot_offset + _SLOT_META_SIZE
        frame_data = bytes(self._mapping[data_offset:data_offset + frame_size])
        metadata_after = _SLOT_META_STRUCT.unpack(
            self._mapping[slot_offset:slot_offset + _SLOT_META_SIZE]
        )
        if metadata_before != metadata_after or metadata_after[0] != metadata_after[3]:
            return None
        return SharedFramePacket(
            sequence=int(latest_sequence),
            timestamp=float(timestamp_ns) / 1_000_000_000,
            shape=(height, width, channels),
            data=frame_data,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._mapping.close()
        finally:
            self._file_handle.close()
