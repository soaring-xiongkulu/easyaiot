#!/usr/bin/env python3
"""
统一的抓拍算法任务服务程序
整合缓流器、抽帧器功能，按 Cron 抓拍，支持追踪和告警（不推流）
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
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
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
from app.utils.alert_images_paths import resolve_alert_images_root
from app.utils.decode.stream_adapter import is_async_stream, open_device_stream, stream_mode_label
from app.utils.cron_utils import (
    normalize_cron_for_croniter,
    snap_cron_interval_seconds,
    snap_cron_match_window_seconds,
    cron_slot_for_time,
)
from app.utils.onnx_inference import ONNXInference
try:
    from app.utils.utf8_detection_label import draw_detection_label
except ModuleNotFoundError as exc:
    if exc.name != "app.utils.utf8_detection_label":
        raise
    # EDGE/runtime 由 VIDEO 服务种子生成，但使用自身独立的公共运行库。
    from lib.utf8_detection_label import draw_detection_label
from app.utils.algo_model_detect import run_model_detection
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
    epoch_to_shanghai_datetime,
    now_shanghai_naive,
    resolve_alert_hook_url,
    resolve_face_matching_publish_url,
    resolve_plate_matching_publish_url,
)
from app.utils.rtsp_stream_utils import (
    build_opencv_ffmpeg_capture_options,
    effective_rtsp_transport,
    gb28181_async_queue_max,
    is_gb28181_source,
    is_likely_rtsp_flat_corrupt_frame,
    task_streams_prefer_tcp,
)


def _shanghai_time_str(timestamp: float) -> str:
    """Unix 时间戳格式化为东八区墙钟字符串（与告警/抓拍入库一致）。"""
    return epoch_to_shanghai_datetime(timestamp).strftime('%Y-%m-%d %H:%M:%S')


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
_EFFECTIVE_RTSP_TRANSPORT = effective_rtsp_transport("", "udp")

_OPENCV_FFMPEG_OPTIONS_CUSTOM = bool(os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS"))
if not _OPENCV_FFMPEG_OPTIONS_CUSTOM:
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = build_opencv_ffmpeg_capture_options(
        _EFFECTIVE_RTSP_TRANSPORT
    )

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
        "OpenCV RTSP: rtsp_transport=%s（由 AI_RTSP_TRANSPORT / OPENCV_FFMPEG_RTSP_TRANSPORT / "
        "FFMPEG_RTSP_TRANSPORT 决定；默认 udp；易丢包/跨主机可试 tcp）",
        _EFFECTIVE_RTSP_TRANSPORT,
    )

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
task_cron_expression = None  # 规范化后的 cron
yolo_models = {}
yolo_model_devices = {}  # {model_id: 'cpu' | 'cuda:N'}
# 为每个摄像头创建独立的追踪器
trackers = {}  # {device_id: SimpleTracker}
# 为每个摄像头创建独立的帧索引计数器
frame_counts = {}  # {device_id: int}
# 检测队列（缓流器 cron 抽帧直投，不经抽帧器中转）
detection_queues = {}  # {device_id: queue.Queue}
# 待完成抓拍的帧（仅用于超时回收，检测完成后由 Worker 直接发告警/入库）
pending_snapshots = {}  # {device_id: {frame_number: float}}  # frame_number -> timestamp
pending_snapshot_locks = {}  # {device_id: threading.Lock()}
# 摄像头流连接（FFmpeg 解码 / OpenCV / 异步缓冲）
device_caps = {}  # {device_id: FfmpegVideoStream | AsyncVideoStream | cv2.VideoCapture}
# 告警抑制：记录每个设备上次告警推送时间
last_alert_time = {}  # {device_id: timestamp}
alert_time_lock = threading.Lock()  # 告警时间戳锁，确保线程安全


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
yolo_executor = None  # YOLO 线程池（与 realtime_algorithm_service 一致）

# 配置参数（算法链路：解码/推理/画框输出）：优先 AI_*，其次 VIEW_*（与 stream_forward 对齐），再回退通用变量
SOURCE_FPS = int(os.getenv('AI_SOURCE_FPS', os.getenv('VIEW_SOURCE_FPS', os.getenv('SOURCE_FPS', '25'))))
TARGET_WIDTH = int(os.getenv('AI_TARGET_WIDTH', os.getenv('VIEW_TARGET_WIDTH', os.getenv('TARGET_WIDTH', '1280'))))
TARGET_HEIGHT = int(os.getenv('AI_TARGET_HEIGHT', os.getenv('VIEW_TARGET_HEIGHT', os.getenv('TARGET_HEIGHT', '720'))))
TARGET_RESOLUTION = (TARGET_WIDTH, TARGET_HEIGHT)
EXTRACT_INTERVAL = int(os.getenv('EXTRACT_INTERVAL', '2'))
BUFFER_SIZE = int(os.getenv('BUFFER_SIZE', '70'))
MIN_BUFFER_FRAMES = int(os.getenv('MIN_BUFFER_FRAMES', '15'))
MAX_WAIT_TIME = float(os.getenv('MAX_WAIT_TIME', '0.08'))
# 抓拍任务不推 RTMP，无 FFmpeg 编码阶段

# YOLO检测参数（优化以降低CPU占用）
YOLO_IMG_SIZE = int(os.getenv('YOLO_IMG_SIZE', '640'))  # 高清场景下提升小目标检测和叠框细节
# 队列大小配置（优化以处理高负载）
DETECTION_QUEUE_SIZE = int(os.getenv('DETECTION_QUEUE_SIZE', '20'))  # 抓拍低频，默认较小
# 检测队列积压时保留最新 cron 帧（默认开启）
DETECTION_KEEP_LATEST = os.getenv('DETECTION_KEEP_LATEST', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
DETECTION_KEEP_LATEST_THRESHOLD = int(
    os.getenv('DETECTION_KEEP_LATEST_THRESHOLD', str(max(2, DETECTION_QUEUE_SIZE // 2)))
)
# 检测工作线程数量
YOLO_WORKER_THREADS = int(os.getenv('YOLO_WORKER_THREADS', '1'))
SNAPSHOT_RESULT_MAX_WAIT_SEC = float(os.getenv('SNAPSHOT_RESULT_MAX_WAIT_SEC', '5.0'))
SNAPSHOT_CRON_WINDOW_SEC = float(os.getenv('SNAPSHOT_CRON_WINDOW_SEC', '5.0'))
SNAP_SAVE_CRON_FRAME = (os.getenv('SNAP_SAVE_CRON_FRAME', '1').strip().lower() not in ('0', 'false', 'no', 'off'))


def _env_gray_float(name: str, default: float) -> float:
    try:
        return float((os.getenv(name, str(default)).strip() or str(default)))
    except ValueError:
        return default


def _gray_frame_thresholds():
    return (
        _env_gray_float('AI_RTSP_GRAY_STD_MAX', 4.0),
        _env_gray_float('AI_RTSP_GRAY_MEAN_LO', 80.0),
        _env_gray_float('AI_RTSP_GRAY_MEAN_HI', 180.0),
    )
# 画质分档（算法链路）：优先 AI_VIDEO_QUALITY_PROFILE
VIDEO_QUALITY_PROFILE = os.getenv(
    'AI_VIDEO_QUALITY_PROFILE',
    os.getenv('VIEW_VIDEO_QUALITY_PROFILE', os.getenv('VIDEO_QUALITY_PROFILE', '')),
).strip().lower()
QUALITY_PROFILE_PRESETS = {
    'low': {
        'source_fps': 15,
        'target_width': 640,
        'target_height': 360,
        'yolo_img_size': 416,
    },
    'medium': {
        'source_fps': 20,
        'target_width': 1280,
        'target_height': 720,
        'yolo_img_size': 512,
    },
    'high': {
        'source_fps': 25,
        'target_width': 1280,
        'target_height': 720,
        'yolo_img_size': 640,
    },
}
if VIDEO_QUALITY_PROFILE in QUALITY_PROFILE_PRESETS:
    selected_profile = QUALITY_PROFILE_PRESETS[VIDEO_QUALITY_PROFILE]
    SOURCE_FPS = selected_profile['source_fps']
    TARGET_WIDTH = selected_profile['target_width']
    TARGET_HEIGHT = selected_profile['target_height']
    TARGET_RESOLUTION = (TARGET_WIDTH, TARGET_HEIGHT)
    YOLO_IMG_SIZE = selected_profile['yolo_img_size']
FACE_CLASS_KEYWORDS = ('face', 'facial', 'person_face', '人脸')
PLATE_CLASS_KEYWORDS = ('plate', 'license_plate', 'licence_plate', 'car_plate', '车牌')


def _normalize_detection_class_name(class_name: str) -> str:
    """标准化类别名，便于匹配中英文和不同命名风格。"""
    return str(class_name or '').strip().lower().replace('-', '_').replace(' ', '_')


def _is_face_class(class_name: str) -> bool:
    normalized = _normalize_detection_class_name(class_name)
    return any(keyword in normalized for keyword in FACE_CLASS_KEYWORDS)


def _is_plate_class(class_name: str) -> bool:
    normalized = _normalize_detection_class_name(class_name)
    return any(keyword in normalized for keyword in PLATE_CLASS_KEYWORDS)


def _should_keep_detection(class_name: str) -> bool:
    """
    根据任务配置过滤检测类别：
    - 关闭人脸检测时，过滤人脸类结果
    - 关闭车牌检测时，过滤车牌类结果
    """
    if not task_config:
        return True

    if _is_face_class(class_name) and not bool(getattr(task_config, 'face_detection_enabled', True)):
        return False
    if _is_plate_class(class_name) and not bool(getattr(task_config, 'plate_detection_enabled', True)):
        return False
    return True


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


def _get_minio_client():
    """算法子进程内创建 MinIO 客户端（与 download 逻辑共用环境变量）。"""
    endpoint = _normalize_minio_endpoint(os.getenv('MINIO_ENDPOINT', '').strip())
    if not endpoint:
        return None
    try:
        from minio import Minio
    except ImportError:
        return None
    access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def upload_frame_to_snap_space(device_id: str, frame: np.ndarray) -> bool:
    """将帧上传到设备抓拍空间（MinIO），不产生告警记录。"""
    import os
    try:
        from app.utils.snap_media_client import stage_snap_frame
        from app.services.media_kafka_service import is_snap_kafka_mode
        staging = os.getenv('MEDIA_SNAP_STAGING_ENABLED', '').lower() in ('1', 'true', 'yes')
        if staging or is_snap_kafka_mode():
            return stage_snap_frame(
                device_id, frame, source='algorithm', task_id=TASK_ID or None,
            )
    except Exception as staging_err:
        logger.debug('抓拍暂存/Kafka 路径不可用，回退直传 MinIO: %s', staging_err)

    import io
    import uuid as _uuid

    client = _get_minio_client()
    if client is None:
        logger.warning(f"设备 {device_id} MinIO 未配置，跳过抓拍空间上传")
        return False

    bucket_name = 'snap-space'
    try:
        app = get_flask_app()
        with app.app_context():
            from models import SnapSpace
            snap_space = SnapSpace.query.filter_by(device_id=device_id).first()
            if snap_space and snap_space.bucket_name:
                bucket_name = snap_space.bucket_name
    except Exception as e:
        logger.debug(f"查询抓拍空间失败，使用默认 bucket: {e}")

    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
    except Exception as e:
        logger.warning(f"检查/创建 bucket {bucket_name} 失败: {e}")
        return False

    ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        return False

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    object_name = f"{device_id}/{_uuid.uuid4().hex[:8]}_{ts}.jpg"
    data = encoded.tobytes()
    try:
        client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type='image/jpeg',
        )
        try:
            from app.services.space_file_metadata_service import upsert_snap_image
            _app = get_flask_app()
            with _app.app_context():
                from models import SnapSpace
                snap_space = SnapSpace.query.filter_by(device_id=device_id).first()
                if snap_space:
                    upsert_snap_image(
                        space_id=snap_space.id,
                        device_id=device_id,
                        object_name=object_name,
                        bucket_name=bucket_name,
                        file_size=len(data),
                        source='algorithm',
                        captured_at=now_shanghai_naive(),
                    )
        except Exception as meta_err:
            logger.debug(f"设备 {device_id} 写入抓拍元数据失败: {meta_err}")
        logger.info(f"📷 设备 {device_id} 已上传抓拍图: {bucket_name}/{object_name}")
        return True
    except Exception as e:
        logger.warning(f"设备 {device_id} 上传抓拍空间失败: {e}")
        return False


def _get_detect_conf() -> float:
    if task_config is not None:
        task_conf = getattr(task_config, 'detect_conf', None)
        if task_conf is not None:
            try:
                return float(task_conf)
            except (TypeError, ValueError):
                pass
    try:
        return float(os.getenv('YOLO_DETECT_CONF', '0.5'))
    except ValueError:
        return 0.5


def _get_device_name(device_id: str) -> str:
    if task_config and hasattr(task_config, 'device_streams'):
        info = task_config.device_streams.get(device_id, {})
        return info.get('device_name', device_id)
    return device_id


def _build_detection_payload(device_id: str, frame, frame_number: int, timestamp: float) -> dict:
    return {
        'frame_id': f"{device_id}_frame_{frame_number}_{int(timestamp)}",
        'frame': frame.copy(),
        'frame_number': frame_number,
        'timestamp': timestamp,
        'device_id': device_id,
    }


def _enqueue_detection_frame(device_id: str, payload: dict) -> bool:
    """cron 抽帧直投检测队列；积压时丢弃旧帧，仅保留最新待检帧。"""
    detection_queue = detection_queues.get(device_id)
    if not detection_queue:
        return False

    frame_number = payload.get('frame_number', 0)
    drained = 0

    if DETECTION_KEEP_LATEST and detection_queue.qsize() >= DETECTION_KEEP_LATEST_THRESHOLD:
        while True:
            try:
                detection_queue.get_nowait()
                drained += 1
            except queue.Empty:
                break
        if drained > 0:
            logger.info(
                f"🔄 设备 {device_id} 检测队列积压，丢弃 {drained} 帧旧数据，保留最新 cron 帧 {frame_number}"
            )

    try:
        detection_queue.put(payload, timeout=0.2)
        return True
    except queue.Full:
        if DETECTION_KEEP_LATEST:
            while True:
                try:
                    detection_queue.get_nowait()
                    drained += 1
                except queue.Empty:
                    break
            try:
                detection_queue.put(payload, timeout=0.05)
                return True
            except queue.Full:
                pass
        logger.warning(
            f"⚠️  设备 {device_id} 检测队列已满，丢弃 cron 帧 {frame_number}（队列大小: {DETECTION_QUEUE_SIZE}）"
        )
        return False


def _track_pending_snapshot(device_id: str, frame_number: int, timestamp: float):
    lock = pending_snapshot_locks.setdefault(device_id, threading.Lock())
    with lock:
        pending_snapshots.setdefault(device_id, {})[frame_number] = timestamp


def _untrack_pending_snapshot(device_id: str, frame_number: int):
    lock = pending_snapshot_locks.get(device_id)
    if not lock:
        return
    with lock:
        pending_snapshots.get(device_id, {}).pop(frame_number, None)


def _save_cron_snapshot_frame(
    device_id: str,
    frame_image,
    fn: int,
    frame_timestamp: float,
    *,
    has_detections: bool = False,
):
    """定时抓拍：写入抓拍空间（有/无检测目标均入库，告警另行发送）。"""
    if not (task_config and SNAP_SAVE_CRON_FRAME):
        return
    if frame_image is None or getattr(frame_image, 'size', 0) == 0:
        logger.warning(f"设备 {device_id} 定时抓拍跳过空帧: 帧 {fn}")
        return
    if is_likely_rtsp_flat_corrupt_frame(frame_image, *_gray_frame_thresholds()):
        logger.warning(f"设备 {device_id} 定时抓拍跳过疑似灰屏帧: 帧 {fn}")
        return
    try:
        if upload_frame_to_snap_space(device_id, frame_image):
            suffix = '含检测目标' if has_detections else '无检测目标'
            logger.info(f"📷 设备 {device_id} 定时抓拍已入库（{suffix}）: 帧 {fn}")
        else:
            save_alert_image(
                frame_image, device_id, fn, {'class_name': 'snapshot', 'track_id': 0}
            )
            logger.warning(
                f"设备 {device_id} 抓拍空间上传失败，已仅落盘 alert_images: 帧 {fn}"
            )
    except Exception as e:
        logger.error(f"设备 {device_id} 定时抓拍保存失败: {str(e)}", exc_info=True)


def _finish_snapshot_detection(
    device_id: str,
    frame_number: int,
    timestamp: float,
    detections: list,
    processed_frame,
):
    """检测完成后发告警（若有目标）并写入抓拍图库，不再经 push_queue 回写。"""
    _untrack_pending_snapshot(device_id, frame_number)
    device_name = _get_device_name(device_id)
    has_detections = bool(detections)
    from app.utils.post_process_runner import task_needs_sink_processing
    sink_enabled = task_needs_sink_processing(task_config)
    if has_detections and sink_enabled:
        alert_image_path = save_alert_image(
            processed_frame,
            device_id,
            frame_number,
            detections[0],
        )
        try:
            from app.utils.post_process_runner import enqueue_post_process_request
            enqueue_post_process_request(
                task_config,
                device_id=device_id,
                device_name=device_name,
                frame_number=frame_number,
                timestamp=timestamp,
                detections=detections,
                tracked_detections=detections,
                alert_image_path=alert_image_path,
            )
        except Exception as pp_exc:
            logger.warning('抓拍后处理请求投递异常: %s', pp_exc)
    elif has_detections:
        try_send_snapshot_detection_alert(
            device_id,
            device_name,
            frame_number,
            detections,
            processed_frame,
            timestamp,
        )
    _save_cron_snapshot_frame(
        device_id,
        processed_frame,
        frame_number,
        timestamp,
        has_detections=has_detections,
    )
    logger.info(f"✅ 设备 {device_id} cron 帧 {frame_number} 处理完成")


def _cleanup_stale_pending_snapshots(device_id: str):
    """回收超时仍未完成检测的 cron 帧，防止 pending 累积。"""
    now_ts = time.time()
    timed_out = []
    lock = pending_snapshot_locks.get(device_id)
    if not lock:
        return
    with lock:
        pending = pending_snapshots.get(device_id, {})
        for fn, frame_ts in list(pending.items()):
            if now_ts - frame_ts > SNAPSHOT_RESULT_MAX_WAIT_SEC:
                timed_out.append(fn)
        for fn in timed_out:
            pending.pop(fn, None)
    if timed_out:
        logger.warning(
            f"⚠️  设备 {device_id} 超时清理待检 cron 帧 {len(timed_out)} 个: {timed_out[:5]}"
            f"{'...' if len(timed_out) > 5 else ''}"
        )


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
    global yolo_model_devices
    yolo_model_devices.clear()
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
                    yolo_model = YOLO(model_path_str)
                    infer_device = get_infer_device(model_id)
                    models[model_id] = yolo_model
                    yolo_model_devices[model_id] = infer_device
                    logger.info(
                        f"✅ YOLO模型加载成功: model_id={model_id}, infer_device={infer_device}"
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
    global task_config, task_cron_expression, yolo_models, yolo_model_devices, tracker

    try:
        logger.info(f"🔄 正在从数据库重新加载任务配置: task_id={TASK_ID}")
        # 刷新数据库会话，确保获取最新数据
        db_session.expire_all()

        task = db_session.query(AlgorithmTask).filter_by(id=TASK_ID).first()
        if not task:
            logger.error(f"任务 {TASK_ID} 不存在")
            return False

        task_config = task

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

        # 从摄像头列表获取输入流地址（支持RTSP和RTMP）
        # 注意：抓拍算法任务不推流，只读取输入流
        device_streams = {}
        if task.devices:
            # 刷新设备关联关系，确保获取最新的设备信息
            db_session.refresh(task)
            for device in task.devices:
                # 刷新设备对象，确保获取最新的source
                db_session.refresh(device)
                # 输入流地址（支持RTSP/RTMP，以及通过gb28181://虚拟源动态解析）
                rtsp_url = resolve_gb28181_source(device.source, logger=logger) if device.source else None
                if not rtsp_url:
                    logger.warning(f"设备 {device.id} 未获取到可用输入流地址，跳过该设备")
                    continue
                device_streams[device.id] = {
                    'rtsp_url': rtsp_url,
                    'device_name': device.name or device.id,
                    'is_gb28181': is_gb28181_source(device.source),
                    'original_source': device.source,
                }
                input_type = "RTSP" if rtsp_url and rtsp_url.startswith(
                    'rtsp://') else "RTMP" if rtsp_url and rtsp_url.startswith('rtmp://') else "输入流"
                logger.info(f"📹 设备 {device.id} ({device.name or device.id}): {input_type}={rtsp_url}")

        # 将设备流地址信息存储到task_config中（通过动态属性）
        task_config.device_streams = device_streams

        # 为每个摄像头初始化独立的资源
        for device_id, stream_info in device_streams.items():
            frame_counts[device_id] = 0
            detection_queues[device_id] = queue.Queue(maxsize=DETECTION_QUEUE_SIZE)
            pending_snapshots[device_id] = {}
            pending_snapshot_locks[device_id] = threading.Lock()

            # 初始化cron相关变量（清理旧状态）
            if device_id in device_last_extract_cron_time:
                device_last_extract_cron_time.pop(device_id, None)

            # 初始化追踪器（如果启用）
            if task.tracking_enabled:
                trackers[device_id] = SimpleTracker(
                    similarity_threshold=task.tracking_similarity_threshold,
                    max_age=task.tracking_max_age,
                    smooth_alpha=task.tracking_smooth_alpha
                )
                logger.info(f"设备 {device_id} 追踪器初始化成功")

        # 记录并规范化 cron 表达式（仅加载时处理一次，避免每帧重复打日志）
        cron_expression = getattr(task, 'cron_expression', None)
        if cron_expression and cron_expression.strip():
            raw_cron = cron_expression.strip()
            task_cron_expression = normalize_cron_for_croniter(raw_cron)
            if task_cron_expression != raw_cron:
                logger.warning(
                    f"⏰ 抓拍算法任务 cron 已规范化: {raw_cron!r} -> {task_cron_expression!r}")
            try:
                _interval = snap_cron_interval_seconds(task_cron_expression)
                _win = snap_cron_match_window_seconds(task_cron_expression, SNAPSHOT_CRON_WINDOW_SEC)
                logger.info(
                    f"⏰ 抓拍算法任务已配置 cron: {task_cron_expression}，"
                    f"触发间隔约 {_interval:.0f}s，匹配窗口 {_win:.1f}s")
            except Exception as _e:
                logger.info(
                    f"⏰ 抓拍算法任务已配置cron表达式: {task_cron_expression}，将按cron时间执行抽帧")
                logger.debug(f"cron 间隔预计算失败: {_e}")
        else:
            task_cron_expression = None
            logger.info(f"⏰ 抓拍算法任务未配置cron表达式，将按抽帧间隔持续抽帧")

        _refresh_opencv_rtsp_options_for_streams(device_streams)

        logger.info(f"任务配置加载成功: {task.task_name}, 模型IDs: {model_ids}, 关联设备数: {len(device_streams)}")

        if task.tracking_enabled:
            logger.info(f"已为 {len(trackers)} 个设备初始化追踪器")

        return True
    except Exception as e:
        logger.error(f"加载任务配置失败: {str(e)}", exc_info=True)
        return False


# 存储每个设备上次抽帧的 cron 时间点（每个 cron 时刻只抽 1 帧）
device_last_extract_cron_time = {}
device_extract_cron_lock = threading.Lock()
device_cron_match_logged_slot = {}  # 已打过「cron 匹配」日志的槽位，避免刷屏
device_cron_gray_warn_slot = {}  # 已打过「cron 花屏跳过」警告的槽位

def _refresh_opencv_rtsp_options_for_streams(device_streams: dict) -> None:
    """HEVC / GB28181 任务将 OpenCV 拉流切换为 tcp（与 realtime 服务 .env 策略一致）。"""
    global _EFFECTIVE_RTSP_TRANSPORT
    if _OPENCV_FFMPEG_OPTIONS_CUSTOM or not device_streams:
        return
    if not task_streams_prefer_tcp(device_streams):
        return
    sample_url = next((info.get("rtsp_url") or "" for info in device_streams.values()), "")
    new_transport = effective_rtsp_transport(sample_url, _EFFECTIVE_RTSP_TRANSPORT)
    if new_transport == _EFFECTIVE_RTSP_TRANSPORT:
        return
    _EFFECTIVE_RTSP_TRANSPORT = new_transport
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = build_opencv_ffmpeg_capture_options(
        _EFFECTIVE_RTSP_TRANSPORT
    )
    logger.info(
        "检测到 GB28181/HEVC RTSP 输入，已将 rtsp_transport 切换为 %s（与 realtime_algorithm_service 对齐）",
        _EFFECTIVE_RTSP_TRANSPORT,
    )

def should_extract_frame_by_cron(device_id: str, current_time: float) -> bool:
    """检查当前时间是否匹配 cron（6 段秒级表达式需 second_at_beginning）。

    仅在成功抓拍后由缓流器标记 device_last_extract_cron_time，避免灰屏/花屏导致整槽浪费。
    """
    global task_config, task_cron_expression, device_last_extract_cron_time
    global device_cron_match_logged_slot

    if not task_config:
        return True
    if not task_cron_expression:
        return True

    try:
        in_window, fire_time, offset_sec = cron_slot_for_time(
            task_cron_expression, current_time
        )
        if not in_window or fire_time is None:
            return False

        with device_extract_cron_lock:
            last_done = device_last_extract_cron_time.get(device_id)
            if last_done is not None and last_done == fire_time:
                return False
            if device_cron_match_logged_slot.get(device_id) != fire_time:
                device_cron_match_logged_slot[device_id] = fire_time
                current_dt = epoch_to_shanghai_datetime(current_time)
                logger.info(
                    f"⏰ 设备 {device_id} cron 匹配，允许抽帧: "
                    f"当前={current_dt.strftime('%H:%M:%S')}, "
                    f"槽位={fire_time.strftime('%H:%M:%S')}, "
                    f"距槽位 {offset_sec:.2f}s"
                )
        return True

    except Exception as e:
        logger.error(
            f"❌ 设备 {device_id} 检查 cron 失败: cron={task_cron_expression}, error={str(e)}",
            exc_info=True,
        )
        return False


def try_send_snapshot_detection_alert(
    device_id: str,
    device_name: str,
    frame_number: int,
    detections: list,
    frame_image: np.ndarray,
    frame_timestamp: float,
) -> None:
    """有真实检测目标时上报告警（带检测框的图），无检测不调用。"""
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
                f"⏸️  设备 {device_id} 抓拍告警抑制：距上次 {time_since_last_alert:.2f} 秒，"
                f"需间隔 {suppress_interval} 秒，帧 {frame_number}，{len(detections)} 个目标"
            )
            return
        last_alert_time[device_id] = current_time

    object_counts: Dict[str, int] = {}
    all_info = []
    for det in detections:
        cn = det.get('class_name', 'unknown')
        object_counts[cn] = object_counts.get(cn, 0) + 1
        all_info.append({
            'track_id': det.get('track_id', 0),
            'class_name': cn,
            'confidence': det.get('confidence', 0),
            'bbox': det.get('bbox', []),
        })
    primary = max(object_counts.items(), key=lambda x: x[1])[0] if object_counts else 'unknown'

    image_path = save_alert_image(
        frame_image,
        device_id,
        frame_number,
        detections[0],
    )
    algorithm_name = getattr(task_config, 'task_name', None) or 'detection'
    correlation_id = str(uuid.uuid4())
    alert_data = {
        'object': primary,
        'event': algorithm_name,
        'device_id': device_id,
        'device_name': device_name,
        'face_detection_enabled': bool(getattr(task_config, 'face_detection_enabled', False)),
        'plate_detection_enabled': bool(getattr(task_config, 'plate_detection_enabled', False)),
        'time': _shanghai_time_str(frame_timestamp),
        'correlation_id': correlation_id,
        'information': json.dumps({
            'total_count': len(detections),
            'object_counts': object_counts,
            'detections': all_info,
            'frame_number': frame_number,
            'correlation_id': correlation_id,
            'task_type': 'snapshot',
            'cron_capture': False,
        }),
        'image_path': image_path,
    }
    logger.info(
        f"🚨 设备 {device_id} 检测告警: 帧 {frame_number}, "
        f"{len(detections)} 个目标 {object_counts}, correlation_id={correlation_id}"
    )
    send_alert_event_async(alert_data)
    try_send_face_matching_for_frame(
        device_id=device_id,
        device_name=device_name,
        frame_for_image=frame_image,
        frame_number=frame_number,
        correlation_id=correlation_id,
        source_event=algorithm_name,
    )
    try_send_plate_matching_for_frame(
        device_id=device_id,
        device_name=device_name,
        frame_for_image=frame_image,
        frame_number=frame_number,
        correlation_id=correlation_id,
    )


def mark_cron_slot_captured(device_id: str, current_time: float) -> None:
    """成功入队抓拍帧后标记当前 cron 槽位已完成。"""
    global task_cron_expression, device_last_extract_cron_time, device_cron_match_logged_slot
    global device_cron_gray_warn_slot
    if not task_cron_expression:
        return
    try:
        _, fire_time, _ = cron_slot_for_time(task_cron_expression, current_time)
        if fire_time is None:
            return
        with device_extract_cron_lock:
            device_last_extract_cron_time[device_id] = fire_time
            device_cron_match_logged_slot.pop(device_id, None)
            device_cron_gray_warn_slot.pop(device_id, None)
    except Exception:
        pass

def _post_snapshot_alert(alert_data: Dict) -> None:
    """POST 抓拍/告警到 hook（cron 整帧抓拍始终发送；目标告警受 alert_event_enabled 控制）。"""
    info_raw = alert_data.get('information')
    is_cron_capture = False
    if isinstance(info_raw, str):
        try:
            is_cron_capture = bool(json.loads(info_raw).get('cron_capture'))
        except Exception:
            pass
    elif isinstance(info_raw, dict):
        is_cron_capture = bool(info_raw.get('cron_capture'))

    if task_config and not task_config.alert_event_enabled and not is_cron_capture:
        return

    try:
        alert_data['task_type'] = 'snapshot'
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
            headers={'Content-Type': 'application/json'},
        )
        if response.status_code != 200:
            logger.warning(
                f"发送抓拍/告警到 hook 失败: status={response.status_code}, "
                f"device_id={alert_data.get('device_id')}, body={response.text[:200]}"
            )
    except requests.exceptions.RequestException as e:
        logger.warning(f"发送抓拍/告警到 hook 异常: {e}, URL={ALERT_HOOK_URL}")


def send_alert_event_async(alert_data: Dict):
    """异步发送告警事件到 sink hook 接口（后台线程）- 抓拍算法任务专用"""

    def _send():
        try:
            device_id = alert_data.get('device_id')
            if not task_config:
                return
            if not task_config.alert_event_enabled:
                info_raw = alert_data.get('information')
                is_cron = False
                if isinstance(info_raw, str):
                    try:
                        is_cron = bool(json.loads(info_raw).get('cron_capture'))
                    except Exception:
                        pass
                if not is_cron:
                    logger.warning(
                        f"⚠️  告警事件未启用，跳过发送: device_id={device_id}")
                    return

            logger.info(
                f"🚨 开始异步发送告警事件: device_id={device_id}, object={alert_data.get('object')}, "
                f"event={alert_data.get('event')}, URL={ALERT_HOOK_URL}")

            # 通过 HTTP 发送告警事件到 sink hook 接口
            # sink 会负责将告警投入 Kafka
            try:
                # 标记为抓拍算法任务（确保task_type正确传递）
                alert_data['task_type'] = 'snapshot'
                # 检测开关由算法服务透传给 alert_hook_service，避免 alert_hook_service 再查库
                if 'face_detection_enabled' not in alert_data:
                    alert_data['face_detection_enabled'] = bool(
                        getattr(task_config, 'face_detection_enabled', False)
                    )
                if 'plate_detection_enabled' not in alert_data:
                    alert_data['plate_detection_enabled'] = bool(
                        getattr(task_config, 'plate_detection_enabled', False)
                    )
                # 如果information是字典，也添加task_type
                if 'information' in alert_data and isinstance(alert_data['information'], dict):
                    alert_data['information']['task_type'] = 'snapshot'
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
                        f"✅ 告警事件已成功处理: device_id={device_id}, "
                        f"object={alert_data.get('object')}, mode={mode}"
                        + (f", alert_id={alert_id}" if alert_id else "")
                    )
                elif response.status_code == 200 and hook_status in ('skipped', 'suppressed'):
                    logger.warning(
                        f"⚠️ 告警被 hook 跳过: device_id={device_id}, "
                        f"status={hook_status}, reason={hook_result.get('reason')}"
                    )
                else:
                    logger.warning(
                        f"❌ 发送告警事件到 hook 失败: status_code={response.status_code}, "
                        f"hook_status={hook_status}, response={response.text}, "
                        f"device_id={device_id}"
                    )
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"❌ 发送告警事件到 hook 异常: {str(e)}, URL={ALERT_HOOK_URL}, "
                    f"device_id={device_id}"
                )
        except Exception as e:
            logger.error(f"❌ 发送告警事件失败: device_id={alert_data.get('device_id')}, error={str(e)}", exc_info=True)

    # 在后台线程中异步执行
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()

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


def save_face_crop_image(frame: np.ndarray, device_id: str, frame_number: int, detection: Dict) -> Optional[str]:
    try:
        bbox = detection.get('bbox') or []
        if len(bbox) < 4:
            return None
        x1, y1, x2, y2 = [int(v) for v in bbox[:4]]
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return None
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        images_root = os.getenv('FACE_IMAGES_DIR', os.path.join(video_root, 'data', 'face_images'))
        face_dir = os.path.join(images_root, f'task_{TASK_ID}', device_id, 'matching')
        os.makedirs(face_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        track_id = detection.get('track_id', 0)
        image_filename = f"{timestamp}_frame{frame_number}_track{track_id}_face.jpg"
        image_path = os.path.join(face_dir, image_filename)
        cv2.imwrite(image_path, crop)
        return image_path
    except Exception as e:
        logger.error(f"保存人脸裁剪图失败: {str(e)}", exc_info=True)
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
    if not task_config or not bool(getattr(task_config, 'face_matching_enabled', False)):
        return
    from models import AlgorithmTask
    library_ids = AlgorithmTask._parse_library_ids(getattr(task_config, 'face_library_ids', None))
    if not library_ids:
        return
    if not face_capture_queue_running():
        return

    enqueue_face_capture(
        frame=frame_for_image,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        task_id=TASK_ID,
        task_name=getattr(task_config, 'task_name', ''),
        task_type='snap',
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
    if not task_config or not bool(getattr(task_config, 'plate_matching_enabled', False)):
        return
    from models import AlgorithmTask
    library_ids = AlgorithmTask._parse_library_ids(getattr(task_config, 'plate_library_ids', None))
    if not library_ids:
        return
    if not plate_capture_queue_running():
        return

    enqueue_plate_capture(
        frame=frame_for_image,
        device_id=device_id,
        device_name=device_name,
        frame_number=frame_number,
        task_id=TASK_ID,
        task_name=getattr(task_config, 'task_name', ''),
        task_type='snap',
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

        # 构建心跳URL
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


def buffer_streamer_worker(device_id: str):
    """缓流器：拉源流，cron 槽位抽帧直投检测队列，不阻塞等待检测结果。"""
    logger.info(f"💾 缓流器线程启动 [设备: {device_id}]")

    if not task_config or not hasattr(task_config, 'device_streams'):
        logger.error(f"任务配置未加载，设备 {device_id} 缓流器退出")
        return

    device_stream_info = task_config.device_streams.get(device_id)
    if not device_stream_info:
        logger.error(f"设备 {device_id} 流信息不存在，缓流器退出")
        return

    rtsp_url = device_stream_info.get('rtsp_url')
    device_name = device_stream_info.get('device_name', device_id)
    _is_gb28181 = device_stream_info.get('is_gb28181', False)
    _original_source = device_stream_info.get('original_source')
    _last_gb28181_resolve_time = 0.0

    # 打印输入流地址信息
    logger.info(f"📺 设备 {device_id} 流地址配置:")
    input_stream_type = "RTSP" if rtsp_url and rtsp_url.startswith(
        'rtsp://') else "RTMP" if rtsp_url and rtsp_url.startswith('rtmp://') else "输入流"
    logger.info(f"   {input_stream_type}输入流: {rtsp_url}")

    if not rtsp_url:
        logger.error(f"设备 {device_id} 输入流地址不存在，缓流器退出")
        return

    # 兼容 RTSP 和 RTMP 两种格式的输入流
    stream_type = "RTSP" if rtsp_url.startswith('rtsp://') else "RTMP" if rtsp_url.startswith('rtmp://') else "未知"
    logger.info(f"📡 设备 {device_id} 输入流类型: {stream_type}")

    cap = None
    frame_width = None
    frame_height = None
    retry_count = 0
    max_retries = 5
    rtsp_open_timeout_msec = int(os.getenv("RTSP_OPEN_TIMEOUT_MSEC", "5000"))
    rtsp_read_timeout_msec = int(os.getenv("RTSP_READ_TIMEOUT_MSEC", "2500"))
    rtsp_retry_delay_sec = max(0.1, float(os.getenv("RTSP_RETRY_DELAY_SEC", "1")))
    rtsp_retry_cooldown_sec = max(1.0, float(os.getenv("RTSP_RETRY_COOLDOWN_SEC", "8")))
    rtsp_read_fail_delay_sec = max(0.1, float(os.getenv("RTSP_READ_FAIL_DELAY_SEC", "0.3")))

    # 流畅度优化：基于时间戳的帧率控制
    frame_interval = 1.0 / SOURCE_FPS
    last_frame_time = time.time()

    # 灰屏重连（默认开启；与实时算法服务一致，见 AI_RTSP_GRAY_*）
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
    if _is_gb28181:
        logger.info(
            f"📌 设备 {device_id} GB28181 源：重连时将重新解析播放地址；"
            f"异步 FIFO={gb28181_async_queue_max()}（AI_GB28181_ASYNC_QUEUE_MAX，与 realtime 一致）"
        )

    while not stop_event.is_set():
        try:
            # 打开源流（支持 RTSP 和 RTMP）
            if cap is None or not cap.isOpened():
                # GB28181：重连时重新解析（会话过期后旧 RTSP URL 失效），与 realtime_algorithm_service 一致
                if _is_gb28181 and _original_source:
                    _resolve_elapsed = time.time() - _last_gb28181_resolve_time
                    if _resolve_elapsed >= 30.0:
                        _last_gb28181_resolve_time = time.time()
                        _new_url = resolve_gb28181_source(_original_source, logger=logger)
                        if _new_url and _new_url != rtsp_url:
                            logger.info(f"📌 设备 {device_id} GB28181 源重新解析: {rtsp_url} -> {_new_url}")
                            rtsp_url = _new_url
                            device_stream_info['rtsp_url'] = _new_url
                            retry_count = 0
                        elif _new_url:
                            logger.info(f"📌 设备 {device_id} GB28181 源重新解析（URL 未变）: {rtsp_url}")
                        else:
                            logger.warning(
                                f"⚠️ 设备 {device_id} GB28181 源重新解析失败，使用上次 URL 重试"
                            )

                stream_type = "RTSP" if rtsp_url.startswith('rtsp://') else "RTMP" if rtsp_url.startswith(
                    'rtmp://') else "流"

                logger.info(f"正在连接设备 {device_id} 的 {stream_type} 流: {rtsp_url} (重试次数: {retry_count})")

                _queue_max_override = None
                if _is_gb28181:
                    _gb_fifo = gb28181_async_queue_max()
                    if _gb_fifo > 1:
                        _queue_max_override = _gb_fifo

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
                logger.info(f"📌 设备 {device_id} {stream_mode_label(cap)}")
                device_caps[device_id] = cap
                logger.info(f"✅ 设备 {device_id} {stream_type} 流连接成功")
                if rtsp_url.startswith("rtsp://"):
                    last_rtsp_connect_time = time.time()

            # 从源流读取帧（异步模式下由后台线程 decode，此处取缓冲区最新帧）
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
                    time.sleep(min(frame_interval * 0.5, 0.02))
                    continue
                logger.warning(f"设备 {device_id} 读取源流帧失败，重新连接...")
                if cap is not None:
                    cap.release()
                    cap = None
                    device_caps.pop(device_id, None)
                gray_bad_streak = 0
                time.sleep(rtsp_read_fail_delay_sec)
                continue

            # 与 realtime 一致：预热期内不判灰屏，避免 HEVC 起播期无法进入 cron 抓拍
            if (
                rtsp_url.startswith("rtsp://")
                and _gray_reconnect
                and (time.time() - last_rtsp_connect_time) >= _gray_warmup_sec
                and is_likely_rtsp_flat_corrupt_frame(
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
                    _cleanup_stale_pending_snapshots(device_id)
                    time.sleep(max(0.5, _gray_reconnect_delay))
                    continue
                _cleanup_stale_pending_snapshots(device_id)
                continue
            gray_bad_streak = 0

            # 抓拍算法任务：只在cron时间点处理1帧，其他帧完全跳过
            current_timestamp = time.time()

            # 检查cron表达式，如果不在cron时间点，直接跳过这帧
            if not should_extract_frame_by_cron(device_id, current_timestamp):
                # 不在cron时间点也要消费检测结果，避免结果堆积到下一次cron才处理
                _cleanup_stale_pending_snapshots(device_id)
                continue

            # cron 槽位：预热期内不判花屏；花屏警告每个槽位只打一次
            _in_rtsp_warmup = (
                rtsp_url.startswith("rtsp://")
                and (time.time() - last_rtsp_connect_time) < _gray_warmup_sec
            )
            _cron_skip_gray = (
                os.getenv("SNAP_CRON_SKIP_GRAY_CHECK", "0").strip().lower()
                in ("1", "true", "yes", "on")
            )
            if (
                not _in_rtsp_warmup
                and not _cron_skip_gray
                and rtsp_url.startswith("rtsp://")
                and is_likely_rtsp_flat_corrupt_frame(
                    frame, _gray_std_max, _gray_mean_lo, _gray_mean_hi
                )
            ):
                _, _cron_fire, _ = cron_slot_for_time(
                    task_cron_expression, current_timestamp
                )
                with device_extract_cron_lock:
                    if device_cron_gray_warn_slot.get(device_id) != _cron_fire:
                        device_cron_gray_warn_slot[device_id] = _cron_fire
                        logger.warning(
                            f"⚠️ 设备 {device_id} cron 槽位 "
                            f"{_cron_fire.strftime('%H:%M:%S') if _cron_fire else '?'} "
                            f"帧疑似解码花屏，窗口内将重试其它帧"
                        )
                _cleanup_stale_pending_snapshots(device_id)
                continue

            # 到了cron时间点，处理这1帧
            # 更新该设备的帧计数（仅用于日志）
            frame_counts[device_id] += 1
            frame_count = frame_counts[device_id]

            # 缩放到目标分辨率（与 stream_forward 的 FFmpeg lanczos 思路一致，使用 OpenCV Lanczos）
            original_height, original_width = frame.shape[:2]
            if (original_width, original_height) != TARGET_RESOLUTION:
                frame = cv2.resize(frame, TARGET_RESOLUTION, interpolation=cv2.INTER_LANCZOS4)

            # cron 槽位：直投检测队列（不经抽帧器），检测完成后 Worker 直接发告警/入库
            payload = _build_detection_payload(device_id, frame, frame_count, current_timestamp)
            if _enqueue_detection_frame(device_id, payload):
                _track_pending_snapshot(device_id, frame_count, current_timestamp)
                mark_cron_slot_captured(device_id, current_timestamp)
                logger.info(
                    f"📸 设备 {device_id} cron 抽帧已入检测队列: 帧号={frame_count}, "
                    f"时间={_shanghai_time_str(current_timestamp)}"
                )

            _cleanup_stale_pending_snapshots(device_id)

            # 优化CPU占用：短暂休眠，避免频繁读取帧
            time.sleep(0.1)  # 100ms

        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 缓流器异常: {str(e)}", exc_info=True)
            time.sleep(2)

    # 清理资源
    if cap is not None:
        cap.release()
        device_caps.pop(device_id, None)

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


def yolo_detection_worker(worker_id: int):
    """YOLO检测工作线程：使用YOLO模型进行识别和画框（多摄像头并行）"""
    logger.info(f"🤖 YOLO检测线程 {worker_id} 启动（多摄像头并行）")

    consecutive_errors = 0
    max_consecutive_errors = 10
    idle_count = 0

    while not stop_event.is_set():
        try:
            # 尝试从每个设备的队列中获取检测数据（带超时）
            device_queue_items = list(detection_queues.items())
            detection_data = None
            device_id = None
            detection_queue = None

            for device_id, detection_queue in device_queue_items:
                try:
                    detection_data = detection_queue.get(timeout=0.1)
                    break  # 成功获取到一个帧，跳出循环
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"❌ 设备 {device_id} 队列获取异常: {str(e)}")
                    continue

            if detection_data is not None:
                # 处理检测数据
                frame = detection_data['frame']
                frame_number = detection_data['frame_number']
                timestamp = detection_data['timestamp']
                device_id_from_data = detection_data.get('device_id', device_id)
                frame_id = detection_data.get('frame_id', f"{device_id_from_data}_frame_{frame_number}")

                consecutive_errors = 0  # 重置错误计数
                idle_count = 0  # 重置空闲计数器

                # 减少日志输出
                if frame_number % 10 == 0:
                    logger.info(f"🔍 [Worker {worker_id}] 开始检测: {frame_id}")

                # 使用所有YOLO模型进行检测（合并结果，优化参数以降低CPU占用）
                all_detections = []
                try:
                    for model_id, yolo_model in yolo_models.items():
                        if stop_event.is_set():
                            break
                        try:
                            infer_device = yolo_model_devices.get(
                                model_id, get_infer_device(device_id_from_data)
                            )
                            model_dets = run_model_detection(
                                yolo_model,
                                frame,
                                conf=_get_detect_conf(),
                                iou=0.45,
                                imgsz=YOLO_IMG_SIZE,
                                infer_device=infer_device,
                                should_keep=_should_keep_detection,
                            )
                            all_detections.extend(model_dets)
                        except Exception as e:
                            if stop_event.is_set():
                                break
                            logger.error(f"❌ 模型 {model_id} 检测异常: {str(e)}", exc_info=True)
                            continue
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"❌ YOLO检测异常: {str(e)} (连续错误: {consecutive_errors})", exc_info=True)
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"❌ 连续错误过多，等待10秒后继续...")
                        time.sleep(10)
                        consecutive_errors = 0
                    continue

                # 如果启用追踪，进行目标追踪
                tracked_detections = []
                if task_config and task_config.tracking_enabled:
                    tracker = trackers.get(device_id_from_data)
                    if tracker:
                        tracked_detections = tracker.update(all_detections, frame_number, current_time=timestamp)
                    else:
                        tracked_detections = [
                            dict(det, track_id=0, is_cached=False, first_seen_time=timestamp, duration=0.0) for det in
                            all_detections]
                else:
                    tracked_detections = [
                        dict(det, track_id=0, is_cached=False, first_seen_time=timestamp, duration=0.0) for det in
                        all_detections]

                # 构建检测结果列表（用于后续处理）
                detections = []
                for tracked_det in tracked_detections:
                    detections.append({
                        'track_id': tracked_det.get('track_id', 0),
                        'class_id': tracked_det.get('class_id', 0),
                        'class_name': tracked_det.get('class_name', 'unknown'),
                        'confidence': tracked_det.get('confidence', 0.0),
                        'bbox': tracked_det.get('bbox', []),
                        'timestamp': timestamp,
                        'frame_id': frame_id,
                        'frame_number': frame_number,
                        'is_cached': tracked_det.get('is_cached', False),
                        'first_seen_time': tracked_det.get('first_seen_time', timestamp),
                        'duration': tracked_det.get('duration', 0.0)
                    })

                # 在帧上绘制检测结果（告警/抓拍展示均使用带框图）
                processed_frame = draw_detections(
                    frame,
                    tracked_detections,
                    frame_number,
                    tracking_enabled=task_config.tracking_enabled if task_config else False,
                ) if tracked_detections else frame.copy()

                if tracked_detections:
                    names = [d.get('class_name') for d in tracked_detections]
                    logger.info(
                        f"🎨 [Worker {worker_id}] 帧 {frame_number} 检测到 {len(tracked_detections)} 个目标: {names}"
                    )
                else:
                    logger.info(f"🔍 [Worker {worker_id}] 帧 {frame_number} 未检测到目标")

                # 检测完成：直接发告警或入库（不经 push_queue 回写）
                _finish_snapshot_detection(
                    device_id_from_data,
                    frame_number,
                    timestamp,
                    detections,
                    processed_frame,
                )
                logger.info(
                    f"✅ [Worker {worker_id}] 检测完成: {frame_id}, 目标数={len(detections)}"
                )
            else:
                # 没有找到工作，增加空闲计数并采用指数退避休眠
                idle_count += 1
                sleep_time = min(0.05 * (2 ** idle_count), 1.0)  # 指数退避，最大1秒
                time.sleep(sleep_time)

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ YOLO检测异常: {str(e)} (连续错误: {consecutive_errors})", exc_info=True)
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"❌ 连续错误过多，等待10秒后继续...")
                time.sleep(10)
                consecutive_errors = 0
            else:
                time.sleep(1)

    logger.info(f"🤖 YOLO检测线程 {worker_id} 停止")


def shutdown_yolo_workers(timeout: float = 8.0):
    """停止 YOLO 检测线程并释放模型，避免停机时 CUDA/ORT 仍在推理。"""
    global yolo_executor, yolo_models, yolo_model_devices

    stop_event.set()

    if yolo_executor:
        logger.info("🛑 等待YOLO检测线程结束...")
        try:
            yolo_executor.shutdown(wait=True, cancel_futures=True)
        except TypeError:
            yolo_executor.shutdown(wait=True)
        yolo_executor = None
        logger.info("✅ YOLO检测线程已结束")

    yolo_models.clear()
    yolo_model_devices.clear()

    stop_face_capture_workers()
    stop_plate_capture_workers()


def cleanup_all_resources():
    """清理所有资源（VideoCapture等）"""
    logger.info("🧹 开始清理所有资源...")

    shutdown_yolo_workers()

    # 清理所有VideoCapture对象
    for device_id, cap in list(device_caps.items()):
        if cap is not None:
            try:
                logger.info(f"🛑 释放设备 {device_id} 的VideoCapture")
                cap.release()
            except Exception as e:
                logger.error(f"❌ 释放设备 {device_id} 的VideoCapture失败: {str(e)}")
        device_caps.pop(device_id, None)

    logger.info("✅ 所有资源已清理")

def signal_handler(sig, frame):
    """信号处理器"""
    logger.info("\n🛑 收到停止信号，正在关闭所有服务...")

    shutdown_yolo_workers()

    # 清理所有资源（FFmpeg进程、VideoCapture等）
    cleanup_all_resources()

    # 等待所有线程结束（增加等待时间）
    logger.info("⏳ 等待所有线程结束...")
    time.sleep(3)

    logger.info("✅ 所有服务已停止")
    sys.exit(0)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 抓拍算法任务服务启动")
    logger.info("=" * 60)
    logger.info("📊 优化配置参数:")
    logger.info(f"   视频分辨率: {TARGET_WIDTH}x{TARGET_HEIGHT} (原1280x720)")
    logger.info(f"   视频帧率: {SOURCE_FPS}fps (原25fps)")
    logger.info(f"   YOLO检测分辨率: {YOLO_IMG_SIZE} (原640)")
    logger.info(f"   检测队列大小: {DETECTION_QUEUE_SIZE}")
    logger.info(f"   检测保留最新帧: {DETECTION_KEEP_LATEST} (阈值: {DETECTION_KEEP_LATEST_THRESHOLD})")
    logger.info(f"   YOLO检测线程数: {YOLO_WORKER_THREADS}")
    logger.info(f"   待检超时: {SNAPSHOT_RESULT_MAX_WAIT_SEC}s")
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

    # 为每个摄像头启动独立的缓流器线程
    buffer_threads = []
    if hasattr(task_config, 'device_streams'):
        for device_id in task_config.device_streams.keys():
            logger.info(f"💾 启动设备 {device_id} 的缓流器线程...")
            buffer_thread = threading.Thread(target=buffer_streamer_worker, args=(device_id,), daemon=True)
            buffer_thread.start()
            buffer_threads.append(buffer_thread)

    # 启动 YOLO 检测线程池（cron 帧直投检测队列，Worker 完成后直接发告警/入库）
    logger.info(f"🤖 启动 {YOLO_WORKER_THREADS} 个YOLO检测线程（多摄像头并行）...")
    global yolo_executor
    yolo_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=YOLO_WORKER_THREADS,
        thread_name_prefix='yolo_worker',
    )
    for worker_id in range(1, YOLO_WORKER_THREADS + 1):
        yolo_executor.submit(yolo_detection_worker, worker_id)
        logger.info(f"   ✅ YOLO检测线程 {worker_id} 已启动")

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
