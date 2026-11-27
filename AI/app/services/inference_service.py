"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import multiprocessing
import os
import platform
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import cv2
import numpy as np
import torch
from flask import current_app
from ultralytics import YOLO

from app.services.minio_service import ModelService
from db_models import Model, InferenceTask, db
from app.utils.onnx_inference import ONNXInference
from app.utils.yolo_chinese_font import ensure_ultralytics_chinese_plot_font
from app.utils.model_class_utils import parse_class_names_json, resolve_class_ids_from_names
from app.utils.algorithm_detection_draw import (
    ALGORITHM_DEFAULT_CONF,
    draw_algorithm_detections,
    yolo_results_to_detections,
)
from app.utils.rtsp_stream_pipeline import RtspStreamPipeline
from app.utils.srs_host import resolve_srs_play_host, resolve_srs_publish_host
from app.utils.stream_detect_utils import (
    build_stream_detect_config,
    warmup_stream_detection,
)


_active_rtsp_sessions: Dict[str, dict] = {}
_rtsp_sessions_lock = threading.Lock()


class _FfmpegFrameReader:
    """通过 ffmpeg 解码 RTSP/RTMP/HTTP-FLV，避免 OpenCV 拉 RTMP 出现 FLV packet mismatch。"""

    def __init__(self, url: str, width: int, height: int, fps: float, process: subprocess.Popen):
        self.url = url
        self.width = width
        self.height = height
        self.fps = fps
        self.process = process
        self._frame_bytes = width * height * 3
        self._pending_frame: Optional[np.ndarray] = None

    @property
    def alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def read(self) -> Optional[np.ndarray]:
        if self._pending_frame is not None:
            frame = self._pending_frame
            self._pending_frame = None
            return frame
        if not self.alive:
            return None
        raw = self.process.stdout.read(self._frame_bytes)
        if not raw or len(raw) < self._frame_bytes:
            return None
        return np.frombuffer(raw, dtype=np.uint8).reshape((self.height, self.width, 3))

    def release(self) -> None:
        proc = self.process
        self.process = None
        if proc is None:
            return
        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        try:
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()
        except Exception:
            pass


def _save_yolo_annotated_image(result, out_path: str) -> None:
    """保存 Ultralytics Results 可视化图；通过本机/环境变量字体映射支持中文类别名。"""
    ensure_ultralytics_chinese_plot_font()
    try:
        result.save(filename=out_path)
    except UnicodeEncodeError:
        logging.warning(
            "检测结果图保存仍出现编码错误，已改为仅绘制框线（不绘制文字标签）；"
            "可设置环境变量 YOLO_RESULT_FONT_PATH 指向可用的 .ttf/.ttc"
        )
        result.save(filename=out_path, labels=False)


class InferenceService:
    def __init__(self, model_id):
        self.model_id = model_id
        self.model_dir = self._get_model_dir()
        self.minio_bucket = "ai-models"
        self.inference_results_bucket = "inference-results"  # 推理结果专用bucket
        self.device = self._select_device()
        self.model_cache = {}  # 模型实例缓存
        self.onnx_cache = {}  # ONNX模型实例缓存
        self.media_server = self._get_media_server_url()
        self.specified_model_path = None  # 外部指定的模型文件路径
        self._local_srs_host: Optional[str] = None

    def _get_media_server_url(self):
        """从环境变量获取推流服务器地址"""
        push_url = os.getenv('MODEL_AI_PUSH_URL', 'pro.basiclab.top:1935')
        if not push_url.startswith('rtmp://'):
            push_url = f'rtmp://{push_url}'
        return push_url.rstrip('/')

    def _get_srs_host(self) -> str:
        parsed = urlparse(self.media_server)
        return parsed.hostname or '127.0.0.1'

    def _get_local_srs_host(self) -> str:
        """AI 服务实际用于推流的 SRS 地址，兼容 host 与 bridge 网络。"""
        if not self._local_srs_host:
            self._local_srs_host = resolve_srs_publish_host(
                port=self._get_local_srs_rtmp_port(),
            )
        return self._local_srs_host

    @staticmethod
    def _get_srs_play_host() -> str:
        return resolve_srs_play_host()

    def _get_stream_pull_hosts(self) -> list[str]:
        """SRS 拉流主机候选：loopback、MODEL_AI_PUSH_URL 主机、POD_IP。"""
        hosts: list[str] = []
        seen: set[str] = set()

        def add(host: str) -> None:
            host = (host or '').strip()
            if host and host not in seen:
                seen.add(host)
                hosts.append(host)

        add(self._get_local_srs_host())
        add(self._get_srs_host())
        add((os.getenv('POD_IP') or '').strip())
        add('127.0.0.1')
        add('localhost')
        return hosts

    def _get_local_srs_rtmp_port(self) -> int:
        try:
            return int(os.getenv('MODEL_AI_SRS_RTMP_PORT', '1935'))
        except (TypeError, ValueError):
            return 1935

    def _get_local_media_server(self) -> str:
        return f'rtmp://{self._get_local_srs_host()}:{self._get_local_srs_rtmp_port()}'

    def _get_srs_http_port(self) -> int:
        raw = os.getenv('MODEL_AI_HTTP_PORT', '8080')
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 8080

    @staticmethod
    def _normalize_model_suffix(model_id) -> str:
        if model_id is None:
            return 'default'
        text = str(model_id).strip()
        safe = re.sub(r'[^a-zA-Z0-9_-]+', '_', text)
        return safe or 'default'

    def _enrich_inference_parameters_from_device(
        self,
        device_id: Optional[str],
        parameters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """通过 VIDEO 服务补全设备流地址（含国标点播解析）。"""
        params = dict(parameters or {})
        device_id = (device_id or '').strip()
        if not device_id:
            return params
        try:
            from app.utils.video_device_client import fetch_device_inference_input
            device_input = fetch_device_inference_input(device_id)
        except Exception as exc:
            logging.warning(f'查询设备推理输入流失败 device_id={device_id}: {exc}')
            return params
        if not device_input:
            return params

        for key in ('rtsp_direct', 'rtmp_stream', 'http_stream', 'resolved_source'):
            val = (device_input.get(key) or '').strip()
            if val and not (params.get(key) or '').strip():
                params[key] = val
        return params

    def _build_inference_stream_urls(self, device_id: str, model_id=None) -> tuple[str, str]:
        """约定推理输出路径：ai/infer_{device_id}_m{model_id}（单层 app，兼容 SRS）"""
        model_suffix = self._normalize_model_suffix(model_id if model_id is not None else self.model_id)
        stream_path = f'ai/infer_{device_id}_m{model_suffix}'
        local_server = self._get_local_media_server()
        output_rtmp = f'{local_server}/{stream_path}'
        output_http = (
            f'http://{self._get_srs_play_host()}:{self._get_srs_http_port()}/{stream_path}.flv'
        )
        return output_rtmp, output_http

    def _http_flv_from_rtmp(self, rtmp_url: str) -> Optional[str]:
        trimmed = (rtmp_url or '').strip()
        if not trimmed.startswith('rtmp://'):
            return None
        try:
            parsed = urlparse(trimmed)
            host = parsed.hostname or '127.0.0.1'
            path = (parsed.path or '/live').strip('/')
            if not path:
                path = 'live'
            if not path.endswith('.flv'):
                path = f'{path}.flv'
            return f'http://{host}:{self._get_srs_http_port()}/{path}'
        except Exception:
            return None

    def _resolve_input_stream_candidates(
        self,
        input_source: str,
        device_id: Optional[str],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> list[str]:
        """输入流优先级：1) RTSP 直连  2) 设备已登记流地址  3) SRS live/{device_id}  4) 显式 RTMP/HTTP-FLV"""
        candidates: list[str] = []
        seen: set[str] = set()
        source = (input_source or '').strip()
        params = parameters or {}

        def add(url: str) -> None:
            url = (url or '').strip()
            if url and url not in seen:
                seen.add(url)
                candidates.append(url)

        if source.startswith('rtsp://'):
            add(source)

        resolved = (params.get('resolved_source') or '').strip()
        if resolved.startswith(('rtsp://', 'rtmp://')):
            add(resolved)
            if resolved.startswith('rtmp://'):
                http_flv = self._http_flv_from_rtmp(resolved)
                if http_flv:
                    add(http_flv)

        for key in ('rtsp_direct', 'rtmp_stream', 'http_stream'):
            val = (params.get(key) or '').strip()
            if val.startswith('rtsp://'):
                add(val)
            elif val.startswith('rtmp://'):
                add(val)
                http_flv = self._http_flv_from_rtmp(val)
                if http_flv:
                    add(http_flv)
            elif val.startswith(('http://', 'https://')) and (
                val.endswith('.flv') or '/live/' in val or '/ai/' in val
            ):
                add(val)

        if device_id:
            rtmp_port = self._get_local_srs_rtmp_port()
            http_port = self._get_srs_http_port()
            for host in self._get_stream_pull_hosts():
                add(f'rtmp://{host}:{rtmp_port}/live/{device_id}')
                add(f'http://{host}:{http_port}/live/{device_id}.flv')

        if source.startswith('rtmp://'):
            add(source)
            http_flv = self._http_flv_from_rtmp(source)
            if http_flv:
                add(http_flv)
        if source.startswith(('http://', 'https://')) and (
            source.endswith('.flv') or '/live/' in source or '/ai/' in source
        ):
            add(source)

        if not candidates:
            raise ValueError('缺少有效的输入流地址，请提供 device_id 或 input_source')
        return candidates

    @staticmethod
    def _parse_ffprobe_fps(rate_str: str) -> float:
        rate_str = (rate_str or '').strip()
        if not rate_str or rate_str == '0/0':
            return 25.0
        if '/' in rate_str:
            num, den = rate_str.split('/', 1)
            try:
                den_f = float(den)
                return float(num) / den_f if den_f else 25.0
            except ValueError:
                return 25.0
        try:
            val = float(rate_str)
            return val if val > 0 else 25.0
        except ValueError:
            return 25.0

    def _probe_stream_info(self, url: str, timeout_sec: float = 5.0) -> Optional[tuple[int, int, float]]:
        cmd = ['ffprobe', '-v', 'error']
        if url.startswith('rtsp://'):
            cmd += [
                '-rtsp_transport', 'tcp',
                '-stimeout', str(int(timeout_sec * 1_000_000)),
            ]
        cmd += [
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,avg_frame_rate',
            '-of', 'csv=p=0',
            url,
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec + 2,
            )
            if result.returncode != 0:
                return None
            parts = [p.strip() for p in result.stdout.strip().split(',')]
            if len(parts) < 3:
                return None
            width, height = int(parts[0]), int(parts[1])
            fps = self._parse_ffprobe_fps(parts[2])
            if width > 0 and height > 0:
                return width, height, fps
        except Exception as exc:
            logging.debug(f'ffprobe 探测失败 {url}: {exc}')
        return None

    def _start_ffmpeg_input_reader(self, url: str) -> subprocess.Popen:
        if url.startswith('rtsp://'):
            cmd = [
                'ffmpeg', '-nostdin', '-loglevel', 'error',
                '-rtsp_transport', 'tcp', '-stimeout', '5000000',
                '-i', url,
                '-an', '-sn', '-dn',
                '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                'pipe:1',
            ]
        else:
            cmd = [
                'ffmpeg', '-nostdin', '-loglevel', 'error',
                '-rw_timeout', '5000000',
                '-probesize', '500000', '-analyzeduration', '1000000',
                '-fflags', 'nobuffer', '-flags', 'low_delay',
                '-i', url,
                '-an', '-sn', '-dn',
                '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                'pipe:1',
            ]
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _open_input_reader(
        self,
        candidates: list[str],
        stop_event: threading.Event,
        session_key: Optional[str] = None,
        max_attempts: int = 15,
        retry_interval_sec: float = 2.0,
    ) -> _FfmpegFrameReader:
        """按优先级依次尝试打开输入流（ffmpeg 解码，RTSP 超时 5s；部署场景下可重试等待推流就绪）"""
        errors: list[str] = []
        attempts = max(1, int(max_attempts or 1))

        for attempt in range(1, attempts + 1):
            if stop_event.is_set():
                raise RuntimeError('推理已取消')
            if attempt > 1:
                logging.info(
                    f'输入流尚未就绪，{retry_interval_sec:.1f}s 后重试 '
                    f'({attempt}/{attempts})'
                )
                time.sleep(retry_interval_sec)
                if stop_event.is_set():
                    raise RuntimeError('推理已取消')

            errors.clear()
            for url in candidates:
                if stop_event.is_set():
                    raise RuntimeError('推理已取消')
                logging.info(f'尝试打开输入流: {url}')
                info = self._probe_stream_info(url, timeout_sec=5.0)
                if stop_event.is_set():
                    raise RuntimeError('推理已取消')
                if not info:
                    errors.append(f'{url}: 无法探测流信息')
                    continue
                width, height, fps = info
                proc = self._start_ffmpeg_input_reader(url)
                reader = _FfmpegFrameReader(url, width, height, fps, proc)
                if session_key:
                    with _rtsp_sessions_lock:
                        session = _active_rtsp_sessions.get(session_key)
                        if session:
                            session['reader'] = reader
                first_frame = reader.read()
                if stop_event.is_set():
                    reader.release()
                    raise RuntimeError('推理已取消')
                if first_frame is not None:
                    reader._pending_frame = first_frame
                    logging.info(f'输入流已连接: {url} ({width}x{height} @ {fps:.1f}fps)')
                    return reader
                stderr = ''
                try:
                    stderr = (proc.stderr.read() or b'').decode('utf-8', errors='ignore')[:200]
                except Exception:
                    pass
                errors.append(f'{url}: 无有效视频帧{(" - " + stderr) if stderr else ""}')
                reader.release()
                if session_key:
                    with _rtsp_sessions_lock:
                        session = _active_rtsp_sessions.get(session_key)
                        if session and session.get('reader') is reader:
                            session['reader'] = None

        raise RuntimeError(
            '无法打开输入流（已按 RTSP → 设备登记流 → SRS live 顺序尝试）: ' + '; '.join(errors)
        )

    @staticmethod
    def _rtsp_session_key(device_id: str, model_id=None) -> str:
        suffix = InferenceService._normalize_model_suffix(model_id)
        return f'{device_id}::{suffix}'

    @staticmethod
    def _terminate_ffmpeg_push(process: Optional[subprocess.Popen]) -> None:
        if process is None:
            return
        try:
            if process.stdin:
                process.stdin.close()
        except Exception:
            pass
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                try:
                    process.kill()
                    process.wait(timeout=1)
                except Exception:
                    pass

    @classmethod
    def _terminate_session_resources(cls, session: dict) -> None:
        reader = session.get('reader')
        if reader:
            try:
                reader.release()
            except Exception:
                pass
            session['reader'] = None
        cls._terminate_ffmpeg_push(session.get('push_process'))
        session['push_process'] = None

    @classmethod
    def stop_rtsp_inference(
        cls,
        device_id: Optional[str] = None,
        record_id: Optional[int] = None,
        stop_all: bool = False,
    ) -> int:
        stopped = 0
        with _rtsp_sessions_lock:
            keys = list(_active_rtsp_sessions.keys())
            for key in keys:
                session = _active_rtsp_sessions.get(key)
                if not session:
                    continue
                if not stop_all:
                    if record_id is not None and session.get('record_id') != record_id:
                        continue
                    if device_id is not None and session.get('device_id') != device_id:
                        continue
                cls._terminate_session_resources(session)
                stop_event = session.get('stop_event')
                if stop_event:
                    stop_event.set()
                output_url = session.get('output_url', '')
                if output_url:
                    logging.info(f'已停止摄像头推理推流: {output_url}')
                stopped += 1
        return stopped

    def _get_model_dir(self):
        """获取模型存储目录路径"""
        return os.path.join(
            current_app.root_path,
            'static',
            'models',
            str(self.model_id),
            'train',
            'weights'
        )

    def _select_device(self):
        """自动选择最优计算设备"""
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'


    def _load_model(self, model_path: str):
        """优化模型加载，支持混合精度和缓存，支持ONNX模型"""
        # 检查是否为ONNX模型
        is_onnx = model_path.lower().endswith('.onnx')
        
        if is_onnx:
            # ONNX模型使用新的ONNX推理模块
            if model_path in self.onnx_cache:
                return self.onnx_cache[model_path]
            
            try:
                onnx_model = ONNXInference(model_path)
                self.onnx_cache[model_path] = onnx_model
                logging.info(f"ONNX模型加载成功: {model_path}")
                return onnx_model
            except Exception as e:
                logging.error(f"ONNX模型加载失败: {str(e)}")
                raise
        else:
            # PyTorch模型使用YOLO
            if model_path in self.model_cache:
                return self.model_cache[model_path]
            
            try:
                model = YOLO(model_path)
                model.to(self.device)
                # 启用半精度推理（GPU环境，仅对PyTorch模型）
                if 'cuda' in self.device:
                    try:
                        model.model.half()  # FP16推理
                    except Exception as e:
                        logging.warning(f"无法启用半精度推理: {str(e)}，使用全精度")
                
                self.model_cache[model_path] = model
                logging.info(f"PyTorch模型加载成功: {model_path}, 设备: {self.device}")
                return model
            except Exception as e:
                logging.error(f"模型加载失败: {str(e)}")
                raise

    def get_model(self) -> YOLO:
        """获取模型实例，优先级：
        1. 外部指定的模型文件路径（specified_model_path）
        2. 如果 model_id 不为 None 且 > 0（用户选择了自己的模型）：
           - 优先查找本地模型目录中的模型文件
           - 如果本地没有，从MinIO下载模型
        3. 如果 model_id 为 None 或 <= 0（使用默认模型）：
           - AI目录下的默认模型文件（yolo11n.pt、yolov8n.pt 或 yolo26n.pt）
           - 其他默认模型路径
        """
        # 1. 优先使用外部指定的模型文件路径
        if self.specified_model_path and os.path.exists(self.specified_model_path):
            logging.info(f"使用指定的模型文件: {self.specified_model_path}")
            return self._load_model(self.specified_model_path)

        # 2. 如果用户选择了自己的模型（model_id > 0），优先使用用户模型
        if self.model_id and self.model_id > 0:
            logging.info(f"用户选择了模型 ID {self.model_id}，优先使用用户模型")
            
            # 2.1 优先查找本地模型文件
            local_model = self._find_local_model()
            if local_model:
                logging.info(f"找到本地用户模型: {local_model}")
                return self._load_model(local_model)

            # 2.2 如果本地没有，从MinIO下载模型
            downloaded_model = self._download_model_from_minio()
            if downloaded_model:
                logging.info(f"从MinIO下载用户模型: {downloaded_model}")
                return self._load_model(downloaded_model)
            
            # 模型记录存在，但本地与MinIO都无法获取可用模型文件
            raise Exception(
                f"模型 ID {self.model_id} 的模型文件不可用，请检查模型路径或先完成训练/上传后再推理"
            )

        # 3. 使用默认模型（当 model_id 为 None 或 <= 0 时）
        # 3.1 查找AI目录下的默认模型文件（yolo11n.pt、yolov8n.pt 或 yolo26n.pt）
        default_models = self._find_default_models()
        for model_path in default_models:
            if os.path.exists(model_path):
                logging.info(f"使用AI目录下的默认模型: {model_path}")
                return self._load_model(model_path)

        # 3.2 使用其他默认模型路径
        default_model = os.path.join('model', 'yolov8n.pt')
        if os.path.exists(default_model):
            return self._load_model(default_model)

        raise Exception("未找到可用的模型文件")

    def set_model_path(self, model_path: str):
        """设置指定的模型文件路径"""
        if model_path and os.path.exists(model_path):
            self.specified_model_path = os.path.abspath(model_path)
            logging.info(f"已设置模型文件路径: {self.specified_model_path}")
        else:
            logging.warning(f"指定的模型文件不存在: {model_path}")
            self.specified_model_path = None

    def _get_model_names_dict(self, model) -> Dict[int, str]:
        if isinstance(model, ONNXInference):
            return {int(k): str(v) for k, v in (model.classes_dict or {}).items()}
        if hasattr(model, 'names') and model.names:
            names = model.names
            if isinstance(names, dict):
                return {int(k): str(v) for k, v in names.items()}
        return {}

    def _resolve_selected_class_names(self, parameters: Optional[Dict[str, Any]]) -> Optional[list]:
        """仅当推理请求显式传入 selected_classes 时才过滤标签。"""
        if not parameters:
            return None
        selected = parameters.get('selected_classes')
        if selected is None:
            selected = parameters.get('selectedClasses')
        if selected is None:
            return None
        parsed = parse_class_names_json(selected)
        return parsed if parsed else None

    def _resolve_class_ids(self, model, parameters: Optional[Dict[str, Any]]) -> Optional[list]:
        selected_names = self._resolve_selected_class_names(parameters)
        if not selected_names:
            return None
        names_dict = self._get_model_names_dict(model)
        if not names_dict:
            return None
        return resolve_class_ids_from_names(names_dict, selected_names)

    def _build_inference_kwargs(
        self,
        model,
        parameters: Optional[Dict[str, Any]],
        conf_thres: float,
        iou_thres: float,
    ) -> Dict[str, Any]:
        inference_kwargs = {
            'conf': conf_thres,
            'iou': iou_thres,
            'verbose': False,
        }
        class_ids = self._resolve_class_ids(model, parameters)
        if class_ids:
            inference_kwargs['classes'] = class_ids
        inference_kwargs.setdefault('max_det', 300)
        return inference_kwargs

    @staticmethod
    def _annotate_frame_algorithm_style(
        frame: np.ndarray,
        *,
        yolo_result=None,
        detections: Optional[list] = None,
    ) -> np.ndarray:
        """绘制检测结果（绿框 + 类别置信度）。"""
        dets = detections if detections is not None else yolo_results_to_detections(yolo_result)
        return draw_algorithm_detections(frame, dets)

    def _find_default_models(self) -> list:
        """查找AI目录下的默认模型文件（yolo11n.pt、yolov8n.pt 或 yolo26n.pt）
        优先级：yolo11n.pt > yolov8n.pt > yolo26n.pt
        """
        default_models = []
        try:
            # 获取AI目录路径（run.py所在目录）
            app_root = current_app.root_path  # app目录路径
            ai_root = os.path.dirname(app_root)  # AI目录路径（通常是AI目录）
            
            # 尝试多个可能的AI目录位置
            possible_ai_dirs = [ai_root]  # 优先使用app的父目录
            
            # 如果app_root的父目录不是AI目录，尝试查找run.py所在目录
            if not os.path.exists(os.path.join(ai_root, 'run.py')):
                # 向上查找包含run.py的目录
                search_dir = os.path.dirname(os.path.abspath(__file__))
                for _ in range(3):  # 最多向上查找3层
                    if os.path.exists(os.path.join(search_dir, 'run.py')):
                        possible_ai_dirs.append(search_dir)
                        break
                    search_dir = os.path.dirname(search_dir)
            
            # 查找模型文件，优先yolo11n.pt，其次yolov8n.pt，再次yolo26n.pt
            for ai_dir in possible_ai_dirs:
                for model_name in ['yolo11n.pt', 'yolov8n.pt', 'yolo26n.pt']:
                    model_path = os.path.join(ai_dir, model_name)
                    abs_path = os.path.abspath(model_path)
                    if os.path.exists(model_path) and abs_path not in default_models:
                        default_models.append(abs_path)
            
            return default_models
        except Exception as e:
            logging.warning(f"查找默认模型文件失败: {str(e)}")
            return []

    def _get_expected_model_filename(self) -> Optional[str]:
        """从数据库获取期望的模型文件名"""
        try:
            model = Model.query.get(self.model_id)
            if not model:
                return None

            # 获取模型路径：优先使用model_path，其次使用onnx_model_path，最后从TrainTask获取minio_model_path
            minio_path = None
            if model.model_path:
                minio_path = model.model_path
            elif model.onnx_model_path:
                minio_path = model.onnx_model_path
            else:
                # 从TrainTask中获取最新的minio_model_path
                from db_models import TrainTask
                train_task = TrainTask.query.filter_by(
                    model_id=self.model_id,
                    status='completed'
                ).order_by(TrainTask.end_time.desc()).first()
                
                if train_task and train_task.minio_model_path:
                    minio_path = train_task.minio_model_path

            if not minio_path:
                return None

            # 如果是本地路径（不以 /api/v1/buckets/ 开头），直接提取文件名
            if not minio_path.startswith('/api/v1/buckets/'):
                return os.path.basename(minio_path)

            # 解析URL格式：/api/v1/buckets/{bucket}/objects/download?prefix={path}
            import urllib.parse
            try:
                parsed = urllib.parse.urlparse(minio_path)
                params = urllib.parse.parse_qs(parsed.query)
                if 'prefix' in params:
                    object_name = params['prefix'][0]
                    return os.path.basename(object_name)
            except Exception as e:
                logging.warning(f"解析模型路径失败: {minio_path}, 错误: {str(e)}")
                return None

        except Exception as e:
            logging.error(f"获取期望模型文件名失败: {str(e)}")
            return None

    def _find_local_model(self) -> Optional[str]:
        """在本地目录查找模型文件，并检查文件名是否与数据库中的模型文件匹配"""
        model_exts = ('.pt', '.onnx', '.engine')
        if not os.path.exists(self.model_dir):
            return None

        # 获取期望的模型文件名
        expected_filename = self._get_expected_model_filename()
        
        # 查找本地模型文件
        local_files = []
        for file in os.listdir(self.model_dir):
            if file.endswith(model_exts):
                model_path = os.path.join(self.model_dir, file)
                if os.path.exists(model_path):
                    local_files.append((file, model_path))

        if not local_files:
            return None

        # 如果数据库中有期望的文件名，检查是否匹配
        if expected_filename:
            # 查找匹配的文件
            for file, model_path in local_files:
                if file == expected_filename:
                    logging.info(f"找到匹配的本地模型文件: {model_path} (期望: {expected_filename})")
                    return model_path
            
            # 如果没有匹配的文件，说明模型文件已更新，需要删除旧文件并重新下载
            logging.info(f"本地模型文件名不匹配，期望: {expected_filename}, 本地文件: {[f[0] for f in local_files]}")
            logging.info("删除旧模型文件并准备重新下载")
            for file, model_path in local_files:
                try:
                    os.remove(model_path)
                    logging.info(f"已删除旧模型文件: {model_path}")
                except Exception as e:
                    logging.warning(f"删除旧模型文件失败: {model_path}, 错误: {str(e)}")
            return None
        else:
            # 如果数据库中没有期望的文件名，使用第一个找到的文件（向后兼容）
            if local_files:
                model_path = local_files[0][1]
                logging.info(f"未找到期望文件名，使用本地模型文件: {model_path}")
                return model_path

        return None

    def _download_model_from_minio(self) -> Optional[str]:
        """从MinIO下载模型文件"""
        try:
            import urllib.parse
            model = Model.query.get(self.model_id)
            if not model:
                return None

            # 获取模型路径：优先使用model_path，其次使用onnx_model_path，最后从TrainTask获取minio_model_path
            minio_path = None
            if model.model_path:
                minio_path = model.model_path
            elif model.onnx_model_path:
                minio_path = model.onnx_model_path
            else:
                # 从TrainTask中获取最新的minio_model_path
                from db_models import TrainTask
                train_task = TrainTask.query.filter_by(
                    model_id=self.model_id,
                    status='completed'
                ).order_by(TrainTask.end_time.desc()).first()
                
                if train_task and train_task.minio_model_path:
                    minio_path = train_task.minio_model_path

            if not minio_path:
                return None

            # 检查是否是本地路径且文件存在
            # 如果是本地路径（不以 /api/v1/buckets/ 开头，且是绝对路径或相对于static的路径）
            if not minio_path.startswith('/api/v1/buckets/'):
                # 尝试作为本地路径处理
                if os.path.isabs(minio_path):
                    # 绝对路径
                    if os.path.exists(minio_path):
                        logging.info(f"找到本地模型文件: {minio_path}")
                        return minio_path
                else:
                    # 相对路径，尝试相对于app root
                    app_root = current_app.root_path
                    local_path = os.path.join(app_root, minio_path)
                    if os.path.exists(local_path):
                        logging.info(f"找到本地模型文件: {local_path}")
                        return local_path
                    # 也尝试相对于AI目录
                    ai_root = os.path.dirname(app_root)
                    local_path = os.path.join(ai_root, minio_path)
                    if os.path.exists(local_path):
                        logging.info(f"找到本地模型文件: {local_path}")
                        return local_path

            # 确保模型目录存在
            os.makedirs(self.model_dir, exist_ok=True)

            # 解析minio_path：可能是URL格式或直接路径
            # URL格式：/api/v1/buckets/{bucket}/objects/download?prefix={path}
            # 直接路径：models/model_1/train_1/best.pt
            bucket_name = self.minio_bucket
            object_name = None

            if minio_path.startswith('/api/v1/buckets/'):
                # 解析URL格式
                try:
                    parsed = urllib.parse.urlparse(minio_path)
                    # 提取bucket名称：/api/v1/buckets/{bucket}/objects/...
                    parts = parsed.path.split('/')
                    if len(parts) >= 5:
                        bucket_name = parts[4]
                    
                    # 提取prefix参数
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'prefix' in params:
                        object_name = params['prefix'][0]
                    else:
                        logging.warning(f"URL中缺少prefix参数: {minio_path}")
                        return None
                except Exception as e:
                    logging.error(f"解析URL失败: {minio_path}, 错误: {str(e)}")
                    return None
            else:
                # 直接使用路径
                object_name = minio_path

            if not object_name:
                return None

            # 从object_name中提取文件名
            filename = object_name.split('/')[-1]
            local_path = os.path.join(self.model_dir, filename)

            # 如果目标文件已存在，先删除它（确保下载最新版本）
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    logging.info(f"已删除已存在的模型文件: {local_path}，准备重新下载")
                except Exception as e:
                    logging.warning(f"删除已存在的模型文件失败: {local_path}, 错误: {str(e)}")

            # 下载模型文件
            success, error_msg = ModelService.download_from_minio(
                    bucket_name,
                    object_name,
                    local_path
            )
            if success:
                # 处理压缩文件
                if filename.endswith('.zip'):
                    ModelService.extract_zip(local_path, self.model_dir)
                    os.remove(local_path)
                    return self._find_local_model()
                return local_path

        except Exception as e:
            logging.error(f"MinIO下载失败: {str(e)}")

        return None

    def inference_image(self, image_file, parameters: Dict[str, Any] = None, record_id: int = None) -> Dict[str, Any]:
        """优化图片推理，支持批量处理和结果导出
        支持文件对象（Flask FileStorage）或文件路径字符串
        """
        if parameters is None:
            parameters = {}

        # 如果提供了 record_id，使用已存在的记录；否则创建新记录
        if record_id:
            record = InferenceTask.query.get(record_id)
            if not record:
                raise ValueError(f"推理任务记录不存在: {record_id}")
        else:
            # 获取文件名（支持文件对象或路径字符串）
            if hasattr(image_file, 'filename'):
                input_source = image_file.filename
            elif isinstance(image_file, str):
                input_source = os.path.basename(image_file)
            else:
                input_source = 'unknown'

            # 处理 model_id：如果为 0 或不存在，设置为 None
            actual_model_id = None
            if self.model_id and self.model_id > 0:
                model = Model.query.get(self.model_id)
                if model:
                    actual_model_id = self.model_id
                else:
                    raise ValueError(f"模型 ID {self.model_id} 不存在，无法进行推理")
            else:
                logging.info(f"使用默认模型（model_id={self.model_id}）")
                actual_model_id = None

            record = InferenceTask(
                model_id=actual_model_id,
                inference_type='image',
                input_source=input_source,
                status='PROCESSING'
            )
            db.session.add(record)
            db.session.commit()

        try:
            start_time = time.time()
            model = self.get_model()
            
            # 判断是否为ONNX模型（通过检查model是否为ONNXInference实例）
            is_onnx = isinstance(model, ONNXInference)

            # 处理文件输入（支持文件对象或路径字符串）
            original_temp_path = None
            
            if isinstance(image_file, str):
                # 如果是路径字符串，直接使用
                temp_path = image_file
            else:
                # 如果是文件对象，保存到临时文件
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_img:
                    image_file.save(temp_img.name)
                    temp_path = temp_img.name
                    original_temp_path = temp_path

            # 执行推理
            conf_thres = parameters.get('conf_thres', 0.5)
            iou_thres = parameters.get('iou_thres', 0.45)
            class_ids = self._resolve_class_ids(model, parameters)
            
            if is_onnx:
                frame_bgr = cv2.imread(temp_path)
                _, detections = model.detect(
                    temp_path,
                    conf_threshold=conf_thres,
                    iou_threshold=iou_thres,
                    draw=False,
                    class_ids=class_ids,
                )
                if frame_bgr is not None:
                    output_image = self._annotate_frame_algorithm_style(
                        frame_bgr,
                        detections=detections,
                    )
                else:
                    output_image, detections = model.detect(
                        temp_path,
                        conf_threshold=conf_thres,
                        iou_threshold=iou_thres,
                        draw=False,
                        class_ids=class_ids,
                    )

                class ONNXResults:
                    def __init__(self, image, detections):
                        self.image = image
                        self.detections = detections

                results = [ONNXResults(output_image, detections)]
            else:
                # 使用YOLO模型推理
                inference_kwargs = self._build_inference_kwargs(model, parameters, conf_thres, iou_thres)
                results = model(temp_path, **inference_kwargs)

            # 获取原始图片URL（从record的input_source获取）
            original_image_url = record.input_source if record.input_source else None
            
            # 处理结果，传递原始图片URL
            result_data = self._process_image_results(results, record.id, original_image_url, is_onnx=is_onnx)

            # 更新任务记录：保存结果图片URL
            record.output_path = result_data.get('result_url')
            record.status = 'COMPLETED'
            record.processing_time = time.time() - start_time
            # 注意：InferenceTask模型可能没有parameters字段，需要检查
            # record.parameters = parameters
            db.session.commit()

            return result_data

        except Exception as e:
            record.status = 'FAILED'
            record.error_message = str(e)
            db.session.commit()
            logging.error(f"图片推理失败: {str(e)}")
            raise
        finally:
            # 清理资源和显存
            # 清理原始临时文件（如果是文件对象上传的）
            if 'original_temp_path' in locals() and original_temp_path and os.path.exists(original_temp_path):
                try:
                    os.unlink(original_temp_path)
                except:
                    pass
            self._cleanup_memory()

    def detect_image_file(self, image_path: str, parameters: Optional[Dict[str, Any]] = None) -> list:
        """轻量图片检测：仅返回 detections，不创建推理任务、不上传 MinIO（供自动标注批量调用）。"""
        if parameters is None:
            parameters = {}

        model = self.get_model()
        is_onnx = isinstance(model, ONNXInference)
        conf_thres = parameters.get('conf_thres', 0.5)
        iou_thres = parameters.get('iou_thres', 0.45)
        class_ids = self._resolve_class_ids(model, parameters)

        if is_onnx:
            _, detections = model.detect(
                image_path,
                conf_threshold=conf_thres,
                iou_threshold=iou_thres,
                draw=False,
                class_ids=class_ids,
            )
            return detections

        inference_kwargs = self._build_inference_kwargs(model, parameters, conf_thres, iou_thres)
        results = model(image_path, **inference_kwargs)
        detections = []
        for result in results:
            for box in result.boxes:
                detections.append({
                    'class': int(box.cls.item()),
                    'class_name': result.names[int(box.cls.item())],
                    'confidence': float(box.conf.item()),
                    'bbox': box.xyxy.tolist()[0],
                })
        return detections

    def _process_image_results(self, results, task_id: str, original_image_url: str = None, is_onnx: bool = False) -> Dict[str, Any]:
        """处理图片推理结果，生成可视化图和检测数据，并上传到MinIO
        Args:
            results: YOLO推理结果或ONNX推理结果
            task_id: 任务ID
            original_image_url: 原始图片的MinIO URL
            is_onnx: 是否为ONNX模型推理结果
        """
        result_image_path = None
        json_path = None
        try:
            # 创建临时目录用于保存结果（上传后删除）
            temp_dir = tempfile.mkdtemp()
            result_image_path = os.path.join(temp_dir, 'result.jpg')
            json_path = os.path.join(temp_dir, 'detections.json')

            # 提取检测结果和保存结果图像
            if is_onnx:
                # ONNX推理结果：results[0]是ONNXResults对象
                result_obj = results[0]
                # 保存结果图像
                cv2.imwrite(result_image_path, result_obj.image)
                # 使用ONNX推理返回的检测结果
                detections = result_obj.detections
            else:
                # YOLO推理结果：使用与 VIDEO 算法任务一致的绿框样式
                orig_img = results[0].orig_img
                if orig_img is None:
                    orig_img = cv2.imread(result_image_path) if os.path.exists(result_image_path) else None
                if orig_img is None:
                    _save_yolo_annotated_image(results[0], result_image_path)
                else:
                    annotated = self._annotate_frame_algorithm_style(
                        orig_img,
                        yolo_result=results[0],
                    )
                    cv2.imwrite(result_image_path, annotated)

                # 提取检测结果
                detections = []
                for i, result in enumerate(results):
                    boxes = result.boxes
                    for box in boxes:
                        detections.append({
                            'class': int(box.cls.item()),
                            'class_name': result.names[int(box.cls.item())],
                            'confidence': float(box.conf.item()),
                            'bbox': box.xyxy.tolist()[0],
                        })

            # 保存JSON检测结果到临时文件
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(detections, f, indent=2, ensure_ascii=False)

            # 上传结果图片到MinIO
            date_str = datetime.now().strftime('%Y%m%d')
            image_filename = f"result_{task_id}_{uuid.uuid4().hex[:8]}.jpg"
            image_object_key = f"images/{date_str}/{image_filename}"
            
            upload_success, upload_error = ModelService.upload_to_minio(
                self.inference_results_bucket,
                image_object_key,
                result_image_path
            )
            
            # 上传JSON检测结果到MinIO
            json_filename = f"detections_{task_id}_{uuid.uuid4().hex[:8]}.json"
            json_object_key = f"json/{date_str}/{json_filename}"
            
            json_upload_success, json_upload_error = ModelService.upload_to_minio(
                self.inference_results_bucket,
                json_object_key,
                json_path
            )
            
            # 生成结果图片的MinIO下载URL
            if upload_success:
                result_url = f"/api/v1/buckets/{self.inference_results_bucket}/objects/download?prefix={image_object_key}"
            else:
                logging.error(f"结果图片上传到MinIO失败: {image_object_key}")
                result_url = None

            # 返回结果：image_url是原始图片URL，result_url是结果图片URL
            return {
                'image_url': original_image_url,  # 原始图片的MinIO URL
                'result_url': result_url,  # 分析后的图片MinIO URL
                'detections': detections,
                'detection_count': len(detections),
                'json_url': f"/api/v1/buckets/{self.inference_results_bucket}/objects/download?prefix={json_object_key}" if json_upload_success else None
            }

        except Exception as e:
            logging.error(f"结果处理失败: {str(e)}")
            raise
        finally:
            # 清理临时文件和目录
            if result_image_path and os.path.exists(result_image_path):
                try:
                    os.unlink(result_image_path)
                except Exception as e:
                    logging.warning(f"删除临时结果图片失败: {str(e)}")
            if json_path and os.path.exists(json_path):
                try:
                    os.unlink(json_path)
                except Exception as e:
                    logging.warning(f"删除临时JSON文件失败: {str(e)}")
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logging.warning(f"删除临时目录失败: {str(e)}")

    def inference_video(self, video_file, parameters: Dict[str, Any] = None, record_id: int = None) -> Dict[str, Any]:
        """多进程视频处理，支持跳帧优化
        支持文件对象（Flask FileStorage）或文件路径字符串
        """
        if parameters is None:
            parameters = {}

        # 如果提供了 record_id，使用已存在的记录；否则创建新记录
        if record_id:
            record = InferenceTask.query.get(record_id)
            if not record:
                raise ValueError(f"推理任务记录不存在: {record_id}")
        else:
            # 获取文件名（支持文件对象或路径字符串）
            if hasattr(video_file, 'filename'):
                input_source = video_file.filename
            elif isinstance(video_file, str):
                input_source = os.path.basename(video_file)
            else:
                input_source = 'unknown'

            # 处理 model_id：如果为 0 或不存在，设置为 None
            actual_model_id = None
            if self.model_id and self.model_id > 0:
                model = Model.query.get(self.model_id)
                if model:
                    actual_model_id = self.model_id
                else:
                    raise ValueError(f"模型 ID {self.model_id} 不存在，无法进行推理")
            else:
                logging.info(f"使用默认模型（model_id={self.model_id}）")
                actual_model_id = None

            record = InferenceTask(
                model_id=actual_model_id,
                inference_type='video',
                input_source=input_source,
                status='PROCESSING'
            )
            db.session.add(record)
            db.session.commit()

        try:
            # 处理文件输入（支持文件对象或路径字符串）
            if isinstance(video_file, str):
                # 如果是路径字符串，直接使用
                video_path = video_file
                # 验证文件是否存在且不为空
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"视频文件不存在: {video_path}")
                if os.path.getsize(video_path) == 0:
                    raise ValueError(f"视频文件为空: {video_path}")
            else:
                # 如果是文件对象，保存到临时文件
                # 确保文件指针在开头
                if hasattr(video_file, 'seek'):
                    video_file.seek(0)
                
                # 创建临时文件（使用mkstemp确保文件存在且可写）
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4')
                os.close(temp_fd)  # 关闭文件描述符，Flask的save方法会重新打开
                
                try:
                    # 使用Flask FileStorage的save方法保存文件
                    # 确保文件指针在开头
                    video_file.seek(0)
                    video_file.save(temp_path)
                    
                    # 验证文件是否成功保存
                    if not os.path.exists(temp_path):
                        raise IOError(f"临时文件创建失败: {temp_path}")
                    
                    file_size = os.path.getsize(temp_path)
                    if file_size == 0:
                        raise ValueError(
                            f"保存的视频文件为空: {temp_path}。"
                            f"可能原因：1) 上传的文件为空 2) 文件保存过程中出错。"
                            f"请检查上传的文件是否完整。"
                        )
                    
                    logging.info(f"视频文件已保存到临时文件: {temp_path}, 大小: {file_size} 字节")
                    video_path = temp_path
                except Exception as e:
                    # 如果保存失败，清理临时文件
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                    logging.error(f"保存视频文件失败: {str(e)}")
                    raise

            # 检查multiprocessing启动方法，确保使用'spawn'以支持CUDA
            try:
                start_method = multiprocessing.get_start_method()
                if start_method != 'spawn':
                    logging.warning(
                        f"multiprocessing启动方法为'{start_method}'，可能导致CUDA错误。"
                        f"建议在应用启动时设置multiprocessing.set_start_method('spawn')"
                    )
            except RuntimeError:
                # 如果无法获取启动方法，继续执行（可能已经在子进程中）
                pass

            # 启动异步处理进程
            process = multiprocessing.Process(
                target=self._process_video_task,
                args=(video_path, record.id, parameters)
            )
            process.start()

            return {
                'status': 'processing',
                'record_id': record.id,
                'message': '视频处理已启动'
            }

        except Exception as e:
            record.status = 'FAILED'
            record.error_message = str(e)
            db.session.commit()
            logging.error(f"视频推理启动失败: {str(e)}")
            raise

    def _process_video_task(self, video_path: str, record_id: int, parameters: Dict[str, Any]):
        """视频处理子进程"""
        # 在子进程中创建应用上下文
        # 由于使用spawn启动方法，子进程需要重新创建应用实例
        from run import create_app
        app = create_app()
        
        temp_dir = None
        try:
            # 整个视频处理过程都在应用上下文中执行
            with app.app_context():
                # 在应用上下文中加载模型
                model = self.get_model()
                
                # 判断是否为ONNX模型（通过检查model是否为ONNXInference实例）
                is_onnx = isinstance(model, ONNXInference)
                
                # 构建推理参数
                conf_thres = parameters.get('conf_thres', 0.5) if parameters else 0.5
                iou_thres = parameters.get('iou_thres', 0.45) if parameters else 0.45
                class_ids = self._resolve_class_ids(model, parameters)
                
                if is_onnx:
                    logging.info(f"视频推理：使用ONNX模型")
                else:
                    inference_kwargs = self._build_inference_kwargs(model, parameters, conf_thres, iou_thres)
                
                start_time = time.time()

                # 创建临时输出目录
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, 'processed.mp4')

                # 验证视频文件是否存在
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"视频文件不存在: {video_path}")
                
                # 检查文件大小
                file_size = os.path.getsize(video_path)
                if file_size == 0:
                    raise ValueError(f"视频文件为空: {video_path}")
                
                # 视频处理
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise ValueError(
                        f"无法打开视频文件: {video_path}。"
                        f"可能原因：1) 视频文件损坏或不完整（moov atom not found）"
                        f" 2) 视频格式不支持 3) 文件权限问题"
                    )
                
                # 尝试读取第一帧以验证视频是否可读
                ret, test_frame = cap.read()
                if not ret or test_frame is None:
                    cap.release()
                    raise ValueError(
                        f"无法读取视频帧: {video_path}。"
                        f"视频文件可能损坏或不完整（moov atom not found）。"
                        f"请检查视频文件是否完整上传。"
                    )
                # 重置到开头
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0:
                    fps = 25  # 默认帧率
                    logging.warning(f"无法获取视频帧率，使用默认值: {fps} fps")
                    
                frame_size = (
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                )
                
                if frame_size[0] <= 0 or frame_size[1] <= 0:
                    cap.release()
                    raise ValueError(f"无效的视频尺寸: {frame_size}。视频文件可能损坏。")

                # 视频编码器 - 使用临时文件，后续用FFmpeg转换为H.264
                # 先使用mp4v编码生成临时视频
                temp_output_path = os.path.join(temp_dir, 'temp_processed.mp4')
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(temp_output_path, fourcc, fps, frame_size)
                
                if not out.isOpened():
                    raise ValueError(f"无法创建视频输出文件: {temp_output_path}")

                # 跳帧处理优化
                frame_skip = parameters.get('frame_skip', 3) if parameters else 3
                frame_count = 0
                processed_frames = 0

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # 跳帧策略
                    if frame_count % frame_skip == 0:
                        if is_onnx:
                            _, detections = model.detect(
                                frame,
                                conf_threshold=conf_thres,
                                iou_threshold=iou_thres,
                                draw=False,
                                class_ids=class_ids,
                            )
                            annotated_frame = self._annotate_frame_algorithm_style(
                                frame,
                                detections=detections,
                            )
                            annotated_frame = cv2.resize(annotated_frame, frame_size, interpolation=cv2.INTER_LINEAR)
                        else:
                            # 使用YOLO模型推理
                            results = model(frame, **inference_kwargs)
                            annotated_frame = self._annotate_frame_algorithm_style(
                                frame,
                                yolo_result=results[0],
                            )
                        out.write(annotated_frame)
                        processed_frames += 1
                    else:
                        out.write(frame)

                    frame_count += 1

                # 释放资源
                cap.release()
                out.release()

                # 使用FFmpeg将视频转换为H.264编码，确保浏览器兼容性
                # H.264编码的MP4文件可以在所有现代浏览器中播放
                logging.info(f"开始使用FFmpeg转换视频为H.264编码: {temp_output_path} -> {output_path}")
                
                # 检查操作系统平台，选择合适的编码器
                if platform.system() == "Darwin":  # macOS
                    # 在macOS上使用VideoToolbox编码器
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-y',  # 覆盖输出文件
                        '-i', temp_output_path,  # 输入文件
                        '-c:v', 'h264_videotoolbox',  # 使用VideoToolbox H.264视频编码
                        '-profile:v', 'main',  # 使用main profile以确保兼容性
                        '-level', '4.0',  # 使用level 4.0以确保兼容性
                        '-pix_fmt', 'yuv420p',  # 像素格式，确保浏览器兼容
                        '-movflags', '+faststart',  # 优化网络播放（将moov atom移到文件开头）
                        '-c:a', 'aac',  # 音频编码（如果有音频轨道）
                        '-b:a', '128k',  # 音频比特率
                        output_path  # 输出文件
                    ]
                else:
                    # 在其他平台上使用libx264编码器
                    ffmpeg_cmd = [
                        'ffmpeg',
                        '-y',  # 覆盖输出文件
                        '-i', temp_output_path,  # 输入文件
                        '-c:v', 'libx264',  # 使用H.264视频编码
                        '-preset', 'medium',  # 编码速度和质量平衡
                        # '-crf', '23',  # 质量控制（18-28，23是默认值）
                        '-pix_fmt', 'yuv420p',  # 像素格式，确保浏览器兼容
                        '-movflags', '+faststart',  # 优化网络播放（将moov atom移到文件开头）
                        '-c:a', 'aac',  # 音频编码（如果有音频轨道）
                        '-b:a', '128k',  # 音频比特率
                        output_path  # 输出文件
                    ]
                
                logging.info(f"执行FFmpeg命令: {' '.join(ffmpeg_cmd)}")
                try:
                    result = subprocess.run(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=300  # 5分钟超时
                    )
                except subprocess.TimeoutExpired as exc:
                    raise RuntimeError('FFmpeg 转换 H.264 超时，未生成浏览器可播放结果') from exc
                except FileNotFoundError as exc:
                    raise RuntimeError('运行环境缺少 FFmpeg，无法生成浏览器可播放的 H.264 视频') from exc

                if result.returncode != 0:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')[-2000:]
                    raise RuntimeError(f'FFmpeg 转换 H.264 失败: {error_msg}')
                if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                    raise RuntimeError('FFmpeg 未生成有效的 H.264 输出文件')

                logging.info(f"FFmpeg转换成功: {output_path}")
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)

                # 上传结果到MinIO（使用推理结果专用bucket）
                date_str = datetime.now().strftime('%Y%m%d')
                object_key = f"videos/{date_str}/processed_{record_id}_{int(time.time())}.mp4"
                upload_success, upload_error = ModelService.upload_to_minio(
                    self.inference_results_bucket,
                    object_key,
                    output_path
                )
                
                # 生成访问URL
                if upload_success:
                    result_url = f"/api/v1/buckets/{self.inference_results_bucket}/objects/download?prefix={object_key}"
                else:
                    raise RuntimeError(
                        f"视频结果上传到MinIO失败: {object_key}: {upload_error or '未知错误'}"
                    )

                # 更新数据库（在应用上下文中）
                record = InferenceTask.query.get(record_id)
                if record:
                    record.output_path = result_url
                    record.processed_frames = processed_frames
                    record.status = 'COMPLETED'
                    record.end_time = datetime.utcnow()
                    record.processing_time = time.time() - start_time
                    db.session.commit()
                else:
                    logging.error(f"推理任务记录不存在: {record_id}")

        except Exception as e:
            logging.error(f"视频处理失败: {str(e)}")
            # 在应用上下文中更新错误状态
            try:
                with app.app_context():
                    record = InferenceTask.query.get(record_id)
                    if record:
                        record.status = 'FAILED'
                        record.error_message = str(e)
                        db.session.commit()
            except Exception as db_error:
                logging.error(f"更新数据库失败: {str(db_error)}")
        finally:
            # 清理资源
            self._cleanup_resources(video_path, temp_dir)

    def inference_rtsp(self, rtsp_url: str, parameters: Dict[str, Any] = None, record_id: int = None) -> Dict[str, Any]:
        """RTSP/RTMP 流实时处理：从 SRS 拉 live 流，推理后推到 ai/infer/{device_id}/m{model_id}"""
        if parameters is None:
            parameters = {}

        device_id = (parameters.get('device_id') or '').strip() or None

        # 如果提供了 record_id，使用已存在的记录；否则创建新记录
        if record_id:
            record = InferenceTask.query.get(record_id)
            if not record:
                raise ValueError(f"推理任务记录不存在: {record_id}")
        else:
            # 处理 model_id：如果为 0 或不存在，设置为 None
            actual_model_id = None
            if self.model_id and self.model_id > 0:
                model = Model.query.get(self.model_id)
                if model:
                    actual_model_id = self.model_id
                else:
                    raise ValueError(f"模型 ID {self.model_id} 不存在，无法进行推理")
            else:
                logging.info(f"使用默认模型（model_id={self.model_id}）")
                actual_model_id = None

            record = InferenceTask(
                model_id=actual_model_id,
                inference_type='rtsp',
                input_source=rtsp_url or (f'device:{device_id}' if device_id else ''),
                status='PROCESSING'
            )
            db.session.add(record)
            db.session.commit()

        try:
            parameters = self._enrich_inference_parameters_from_device(device_id, parameters)
            input_candidates = self._resolve_input_stream_candidates(rtsp_url, device_id, parameters)
            # 同一时刻仅保留一路推理推流，启动前先停掉所有旧会话
            self.stop_rtsp_inference(stop_all=True)
            time.sleep(0.3)

            local_server = self._get_local_media_server()
            if device_id:
                output_url, play_url = self._build_inference_stream_urls(device_id, self.model_id)
            else:
                stream_name = f"stream_{self.model_id}_{int(time.time())}"
                output_url = f"{local_server}/live/{stream_name}"
                play_url = (
                    f"http://{self._get_srs_play_host()}:{self._get_srs_http_port()}"
                    f"/live/{stream_name}.flv"
                )

            stop_event = threading.Event()
            session_key = self._rtsp_session_key(device_id or f'record_{record.id}', self.model_id)
            with _rtsp_sessions_lock:
                _active_rtsp_sessions[session_key] = {
                    'record_id': record.id,
                    'device_id': device_id,
                    'model_id': self.model_id,
                    'output_url': output_url,
                    'stop_event': stop_event,
                    'reader': None,
                    'push_process': None,
                }

            # 启动流处理线程（子线程无 Flask 请求上下文，须传入 app 实例）
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=self._process_rtsp_stream,
                args=(app, input_candidates, output_url, record.id, parameters, stop_event, session_key),
                daemon=True
            )
            thread.start()

            return {
                'stream_url': play_url,
                'rtmp_url': output_url,
                'input_url': input_candidates[0],
                'input_candidates': input_candidates,
                'record_id': record.id,
                'device_id': device_id,
                'status': 'streaming_started'
            }

        except Exception as e:
            record.status = 'FAILED'
            record.error_message = str(e)
            db.session.commit()
            logging.error(f"RTSP流启动失败: {str(e)}")
            raise

    def _process_rtsp_stream(
        self,
        app,
        input_candidates: list[str],
        output_url: str,
        record_id: int,
        parameters: Dict[str, Any],
        stop_event: threading.Event,
        session_key: str,
    ):
        """从 RTSP/本机 SRS 拉流，推理后推送到本机 SRS"""
        ctx = app.app_context()
        ctx.push()
        reader: Optional[_FfmpegFrameReader] = None
        ffmpeg_process = None
        input_url = input_candidates[0] if input_candidates else ''

        try:
            model = self.get_model()
            model_label = getattr(model, 'model_path', None) or self.specified_model_path or str(self.model_id)
            logging.info(f'RTSP流推理模型: {model_label}')

            class_ids = self._resolve_class_ids(model, parameters)
            class_id_set = set(class_ids) if class_ids else None
            model_path = getattr(model, 'model_path', None) or self.specified_model_path or ''

            reader = self._open_input_reader(input_candidates, stop_event, session_key)
            input_url = reader.url
            width, height, fps = reader.width, reader.height, reader.fps
            logging.info(f'摄像头推理输入流: {input_url} ({width}x{height} @ {fps:.1f}fps)')
            logging.info(f'摄像头推理输出流: {output_url}')

            if width <= 0 or height <= 0:
                raise RuntimeError(f'输入流无有效视频帧: {input_url}')

            detect_config = build_stream_detect_config(
                model,
                frame_height=height,
                model_path=str(model_path),
                model_id=self.model_id,
                parameters=parameters,
                infer_device=self.device,
            )
            try:
                extract_interval = int(
                    parameters.get('stream_extract_interval')
                    or parameters.get('frame_skip')
                    or os.getenv('OVERLAY_EXTRACT_INTERVAL', '5')
                )
            except (TypeError, ValueError):
                extract_interval = 5
            extract_interval = max(1, extract_interval)

            cap_fps = int(os.getenv('STREAM_OUTPUT_FPS', os.getenv('AI_OUTPUT_FPS', '25')))
            output_fps = max(1, min(int(fps or 25), cap_fps))

            logging.info(
                f'RTSP流推理参数(对齐算法任务): conf={detect_config["conf"]:.2f} '
                f'iou={detect_config["iou"]:.2f} imgsz={detect_config["imgsz"]} '
                f'overlay_interval={extract_interval} output_fps={output_fps} '
                f'classes={sorted(class_id_set) if class_id_set else "all"}'
            )

            try:
                warmup_stream_detection(model, detect_config=detect_config)
            except Exception as warmup_err:
                logging.warning(f'RTSP流推理预热失败（继续运行）: {warmup_err}')

            # FFmpeg推流命令 - 根据平台选择编码器
            if platform.system() == "Darwin":  # macOS
                command = [
                    'ffmpeg',
                    '-y',
                    '-f', 'rawvideo',
                    '-vcodec', 'rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-s', f'{width}x{height}',
                    '-r', str(output_fps),
                    '-i', '-',
                    '-c:v', 'h264_videotoolbox',
                    '-profile:v', 'main',
                    '-level', '4.0',
                    '-preset', 'ultrafast',
                    '-tune', 'zerolatency',
                    '-pix_fmt', 'yuv420p',
                    '-f', 'flv',
                    output_url
                ]
            else:
                command = [
                    'ffmpeg',
                    '-y',
                    '-f', 'rawvideo',
                    '-vcodec', 'rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-s', f'{width}x{height}',
                    '-r', str(output_fps),
                    '-i', '-',
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-tune', 'zerolatency',
                    '-pix_fmt', 'yuv420p',
                    '-f', 'flv',
                    output_url
                ]

            ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE)
            with _rtsp_sessions_lock:
                session = _active_rtsp_sessions.get(session_key)
                if session:
                    session['reader'] = reader
                    session['push_process'] = ffmpeg_process

            # 更新状态
            record = InferenceTask.query.get(record_id)
            record.stream_output_url = output_url
            record.status = 'RUNNING'
            db.session.commit()

            # 推流与推理分离：主循环只读帧叠 overlay，检测与固定帧率推流在独立线程
            pipeline = RtspStreamPipeline(
                reader=reader,
                ffmpeg_process=ffmpeg_process,
                model=model,
                detect_config=detect_config,
                stop_event=stop_event,
                class_ids=class_id_set,
                extract_interval=extract_interval,
                output_fps=output_fps,
                log_interval=max(1, output_fps * 6),
            )
            pipeline.run()

            # 流结束
            record = InferenceTask.query.get(record_id)
            if record:
                record.status = 'COMPLETED' if not stop_event.is_set() else 'STOPPED'
                db.session.commit()

        except Exception as e:
            logging.error(f"RTSP处理失败: {str(e)}")
            try:
                record = InferenceTask.query.get(record_id)
                if record:
                    record.status = 'FAILED'
                    record.error_message = str(e)
                    db.session.commit()
            except Exception as db_error:
                logging.error(f"更新RTSP任务失败状态失败: {str(db_error)}")
        finally:
            with _rtsp_sessions_lock:
                _active_rtsp_sessions.pop(session_key, None)
            if reader:
                reader.release()
            if ffmpeg_process:
                self._terminate_ffmpeg_push(ffmpeg_process)
            self._cleanup_memory()
            ctx.pop()

    def _cleanup_memory(self):
        """清理内存和显存资源"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def _cleanup_resources(self, file_path: str, temp_dir: Optional[str]):
        """清理临时资源"""
        try:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logging.warning(f"资源清理失败: {str(e)}")

    def get_task_status(self, record_id: int) -> Dict[str, Any]:
        """获取任务状态"""
        record = InferenceTask.query.get(record_id)
        if not record:
            return {'error': '任务不存在'}

        return {
            'status': record.status,
            'output_path': record.output_path,
            'processing_time': record.processing_time,
            'error_message': record.error_message
        }
