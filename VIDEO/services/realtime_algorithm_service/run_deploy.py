#!/usr/bin/env python3
"""
统一的实时算法任务服务程序
整合缓流器、抽帧器、推帧器功能，支持追踪和告警
参照test_services_pipeline.py和test_services_pipeline_tracking.py

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import time
import threading
import logging
import subprocess
import signal
import queue
import cv2
import numpy as np
import requests
import json
import socket
import urllib.parse
import uuid
from datetime import datetime, timezone
import pytz
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
import zlib
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import concurrent.futures

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, video_root)
_repo_root = os.path.abspath(os.path.join(video_root, '..'))
_lib_root = os.path.join(_repo_root, '.scripts', 'lib')
for _p in (_lib_root,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.utils.video_env import load_video_env

load_video_env(override=True)

import app.utils.nvidia_lib_path  # noqa: F401  须在 import onnxruntime 之前

# 导入VIDEO模块的模型
from models import db, AlgorithmTask, Device
from app.utils.gb28181_source import resolve_gb28181_alternate_pull_url, resolve_gb28181_source
from app.services.camera_service import resolve_device_ai_rtmp_stream
from app.utils.alert_images_paths import resolve_alert_images_root
from app.utils.decode.stream_adapter import is_async_stream, open_device_stream, stream_mode_label
from app.utils.onnx_inference import ONNXInference
try:
    from app.utils.utf8_detection_label import draw_detection_label
except ModuleNotFoundError as exc:
    if exc.name != "app.utils.utf8_detection_label":
        raise
    # EDGE/runtime 由 VIDEO 服务种子生成，但使用自身独立的公共运行库。
    from lib.utf8_detection_label import draw_detection_label
from app.utils.algo_model_detect import (
    is_end2end_ultralytics_model,
    is_yolo26_model,
    run_model_detection,
    warmup_model_detection,
)
from app.utils.face_capture_queue_service import (
    enqueue_face_capture,
    is_running as face_capture_queue_running,
    start_face_capture_workers,
    stop_face_capture_workers,
    FACE_CAPTURE_QUEUE_SIZE,
    FACE_CAPTURE_WORKER_THREADS,
)
from app.utils.plate_capture_queue_service import (
    enqueue_plate_capture,
    is_running as plate_capture_queue_running,
    start_plate_capture_workers,
    stop_plate_capture_workers,
    PLATE_CAPTURE_QUEUE_SIZE,
    PLATE_CAPTURE_WORKER_THREADS,
)
from app.utils.service_urls import (
    is_mini_deploy_profile,
    resolve_alert_hook_url,
    resolve_face_matching_publish_url,
    resolve_plate_matching_publish_url,
)


def _parse_gpu_id_list(value: str) -> List[int]:
    if not value:
        return []
    ids: List[int] = []
    for part in str(value).split(','):
        p = part.strip()
        if not p:
            continue
        try:
            ids.append(int(p))
        except Exception:
            continue
    # 去重但保序
    seen = set()
    result: List[int] = []
    for x in ids:
        if x in seen:
            continue
        seen.add(x)
        result.append(x)
    return result


def _detect_visible_gpu_ids() -> List[int]:
    """
    返回当前进程“可见”的GPU索引列表（用于推理/ultralytics/torch）。
    - 若设置 CUDA_VISIBLE_DEVICES，torch 看到的是重映射后的连续索引（0..N-1），这里以 torch 为准。
    - 若未安装 torch 或 CUDA 不可用，则返回空列表。
    """
    use_gpu = os.environ.get('USE_GPU', 'False').lower() == 'true'
    if not use_gpu:
        return []

    try:
        import torch  # type: ignore
        if not torch.cuda.is_available():
            return []
        n = int(torch.cuda.device_count())
        if n <= 0:
            return []
        return list(range(n))
    except Exception:
        return []


# GPU调度（按设备稳定映射到多张GPU，避免全部压到0号卡）
_VISIBLE_GPU_IDS: List[int] = []
_GPU_ASSIGNMENTS: Dict[str, Dict[str, int]] = {"infer": {}, "ffmpeg": {}}
_GPU_RR_COUNTER: Dict[str, int] = {"infer": 0, "ffmpeg": 0}
_GPU_SCHED_LOCK = threading.Lock()


def _get_gpu_policy(kind: str) -> str:
    # kind: infer / ffmpeg
    # 可选: hash | round_robin
    v = (os.getenv(f"{kind.upper()}_GPU_POLICY") or os.getenv("GPU_POLICY") or "hash").strip().lower()
    return v if v in ("hash", "round_robin") else "hash"


def _ensure_gpu_ids_initialized() -> None:
    global _VISIBLE_GPU_IDS
    if _VISIBLE_GPU_IDS:
        return

    # 优先使用显式配置（GPU_IDS），否则按 torch 可见设备数自动探测
    configured = _parse_gpu_id_list(os.getenv("GPU_IDS", "").strip())
    if configured:
        _VISIBLE_GPU_IDS = configured
        return

    _VISIBLE_GPU_IDS = _detect_visible_gpu_ids()


def _stable_key_hash(s: str) -> int:
    # Python 内置 hash() 在不同进程/启动间可能随机化，这里用 crc32 保证稳定映射
    return int(zlib.crc32(s.encode("utf-8")) & 0xFFFFFFFF)


def get_assigned_gpu_id(device_key: Any, kind: str) -> Optional[int]:
    """
    为某个 device_key 分配GPU索引。
    kind:
    - infer: 算法推理
    - ffmpeg: 编码/推流（h264_nvenc 的 -gpu 参数）
    """
    kind = (kind or "").strip().lower()
    if kind not in ("infer", "ffmpeg"):
        kind = "infer"

    _ensure_gpu_ids_initialized()
    if not _VISIBLE_GPU_IDS:
        return None

    key_str = str(device_key)
    with _GPU_SCHED_LOCK:
        cached = _GPU_ASSIGNMENTS[kind].get(key_str)
        if cached is not None:
            return cached

        policy = _get_gpu_policy(kind)
        if policy == "round_robin":
            idx = _GPU_RR_COUNTER[kind] % len(_VISIBLE_GPU_IDS)
            _GPU_RR_COUNTER[kind] += 1
            gpu_id = _VISIBLE_GPU_IDS[idx]
        else:
            gpu_id = _VISIBLE_GPU_IDS[_stable_key_hash(key_str) % len(_VISIBLE_GPU_IDS)]

        _GPU_ASSIGNMENTS[kind][key_str] = gpu_id
        return gpu_id


def get_infer_device(device_key: Any = None) -> str:
    """给推理用：返回 'cpu' 或 'cuda:{idx}'"""
    gpu_id = get_assigned_gpu_id(device_key if device_key is not None else "default", kind="infer")
    if gpu_id is None:
        return "cpu"
    return f"cuda:{gpu_id}"


def resolve_onnx_gpu_id(model_id: int) -> Optional[int]:
    """为 ONNX 模型分配 GPU 索引；USE_GPU=False 时返回 None（走 CPU）。"""
    if os.environ.get('USE_GPU', 'False').lower() != 'true':
        return None
    return get_assigned_gpu_id(model_id, kind='infer')


def get_ffmpeg_gpu_id(device_key: Any = None) -> Optional[int]:
    """给FFmpeg用：返回整数GPU索引（传给 -gpu），无GPU时返回None"""
    return get_assigned_gpu_id(device_key if device_key is not None else "default", kind="ffmpeg")


# Flask应用实例（延迟创建，避免导入run模块时的副作用）
_flask_app = None


def get_flask_app():
    """获取Flask应用实例（延迟创建，避免导入run模块时的副作用）"""
    global _flask_app
    if _flask_app is None:
        from flask import Flask
        app = Flask(__name__)
        # 从环境变量获取数据库URL
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 3600,
            'pool_size': 10,
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10,
            }
        }

        # 初始化数据库
        db.init_app(app)
        _flask_app = app
    return _flask_app


# 导入追踪器（使用相对导入）
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'utils'))
from tracker import SimpleTracker

# 环境变量已在文件顶部通过 load_video_env 加载

# OpenCV FFmpeg 解码参数（用于降低延迟并尽量忽略/丢弃损坏包）
# 说明：当上游流发生抖动/重连/丢包时，FFmpeg 解码常出现 "error while decoding MB..."；
# 该配置倾向于“丢弃损坏数据继续跑”，避免花屏/撕裂持续时间过长。
# RTSP 传输：优先 AI_RTSP_TRANSPORT，其次 OPENCV_/FFMPEG_；默认 udp（低延迟）；易丢包/跨主机可设 AI_RTSP_TRANSPORT=tcp
_EFFECTIVE_RTSP_TRANSPORT = (
    os.getenv("AI_RTSP_TRANSPORT")
    or os.getenv("OPENCV_FFMPEG_RTSP_TRANSPORT")
    or os.getenv("FFMPEG_RTSP_TRANSPORT")
    or "udp"
).strip().lower()
if _EFFECTIVE_RTSP_TRANSPORT not in ("tcp", "udp"):
    _EFFECTIVE_RTSP_TRANSPORT = "udp"

_OPENCV_FFMPEG_OPTIONS_CUSTOM = bool(os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS"))


def _realtime_env_int(name: str, default: int) -> int:
    try:
        raw = os.getenv(name, '').strip()
        return int(raw) if raw else default
    except (ValueError, TypeError):
        return default


def _expected_realtime_stream_count() -> int:
    """预期并发路数：显式配置 > 任务设备数 > 默认 8。"""
    for key in ('REALTIME_TARGET_STREAMS', 'STREAM_FORWARD_TARGET_STREAMS', 'AI_TARGET_STREAMS'):
        configured = _realtime_env_int(key, 0)
        if configured > 0:
            return configured
    cfg = globals().get('task_config')
    if cfg and getattr(cfg, 'device_streams', None):
        return max(1, len(cfg.device_streams))
    return 8


def _resolve_opencv_thread_queue_size() -> Optional[int]:
    """OpenCV thread_queue_size：默认不写入（兼容性更好）；显式配置或 ≥32 路时启用。"""
    explicit = os.getenv('REALTIME_THREAD_QUEUE_SIZE', '').strip()
    if not explicit:
        explicit = os.getenv('STREAM_FORWARD_THREAD_QUEUE_SIZE', '').strip()
    if explicit:
        try:
            return max(8, int(explicit))
        except (ValueError, TypeError):
            pass
    stream_count = _expected_realtime_stream_count()
    if stream_count >= 100:
        return 1024
    if stream_count >= 32:
        return 768
    return None


def _get_realtime_stream_stagger_sec() -> float:
    """多路 RTSP 建连错峰（与 stream_forward RELAY_STAGGER 对齐）。"""
    raw = os.getenv('REALTIME_STREAM_STAGGER_SEC', '').strip()
    if not raw:
        raw = os.getenv('STREAM_FORWARD_RELAY_STAGGER_SEC', '0.3').strip()
    try:
        return max(0.0, float(raw or '0.3'))
    except (ValueError, TypeError):
        return 0.3


def _build_opencv_ffmpeg_capture_options() -> str:
    rtsp_io_timeout_us = os.getenv('REALTIME_RW_TIMEOUT_US', '').strip() or os.getenv(
        'STREAM_FORWARD_RW_TIMEOUT_US', '5000000'
    ).strip() or '5000000'
    rtsp_open_timeout_us = os.getenv('REALTIME_RTSP_OPEN_TIMEOUT_US', '').strip() or os.getenv(
        'STREAM_FORWARD_RTSP_OPEN_TIMEOUT_US', '10000000'
    ).strip() or '10000000'
    parts = [
        f"rtsp_transport;{_EFFECTIVE_RTSP_TRANSPORT}",
        f"timeout;{rtsp_open_timeout_us}",
        f"rw_timeout;{rtsp_io_timeout_us}",
        "max_delay;500000",
        "fflags;nobuffer+discardcorrupt+genpts",
        "flags;low_delay",
        "err_detect;ignore_err",
    ]
    thread_queue_size = _resolve_opencv_thread_queue_size()
    if thread_queue_size is not None:
        parts.insert(4, f"thread_queue_size;{thread_queue_size}")
    return "|".join(parts)


def _opencv_thread_queue_log_label() -> str:
    tqs = _resolve_opencv_thread_queue_size()
    return str(tqs) if tqs is not None else '默认(未设置)'


def _refresh_opencv_ffmpeg_capture_options() -> None:
    """任务配置加载后刷新 OpenCV RTSP 参数。"""
    if _OPENCV_FFMPEG_OPTIONS_CUSTOM:
        return
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = _build_opencv_ffmpeg_capture_options()
    logger.info(
        "OpenCV RTSP: rtsp_transport=%s, thread_queue_size=%s/路",
        _EFFECTIVE_RTSP_TRANSPORT, _opencv_thread_queue_log_label(),
    )


if not _OPENCV_FFMPEG_OPTIONS_CUSTOM:
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = _build_opencv_ffmpeg_capture_options()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

if _OPENCV_FFMPEG_OPTIONS_CUSTOM:
    logger.info(
        "OpenCV RTSP: 已设置 OPENCV_FFMPEG_CAPTURE_OPTIONS（自定义），"
        "实际 rtsp_transport 以 options 为准（未走 AI_RTSP_TRANSPORT 默认拼接）"
    )
else:
    logger.info(
        "OpenCV RTSP: rtsp_transport=%s, thread_queue_size=%s/路（由 AI_RTSP_TRANSPORT / "
        "OPENCV_FFMPEG_RTSP_TRANSPORT / FFMPEG_RTSP_TRANSPORT 决定；默认 udp；易丢包/跨主机可试 tcp）",
        _EFFECTIVE_RTSP_TRANSPORT, _opencv_thread_queue_log_label(),
    )

# 时区设置（使用Asia/Shanghai，与Java端保持一致）
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# 全局变量
TASK_ID = int(os.getenv('TASK_ID', '0'))
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
VIDEO_SERVICE_PORT = os.getenv('VIDEO_SERVICE_PORT', '6000')
# 告警/匹配回调：mini 形态直连 VIDEO；完整形态经 iot-gateway /admin-api/video
ALERT_HOOK_URL = resolve_alert_hook_url()
FACE_MATCHING_PUBLISH_URL = resolve_face_matching_publish_url()
PLATE_MATCHING_PUBLISH_URL = resolve_plate_matching_publish_url()

# 数据库会话
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db_session = scoped_session(SessionLocal)

# 全局变量
stop_event = threading.Event()
task_config = None
yolo_models = {}
yolo_model_devices = {}  # {model_id: 'cpu' | 'cuda:N'}
yolo_model_meta = {}  # {model_id: {'yolo26': bool, 'end2end': bool, 'path': str}}
# 为每个摄像头创建独立的追踪器
trackers = {}  # {device_id: SimpleTracker}
# 为每个摄像头创建独立的帧索引计数器
frame_counts = {}  # {device_id: int}
# 双检测队列：overlay（主画面叠框）与 alert（告警）完全分离
overlay_detection_queues = {}  # {device_id: queue.Queue}
alert_detection_queues = {}  # {device_id: queue.Queue}
overlay_executor = None
alert_executor = None
# 摄像头流连接（FFmpeg 解码 / OpenCV / 异步缓冲）
device_caps = {}  # {device_id: FfmpegVideoStream | AsyncVideoStream | cv2.VideoCapture}
# 摄像头推送进程（FFmpeg进程）
device_pushers = {}  # {device_id: subprocess.Popen}
# 固定速率推帧线程：将推帧从主循环解耦，确保匀速推流
device_output_frames = {}  # {device_id: {'frame': np.ndarray, 'w': int, 'h': int} or None}
device_output_locks = {}  # {device_id: threading.Lock()}
device_push_threads = {}  # {device_id: threading.Thread}
device_push_running = {}  # {device_id: threading.Event()}
# FFmpeg进程的stderr读取线程和错误信息
device_pusher_stderr_threads = {}  # {device_id: threading.Thread}
device_pusher_stderr_buffers = {}  # {device_id: list} 存储stderr输出
device_pusher_stderr_locks = {}  # {device_id: threading.Lock}
# 设备编码器状态：记录每个设备实际使用的编码器（用于硬件编码失败时自动回退）
device_codec_status = {}  # {device_id: 'h264_nvenc' | 'libx264'}
device_codec_locks = {}  # {device_id: threading.Lock} 保护编码器状态
# 告警抑制：记录每个设备上次告警推送时间
last_alert_time = {}  # {device_id: timestamp}
alert_time_lock = threading.Lock()  # 告警时间戳锁，确保线程安全
# 最新检测 overlay 缓存：检测迟达时主画面仍可叠框（与告警图一致）
device_latest_overlays = {}  # {device_id: {'detections': [...], 'timestamp': float, 'frame_number': int}}
# SAM 补充识别（YOLO + SAM Pipeline）
_sam_config = None
_sam_client = None
device_latest_overlay_locks = {}  # {device_id: threading.Lock()}


def _alert_event_suppress_seconds() -> float:
    """从任务配置读取告警事件抑制间隔（秒），减轻 hook/Kafka 压力。"""
    if task_config is None:
        return float(os.getenv('ALERT_EVENT_SUPPRESS_INTERVAL', '5'))
    raw = getattr(task_config, 'alert_event_suppress_time', None)
    if raw is None:
        return 5.0
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 5.0

# 配置参数（算法链路）
# 观感推流帧率（与 AI 抽帧完全解耦）：默认 25fps
AI_OUTPUT_FPS = int(os.getenv(
    'AI_OUTPUT_FPS',
    os.getenv('AI_SOURCE_FPS', os.getenv('VIEW_OUTPUT_FPS', os.getenv('VIEW_SOURCE_FPS', '25'))),
))
TARGET_WIDTH = int(os.getenv('AI_TARGET_WIDTH', os.getenv('VIEW_TARGET_WIDTH', os.getenv('TARGET_WIDTH', '1280'))))
TARGET_HEIGHT = int(os.getenv('AI_TARGET_HEIGHT', os.getenv('VIEW_TARGET_HEIGHT', os.getenv('TARGET_HEIGHT', '720'))))
TARGET_RESOLUTION = (TARGET_WIDTH, TARGET_HEIGHT)
# AI 检测/告警抽帧间隔（仅影响告警推理队列，overlay 叠框见 OVERLAY_EXTRACT_INTERVAL）
EXTRACT_INTERVAL = int(os.getenv('EXTRACT_INTERVAL', '12'))
# 运行时任务级抽帧间隔（load_task_config 后覆盖环境变量默认值）
_runtime_extract_interval = EXTRACT_INTERVAL
# overlay 叠框专用抽帧间隔（与告警/任务 DB extract_interval 解耦，默认每 5 帧检测一次）
OVERLAY_EXTRACT_INTERVAL = int(os.getenv('OVERLAY_EXTRACT_INTERVAL', '5'))
_runtime_overlay_extract_interval = OVERLAY_EXTRACT_INTERVAL
_runtime_alert_extract_interval = int(
    os.getenv('ALERT_EXTRACT_INTERVAL', str(max(EXTRACT_INTERVAL * 2, EXTRACT_INTERVAL)))
)
# 运动检测门控
motion_gate = None  # load_task_config 后初始化
BUFFER_SIZE = int(os.getenv('BUFFER_SIZE', '70'))
MIN_BUFFER_FRAMES = int(os.getenv('MIN_BUFFER_FRAMES', '15'))
MAX_WAIT_TIME = float(os.getenv('MAX_WAIT_TIME', '0.08'))
# FFmpeg编码参数（优化以降低CPU占用）
# FFmpeg编码参数（优化以降低CPU占用）
# 处理空字符串的情况，确保参数有效
FFMPEG_PRESET_ENV = os.getenv('AI_FFMPEG_PRESET', os.getenv('VIEW_FFMPEG_PRESET', os.getenv('FFMPEG_PRESET', 'veryfast')))
FFMPEG_PRESET = FFMPEG_PRESET_ENV.strip() if FFMPEG_PRESET_ENV and FFMPEG_PRESET_ENV.strip() else 'veryfast'  # 高清优先：veryfast 在质量和延迟间平衡

FFMPEG_VIDEO_BITRATE_ENV = os.getenv('AI_FFMPEG_VIDEO_BITRATE', os.getenv('VIEW_FFMPEG_VIDEO_BITRATE', os.getenv('FFMPEG_VIDEO_BITRATE', '3500k')))
FFMPEG_VIDEO_BITRATE = FFMPEG_VIDEO_BITRATE_ENV.strip() if FFMPEG_VIDEO_BITRATE_ENV and FFMPEG_VIDEO_BITRATE_ENV.strip() else '3500k'  # 高清优先：720p建议>=3000k

# 编码线程数：None表示自动，可设置为较小值降低CPU
# 处理空字符串的情况，确保只有有效的数字字符串才会被使用
FFMPEG_THREADS_ENV = os.getenv('FFMPEG_THREADS', None)
FFMPEG_THREADS = None if not FFMPEG_THREADS_ENV or FFMPEG_THREADS_ENV.strip() == '' else FFMPEG_THREADS_ENV.strip()
# GOP大小：2秒一个关键帧（在SOURCE_FPS定义后计算）
FFMPEG_GOP_SIZE_ENV = os.getenv('AI_FFMPEG_GOP_SIZE', os.getenv('VIEW_FFMPEG_GOP_SIZE', os.getenv('FFMPEG_GOP_SIZE', None)))
FFMPEG_GOP_SIZE = int(FFMPEG_GOP_SIZE_ENV) if FFMPEG_GOP_SIZE_ENV else max(1, AI_OUTPUT_FPS * 2)

# 硬件加速配置
FFMPEG_HWACCEL_ENV = os.getenv('FFMPEG_HWACCEL', 'auto').strip().lower()
FFMPEG_HWACCEL = FFMPEG_HWACCEL_ENV if FFMPEG_HWACCEL_ENV in ['auto', 'nvenc', 'cuvid', 'none'] else 'auto'

# YOLO检测参数（优化以降低CPU占用）
YOLO_IMG_SIZE = int(os.getenv('YOLO_IMG_SIZE', '640'))  # 高清场景下提升小目标检测和叠框细节
YOLO_DETECT_IOU = float(os.getenv('YOLO_DETECT_IOU', '0.45'))


def _get_detect_conf(*, end2end: bool = False, yolo26: bool = False) -> float:
    """检测置信度阈值；优先使用任务配置，其次环境变量，默认 0.5。"""
    if task_config is not None:
        task_conf = getattr(task_config, 'detect_conf', None)
        if task_conf is not None:
            try:
                return float(task_conf)
            except (TypeError, ValueError):
                pass
    raw = os.getenv('YOLO_DETECT_CONF', '').strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return 0.5


def _any_loaded_model_is_end2end() -> bool:
    if yolo_model_meta:
        return any(meta.get('end2end') or meta.get('yolo26') for meta in yolo_model_meta.values())
    return any(is_end2end_ultralytics_model(model) for model in yolo_models.values())


def _any_loaded_model_is_yolo26() -> bool:
    if yolo_model_meta:
        return any(meta.get('yolo26') for meta in yolo_model_meta.values())
    return any(is_yolo26_model(model) for model in yolo_models.values())


def _resolve_detection_imgsz(frame, base_imgsz: int) -> int:
    """1080p 源流下自动提高推理分辨率，缓解 yolo26n 漏检远处行人。"""
    env_raw = os.getenv('YOLO_DETECT_IMG_SIZE', '').strip()
    if env_raw:
        try:
            return max(32, int(env_raw))
        except ValueError:
            pass
    if _any_loaded_model_is_yolo26():
        yolo26_imgsz = int(os.getenv('YOLO26_IMG_SIZE', '1280'))
        if frame is not None and getattr(frame, 'shape', None):
            frame_h = int(frame.shape[0])
            if frame_h >= 1080:
                return max(base_imgsz, yolo26_imgsz)
            if frame_h >= 720:
                return max(base_imgsz, min(yolo26_imgsz, 960))
    return base_imgsz


def _summarize_detections(detections: list, limit: int = 5) -> str:
    if not detections:
        return '无'
    parts = []
    for det in detections[:limit]:
        name = det.get('class_name', 'unknown')
        score = float(det.get('confidence', 0.0))
        parts.append(f'{name}:{score:.2f}')
    if len(detections) > limit:
        parts.append(f'...+{len(detections) - limit}')
    return ', '.join(parts)


def _check_ultralytics_for_yolo26(model_path: str, model_id: int) -> None:
    """YOLO26 需 ultralytics>=8.4.0，旧版本会导致 end2end 后处理异常、漏检严重。"""
    path_lower = str(model_path or '').lower()
    if model_id != -3 and 'yolo26' not in path_lower:
        return
    try:
        import ultralytics
        from packaging.version import Version
        version = Version(getattr(ultralytics, '__version__', '0.0.0'))
        if version < Version('8.4.0'):
            logger.error(
                '⚠️ YOLO26 模型需要 ultralytics>=8.4.0，当前版本 %s 可能导致大量漏检（仅检出冰箱等大目标）。'
                '请升级依赖后重启服务：pip install "ultralytics>=8.4.0,<9.0.0"',
                ultralytics.__version__,
            )
        else:
            logger.info('ultralytics 版本 %s 满足 YOLO26 要求', ultralytics.__version__)
    except Exception as exc:
        logger.warning('无法校验 ultralytics 版本（YOLO26）: %s', exc)

# 队列大小：主画面 overlay 小队列+保留最新；告警队列可独立积压
_legacy_detection_qsize = int(os.getenv('DETECTION_QUEUE_SIZE', '100'))
OVERLAY_DETECTION_QUEUE_SIZE = int(os.getenv('OVERLAY_DETECTION_QUEUE_SIZE', '5'))
ALERT_DETECTION_QUEUE_SIZE = int(os.getenv('ALERT_DETECTION_QUEUE_SIZE', str(_legacy_detection_qsize)))
PUSH_QUEUE_SIZE = int(os.getenv('PUSH_QUEUE_SIZE', '100'))  # 推帧队列大小（默认100，原50）
EXTRACT_QUEUE_SIZE = int(os.getenv('EXTRACT_QUEUE_SIZE', '50'))  # 抽帧队列大小（默认50）
# 双队列 Worker：主画面与告警分离，互不争抢 GPU
_legacy_yolo_workers = int(os.getenv('YOLO_WORKER_THREADS', '2'))
OVERLAY_WORKER_THREADS = int(os.getenv('OVERLAY_WORKER_THREADS', os.getenv('YOLO_WORKER_THREADS', '1')))
ALERT_WORKER_THREADS = int(os.getenv('ALERT_WORKER_THREADS', '1'))


def _resolve_worker_thread_count(
    device_count: int,
    *,
    thread_env: str,
    legacy_env: str = 'YOLO_WORKER_THREADS',
    auto_env: str,
    max_env: str,
    default_max: int,
    default_fixed: int = 1,
) -> int:
    """按摄像头数量分配检测线程；可通过 *_AUTO=false 退回固定线程数。"""
    auto = os.getenv(auto_env, 'true').strip().lower() in ('1', 'true', 'yes', 'on')
    if not auto:
        raw = (os.getenv(thread_env) or os.getenv(legacy_env) or '').strip()
        return max(1, int(raw or default_fixed))
    max_workers = max(1, int(os.getenv(max_env, str(default_max))))
    return max(1, min(max(1, device_count), max_workers))
# 告警抽帧间隔（默认比主画面更稀疏，减轻 GPU 压力；运行时由 _runtime_alert_extract_interval 覆盖）
ALERT_EXTRACT_INTERVAL = int(os.getenv('ALERT_EXTRACT_INTERVAL', str(max(EXTRACT_INTERVAL * 2, EXTRACT_INTERVAL))))
# 主画面 overlay 推理分辨率（默认同 YOLO_IMG_SIZE，可单独调低以提速）
OVERLAY_YOLO_IMG_SIZE = int(os.getenv('OVERLAY_YOLO_IMG_SIZE', os.getenv('YOLO_IMG_SIZE', '640')))
# 画质分档（算法链路）：优先 AI_VIDEO_QUALITY_PROFILE
VIDEO_QUALITY_PROFILE = os.getenv(
    'AI_VIDEO_QUALITY_PROFILE',
    os.getenv('VIEW_VIDEO_QUALITY_PROFILE', os.getenv('VIDEO_QUALITY_PROFILE', '')),
).strip().lower()
QUALITY_PROFILE_PRESETS = {
    'low': {
        'target_width': 640,
        'target_height': 360,
        'ffmpeg_video_bitrate': '1500k',
        'yolo_img_size': 416,
    },
    'medium': {
        'target_width': 1280,
        'target_height': 720,
        'ffmpeg_video_bitrate': '2500k',
        'yolo_img_size': 512,
    },
    'high': {
        'target_width': 1280,
        'target_height': 720,
        'ffmpeg_video_bitrate': '3500k',
        'yolo_img_size': 640,
    },
}
if VIDEO_QUALITY_PROFILE in QUALITY_PROFILE_PRESETS:
    selected_profile = QUALITY_PROFILE_PRESETS[VIDEO_QUALITY_PROFILE]
    TARGET_WIDTH = selected_profile['target_width']
    TARGET_HEIGHT = selected_profile['target_height']
    TARGET_RESOLUTION = (TARGET_WIDTH, TARGET_HEIGHT)
    FFMPEG_VIDEO_BITRATE = selected_profile['ffmpeg_video_bitrate']
    YOLO_IMG_SIZE = selected_profile['yolo_img_size']
    if not FFMPEG_GOP_SIZE_ENV:
        FFMPEG_GOP_SIZE = max(1, AI_OUTPUT_FPS * 2)
if not (os.getenv('OVERLAY_YOLO_IMG_SIZE') or '').strip():
    OVERLAY_YOLO_IMG_SIZE = YOLO_IMG_SIZE
# 自适应画质配置：根据推流稳定性自动升降档
AUTO_QUALITY_ENABLED = os.getenv('AUTO_QUALITY_ENABLED', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
AUTO_QUALITY_FAILURE_THRESHOLD = int(os.getenv('AUTO_QUALITY_FAILURE_THRESHOLD', '5'))
AUTO_QUALITY_RECOVERY_SECONDS = int(os.getenv('AUTO_QUALITY_RECOVERY_SECONDS', '180'))
AUTO_QUALITY_SWITCH_COOLDOWN_SECONDS = int(os.getenv('AUTO_QUALITY_SWITCH_COOLDOWN_SECONDS', '30'))
QUALITY_PROFILE_ORDER = ['low', 'medium', 'high']
AUTO_QUALITY_LOCK_PROFILE = os.getenv('AUTO_QUALITY_LOCK_PROFILE', '').strip().lower()
_quality_profile_lock = threading.Lock()
_quality_current_index = QUALITY_PROFILE_ORDER.index(VIDEO_QUALITY_PROFILE) if VIDEO_QUALITY_PROFILE in QUALITY_PROFILE_ORDER else QUALITY_PROFILE_ORDER.index('high')
_quality_last_switch_ts = 0.0
_quality_last_failure_ts = 0.0
_quality_failure_count = 0


def _get_effective_quality_profile_name() -> str:
    with _quality_profile_lock:
        return QUALITY_PROFILE_ORDER[_quality_current_index]


def _get_effective_realtime_stream_params():
    """返回观感推流参数；output_fps 固定走 AI_OUTPUT_FPS，与 EXTRACT_INTERVAL 无关。"""
    profile_name = AUTO_QUALITY_LOCK_PROFILE if AUTO_QUALITY_LOCK_PROFILE in QUALITY_PROFILE_PRESETS else _get_effective_quality_profile_name()
    preset = QUALITY_PROFILE_PRESETS.get(profile_name, QUALITY_PROFILE_PRESETS['high'])
    output_fps = max(1, int(AI_OUTPUT_FPS))
    target_width = int(preset['target_width'])
    target_height = int(preset['target_height'])
    bitrate = str(preset['ffmpeg_video_bitrate'])
    gop_size = int(FFMPEG_GOP_SIZE) if FFMPEG_GOP_SIZE_ENV else max(1, output_fps * 2)
    return profile_name, output_fps, target_width, target_height, bitrate, gop_size


def _mark_quality_failure(reason: str):
    if AUTO_QUALITY_LOCK_PROFILE in QUALITY_PROFILE_PRESETS:
        return
    if not AUTO_QUALITY_ENABLED:
        return
    global _quality_failure_count, _quality_last_switch_ts, _quality_last_failure_ts, _quality_current_index
    now = time.time()
    with _quality_profile_lock:
        _quality_last_failure_ts = now
        _quality_failure_count += 1
        if _quality_failure_count < AUTO_QUALITY_FAILURE_THRESHOLD:
            return
        if now - _quality_last_switch_ts < AUTO_QUALITY_SWITCH_COOLDOWN_SECONDS:
            return
        if _quality_current_index <= 0:
            _quality_failure_count = 0
            return
        _quality_current_index -= 1
        _quality_last_switch_ts = now
        _quality_failure_count = 0
        new_profile = QUALITY_PROFILE_ORDER[_quality_current_index]
    logger.warning(f"⚠️ 自动降档到 {new_profile}（原因: {reason}）")


def _mark_quality_success():
    if AUTO_QUALITY_LOCK_PROFILE in QUALITY_PROFILE_PRESETS:
        return
    if not AUTO_QUALITY_ENABLED:
        return
    global _quality_failure_count, _quality_last_switch_ts, _quality_current_index
    now = time.time()
    with _quality_profile_lock:
        if _quality_failure_count > 0:
            _quality_failure_count -= 1
        if now - _quality_last_failure_ts < AUTO_QUALITY_RECOVERY_SECONDS:
            return
        if now - _quality_last_switch_ts < AUTO_QUALITY_SWITCH_COOLDOWN_SECONDS:
            return
        if _quality_current_index >= len(QUALITY_PROFILE_ORDER) - 1:
            return
        _quality_current_index += 1
        _quality_last_switch_ts = now
        new_profile = QUALITY_PROFILE_ORDER[_quality_current_index]
    logger.info(f"✅ 自动升档到 {new_profile}（链路稳定）")
# 插值框复用阈值：限制旧检测结果复用时长，避免低延迟模式下出现拖影
INTERPOLATED_DETECTION_MAX_AGE_MS = int(os.getenv('INTERPOLATED_DETECTION_MAX_AGE_MS', '200'))
INTERPOLATED_DETECTION_MAX_AGE_SEC = max(0.0, INTERPOLATED_DETECTION_MAX_AGE_MS / 1000.0)
INTERPOLATED_DETECTION_MAX_FRAME_GAP = int(
    os.getenv('INTERPOLATED_DETECTION_MAX_FRAME_GAP', str(max(2, AI_OUTPUT_FPS)))
)
# 主画面 overlay 队列：始终保留最新待检帧
OVERLAY_KEEP_LATEST = os.getenv('OVERLAY_KEEP_LATEST', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
OVERLAY_KEEP_LATEST_THRESHOLD = int(os.getenv('OVERLAY_KEEP_LATEST_THRESHOLD', '2'))
# 告警检测队列：默认保留最新帧，多路摄像头避免队列满丢帧
_alert_keep_latest_default = 'true'
ALERT_KEEP_LATEST = os.getenv('ALERT_KEEP_LATEST', _alert_keep_latest_default).strip().lower() in ('1', 'true', 'yes', 'on')
ALERT_KEEP_LATEST_THRESHOLD = int(os.getenv('ALERT_KEEP_LATEST_THRESHOLD', str(max(2, ALERT_DETECTION_QUEUE_SIZE // 2))))
# 兼容旧配置名
DETECTION_KEEP_LATEST = OVERLAY_KEEP_LATEST
DETECTION_KEEP_LATEST_THRESHOLD = OVERLAY_KEEP_LATEST_THRESHOLD
# 主画面 overlay 最大复用时长（毫秒）；0=直到下次检测更新/清空，仅设安全上限
# 主画面叠框追踪（默认关闭：追踪会在推流侧插值框位置，产生“假框自己动”）
OVERLAY_USE_TRACKING = os.getenv('OVERLAY_USE_TRACKING', 'false').strip().lower() in (
    '1', 'true', 'yes', 'on',
)
LATEST_OVERLAY_MAX_AGE_MS = int(os.getenv('LATEST_OVERLAY_MAX_AGE_MS', '0'))
LATEST_OVERLAY_MAX_AGE_SEC = max(0.0, LATEST_OVERLAY_MAX_AGE_MS / 1000.0)

FACE_CLASS_KEYWORDS = ('face', 'facial', 'person_face', '人脸')
PLATE_CLASS_KEYWORDS = ('plate', 'license_plate', 'licence_plate', 'car_plate', '车牌')


def _detections_to_overlay_entries(detections, timestamp):
    """将检测结果转为 draw_detections 可用的 overlay 条目（均为真实检测框）。"""
    entries = []
    for det in detections:
        bbox = det.get('bbox', [])
        if bbox and len(bbox) == 4:
            entries.append({
                'bbox': bbox,
                'class_name': det.get('class_name', 'unknown'),
                'confidence': det.get('confidence', 0.0),
                'track_id': det.get('track_id', 0),
                'is_cached': False,
                'first_seen_time': det.get('first_seen_time', timestamp),
                'duration': det.get('duration', 0.0),
            })
    return entries


def _overlay_stale_frame_lag() -> int:
    """积压队列中超过此帧差的待检帧视为过期，不应用「空结果」清空当前叠框缓存。"""
    fps = max(1, AI_OUTPUT_FPS)
    interval = max(1, _runtime_overlay_extract_interval)
    device_n = max(1, len(overlay_detection_queues) or len(frame_counts) or 1)
    # 多路 CPU 推理时队列滞后常达数百帧；按路数预留约 2s/路的排队预算
    per_device_budget = max(interval * 6, fps * 2)
    return max(interval * 4, fps, per_device_budget * device_n)


def _is_stale_overlay_detection_frame(device_id: str, frame_number: int) -> bool:
    current = frame_counts.get(device_id, frame_number)
    return frame_number < current - _overlay_stale_frame_lag()


def _overlay_effective_max_age_sec() -> float:
    """overlay 框最大存活时间；LATEST_OVERLAY_MAX_AGE_MS=0 时按 overlay 检测周期设上限。"""
    if LATEST_OVERLAY_MAX_AGE_MS > 0:
        return LATEST_OVERLAY_MAX_AGE_SEC
    interval = max(1, _runtime_overlay_extract_interval)
    fps = max(1, AI_OUTPUT_FPS)
    period = interval / fps
    device_n = max(1, len(overlay_detection_queues) or len(frame_counts) or 1)
    # 多路轮转 + CPU 推理延迟：TTL 需撑到下一次 overlay 检测完成
    return max(0.8, period * (device_n + 2) + 0.3)


def _update_device_latest_overlay(
    device_id: str,
    detections: list,
    timestamp: float,
    frame_number: int,
    *,
    applied_at: Optional[float] = None,
) -> bool:
    """更新设备最新检测 overlay；无目标时清空缓存，避免旧框长期残留。

    返回 True 表示缓存已写入/清空；False 表示因积压过期而跳过（仅空结果会跳过）。
    """
    is_stale = _is_stale_overlay_detection_frame(device_id, frame_number)
    # 推流侧按「检测完成时刻」计算 TTL，避免队列迟延导致刚写入即过期
    cache_timestamp = applied_at if applied_at is not None else time.time()

    lock = device_latest_overlay_locks.setdefault(device_id, threading.Lock())
    with lock:
        if not detections:
            if is_stale:
                return False
            device_latest_overlays.pop(device_id, None)
            return True
    entries = _detections_to_overlay_entries(detections, timestamp)
    if not entries:
        with lock:
            if is_stale:
                return False
            device_latest_overlays.pop(device_id, None)
        return True
    # 有目标时始终接受（即便帧号滞后，也是当前能拿到的最新推理结果）
    with lock:
        device_latest_overlays[device_id] = {
            'detections': entries,
            'timestamp': cache_timestamp,
            'frame_number': frame_number,
        }
    return True


def _apply_latest_overlay_if_needed(
    device_id: str,
    output_frame,
    current_timestamp: float,
    frame_number: int,
    tracking_enabled: bool = False,
):
    """用最近一次真实 YOLO 检测结果叠框；默认不做追踪插值，避免假框漂移。"""
    lock = device_latest_overlay_locks.get(device_id)
    if not lock:
        return output_frame, False

    overlay_detections = None
    with lock:
        overlay = device_latest_overlays.get(device_id)
    if overlay and overlay.get('detections'):
        age = current_timestamp - overlay.get('timestamp', 0)
        max_age = _overlay_effective_max_age_sec()
        if age <= max_age:
            overlay_detections = overlay['detections']
        elif age > max_age:
            # 过期缓存主动清理，避免推流侧反复判断
            with lock:
                if device_latest_overlays.get(device_id) is overlay:
                    device_latest_overlays.pop(device_id, None)

    # 仅显式开启 OVERLAY_USE_TRACKING 时才在推流侧做追踪插值（会产生非检测帧的“假框”）
    use_overlay_tracking = OVERLAY_USE_TRACKING
    if use_overlay_tracking:
        tracker = trackers.get(device_id)
        if tracker:
            tracked = tracker.get_all_tracks(current_time=current_timestamp, frame_number=frame_number)
            if tracked:
                overlay_detections = tracked

    if not overlay_detections:
        return output_frame, False

    # 非追踪模式：只绘制真实检测框，过滤追踪器缓存/插值框
    if not use_overlay_tracking:
        overlay_detections = [d for d in overlay_detections if not d.get('is_cached')]

    if not overlay_detections:
        return output_frame, False

    drawn = draw_detections(
        output_frame.copy(),
        overlay_detections,
        frame_number=frame_number,
        tracking_enabled=use_overlay_tracking,
    )
    return drawn, True


def _enqueue_keep_latest(
    target_queue: queue.Queue,
    device_id: str,
    payload: dict,
    *,
    queue_size: int,
    keep_latest: bool,
    keep_latest_threshold: int,
    queue_label: str,
) -> bool:
    """将帧送入指定检测队列；可选积压时丢弃旧帧仅保留最新。"""
    if target_queue is None:
        return False

    frame_number = payload.get('frame_number', 0)
    drained = 0

    if keep_latest and target_queue.qsize() >= keep_latest_threshold:
        while True:
            try:
                target_queue.get_nowait()
                drained += 1
            except queue.Empty:
                break
        if drained > 0 and frame_number % 50 == 0:
            logger.info(
                f"🔄 设备 {device_id} {queue_label}队列积压，丢弃 {drained} 帧旧数据，保留最新待检帧 {frame_number}"
            )

    try:
        target_queue.put(payload, timeout=0.2)
        return True
    except queue.Full:
        if keep_latest:
            while True:
                try:
                    target_queue.get_nowait()
                    drained += 1
                except queue.Empty:
                    break
            try:
                target_queue.put(payload, timeout=0.05)
                if drained > 0:
                    logger.debug(
                        f"🔄 设备 {device_id} {queue_label}队列满，清空 {drained} 帧后入队最新帧 {frame_number}"
                    )
                return True
            except queue.Full:
                pass
        frame_id = payload.get('frame_id', frame_number)
        logger.warning(
            f"⚠️  设备 {device_id} {queue_label}队列已满，丢弃帧 {frame_id}（队列大小: {queue_size}）"
        )
        return False


# 多设备检测队列公平轮询（避免字典序第一路独占 Worker）
_poll_rr_counters = {}
_poll_rr_lock = threading.Lock()


def _poll_device_detection_queue(queues_dict: dict, timeout: float = 0.1):
    """从多设备检测队列中公平轮询取一帧，避免单路摄像头饿死其余路。"""
    if not queues_dict:
        return None, None, None

    device_ids = sorted(queues_dict.keys())
    n = len(device_ids)
    dict_id = id(queues_dict)

    with _poll_rr_lock:
        start = _poll_rr_counters.get(dict_id, 0) % n

    for attempt in range(n):
        idx = (start + attempt) % n
        device_id = device_ids[idx]
        device_queue = queues_dict[device_id]
        try:
            item = device_queue.get_nowait()
            with _poll_rr_lock:
                _poll_rr_counters[dict_id] = (idx + 1) % n
            return item, device_id, device_queue
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 队列获取异常: {str(e)}")

    per_wait = max(0.01, timeout / max(n, 1))
    for attempt in range(n):
        idx = (start + attempt) % n
        device_id = device_ids[idx]
        device_queue = queues_dict[device_id]
        try:
            item = device_queue.get(timeout=per_wait)
            with _poll_rr_lock:
                _poll_rr_counters[dict_id] = (idx + 1) % n
            return item, device_id, device_queue
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 队列获取异常: {str(e)}")

    return None, None, None


def _run_yolo_on_frame(
    frame,
    device_id: str,
    *,
    frame_number: int,
    timestamp: float,
    imgsz: int,
    use_tracking: bool,
):
    """对单帧执行全部模型检测，返回 (tracked_detections, detections)。"""
    all_detections = []
    use_yolo26 = _any_loaded_model_is_yolo26()
    detect_conf = _get_detect_conf(
        end2end=_any_loaded_model_is_end2end(),
        yolo26=use_yolo26,
    )
    effective_imgsz = _resolve_detection_imgsz(frame, imgsz)
    for model_id, yolo_model in yolo_models.items():
        if stop_event.is_set():
            break
        try:
            infer_device = yolo_model_devices.get(model_id, get_infer_device(device_id))
            model_dets = run_model_detection(
                yolo_model,
                frame,
                conf=detect_conf,
                iou=YOLO_DETECT_IOU,
                imgsz=effective_imgsz,
                infer_device=infer_device,
                should_keep=_make_detection_filter(yolo_model),
            )
            all_detections.extend(model_dets)
        except Exception as e:
            if stop_event.is_set():
                break
            logger.error(f"❌ 模型 {model_id} 检测异常: {str(e)}", exc_info=True)

    tracked_detections = []
    if use_tracking:
        tracker = trackers.get(device_id)
        if tracker:
            tracked_detections = tracker.update(all_detections, frame_number, current_time=timestamp)
        else:
            tracked_detections = [
                dict(det, track_id=0, is_cached=False, first_seen_time=timestamp, duration=0.0)
                for det in all_detections
            ]
    else:
        tracked_detections = [
            dict(det, track_id=0, is_cached=False, first_seen_time=timestamp, duration=0.0)
            for det in all_detections
        ]

    # SAM 补充识别（Pipeline 精修 / 开放词汇 / 告警确认）
    global _sam_config, _sam_client
    if _sam_config and _sam_config.get('enabled') and _sam_client:
        try:
            from app.utils.sam_supplement import sam_supplement_frame
            supplemented = sam_supplement_frame(
                frame, all_detections, _sam_config, _sam_client, frame_number=frame_number,
            )
            if supplemented is not all_detections:
                all_detections = supplemented
                if use_tracking:
                    tracker = trackers.get(device_id)
                    if tracker:
                        tracked_detections = tracker.update(all_detections, frame_number, current_time=timestamp)
                    else:
                        tracked_detections = [
                            dict(det, track_id=0, is_cached=False, first_seen_time=timestamp, duration=0.0)
                            for det in all_detections
                        ]
                else:
                    tracked_detections = [
                        dict(det, track_id=0, is_cached=False, first_seen_time=timestamp, duration=0.0)
                        for det in all_detections
                    ]
        except Exception as e:
            logger.warning(f"SAM 补充识别异常 device={device_id}: {e}")

    detections = []
    for tracked_det in tracked_detections:
        detections.append({
            'track_id': tracked_det.get('track_id', 0),
            'class_id': tracked_det.get('class_id', 0),
            'class_name': tracked_det.get('class_name', 'unknown'),
            'confidence': tracked_det.get('confidence', 0.0),
            'bbox': tracked_det.get('bbox', []),
            'timestamp': timestamp,
            'frame_number': frame_number,
            'is_cached': tracked_det.get('is_cached', False),
            'first_seen_time': tracked_det.get('first_seen_time', timestamp),
            'duration': tracked_det.get('duration', 0.0),
        })
    return tracked_detections, detections


def _build_detection_payload(device_id: str, frame, frame_number: int, timestamp: float) -> dict:
    """构造检测队列 payload（每队列独立 copy，避免共享引用）。"""
    return {
        'frame_id': f"{device_id}_frame_{frame_number}_{int(timestamp)}",
        'frame': frame.copy(),
        'frame_number': frame_number,
        'timestamp': timestamp,
        'device_id': device_id,
    }


def _resolve_runtime_extract_interval(task) -> int:
    """解析有效检测间隔：任务 DB > 环境变量 EXTRACT_INTERVAL（默认 12，25fps 下约每秒 2 次）。"""
    env_interval = max(1, int(os.getenv('EXTRACT_INTERVAL', str(EXTRACT_INTERVAL))))
    if not task:
        return env_interval
    db_raw = getattr(task, 'extract_interval', None)
    if db_raw is None or int(db_raw) <= 0:
        return env_interval
    return max(1, int(db_raw))


def _apply_runtime_sampling_config(task):
    """从任务配置 / 环境变量更新运行时抽帧间隔与运动门控。"""
    global _runtime_extract_interval, _runtime_overlay_extract_interval, _runtime_alert_extract_interval, motion_gate

    _runtime_extract_interval = _resolve_runtime_extract_interval(task)
    _runtime_overlay_extract_interval = max(
        1, int(os.getenv('OVERLAY_EXTRACT_INTERVAL', str(OVERLAY_EXTRACT_INTERVAL)))
    )

    alert_env = os.getenv('ALERT_EXTRACT_INTERVAL', '').strip()
    if alert_env:
        _runtime_alert_extract_interval = max(_runtime_extract_interval, int(alert_env))
    else:
        _runtime_alert_extract_interval = _runtime_extract_interval * 2

    try:
        from app.utils.motion_gate import MotionGate, MotionGateConfig
        base_cfg = MotionGateConfig.from_env()
        cfg = MotionGateConfig.from_task(task, base=base_cfg)
        motion_gate = MotionGate(cfg) if cfg.enabled else None
        logger.info(
            '检测采样已更新: overlay_interval=%s (约 %.1f 次/秒@25fps), alert_interval=%s, env=%s, db=%s, motion_gate=%s, preset=%s',
            _runtime_overlay_extract_interval,
            25.0 / _runtime_overlay_extract_interval,
            _runtime_alert_extract_interval,
            os.getenv('EXTRACT_INTERVAL', str(EXTRACT_INTERVAL)),
            getattr(task, 'extract_interval', None) if task else None,
            cfg.enabled,
            cfg.preset,
        )
    except Exception as exc:
        logger.warning('运动门控初始化失败: %s', exc)
        motion_gate = None


def _feed_stream_detection_queues(device_id: str, frame, frame_number: int, timestamp: float):
    """缓流器内投递 overlay/告警双队列（仅 AI 推理采样，与观感推流帧率完全分离）。"""
    alert_interval = max(1, _runtime_alert_extract_interval)
    overlay_interval = max(1, _runtime_overlay_extract_interval)
    # 首帧立即采样，避免启动后长时间无检测框
    is_overlay_sample = (frame_number == 1) or (frame_number % overlay_interval == 0)
    is_alert_sample = (frame_number == 1) or (frame_number % alert_interval == 0)

    motion_result = None
    if (is_overlay_sample or is_alert_sample) and motion_gate is not None:
        try:
            motion_result = motion_gate.on_sample_frame(device_id, frame, frame_number)
            if motion_result.triggered and frame_number % 25 == 0:
                logger.debug(
                    '设备 %s 运动门控命中: frame=%s score=%.4f area=%.4f reason=%s',
                    device_id, frame_number, motion_result.score,
                    motion_result.changed_area_ratio, motion_result.reason,
                )
        except Exception as exc:
            logger.warning('设备 %s 运动门控评估失败: %s', device_id, exc)

    if is_overlay_sample:
        _enqueue_keep_latest(
            overlay_detection_queues.get(device_id),
            device_id,
            _build_detection_payload(device_id, frame, frame_number, timestamp),
            queue_size=OVERLAY_DETECTION_QUEUE_SIZE,
            keep_latest=OVERLAY_KEEP_LATEST,
            keep_latest_threshold=OVERLAY_KEEP_LATEST_THRESHOLD,
            queue_label='overlay',
        )

    if task_config and task_config.alert_event_enabled:
        enqueue_alert = is_alert_sample
        if (
            not enqueue_alert
            and motion_gate is not None
            and motion_result is not None
            and motion_result.triggered
            and getattr(motion_gate.config, 'alert_motion_sync', False)
        ):
            enqueue_alert = True
        if enqueue_alert:
            _enqueue_keep_latest(
                alert_detection_queues.get(device_id),
                device_id,
                _build_detection_payload(device_id, frame, frame_number, timestamp),
                queue_size=ALERT_DETECTION_QUEUE_SIZE,
                keep_latest=ALERT_KEEP_LATEST,
                keep_latest_threshold=ALERT_KEEP_LATEST_THRESHOLD,
                queue_label='alert',
            )


def _normalize_detection_class_name(class_name: str) -> str:
    """标准化类别名，便于匹配中英文和不同命名风格。"""
    return str(class_name or '').strip().lower().replace('-', '_').replace(' ', '_')


def _is_face_class(class_name: str) -> bool:
    normalized = _normalize_detection_class_name(class_name)
    return any(keyword in normalized for keyword in FACE_CLASS_KEYWORDS)


def _is_plate_class(class_name: str) -> bool:
    normalized = _normalize_detection_class_name(class_name)
    return any(keyword in normalized for keyword in PLATE_CLASS_KEYWORDS)


def _model_class_name_list(model) -> List[str]:
    """提取模型声明的全部类别名（兼容 ONNXInference.classes_dict 与 Ultralytics .names）。"""
    names = getattr(model, 'classes_dict', None)
    if not names:
        names = getattr(model, 'names', None)
    if isinstance(names, dict):
        return [str(v) for v in names.values()]
    if isinstance(names, (list, tuple)):
        return [str(v) for v in names]
    return []


def _model_is_dedicated_face(model) -> bool:
    """模型是否为“专用人脸/口罩模型”（其声明的全部类别都是人脸类）。"""
    names = _model_class_name_list(model)
    return bool(names) and all(_is_face_class(name) for name in names)


def _model_is_dedicated_plate(model) -> bool:
    """模型是否为“专用车牌模型”（其声明的全部类别都是车牌类）。"""
    names = _model_class_name_list(model)
    return bool(names) and all(_is_plate_class(name) for name in names)


def _should_keep_detection(
    class_name: str,
    *,
    dedicated_face: bool = False,
    dedicated_plate: bool = False,
) -> bool:
    """
    根据任务配置过滤检测类别：
    - 关闭人脸检测时，过滤通用模型“附带”输出的人脸类结果
    - 关闭车牌检测时，过滤通用模型“附带”输出的车牌类结果

    例外：当检测来自“专用人脸/口罩模型”或“专用车牌模型”（模型声明的全部
    类别都是人脸/车牌类）时，说明用户是显式选了这个模型，应保留其结果，
    不受 face_detection_enabled / plate_detection_enabled 开关影响。否则口罩
    模型（类名 face/face_mask）等会因开关关闭而被整条过滤 → 永远 0 目标、
    永不告警。
    """
    if not task_config:
        return True

    if (
        _is_face_class(class_name)
        and not dedicated_face
        and not bool(getattr(task_config, 'face_detection_enabled', True))
    ):
        return False
    if (
        _is_plate_class(class_name)
        and not dedicated_plate
        and not bool(getattr(task_config, 'plate_detection_enabled', True))
    ):
        return False
    return True


def _make_detection_filter(model) -> Callable[[str], bool]:
    """为单个模型构造检测过滤器，专用人脸/车牌模型的结果不受对应开关影响。"""
    dedicated_face = _model_is_dedicated_face(model)
    dedicated_plate = _model_is_dedicated_plate(model)

    def _keep(class_name: str) -> bool:
        return _should_keep_detection(
            class_name,
            dedicated_face=dedicated_face,
            dedicated_plate=dedicated_plate,
        )

    return _keep


def _is_valid_model_file(path: str) -> bool:
    """检查模型文件是否真实存在且非空（避免“下载成功但没落盘/0字节”）"""
    try:
        if not path:
            return False
        if not os.path.exists(path):
            return False
        return os.path.getsize(path) > 0
    except Exception:
        return False


def _build_absolute_url(maybe_path_or_url: str) -> Optional[str]:
    """将 /api/v1/... 之类的路径补全成可下载的 http(s)://... URL"""
    if not maybe_path_or_url:
        return None
    if maybe_path_or_url.startswith('http://') or maybe_path_or_url.startswith('https://'):
        return maybe_path_or_url
    if maybe_path_or_url.startswith('/'):
        # 优先 MinIO Console（9001），其次 AI 代理（与 AI_SERVICE_URL 拼接），再网关
        base = (
            os.getenv('MODEL_DOWNLOAD_BASE_URL')
            or os.getenv('MINIO_CONSOLE_URL')
            or os.getenv('AI_SERVICE_URL')
            or os.getenv('GATEWAY_URL')
            or 'http://localhost:5000'
        )
        if not base.endswith('/'):
            base += '/'
        return urllib.parse.urljoin(base, maybe_path_or_url.lstrip('/'))
    return None


def _normalize_minio_endpoint(raw: str) -> str:
    """Minio 客户端要求 host:port，去掉误配的 scheme。"""
    s = (raw or '').strip()
    for prefix in ('https://', 'http://'):
        if s.lower().startswith(prefix):
            s = s[len(prefix):]
    return s.rstrip('/')


def _download_model_from_minio_direct(bucket_name: str, object_key: str, local_path: str) -> bool:
    """
    在算法服务本机路径落盘（与 AI 服务的 download_model_forVideo 不同：后者写在 AI 容器内，
    跨容器时算法任务会收到 code=0 但本机文件不存在/为空）。
    需配置与 AI 模块一致的 MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY / MINIO_SECURE。
    """
    endpoint = _normalize_minio_endpoint(os.getenv('MINIO_ENDPOINT', '').strip())
    if not endpoint:
        return False
    try:
        from minio import Minio
        from minio.error import S3Error
    except ImportError:
        logger.warning('未安装 minio 包，跳过直连 MinIO 下载')
        return False
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    tmp_path = f"{local_path}.minio.tmp"
    try:
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        client.fget_object(bucket_name, object_key, tmp_path)
        if _is_valid_model_file(tmp_path):
            os.replace(tmp_path, local_path)
            return _is_valid_model_file(local_path)
        logger.warning(f"直连MinIO下载后文件无效: {tmp_path}")
        return False
    except S3Error as e:
        logger.warning(f"直连MinIO下载失败(S3): bucket={bucket_name}, object={object_key}, error={e}")
        return False
    except Exception as e:
        logger.warning(f"直连MinIO下载失败: bucket={bucket_name}, object={object_key}, error={e}")
        return False
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def _download_url_to_file(url: str, dst_path: str, timeout=(5, 300)) -> bool:
    """下载URL到本地文件，成功返回True（会写临时文件再原子替换）"""
    if not url or not dst_path:
        return False
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    tmp_path = f"{dst_path}.tmp"
    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(tmp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        if _is_valid_model_file(tmp_path):
            os.replace(tmp_path, dst_path)
            return _is_valid_model_file(dst_path)
        return False
    except Exception as e:
        logger.warning(f"从URL下载模型失败: url={url}, dst={dst_path}, error={str(e)}")
        return False
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def download_model_file(model_id: int, model_path: str) -> Optional[str]:
    """下载模型文件到本地

    Args:
        model_id: 模型ID（正数表示数据库模型，负数表示默认模型）
        model_path: 模型路径（MinIO URL或本地路径）

    Returns:
        str: 本地模型文件路径，失败返回None
    """
    try:
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # 默认模型映射
        default_model_map = {
            -1: 'yolo11n.pt',
            -2: 'yolov8n.pt',
            -3: 'yolo26n.pt',
        }

        # 如果是负数ID，表示默认模型
        if model_id < 0:
            model_filename = default_model_map.get(model_id)
            if not model_filename:
                logger.error(f"未知的默认模型ID: {model_id}")
                return None

            # 默认模型路径：VIDEO目录下
            local_path = os.path.join(video_root, model_filename)
            if os.path.exists(local_path):
                logger.info(f"默认模型文件已存在: {local_path}")
                return local_path
            else:
                logger.warning(f"默认模型文件不存在: {local_path}，请确保文件已下载")
                return None

        # 正数ID，从数据库或MinIO下载
        # 集群模式：优先读 CephFS 共享缓存
        try:
            from model_resolver import try_resolve_cluster_model_path
            cluster_path = try_resolve_cluster_model_path(model_id)
            if cluster_path:
                logger.info(f"使用集群共享模型: model_id={model_id}, path={cluster_path}")
                return cluster_path
        except ImportError:
            pass

        # 创建模型存储目录
        model_storage_dir = os.path.join(video_root, 'data', 'models', str(model_id))
        os.makedirs(model_storage_dir, exist_ok=True)

        # 从model_path中提取文件名
        if not model_path:
            logger.error(f"模型 {model_id} 的路径为空")
            return None

        # 如果是MinIO URL，需要下载
        if model_path.startswith('/api/v1/buckets/'):
            try:
                parsed = urllib.parse.urlparse(model_path)
                path_parts = parsed.path.split('/')

                # 提取bucket名称
                if len(path_parts) >= 5 and path_parts[3] == 'buckets':
                    bucket_name = path_parts[4]
                else:
                    raise ValueError(f'URL格式不正确: {model_path}')

                # 提取object_key
                query_params = urllib.parse.parse_qs(parsed.query)
                object_key = query_params.get('prefix', [None])[0]

                if not object_key:
                    raise ValueError(f'URL中缺少prefix参数: {model_path}')

                filename = os.path.basename(object_key) or f"model_{model_id}.pt"
                local_path = os.path.join(model_storage_dir, filename)

                # 如果文件已存在，直接返回
                if os.path.exists(local_path):
                    logger.info(f"模型文件已存在，跳过下载: {local_path}")
                    return local_path

                # 优先本容器直连 MinIO（跨容器调用 AI 的 destination_path 会落在 AI 容器，导致本机文件始终无效）
                logger.info(f"开始从MinIO下载模型文件: bucket={bucket_name}, object={object_key}")
                if _download_model_from_minio_direct(bucket_name, object_key, local_path):
                    logger.info(
                        f"✅ 直连MinIO下载模型成功: {local_path} (size={os.path.getsize(local_path)})")
                    return local_path

                import requests
                import os as os_module
                ai_service_url = os_module.getenv('AI_SERVICE_URL', 'http://localhost:5000')
                try:
                    response = requests.post(
                        f"{ai_service_url}/model/download_model_forVideo",
                        headers={'X-Authorization': f'Bearer {os.getenv("JWT_TOKEN", "")}'},
                        json={
                            'bucket_name': bucket_name,
                            'object_key': object_key,
                            'destination_path': local_path
                        },
                        timeout=(5, 300)
                    )
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('code') == 0:
                            if _is_valid_model_file(local_path):
                                logger.debug(f'模型下载完成: {local_path} (size={os.path.getsize(local_path)})')
                                return local_path
                            else:
                                size = None
                                try:
                                    size = os.path.getsize(local_path) if os.path.exists(local_path) else None
                                except Exception:
                                    pass
                                logger.error(f"下载返回成功但文件无效: {local_path} (size={size})，将尝试HTTP直链下载")

                                abs_url = _build_absolute_url(model_path)
                                if abs_url and _download_url_to_file(abs_url, local_path):
                                    logger.info(
                                        f"✅ 通过HTTP直链下载模型成功: {local_path} (size={os.path.getsize(local_path)})")
                                    return local_path
                                return None
                        else:
                            logger.warning(f"模型下载失败: {result}")
                            return None
                    else:
                        try:
                            err = response.json()
                            logger.warning(f"模型下载失败: {err}")
                        except:
                            logger.warning(f"模型下载失败: HTTP {response.status_code}, {response.text}")
                        return None
                except Exception as e:
                    logger.warning(f"模型下载异常: {str(e)}")
                    return None
                return None

            except Exception as e:
                logger.error(f"解析MinIO URL失败: {str(e)}", exc_info=True)
                return None
        else:
            # 本地路径
            if os.path.isabs(model_path):
                local_path = model_path
            else:
                local_path = os.path.join(video_root, model_path)

            if os.path.exists(local_path):
                logger.info(f"模型文件已存在: {local_path}")
                return local_path
            else:
                logger.error(f"模型文件不存在: {local_path}")
                return None

    except Exception as e:
        logger.error(f"下载模型文件失败: model_id={model_id}, error={str(e)}", exc_info=True)
        return None


def load_yolo_models(model_ids: List[int]) -> Dict[int, Any]:
    """加载YOLO模型列表

    Args:
        model_ids: 模型ID列表（正数表示数据库模型，负数表示默认模型）

    Returns:
        Dict[int, YOLO]: 模型字典 {model_id: YOLO模型实例}
    """
    global yolo_model_devices, yolo_model_meta
    yolo_model_devices.clear()
    yolo_model_meta.clear()
    try:
        from ultralytics import YOLO

        models = {}

        for model_id in model_ids:
            try:
                model_api_class_names = None
                # 默认模型映射
                default_model_map = {
                    -1: 'yolo11n.pt',
                    -2: 'yolov8n.pt',
                    -3: 'yolo26n.pt',
                }

                # 如果是负数ID，表示默认模型
                if model_id < 0:
                    model_filename = default_model_map.get(model_id)
                    if not model_filename:
                        logger.warning(f"未知的默认模型ID: {model_id}，跳过")
                        continue

                    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    model_path = os.path.join(video_root, model_filename)

                    if not os.path.exists(model_path):
                        logger.warning(f"默认模型文件不存在: {model_path}，尝试从ultralytics下载")
                        # 尝试从ultralytics下载（如果本地不存在）
                        model_path = model_filename  # ultralytics会自动下载
                else:
                    # 正数ID，从数据库获取模型信息
                    import requests
                    import os as os_module
                    ai_service_url = os_module.getenv('AI_SERVICE_URL', 'http://localhost:5000')

                    try:
                        response = requests.get(
                            f"{ai_service_url}/model/{model_id}",
                            headers={'X-Authorization': f'Bearer {os_module.getenv("JWT_TOKEN", "")}'},
                            timeout=5
                        )
                        if response.status_code == 200:
                            model_data = response.json()
                            if model_data.get('code') == 0:
                                model_info = model_data.get('data', {})
                                model_path = model_info.get('model_path') or model_info.get('onnx_model_path')
                                model_api_class_names = (
                                    model_info.get('classNames') or model_info.get('class_names')
                                )

                                if not model_path:
                                    logger.warning(f"模型 {model_id} 没有模型路径，跳过")
                                    continue

                                # 下载模型文件到本地
                                local_path = download_model_file(model_id, model_path)
                                if local_path:
                                    model_path = local_path
                                else:
                                    # 兜底：如果仍是 /api/v1/...，尝试HTTP下载到本地再加载，避免把接口路径当成本地文件
                                    if isinstance(model_path, str) and model_path.startswith('/api/v1/buckets/'):
                                        video_root = os.path.dirname(
                                            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                                        model_storage_dir = os.path.join(video_root, 'data', 'models', str(model_id))
                                        os.makedirs(model_storage_dir, exist_ok=True)

                                        # 从prefix提取文件名
                                        filename = f"model_{model_id}.pt"
                                        try:
                                            parsed = urllib.parse.urlparse(model_path)
                                            query_params = urllib.parse.parse_qs(parsed.query)
                                            object_key = query_params.get('prefix', [None])[0]
                                            if object_key:
                                                filename = os.path.basename(object_key) or filename
                                        except Exception:
                                            pass
                                        fallback_local = os.path.join(model_storage_dir, filename)

                                        abs_url = _build_absolute_url(model_path)
                                        if abs_url and _download_url_to_file(abs_url, fallback_local):
                                            model_path = fallback_local
                                            logger.info(
                                                f"✅ 兜底HTTP下载成功，将使用本地模型文件加载: model_id={model_id}, path={model_path}")
                                        else:
                                            logger.error(
                                                f"模型 {model_id} 下载失败（落盘/直链均失败），跳过该模型以避免服务退出: {model_path}")
                                            continue
                                    else:
                                        logger.warning(f"模型 {model_id} 下载失败，尝试使用原始路径")
                            else:
                                logger.warning(f"获取模型 {model_id} 信息失败: {model_data.get('msg')}")
                                continue
                        else:
                            logger.warning(f"获取模型 {model_id} 信息失败: HTTP {response.status_code}")
                            continue
                    except Exception as e:
                        logger.warning(f"获取模型 {model_id} 信息异常: {str(e)}")
                        continue

                model_path_str = str(model_path)
                if model_path_str.lower().endswith('.onnx'):
                    gpu_id = resolve_onnx_gpu_id(model_id)
                    logger.info(f"正在加载ONNX模型: model_id={model_id}, path={model_path}, gpu_id={gpu_id}")
                    onnx_model = ONNXInference(
                        model_path_str,
                        conf_threshold=_get_detect_conf(),
                        iou_threshold=0.45,
                        device_id=gpu_id,
                        api_class_names=model_api_class_names,
                    )
                    models[model_id] = onnx_model
                    yolo_model_devices[model_id] = (
                        f'onnx:cuda:{gpu_id}' if gpu_id is not None else 'onnx:cpu'
                    )
                    logger.info(
                        f"✅ ONNX模型加载成功: model_id={model_id}, classes={onnx_model.classes_dict}, "
                        f"providers={onnx_model.providers}"
                    )
                else:
                    logger.info(f"正在加载YOLO模型: model_id={model_id}, path={model_path}")
                    _check_ultralytics_for_yolo26(model_path, model_id)
                    yolo_model = YOLO(model_path_str)
                    infer_device = get_infer_device(model_id)
                    models[model_id] = yolo_model
                    yolo_model_devices[model_id] = infer_device
                    yolo26 = is_yolo26_model(
                        yolo_model, model_path=model_path_str, model_id=model_id,
                    )
                    end2end = is_end2end_ultralytics_model(yolo_model) or yolo26
                    inner = getattr(yolo_model, 'model', None)
                    raw_end2end = bool(getattr(inner, 'end2end', False)) if inner else False
                    yaml_end2end = bool(
                        isinstance(getattr(inner, 'yaml', None), dict)
                        and inner.yaml.get('end2end')
                    )
                    yolo_model_meta[model_id] = {
                        'yolo26': yolo26,
                        'end2end': end2end,
                        'path': model_path_str,
                    }
                    try:
                        import ultralytics as _ultra
                        ultra_ver = getattr(_ultra, '__version__', 'unknown')
                    except Exception:
                        ultra_ver = 'unknown'
                    warmup_imgsz = int(os.getenv('YOLO_IMG_SIZE', '640'))
                    try:
                        warmup_model_detection(
                            yolo_model,
                            infer_device=infer_device,
                            imgsz=warmup_imgsz,
                            conf=_get_detect_conf(end2end=end2end, yolo26=yolo26),
                            iou=YOLO_DETECT_IOU,
                        )
                        logger.info(f"✅ YOLO模型预热完成: model_id={model_id}")
                    except Exception as warmup_exc:
                        logger.warning(f"YOLO模型预热失败 model_id={model_id}: {warmup_exc}")
                    logger.info(
                        f"✅ YOLO模型加载成功: model_id={model_id}, infer_device={infer_device}, "
                        f"yolo26={yolo26}, end2end={end2end} (attr={raw_end2end}, yaml={yaml_end2end}), "
                        f"ultralytics={ultra_ver}, detect_conf={_get_detect_conf(end2end=end2end, yolo26=yolo26)}, "
                        f"1080p_imgsz={os.getenv('YOLO26_IMG_SIZE', '1280')}"
                    )

            except Exception as e:
                logger.error(f"❌ 加载YOLO模型失败: model_id={model_id}, error={str(e)}", exc_info=True)
                continue

        return models

    except Exception as e:
        logger.error(f"加载YOLO模型列表失败: {str(e)}", exc_info=True)
        return {}


def load_task_config():
    """从数据库加载任务配置（重启时会重新加载，确保获取最新的摄像头信息）"""
    global task_config, yolo_models, yolo_model_devices, tracker, _sam_config, _sam_client
    global motion_gate

    try:
        logger.info(f"🔄 正在从数据库重新加载任务配置: task_id={TASK_ID}")
        # PostgreSQL 任意一条 SQL 失败后，当前事务会一直处于 aborted 状态，
        # 必须先 rollback 才能继续查询。启动阶段数据库自动迁移可能与本进程
        # 并行执行，因此每次重试前都先结束上一次事务，确保迁移完成后可恢复。
        db_session.rollback()

        # 刷新数据库会话，确保获取最新数据
        db_session.expire_all()

        task = db_session.query(AlgorithmTask).filter_by(id=TASK_ID).first()
        if not task:
            logger.error(f"任务 {TASK_ID} 不存在")
            return False

        task_config = task

        _apply_runtime_sampling_config(task)

        # SAM 补充识别配置
        try:
            from app.utils.sam_supplement import load_sam_config_from_env, SamClient
            _sam_config = load_sam_config_from_env()
            if not _sam_config.get('enabled') and getattr(task, 'sam_supplement_enabled', False):
                raw = getattr(task, 'sam_supplement_config', None)
                cfg = json.loads(raw) if raw and isinstance(raw, str) else (raw or {})
                _sam_config = {
                    'enabled': True,
                    'pipeline_mode': cfg.get('pipeline_mode', 'none'),
                    'text_prompts': cfg.get('text_prompts') or [],
                    'conf': float(cfg.get('conf', 0.45)),
                    'trigger': cfg.get('trigger', 'on_interval'),
                    'interval_frames': int(cfg.get('interval_frames', 25)),
                    'merge_iou': float(cfg.get('merge_iou', 0.5)),
                    'return_masks': bool(cfg.get('return_masks', True)),
                }
            _sam_client = SamClient() if _sam_config.get('enabled') else None
            if _sam_config.get('enabled'):
                logger.info(f"✅ SAM 补充识别已启用: mode={_sam_config.get('pipeline_mode')}")
        except Exception as e:
            logger.warning(f"SAM 补充配置加载失败: {e}")
            _sam_config = {'enabled': False}
            _sam_client = None

        # 解析模型ID列表
        model_ids = []
        if task.model_ids:
            try:
                model_ids = json.loads(task.model_ids) if isinstance(task.model_ids, str) else task.model_ids
            except:
                pass

        if not model_ids:
            logger.error(f"任务 {TASK_ID} 没有配置模型ID列表")
            return False

        # 加载YOLO模型列表
        yolo_models = load_yolo_models(model_ids)
        if not yolo_models:
            logger.error(f"任务 {TASK_ID} 没有成功加载任何模型")
            return False

        logger.info(f"✅ 成功加载 {len(yolo_models)} 个YOLO模型")

        # 从摄像头列表获取输入流地址（支持RTSP和RTMP）和RTMP输出流地址（重新加载，确保获取最新地址）
        # 注意：rtmp_input_url和rtmp_output_url字段已废弃，改为从摄像头列表获取
        device_streams = {}
        if task.devices:
            # 刷新设备关联关系，确保获取最新的设备信息
            db_session.refresh(task)
            for device in task.devices:
                # 刷新设备对象，确保获取最新的source和ai_rtmp_stream
                db_session.refresh(device)
                # 输入流地址（支持RTSP/RTMP，以及通过gb28181://虚拟源动态解析）
                rtsp_url = resolve_gb28181_source(device.source, logger=logger) if device.source else None
                if not rtsp_url:
                    logger.warning(f"设备 {device.id} 未获取到可用输入流地址，跳过该设备")
                    continue
                # AI RTMP 输出流（国标设备同步时可能仅留空 live 地址，此处含按 device_id 生成的兜底）
                playback_rtmp_url = resolve_device_ai_rtmp_stream(device)
                rtmp_url = _resolve_ai_rtmp_push_url(device.id, playback_rtmp_url)
                device_streams[device.id] = {
                    'rtsp_url': rtsp_url,  # 输入流地址
                    'rtmp_url': rtmp_url,  # AI FFmpeg 推流地址（本机推 127.0.0.1/ai）
                    'playback_rtmp_url': playback_rtmp_url,  # 播放地址（外网 IP，供日志对照）
                    'device_name': device.name or device.id,
                    'is_gb28181': bool(device.source and device.source.strip().lower().startswith('gb28181://')),
                    'original_source': device.source,  # 原始源地址（用于GB28181重连时重新解析）
                }
                input_type = "RTSP" if rtsp_url and rtsp_url.startswith(
                    'rtsp://') else "RTMP" if rtsp_url and rtsp_url.startswith('rtmp://') else "输入流"
                if playback_rtmp_url and playback_rtmp_url != rtmp_url:
                    logger.info(
                        f"📹 设备 {device.id} ({device.name or device.id}): {input_type}={rtsp_url}, "
                        f"AI推流={rtmp_url}, 播放地址={playback_rtmp_url}")
                else:
                    logger.info(
                        f"📹 设备 {device.id} ({device.name or device.id}): {input_type}={rtsp_url}, AI RTMP输出={rtmp_url}")

        # 将设备流地址信息存储到task_config中（通过动态属性）
        task_config.device_streams = device_streams

        # 为每个摄像头初始化独立资源（热更新时不重置帧计数与检测队列，避免检测中断）
        for device_id, stream_info in device_streams.items():
            if device_id not in frame_counts:
                frame_counts[device_id] = 0
            if device_id not in overlay_detection_queues:
                overlay_detection_queues[device_id] = queue.Queue(maxsize=OVERLAY_DETECTION_QUEUE_SIZE)
            if device_id not in alert_detection_queues:
                alert_detection_queues[device_id] = queue.Queue(maxsize=ALERT_DETECTION_QUEUE_SIZE)
            if device_id not in device_latest_overlay_locks:
                device_latest_overlay_locks[device_id] = threading.Lock()

            # 初始化追踪器（叠框/告警共用；OVERLAY_USE_TRACKING 默认开启）
            if (task.tracking_enabled or OVERLAY_USE_TRACKING) and device_id not in trackers:
                trackers[device_id] = SimpleTracker(
                    similarity_threshold=task.tracking_similarity_threshold,
                    max_age=task.tracking_max_age,
                    smooth_alpha=task.tracking_smooth_alpha
                )
                logger.info(f"设备 {device_id} 追踪器初始化成功")

        logger.info(f"任务配置加载成功: {task.task_name}, 模型IDs: {model_ids}, 关联设备数: {len(device_streams)}")
        pod_ip = os.getenv('POD_IP', '').strip()
        logger.info(
            'AI推流目标解析: POD_IP=%s, SRS_RTMP=%s, SRS_API=%s',
            pod_ip or '(未设置，将使用 device.ai_rtmp_stream 外网地址)',
            _srs_rtmp_port(),
            _srs_api_port(),
        )
        for dev_id, info in device_streams.items():
            logger.info('  设备 %s AI推流 -> %s', dev_id, info.get('rtmp_url'))
        logger.info(
            f"   YOLO检测阈值: conf={_get_detect_conf(end2end=_any_loaded_model_is_end2end(), yolo26=_any_loaded_model_is_yolo26())} "
            f"(env YOLO_DETECT_CONF), iou={YOLO_DETECT_IOU}, imgsz={YOLO_IMG_SIZE}, "
            f"yolo26_1080p_imgsz={os.getenv('YOLO26_IMG_SIZE', '1280')}"
        )

        if task.tracking_enabled or OVERLAY_USE_TRACKING:
            logger.info(f"已为 {len(trackers)} 个设备初始化追踪器")

        return True
    except Exception as e:
        logger.error(f"加载任务配置失败: {str(e)}", exc_info=True)
        try:
            db_session.rollback()
        except Exception as rollback_error:
            logger.error(f"任务配置加载失败后回滚数据库事务失败: {rollback_error}", exc_info=True)
            db_session.remove()
        return False


def _ensure_alert_workers_started():
    """告警事件启用后动态拉起告警检测线程（配置热更新）。"""
    global alert_executor
    if alert_executor is not None:
        return
    if not task_config or not task_config.alert_event_enabled:
        return
    logger.info(f"🔔 检测到告警事件已启用，启动 {ALERT_WORKER_THREADS} 个告警检测线程...")
    alert_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=ALERT_WORKER_THREADS,
        thread_name_prefix='alert_worker',
    )
    for worker_id in range(1, ALERT_WORKER_THREADS + 1):
        alert_executor.submit(alert_detection_worker, worker_id)
        logger.info(f"   ✅ 告警检测线程 {worker_id} 已启动（热更新）")


def _task_config_reload_worker(interval_sec: int = 30):
    """定期重载任务配置，使告警开关等变更在重启任务后无需杀进程即可生效。"""
    while not stop_event.is_set():
        for _ in range(max(5, interval_sec)):
            if stop_event.is_set():
                return
            time.sleep(1)
        try:
            prev_alert_enabled = bool(task_config and task_config.alert_event_enabled)
            if not load_task_config():
                continue
            now_alert_enabled = bool(task_config and task_config.alert_event_enabled)
            if now_alert_enabled and not prev_alert_enabled:
                _ensure_alert_workers_started()
            elif now_alert_enabled != prev_alert_enabled:
                logger.info(
                    f"任务配置已热更新: alert_event_enabled {prev_alert_enabled} -> {now_alert_enabled}"
                )
        except Exception as exc:
            logger.warning(f"任务配置热更新失败: {exc}")


def send_alert_event_async(alert_data: Dict):
    """异步发送告警事件到 sink hook 接口（后台线程）"""

    def _send():
        try:
            if not task_config or not task_config.alert_event_enabled:
                logger.warning(f"⚠️ 告警事件发送被跳过：task_config={task_config is not None}, alert_event_enabled={task_config.alert_event_enabled if task_config else None}, device_id={alert_data.get('device_id')}")
                return
            
            logger.info(f"📤 开始发送告警事件: device_id={alert_data.get('device_id')}, object={alert_data.get('object')}, URL={ALERT_HOOK_URL}")

            # 通过 HTTP 发送告警事件到 sink hook 接口
            # sink 会负责将告警投入 Kafka
            try:
                # 标记为实时算法任务
                alert_data['task_type'] = 'realtime'
                # 检测开关由算法服务透传给 alert_hook_service，避免 alert_hook_service 再查库
                if 'face_detection_enabled' not in alert_data:
                    alert_data['face_detection_enabled'] = bool(
                        getattr(task_config, 'face_detection_enabled', False)
                    )
                if 'plate_detection_enabled' not in alert_data:
                    alert_data['plate_detection_enabled'] = bool(
                        getattr(task_config, 'plate_detection_enabled', False)
                    )
                response = requests.post(
                    ALERT_HOOK_URL,
                    json=alert_data,
                    timeout=5,
                    headers={'Content-Type': 'application/json'}
                )
                hook_result = {}
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        hook_result = body.get('data') if isinstance(body.get('data'), dict) else body
                except Exception:
                    hook_result = {}

                hook_status = hook_result.get('status')
                if response.status_code == 200 and hook_status in (None, 'success'):
                    mode = hook_result.get('mode', 'kafka')
                    alert_id = hook_result.get('alert_id')
                    logger.info(
                        f"✅ 告警事件已成功处理: device_id={alert_data.get('device_id')}, "
                        f"object={alert_data.get('object')}, mode={mode}"
                        + (f", alert_id={alert_id}" if alert_id else "")
                    )
                elif response.status_code == 200 and hook_status in ('skipped', 'suppressed'):
                    logger.warning(
                        f"⚠️ 告警被 hook 跳过: device_id={alert_data.get('device_id')}, "
                        f"status={hook_status}, reason={hook_result.get('reason')}"
                    )
                else:
                    logger.warning(
                        f"❌ 发送告警事件到 hook 失败: status_code={response.status_code}, "
                        f"hook_status={hook_status}, response={response.text}, "
                        f"device_id={alert_data.get('device_id')}"
                    )
            except requests.exceptions.RequestException as e:
                logger.warning(f"❌ 发送告警事件到 sink hook 异常: {str(e)}, URL={ALERT_HOOK_URL}, device_id={alert_data.get('device_id')}")
        except Exception as e:
            logger.error(f"发送告警事件失败: {str(e)}", exc_info=True)

    # 在后台线程中异步执行
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


def try_send_alert_for_detections(
    device_id: str,
    device_name: str,
    frame_number: int,
    detections: list,
    frame_for_image: np.ndarray,
    current_timestamp: float,
    *,
    log_suffix: str = "",
) -> None:
    """在具备真实检测结果时按抑制策略发送告警（用于输出帧或检测迟达补发）。"""
    from app.utils.alert_class_filter import filter_detections_for_alert, get_task_alert_class_names

    detections = filter_detections_for_alert(
        detections,
        get_task_alert_class_names(task_config),
    )
    if not detections or not task_config or not task_config.alert_event_enabled:
        return
    current_time = time.time()
    with alert_time_lock:
        last_time = last_alert_time.get(device_id, 0)
        time_since_last_alert = current_time - last_time
        suppress_interval = _alert_event_suppress_seconds()
        if suppress_interval > 0 and time_since_last_alert < suppress_interval:
            logger.info(
                f"⏸️  设备 {device_id} 告警抑制{log_suffix}：距离上次推送仅 {time_since_last_alert:.2f} 秒，跳过（需间隔 {suppress_interval} 秒），帧 {frame_number}，{len(detections)} 个目标"
            )
            return
        last_alert_time[device_id] = current_time
        logger.info(
            f"🔔 设备 {device_id} 准备发送告警{log_suffix}：帧 {frame_number}，{len(detections)} 个目标，距上次告警 {time_since_last_alert:.2f} 秒"
        )
    try:
        object_counts = {}
        all_detections_info = []
        for det in detections:
            class_name = det.get('class_name', 'unknown')
            object_counts[class_name] = object_counts.get(class_name, 0) + 1
            all_detections_info.append({
                'track_id': det.get('track_id', 0),
                'class_name': class_name,
                'confidence': det.get('confidence', 0),
                'bbox': det.get('bbox', []),
                'first_seen_time': datetime.fromtimestamp(
                    det.get('first_seen_time', current_timestamp), tz=BEIJING_TZ).isoformat() if det.get(
                    'first_seen_time') else None,
                'duration': det.get('duration', 0)
            })
        primary_object = max(object_counts.items(), key=lambda x: x[1])[0] if object_counts else 'unknown'
        image_path = save_alert_image(
            frame_for_image,
            device_id,
            frame_number,
            detections[0] if detections else {}
        )
        algorithm_name = task_config.task_name if task_config and hasattr(task_config, 'task_name') else 'detection'
        correlation_id = str(uuid.uuid4())
        alert_data = {
            'object': primary_object,
            'event': algorithm_name,
            'device_id': device_id,
            'device_name': device_name,
            # GB28181/实时算法统一走 realtime，便于 hook 侧选择 Kafka 主题与任务查询（snap/snapshot 另有分支）
            'task_type': 'realtime',
            'correlation_id': correlation_id,
            'face_detection_enabled': bool(getattr(task_config, 'face_detection_enabled', False)),
            'plate_detection_enabled': bool(getattr(task_config, 'plate_detection_enabled', False)),
            'time': datetime.fromtimestamp(current_timestamp, tz=BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S'),
            'information': json.dumps({
                'total_count': len(detections),
                'object_counts': object_counts,
                'detections': all_detections_info,
                'frame_number': frame_number,
                'correlation_id': correlation_id,
            }),
            'image_path': image_path if image_path else None,
        }
        send_alert_event_async(alert_data)
        try_send_face_matching_for_frame(
            device_id=device_id,
            device_name=device_name,
            frame_for_image=frame_for_image,
            frame_number=frame_number,
            correlation_id=correlation_id,
            source_event=algorithm_name,
        )
        try_send_plate_matching_for_frame(
            device_id=device_id,
            device_name=device_name,
            frame_for_image=frame_for_image,
            frame_number=frame_number,
            correlation_id=correlation_id,
        )
        extra = f" {log_suffix}" if log_suffix else ""
        logger.info(f"📨 已发送告警事件{extra}：帧 {frame_number}，{len(detections)} 个目标（{object_counts}）")
    except Exception as e:
        logger.error(f"发送告警失败{log_suffix}: {str(e)}", exc_info=True)


def cleanup_alert_images(alert_image_dir: str, max_images: int = 300, keep_ratio: float = 0.1):
    """清理告警图片目录，当图片数量超过限制时，删除最旧的图片

    Args:
        alert_image_dir: 告警图片目录路径
        max_images: 最大图片数量，超过此数量时触发清理（默认300张）
        keep_ratio: 保留比例（0.0-1.0），例如0.1表示保留最新的10%（删除90%）
    """
    try:
        if not os.path.exists(alert_image_dir):
            return

        # 获取所有jpg图片文件
        image_files = []
        for filename in os.listdir(alert_image_dir):
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                file_path = os.path.join(alert_image_dir, filename)
                if os.path.isfile(file_path):
                    # 获取文件修改时间
                    mtime = os.path.getmtime(file_path)
                    image_files.append((file_path, mtime))

        total_images = len(image_files)

        # 如果图片数量未超过限制，不需要清理
        if total_images <= max_images:
            return

        # 按修改时间排序（最旧的在前）
        image_files.sort(key=lambda x: x[1])

        # 计算需要保留的图片数量（最新的10%）
        keep_count = max(1, int(total_images * keep_ratio))

        # 计算需要删除的图片数量（最旧的90%）
        delete_count = total_images - keep_count

        # 删除最旧的图片
        deleted_count = 0
        for i in range(delete_count):
            try:
                file_path = image_files[i][0]
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"删除告警图片失败: {file_path}, 错误: {str(e)}")

        if deleted_count > 0:
            logger.info(
                f"告警图片清理完成: 目录={alert_image_dir}, 总数={total_images}, 删除={deleted_count}, 保留={keep_count}")
    except Exception as e:
        logger.error(f"清理告警图片失败: {str(e)}", exc_info=True)


def cleanup_srs_recordings(srs_record_dir: str | None = None, max_recordings: int = 500, keep_ratio: float = 0.1):
    """清理 SRS 录像目录（委托 VIDEO 回放磁盘守护服务）。"""
    try:
        if not srs_record_dir:
            try:
                from app.services.playback_disk_guard_service import get_srs_record_dir
                srs_record_dir = get_srs_record_dir()
            except Exception:
                from app.services.media_dvr_utils import DEFAULT_SRS_HOST_DATA_ROOT
                srs_record_dir = os.path.join(
                    os.path.expanduser(DEFAULT_SRS_HOST_DATA_ROOT), 'playbacks',
                )
        os.environ.setdefault('SRS_RECORD_DIR', srs_record_dir)
        from app.services.playback_disk_guard_service import run_playback_disk_guard
        run_playback_disk_guard()
    except Exception as e:
        logger.error(f"清理SRS录像失败: {str(e)}", exc_info=True)


def save_alert_image(frame: np.ndarray, device_id: str, frame_number: int, detection: Dict) -> Optional[str]:
    """保存告警图片到本地目录

    Args:
        frame: 图片帧
        device_id: 设备ID
        frame_number: 帧号
        detection: 检测结果字典

    Returns:
        图片保存路径，如果保存失败返回None
    """
    try:
        # 创建告警图片保存目录（ALERT_IMAGES_DIR=/app/alert_images 与 iot-sink 挂载对齐）
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        images_root = resolve_alert_images_root(video_root)
        alert_image_dir = os.path.join(images_root, f'task_{TASK_ID}', device_id)
        os.makedirs(alert_image_dir, exist_ok=True)

        # 生成图片文件名（包含时间戳和帧号）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        track_id = detection.get('track_id', 0)
        class_name = detection.get('class_name', 'unknown')
        image_filename = f"{timestamp}_frame{frame_number}_track{track_id}_{class_name}.jpg"
        image_path = os.path.join(alert_image_dir, image_filename)

        # 保存图片
        cv2.imwrite(image_path, frame)

        logger.debug(f"告警图片已保存: {image_path}")

        # 保存后检查并清理旧图片（超过300张时，删除最旧的90%）
        cleanup_alert_images(alert_image_dir, max_images=300, keep_ratio=0.1)

        return image_path
    except Exception as e:
        logger.error(f"保存告警图片失败: {str(e)}", exc_info=True)
        return None


def _resolve_face_matching_threshold() -> Optional[float]:
    if not task_config:
        return None
    threshold = getattr(task_config, 'face_matching_threshold', None)
    if threshold is not None:
        return float(threshold)
    from models import AlgorithmTask, FaceLibrary
    lib_ids = AlgorithmTask._parse_library_ids(getattr(task_config, 'face_library_ids', None))
    if lib_ids:
        library = FaceLibrary.query.get(lib_ids[0])
        if library is not None and getattr(library, 'similarity_threshold', None) is not None:
            return float(library.similarity_threshold)
    return None


def try_send_face_matching_for_frame(
    device_id: str,
    device_name: str,
    frame_for_image: np.ndarray,
    frame_number: int,
    correlation_id: Optional[str] = None,
    source_event: Optional[str] = None,
) -> None:
    """启用人脸匹配时，将帧送入独立人脸抓取队列（不阻塞主算法链路）"""
    if not task_config or not bool(getattr(task_config, 'face_matching_enabled', False)):
        return
    from models import AlgorithmTask
    library_ids = AlgorithmTask._parse_library_ids(getattr(task_config, 'face_library_ids', None))
    if not library_ids:
        logger.warning("人脸匹配已开启但未配置人脸库，跳过投递")
        return
    if not face_capture_queue_running():
        logger.warning("人脸抓取队列未启动，跳过帧 %s", frame_number)
        return

    enqueue_face_capture(
        frame=frame_for_image,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        task_id=TASK_ID,
        task_name=getattr(task_config, 'task_name', ''),
        task_type='realtime',
        library_ids=library_ids,
        threshold=_resolve_face_matching_threshold(),
        publish_url=FACE_MATCHING_PUBLISH_URL,
        correlation_id=correlation_id,
        source_event=source_event,
    )


def try_send_plate_matching_for_frame(
    device_id: str,
    device_name: str,
    frame_for_image: np.ndarray,
    frame_number: int,
    correlation_id: Optional[str] = None,
) -> None:
    """启用车牌匹配时，将帧送入独立车牌抓取队列（不阻塞主算法链路）"""
    if not task_config or not bool(getattr(task_config, 'plate_matching_enabled', False)):
        return
    from models import AlgorithmTask
    library_ids = AlgorithmTask._parse_library_ids(getattr(task_config, 'plate_library_ids', None))
    if not library_ids:
        logger.warning("车牌匹配已开启但未配置车牌库，跳过投递")
        return
    if not plate_capture_queue_running():
        logger.warning("车牌抓取队列未启动，跳过帧 %s", frame_number)
        return

    enqueue_plate_capture(
        frame=frame_for_image,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        task_id=TASK_ID,
        task_name=getattr(task_config, 'task_name', ''),
        task_type='realtime',
        library_ids=library_ids,
        publish_url=PLATE_MATCHING_PUBLISH_URL,
        correlation_id=correlation_id,
    )


def send_heartbeat():
    """发送心跳到VIDEO服务"""
    try:
        import socket
        import os as os_module

        # 获取服务器IP
        server_ip = os_module.getenv('POD_IP', '')
        if not server_ip:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                server_ip = s.getsockname()[0]
                s.close()
            except:
                server_ip = 'localhost'

        # 获取进程ID
        process_id = os_module.getpid()

        # 构建日志路径
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_base_dir = os.path.join(video_root, 'logs')
        log_path = os.path.join(log_base_dir, f'task_{TASK_ID}')

        heartbeat_url = os_module.getenv('VIDEO_HEARTBEAT_URL')
        if not heartbeat_url:
            control_url = os_module.getenv('VIDEO_CONTROL_URL', '').rstrip('/')
            if control_url:
                heartbeat_url = f'{control_url}/algorithm/heartbeat/realtime'
            else:
                heartbeat_url = f"http://localhost:{VIDEO_SERVICE_PORT}/video/algorithm/heartbeat/realtime"

        # 发送心跳
        response = requests.post(
            heartbeat_url,
            json={
                'task_id': TASK_ID,
                'server_ip': server_ip,
                'port': None,  # 实时算法服务不监听端口
                'process_id': process_id,
                'log_path': log_path
            },
            timeout=5
        )
        response.raise_for_status()
        logger.debug(f"心跳上报成功: task_id={TASK_ID}")
    except Exception as e:
        logger.warning(f"心跳上报失败: {str(e)}")


def heartbeat_worker():
    """心跳上报工作线程"""
    logger.info("💓 心跳上报线程启动")
    while not stop_event.is_set():
        try:
            send_heartbeat()
            # 每10秒发送一次心跳
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(1)
        except Exception as e:
            logger.error(f"心跳上报线程异常: {str(e)}", exc_info=True)
            time.sleep(10)
    logger.info("💓 心跳上报线程停止")


def srs_recording_cleanup_worker():
    """SRS录像清理工作线程"""
    logger.info("🧹 SRS录像清理线程启动")
    try:
        from app.services.playback_disk_guard_service import get_srs_record_dir
        srs_record_dir = get_srs_record_dir()
    except Exception:
        from app.services.media_dvr_utils import DEFAULT_SRS_HOST_DATA_ROOT
        srs_record_dir = os.path.join(os.path.expanduser(DEFAULT_SRS_HOST_DATA_ROOT), 'playbacks')

    while not stop_event.is_set():
        try:
            # 清理SRS录像目录（超过500个时，删除最旧的90%）
            cleanup_srs_recordings(srs_record_dir, max_recordings=500, keep_ratio=0.1)
            # 每60秒检查一次
            for _ in range(60):
                if stop_event.is_set():
                    break
                time.sleep(1)
        except Exception as e:
            logger.error(f"SRS录像清理线程异常: {str(e)}", exc_info=True)
            time.sleep(60)
    logger.info("🧹 SRS录像清理线程停止")


def save_tracking_target(track_data: Dict):
    """处理追踪目标（不保存到数据库，仅用于追踪逻辑）"""
    # 不再保存到数据库，仅用于追踪逻辑处理
    pass


def save_tracking_targets_periodically():
    """定期处理追踪目标（后台线程，不保存到数据库）"""
    logger.info("💾 追踪目标处理线程启动（不保存到数据库）")
    while not stop_event.is_set():
        try:
            if task_config and task_config.tracking_enabled:
                # 仅用于追踪逻辑处理，不保存到数据库
                for device_id, tracker in trackers.items():
                    try:
                        # 获取需要处理的追踪目标（用于追踪逻辑，不保存）
                        tracks_to_process = tracker.get_tracks_for_save()
                        # 这里可以添加其他追踪相关的处理逻辑，但不保存到数据库
                        if tracks_to_process and len(tracks_to_process) > 0:
                            logger.debug(f"设备 {device_id} 有 {len(tracks_to_process)} 个追踪目标需要处理")
                    except Exception as e:
                        logger.error(f"处理设备 {device_id} 的追踪目标失败: {str(e)}", exc_info=True)

            # 每5秒检查一次
            for _ in range(50):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"追踪目标处理线程异常: {str(e)}", exc_info=True)
            time.sleep(5)
    logger.info("💾 追踪目标处理线程停止")


def _resolve_ffmpeg_binary() -> str:
    path = os.getenv('FFMPEG_PATH', '').strip()
    if path and os.path.isfile(path) and os.access(path, os.X_OK):
        return path
    return 'ffmpeg'


_FFMPEG_CAPS: Optional[Dict[str, bool]] = None


def _ffmpeg_supports_input_option(option_flag: str, option_value: str) -> bool:
    try:
        result = subprocess.run(
            [
                _resolve_ffmpeg_binary(),
                '-hide_banner',
                option_flag,
                option_value,
                '-f',
                'lavfi',
                '-i',
                'testsrc=duration=0.01:size=16x16:rate=1',
                '-frames:v',
                '1',
                '-f',
                'null',
                '-',
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        err = (result.stderr or b'').decode('utf-8', errors='ignore')
        return 'Option not found' not in err and 'Unrecognized option' not in err
    except Exception:
        return False


def _get_ffmpeg_caps() -> Dict[str, bool]:
    global _FFMPEG_CAPS
    if _FFMPEG_CAPS is not None:
        return _FFMPEG_CAPS
    caps = {
        'fps_mode': False,
        'max_muxing_queue_size': False,
        'thread_queue_size': False,
        'err_detect': False,
    }
    try:
        result = subprocess.run(
            [_resolve_ffmpeg_binary(), '-hide_banner', '-h', 'full'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=8,
        )
        help_text = result.stdout.decode('utf-8', errors='ignore')
        caps['fps_mode'] = '-fps_mode' in help_text
        caps['max_muxing_queue_size'] = '-max_muxing_queue_size' in help_text
    except Exception as exc:
        logger.warning('FFmpeg 能力探测失败: %s', exc)
    caps['thread_queue_size'] = _ffmpeg_supports_input_option('-thread_queue_size', '512')
    caps['err_detect'] = _ffmpeg_supports_input_option('-err_detect', 'ignore_err')
    _FFMPEG_CAPS = caps
    logger.info(
        'FFmpeg 能力探测: fps_mode=%s, max_muxing_queue_size=%s, thread_queue_size=%s, err_detect=%s',
        caps['fps_mode'], caps['max_muxing_queue_size'],
        caps['thread_queue_size'], caps['err_detect'],
    )
    return caps


def _resolve_realtime_mux_queue_size() -> int:
    """FFmpeg 推流 mux 队列；与 stream_forward max_muxing_queue_size 策略一致。"""
    explicit = os.getenv('REALTIME_MAX_MUXING_QUEUE_SIZE', '').strip()
    if not explicit:
        explicit = os.getenv('STREAM_FORWARD_MAX_MUXING_QUEUE_SIZE', '').strip()
    if explicit:
        try:
            return max(128, int(explicit))
        except (ValueError, TypeError):
            pass
    stream_count = _expected_realtime_stream_count()
    if stream_count >= 100:
        return 2048
    if stream_count >= 32:
        return 1536
    return 1024


def _realtime_ffmpeg_mux_output_options() -> List[str]:
    return ['-avoid_negative_ts', 'make_zero', '-muxdelay', '0', '-muxpreload', '0']


def _disable_hwaccel_globally(reason: str) -> None:
    global _hwaccel_codec, _nvenc_push_verified
    if _hwaccel_codec == 'h264_nvenc':
        _hwaccel_codec = 'libx264'
        _nvenc_push_verified = False
        logger.warning('本节点 NVENC 不可用 (%s)，后续推流统一使用 libx264', reason)


def _verify_nvenc_for_push() -> bool:
    """首次推流前用与生产一致的 scale+NVENC 参数自检（对齐 stream_forward_service）。"""
    global _nvenc_push_verified
    if _nvenc_push_verified is not None:
        return _nvenc_push_verified
    if _hwaccel_codec != 'h264_nvenc':
        _nvenc_push_verified = False
        return False

    _profile_name, _effective_fps, effective_w, effective_h, effective_bitrate, _effective_gop = _get_effective_realtime_stream_params()
    target_w, target_h = align_resolution(effective_w, effective_h, 16)
    gpu_id = get_ffmpeg_gpu_id('nvenc-push-selftest')
    preset = os.getenv('REALTIME_NVENC_PRESET', os.getenv('STREAM_FORWARD_NVENC_PRESET', 'p3'))
    test_cmd = [
        _resolve_ffmpeg_binary(),
        '-y',
        '-hide_banner',
        '-f', 'lavfi',
        '-i', f'testsrc=duration=1:size={target_w}x{target_h}:rate=1',
        '-vf', f'scale={target_w}:{target_h}:flags=bilinear',
        '-c:v', 'h264_nvenc',
        '-preset', preset,
        '-tune', 'll',
        '-gpu', str(gpu_id if gpu_id is not None else 0),
        '-b:v', effective_bitrate,
        '-frames:v', '1',
        '-f', 'null',
        '-',
    ]
    try:
        test_result = subprocess.run(
            test_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        _nvenc_push_verified = test_result.returncode == 0
        if not _nvenc_push_verified:
            err_snip = test_result.stderr.decode('utf-8', errors='ignore').strip()[-400:]
            logger.warning('NVENC 推流自检失败 (%dx%d preset=%s gpu=%s): %s',
                           target_w, target_h, preset, gpu_id, err_snip)
            _disable_hwaccel_globally('NVENC 推流自检未通过')
        else:
            logger.info('NVENC 推流自检通过 (%dx%d, preset=%s, gpu=%s)',
                        target_w, target_h, preset, gpu_id)
    except Exception as exc:
        logger.warning('NVENC 推流自检异常: %s', exc)
        _nvenc_push_verified = False
        _disable_hwaccel_globally('NVENC 推流自检异常')

    return _nvenc_push_verified


def _build_realtime_ffmpeg_push_cmd(
    device_id: str,
    stdin_w: int,
    stdin_h: int,
    rtmp_url: str,
    device_codec: str,
    effective_fps: int,
    effective_w: int,
    effective_h: int,
    effective_bitrate: str,
    effective_gop: int,
) -> tuple:
    """构建 AI 推流 FFmpeg 命令，返回 (cmd, actual_codec, target_w, target_h)。"""
    caps = _get_ffmpeg_caps()
    use_hardware = device_codec == 'h264_nvenc'
    if use_hardware and not _verify_nvenc_for_push():
        use_hardware = False
    actual_codec = 'h264_nvenc' if use_hardware else 'libx264'

    if use_hardware:
        target_w, target_h = align_resolution(effective_w, effective_h, 16)
    else:
        target_w, target_h = effective_w, effective_h

    gop_out = max(1, effective_gop)
    ffmpeg_cmd = [
        _resolve_ffmpeg_binary(),
        "-y",
        "-fflags", "nobuffer+flush_packets+genpts",
        "-flags", "low_delay",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{stdin_w}x{stdin_h}",
        "-r", str(effective_fps),
        "-i", "-",
        "-vf", f"scale={target_w}:{target_h}:flags=bilinear",
    ]

    if caps.get('max_muxing_queue_size'):
        ffmpeg_cmd.extend(['-max_muxing_queue_size', str(_resolve_realtime_mux_queue_size())])

    if use_hardware:
        ffmpeg_gpu_id = get_ffmpeg_gpu_id(device_id)
        ffmpeg_cmd.extend([
            "-c:v", "h264_nvenc",
            "-b:v", effective_bitrate,
            "-preset", os.getenv('REALTIME_NVENC_PRESET', os.getenv('STREAM_FORWARD_NVENC_PRESET', 'p3')),
            "-tune", "ll",
            "-gpu", str(ffmpeg_gpu_id if ffmpeg_gpu_id is not None else 0),
            "-rc", "vbr",
            "-profile:v", "main",
            "-level", "4.0",
            "-g", str(gop_out),
            "-bf", "0",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
        ])
    else:
        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-b:v", effective_bitrate,
            "-preset", FFMPEG_PRESET,
            "-tune", "zerolatency",
            "-profile:v", "main",
            "-g", str(gop_out),
            "-bf", "0",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
        ])
        if FFMPEG_THREADS is not None and str(FFMPEG_THREADS).strip():
            try:
                threads_value = int(FFMPEG_THREADS)
                if threads_value > 0:
                    ffmpeg_cmd.extend(["-threads", str(threads_value)])
            except (ValueError, TypeError):
                pass

    ffmpeg_cmd.extend(_realtime_ffmpeg_mux_output_options())
    ffmpeg_cmd.extend([
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
        rtmp_url,
    ])
    return ffmpeg_cmd, actual_codec, target_w, target_h


def check_hardware_acceleration():
    """检测硬件加速是否可用
    
    Returns:
        tuple: (use_nvenc: bool, use_cuvid: bool, codec_name: str)
    """
    use_nvenc = False
    use_cuvid = False
    codec_name = 'libx264'
    
    # 如果明确设置为none，使用软件编码
    if FFMPEG_HWACCEL == 'none':
        logger.info("硬件加速已禁用，使用软件编码 libx264")
        return False, False, 'libx264'
    
    # 如果明确设置为nvenc，尝试使用硬件编码
    if FFMPEG_HWACCEL in ['nvenc', 'auto']:
        try:
            result = subprocess.run(
                [_resolve_ffmpeg_binary(), '-hide_banner', '-encoders'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            output = result.stdout.decode('utf-8', errors='ignore') + result.stderr.decode('utf-8', errors='ignore')

            if 'h264_nvenc' in output:
                skip_test = os.getenv(
                    'REALTIME_NVENC_SKIP_TEST',
                    os.getenv('STREAM_FORWARD_NVENC_SKIP_TEST', 'true'),
                ).strip().lower() in ('1', 'true', 'yes', 'on')
                if skip_test:
                    use_nvenc = True
                    codec_name = 'h264_nvenc'
                    logger.info(
                        '✅ 检测到 h264_nvenc（跳过 lavfi 自检；首次推流前将做生产参数自检，失败自动回退 libx264）'
                    )
                else:
                    try:
                        test_cmd = [
                            _resolve_ffmpeg_binary(), '-y', '-f', 'lavfi',
                            '-i', 'testsrc=duration=1:size=640x360:rate=1',
                            '-c:v', 'h264_nvenc', '-preset', 'p3', '-b:v', '500k',
                            '-frames:v', '1', '-f', 'null', '-',
                        ]
                        test_result = subprocess.run(
                            test_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=10,
                        )
                        if test_result.returncode == 0:
                            use_nvenc = True
                            codec_name = 'h264_nvenc'
                            logger.info('✅ 检测到硬件加速支持，使用 h264_nvenc 编码器')
                        else:
                            logger.warning('⚠️  h264_nvenc 编码器检测到但测试失败，使用软件编码 libx264')
                    except Exception as test_e:
                        logger.warning(
                            '⚠️  测试 h264_nvenc 编码器时出错: %s，使用软件编码 libx264', test_e,
                        )
            else:
                logger.info("⚠️  未检测到 h264_nvenc 编码器，使用软件编码 libx264")
        except Exception as e:
            logger.warning(f"检测硬件加速时出错: {str(e)}，使用软件编码 libx264")
    
    return use_nvenc, use_cuvid, codec_name


def align_resolution(width: int, height: int, align: int = 16) -> tuple:
    """对齐分辨率（与 stream_forward_service 一致，h264_nvenc 常见要求为 16 对齐）"""
    aligned_width = (width // align) * align
    aligned_height = (height // align) * align
    if aligned_width < align:
        aligned_width = align
    if aligned_height < align:
        aligned_height = align
    return aligned_width, aligned_height


# 在启动时检测硬件加速
_hwaccel_nvenc, _hwaccel_cuvid, _hwaccel_codec = check_hardware_acceleration()
_nvenc_push_verified: Optional[bool] = None


def _srs_api_port() -> int:
    raw = os.getenv('SRS_API_PORT', '1985').strip() or '1985'
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 1985


def _srs_rtmp_port() -> int:
    raw = os.getenv('SRS_RTMP_PORT', '1935').strip() or '1935'
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 1935


def _check_srs_api_ready(host: str, api_port: int, timeout: float = 3.0) -> bool:
    host = (host or '').strip()
    if not host:
        return False
    try:
        resp = requests.get(
            f'http://{host}:{api_port}/api/v1/versions',
            timeout=timeout,
        )
        if resp.status_code != 200:
            return False
        data = resp.json()
        return data.get('code') == 0 and bool(data.get('data'))
    except Exception:
        return False


def _normalize_srs_api_host(host: str) -> str:
    """本机推流时 SRS HTTP API 统一走 loopback（与 stream_forward_service 一致）。"""
    host = (host or '').strip()
    if host in ('srs-server', 'srs', 'SRS', 'localhost', '127.0.0.1'):
        return '127.0.0.1'
    if os.getenv('POD_IP', '').strip():
        return '127.0.0.1'
    return host


def _resolve_ai_rtmp_push_url(device_id: str, device_ai_rtmp_stream: Optional[str] = None) -> Optional[str]:
    """解析 AI 推流 FFmpeg 地址。

    远程分片在节点本机推 SRS，固定走 127.0.0.1（避免外网 IP 回环/on_publish 误判）；
    播放地址仍由 stream_url_sync_service 写入 device.ai_rtmp_stream（外网 IP）。
    """
    pod_ip = os.getenv('POD_IP', '').strip()
    if pod_ip:
        rtmp_port = _srs_rtmp_port()
        return f'rtmp://127.0.0.1:{rtmp_port}/ai/{device_id}'

    rtmp_url = (device_ai_rtmp_stream or '').strip()
    return rtmp_url or None


def check_rtmp_server_connection(rtmp_url: str) -> bool:
    """检查 RTMP/SRS 是否可用（优先 SRS API，避免仅 TCP 端口占用误判）。"""
    try:
        if not rtmp_url.startswith('rtmp://'):
            return False

        api_port = _srs_api_port()
        if _check_srs_api_ready('127.0.0.1', api_port):
            return True

        url_part = rtmp_url.replace('rtmp://', '')
        host_port = url_part.split('/')[0] if '/' in url_part else url_part

        if ':' in host_port:
            host, port_str = host_port.split(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 1935
        else:
            host = host_port
            port = 1935

        host = _normalize_srs_api_host(host)
        if _check_srs_api_ready(host, api_port):
            return True

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.debug(f"检查RTMP服务器连接时出错: {str(e)}")
        return False


def check_and_stop_existing_stream(stream_url: str):
    """检查并停止现有的 RTMP 流（通过 SRS HTTP API）

    当检测到流已存在时，会检查流是否真的在活动：
    1. 如果流存在但没有活跃的发布者（僵尸连接），直接清理流资源
    2. 如果流存在且有发布者，检查发布者连接是否真的在活动
    3. 如果发布者连接已断开，强制清理流资源
    4. 如果发布者连接正常，断开发布者连接

    Args:
        stream_url: RTMP流地址，格式如 rtmp://localhost:1935/live/stream
    """
    try:
        # 从 RTMP URL 中提取流名称和主机
        # rtmp://localhost:1935/live/test_input -> live/test_input
        if not stream_url.startswith('rtmp://'):
            logger.warning("⚠️  无效的RTMP URL格式，跳过流检查")
            return

        # 解析URL: rtmp://host:port/path -> (host, port, path)
        url_part = stream_url.replace('rtmp://', '')
        if '/' in url_part:
            host_port = url_part.split('/')[0]
            stream_path = '/'.join(url_part.split('/')[1:])
        else:
            host_port = url_part
            stream_path = ""

        if not stream_path:
            logger.warning("⚠️  无法从 URL 中提取流路径，跳过流检查")
            return

        # 提取主机地址（用于SRS API调用）
        if ':' in host_port:
            rtmp_host = host_port.split(':')[0]
        else:
            rtmp_host = host_port

        rtmp_host = _normalize_srs_api_host(rtmp_host)
        api_port = _srs_api_port()

        # SRS HTTP API 地址（默认端口 1985）
        srs_api_url = f"http://{rtmp_host}:{api_port}/api/v1/streams/"
        srs_clients_api_url = f"http://{rtmp_host}:{api_port}/api/v1/clients/"

        logger.info(f"🔍 检查现有流: {stream_path}")

        try:
            # 获取所有流
            response = requests.get(srs_api_url, timeout=3)
            if response.status_code == 200:
                streams = response.json()

                # 查找匹配的流
                stream_to_stop = None
                if isinstance(streams, dict) and 'streams' in streams:
                    stream_list = streams['streams']
                elif isinstance(streams, list):
                    stream_list = streams
                else:
                    stream_list = []

                for stream in stream_list:
                    stream_name = stream.get('name', '')
                    stream_app = stream.get('app', '')
                    stream_stream = stream.get('stream', '')

                    # 匹配流路径（格式：app/stream）
                    # 使用精确匹配，避免误匹配其他流
                    full_stream_path = f"{stream_app}/{stream_stream}" if stream_stream else stream_app

                    # 精确匹配：只有当流路径完全匹配时才停止
                    # 这样可以避免误停止其他设备的流
                    if stream_path == full_stream_path:
                        stream_to_stop = stream
                        break

                if stream_to_stop:
                    stream_id = stream_to_stop.get('id', '')
                    publish_info = stream_to_stop.get('publish', {})
                    publish_cid = publish_info.get('cid', '') if isinstance(publish_info, dict) else None

                    logger.warning(f"⚠️  发现现有流: {stream_path} (ID: {stream_id})")

                    # 检查是否有活跃的发布者
                    if not publish_cid:
                        # 流存在但没有发布者（僵尸流），直接清理
                        logger.warning(f"   流存在但没有活跃的发布者（僵尸流），直接清理...")
                        try:
                            stop_url = f"{srs_api_url}{stream_id}"
                            stop_response = requests.delete(stop_url, timeout=3)
                            if stop_response.status_code in [200, 204]:
                                logger.info(f"✅ 已清理僵尸流: {stream_path}")
                                time.sleep(1)  # 等待流完全停止
                                return
                        except Exception as e:
                            logger.warning(f"   清理僵尸流异常: {str(e)}")
                    else:
                        # 有发布者ID，检查发布者连接是否真的在活动
                        logger.info(f"   检查发布者连接状态: {publish_cid}")
                        try:
                            # 获取客户端信息，检查连接是否真的存在
                            client_info_url = f"{srs_clients_api_url}{publish_cid}"
                            client_response = requests.get(client_info_url, timeout=2)

                            if client_response.status_code == 200:
                                client_info = client_response.json()
                                # 检查客户端是否真的在活动
                                client_active = client_info.get('active', True) if isinstance(client_info,
                                                                                              dict) else True

                                if not client_active:
                                    # 客户端已断开，清理僵尸流
                                    logger.warning(f"   发布者连接已断开（僵尸连接），清理流资源...")
                                    try:
                                        stop_url = f"{srs_api_url}{stream_id}"
                                        stop_response = requests.delete(stop_url, timeout=3)
                                        if stop_response.status_code in [200, 204]:
                                            logger.info(f"✅ 已清理僵尸流: {stream_path}")
                                            time.sleep(1)
                                            return
                                    except Exception as e:
                                        logger.warning(f"   清理僵尸流异常: {str(e)}")
                                else:
                                    # 客户端连接正常，尝试断开
                                    logger.info(f"   发布者连接正常，尝试断开连接...")
                                    try:
                                        stop_response = requests.delete(client_info_url, timeout=3)
                                        if stop_response.status_code in [200, 204]:
                                            logger.info(f"✅ 已断开发布者客户端，流将自动停止")
                                            time.sleep(2)  # 等待流完全停止
                                            return
                                        else:
                                            logger.warning(
                                                f"   断开客户端失败 (状态码: {stop_response.status_code})，尝试其他方法...")
                                    except Exception as e:
                                        logger.warning(f"   断开客户端异常: {str(e)}，尝试其他方法...")
                            else:
                                # 无法获取客户端信息，可能连接已断开，尝试清理流
                                logger.warning(
                                    f"   无法获取发布者信息 (状态码: {client_response.status_code})，可能连接已断开，尝试清理流...")
                                try:
                                    # 先尝试断开客户端（即使可能已断开）
                                    try:
                                        requests.delete(client_info_url, timeout=2)
                                    except:
                                        pass

                                    # 然后清理流
                                    stop_url = f"{srs_api_url}{stream_id}"
                                    stop_response = requests.delete(stop_url, timeout=3)
                                    if stop_response.status_code in [200, 204]:
                                        logger.info(f"✅ 已清理流: {stream_path}")
                                        time.sleep(1)
                                        return
                                except Exception as e:
                                    logger.warning(f"   清理流异常: {str(e)}")
                        except requests.exceptions.RequestException as e:
                            # 无法连接到客户端API，可能连接已断开，尝试清理流
                            logger.warning(f"   无法连接到客户端API: {str(e)}，尝试清理流...")
                            try:
                                stop_url = f"{srs_api_url}{stream_id}"
                                stop_response = requests.delete(stop_url, timeout=3)
                                if stop_response.status_code in [200, 204]:
                                    logger.info(f"✅ 已清理流: {stream_path}")
                                    time.sleep(1)
                                    return
                            except Exception as e2:
                                logger.warning(f"   清理流异常: {str(e2)}")

                    # 方法2: 尝试通过流ID停止（某些SRS版本支持）
                    logger.info(f"   尝试通过流ID停止: {stream_id}")
                    stop_url = f"{srs_api_url}{stream_id}"
                    try:
                        stop_response = requests.delete(stop_url, timeout=3)
                        if stop_response.status_code in [200, 204]:
                            logger.info(f"✅ 已停止现有流: {stream_path}")
                            time.sleep(2)  # 等待流完全停止
                            return
                        else:
                            logger.warning(f"   停止流失败 (状态码: {stop_response.status_code})")
                    except Exception as e:
                        logger.warning(f"   停止流异常: {str(e)}")

                    # 方法3: 如果API都失败，尝试查找并杀死占用该流的ffmpeg进程
                    logger.warning(f"⚠️  API方法失败，尝试查找占用该流的进程...")
                    try:
                        # 查找推流到该地址的ffmpeg进程
                        result = subprocess.run(
                            ["pgrep", "-f", f"rtmp://.*{stream_path.split('/')[-1]}"],
                            capture_output=True,
                            text=True,
                            timeout=3
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            pids = result.stdout.strip().split('\n')
                            for pid in pids:
                                if pid.strip():
                                    logger.info(f"   发现进程 PID: {pid.strip()}，正在终止...")
                                    try:
                                        subprocess.run(["kill", "-TERM", pid.strip()], timeout=2)
                                        time.sleep(1)
                                        logger.info(f"✅ 已终止进程: {pid.strip()}")
                                    except:
                                        pass
                            time.sleep(2)  # 等待进程完全退出
                            return
                    except Exception as e:
                        logger.warning(f"   查找进程失败: {str(e)}")

                    logger.warning(f"⚠️  无法停止现有流，但将继续尝试推流...")
                else:
                    logger.info(f"✅ 未发现现有流: {stream_path}")
            else:
                logger.warning(f"⚠️  无法获取流列表 (状态码: {response.status_code})，继续尝试推流...")

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️  无法连接到 SRS API: {str(e)}，继续尝试推流...")

    except Exception as e:
        logger.warning(f"⚠️  检查现有流时出错: {str(e)}，继续尝试推流...")


def read_ffmpeg_stderr(device_id: str, stderr_pipe, stderr_buffer: list, stderr_lock: threading.Lock):
    """实时读取FFmpeg进程的stderr输出"""
    try:
        for line in iter(stderr_pipe.readline, b''):
            if not line:
                break
            try:
                line_str = line.decode('utf-8', errors='ignore').strip()
                if line_str:
                    with stderr_lock:
                        stderr_buffer.append(line_str)
                        # 只保留最近100行
                        if len(stderr_buffer) > 100:
                            stderr_buffer.pop(0)
            except:
                pass
    except Exception as e:
        logger.debug(f"设备 {device_id} stderr读取线程异常: {str(e)}")
    finally:
        stderr_pipe.close()


def _is_likely_rtsp_flat_corrupt_frame(
    frame,
    std_max: float = 4.0,
    mean_lo: float = 80.0,
    mean_hi: float = 180.0,
) -> bool:
    """
    判断整帧是否像解码失败后的典型「中灰塌缩」屏（OpenCV 仍可能 ret=True）。
    仅当中灰区间且极低方差时判定，避免夜景/暗场整幅低方差被误杀。
    """
    if frame is None or frame.size == 0:
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


def _bgr_frame_to_ffmpeg_rgb24_bytes(frame: np.ndarray, expect_h: int, expect_w: int) -> Optional[bytes]:
    """
    将 OpenCV BGR 帧转为 FFmpeg rawvideo rgb24 写入字节，尺寸必须与启动 FFmpeg 时的 -s {W}x{H} 完全一致，
    否则会出现整幅灰屏/花屏。
    """
    if frame is None or frame.size == 0:
        return None
    try:
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        h, w = frame.shape[:2]
        if h != expect_h or w != expect_w:
            frame = cv2.resize(frame, (expect_w, expect_h), interpolation=cv2.INTER_LINEAR)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).tobytes()
    except Exception:
        return None

def _fixed_rate_push_worker(device_id: str):
    """固定速率推帧线程：独立于主循环，以精确帧率间隔向 FFmpeg 推帧。
    
    核心思路：
    - 主循环负责读取帧、缓冲、AI处理，将待推帧写入 device_output_frames
    - 本线程以 steady clock 间隔读取 latest output frame 并写入 FFmpeg stdin
    - 当 AI 处理慢、主循环未产出新帧时，重复推上一帧（保持流畅，避免卡顿快进）
    - 当主循环产出帧过快时，只保留最新帧（丢旧帧追实时）
    """
    logger.info(f"📤 固定速率推帧线程启动 [设备: {device_id}]")
    push_running = device_push_running.get(device_id)
    
    # 获取推流参数
    _profile_name, _effective_fps, _effective_w, _effective_h, _effective_bitrate, _effective_gop = _get_effective_realtime_stream_params()
    frame_interval = 1.0 / max(1, _effective_fps)
    
    last_push_frame = None
    last_push_w = None
    last_push_h = None
    last_push_time = time.perf_counter()
    push_frame_count = 0
    flush_every = max(1, int(os.getenv('AI_PUSH_FLUSH_EVERY', os.getenv('VIEW_PUSH_FLUSH_EVERY', '5'))))

    while push_running and not push_running.is_set() and not stop_event.is_set():
        try:
            # 精确帧率控制：计算下一帧应该推送的时间
            target_time = last_push_time + frame_interval
            now = time.perf_counter()
            sleep_duration = target_time - now
            
            if sleep_duration > 0:
                time.sleep(sleep_duration)
            elif sleep_duration < -frame_interval * 2:
                # 严重落后（超过2帧间隔），重置时间基准避免突发推帧
                last_push_time = time.perf_counter()
                target_time = last_push_time + frame_interval
                time.sleep(frame_interval)
            
            last_push_time = time.perf_counter()
            
            # 获取当前推送进程
            pusher_process = device_pushers.get(device_id)
            if not pusher_process or pusher_process.poll() is not None:
                # 推送进程不可用，短暂等待
                time.sleep(0.01)
                continue
            
            # 读取最新待推帧
            output_lock = device_output_locks.get(device_id)
            output_frame_info = None
            if output_lock:
                with output_lock:
                    output_frame_info = device_output_frames.get(device_id)
            
            # 确定要推送的帧
            frame_to_push = None
            push_w = None
            push_h = None
            
            if output_frame_info is not None and output_frame_info.get('frame') is not None:
                frame_to_push = output_frame_info['frame']
                push_w = output_frame_info['w']
                push_h = output_frame_info['h']
                # 更新上一帧缓存
                last_push_frame = frame_to_push
                last_push_w = push_w
                last_push_h = push_h
            elif last_push_frame is not None:
                # 没有新帧，重复上一帧（保持流畅）
                frame_to_push = last_push_frame
                push_w = last_push_w
                push_h = last_push_h
            else:
                # 首帧尚未就绪，等待
                time.sleep(0.005)
                continue
            
            # 确保帧尺寸与 FFmpeg -s 参数一致
            raw_bytes = _bgr_frame_to_ffmpeg_rgb24_bytes(frame_to_push, push_h, push_w)
            if raw_bytes is None:
                continue
            
            # 写入 FFmpeg stdin
            try:
                pusher_process.stdin.write(raw_bytes)
                if push_frame_count % flush_every == 0:
                    pusher_process.stdin.flush()
                push_frame_count += 1
                if push_frame_count % 150 == 0:
                    _mark_quality_success()
            except Exception as e:
                logger.error(f"❌ 设备 {device_id} 固定速率推帧写入失败: {str(e)}")
                _mark_quality_failure("推送帧失败")
                if pusher_process.poll() is not None:
                    device_pushers.pop(device_id, None)
                    
        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 固定速率推帧线程异常: {str(e)}", exc_info=True)
            time.sleep(0.01)
    
    logger.info(f"📤 固定速率推帧线程停止 [设备: {device_id}]")


def buffer_streamer_worker(device_id: str):
    """
    缓流器工作线程：拉源流并推 AI 流。

    架构说明：
    - 队列1 / 推流链路：读帧后立即叠 overlay 缓存并推流，不等待任何检测完成
    - 队列2 / overlay 检测：缓流器直投 overlay_detection_queues，Worker 仅更新叠框缓存
    - 队列3 / 告警检测：缓流器直投 alert_detection_queues，Worker 独立发告警
    """
    logger.info(f"💾 缓流器线程启动 [设备: {device_id}]")

    if not task_config or not hasattr(task_config, 'device_streams'):
        logger.error(f"任务配置未加载，设备 {device_id} 缓流器退出")
        return

    device_stream_info = task_config.device_streams.get(device_id)
    if not device_stream_info:
        logger.error(f"设备 {device_id} 流信息不存在，缓流器退出")
        return

    rtsp_url = device_stream_info.get('rtsp_url')
    rtmp_url = device_stream_info.get('rtmp_url')
    device_name = device_stream_info.get('device_name', device_id)
    _is_gb28181 = device_stream_info.get('is_gb28181', False)
    _original_source = device_stream_info.get('original_source')

    # 打印推流地址信息
    logger.info(f"📺 设备 {device_id} 流地址配置:")
    input_stream_type = "RTSP" if rtsp_url and rtsp_url.startswith(
        'rtsp://') else "RTMP" if rtsp_url and rtsp_url.startswith('rtmp://') else "输入流"
    logger.info(f"   {input_stream_type}输入流: {rtsp_url}")
    logger.info(f"   RTMP推流地址: {rtmp_url if rtmp_url else '(未配置)'}")

    if not rtsp_url:
        logger.error(f"设备 {device_id} 输入流地址不存在，缓流器退出")
        return

    # 兼容 RTSP 和 RTMP 两种格式的输入流
    stream_type = "RTSP" if rtsp_url.startswith('rtsp://') else "RTMP" if rtsp_url.startswith('rtmp://') else "未知"
    logger.info(f"📡 设备 {device_id} 输入流类型: {stream_type}")

    cap = None
    pusher_process = None
    frame_width = None
    frame_height = None
    retry_count = 0
    max_retries = 5
    rtsp_open_timeout_msec = int(os.getenv("RTSP_OPEN_TIMEOUT_MSEC", "5000"))
    rtsp_read_timeout_msec = int(os.getenv("RTSP_READ_TIMEOUT_MSEC", "2500"))
    rtsp_retry_delay_sec = max(0.1, float(os.getenv("RTSP_RETRY_DELAY_SEC", "1")))
    rtsp_retry_cooldown_sec = max(1.0, float(os.getenv("RTSP_RETRY_COOLDOWN_SEC", "8")))
    rtsp_read_fail_delay_sec = max(0.1, float(os.getenv("RTSP_READ_FAIL_DELAY_SEC", "0.3")))
    pusher_retry_count = 0  # FFmpeg 推送进程重试计数
    pusher_max_retries = 3  # FFmpeg 推送进程最大重试次数
    last_pusher_failure_time = 0  # 上次推送进程失败的时间
    _last_gb28181_resolve_time = 0.0  # GB28181 上次重新解析时间（用于频率限制）

    # 初始化stderr缓冲区
    if device_id not in device_pusher_stderr_buffers:
        device_pusher_stderr_buffers[device_id] = []
        device_pusher_stderr_locks[device_id] = threading.Lock()
    
    # 初始化设备编码器状态（如果不存在，使用全局配置）
    if device_id not in device_codec_status:
        device_codec_status[device_id] = _hwaccel_codec
        device_codec_locks[device_id] = threading.Lock()

    # 流畅度优化已移至独立固定速率推帧线程（_fixed_rate_push_worker）
    # 主循环仍需帧消费速率控制，防止 GB28181 录像回放等非实时源全速发帧导致快进
    _profile_name, _effective_fps, _effective_w, _effective_h, _effective_bitrate, _effective_gop = _get_effective_realtime_stream_params()
    _frame_interval = 1.0 / max(1, _effective_fps)
    _last_frame_consume_time = time.perf_counter()

    # 灰屏/解码塌缩检测（默认开启；误判可调高 WARMUP/STREAK 或设 AI_RTSP_GRAY_RECONNECT=0）
    _gray_reconnect = (os.getenv("AI_RTSP_GRAY_RECONNECT", "1").strip().lower() not in ("0", "false", "no", "off"))
    try:
        _gray_streak_need = max(1, int((os.getenv("AI_RTSP_GRAY_STREAK", "20").strip() or "20")))
    except Exception:
        _gray_streak_need = 20

    def _gray_float(name: str, default: float) -> float:
        try:
            return float((os.getenv(name) or "").strip() or default)
        except Exception:
            return default

    _gray_std_max = _gray_float("AI_RTSP_GRAY_STD_MAX", 4.0)
    _gray_mean_lo = _gray_float("AI_RTSP_GRAY_MEAN_LO", 80.0)
    _gray_mean_hi = _gray_float("AI_RTSP_GRAY_MEAN_HI", 180.0)
    _gray_warmup_sec = _gray_float("AI_RTSP_GRAY_WARMUP_SEC", 15.0)
    _gray_reconnect_delay = _gray_float("AI_RTSP_GRAY_RECONNECT_DELAY_SEC", 2.0)
    gray_bad_streak = 0
    last_rtsp_connect_time = 0.0

    while not stop_event.is_set():
        try:
            # 打开源流（支持 RTSP 和 RTMP）
            if cap is None or not cap.isOpened():
                # GB28181 源重连时重新解析 URL（录像回放会话结束后旧 URL 会失效）
                # 频率限制：至少间隔30秒，避免重连时反复请求 GB28181 播放 API
                if _is_gb28181 and _original_source:
                    _resolve_elapsed = time.time() - _last_gb28181_resolve_time
                    if _resolve_elapsed >= 30.0:
                        _last_gb28181_resolve_time = time.time()
                        _new_url = resolve_gb28181_source(_original_source, logger=logger)
                        if _new_url and _new_url != rtsp_url:
                            logger.info(f"📌 设备 {device_id} GB28181源重新解析: {rtsp_url} -> {_new_url}")
                            rtsp_url = _new_url
                            retry_count = 0  # URL 已更新，重置重试计数
                        elif _new_url:
                            logger.info(f"📌 设备 {device_id} GB28181源重新解析（URL未变）: {rtsp_url}")
                        else:
                            logger.warning(f"⚠️ 设备 {device_id} GB28181源重新解析失败，使用上次URL重试")

                # 源流断开期间：检查推流进程是否存活，记录状态
                if pusher_process is not None and pusher_process.poll() is not None:
                    logger.debug(f"设备 {device_id} 源流断开期间推流进程已退出，将在源流重连后自动重启")

                stream_type = "RTSP" if rtsp_url.startswith('rtsp://') else "RTMP" if rtsp_url.startswith(
                    'rtmp://') else "流"

                # 对于 RTMP 流，先检查服务器是否可用
                if rtsp_url.startswith('rtmp://'):
                    if not check_rtmp_server_connection(rtsp_url):
                        retry_count += 1
                        if retry_count >= max_retries:
                            logger.error(f"❌ 设备 {device_id} RTMP 服务器不可用，已达到最大重试次数 {max_retries}")
                            logger.info(f"等待{rtsp_retry_cooldown_sec:.1f}秒后重新尝试...")
                            time.sleep(rtsp_retry_cooldown_sec)
                            retry_count = 0
                        else:
                            logger.warning(
                                f"设备 {device_id} RTMP 服务器不可用，等待重试... ({retry_count}/{max_retries})")
                            time.sleep(rtsp_retry_delay_sec)
                        continue

                logger.info(f"正在连接设备 {device_id} 的 {stream_type} 流: {rtsp_url} (重试次数: {retry_count})")

                _queue_max_override = None
                if _is_gb28181 or device_stream_info.get('source_type') == 'gb28181':
                    _gb_fifo = int(os.getenv("AI_GB28181_ASYNC_QUEUE_MAX", "10"))
                    if _gb_fifo > 1:
                        _queue_max_override = _gb_fifo
                        logger.info(
                            f"📌 设备 {device_id} GB28181源，FIFO 缓冲 {_gb_fifo} 帧按序消费（AI_GB28181_ASYNC_QUEUE_MAX）"
                        )

                try:
                    cap = open_device_stream(
                        rtsp_url,
                        device_id,
                        task_id=str(TASK_ID),
                        open_timeout_msec=rtsp_open_timeout_msec,
                        read_timeout_msec=rtsp_read_timeout_msec,
                        queue_max_override=_queue_max_override,
                    )
                except Exception as e:
                    logger.error(f"设备 {device_id} 打开视频流时出错: {str(e)}")
                    # 确保释放资源
                    if cap is not None:
                        try:
                            cap.release()
                        except:
                            pass
                        cap = None
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ 设备 {device_id} 连接 {stream_type} 流失败，已达到最大重试次数 {max_retries}")
                        logger.info(f"等待{rtsp_retry_cooldown_sec:.1f}秒后重新尝试...")
                        time.sleep(rtsp_retry_cooldown_sec)
                        retry_count = 0
                    else:
                        logger.warning(
                            f"设备 {device_id} 无法打开 {stream_type} 流，等待重试... ({retry_count}/{max_retries})")
                        time.sleep(rtsp_retry_delay_sec)
                    continue

                if not cap.isOpened():
                    _fallback_url = None
                    if _is_gb28181 and _original_source and rtsp_url.startswith('rtmp://'):
                        _fallback_url = resolve_gb28181_alternate_pull_url(
                            _original_source, rtsp_url, logger=logger,
                        )
                    if _fallback_url:
                        if cap is not None:
                            try:
                                cap.release()
                            except Exception:
                                pass
                        rtsp_url = _fallback_url
                        retry_count = 0
                        cap = None
                        continue

                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ 设备 {device_id} 连接 {stream_type} 流失败，已达到最大重试次数 {max_retries}")
                        logger.info(f"等待{rtsp_retry_cooldown_sec:.1f}秒后重新尝试...")
                        time.sleep(rtsp_retry_cooldown_sec)
                        retry_count = 0
                    else:
                        logger.warning(
                            f"设备 {device_id} 无法打开 {stream_type} 流，等待重试... ({retry_count}/{max_retries})")
                        time.sleep(rtsp_retry_delay_sec)
                    if cap is not None:
                        try:
                            cap.release()
                        except Exception:
                            pass
                        cap = None
                    continue

                retry_count = 0

                # GB28181 源：读取源流实际帧率用于帧消费速率控制，防止快进
                if _is_gb28181:
                    try:
                        _src_fps_raw = cap.get(cv2.CAP_PROP_FPS)
                        if _src_fps_raw and _src_fps_raw > 1:
                            _frame_interval_old = _frame_interval
                            _frame_interval = 1.0 / int(round(_src_fps_raw))
                            logger.info(
                                f"📌 设备 {device_id} GB28181源实际帧率: {_src_fps_raw:.1f}fps → "
                                f"消费间隔 {_frame_interval:.4f}s（替代输出帧率 {_effective_fps}fps 的 {_frame_interval_old:.4f}s）"
                            )
                    except Exception as _e:
                        logger.debug(f"设备 {device_id} 读取源流帧率失败: {_e}")

                logger.info(f"📌 设备 {device_id} {stream_mode_label(cap)}")
                device_caps[device_id] = cap
                logger.info(f"✅ 设备 {device_id} {stream_type} 流连接成功")
                if motion_gate is not None:
                    motion_gate.reset(device_id)
                if rtsp_url.startswith("rtsp://"):
                    last_rtsp_connect_time = time.time()

            # 从源流读取帧（异步模式下由后台线程 decode，此处取缓冲区最新帧）
            # 帧消费速率控制：按 effective_fps 消费帧，防止非实时源（GB28181录像回放）全速发帧导致快进
            _now = time.perf_counter()
            _elapsed = _now - _last_frame_consume_time
            if _elapsed < _frame_interval:
                time.sleep(_frame_interval - _elapsed)
            _last_frame_consume_time = time.perf_counter()

            ret, frame = cap.read()

            if not ret or frame is None:
                if is_async_stream(cap):
                    if cap.read_failed:
                        logger.warning(f"设备 {device_id} 异步拉流结束或解码失败，重新连接...")
                        if cap is not None:
                            cap.release()
                            cap = None
                            device_caps.pop(device_id, None)
                        gray_bad_streak = 0
                        time.sleep(rtsp_read_fail_delay_sec)
                        continue
                    # FIFO 队列暂时为空（后台线程仍在解码），等待帧间隔的一半再重试
                    # 对于 GB28181 源帧率可能较低，避免高频空转
                    time.sleep(min(_frame_interval * 0.5, 0.02))
                    continue
                logger.warning(f"设备 {device_id} 读取源流帧失败，重新连接...")
                if cap is not None:
                    cap.release()
                    cap = None
                    device_caps.pop(device_id, None)
                gray_bad_streak = 0
                time.sleep(rtsp_read_fail_delay_sec)
                continue

            # RTSP：可选灰屏重连（预热期内不判定，重连间隔加长以减少 UDP bind 冲突）
            if (
                rtsp_url.startswith("rtsp://")
                and _gray_reconnect
                and (time.time() - last_rtsp_connect_time) >= _gray_warmup_sec
                and _is_likely_rtsp_flat_corrupt_frame(
                    frame, _gray_std_max, _gray_mean_lo, _gray_mean_hi
                )
            ):
                gray_bad_streak += 1
                if gray_bad_streak >= _gray_streak_need:
                    logger.warning(
                        f"设备 {device_id} 连续 {gray_bad_streak} 帧疑似解码灰屏/塌缩，释放并重连 RTSP"
                    )
                    if cap is not None:
                        try:
                            cap.release()
                        except Exception:
                            pass
                        cap = None
                        device_caps.pop(device_id, None)
                    gray_bad_streak = 0
                    time.sleep(max(0.5, _gray_reconnect_delay))
                    continue
                continue
            gray_bad_streak = 0

            # 更新该设备的帧计数
            frame_counts[device_id] += 1
            frame_count = frame_counts[device_id]
            profile_name, effective_fps, effective_w, effective_h, effective_bitrate, effective_gop = _get_effective_realtime_stream_params()

            # 与 stream_forward_service 一致：raw 帧保持摄像头/源流分辨率，由 FFmpeg bilinear 缩放到画质档位
            stdin_h, stdin_w = frame.shape[:2]

            # 初始化推送进程（为该设备）- 只在需要时启动，避免频繁重启
            if pusher_process is None or pusher_process.poll() is not None:
                # 如果进程已退出，记录原因并添加重试延迟
                if pusher_process and pusher_process.poll() is not None:
                    # 检查是否需要等待重试（避免频繁重启）
                    current_time = time.time()
                    time_since_last_failure = current_time - last_pusher_failure_time
                    min_retry_interval = 2.0  # 最小重试间隔：2秒

                    if time_since_last_failure < min_retry_interval:
                        # 如果距离上次失败时间太短，等待一段时间
                        wait_time = min_retry_interval - time_since_last_failure
                        logger.debug(f"设备 {device_id} 推送进程失败后等待 {wait_time:.1f} 秒后重试...")
                        time.sleep(wait_time)

                    last_pusher_failure_time = time.time()
                    # 停止stderr读取线程
                    stderr_thread = device_pusher_stderr_threads.pop(device_id, None)
                    if stderr_thread and stderr_thread.is_alive():
                        try:
                            # 等待线程结束（最多等待1秒）
                            stderr_thread.join(timeout=1)
                        except:
                            pass

                    # 获取stderr错误信息
                    stderr_lines = []
                    with device_pusher_stderr_locks[device_id]:
                        stderr_lines = device_pusher_stderr_buffers[device_id].copy()
                        device_pusher_stderr_buffers[device_id].clear()

                    exit_code = pusher_process.returncode
                    logger.warning(f"⚠️  设备 {device_id} 推送进程已退出 (退出码: {exit_code})")

                    # 提取关键错误信息（过滤掉版本信息等）
                    error_lines = []
                    hw_encoder_error = False  # 标记是否是硬件编码器错误
                    for line in stderr_lines:
                        line_lower = line.lower()
                        # 跳过版本信息、配置信息等
                        if any(skip in line_lower for skip in
                               ['version', 'copyright', 'built with', 'configuration:', 'libav']):
                            continue
                        # 保留错误、警告、失败等信息
                        if any(keyword in line_lower for keyword in
                               ['error', 'failed', 'warning', 'cannot', 'unable', 'invalid', 'connection refused',
                                'connection reset', 'timeout', 'input/output error', 'stream busy', 'broken pipe']):
                            error_lines.append(line)
                            # 检测硬件编码器相关错误
                            if any(hw_err in line_lower for hw_err in ['cannot load libcuda', 'libcuda.so', 'h264_nvenc', 'nvenc', 'cuda']):
                                hw_encoder_error = True

                    if error_lines:
                        logger.warning(f"   关键错误信息:")
                        for err_line in error_lines[-10:]:  # 只显示最后10行关键错误
                            logger.warning(f"   {err_line}")
                    elif stderr_lines:
                        # 如果没有关键错误，显示最后几行
                        logger.warning(f"   最后输出: {stderr_lines[-3:]}")
                    else:
                        logger.warning(f"   未捕获到错误信息，可能是进程启动失败或RTMP服务器连接问题")
                    
                    # 如果是硬件编码器错误，自动切换到软件编码
                    should_retry_with_software = False
                    if hw_encoder_error:
                        # 初始化设备编码器锁（如果不存在）
                        if device_id not in device_codec_locks:
                            device_codec_locks[device_id] = threading.Lock()
                        
                        with device_codec_locks[device_id]:
                            current_codec = device_codec_status.get(device_id, _hwaccel_codec)
                            if current_codec == 'h264_nvenc':
                                logger.warning(f"🔄 设备 {device_id} 硬件编码器失败，自动切换到软件编码 (libx264)")
                                device_codec_status[device_id] = 'libx264'
                                _disable_hwaccel_globally('硬件编码运行失败')
                                should_retry_with_software = True
                            else:
                                # 已经使用软件编码，不需要切换
                                pass
                    
                    # 如果切换到软件编码，确保进程被重置以便立即重试
                    if should_retry_with_software:
                        # 停止固定速率推帧线程
                        _push_running = device_push_running.get(device_id)
                        if _push_running:
                            _push_running.set()
                        _push_thread = device_push_threads.pop(device_id, None)
                        if _push_thread and _push_thread.is_alive():
                            try:
                                _push_thread.join(timeout=2)
                            except:
                                pass
                        # 关闭旧进程（如果还在运行）
                        if pusher_process and pusher_process.poll() is None:
                            try:
                                pusher_process.stdin.close()
                                pusher_process.terminate()
                                pusher_process.wait(timeout=2)
                            except:
                                if pusher_process.poll() is None:
                                    pusher_process.kill()
                        pusher_process = None
                        device_pushers.pop(device_id, None)
                        logger.info(f"🔄 设备 {device_id} 将使用软件编码重新启动推送进程...")

                    # 检查RTMP/SRS 状态（仅在首次失败时检查，避免频繁检查）
                    if pusher_retry_count == 0:
                        srs_api_ok = _check_srs_api_ready('127.0.0.1', _srs_api_port())
                        if not srs_api_ok or any('input/output error' in e.lower() for e in error_lines):
                            logger.warning("")
                            logger.warning("=" * 60)
                            logger.warning("💡 AI 推流失败（FFmpeg 退出码 251 / Input/output error），常见原因：")
                            logger.warning("=" * 60)
                            if not srs_api_ok:
                                logger.warning("1. SRS 未就绪或 /data 目录异常（DVR/on_publish 失败）")
                                logger.warning("   - 检查: curl http://127.0.0.1:1985/api/v1/versions")
                                logger.warning("   - 修复: cd VIDEO && ./fix_srs.sh  （重建 SRS 并创建 ~/easyaiot/data）")
                            else:
                                logger.warning("1. SRS on_publish 回调超时或被拒绝（查看 ~/easyaiot/data/srs.log）")
                            logger.warning("2. 本机推流应使用 127.0.0.1/ai/{device_id}，勿用外网 IP 回环推流")
                            logger.warning("   - 当前推流地址: %s", rtmp_url)
                            logger.warning("3. 检查 SRS 服务: docker ps | grep srs")
                            logger.warning("4. 检查 Gateway/VIDEO 回调: curl -X POST http://127.0.0.1:48080/admin-api/video/camera/callback/on_publish -d '{}'")
                            logger.warning("=" * 60)
                            logger.warning("")

                # 关闭旧进程
                # 停止固定速率推帧线程
                _push_running = device_push_running.get(device_id)
                if _push_running:
                    _push_running.set()
                _push_thread = device_push_threads.pop(device_id, None)
                if _push_thread and _push_thread.is_alive():
                    try:
                        _push_thread.join(timeout=2)
                    except:
                        pass

                if pusher_process and pusher_process.poll() is None:
                    try:
                        pusher_process.stdin.close()
                        pusher_process.terminate()
                        pusher_process.wait(timeout=2)
                    except:
                        if pusher_process.poll() is None:
                            pusher_process.kill()

                frame_width = stdin_w
                frame_height = stdin_h

                if not rtmp_url:
                    logger.warning(f"设备 {device_id} RTMP输出流地址不存在，跳过推送")
                else:
                    # 在启动推流前，检查并停止现有流（避免StreamBusy错误）
                    # 重要：只检查推流地址，不检查输入流地址，避免误停止输入流
                    # 如果输入流地址和推流地址相同，则跳过检查（避免误停止输入流）
                    if rtsp_url and rtsp_url == rtmp_url:
                        logger.warning(f"⚠️  设备 {device_id} 输入流地址和推流地址相同，跳过流检查（避免误停止输入流）")
                    else:
                        logger.info(f"🔍 检查设备 {device_id} 是否存在占用该地址的流...")
                        check_and_stop_existing_stream(rtmp_url)

                    if device_id not in device_codec_locks:
                        device_codec_locks[device_id] = threading.Lock()
                    with device_codec_locks[device_id]:
                        device_codec = device_codec_status.get(device_id, _hwaccel_codec)

                    ffmpeg_cmd, actual_codec, target_w, target_h = _build_realtime_ffmpeg_push_cmd(
                        device_id,
                        stdin_w,
                        stdin_h,
                        rtmp_url,
                        device_codec,
                        effective_fps,
                        effective_w,
                        effective_h,
                        effective_bitrate,
                        effective_gop,
                    )
                    if actual_codec != device_codec:
                        with device_codec_locks[device_id]:
                            device_codec_status[device_id] = actual_codec
                        device_codec = actual_codec

                    gop_out = max(1, effective_gop)
                    if target_w != effective_w or target_h != effective_h:
                        logger.debug(
                            f"设备 {device_id} 编码分辨率对齐: {effective_w}x{effective_h} -> {target_w}x{target_h}"
                        )

                    codec_info = f"硬件编码 ({device_codec})" if device_codec == 'h264_nvenc' else f"软件编码 ({device_codec})"
                    logger.info(f"🚀 启动设备 {device_id} 推送进程")
                    logger.info(f"   📺 推流地址: {rtmp_url}")
                    logger.info(
                        f"   📐 raw输入 {stdin_w}x{stdin_h} -> 编码约 {target_w}x{target_h} @ {effective_fps}fps"
                    )
                    logger.info(f"   🎬 编码器: {codec_info}, 比特率: {effective_bitrate}, GOP: {gop_out}")
                    logger.info(f"   🎯 画质档位: {profile_name}")
                    logger.info(
                        f"   📦 max_muxing_queue_size={_resolve_realtime_mux_queue_size()}, "
                        f"opencv_thread_queue_size={_opencv_thread_queue_log_label()}/路"
                    )
                    if device_codec != 'h264_nvenc' and FFMPEG_THREADS is not None and str(FFMPEG_THREADS).strip():
                        logger.info(f"   🧵 编码线程数: {FFMPEG_THREADS}")
                    logger.debug(f"   FFmpeg命令: {' '.join(ffmpeg_cmd)}")
                    logger.debug(f"   FFmpeg命令参数列表: {ffmpeg_cmd}")

                    try:
                        pusher_process = subprocess.Popen(
                            ffmpeg_cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            bufsize=0,
                            shell=False  # 明确指定不使用shell，避免容器环境中的参数解析问题
                        )

                        # 启动stderr读取线程
                        stderr_buffer = device_pusher_stderr_buffers[device_id]
                        stderr_lock = device_pusher_stderr_locks[device_id]
                        stderr_thread = threading.Thread(
                            target=read_ffmpeg_stderr,
                            args=(device_id, pusher_process.stderr, stderr_buffer, stderr_lock),
                            daemon=True
                        )
                        stderr_thread.start()
                        device_pusher_stderr_threads[device_id] = stderr_thread

                        # 等待一小段时间，检查进程是否立即退出
                        time.sleep(0.5)

                        if pusher_process.poll() is not None:
                            # 等待stderr线程读取一些输出
                            time.sleep(0.3)

                            # 获取错误信息
                            error_lines = []
                            with device_pusher_stderr_locks[device_id]:
                                error_lines = device_pusher_stderr_buffers[device_id].copy()
                                device_pusher_stderr_buffers[device_id].clear()

                            exit_code = pusher_process.returncode
                            logger.error(f"❌ 设备 {device_id} 推送进程启动失败 (退出码: {exit_code})")
                            logger.error(f"   FFmpeg命令: {' '.join(ffmpeg_cmd)}")
                            logger.error(f"   FFmpeg命令参数列表: {ffmpeg_cmd}")

                            # 提取关键错误信息
                            key_errors = []
                            hw_encoder_error = False  # 标记是否是硬件编码器错误
                            for line in error_lines:
                                line_lower = line.lower()
                                if any(skip in line_lower for skip in
                                       ['version', 'copyright', 'built with', 'configuration:', 'libav']):
                                    continue
                                if any(keyword in line_lower for keyword in
                                       ['error', 'failed', 'cannot', 'unable', 'invalid', 'connection refused',
                                        'connection reset', 'timeout', 'no such file', 'permission denied', 'splitting',
                                        'option not found', 'input/output error', 'stream busy', 'broken pipe']):
                                    key_errors.append(line)
                                    # 检测硬件编码器相关错误
                                    if any(hw_err in line_lower for hw_err in ['cannot load libcuda', 'libcuda.so', 'h264_nvenc', 'nvenc', 'cuda']):
                                        hw_encoder_error = True

                            if key_errors:
                                logger.error(f"   关键错误:")
                                for err in key_errors[-10:]:
                                    logger.error(f"   {err}")
                            elif error_lines:
                                logger.error(f"   输出: {error_lines[-5:]}")
                            else:
                                logger.error(f"   未捕获到错误信息，请检查RTMP服务器是否运行: {rtmp_url}")
                            
                            # 如果是硬件编码器错误，自动切换到软件编码并重新启动
                            should_retry_with_software = False
                            if hw_encoder_error:
                                # 初始化设备编码器锁（如果不存在）
                                if device_id not in device_codec_locks:
                                    device_codec_locks[device_id] = threading.Lock()
                                
                                with device_codec_locks[device_id]:
                                    current_codec = device_codec_status.get(device_id, _hwaccel_codec)
                                    if current_codec == 'h264_nvenc':
                                        logger.warning(f"🔄 设备 {device_id} 硬件编码器启动失败，自动切换到软件编码 (libx264)")
                                        device_codec_status[device_id] = 'libx264'
                                        should_retry_with_software = True
                            
                            # 如果切换到软件编码，重置进程以便立即重试
                            if should_retry_with_software:
                                pusher_process = None
                                device_pushers.pop(device_id, None)
                                logger.info(f"🔄 设备 {device_id} 将使用软件编码重新启动推送进程...")
                                continue

                            # 检查RTMP服务器连接状态
                            if not check_rtmp_server_connection(rtmp_url):
                                logger.error("")
                                logger.error("=" * 60)
                                logger.error("💡 RTMP服务器连接检查失败，可能的原因和解决方案：")
                                logger.error("=" * 60)
                                logger.error("1. RTMP服务器（SRS）未运行")
                                logger.error("   - 检查SRS服务状态: docker ps | grep srs")
                                logger.error("   - 或使用: systemctl status srs")
                                logger.error("")
                                logger.error("2. 启动SRS服务器：")
                                logger.error(
                                    "   - 使用Docker Compose: cd /opt/projects/easyaiot/.scripts/docker && docker-compose up -d srs")
                                logger.error(
                                    "   - 或使用Docker: docker run -d --name srs-server -p 1935:1935 -p 1985:1985 -p 8080:8080 ossrs/srs:5")
                                logger.error("")
                                logger.error("3. SRS HTTP回调服务未运行（常见原因）")
                                logger.error("   - SRS配置了on_publish回调，但回调服务未启动")
                                logger.error("   - 请确保VIDEO服务在端口48080上运行")
                                logger.error("   - 检查服务: docker ps | grep video")
                                logger.error("")
                                logger.error("4. 检查RTMP端口是否监听：")
                                logger.error("   - netstat -tuln | grep 1935")
                                logger.error("   - 或: ss -tuln | grep 1935")
                                logger.error("")
                                logger.error("5. 测试RTMP连接：")
                                logger.error("   - telnet localhost 1935")
                                logger.error("   - 或: curl http://localhost:1985/api/v1/versions")
                                logger.error("=" * 60)
                                logger.error("")

                            # 停止stderr线程
                            if stderr_thread.is_alive():
                                stderr_thread.join(timeout=0.5)
                            device_pusher_stderr_threads.pop(device_id, None)

                            pusher_retry_count += 1
                            _mark_quality_failure("推流进程启动失败")
                            if pusher_retry_count >= pusher_max_retries:
                                logger.error(
                                    f"❌ 设备 {device_id} 推送进程启动失败次数过多 ({pusher_retry_count}/{pusher_max_retries})，等待10秒后重置重试计数")
                                time.sleep(10)
                                pusher_retry_count = 0

                            pusher_process = None
                        else:
                            # 推送进程启动成功，重置重试计数
                            pusher_retry_count = 0
                            _mark_quality_success()
                            device_pushers[device_id] = pusher_process
                            logger.info(f"✅ 设备 {device_id} 推送进程已启动 (PID: {pusher_process.pid})")
                            logger.info(f"   📺 推流地址: {rtmp_url}")
                            logger.info(
                                f"   📐 输出参数: raw {stdin_w}x{stdin_h} -> scale至档位分辨率 @ {effective_fps}fps"
                            )

                            # 额外等待一小段时间，确保 RTMP 连接已建立
                            time.sleep(0.3)

                            # 启动固定速率推帧线程
                            if device_id not in device_output_locks:
                                device_output_locks[device_id] = threading.Lock()
                            if device_id not in device_output_frames:
                                device_output_frames[device_id] = None
                            if device_id not in device_push_running:
                                device_push_running[device_id] = threading.Event()
                            device_push_running[device_id].clear()
                            push_thread = threading.Thread(
                                target=_fixed_rate_push_worker,
                                args=(device_id,),
                                daemon=True
                            )
                            device_push_threads[device_id] = push_thread
                            push_thread.start()
                            logger.info(f"📤 设备 {device_id} 固定速率推帧线程已启动")
                    except Exception as e:
                        logger.error(f"❌ 设备 {device_id} 启动推送进程异常: {str(e)}", exc_info=True)
                        pusher_process = None
            elif frame_width is not None and (stdin_w != frame_width or stdin_h != frame_height):
                # 源流分辨率变化：必须清空缓冲区，否则旧分辨率帧写入新 FFmpeg -s 会导致灰屏
                logger.info(
                    f"🔄 设备 {device_id} 源流分辨率变化 ({frame_width}x{frame_height} -> {stdin_w}x{stdin_h})，"
                    f"重启推送进程并清空缓冲（避免 rawvideo 与 -s 不一致导致推流灰屏）"
                )
                # 停止固定速率推帧线程
                _push_running = device_push_running.get(device_id)
                if _push_running:
                    _push_running.set()
                _push_thread = device_push_threads.pop(device_id, None)
                if _push_thread and _push_thread.is_alive():
                    try:
                        _push_thread.join(timeout=2)
                    except:
                        pass

                if pusher_process and pusher_process.poll() is None:
                    try:
                        pusher_process.stdin.close()
                        pusher_process.terminate()
                        pusher_process.wait(timeout=2)
                    except:
                        if pusher_process.poll() is None:
                            pusher_process.kill()

                # 停止stderr读取线程
                stderr_thread = device_pusher_stderr_threads.pop(device_id, None)
                if stderr_thread and stderr_thread.is_alive():
                    try:
                        stderr_thread.join(timeout=1)
                    except:
                        pass

                pusher_process = None
                device_pushers.pop(device_id, None)

                frame_width = stdin_w
                frame_height = stdin_h
                output_lock = device_output_locks.get(device_id)
                if output_lock:
                    with output_lock:
                        device_output_frames[device_id] = None

            current_timestamp = time.time()

            # ========== 队列1：主画面推流（不等待检测，仅叠 overlay 缓存） ==========
            if frame_width is not None and frame_height is not None:
                output_frame, overlay_applied = _apply_latest_overlay_if_needed(
                    device_id,
                    frame,
                    current_timestamp,
                    frame_count,
                    tracking_enabled=task_config.tracking_enabled if task_config else False,
                )
                output_lock = device_output_locks.get(device_id)
                if output_lock:
                    with output_lock:
                        device_output_frames[device_id] = {
                            'frame': output_frame,
                            'w': frame_width,
                            'h': frame_height,
                        }
                if overlay_applied and frame_count % 100 == 0:
                    logger.debug(
                        f"📺 设备 {device_id} 推流帧 {frame_count} 已叠 overlay 缓存"
                    )

            # ========== 队列2/3：overlay 叠框 + 告警（缓流器直投，完全独立于推流） ==========
            _feed_stream_detection_queues(device_id, frame, frame_count, current_timestamp)

        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 缓流器异常: {str(e)}", exc_info=True)
            time.sleep(2)

    # 停止固定速率推帧线程
    push_running = device_push_running.get(device_id)
    if push_running:
        push_running.set()
    push_thread = device_push_threads.pop(device_id, None)
    if push_thread and push_thread.is_alive():
        try:
            push_thread.join(timeout=3)
        except:
            pass

    # 清理资源
    if cap is not None:
        cap.release()
        device_caps.pop(device_id, None)
    if pusher_process and pusher_process.poll() is None:
        try:
            pusher_process.stdin.close()
            pusher_process.terminate()
            pusher_process.wait(timeout=2)
        except:
            if pusher_process.poll() is None:
                pusher_process.kill()
        device_pushers.pop(device_id, None)

    # 停止stderr读取线程
    stderr_thread = device_pusher_stderr_threads.pop(device_id, None)
    if stderr_thread and stderr_thread.is_alive():
        try:
            stderr_thread.join(timeout=1)
        except:
            pass

    # 清理stderr缓冲区
    device_pusher_stderr_buffers.pop(device_id, None)
    device_pusher_stderr_locks.pop(device_id, None)

    logger.info(f"💾 设备 {device_id} 缓流器线程停止")


def draw_detections(frame, tracked_detections, frame_number=None, tracking_enabled=False):
    """在帧上绘制检测结果

    Args:
        frame: 输入帧
        tracked_detections: 检测结果列表
        frame_number: 帧号
        tracking_enabled: 是否启用追踪
            - False: 画框 + 显示类别名（text）
            - True: 画框 + 显示类别名 + ID（text），不画卡片
    """
    import cv2
    from datetime import datetime

    if not tracked_detections:
        return frame

    annotated_frame = frame.copy()

    for tracked_det in tracked_detections:
        bbox = tracked_det.get('bbox', [])
        if not bbox or len(bbox) != 4:
            continue

        x1, y1, x2, y2 = bbox
        # 确保坐标在有效范围内
        h, w = annotated_frame.shape[:2]
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(x1 + 1, min(x2, w))
        y2 = max(y1 + 1, min(y2, h))

        class_name = tracked_det.get('class_name', 'unknown')
        confidence = tracked_det.get('confidence', 0.0)
        track_id = tracked_det.get('track_id', 0)
        is_cached = tracked_det.get('is_cached', False)
        first_seen_time = tracked_det.get('first_seen_time', time.time())
        duration = tracked_det.get('duration', 0.0)

        # 根据是否为缓存框选择颜色和样式
        if is_cached:
            color = (0, 200, 0)  # 稍暗的亮绿色
            thickness = 2
            alpha = 0.7
        else:
            color = (0, 255, 0)  # 亮绿色 (BGR格式)
            thickness = 2
            alpha = 1.0

        # 画框
        if is_cached:
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness)
            cv2.addWeighted(overlay, alpha, annotated_frame, 1 - alpha, 0, annotated_frame)
        else:
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)

        # 绘制文字标签（根据是否启用追踪显示不同内容）
        font_scale = 0.8  # 增大字体
        font_thickness = 2  # 加粗字体

        # 根据是否启用追踪决定显示内容
        if tracking_enabled:
            # 启用追踪：显示类别名 + ID
            text = f"ID:{track_id} {class_name}"
        else:
            # 未启用追踪：只显示类别名
            text = class_name

        # 在框的上方显示文字；中文类别使用 Pillow + CJK 字体绘制
        draw_detection_label(
            annotated_frame,
            text,
            x1,
            y1,
            color,
            font_scale=font_scale,
            font_thickness=font_thickness,
        )

    return annotated_frame


def overlay_detection_worker(worker_id: int):
    """主画面 overlay 检测线程：仅更新叠框缓存，不参与推流阻塞（推流侧读缓存即时叠框）。"""
    logger.info(f"🖼️  Overlay检测线程 {worker_id} 启动（主画面叠框专用）")

    consecutive_errors = 0
    max_consecutive_errors = 10
    idle_count = 0

    while not stop_event.is_set():
        try:
            detection_data, device_id, _ = _poll_device_detection_queue(overlay_detection_queues, timeout=0.1)

            if detection_data is not None:
                frame = detection_data['frame']
                frame_number = detection_data['frame_number']
                timestamp = detection_data['timestamp']
                device_id_from_data = detection_data.get('device_id', device_id)
                frame_id = detection_data.get('frame_id', f"{device_id_from_data}_frame_{frame_number}")

                consecutive_errors = 0
                idle_count = 0

                if frame_number % 10 == 0:
                    logger.info(f"🔍 [Overlay {worker_id}] 开始检测: {frame_id}")

                try:
                    _, detections = _run_yolo_on_frame(
                        frame,
                        device_id_from_data,
                        frame_number=frame_number,
                        timestamp=timestamp,
                        imgsz=OVERLAY_YOLO_IMG_SIZE,
                        use_tracking=OVERLAY_USE_TRACKING,
                    )
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"❌ Overlay检测异常: {str(e)} (连续错误: {consecutive_errors})", exc_info=True)
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("❌ Overlay连续错误过多，等待10秒后继续...")
                        time.sleep(10)
                        consecutive_errors = 0
                    continue

                cache_updated = _update_device_latest_overlay(
                    device_id_from_data,
                    detections,
                    timestamp,
                    frame_number,
                    applied_at=time.time(),
                )

                if frame_number % 10 == 0:
                    lag = frame_counts.get(device_id_from_data, frame_number) - frame_number
                    lag_hint = f", 队列滞后 {lag} 帧" if lag > _overlay_stale_frame_lag() // 2 else ""
                    stale_hint = '' if cache_updated else ', 积压过期未写缓存'
                    logger.info(
                        f"✅ [Overlay {worker_id}] 检测完成: {frame_id} (帧号: {frame_number}), "
                        f"{'更新' if cache_updated else '跳过'} overlay 缓存 {len(detections)} 个目标 "
                        f"[{_summarize_detections(detections)}]"
                        f"{lag_hint}{stale_hint}"
                    )
            else:
                idle_count += 1
                sleep_time = min(0.05 * (2 ** idle_count), 1.0)
                time.sleep(sleep_time)

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ Overlay检测异常: {str(e)} (连续错误: {consecutive_errors})", exc_info=True)
            if consecutive_errors >= max_consecutive_errors:
                logger.error("❌ Overlay连续错误过多，等待10秒后继续...")
                time.sleep(10)
                consecutive_errors = 0
            else:
                time.sleep(1)

    logger.info(f"🖼️  Overlay检测线程 {worker_id} 停止")


def alert_detection_worker(worker_id: int):
    """告警检测线程：独立队列，检测完成后直接发告警，不阻塞主画面。"""
    logger.info(f"🔔 告警检测线程 {worker_id} 启动（告警专用）")

    consecutive_errors = 0
    max_consecutive_errors = 10
    idle_count = 0

    while not stop_event.is_set():
        try:
            detection_data, device_id, _ = _poll_device_detection_queue(alert_detection_queues, timeout=0.1)

            if detection_data is not None:
                frame = detection_data['frame']
                frame_number = detection_data['frame_number']
                timestamp = detection_data['timestamp']
                device_id_from_data = detection_data.get('device_id', device_id)
                frame_id = detection_data.get('frame_id', f"{device_id_from_data}_frame_{frame_number}")

                consecutive_errors = 0
                idle_count = 0

                if frame_number % 10 == 0:
                    logger.info(f"🔍 [Alert {worker_id}] 开始检测: {frame_id}")

                try:
                    tracked_detections, detections = _run_yolo_on_frame(
                        frame,
                        device_id_from_data,
                        frame_number=frame_number,
                        timestamp=timestamp,
                        imgsz=YOLO_IMG_SIZE,
                        use_tracking=True,
                    )
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"❌ 告警检测异常: {str(e)} (连续错误: {consecutive_errors})", exc_info=True)
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("❌ 告警连续错误过多，等待10秒后继续...")
                        time.sleep(10)
                        consecutive_errors = 0
                    continue

                fresh_detections = [d for d in detections if not d.get('is_cached')]
                if fresh_detections:
                    _update_device_latest_overlay(
                        device_id_from_data,
                        fresh_detections,
                        timestamp,
                        frame_number,
                        applied_at=time.time(),
                    )

                if not detections:
                    continue

                if tracked_detections:
                    alert_frame = draw_detections(
                        frame,
                        tracked_detections,
                        frame_number,
                        tracking_enabled=bool(task_config and task_config.tracking_enabled),
                    )
                else:
                    alert_frame = frame.copy()

                device_name = device_id_from_data
                if task_config and hasattr(task_config, 'device_streams'):
                    stream_info = task_config.device_streams.get(device_id_from_data, {})
                    device_name = stream_info.get('device_name', device_id_from_data)

                from app.utils.post_process_runner import task_needs_sink_processing
                sink_enabled = task_needs_sink_processing(task_config)
                if sink_enabled:
                    alert_image_path = None
                    if detections:
                        alert_image_path = save_alert_image(
                            alert_frame,
                            device_id_from_data,
                            frame_number,
                            detections[0],
                        )
                    try:
                        from app.utils.post_process_runner import enqueue_post_process_request
                        enqueue_post_process_request(
                            task_config,
                            device_id=device_id_from_data,
                            device_name=device_name,
                            frame_number=frame_number,
                            timestamp=timestamp,
                            detections=detections,
                            tracked_detections=tracked_detections,
                            alert_image_path=alert_image_path,
                        )
                    except Exception as pp_exc:
                        logger.warning('后处理请求投递异常: %s', pp_exc)
                else:
                    if detections:
                        try_send_alert_for_detections(
                            device_id_from_data,
                            device_name,
                            frame_number,
                            detections,
                            alert_frame,
                            timestamp,
                        )

                if frame_number % 10 == 0:
                    logger.info(
                        f"✅ [Alert {worker_id}] 检测完成: {frame_id} (帧号: {frame_number}), "
                        f"本帧检出 {len(fresh_detections)} 个目标 [{_summarize_detections(fresh_detections)}]"
                        + (
                            f"（含缓存轨迹共 {len(detections)} 个）"
                            if len(detections) != len(fresh_detections)
                            else ""
                        )
                    )
            else:
                idle_count += 1
                sleep_time = min(0.05 * (2 ** idle_count), 1.0)
                time.sleep(sleep_time)

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ 告警检测异常: {str(e)} (连续错误: {consecutive_errors})", exc_info=True)
            if consecutive_errors >= max_consecutive_errors:
                logger.error("❌ 告警连续错误过多，等待10秒后继续...")
                time.sleep(10)
                consecutive_errors = 0
            else:
                time.sleep(1)

    logger.info(f"🔔 告警检测线程 {worker_id} 停止")


def shutdown_yolo_workers(timeout: float = 8.0):
    """停止 overlay/alert 检测线程并释放模型，避免停机时 CUDA/ORT 仍在推理。"""
    global overlay_executor, alert_executor, yolo_models, yolo_model_devices

    stop_event.set()

    for label, executor in (('Overlay', overlay_executor), ('Alert', alert_executor)):
        if executor:
            logger.info(f"🛑 等待{label}检测线程结束...")
            try:
                executor.shutdown(wait=True, cancel_futures=True)
            except TypeError:
                executor.shutdown(wait=True)
            logger.info(f"✅ {label}检测线程已结束")

    overlay_executor = None
    alert_executor = None

    stop_face_capture_workers()
    stop_plate_capture_workers()

    yolo_models.clear()
    yolo_model_devices.clear()
    yolo_model_meta.clear()


def cleanup_all_resources():
    """清理所有资源（FFmpeg进程、VideoCapture等）"""
    logger.info("🧹 开始清理所有资源...")

    # 停止所有固定速率推帧线程
    for device_id, push_running in list(device_push_running.items()):
        if push_running:
            push_running.set()
    for device_id, push_thread in list(device_push_threads.items()):
        if push_thread and push_thread.is_alive():
            try:
                push_thread.join(timeout=2)
            except:
                pass
    device_push_threads.clear()
    device_push_running.clear()
    device_output_frames.clear()
    device_latest_overlays.clear()
    device_latest_overlay_locks.clear()

    # 清理所有FFmpeg推送进程
    for device_id, pusher_process in list(device_pushers.items()):
        if pusher_process and pusher_process.poll() is None:
            try:
                logger.info(f"🛑 停止设备 {device_id} 的FFmpeg推送进程 (PID: {pusher_process.pid})")
                pusher_process.stdin.close()
                pusher_process.terminate()
                try:
                    pusher_process.wait(timeout=3)
                    logger.info(f"✅ 设备 {device_id} 的FFmpeg推送进程已停止")
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️ 设备 {device_id} 的FFmpeg推送进程未在3秒内退出，强制终止")
                    pusher_process.kill()
                    pusher_process.wait(timeout=1)
            except Exception as e:
                logger.error(f"❌ 停止设备 {device_id} 的FFmpeg推送进程失败: {str(e)}")
                try:
                    if pusher_process.poll() is None:
                        pusher_process.kill()
                except:
                    pass
        device_pushers.pop(device_id, None)

    # 清理所有VideoCapture对象
    for device_id, cap in list(device_caps.items()):
        if cap is not None:
            try:
                logger.info(f"🛑 释放设备 {device_id} 的VideoCapture")
                cap.release()
            except Exception as e:
                logger.error(f"❌ 释放设备 {device_id} 的VideoCapture失败: {str(e)}")
        device_caps.pop(device_id, None)

    # 清理stderr读取线程
    for device_id, stderr_thread in list(device_pusher_stderr_threads.items()):
        if stderr_thread and stderr_thread.is_alive():
            try:
                stderr_thread.join(timeout=1)
            except:
                pass
        device_pusher_stderr_threads.pop(device_id, None)

    # 清理YOLO线程池（若 signal_handler 已调用 shutdown_yolo_workers 则此处为空操作）
    shutdown_yolo_workers()

    # 清理其他资源
    device_pusher_stderr_buffers.clear()
    device_pusher_stderr_locks.clear()

    logger.info("✅ 所有资源已清理")


def signal_handler(sig, frame):
    """信号处理器"""
    logger.info("\n🛑 收到停止信号，正在关闭所有服务...")

    # 先停推理线程，再清理 FFmpeg/VideoCapture，避免停机时 ORT GPU↔CPU 拷贝报错
    shutdown_yolo_workers()

    # 清理所有资源（FFmpeg进程、VideoCapture等）
    cleanup_all_resources()

    # 等待工作线程收尾（缩短等待，避免外部 SIGKILL 与优雅退出竞态）
    logger.info("⏳ 等待所有线程结束...")
    time.sleep(0.5)

    logger.info("✅ 所有服务已停止")
    sys.exit(0)


def main():
    """主函数"""
    global overlay_executor, alert_executor, OVERLAY_WORKER_THREADS, ALERT_WORKER_THREADS

    logger.info("=" * 60)
    logger.info("🚀 统一的实时算法任务服务启动（优化模式：低CPU占用）")
    logger.info("=" * 60)
    logger.info("📊 优化配置参数:")
    logger.info(f"   视频分辨率: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    logger.info(f"   观感推流帧率: {AI_OUTPUT_FPS}fps（与 AI 抽帧 EXTRACT_INTERVAL 解耦）")
    logger.info(f"   FFmpeg编码预设: {FFMPEG_PRESET}")
    logger.info(f"   视频比特率: {FFMPEG_VIDEO_BITRATE}")
    logger.info(f"   GOP大小: {FFMPEG_GOP_SIZE} (约2秒一个关键帧)")
    logger.info(f"   编码线程数: {FFMPEG_THREADS if FFMPEG_THREADS else '自动'}")
    logger.info(f"   YOLO检测分辨率: {YOLO_IMG_SIZE}")
    logger.info(f"   Overlay队列大小: {OVERLAY_DETECTION_QUEUE_SIZE}, Worker: {OVERLAY_WORKER_THREADS}, imgsz: {OVERLAY_YOLO_IMG_SIZE}")
    logger.info(f"   告警队列大小: {ALERT_DETECTION_QUEUE_SIZE}, Worker: {ALERT_WORKER_THREADS}")
    logger.info(f"   AI检测间隔(仅推理): overlay={OVERLAY_EXTRACT_INTERVAL}, alert={ALERT_EXTRACT_INTERVAL} (告警/任务DB优先; overlay不受DB extract_interval影响)")
    logger.info(f"   叠框追踪: OVERLAY_USE_TRACKING={OVERLAY_USE_TRACKING}")
    logger.info(f"   运动门控: MOTION_GATE_ENABLED={os.getenv('MOTION_GATE_ENABLED', 'false')}")
    logger.info(f"   Overlay保留最新帧: {OVERLAY_KEEP_LATEST} (阈值: {OVERLAY_KEEP_LATEST_THRESHOLD})")
    logger.info(f"   告警保留最新帧: {ALERT_KEEP_LATEST} (阈值: {ALERT_KEEP_LATEST_THRESHOLD})")
    logger.info(f"   主画面 overlay 最大复用: {_overlay_effective_max_age_sec():.2f}s (LATEST_OVERLAY_MAX_AGE_MS={LATEST_OVERLAY_MAX_AGE_MS or 'auto'})")
    logger.info(f"   告警 Hook URL: {ALERT_HOOK_URL}")
    logger.info("=" * 60)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 加载任务配置（失败不退出：定时重试，避免守护进程重启风暴）
    retry_interval = int(os.getenv('TASK_CONFIG_RETRY_INTERVAL', '10'))
    while not stop_event.is_set():
        ok = load_task_config()
        if ok:
            break
        logger.error(f"❌ 任务配置加载失败，将在 {retry_interval}s 后重试（不会退出进程）")
        for _ in range(retry_interval):
            if stop_event.is_set():
                break
            time.sleep(1)
    if stop_event.is_set():
        logger.info("收到停止信号，退出启动流程")
        return

    _refresh_opencv_ffmpeg_capture_options()
    _get_ffmpeg_caps()
    stagger_sec = _get_realtime_stream_stagger_sec()
    logger.info(
        f"   多路推流队列: max_muxing_queue_size={_resolve_realtime_mux_queue_size()}, "
        f"opencv_thread_queue_size={_opencv_thread_queue_log_label()}/路, "
        f"预期并发={_expected_realtime_stream_count()} 路, 建连错峰={stagger_sec:.1f}s/路"
    )

    # 为每个摄像头启动独立的缓流器线程（错峰建连，减轻 NVR 并发冲击）
    buffer_threads = []
    device_count = 0
    if hasattr(task_config, 'device_streams'):
        device_ids_ordered = list(task_config.device_streams.keys())
        device_count = len(device_ids_ordered)
        for idx, device_id in enumerate(device_ids_ordered):
            if idx > 0 and stagger_sec > 0:
                time.sleep(stagger_sec)
            logger.info(f"💾 启动设备 {device_id} 的缓流器线程...")
            buffer_thread = threading.Thread(target=buffer_streamer_worker, args=(device_id,), daemon=True)
            buffer_thread.start()
            buffer_threads.append(buffer_thread)

    # 按摄像头数量分配检测线程（默认每路 1 线程，受上限约束）
    OVERLAY_WORKER_THREADS = _resolve_worker_thread_count(
        device_count,
        thread_env='OVERLAY_WORKER_THREADS',
        auto_env='OVERLAY_WORKER_THREADS_AUTO',
        max_env='OVERLAY_WORKER_THREADS_MAX',
        default_max=12,
        default_fixed=1,
    )
    ALERT_WORKER_THREADS = _resolve_worker_thread_count(
        device_count,
        thread_env='ALERT_WORKER_THREADS',
        auto_env='ALERT_WORKER_THREADS_AUTO',
        max_env='ALERT_WORKER_THREADS_MAX',
        default_max=4,
        default_fixed=1,
    )
    logger.info(
        f"📊 检测线程分配: 摄像头={device_count}, "
        f"overlay_workers={OVERLAY_WORKER_THREADS}, alert_workers={ALERT_WORKER_THREADS}"
    )

    # 启动双队列检测线程：主画面 overlay + 告警分离（缓流器直投队列，无抽帧器中转）
    logger.info(f"🖼️  启动 {OVERLAY_WORKER_THREADS} 个 Overlay 检测线程（主画面叠框）...")
    overlay_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=OVERLAY_WORKER_THREADS,
        thread_name_prefix='overlay_worker',
    )
    for worker_id in range(1, OVERLAY_WORKER_THREADS + 1):
        overlay_executor.submit(overlay_detection_worker, worker_id)
        logger.info(f"   ✅ Overlay检测线程 {worker_id} 已启动")

    if task_config and task_config.alert_event_enabled:
        logger.info(f"🔔 启动 {ALERT_WORKER_THREADS} 个告警检测线程...")
        alert_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=ALERT_WORKER_THREADS,
            thread_name_prefix='alert_worker',
        )
        for worker_id in range(1, ALERT_WORKER_THREADS + 1):
            alert_executor.submit(alert_detection_worker, worker_id)
            logger.info(f"   ✅ 告警检测线程 {worker_id} 已启动")
    else:
        logger.info("🔔 告警事件未启用，跳过告警检测线程")

    if task_config and bool(getattr(task_config, 'face_matching_enabled', False)):
        logger.info(
            f"👤 启动人脸抓取独立队列: size={FACE_CAPTURE_QUEUE_SIZE}, "
            f"workers={FACE_CAPTURE_WORKER_THREADS}"
        )
        start_face_capture_workers(stop_event)
    else:
        logger.info("👤 人脸匹配未启用，跳过人脸抓取队列")

    if task_config and bool(getattr(task_config, 'plate_matching_enabled', False)):
        logger.info(
            f"🚗 启动车牌抓取独立队列: size={PLATE_CAPTURE_QUEUE_SIZE}, "
            f"workers={PLATE_CAPTURE_WORKER_THREADS}"
        )
        start_plate_capture_workers(stop_event)
    else:
        logger.info("🚗 车牌匹配未启用，跳过车牌抓取队列")

    # 启动心跳上报线程
    logger.info("💓 启动心跳上报线程...")
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()

    reload_interval = int(os.getenv('TASK_CONFIG_RELOAD_INTERVAL', '30'))
    logger.info(f"🔄 启动任务配置热更新线程（间隔 {reload_interval}s）...")
    config_reload_thread = threading.Thread(
        target=_task_config_reload_worker,
        args=(reload_interval,),
        daemon=True,
        name='task_config_reload',
    )
    config_reload_thread.start()

    # 启动SRS录像清理线程
    logger.info("🧹 启动SRS录像清理线程...")
    srs_cleanup_thread = threading.Thread(target=srs_recording_cleanup_worker, daemon=True)
    srs_cleanup_thread.start()

    # 启动追踪目标保存线程（如果启用追踪）
    if task_config and task_config.tracking_enabled:
        logger.info("💾 启动追踪目标保存线程...")
        tracking_save_thread = threading.Thread(target=save_tracking_targets_periodically, daemon=True)
        tracking_save_thread.start()

    logger.info("=" * 60)
    logger.info("✅ 所有服务已启动")
    logger.info("=" * 60)
    logger.info("按 Ctrl+C 停止所有服务")
    logger.info("=" * 60)

    # 主循环
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        logger.error(f"❌ 主循环异常: {str(e)}", exc_info=True)
        signal_handler(None, None)


if __name__ == "__main__":
    main()
