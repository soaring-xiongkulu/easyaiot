"""
姿态分析服务：图片 / 视频 / 摄像头(RTSP) 姿态估计。
"""
from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from typing import Any, Dict, Optional

from flask import current_app

from app.services.inference_service import InferenceService
from app.services.minio_service import ModelService
from app.utils.pose_inference import DEFAULT_POSE_MODELS, estimate_pose, pose_video
from app.utils.pose_rtsp_pipeline import PoseRtspStreamPipeline
from db_models import InferenceTask, Model, db

logger = logging.getLogger(__name__)

_pose_video_jobs: Dict[str, dict] = {}
_pose_video_jobs_lock = threading.Lock()

_active_pose_rtsp_sessions: Dict[str, dict] = {}
_pose_rtsp_sessions_lock = threading.Lock()


class PoseService:
    """姿态估计服务，复用 InferenceService 的模型加载与 RTSP 基础设施。"""

    def __init__(self, model_id: Optional[int] = None):
        self.model_id = model_id if model_id and model_id > 0 else None
        self._inference = InferenceService(model_id or 0)

    def set_model_file_path(self, model_file_path: str) -> None:
        self._inference.set_model_path(self._resolve_model_path(model_file_path))

    def _resolve_model_path(self, model_file_path: str) -> str:
        app_root = current_app.root_path
        ai_root = os.path.dirname(app_root)
        candidates = [
            os.path.join(ai_root, model_file_path),
            os.path.join(os.getcwd(), model_file_path),
            os.path.join(os.getcwd(), 'AI', model_file_path),
        ]
        for path in candidates:
            abs_path = os.path.abspath(path)
            if os.path.isfile(abs_path):
                return abs_path
        raise FileNotFoundError(f'姿态模型文件不存在: {model_file_path}')

    def get_model_path(self) -> str:
        """获取可用于姿态推理的 YOLO 权重路径。"""
        if self._inference.specified_model_path and os.path.isfile(self._inference.specified_model_path):
            return self._inference.specified_model_path

        if self.model_id:
            model = Model.query.get(self.model_id)
            if not model:
                raise ValueError(f'模型 ID {self.model_id} 不存在')
            local = self._inference._find_local_model()
            if local:
                return local
            downloaded = self._inference._download_model_from_minio()
            if downloaded:
                return downloaded
            raise ValueError(f'模型 ID {self.model_id} 的权重文件不可用')

        app_root = current_app.root_path
        ai_root = os.path.dirname(app_root)
        for name in DEFAULT_POSE_MODELS:
            for base in (ai_root, os.getcwd(), os.path.join(os.getcwd(), 'AI')):
                path = os.path.abspath(os.path.join(base, name))
                if os.path.isfile(path):
                    return path
        return DEFAULT_POSE_MODELS[0]

    def predict_image(self, image_bytes: bytes, conf: float = 0.25, draw: bool = True) -> dict:
        model_path = self.get_model_path()
        if not os.path.isfile(model_path):
            from ultralytics import YOLO
            YOLO(model_path)
        return estimate_pose(model_path, image_bytes, conf=conf, draw=draw)

    def start_video_job(self, src_path: str, conf: float = 0.25) -> str:
        job_id = uuid.uuid4().hex
        out_dir = os.path.join(tempfile.gettempdir(), 'pose_outputs')
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(src_path))[0] or 'video'
        out_name = f'{base}_{int(time.time())}_pose.mp4'
        out_path = os.path.join(out_dir, out_name)

        with _pose_video_jobs_lock:
            _pose_video_jobs[job_id] = {
                'status': 'running',
                'processed': 0,
                'total': 0,
                'stats': None,
                'error': None,
            }

        model_path = self.get_model_path()
        app = current_app._get_current_object()

        def worker():
            with app.app_context():
                def progress_cb(processed, total):
                    with _pose_video_jobs_lock:
                        job = _pose_video_jobs.get(job_id)
                        if job:
                            job['processed'] = processed
                            job['total'] = total

                try:
                    stats = pose_video(model_path, src_path, out_path, conf=conf, progress_cb=progress_cb)
                    result_url = self._upload_video_result(out_path, out_name)
                    stats['output'] = out_name
                    stats['result_url'] = result_url
                    with _pose_video_jobs_lock:
                        _pose_video_jobs[job_id].update(
                            status='done',
                            stats=stats,
                            processed=stats['frames'],
                            total=stats['frames'],
                        )
                except Exception as exc:
                    logger.exception('姿态视频处理失败')
                    with _pose_video_jobs_lock:
                        _pose_video_jobs[job_id].update(status='error', error=str(exc))
                finally:
                    if os.path.isfile(src_path) and src_path.startswith(tempfile.gettempdir()):
                        try:
                            os.remove(src_path)
                        except OSError:
                            pass

        threading.Thread(target=worker, daemon=True).start()
        return job_id

    def get_video_progress(self, job_id: str) -> Optional[dict]:
        with _pose_video_jobs_lock:
            return dict(_pose_video_jobs.get(job_id) or {})

    def get_output_path(self, filename: str) -> str:
        safe = os.path.basename(filename)
        out_dir = os.path.join(tempfile.gettempdir(), 'pose_outputs')
        path = os.path.join(out_dir, safe)
        if not os.path.isfile(path):
            raise FileNotFoundError(f'输出文件不存在: {safe}')
        return path

    def _upload_video_result(self, local_path: str, filename: str) -> str:
        bucket = 'inference-results'
        object_key = f'pose/{filename}'
        upload_ok, upload_err = ModelService.upload_to_minio(bucket, object_key, local_path)
        if upload_ok:
            return f'/api/v1/buckets/{bucket}/objects/download?prefix={object_key}'
        logger.warning('姿态视频上传 MinIO 失败，使用本地路径: %s', upload_err)
        return local_path

    def start_rtsp(
        self,
        rtsp_url: str,
        parameters: Optional[Dict[str, Any]] = None,
        record_id: Optional[int] = None,
    ) -> dict:
        """启动 RTSP/RTMP 摄像头姿态推流。"""
        parameters = dict(parameters or {})
        device_id = (parameters.get('device_id') or '').strip() or None
        conf = float(parameters.get('conf') or parameters.get('conf_thres') or 0.25)

        if record_id:
            record = InferenceTask.query.get(record_id)
            if not record:
                raise ValueError(f'推理任务记录不存在: {record_id}')
        else:
            record = InferenceTask(
                model_id=self.model_id,
                inference_type='rtsp',
                input_source=rtsp_url or (f'device:{device_id}' if device_id else ''),
                status='PROCESSING',
            )
            db.session.add(record)
            db.session.commit()

        try:
            parameters = self._inference._enrich_inference_parameters_from_device(device_id, parameters)
            input_candidates = self._inference._resolve_input_stream_candidates(rtsp_url, device_id, parameters)
            self.stop_rtsp(stop_all=True)
            time.sleep(0.3)

            local_server = self._inference._get_local_media_server()
            if device_id:
                model_suffix = InferenceService._normalize_model_suffix(
                    self.model_id if self.model_id is not None else 0
                )
                stream_path = f'ai/pose_{device_id}_m{model_suffix}'
                output_url = f'{local_server}/{stream_path}'
                play_url = (
                    f'http://{self._inference._get_srs_play_host()}:{self._inference._get_srs_http_port()}'
                    f'/{stream_path}.flv'
                )
            else:
                stream_name = f'pose_{self.model_id or 0}_{int(time.time())}'
                output_url = f'{local_server}/live/{stream_name}'
                play_url = (
                    f'http://{self._inference._get_srs_play_host()}:{self._inference._get_srs_http_port()}'
                    f'/live/{stream_name}.flv'
                )

            stop_event = threading.Event()
            session_key = self._pose_session_key(device_id or f'record_{record.id}', self.model_id)
            with _pose_rtsp_sessions_lock:
                _active_pose_rtsp_sessions[session_key] = {
                    'record_id': record.id,
                    'device_id': device_id,
                    'model_id': self.model_id,
                    'output_url': output_url,
                    'stop_event': stop_event,
                    'reader': None,
                    'push_process': None,
                }

            app = current_app._get_current_object()
            thread = threading.Thread(
                target=self._process_rtsp_stream,
                args=(app, input_candidates, output_url, record.id, conf, parameters, stop_event, session_key),
                daemon=True,
            )
            thread.start()

            return {
                'stream_url': play_url,
                'rtmp_url': output_url,
                'input_url': input_candidates[0],
                'record_id': record.id,
                'device_id': device_id,
                'status': 'streaming_started',
            }
        except Exception as exc:
            record.status = 'FAILED'
            record.error_message = str(exc)
            db.session.commit()
            raise

    @staticmethod
    def _pose_session_key(device_id: str, model_id) -> str:
        return f'pose:{device_id}:m{model_id or 0}'

    def stop_rtsp(
        self,
        device_id: Optional[str] = None,
        record_id: Optional[int] = None,
        stop_all: bool = False,
    ) -> int:
        stopped = 0
        with _pose_rtsp_sessions_lock:
            keys = list(_active_pose_rtsp_sessions.keys())
            for key in keys:
                session = _active_pose_rtsp_sessions.get(key)
                if not session:
                    continue
                if not stop_all:
                    if device_id and session.get('device_id') != device_id:
                        continue
                    if record_id and session.get('record_id') != record_id:
                        continue
                    if not device_id and not record_id:
                        continue

                stop_event = session.get('stop_event')
                if stop_event:
                    stop_event.set()
                reader = session.get('reader')
                if reader:
                    reader.release()
                proc = session.get('push_process')
                if proc:
                    self._inference._terminate_ffmpeg_push(proc)
                _active_pose_rtsp_sessions.pop(key, None)
                stopped += 1
        return stopped

    def _process_rtsp_stream(
        self,
        app,
        input_candidates: list,
        output_url: str,
        record_id: int,
        conf: float,
        parameters: dict,
        stop_event: threading.Event,
        session_key: str,
    ):
        ctx = app.app_context()
        ctx.push()
        reader = None
        ffmpeg_process = None

        try:
            model = self._inference.get_model()
            reader = self._inference._open_input_reader(input_candidates, stop_event, session_key=None)
            width, height, fps = reader.width, reader.height, reader.fps
            if width <= 0 or height <= 0:
                raise RuntimeError(f'输入流无有效视频帧: {reader.url}')

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

            if platform.system() == 'Darwin':
                command = [
                    'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
                    '-pix_fmt', 'bgr24', '-s', f'{width}x{height}', '-r', str(output_fps),
                    '-i', '-', '-c:v', 'h264_videotoolbox', '-profile:v', 'main',
                    '-level', '4.0', '-preset', 'ultrafast', '-tune', 'zerolatency',
                    '-pix_fmt', 'yuv420p', '-f', 'flv', output_url,
                ]
            else:
                command = [
                    'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
                    '-pix_fmt', 'bgr24', '-s', f'{width}x{height}', '-r', str(output_fps),
                    '-i', '-', '-c:v', 'libx264', '-preset', 'ultrafast',
                    '-tune', 'zerolatency', '-pix_fmt', 'yuv420p', '-f', 'flv', output_url,
                ]

            ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE)
            with _pose_rtsp_sessions_lock:
                session = _active_pose_rtsp_sessions.get(session_key)
                if session:
                    session['reader'] = reader
                    session['push_process'] = ffmpeg_process

            record = InferenceTask.query.get(record_id)
            record.stream_output_url = output_url
            record.status = 'RUNNING'
            db.session.commit()

            pipeline = PoseRtspStreamPipeline(
                reader=reader,
                ffmpeg_process=ffmpeg_process,
                model=model,
                stop_event=stop_event,
                conf=conf,
                extract_interval=extract_interval,
                output_fps=output_fps,
                log_interval=max(1, output_fps * 6),
            )
            pipeline.run()

            record = InferenceTask.query.get(record_id)
            if record:
                record.status = 'COMPLETED' if not stop_event.is_set() else 'STOPPED'
                db.session.commit()
        except Exception as exc:
            logger.exception('RTSP 姿态推流失败')
            try:
                record = InferenceTask.query.get(record_id)
                if record:
                    record.status = 'FAILED'
                    record.error_message = str(exc)
                    db.session.commit()
            except Exception:
                pass
        finally:
            with _pose_rtsp_sessions_lock:
                _active_pose_rtsp_sessions.pop(session_key, None)
            if reader:
                reader.release()
            if ffmpeg_process:
                self._inference._terminate_ffmpeg_push(ffmpeg_process)
            ctx.pop()
