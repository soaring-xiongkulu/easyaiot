#!/usr/bin/env python3
"""
推流转发服务程序
用于批量推送多个摄像头实时画面，无需AI推理

架构（由 STREAM_FORWARD_FFMPEG_NATIVE / STREAM_FORWARD_FFMPEG_MUX 控制）：
- 原生模式（默认）：独立推流转发，故障隔离 + 自动重启
- 原生多路复用（STREAM_FORWARD_FFMPEG_MUX=true）：单进程多路，仅适合单路或调试
- 经典模式（STREAM_FORWARD_FFMPEG_NATIVE=false）：OpenCV 拉流 + stdin 推流

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
import cv2
import numpy as np
import requests
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import zlib
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, video_root)

from app.utils.video_env import load_video_env
from app.utils.ffmpeg_compat import ffmpeg_rtsp_timeout_args

# 子进程由 launcher 注入 POD_IP / SRS_* / DEVICE_IDS 等；.env 中空 POD_IP= 会覆盖注入值，
# 导致误用 device.rtmp_stream（节点外网播放地址）推流而非本机 127.0.0.1:SRS。
_LAUNCHER_ENV_KEYS = (
    'POD_IP', 'HOST_IP', 'TASK_ID', 'DEVICE_IDS', 'WORKLOAD_ID',
    'SRS_RTMP_PORT', 'SRS_HTTP_PORT', 'SRS_API_PORT',
    'VIDEO_HEARTBEAT_URL', 'VIDEO_CONTROL_URL', 'LOG_PATH', 'DATABASE_URL',
)
_preserved_launcher_env = {k: os.environ[k] for k in _LAUNCHER_ENV_KEYS if os.environ.get(k)}
load_video_env(override=False)
for _key, _val in _preserved_launcher_env.items():
    os.environ[_key] = _val

# 导入VIDEO模块的模型
from models import db, StreamForwardTask, Device
from app.utils.decode.stream_adapter import is_async_stream, open_device_stream, stream_mode_label

# Flask应用实例（延迟创建）
_flask_app = None

def get_flask_app():
    """获取Flask应用实例"""
    global _flask_app
    if _flask_app is None:
        from flask import Flask
        app = Flask(__name__)
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
        db.init_app(app)
        _flask_app = app
    return _flask_app

# 环境变量已在文件顶部通过 load_video_env 加载

# OpenCV 经 FFmpeg 拉 RTSP 时的默认选项（与抓拍/实时算法服务对齐）
# 默认 udp（低延迟）；跨主机/易丢包可设 AI_RTSP_TRANSPORT=tcp 或 OPENCV_FFMPEG_RTSP_TRANSPORT=tcp
if not os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS"):
    _rtsp_tr = (
        os.getenv("AI_RTSP_TRANSPORT")
        or os.getenv("OPENCV_FFMPEG_RTSP_TRANSPORT")
        or os.getenv("FFMPEG_RTSP_TRANSPORT")
        or "udp"
    ).strip().lower()
    if _rtsp_tr not in ("tcp", "udp"):
        _rtsp_tr = "udp"
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
        f"rtsp_transport;{_rtsp_tr}"
        "|timeout;10000000"
        "|rw_timeout;5000000"
        "|max_delay;500000"
        "|fflags;nobuffer+discardcorrupt+genpts"
        "|flags;low_delay"
        "|err_detect;ignore_err"
    )

# GPU调度（按设备稳定映射到多张GPU，避免全部压到0号卡）
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
    seen = set()
    result: List[int] = []
    for x in ids:
        if x in seen:
            continue
        seen.add(x)
        result.append(x)
    return result


def _stable_key_hash(s: str) -> int:
    return int(zlib.crc32(s.encode("utf-8")) & 0xFFFFFFFF)


_GPU_IDS: List[int] = []
_GPU_ASSIGNMENTS: Dict[str, int] = {}
_GPU_RR_COUNTER = 0
_GPU_SCHED_LOCK = threading.Lock()


def _get_gpu_policy() -> str:
    v = (os.getenv("FFMPEG_GPU_POLICY") or os.getenv("GPU_POLICY") or "hash").strip().lower()
    return v if v in ("hash", "round_robin") else "hash"


def _ensure_gpu_ids_initialized() -> None:
    global _GPU_IDS
    if _GPU_IDS:
        return
    configured = _parse_gpu_id_list(os.getenv("GPU_IDS", "").strip())
    _GPU_IDS = configured if configured else [0]


def get_ffmpeg_gpu_id(device_key: Any = None) -> int:
    """
    给FFmpeg用：返回整数GPU索引（传给 -gpu）。
    默认至少返回0（即使未配置多GPU）。
    """
    _ensure_gpu_ids_initialized()
    if not _GPU_IDS:
        return 0
    key_str = str(device_key if device_key is not None else "default")
    with _GPU_SCHED_LOCK:
        cached = _GPU_ASSIGNMENTS.get(key_str)
        if cached is not None:
            return cached

        global _GPU_RR_COUNTER
        policy = _get_gpu_policy()
        if policy == "round_robin":
            idx = _GPU_RR_COUNTER % len(_GPU_IDS)
            _GPU_RR_COUNTER += 1
            gpu_id = _GPU_IDS[idx]
        else:
            gpu_id = _GPU_IDS[_stable_key_hash(key_str) % len(_GPU_IDS)]

        _GPU_ASSIGNMENTS[key_str] = gpu_id
        return gpu_id

# ============================================
# 自定义日志处理器
# ============================================
class DailyRotatingFileHandler(logging.FileHandler):
    """按日期自动切换的日志文件处理器"""
    
    def __init__(self, log_dir, filename_pattern='%Y-%m-%d.log', encoding='utf-8'):
        self.log_dir = log_dir
        self.filename_pattern = filename_pattern
        self.current_date = datetime.now().date()
        self.current_file_path = None
        self._update_file_path()
        super().__init__(self.current_file_path, encoding=encoding)
    
    def _update_file_path(self):
        """更新当前日志文件路径"""
        today = datetime.now().date()
        if today != self.current_date or self.current_file_path is None:
            self.current_date = today
            filename = datetime.now().strftime(self.filename_pattern)
            self.current_file_path = os.path.join(self.log_dir, filename)
    
    def emit(self, record):
        """发送日志记录，如果日期变化则切换文件"""
        if datetime.now().date() != self.current_date:
            self.close()
            self._update_file_path()
            self.baseFilename = self.current_file_path
            if self.stream:
                self.stream.close()
                self.stream = None
            self.stream = self._open()
        
        super().emit(record)

# 配置日志
# 先获取日志目录（video_root在文件开头已定义）
log_path = os.getenv('LOG_PATH')
if log_path:
    service_log_dir = log_path
else:
    # video_root在文件开头已定义
    service_log_dir = os.path.join(video_root, 'logs', f'stream_forward_task_{os.getenv("TASK_ID", "0")}')
os.makedirs(service_log_dir, exist_ok=True)

# 保存日志目录到全局变量，供心跳上报使用
SERVICE_LOG_DIR = service_log_dir

# 创建日志格式
log_format = '[STREAM_FORWARD] [%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

# 创建根logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()

# 创建文件handler
file_handler = DailyRotatingFileHandler(service_log_dir, filename_pattern='%Y-%m-%d.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# 同时输出到stderr
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

# 全局变量
TASK_ID = int(os.getenv('TASK_ID', '0'))
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
VIDEO_SERVICE_PORT = os.getenv('VIDEO_SERVICE_PORT', '6000')
# 控制面心跳连续失败 N 次后 worker 自行退出，避免主程序停止后孤儿进程持续推流
HEARTBEAT_EXIT_ENABLED = os.getenv('STREAM_FORWARD_HEARTBEAT_EXIT', 'true').strip().lower() in (
    '1', 'true', 'yes', 'on',
)
try:
    HEARTBEAT_EXIT_FAILURES = max(1, int(os.getenv('STREAM_FORWARD_HEARTBEAT_EXIT_FAILURES', '6')))
except (TypeError, ValueError):
    HEARTBEAT_EXIT_FAILURES = 6
# GATEWAY_URL 已不再用于心跳上报，心跳上报直接使用 localhost:VIDEO_SERVICE_PORT
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:48080')

# 数据库会话
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db_session = scoped_session(SessionLocal)

# 配置参数（观看链路）：优先 VIEW_*，回退到历史通用变量
# 观感推流帧率（与 AI 检测 EXTRACT_INTERVAL 完全解耦）
VIEW_OUTPUT_FPS = int(os.getenv('VIEW_OUTPUT_FPS', os.getenv('VIEW_SOURCE_FPS', os.getenv('SOURCE_FPS', '25'))))
SOURCE_FPS = VIEW_OUTPUT_FPS
TARGET_WIDTH = int(os.getenv('VIEW_TARGET_WIDTH', os.getenv('TARGET_WIDTH', '1280')))
TARGET_HEIGHT = int(os.getenv('VIEW_TARGET_HEIGHT', os.getenv('TARGET_HEIGHT', '720')))
TARGET_RESOLUTION = (TARGET_WIDTH, TARGET_HEIGHT)
# 观看链路不抽帧（全帧率推流）；勿读取 EXTRACT_INTERVAL（算法检测专用）
EXTRACT_INTERVAL = int(os.getenv('VIEW_EXTRACT_INTERVAL', '1'))
TARGET_FPS = max(1, VIEW_OUTPUT_FPS // EXTRACT_INTERVAL)

# FFmpeg编码参数（推流转发默认 ultrafast + 每路限线程，减轻多路 CPU 争抢）
FFMPEG_PRESET_ENV = os.getenv('VIEW_FFMPEG_PRESET', os.getenv('FFMPEG_PRESET', 'ultrafast'))
FFMPEG_PRESET = FFMPEG_PRESET_ENV.strip() if FFMPEG_PRESET_ENV and FFMPEG_PRESET_ENV.strip() else 'ultrafast'
FFMPEG_VIDEO_BITRATE_ENV = os.getenv('VIEW_FFMPEG_VIDEO_BITRATE', os.getenv('FFMPEG_VIDEO_BITRATE', '3500k'))
FFMPEG_VIDEO_BITRATE = FFMPEG_VIDEO_BITRATE_ENV.strip() if FFMPEG_VIDEO_BITRATE_ENV and FFMPEG_VIDEO_BITRATE_ENV.strip() else '3500k'
FFMPEG_THREADS_ENV = os.getenv('FFMPEG_THREADS', os.getenv('STREAM_FORWARD_X264_THREADS', '2'))
FFMPEG_THREADS = None if not FFMPEG_THREADS_ENV or FFMPEG_THREADS_ENV.strip() == '' else FFMPEG_THREADS_ENV.strip()
FFMPEG_GOP_SIZE_ENV = os.getenv('VIEW_FFMPEG_GOP_SIZE', os.getenv('FFMPEG_GOP_SIZE', None))
# 优化：减小GOP大小，提高关键帧频率，减少首帧加载时间
# 默认GOP设为实际推流帧率（约1秒一个关键帧），而不是源流帧率的2倍
# 这样可以更快地开始播放，减少转圈时间
FFMPEG_GOP_SIZE = int(FFMPEG_GOP_SIZE_ENV) if FFMPEG_GOP_SIZE_ENV else max(1, VIEW_OUTPUT_FPS * 2)
# 画质分档（low/medium/high）
VIDEO_QUALITY_PROFILE = os.getenv('VIEW_VIDEO_QUALITY_PROFILE', os.getenv('VIDEO_QUALITY_PROFILE', '')).strip().lower()
QUALITY_PROFILE_PRESETS = {
    'low': {
        'target_width': 640,
        'target_height': 360,
        'ffmpeg_video_bitrate': '1500k',
    },
    'medium': {
        'target_width': 1280,
        'target_height': 720,
        'ffmpeg_video_bitrate': '2500k',
    },
    'high': {
        'target_width': 1280,
        'target_height': 720,
        'ffmpeg_video_bitrate': '3500k',
    },
}
if VIDEO_QUALITY_PROFILE in QUALITY_PROFILE_PRESETS:
    selected_profile = QUALITY_PROFILE_PRESETS[VIDEO_QUALITY_PROFILE]
    TARGET_WIDTH = selected_profile['target_width']
    TARGET_HEIGHT = selected_profile['target_height']
    TARGET_RESOLUTION = (TARGET_WIDTH, TARGET_HEIGHT)
    FFMPEG_VIDEO_BITRATE = selected_profile['ffmpeg_video_bitrate']
    TARGET_FPS = max(1, VIEW_OUTPUT_FPS // EXTRACT_INTERVAL)
    if not FFMPEG_GOP_SIZE_ENV:
        FFMPEG_GOP_SIZE = max(1, VIEW_OUTPUT_FPS * 2)

# 自适应画质：推流转发默认关闭，避免降档触发重编码导致画面卡顿
AUTO_QUALITY_ENABLED = os.getenv('VIEW_AUTO_QUALITY_ENABLED', os.getenv('AUTO_QUALITY_ENABLED', 'false')).strip().lower() in ('1', 'true', 'yes', 'on')
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


def _get_effective_stream_params():
    """返回观感推流参数；output_fps 固定走 VIEW_OUTPUT_FPS，与 EXTRACT_INTERVAL 无关。"""
    profile_name = AUTO_QUALITY_LOCK_PROFILE if AUTO_QUALITY_LOCK_PROFILE in QUALITY_PROFILE_PRESETS else _get_effective_quality_profile_name()
    preset = QUALITY_PROFILE_PRESETS.get(profile_name, QUALITY_PROFILE_PRESETS['high'])
    output_fps = max(1, int(VIEW_OUTPUT_FPS))
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

# 硬件加速配置
FFMPEG_HWACCEL_ENV = os.getenv('FFMPEG_HWACCEL', 'auto').strip().lower()
FFMPEG_HWACCEL = FFMPEG_HWACCEL_ENV if FFMPEG_HWACCEL_ENV in ['auto', 'nvenc', 'cuvid', 'none'] else 'auto'

# 全局变量
stop_event = threading.Event()
_heartbeat_fail_streak = 0
_heartbeat_fail_lock = threading.Lock()
task_config = None
# 最新帧缓存（拉流线程写、推流线程读，只保留最新一帧）
device_latest_frames = {}  # {device_id: {'frame': np.ndarray, 'w': int, 'h': int} | None}
device_latest_frame_locks = {}  # {device_id: threading.Lock}
# 摄像头流连接（FFmpeg 解码 / OpenCV / 异步缓冲）
device_caps = {}  # {device_id: FfmpegVideoStream | AsyncVideoStream | cv2.VideoCapture}
# 摄像头推送进程（FFmpeg进程）
device_pushers = {}  # {device_id: subprocess.Popen}
native_mux_process: Optional[subprocess.Popen] = None
native_mux_stderr_thread: Optional[threading.Thread] = None
device_push_threads = {}  # {device_id: threading.Thread}
device_push_running = {}  # {device_id: threading.Event}  set() 表示停止
device_codec_fallback = {}  # {device_id: bool} True 表示已回退到软件编码
device_copy_fallback = {}  # {device_id: bool} True 表示 copy 直通失败，已回退转码
device_source_codec = {}  # {device_id: str} RTSP 源视频编码（h264/hevc/...）
device_relay_use_copy = {}  # {device_id: bool} 当前进程是否为 copy 模式
device_push_success_counts = {}  # {device_id: int}
# FFmpeg进程的stderr读取线程和错误信息
device_pusher_stderr_threads = {}  # {device_id: threading.Thread}
device_pusher_stderr_buffers = {}  # {device_id: list}
device_pusher_stderr_locks = {}  # {device_id: threading.Lock}
# 设备流信息
device_streams = {}  # {device_id: {'rtsp_url': str, 'rtmp_url': str, 'device_name': str}}
# 帧计数
frame_counts = {}  # {device_id: int}
# 心跳线程
heartbeat_thread = None


def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def _resolve_ffmpeg_binary() -> str:
    path = os.getenv('FFMPEG_PATH', '').strip()
    if path and os.path.isfile(path) and os.access(path, os.X_OK):
        return path
    return 'ffmpeg'


def _resolve_ffprobe_binary() -> str:
    probe = os.getenv('FFPROBE_PATH', '').strip()
    if probe and os.path.isfile(probe) and os.access(probe, os.X_OK):
        return probe
    ffmpeg = _resolve_ffmpeg_binary()
    if ffmpeg.endswith('ffmpeg'):
        candidate = ffmpeg[:-6] + 'ffprobe'
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return 'ffprobe'


_FFMPEG_CAPS: Optional[Dict[str, bool]] = None


def _ffmpeg_supports_input_option(option_flag: str, option_value: str) -> bool:
    """探测 FFmpeg 在 -i 之前是否接受该输入选项。"""
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
    """探测当前 FFmpeg 支持的选项，避免 RTSP 输入报 Option not found。"""
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
            # 检查FFmpeg是否支持h264_nvenc编码器
            result = subprocess.run(
                [_resolve_ffmpeg_binary(), '-hide_banner', '-encoders'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            output = result.stdout.decode('utf-8', errors='ignore') + result.stderr.decode('utf-8', errors='ignore')
            
            if 'h264_nvenc' in output:
                skip_test = os.getenv('STREAM_FORWARD_NVENC_SKIP_TEST', 'true').strip().lower() in (
                    '1', 'true', 'yes', 'on',
                )
                if skip_test:
                    use_nvenc = True
                    codec_name = 'h264_nvenc'
                    logger.info(
                        '✅ 检测到 h264_nvenc（跳过 lavfi 自检；推流失败时自动回退 libx264）'
                    )
                else:
                    try:
                        test_cmd = [
                            _resolve_ffmpeg_binary(), '-y', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=640x360:rate=1',
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
                            logger.debug(
                                '测试输出: %s',
                                test_result.stderr.decode('utf-8', errors='ignore')[:200],
                            )
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
    """对齐分辨率到指定倍数（h264_nvenc要求分辨率是16的倍数）
    
    Args:
        width: 原始宽度
        height: 原始高度
        align: 对齐倍数，默认16
    
    Returns:
        tuple: (对齐后的宽度, 对齐后的高度)
    """
    aligned_width = (width // align) * align
    aligned_height = (height // align) * align
    # 确保至少是align的倍数
    if aligned_width < align:
        aligned_width = align
    if aligned_height < align:
        aligned_height = align
    return aligned_width, aligned_height


# 在启动时检测硬件加速
_hwaccel_nvenc, _hwaccel_cuvid, _hwaccel_codec = check_hardware_acceleration()
_nvenc_relay_verified: Optional[bool] = None


def load_task_config():
    """加载任务配置"""
    global task_config
    
    try:
        with get_flask_app().app_context():
            task = db.session.get(StreamForwardTask, TASK_ID)
            if not task:
                logger.error(f"推流转发任务不存在: TASK_ID={TASK_ID}")
                return False
            
            # 获取关联的设备
            devices = task.devices if task.devices else []
            if not devices:
                logger.error(f"推流转发任务没有关联的设备: TASK_ID={TASK_ID}")
                return False
            
            # 构建设备流信息（支持 DEVICE_IDS 环境变量按分片/设备过滤）
            device_filter_raw = os.getenv('DEVICE_IDS', '').strip()
            allowed_device_ids = None
            if device_filter_raw:
                allowed_device_ids = {
                    item.strip() for item in device_filter_raw.split(',') if item and item.strip()
                }
                logger.info(f"📌 设备过滤已启用: {sorted(allowed_device_ids)}")

            device_streams_info = {}
            for device in devices:
                if allowed_device_ids is not None and device.id not in allowed_device_ids:
                    continue
                # 获取RTSP输入流地址
                rtsp_url = device.source
                if not rtsp_url:
                    logger.warning(f"设备 {device.id} 没有配置源地址，跳过")
                    continue
                
                # 获取 RTMP 推流地址（远程分片推本机 SRS；播放地址由 launcher 同步到外网 IP）
                rtmp_url = _resolve_rtmp_push_url(device.id, device.rtmp_stream)
                if not rtmp_url:
                    logger.warning(f"设备 {device.id} 没有配置RTMP输出地址，跳过")
                    continue
                
                device_streams_info[device.id] = {
                    'rtsp_url': rtsp_url,
                    'rtmp_url': rtmp_url,
                    'device_name': device.name or device.id
                }
            
            if not device_streams_info:
                logger.error(
                    f"推流转发任务没有可用的设备流: TASK_ID={TASK_ID}"
                    + (f", DEVICE_IDS={device_filter_raw}" if allowed_device_ids else "")
                )
                return False
            
            task_config = type('TaskConfig', (), {
                'task_id': task.id,
                'task_name': task.task_name,
                'output_format': task.output_format,
                'output_quality': task.output_quality,
                'output_bitrate': task.output_bitrate,
                'device_streams': device_streams_info
            })()
            
            logger.info(f"✅ 任务配置加载成功: task_id={TASK_ID}, task_name={task.task_name}, 设备数={len(device_streams_info)}")
            pod_ip = os.getenv('POD_IP', '').strip()
            logger.info(
                '推流目标解析: POD_IP=%s, SRS_RTMP=%s, SRS_API=%s',
                pod_ip or '(未设置，将使用 device.rtmp_stream 外网地址)',
                _srs_rtmp_port(),
                _srs_api_port(),
            )
            for dev_id, info in device_streams_info.items():
                logger.info('  设备 %s 推流 -> %s', dev_id, info.get('rtmp_url'))
            return True
            
    except Exception as e:
        logger.error(f"❌ 加载任务配置失败: {str(e)}", exc_info=True)
        return False


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


def _resolve_rtmp_push_url(device_id: str, device_rtmp_stream: Optional[str] = None) -> Optional[str]:
    """解析 FFmpeg 推流地址。

    远程分片在节点本机推 SRS，固定走 127.0.0.1（避免外网 IP 回环/端口误判）；
    播放地址仍由 stream_url_sync_service 写入 device.rtmp_stream（外网 IP）。
    """
    pod_ip = os.getenv('POD_IP', '').strip()
    if pod_ip:
        rtmp_port = _srs_rtmp_port()
        return f'rtmp://127.0.0.1:{rtmp_port}/live/{device_id}'

    rtmp_url = (device_rtmp_stream or '').strip()
    return rtmp_url or None


def check_rtmp_server_connection(rtmp_url: str) -> bool:
    """检查 RTMP/SRS 是否可用（优先 SRS API，避免仅 TCP 端口占用误判）。"""
    try:
        if not rtmp_url.startswith('rtmp://'):
            return False

        api_port = _srs_api_port()
        if _check_srs_api_ready('127.0.0.1', api_port):
            return True

        url_parts = rtmp_url.replace('rtmp://', '').split('/')
        host_port = url_parts[0]

        if ':' in host_port:
            host, port_str = host_port.split(':')
            try:
                port = int(port_str)
            except ValueError:
                port = 1935
        else:
            host = host_port
            port = 1935

        if host in ('127.0.0.1', 'localhost') and _check_srs_api_ready('127.0.0.1', api_port):
            return True

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.debug(f"检查RTMP服务器连接时出错: {str(e)}")
        return False


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


def _srs_stream_path_key(stream: dict) -> str:
    """从 SRS streams API 条目解析 app/stream 路径，如 live/device_id。"""
    url = (stream.get('url') or '').strip().lstrip('/')
    if url:
        return url
    stream_app = (stream.get('app') or '').strip()
    stream_name = (stream.get('name') or '').strip()
    if stream_name.endswith('.flv'):
        stream_name = stream_name[:-4]
    if stream_app and stream_name:
        return f'{stream_app}/{stream_name}'
    return stream_app


def check_and_stop_existing_stream(stream_url: str) -> None:
    """推流前清理 SRS 上同路径的旧 publisher，避免 StreamBusy / Broken pipe。"""
    try:
        if not stream_url or not stream_url.startswith('rtmp://'):
            return

        url_part = stream_url.replace('rtmp://', '')
        if '/' not in url_part:
            return
        host_port, stream_path = url_part.split('/', 1)[0], '/'.join(url_part.split('/')[1:])
        if not stream_path:
            return

        rtmp_host = host_port.split(':')[0] if ':' in host_port else host_port
        if rtmp_host in ('srs-server', 'srs', 'SRS'):
            rtmp_host = '127.0.0.1'
        if rtmp_host in ('localhost', '127.0.0.1'):
            rtmp_host = '127.0.0.1'

        api_port = _srs_api_port()
        srs_streams_base = f'http://{rtmp_host}:{api_port}/api/v1/streams/'
        srs_streams_list_url = f'{srs_streams_base}?count=100'
        srs_clients_api_url = f'http://{rtmp_host}:{api_port}/api/v1/clients/'
        logger.info('检查现有流: %s', stream_path)

        response = requests.get(srs_streams_list_url, timeout=3)
        if response.status_code != 200:
            logger.warning('无法获取 SRS 流列表 (状态码: %s)，继续推流', response.status_code)
            return

        streams = response.json()
        if isinstance(streams, dict) and 'streams' in streams:
            stream_list = streams['streams']
        elif isinstance(streams, list):
            stream_list = streams
        else:
            stream_list = []

        stream_to_stop = None
        for stream in stream_list:
            if _srs_stream_path_key(stream) == stream_path:
                stream_to_stop = stream
                break

        if not stream_to_stop:
            logger.debug('未发现现有流: %s', stream_path)
            return

        stream_id = stream_to_stop.get('id', '')
        publish_info = stream_to_stop.get('publish', {})
        publish_active = bool(publish_info.get('active')) if isinstance(publish_info, dict) else False
        publish_cid = publish_info.get('cid', '') if isinstance(publish_info, dict) else None
        logger.warning('发现现有流: %s (ID: %s)，正在清理...', stream_path, stream_id)

        if publish_cid and publish_active:
            client_info_url = f'{srs_clients_api_url}{publish_cid}'
            try:
                stop_response = requests.delete(client_info_url, timeout=3)
                if stop_response.status_code in (200, 204):
                    logger.info('已断开发布者客户端: %s', stream_path)
                    time.sleep(1)
                    return
            except Exception as e:
                logger.warning('断开客户端异常: %s', e)

        if stream_id:
            try:
                stop_response = requests.delete(f'{srs_streams_base}{stream_id}', timeout=3)
                if stop_response.status_code in (200, 204):
                    logger.info('已停止现有流: %s', stream_path)
                    time.sleep(1)
                    return
            except Exception as e:
                logger.warning('停止流异常: %s', e)

        stream_key = stream_path.split('/')[-1]
        try:
            result = subprocess.run(
                ['pgrep', '-f', f'rtmp://.*{stream_key}'],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                for pid in result.stdout.strip().split('\n'):
                    pid = pid.strip()
                    if not pid:
                        continue
                    logger.info('终止占用流的进程 PID: %s', pid)
                    subprocess.run(['kill', '-TERM', pid], timeout=2)
                time.sleep(1)
        except Exception as e:
            logger.warning('查找占用流进程失败: %s', e)
    except Exception as e:
        logger.warning('检查现有流时出错: %s，继续推流', e)


def read_ffmpeg_stderr(device_id: str, stderr_pipe, stderr_buffer: list, stderr_lock: threading.Lock):
    """读取FFmpeg进程的stderr输出"""
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
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try:
            stderr_pipe.close()
        except:
            pass


def _collect_key_stderr_errors(stderr_lines: List[str]) -> List[str]:
    key_errors = []
    for line in stderr_lines:
        line_lower = line.lower()
        if any(skip in line_lower for skip in ['version', 'copyright', 'built with', 'configuration:', 'libav']):
            continue
        if any(keyword in line_lower for keyword in [
            'error', 'failed', 'cannot', 'unable', 'invalid',
            'connection refused', 'connection reset', 'timeout',
        ]):
            key_errors.append(line)
    return key_errors


def _is_hw_encoder_stderr_error(stderr_lines: List[str]) -> bool:
    for line in stderr_lines:
        line_lower = line.lower()
        if 'h264_nvenc' in line_lower and any(
            keyword in line_lower for keyword in ['error', 'failed', 'cannot', 'unable', 'invalid']
        ):
            return True
    return False


def _get_device_stderr_lines(device_id: str) -> List[str]:
    if device_id not in device_pusher_stderr_buffers:
        return []
    with device_pusher_stderr_locks.get(device_id, threading.Lock()):
        lines = device_pusher_stderr_buffers[device_id].copy()
        device_pusher_stderr_buffers[device_id].clear()
    return lines


def _bgr_frame_to_ffmpeg_rgb24_bytes(frame: np.ndarray, expect_h: int, expect_w: int) -> Optional[bytes]:
    """OpenCV BGR 帧转 FFmpeg rawvideo rgb24，尺寸须与 FFmpeg -s 一致。"""
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


def _build_ffmpeg_cmd(
    frame_width: int,
    frame_height: int,
    rtmp_url: str,
    device_id: str,
    use_hardware: bool,
) -> List[str]:
    profile_name, effective_fps, effective_w, effective_h, effective_bitrate, effective_gop = _get_effective_stream_params()
    if use_hardware:
        target_w, target_h = align_resolution(effective_w, effective_h, 16)
    else:
        target_w, target_h = effective_w, effective_h

    ffmpeg_cmd = [
        _resolve_ffmpeg_binary(),
        "-y",
        "-fflags", "nobuffer+flush_packets+genpts",
        "-flags", "low_delay",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{frame_width}x{frame_height}",
        "-r", str(effective_fps),
        "-i", "-",
        "-vf", f"scale={target_w}:{target_h}:flags=bilinear",
    ]

    if use_hardware:
        ffmpeg_gpu_id = get_ffmpeg_gpu_id(device_id)
        ffmpeg_cmd.extend([
            "-c:v", "h264_nvenc",
            "-b:v", effective_bitrate,
            "-preset", "p3",
            "-tune", "ll",
            "-gpu", str(ffmpeg_gpu_id),
            "-rc", "vbr",
            "-profile:v", "main",
            "-level", "4.0",
            "-g", str(effective_gop),
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
            "-g", str(effective_gop),
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

    ffmpeg_cmd.extend([
        "-f", "flv",
        "-flvflags", "no_duration_filesize",
        rtmp_url,
    ])
    return ffmpeg_cmd


def _ffmpeg_native_enabled() -> bool:
    return os.getenv('STREAM_FORWARD_FFMPEG_NATIVE', 'true').strip().lower() in (
        '1', 'true', 'yes', 'on',
    )


def _ffmpeg_native_mux_enabled() -> bool:
    """单进程多路复用（故障会拖垮全部路，默认关闭）。"""
    return os.getenv('STREAM_FORWARD_FFMPEG_MUX', 'false').strip().lower() in (
        '1', 'true', 'yes', 'on',
    )


def _get_rtsp_transport() -> str:
    rtsp_transport = (
        os.getenv('AI_RTSP_TRANSPORT')
        or os.getenv('FFMPEG_RTSP_TRANSPORT')
        or os.getenv('OPENCV_FFMPEG_RTSP_TRANSPORT')
        or 'tcp'
    ).strip().lower()
    return rtsp_transport if rtsp_transport in ('tcp', 'udp') else 'tcp'


def _get_push_fps() -> int:
    """推流输出帧率（VIEW_OUTPUT_FPS / VIEW_EXTRACT_INTERVAL，与 AI EXTRACT_INTERVAL 无关）。"""
    return max(1, TARGET_FPS)


def _is_ffmpeg_option_stderr_error(stderr_lines: List[str]) -> bool:
    """FFmpeg 命令行参数不兼容（不应触发画质自动降档）。"""
    for line in stderr_lines:
        line_lower = line.lower()
        if any(token in line_lower for token in (
            'unrecognized option',
            'option not found',
            'error splitting the argument list',
        )):
            return True
    return False


def _stream_forward_env_int(name: str, default: int) -> int:
    try:
        raw = os.getenv(name, '').strip()
        return int(raw) if raw else default
    except (ValueError, TypeError):
        return default


def _expected_relay_stream_count() -> int:
    """预期并发推流路数：显式配置 > 当前任务设备数 > 默认 8。"""
    configured = _stream_forward_env_int('STREAM_FORWARD_TARGET_STREAMS', 0)
    if configured > 0:
        return configured
    if task_config and getattr(task_config, 'device_streams', None):
        return max(1, len(task_config.device_streams))
    return 8


def _resolve_relay_thread_queue_size() -> int:
    """
    FFmpeg -thread_queue_size：每路输入 demux 包队列深度（非全局路数上限）。
    2 路及以上默认 512（4 路场景实测有效）；仅在大规模部署时自动抬高。
    """
    explicit = os.getenv('STREAM_FORWARD_THREAD_QUEUE_SIZE', '').strip()
    if explicit:
        return max(8, _stream_forward_env_int('STREAM_FORWARD_THREAD_QUEUE_SIZE', 512))
    stream_count = _expected_relay_stream_count()
    if stream_count >= 100:
        return 1024
    if stream_count >= 32:
        return 768
    if stream_count >= 2:
        return 512
    return 256


def _resolve_relay_mux_queue_size() -> int:
    """转码输出 mux 队列；多路并发时与 thread_queue_size 同步抬高。"""
    explicit = os.getenv('STREAM_FORWARD_MAX_MUXING_QUEUE_SIZE', '').strip()
    if explicit:
        return max(128, _stream_forward_env_int('STREAM_FORWARD_MAX_MUXING_QUEUE_SIZE', 1024))
    stream_count = _expected_relay_stream_count()
    if stream_count >= 100:
        return 2048
    if stream_count >= 32:
        return 1536
    return 1024


def _native_relay_input_options(rtsp_transport: str) -> List[str]:
    """拉流输入参数：多路并发时需超时/thread_queue，避免部分 RTSP 挂死导致画面时间停住。"""
    caps = _get_ffmpeg_caps()
    analyzeduration = os.getenv('STREAM_FORWARD_ANALYZEDURATION', '2000000').strip() or '2000000'
    probesize = os.getenv('STREAM_FORWARD_PROBESIZE', '2000000').strip() or '2000000'
    open_timeout_us = _stream_forward_env_int('STREAM_FORWARD_RTSP_OPEN_TIMEOUT_US', 10_000_000)
    rw_timeout_us = _stream_forward_env_int('STREAM_FORWARD_RW_TIMEOUT_US', 5_000_000)
    thread_queue_size = _resolve_relay_thread_queue_size()

    opts: List[str] = [
        '-rtsp_transport', rtsp_transport,
        '-analyzeduration', analyzeduration,
        '-probesize', probesize,
    ]
    if rtsp_transport == 'tcp':
        opts.extend(['-rtsp_flags', 'prefer_tcp'])
    opts.extend(ffmpeg_rtsp_timeout_args(open_timeout_us, rw_timeout_us))
    if caps.get('thread_queue_size') and thread_queue_size > 0:
        opts.extend(['-thread_queue_size', str(thread_queue_size)])
    opts.extend(['-fflags', '+genpts+discardcorrupt', '-flags', 'low_delay'])
    if caps.get('err_detect'):
        opts.extend(['-err_detect', 'ignore_err'])
    if os.getenv('STREAM_FORWARD_USE_WALLCLOCK_TS', 'false').strip().lower() in (
        '1', 'true', 'yes', 'on',
    ):
        opts.append('-use_wallclock_as_timestamps')
        opts.append('1')
    return opts


def _native_relay_mux_output_options() -> List[str]:
    """copy/转码共用：避免多路 RTSP 时间戳异常导致 FLV 播放时间停住。"""
    return ['-avoid_negative_ts', 'make_zero', '-muxdelay', '0', '-muxpreload', '0']


def _stream_forward_copy_enabled() -> bool:
    """H.264 直通(copy) 不转码，多路观看最流畅（HEVC 等会自动回退转码）。"""
    return os.getenv('STREAM_FORWARD_VIDEO_COPY', 'true').strip().lower() in (
        '1', 'true', 'yes', 'on',
    )


def _is_h264_source_codec(codec: Optional[str]) -> bool:
    if not codec:
        return False
    return codec.lower() in ('h264', 'avc', 'avc1')


def _probe_rtsp_video_codec(rtsp_url: str, timeout: float = 10.0) -> Optional[str]:
    """探测 RTSP 主视频轨编码，用于判断是否可 copy。"""
    try:
        rtsp_transport = _get_rtsp_transport()
        analyzeduration = os.getenv('STREAM_FORWARD_ANALYZEDURATION', '3000000').strip() or '3000000'
        probesize = os.getenv('STREAM_FORWARD_PROBESIZE', '3000000').strip() or '3000000'
        cmd = [
            _resolve_ffprobe_binary(),
            '-hide_banner', '-loglevel', 'error',
            '-rtsp_transport', rtsp_transport,
            '-analyzeduration', analyzeduration,
            '-probesize', probesize,
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            rtsp_url,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.debug('ffprobe 探测失败: %s', (result.stderr or result.stdout or '').strip()[:200])
            return None
        codec = (result.stdout or '').strip().lower()
        return codec or None
    except subprocess.TimeoutExpired:
        logger.warning('ffprobe 探测 RTSP 编码超时: %s', rtsp_url)
        return None
    except Exception as exc:
        logger.debug('ffprobe 探测 RTSP 编码异常: %s', exc)
        return None


def _ensure_copy_compatible_source(device_id: str, rtsp_url: str) -> None:
    """非 H.264 源 copy 到 FLV 无法 Web 播放，启动前探测并自动转码。"""
    if device_copy_fallback.get(device_id, False):
        return

    codec = device_source_codec.get(device_id)
    if codec is None:
        codec = _probe_rtsp_video_codec(rtsp_url)
        if codec:
            device_source_codec[device_id] = codec

    if not codec:
        logger.debug('设备 %s RTSP 编码探测失败，先尝试 copy', device_id)
        return

    logger.info('设备 %s RTSP 源编码: %s', device_id, codec)
    if not _is_h264_source_codec(codec):
        logger.info(
            '设备 %s 源为 %s（非 H.264），copy 无法 Web 播放，自动使用 H.264 转码',
            device_id, codec,
        )
        device_copy_fallback[device_id] = True


def _is_copy_mode_stderr_error(stderr_lines: List[str]) -> bool:
    for line in stderr_lines:
        line_lower = line.lower()
        if any(token in line_lower for token in (
            'hevc', 'h265', 'could not find tag', 'codec not currently supported',
            'error while opening encoder', 'cannot copy', 'non-key frame',
        )):
            return True
    return False


def _is_broken_pipe_stderr_error(stderr_lines: List[str]) -> bool:
    for line in stderr_lines:
        line_lower = line.lower()
        if 'broken pipe' in line_lower or 'error code: -32' in line_lower:
            return True
    return False


def _is_rtmp_connect_stderr_error(stderr_lines: List[str]) -> bool:
    for line in stderr_lines:
        line_lower = line.lower()
        if 'cannot open connection' in line_lower and ('1935' in line_lower or 'rtmp' in line_lower):
            return True
        if 'error opening output' in line_lower and 'rtmp://' in line_lower:
            return True
        if 'immediate exit requested' in line_lower:
            return True
    return False


def _is_srs_disconnect_stderr_error(stderr_lines: List[str]) -> bool:
    return _is_broken_pipe_stderr_error(stderr_lines) or _is_rtmp_connect_stderr_error(stderr_lines)


def _should_fallback_copy_to_transcode(stderr_lines: List[str]) -> bool:
    if _is_srs_disconnect_stderr_error(stderr_lines):
        return False
    return _is_copy_mode_stderr_error(stderr_lines)


def _disable_hwaccel_globally(reason: str) -> None:
    global _hwaccel_codec, _nvenc_relay_verified
    if _hwaccel_codec == 'h264_nvenc':
        _hwaccel_codec = 'libx264'
        _nvenc_relay_verified = False
        logger.warning('本节点 NVENC 不可用 (%s)，后续推流统一使用 libx264', reason)


def _verify_nvenc_for_relay() -> bool:
    """首次转码前用与推流一致的 scale+NVENC 参数自检，避免 skip_test 误报导致首包失败。"""
    global _nvenc_relay_verified
    if _nvenc_relay_verified is not None:
        return _nvenc_relay_verified
    if _hwaccel_codec != 'h264_nvenc':
        _nvenc_relay_verified = False
        return False

    _profile_name, _effective_fps, effective_w, effective_h, effective_bitrate, _effective_gop = _get_effective_stream_params()
    target_w, target_h = align_resolution(effective_w, effective_h, 16)
    gpu_id = get_ffmpeg_gpu_id('nvenc-relay-selftest')
    preset = os.getenv('STREAM_FORWARD_NVENC_PRESET', 'p1')
    test_cmd = [
        _resolve_ffmpeg_binary(),
        '-y',
        '-hide_banner',
        '-f', 'lavfi',
        '-i', f'testsrc=duration=1:size={target_w}x{target_h}:rate=1',
        '-vf', f'scale={target_w}:{target_h}:flags=fast_bilinear',
        '-c:v', 'h264_nvenc',
        '-preset', preset,
        '-tune', 'll',
        '-gpu', str(gpu_id),
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
        _nvenc_relay_verified = test_result.returncode == 0
        if not _nvenc_relay_verified:
            err_snip = test_result.stderr.decode('utf-8', errors='ignore').strip()[-400:]
            logger.warning('NVENC 转码自检失败 (%dx%d preset=%s gpu=%s): %s',
                           target_w, target_h, preset, gpu_id, err_snip)
            _disable_hwaccel_globally('NVENC 转码自检未通过')
        else:
            logger.info('NVENC 转码自检通过 (%dx%d, preset=%s, gpu=%s)',
                        target_w, target_h, preset, gpu_id)
    except Exception as exc:
        logger.warning('NVENC 转码自检异常: %s', exc)
        _nvenc_relay_verified = False
        _disable_hwaccel_globally('NVENC 转码自检异常')

    return _nvenc_relay_verified


def _build_native_ffmpeg_copy_cmd(device_id: str, rtsp_url: str, rtmp_url: str) -> List[str]:
    """H.264 直通：RTSP -> RTMP，零转码，CPU 占用最低。"""
    rtsp_transport = _get_rtsp_transport()
    cmd = [_resolve_ffmpeg_binary(), '-nostdin', '-hide_banner', '-loglevel', 'warning']
    cmd.extend(_native_relay_input_options(rtsp_transport))
    cmd.extend(['-i', rtsp_url, '-an', '-c:v', 'copy'])
    cmd.extend(_native_relay_mux_output_options())
    cmd.extend(['-f', 'flv', '-flvflags', 'no_duration_filesize', rtmp_url])
    logger.info('设备推流 [%s]: 模式 copy(直通), 无转码', device_id)
    return cmd


def _native_relay_encode_options(
    device_id: str,
    use_hardware: bool,
    effective_bitrate: str,
    effective_gop: int,
    push_fps: int,
) -> List[str]:
    caps = _get_ffmpeg_caps()
    opts: List[str] = ['-an']
    if caps.get('max_muxing_queue_size'):
        opts.extend(['-max_muxing_queue_size', str(_resolve_relay_mux_queue_size())])
    push_fps = max(1, int(push_fps))
    if caps.get('fps_mode'):
        opts.extend(['-fps_mode', 'cfr', '-r', str(push_fps)])
    else:
        opts.extend(['-vsync', 'cfr', '-r', str(push_fps)])
    if use_hardware:
        ffmpeg_gpu_id = get_ffmpeg_gpu_id(device_id)
        opts.extend([
            '-c:v', 'h264_nvenc',
            '-b:v', effective_bitrate,
            '-preset', os.getenv('STREAM_FORWARD_NVENC_PRESET', 'p1'),
            '-tune', 'll',
            '-gpu', str(ffmpeg_gpu_id),
            '-rc', 'vbr',
            '-profile:v', 'main',
            '-g', str(effective_gop),
            '-bf', '0',
            '-pix_fmt', 'yuv420p',
        ])
    else:
        opts.extend([
            '-c:v', 'libx264',
            '-b:v', effective_bitrate,
            '-preset', FFMPEG_PRESET,
            '-tune', 'zerolatency',
            '-profile:v', 'main',
            '-g', str(effective_gop),
            '-bf', '0',
            '-pix_fmt', 'yuv420p',
        ])
        if FFMPEG_THREADS is not None and str(FFMPEG_THREADS).strip():
            try:
                threads_value = int(FFMPEG_THREADS)
                if threads_value > 0:
                    opts.extend(['-threads', str(threads_value)])
            except (ValueError, TypeError):
                pass
    return opts


def _build_native_ffmpeg_relay_cmd(
    device_id: str,
    rtsp_url: str,
    rtmp_url: str,
    use_hardware: bool,
) -> List[str]:
    """构建单路推流命令。"""
    rtsp_transport = _get_rtsp_transport()
    profile_name, _source_fps, effective_w, effective_h, effective_bitrate, effective_gop = _get_effective_stream_params()
    push_fps = _get_push_fps()
    if use_hardware:
        target_w, target_h = align_resolution(effective_w, effective_h, 16)
    else:
        target_w, target_h = effective_w, effective_h

    cmd = [_resolve_ffmpeg_binary(), '-nostdin', '-hide_banner', '-loglevel', 'warning']
    cmd.extend(_native_relay_input_options(rtsp_transport))
    cmd.extend(['-i', rtsp_url])
    cmd.extend([
        '-vf', f'scale={target_w}:{target_h}:flags=fast_bilinear',
    ])
    cmd.extend(_native_relay_encode_options(device_id, use_hardware, effective_bitrate, effective_gop, push_fps))
    cmd.extend(_native_relay_mux_output_options())
    cmd.extend(['-f', 'flv', '-flvflags', 'no_duration_filesize', rtmp_url])

    logger.info(
        '设备推流 [%s]: 编码 %s, 输出 %dx%d@%sfps, 档位=%s',
        device_id,
        'h264_nvenc' if use_hardware else 'libx264',
        target_w, target_h, push_fps, profile_name,
    )
    return cmd


def _build_native_ffmpeg_mux_cmd(device_streams: Dict[str, dict]) -> List[str]:
    """单 FFmpeg 进程：多路 RTSP 拉流 + 多路 RTMP 推流（任一路故障会导致整进程退出，不推荐）。"""
    rtsp_transport = _get_rtsp_transport()
    profile_name, _source_fps, effective_w, effective_h, effective_bitrate, effective_gop = _get_effective_stream_params()
    push_fps = _get_push_fps()
    use_hardware = _hwaccel_codec == 'h264_nvenc'
    if use_hardware:
        target_w, target_h = align_resolution(effective_w, effective_h, 16)
    else:
        target_w, target_h = effective_w, effective_h

    cmd = [_resolve_ffmpeg_binary(), '-nostdin', '-hide_banner', '-loglevel', 'warning']
    entries = list(device_streams.items())
    for _device_id, info in entries:
        cmd.extend(_native_relay_input_options(rtsp_transport))
        cmd.extend(['-i', info['rtsp_url']])

    for idx, (device_id, info) in enumerate(entries):
        rtmp_url = info['rtmp_url']
        use_hw = use_hardware and not device_codec_fallback.get(device_id, False)
        cmd.extend([
            '-map', f'{idx}:v:0?',
            '-vf', f'scale={target_w}:{target_h}:flags=fast_bilinear',
        ])
        cmd.extend(_native_relay_encode_options(device_id, use_hw, effective_bitrate, effective_gop, push_fps))
        cmd.extend(_native_relay_mux_output_options())
        cmd.extend(['-f', 'flv', '-flvflags', 'no_duration_filesize', rtmp_url])

    logger.info(
        'FFmpeg 单进程多路复用: %d 路, 编码 %s, 输出 %dx%d@%sfps, 档位=%s',
        len(entries),
        'h264_nvenc' if use_hardware else 'libx264',
        target_w, target_h, push_fps, profile_name,
    )
    return cmd


def _stop_native_mux_process() -> None:
    global native_mux_process
    proc = native_mux_process
    native_mux_process = None
    if not proc:
        return
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    except Exception as e:
        logger.warning('停止 FFmpeg 多路复用进程时出错: %s', e)


def _stop_native_relay_process(device_id: str) -> None:
    proc = device_pushers.pop(device_id, None)
    if not proc:
        return
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    except Exception as e:
        logger.warning('停止设备 %s 推流进程时出错: %s', device_id, e)


def _handle_native_relay_exit(device_id: str, exit_code: Optional[int]) -> None:
    stderr_lines = _get_device_stderr_lines(device_id)
    if stop_event.is_set():
        device_relay_use_copy.pop(device_id, None)
        device_pushers.pop(device_id, None)
        return

    rtmp_url = None
    if task_config and device_id in task_config.device_streams:
        rtmp_url = task_config.device_streams[device_id].get('rtmp_url')

    if (
        device_relay_use_copy.get(device_id)
        and not device_copy_fallback.get(device_id, False)
    ):
        if _should_fallback_copy_to_transcode(stderr_lines):
            logger.warning('设备 %s copy 直通不兼容，下次重启将回退转码', device_id)
            device_copy_fallback[device_id] = True
        elif _is_srs_disconnect_stderr_error(stderr_lines):
            logger.warning(
                '设备 %s copy 推流 SRS 连接断开 (code=%s)，清理后仍以 copy 重试',
                device_id, exit_code,
            )
            if rtmp_url:
                check_and_stop_existing_stream(rtmp_url)
        else:
            logger.warning(
                '设备 %s copy 进程退出 (code=%s)，仍以 copy 模式重试',
                device_id, exit_code,
            )
    device_relay_use_copy.pop(device_id, None)
    if _is_hw_encoder_stderr_error(stderr_lines) and not device_codec_fallback.get(device_id, False):
        logger.warning('设备 %s 硬件编码失败，自动回退到软件编码', device_id)
        device_codec_fallback[device_id] = True
        _disable_hwaccel_globally('硬件编码运行失败')
        _mark_quality_failure('硬件编码运行失败')
    logger.warning('设备 %s 推流进程退出 (code=%s)', device_id, exit_code)
    if not _is_ffmpeg_option_stderr_error(stderr_lines):
        _mark_quality_failure(f'推流进程退出({exit_code})')
    key_errors = _collect_key_stderr_errors(stderr_lines)
    if key_errors:
        logger.warning('   关键错误: %s', key_errors[-5:])
    device_pushers.pop(device_id, None)


def _start_native_relay_process(device_id: str) -> Optional[subprocess.Popen]:
    """启动单路推流进程，失败时尝试软件编码回退。"""
    if not task_config or device_id not in task_config.device_streams:
        return None

    info = task_config.device_streams[device_id]
    rtsp_url = info.get('rtsp_url')
    rtmp_url = info.get('rtmp_url')
    if not rtsp_url or not rtmp_url:
        return None

    if not check_rtmp_server_connection(rtmp_url):
        logger.warning('设备 %s RTMP/SRS 不可用: %s', device_id, rtmp_url)
        _mark_quality_failure('RTMP服务器不可用')
        return None

    check_and_stop_existing_stream(rtmp_url)

    if _stream_forward_copy_enabled() and not device_copy_fallback.get(device_id, False):
        _ensure_copy_compatible_source(device_id, rtsp_url)

    use_copy = _stream_forward_copy_enabled() and not device_copy_fallback.get(device_id, False)
    use_hardware = (
        not use_copy
        and _hwaccel_codec == 'h264_nvenc'
        and not device_codec_fallback.get(device_id, False)
    )
    if use_hardware and not _verify_nvenc_for_relay():
        use_hardware = False
    if use_copy:
        ffmpeg_cmd = _build_native_ffmpeg_copy_cmd(device_id, rtsp_url, rtmp_url)
    else:
        source_codec = device_source_codec.get(device_id)
        if device_copy_fallback.get(device_id, False) and source_codec:
            logger.info(
                '设备 %s 使用 H.264 转码 (源编码 %s，非 H.264 或 copy 不可用)',
                device_id, source_codec,
            )
        elif not _stream_forward_copy_enabled():
            logger.info('设备 %s 使用 H.264 转码 (STREAM_FORWARD_VIDEO_COPY=false)', device_id)
        ffmpeg_cmd = _build_native_ffmpeg_relay_cmd(device_id, rtsp_url, rtmp_url, use_hardware)

    if device_id not in device_pusher_stderr_buffers:
        device_pusher_stderr_buffers[device_id] = []
        device_pusher_stderr_locks[device_id] = threading.Lock()

    try:
        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            shell=False,
        )
        stderr_buffer = device_pusher_stderr_buffers[device_id]
        stderr_lock = device_pusher_stderr_locks[device_id]
        stderr_thread = threading.Thread(
            target=read_ffmpeg_stderr,
            args=(device_id, proc.stderr, stderr_buffer, stderr_lock),
            daemon=True,
        )
        stderr_thread.start()
        device_pusher_stderr_threads[device_id] = stderr_thread

        time.sleep(0.5)
        if proc.poll() is not None:
            error_lines = _get_device_stderr_lines(device_id)
            exit_code = proc.returncode
            if use_copy and not device_copy_fallback.get(device_id, False):
                key_errors = _collect_key_stderr_errors(error_lines)
                if stop_event.is_set():
                    return None
                if _should_fallback_copy_to_transcode(error_lines):
                    logger.warning('设备 %s copy 直通启动失败 (code=%s)，回退转码', device_id, exit_code)
                    device_copy_fallback[device_id] = True
                    if key_errors:
                        logger.warning('   copy 失败原因: %s', key_errors[-3:])
                    return _start_native_relay_process(device_id)
                if _is_srs_disconnect_stderr_error(error_lines):
                    logger.warning(
                        '设备 %s copy 启动时 SRS 不可用 (code=%s)，清理后重试 copy',
                        device_id, exit_code,
                    )
                    if key_errors:
                        logger.warning('   连接错误: %s', key_errors[-3:])
                    check_and_stop_existing_stream(rtmp_url)
                    return None
                logger.warning('设备 %s copy 启动失败 (code=%s)，将重试 copy', device_id, exit_code)
                if key_errors:
                    logger.warning('   失败原因: %s', key_errors[-3:])
                return None
            if _is_hw_encoder_stderr_error(error_lines) and use_hardware and not device_codec_fallback.get(device_id, False):
                logger.warning('设备 %s 硬件编码启动失败，回退软件编码', device_id)
                device_codec_fallback[device_id] = True
                _disable_hwaccel_globally('硬件编码启动失败')
                _mark_quality_failure('硬件编码启动失败')
                return _start_native_relay_process(device_id)

            logger.error('设备 %s 推流启动失败 (code=%s)', device_id, exit_code)
            if not _is_ffmpeg_option_stderr_error(error_lines):
                _mark_quality_failure(f'推流启动失败({exit_code})')
            else:
                logger.error('设备 %s FFmpeg 参数与当前版本不兼容，请检查 FFMPEG_PATH', device_id)
            logger.error('   FFmpeg 命令: %s', ' '.join(ffmpeg_cmd))
            key_errors = _collect_key_stderr_errors(error_lines)
            if key_errors:
                logger.error('   关键错误: %s', key_errors[-5:])
            return None

        device_pushers[device_id] = proc
        device_relay_use_copy[device_id] = use_copy
        if use_copy:
            actual_codec = 'copy'
        else:
            actual_codec = 'libx264' if device_codec_fallback.get(device_id, False) else _hwaccel_codec
        logger.info('设备 %s 推流已启动 PID=%s -> %s (%s)', device_id, proc.pid, rtmp_url, actual_codec)
        return proc
    except Exception as e:
        logger.error('设备 %s 启动推流失败: %s', device_id, e, exc_info=True)
        return None


def _run_native_ffmpeg_mux_mode(device_streams: Dict[str, dict]) -> None:
    """FFmpeg 单进程多路复用（不推荐：任一路 Broken pipe 会拖垮全部路）。"""
    global native_mux_process, native_mux_stderr_thread, heartbeat_thread

    unavailable = []
    for device_id, info in device_streams.items():
        rtmp_url = info.get('rtmp_url')
        if rtmp_url and not check_rtmp_server_connection(rtmp_url):
            unavailable.append((device_id, rtmp_url))
            logger.warning('设备 %s RTMP/SRS 不可用: %s', device_id, rtmp_url)

    if unavailable:
        api_port = _srs_api_port()
        reason = (
            f'SRS 未就绪（{len(unavailable)} 路），'
            f'请确认节点媒体栈已部署且 API {api_port} 可访问'
        )
        logger.error(reason)
        update_task_status(status=1, exception_reason=reason[:200])
        return

    ffmpeg_cmd = _build_native_ffmpeg_mux_cmd(device_streams)
    logger.info('启动 FFmpeg 多路复用: %s', ' '.join(ffmpeg_cmd[:20]) + ' ...')

    stderr_buffer: List[str] = []
    stderr_lock = threading.Lock()
    try:
        native_mux_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            shell=False,
        )
        native_mux_stderr_thread = threading.Thread(
            target=read_ffmpeg_stderr,
            args=('native-mux', native_mux_process.stderr, stderr_buffer, stderr_lock),
            daemon=True,
        )
        native_mux_stderr_thread.start()
    except Exception as e:
        logger.error('FFmpeg 多路复用启动失败: %s', e, exc_info=True)
        update_task_status(status=1, exception_reason=f'FFmpeg多路复用启动失败: {str(e)[:200]}')
        return

    logger.info('FFmpeg 多路复用进程已启动 PID=%s', native_mux_process.pid)
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()

    try:
        while not stop_event.is_set():
            if native_mux_process.poll() is not None:
                exit_code = native_mux_process.returncode
                with stderr_lock:
                    tail = stderr_buffer[-10:]
                logger.error('FFmpeg 多路复用进程退出 code=%s, stderr=%s', exit_code, tail)
                update_task_status(status=1, exception_reason=f'FFmpeg多路复用退出({exit_code})')
                break
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info('收到键盘中断，准备退出多路复用模式...')
    finally:
        stop_event.set()
        _stop_native_mux_process()
        try:
            update_task_status(status=0, exception_reason=None)
        except Exception as e:
            logger.warning('更新任务停止状态失败: %s', e)
        logger.info('FFmpeg 多路复用模式已停止')


def _prefetch_source_codecs_parallel(device_streams: Dict[str, dict]) -> None:
    """并行预探测各路 RTSP 编码，避免监督线程顺序 ffprobe 阻塞多路同时启动。"""
    if not _stream_forward_copy_enabled():
        return

    def _probe_one(device_id: str, rtsp_url: str) -> None:
        if device_id in device_source_codec or device_copy_fallback.get(device_id, False):
            return
        codec = _probe_rtsp_video_codec(rtsp_url)
        if not codec:
            return
        device_source_codec[device_id] = codec
        logger.info('设备 %s RTSP 源编码(预探测): %s', device_id, codec)
        if not _is_h264_source_codec(codec):
            device_copy_fallback[device_id] = True
            logger.info(
                '设备 %s 源为 %s（非 H.264），copy 无法 Web 播放，将使用 H.264 转码',
                device_id, codec,
            )

    threads: List[threading.Thread] = []
    for device_id, info in device_streams.items():
        rtsp_url = info.get('rtsp_url')
        if not rtsp_url:
            continue
        thread = threading.Thread(
            target=_probe_one,
            args=(device_id, rtsp_url),
            daemon=True,
            name=f'probe-{device_id}',
        )
        thread.start()
        threads.append(thread)

    probe_timeout = max(12.0, float(os.getenv('STREAM_FORWARD_PROBE_TIMEOUT_SEC', '12')))
    for thread in threads:
        thread.join(timeout=probe_timeout)


def _run_native_ffmpeg_relay_mode(device_streams: Dict[str, dict]) -> None:
    """独立推流模式：监督线程自动重启。"""
    global heartbeat_thread

    unavailable = []
    for device_id, info in device_streams.items():
        rtmp_url = info.get('rtmp_url')
        if rtmp_url and not check_rtmp_server_connection(rtmp_url):
            unavailable.append((device_id, rtmp_url))
            logger.warning('设备 %s RTMP/SRS 不可用: %s', device_id, rtmp_url)

    if unavailable and len(unavailable) >= len(device_streams):
        api_port = _srs_api_port()
        reason = (
            f'SRS 未就绪（{len(unavailable)} 路），'
            f'请确认节点媒体栈已部署且 API {api_port} 可访问'
        )
        logger.error(reason)
        update_task_status(status=1, exception_reason=reason[:200])
        return

    restart_delay_sec = max(0.3, float(os.getenv('STREAM_FORWARD_RELAY_RESTART_DELAY_SEC', '0.5')))
    restart_cooldown_sec = max(restart_delay_sec, float(os.getenv('STREAM_FORWARD_RELAY_RESTART_COOLDOWN_SEC', '3')))
    max_backoff_sec = max(restart_cooldown_sec, float(os.getenv('STREAM_FORWARD_RELAY_MAX_BACKOFF_SEC', '15')))
    relay_fail_counts: Dict[str, int] = {}
    relay_next_retry: Dict[str, float] = {}
    stagger_sec = max(0.0, float(os.getenv('STREAM_FORWARD_RELAY_STAGGER_SEC', '0.3')))

    for device_id in device_streams:
        device_codec_fallback[device_id] = False
        device_copy_fallback[device_id] = False
        device_source_codec.pop(device_id, None)

    _prefetch_source_codecs_parallel(device_streams)

    device_ids_ordered = list(device_streams.keys())
    start_base = time.time()
    for idx, device_id in enumerate(device_ids_ordered):
        device_push_success_counts[device_id] = 0
        relay_fail_counts[device_id] = 0
        relay_next_retry[device_id] = start_base + idx * stagger_sec

    logger.info(
        '独立推流模式: %d 路, 重启间隔 %.1fs~%.1fs, 启动错峰 %.1fs/路, '
        'thread_queue_size=%d/路, max_muxing_queue_size=%d',
        len(device_streams), restart_delay_sec, max_backoff_sec, stagger_sec,
        _resolve_relay_thread_queue_size(), _resolve_relay_mux_queue_size(),
    )

    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()

    try:
        while not stop_event.is_set():
            now = time.time()
            alive_count = 0

            for device_id in device_streams:
                proc = device_pushers.get(device_id)
                if proc and proc.poll() is None:
                    alive_count += 1
                    relay_fail_counts[device_id] = 0
                    device_push_success_counts[device_id] = device_push_success_counts.get(device_id, 0) + 1
                    if device_push_success_counts[device_id] % 60 == 0:
                        _mark_quality_success()
                    continue

                if proc is not None and proc.poll() is not None:
                    _handle_native_relay_exit(device_id, proc.returncode)
                    relay_fail_counts[device_id] = relay_fail_counts.get(device_id, 0) + 1
                    backoff = min(
                        max_backoff_sec,
                        restart_delay_sec * (2 ** min(relay_fail_counts[device_id] - 1, 4)),
                    )
                    relay_next_retry[device_id] = now + backoff
                    logger.info(
                        '设备 %s 将在 %.1fs 后重启推流（连续失败 %d 次）',
                        device_id, backoff, relay_fail_counts[device_id],
                    )
                    continue

                if now < relay_next_retry.get(device_id, 0.0):
                    continue

                if _start_native_relay_process(device_id):
                    alive_count += 1
                    relay_fail_counts[device_id] = 0
                else:
                    relay_fail_counts[device_id] = relay_fail_counts.get(device_id, 0) + 1
                    backoff = min(
                        max_backoff_sec,
                        restart_delay_sec * (2 ** min(relay_fail_counts[device_id] - 1, 4)),
                    )
                    relay_next_retry[device_id] = now + backoff

            if alive_count == 0 and device_streams:
                update_task_status(status=1, exception_reason='所有推流进程均未运行')
            elif alive_count > 0:
                update_task_status(status=0, exception_reason=None)

            time.sleep(1)
    except KeyboardInterrupt:
        logger.info('收到键盘中断，准备退出独立推流模式...')
    finally:
        stop_event.set()
        for device_id in list(device_pushers.keys()):
            _stop_native_relay_process(device_id)
        try:
            update_task_status(status=0, exception_reason=None)
        except Exception as e:
            logger.warning('更新任务停止状态失败: %s', e)
        logger.info('独立推流模式已停止')


def _stop_device_pusher_process(device_id: str) -> None:
    pusher_process = device_pushers.pop(device_id, None)
    if not pusher_process:
        return
    try:
        if pusher_process.stdin:
            try:
                pusher_process.stdin.close()
            except Exception:
                pass
        if pusher_process.poll() is None:
            try:
                pusher_process.terminate()
                pusher_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                if pusher_process.poll() is None:
                    pusher_process.kill()
                    pusher_process.wait()
            except Exception:
                if pusher_process.poll() is None:
                    pusher_process.kill()
    except Exception as e:
        logger.warning(f"停止设备 {device_id} 推送进程时出错: {str(e)}")


def _start_device_ffmpeg_pusher(device_id: str, frame_width: int, frame_height: int) -> Optional[subprocess.Popen]:
    """为指定设备启动 FFmpeg 推流进程，失败时自动尝试软件编码回退。"""
    device_stream_info = task_config.device_streams.get(device_id) if task_config else None
    if not device_stream_info:
        return None

    rtmp_url = device_stream_info.get('rtmp_url')
    if not rtmp_url:
        return None

    if not check_rtmp_server_connection(rtmp_url):
        logger.warning(f"⚠️  设备 {device_id} RTMP服务器不可用: {rtmp_url}")
        _mark_quality_failure("RTMP服务器不可用")
        return None

    use_hardware = (
        _hwaccel_codec == 'h264_nvenc'
        and not device_codec_fallback.get(device_id, False)
    )
    ffmpeg_cmd = _build_ffmpeg_cmd(frame_width, frame_height, rtmp_url, device_id, use_hardware)

    if device_id not in device_pusher_stderr_buffers:
        device_pusher_stderr_buffers[device_id] = []
        device_pusher_stderr_locks[device_id] = threading.Lock()

    try:
        pusher_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            shell=False,
        )
        stderr_buffer = device_pusher_stderr_buffers[device_id]
        stderr_lock = device_pusher_stderr_locks[device_id]
        stderr_thread = threading.Thread(
            target=read_ffmpeg_stderr,
            args=(device_id, pusher_process.stderr, stderr_buffer, stderr_lock),
            daemon=True,
        )
        stderr_thread.start()
        device_pusher_stderr_threads[device_id] = stderr_thread

        time.sleep(0.5)
        if pusher_process.poll() is not None:
            error_lines = _get_device_stderr_lines(device_id)
            exit_code = pusher_process.returncode
            if _is_hw_encoder_stderr_error(error_lines) and use_hardware and not device_codec_fallback.get(device_id, False):
                logger.warning(f"⚠️  设备 {device_id} 硬件编码失败，自动回退到软件编码")
                device_codec_fallback[device_id] = True
                _mark_quality_failure("硬件编码启动失败")
                return _start_device_ffmpeg_pusher(device_id, frame_width, frame_height)

            logger.error(f"❌ 设备 {device_id} 推送进程启动失败 (退出码: {exit_code})")
            _mark_quality_failure(f"推流进程启动失败({exit_code})")
            key_errors = _collect_key_stderr_errors(error_lines)
            if key_errors:
                logger.error(f"   关键错误: {key_errors[-5:]}")
            return None

        device_pushers[device_id] = pusher_process
        profile_name, effective_fps, effective_w, effective_h, effective_bitrate, effective_gop = _get_effective_stream_params()
        if use_hardware:
            target_w, target_h = align_resolution(effective_w, effective_h, 16)
        else:
            target_w, target_h = effective_w, effective_h
        actual_codec = 'libx264' if device_codec_fallback.get(device_id, False) else _hwaccel_codec
        codec_info = (
            f"硬件编码 ({actual_codec})" if actual_codec == 'h264_nvenc'
            else f"软件编码 ({actual_codec})"
        )
        logger.info(f"✅ 设备 {device_id} 推送进程已启动 (PID: {pusher_process.pid})")
        logger.info(f"   📺 推流地址: {rtmp_url}")
        logger.info(f"   📐 raw输入 {frame_width}x{frame_height} -> 编码约 {target_w}x{target_h} @ {effective_fps} fps")
        logger.info(f"   🎬 编码器: {codec_info}, 比特率: {effective_bitrate}")
        logger.info(f"   🎯 画质档位: {profile_name}, GOP: {effective_gop}")
        return pusher_process
    except Exception as e:
        logger.error(f"❌ 设备 {device_id} 启动推送进程失败: {str(e)}", exc_info=True)
        return None


def _handle_pusher_process_exit(device_id: str, exit_code: Optional[int]) -> None:
    stderr_lines = _get_device_stderr_lines(device_id)
    if _is_hw_encoder_stderr_error(stderr_lines) and not device_codec_fallback.get(device_id, False):
        logger.warning(f"⚠️  设备 {device_id} 硬件编码失败，自动回退到软件编码")
        device_codec_fallback[device_id] = True
        _mark_quality_failure("硬件编码运行失败")
    logger.warning(f"⚠️  设备 {device_id} 推送进程异常退出 (退出码: {exit_code})")
    _mark_quality_failure(f"FFmpeg进程退出({exit_code})")
    key_errors = _collect_key_stderr_errors(stderr_lines)
    if key_errors:
        logger.warning(f"   关键错误: {key_errors[-5:]}")
    device_pushers.pop(device_id, None)


def buffer_worker(device_id: str):
    """拉流线程：从 RTSP 读取帧，抽帧后写入 latest-frame 缓存。"""
    logger.info(f"📹 拉流线程启动 [设备: {device_id}]，抽帧间隔: 每 {EXTRACT_INTERVAL} 帧取 1 帧")
    
    if not task_config or not hasattr(task_config, 'device_streams'):
        logger.error(f"任务配置未加载，设备 {device_id} 读取器退出")
        return
    
    device_stream_info = task_config.device_streams.get(device_id)
    if not device_stream_info:
        logger.error(f"设备 {device_id} 流信息不存在，读取器退出")
        return
    
    rtsp_url = device_stream_info.get('rtsp_url')
    device_name = device_stream_info.get('device_name', device_id)
    
    if not rtsp_url:
        logger.error(f"设备 {device_id} 输入流地址不存在，读取器退出")
        return
    
    # 初始化帧计数
    if device_id not in frame_counts:
        frame_counts[device_id] = 0
    
    cap = None
    retry_count = 0
    max_retries = 5
    rtsp_open_timeout_msec = int(os.getenv("RTSP_OPEN_TIMEOUT_MSEC", "5000"))
    rtsp_read_timeout_msec = int(os.getenv("RTSP_READ_TIMEOUT_MSEC", "2500"))
    rtsp_retry_delay_sec = max(0.1, float(os.getenv("RTSP_RETRY_DELAY_SEC", "1")))
    rtsp_retry_cooldown_sec = max(1.0, float(os.getenv("RTSP_RETRY_COOLDOWN_SEC", "8")))
    rtsp_read_fail_delay_sec = max(0.1, float(os.getenv("RTSP_READ_FAIL_DELAY_SEC", "0.3")))
    
    while not stop_event.is_set():
        try:
            # 打开源流
            if cap is None or not cap.isOpened():
                stream_type = "RTSP" if rtsp_url.startswith('rtsp://') else "RTMP" if rtsp_url.startswith('rtmp://') else "流"
                
                logger.info(f"正在连接设备 {device_id} 的 {stream_type} 流: {rtsp_url} (重试次数: {retry_count})")
                
                try:
                    cap = open_device_stream(
                        rtsp_url,
                        device_id,
                        task_id=str(TASK_ID),
                        open_timeout_msec=rtsp_open_timeout_msec,
                        read_timeout_msec=rtsp_read_timeout_msec,
                    )
                except Exception as e:
                    logger.error(f"设备 {device_id} 打开视频流时出错: {str(e)}")
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
                        logger.warning(f"设备 {device_id} 无法打开 {stream_type} 流，等待重试... ({retry_count}/{max_retries})")
                        time.sleep(rtsp_retry_delay_sec)
                    continue
                
                if not cap.isOpened():
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ 设备 {device_id} 连接 {stream_type} 流失败，已达到最大重试次数 {max_retries}")
                        logger.info(f"等待{rtsp_retry_cooldown_sec:.1f}秒后重新尝试...")
                        time.sleep(rtsp_retry_cooldown_sec)
                        retry_count = 0
                    else:
                        logger.warning(f"设备 {device_id} 无法打开 {stream_type} 流，等待重试... ({retry_count}/{max_retries})")
                        time.sleep(rtsp_retry_delay_sec)
                    if cap is not None:
                        try:
                            cap.release()
                        except:
                            pass
                        cap = None
                    continue
                
                retry_count = 0
                logger.info(f"📌 设备 {device_id} {stream_mode_label(cap)}")
                device_caps[device_id] = cap
                logger.info(f"✅ 设备 {device_id} {stream_type} 流连接成功")
            
            # 从源流读取帧（异步模式下后台 decode，此处取缓冲区最新帧）
            ret, frame = cap.read()
            
            if not ret or frame is None:
                if is_async_stream(cap):
                    if cap.read_failed:
                        logger.warning(f"设备 {device_id} 异步拉流结束或解码失败，重新连接...")
                        if cap is not None:
                            try:
                                cap.release()
                            except Exception:
                                pass
                            cap = None
                            device_caps.pop(device_id, None)
                        time.sleep(rtsp_read_fail_delay_sec)
                        retry_count += 1
                        if retry_count >= max_retries:
                            logger.error(
                                f"❌ 设备 {device_id} 读取帧失败次数过多，等待{rtsp_retry_cooldown_sec:.1f}秒后重新尝试..."
                            )
                            time.sleep(rtsp_retry_cooldown_sec)
                            retry_count = 0
                        continue
                    time.sleep(0.002)
                    continue
                logger.warning(f"设备 {device_id} 读取源流帧失败，重新连接...")
                # 清理当前连接
                if cap is not None:
                    try:
                        cap.release()
                    except Exception:
                        pass
                    cap = None
                    device_caps.pop(device_id, None)
                
                # 等待后重试连接
                time.sleep(rtsp_read_fail_delay_sec)
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"❌ 设备 {device_id} 读取帧失败次数过多，等待{rtsp_retry_cooldown_sec:.1f}秒后重新尝试...")
                    time.sleep(rtsp_retry_cooldown_sec)
                    retry_count = 0
                continue
            
            # 更新帧计数并按 EXTRACT_INTERVAL 抽帧
            frame_counts[device_id] += 1
            if EXTRACT_INTERVAL > 1 and frame_counts[device_id] % EXTRACT_INTERVAL != 0:
                continue

            frame_h, frame_w = frame.shape[:2]
            frame_lock = device_latest_frame_locks.get(device_id)
            if frame_lock:
                with frame_lock:
                    device_latest_frames[device_id] = {
                        'frame': frame,
                        'w': frame_w,
                        'h': frame_h,
                    }
            
        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 读取器异常: {str(e)}", exc_info=True)
            time.sleep(2)
    
    # 清理资源
    if cap is not None:
        try:
            cap.release()
        except:
            pass
        device_caps.pop(device_id, None)
    
    frame_lock = device_latest_frame_locks.get(device_id)
    if frame_lock:
        with frame_lock:
            device_latest_frames[device_id] = None

    logger.info(f"📹 设备 {device_id} 拉流线程停止")


def _fixed_rate_push_worker(device_id: str):
    """固定速率推帧线程：每路独立，匀速写入 FFmpeg stdin。"""
    logger.info(f"📤 固定速率推帧线程启动 [设备: {device_id}]")
    push_running = device_push_running.get(device_id)

    _profile_name, _effective_fps, _effective_w, _effective_h, _effective_bitrate, _effective_gop = _get_effective_stream_params()
    frame_interval = 1.0 / max(1, _effective_fps)

    last_push_frame = None
    last_push_w = None
    last_push_h = None
    last_push_time = time.perf_counter()
    push_frame_count = 0
    ffmpeg_stdin_w = None
    ffmpeg_stdin_h = None
    flush_every = max(1, int(os.getenv('VIEW_PUSH_FLUSH_EVERY', os.getenv('PUSH_FLUSH_EVERY', '5'))))

    while push_running and not push_running.is_set() and not stop_event.is_set():
        try:
            target_time = last_push_time + frame_interval
            now = time.perf_counter()
            sleep_duration = target_time - now

            if sleep_duration > 0:
                time.sleep(sleep_duration)
            elif sleep_duration < -frame_interval * 2:
                last_push_time = time.perf_counter()
                target_time = last_push_time + frame_interval
                time.sleep(frame_interval)

            last_push_time = time.perf_counter()

            frame_lock = device_latest_frame_locks.get(device_id)
            frame_info = None
            if frame_lock:
                with frame_lock:
                    frame_info = device_latest_frames.get(device_id)

            frame_to_push = None
            push_w = None
            push_h = None

            if frame_info is not None and frame_info.get('frame') is not None:
                frame_to_push = frame_info['frame']
                push_w = frame_info['w']
                push_h = frame_info['h']
                last_push_frame = frame_to_push
                last_push_w = push_w
                last_push_h = push_h
            elif last_push_frame is not None:
                frame_to_push = last_push_frame
                push_w = last_push_w
                push_h = last_push_h
            else:
                time.sleep(0.005)
                continue

            pusher_process = device_pushers.get(device_id)
            if pusher_process is None or pusher_process.poll() is not None:
                if pusher_process is not None and pusher_process.poll() is not None:
                    _handle_pusher_process_exit(device_id, pusher_process.returncode)
                pusher_process = _start_device_ffmpeg_pusher(device_id, push_w, push_h)
                if not pusher_process:
                    time.sleep(1)
                    continue
                ffmpeg_stdin_w = push_w
                ffmpeg_stdin_h = push_h

            if ffmpeg_stdin_w != push_w or ffmpeg_stdin_h != push_h:
                _stop_device_pusher_process(device_id)
                pusher_process = _start_device_ffmpeg_pusher(device_id, push_w, push_h)
                if not pusher_process:
                    time.sleep(1)
                    continue
                ffmpeg_stdin_w = push_w
                ffmpeg_stdin_h = push_h

            raw_bytes = _bgr_frame_to_ffmpeg_rgb24_bytes(frame_to_push, ffmpeg_stdin_h, ffmpeg_stdin_w)
            if raw_bytes is None:
                continue

            try:
                pusher_process.stdin.write(raw_bytes)
                if push_frame_count % flush_every == 0:
                    pusher_process.stdin.flush()
                push_frame_count += 1
                if push_frame_count % 150 == 0:
                    _mark_quality_success()
                    device_push_success_counts[device_id] = device_push_success_counts.get(device_id, 0) + 1
            except (BrokenPipeError, OSError, IOError) as e:
                logger.error(f"❌ 设备 {device_id} 固定速率推帧写入失败: {str(e)}")
                _mark_quality_failure("写入推流进程失败")
                if pusher_process.poll() is not None:
                    _handle_pusher_process_exit(device_id, pusher_process.returncode)
                ffmpeg_stdin_w = None
                ffmpeg_stdin_h = None
            except Exception as e:
                logger.error(f"❌ 设备 {device_id} 固定速率推帧异常: {str(e)}")
                if pusher_process.poll() is not None:
                    _handle_pusher_process_exit(device_id, pusher_process.returncode)
                ffmpeg_stdin_w = None
                ffmpeg_stdin_h = None

        except Exception as e:
            logger.error(f"❌ 设备 {device_id} 固定速率推帧线程异常: {str(e)}", exc_info=True)
            time.sleep(0.01)

    _stop_device_pusher_process(device_id)
    logger.info(f"📤 固定速率推帧线程停止 [设备: {device_id}]")


def update_task_status(status: str = None, exception_reason: str = None):
    """更新任务状态到数据库
    
    Args:
        status: 状态值 [0:正常, 1:异常]
        exception_reason: 异常原因
    """
    try:
        with get_flask_app().app_context():
            task = db.session.get(StreamForwardTask, TASK_ID)
            if task:
                if status is not None:
                    task.status = status
                if exception_reason is not None:
                    task.exception_reason = exception_reason[:500]  # 限制长度
                db.session.commit()
                logger.debug(f"任务状态已更新: status={status}, exception_reason={exception_reason}")
    except Exception as e:
        logger.warning(f"更新任务状态失败: {str(e)}")


def send_heartbeat() -> bool:
    """发送心跳到 VIDEO 服务，成功返回 True。"""
    global _heartbeat_fail_streak
    try:
        import socket
        import os as os_module

        server_ip = os_module.getenv('POD_IP', '')
        if not server_ip:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                server_ip = s.getsockname()[0]
                s.close()
            except Exception:
                server_ip = 'localhost'

        process_id = os_module.getpid()
        log_path_for_heartbeat = (
            SERVICE_LOG_DIR
            if 'SERVICE_LOG_DIR' in globals()
            else os.path.join(video_root, 'logs', f'stream_forward_task_{TASK_ID}')
        )

        heartbeat_url = os.getenv('VIDEO_HEARTBEAT_URL', '').strip()
        if not heartbeat_url:
            heartbeat_url = f"http://localhost:{VIDEO_SERVICE_PORT}/video/stream-forward/heartbeat"

        response = requests.post(
            heartbeat_url,
            json={
                'task_id': TASK_ID,
                'server_ip': server_ip,
                'port': int(VIDEO_SERVICE_PORT),
                'process_id': process_id,
                'log_path': log_path_for_heartbeat,
            },
            timeout=5,
        )
        response.raise_for_status()
        logger.debug('心跳上报成功: task_id=%s', TASK_ID)
        update_task_status(status=0, exception_reason=None)
        with _heartbeat_fail_lock:
            _heartbeat_fail_streak = 0
        return True
    except Exception as e:
        logger.warning('心跳上报失败: %s', e)
        return False


def heartbeat_worker():
    """心跳上报工作线程"""
    global _heartbeat_fail_streak
    logger.info('💓 心跳上报线程启动')
    while not stop_event.is_set():
        try:
            if send_heartbeat():
                for _ in range(10):
                    if stop_event.is_set():
                        break
                    time.sleep(1)
                continue

            with _heartbeat_fail_lock:
                _heartbeat_fail_streak += 1
                streak = _heartbeat_fail_streak

            if HEARTBEAT_EXIT_ENABLED and streak >= HEARTBEAT_EXIT_FAILURES:
                logger.error(
                    '连续 %d 次心跳失败，控制面不可用，推流 worker 退出 (task_id=%s)',
                    streak, TASK_ID,
                )
                stop_event.set()
                break

            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(1)
        except Exception as e:
            logger.error('心跳上报线程异常: %s', e, exc_info=True)
            time.sleep(10)
    logger.info('💓 心跳上报线程停止')


def signal_handler(signum, frame):
    """信号处理函数"""
    logger.info(f"收到信号 {signum}，准备退出...")
    stop_event.set()


def main():
    """主函数"""
    global task_config, device_streams, heartbeat_thread
    
    logger.info("=" * 60)
    logger.info("推流转发服务启动")
    logger.info(f"任务ID: {TASK_ID}")
    logger.info(f"数据库URL: {DATABASE_URL}")
    logger.info(f"VIDEO服务端口: {VIDEO_SERVICE_PORT}")
    logger.info(f"心跳上报URL: http://localhost:{VIDEO_SERVICE_PORT}/video/stream-forward/heartbeat")
    logger.info(f"观感推流: {VIEW_OUTPUT_FPS} fps，VIEW_EXTRACT_INTERVAL={EXTRACT_INTERVAL}，实际推流 {TARGET_FPS} fps")
    logger.info(f"目标分辨率: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    logger.info(f"GOP大小: {FFMPEG_GOP_SIZE}")
    logger.info("=" * 60)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 加载任务配置
    if not load_task_config():
        logger.error("❌ 加载任务配置失败，服务退出")
        update_task_status(status=1, exception_reason="加载任务配置失败")
        return
    
    # 服务启动成功，更新状态为正常
    update_task_status(status=0, exception_reason=None)
    
    device_streams = task_config.device_streams

    if _ffmpeg_native_enabled():
        if _ffmpeg_native_mux_enabled():
            logger.info('使用 FFmpeg 单进程多路复用（STREAM_FORWARD_FFMPEG_MUX=true，不推荐生产）')
            _run_native_ffmpeg_mux_mode(device_streams)
        else:
            logger.info('使用原生推流模式（STREAM_FORWARD_FFMPEG_NATIVE=true）')
            _run_native_ffmpeg_relay_mode(device_streams)
        return
    
    # 经典模式：OpenCV 拉流 + stdin 推流
    # 为每个设备初始化 latest-frame 缓存与推流控制
    push_threads = []
    for device_id in device_streams.keys():
        device_latest_frames[device_id] = None
        device_latest_frame_locks[device_id] = threading.Lock()
        device_push_running[device_id] = threading.Event()
        device_push_running[device_id].clear()
        device_codec_fallback[device_id] = False
        device_push_success_counts[device_id] = 0
        frame_counts[device_id] = 0
        logger.info(f"✅ 初始化设备 {device_id} 的帧缓存与推流控制")
    
    # 为每个摄像头启动独立的拉流线程
    buffer_threads = []
    for device_id in device_streams.keys():
        thread = threading.Thread(
            target=buffer_worker,
            args=(device_id,),
            daemon=True,
            name=f"buffer-{device_id}",
        )
        thread.start()
        buffer_threads.append(thread)
        logger.info(f"✅ 启动设备 {device_id} 的拉流线程")
    
    # 为每个摄像头启动独立的固定速率推帧线程
    for device_id in device_streams.keys():
        push_thread = threading.Thread(
            target=_fixed_rate_push_worker,
            args=(device_id,),
            daemon=True,
            name=f"push-{device_id}",
        )
        push_thread.start()
        device_push_threads[device_id] = push_thread
        push_threads.append(push_thread)
        logger.info(f"✅ 启动设备 {device_id} 的固定速率推帧线程")
    
    # 启动心跳上报线程
    logger.info("💓 启动心跳上报线程...")
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    
    logger.info("=" * 60)
    logger.info("推流转发服务运行中...")
    logger.info(f"活跃设备数: {len(device_streams)}")
    logger.info("=" * 60)
    
    try:
        # 主循环
        while not stop_event.is_set():
            time.sleep(1)
            
            # 检查所有工作线程是否还在运行
            alive_buffer_threads = [t for t in buffer_threads if t.is_alive()]
            if len(alive_buffer_threads) == 0:
                logger.error("❌ 所有缓流器线程已退出，服务异常")
                update_task_status(status=1, exception_reason="所有缓流器线程已退出")
                break
            
            alive_push_threads = [t for t in push_threads if t.is_alive()]
            if len(alive_push_threads) == 0 and push_threads:
                logger.error("❌ 所有推流线程已退出，服务异常")
                update_task_status(status=1, exception_reason="所有推流线程已退出")
                break
            
            # 检查是否有活跃的推流进程
            active_pushers = sum(1 for p in device_pushers.values() if p and p.poll() is None)
            if active_pushers == 0 and len(device_pushers) > 0:
                # 有设备但没有活跃的推流进程，可能是异常情况
                logger.warning("⚠️  没有活跃的推流进程")
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，准备退出...")
    except Exception as e:
        logger.error(f"❌ 主循环异常: {str(e)}", exc_info=True)
        update_task_status(status=1, exception_reason=f"主循环异常: {str(e)[:450]}")
    finally:
        # 停止所有线程
        logger.info("正在停止推流转发服务...")
        stop_event.set()
        
        # 通知所有推流线程停止
        for device_id, push_running in list(device_push_running.items()):
            if push_running:
                push_running.set()
        
        # 等待所有工作线程结束
        for thread in buffer_threads:
            thread.join(timeout=10)
        
        for thread in push_threads:
            thread.join(timeout=10)
        
        # 停止所有FFmpeg进程
        for device_id, pusher in list(device_pushers.items()):
            if pusher:
                try:
                    # 先关闭stdin
                    if pusher.stdin:
                        try:
                            pusher.stdin.close()
                        except:
                            pass
                    
                    # 检查进程是否还在运行
                    if pusher.poll() is None:
                        # 尝试优雅终止
                        try:
                            pusher.terminate()
                            pusher.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            # 如果5秒内未结束，强制终止
                            if pusher.poll() is None:
                                try:
                                    pusher.kill()
                                    pusher.wait()
                                except:
                                    pass
                        except:
                            # 如果terminate失败，直接kill
                            if pusher.poll() is None:
                                try:
                                    pusher.kill()
                                    pusher.wait()
                                except:
                                    pass
                except Exception as e:
                    logger.warning(f"停止设备 {device_id} FFmpeg进程时出错: {str(e)}")
        
        # 停止所有VideoCapture
        for device_id, cap in list(device_caps.items()):
            if cap is not None:
                try:
                    cap.release()
                except:
                    pass
            device_caps.pop(device_id, None)
        
        # 清理 latest-frame 缓存
        device_latest_frames.clear()
        device_latest_frame_locks.clear()
        device_push_threads.clear()
        device_push_running.clear()
        
        # 更新任务状态为已停止
        try:
            update_task_status(status=0, exception_reason=None)
        except Exception as e:
            logger.warning(f"更新任务停止状态失败: {str(e)}")
        
        logger.info("推流转发服务已停止")


if __name__ == '__main__':
    main()
