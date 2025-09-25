import logging
import multiprocessing
import os
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import torch
from flask import current_app
from ultralytics import YOLO

from app.services.minio_service import ModelService
from models import Model, InferenceTask, db


class InferenceService:
    def __init__(self, model_id):
        self.model_id = model_id
        self.model_dir = self._get_model_dir()
        self.minio_bucket = "ai-models"
        self.device = self._select_device()
        self.model_cache = {}  # 模型实例缓存
        self.media_server = self._get_media_server_url()

    def _get_media_server_url(self):
        """从环境变量获取推流服务器地址"""
        push_url = os.getenv('MODEL_AI_PUSH_URL', 'pro.basiclab.top:1935')
        if not push_url.startswith('rtmp://'):
            push_url = f'rtmp://{push_url}'
        return push_url.rstrip('/')

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

    def _load_model(self, model_path: str) -> YOLO:
        """优化模型加载，支持混合精度和缓存"""
        if model_path in self.model_cache:
            return self.model_cache[model_path]

        try:
            # 使用混合精度训练减少内存占用
            model = YOLO(model_path)
            model.to(self.device)

            # 启用半精度推理（GPU环境）
            if 'cuda' in self.device:
                model.model.half()  # FP16推理

            self.model_cache[model_path] = model
            logging.info(f"模型加载成功: {model_path}, 设备: {self.device}")
            return model

        except Exception as e:
            logging.error(f"模型加载失败: {str(e)}")
            raise

    def get_model(self) -> YOLO:
        """获取模型实例，优先本地查找，其次MinIO下载"""
        # 1. 查找本地模型文件
        local_model = self._find_local_model()
        if local_model:
            return self._load_model(local_model)

        # 2. 从MinIO下载模型
        downloaded_model = self._download_model_from_minio()
        if downloaded_model:
            return self._load_model(downloaded_model)

        # 3. 使用默认模型
        default_model = os.path.join('model', 'yolov8n.pt')
        if os.path.exists(default_model):
            return self._load_model(default_model)

        raise Exception("未找到可用的模型文件")

    def _find_local_model(self) -> Optional[str]:
        """在本地目录查找模型文件"""
        model_exts = ('.pt', '.onnx', '.engine')
        if not os.path.exists(self.model_dir):
            return None

        for file in os.listdir(self.model_dir):
            if file.endswith(model_exts):
                model_path = os.path.join(self.model_dir, file)
                if os.path.exists(model_path):
                    return model_path
        return None

    def _download_model_from_minio(self) -> Optional[str]:
        """从MinIO下载模型文件"""
        try:
            model = Model.query.get(self.model_id)
            if not model or not model.minio_model_path:
                return None

            # 确保模型目录存在
            os.makedirs(self.model_dir, exist_ok=True)

            filename = model.minio_model_path.split('/')[-1]
            local_path = os.path.join(self.model_dir, filename)

            # 下载模型文件
            if ModelService.download_from_minio(
                    self.minio_bucket,
                    model.minio_model_path,
                    local_path
            ):
                # 处理压缩文件
                if filename.endswith('.zip'):
                    ModelService.extract_zip(local_path, self.model_dir)
                    os.remove(local_path)
                    return self._find_local_model()
                return local_path

        except Exception as e:
            logging.error(f"MinIO下载失败: {str(e)}")

        return None

    def inference_image(self, image_file, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """优化图片推理，支持批量处理和结果导出"""
        if parameters is None:
            parameters = {}

        record = InferenceTask(
            model_id=self.model_id,
            inference_type='image',
            input_source=image_file.filename,
            status='PROCESSING'
        )
        db.session.add(record)
        db.session.commit()

        try:
            start_time = time.time()
            model = self.get_model()

            # 使用临时文件处理
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_img:
                image_file.save(temp_img.name)
                temp_path = temp_img.name

            # 执行推理
            conf_thres = parameters.get('conf_thres', 0.25)
            iou_thres = parameters.get('iou_thres', 0.45)

            results = model(
                temp_path,
                conf=conf_thres,
                iou=iou_thres,
                verbose=False  # 减少日志输出
            )

            # 处理结果
            result_data = self._process_image_results(results, record.id)

            # 更新任务记录
            record.output_path = result_data['result_url']
            record.status = 'COMPLETED'
            record.processing_time = time.time() - start_time
            record.parameters = parameters
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
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            self._cleanup_memory()

    def _process_image_results(self, results, task_id: str) -> Dict[str, Any]:
        """处理图片推理结果，生成可视化图和检测数据"""
        try:
            # 创建输出目录
            output_dir = Path(current_app.root_path) / 'static' / 'results' / str(task_id)
            output_dir.mkdir(parents=True, exist_ok=True)

            # 保存结果图像
            result_image_path = output_dir / 'result.jpg'
            results[0].save(filename=str(result_image_path))

            # 保存JSON检测结果
            json_path = output_dir / 'detections.json'
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

            # 保存JSON文件
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(detections, f, indent=2, ensure_ascii=False)

            # 生成访问URL
            result_url = f"/static/results/{task_id}/result.jpg"

            return {
                'image_url': result_url,
                'detections': detections,
                'detection_count': len(detections),
                'result_path': str(result_image_path)
            }

        except Exception as e:
            logging.error(f"结果处理失败: {str(e)}")
            raise

    def inference_video(self, video_file, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """多进程视频处理，支持跳帧优化"""
        if parameters is None:
            parameters = {}

        record = InferenceTask(
            model_id=self.model_id,
            inference_type='video',
            input_source=video_file.filename,
            status='PROCESSING'
        )
        db.session.add(record)
        db.session.commit()

        try:
            # 保存视频到临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                video_file.save(temp_video.name)
                video_path = temp_video.name

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
        try:
            model = self.get_model()
            start_time = time.time()

            # 创建临时输出目录
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, 'processed.mp4')

            # 视频处理
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_size = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )

            # 视频编码器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)

            # 跳帧处理优化
            frame_skip = parameters.get('frame_skip', 3)
            frame_count = 0
            processed_frames = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 跳帧策略
                if frame_count % frame_skip == 0:
                    results = model(frame, verbose=False)
                    annotated_frame = results[0].plot()
                    out.write(annotated_frame)
                    processed_frames += 1
                else:
                    out.write(frame)

                frame_count += 1

            # 释放资源
            cap.release()
            out.release()

            # 上传结果
            result_url = ModelService.upload_to_minio(
                self.minio_bucket,
                f"inference/{self.model_id}/{datetime.now().strftime('%Y%m%d')}/processed.mp4",
                output_path
            )

            # 更新数据库
            with current_app.app_context():
                record = InferenceTask.query.get(record_id)
                record.output_path = result_url
                record.status = 'COMPLETED'
                record.processing_time = time.time() - start_time
                db.session.commit()

        except Exception as e:
            logging.error(f"视频处理失败: {str(e)}")
            with current_app.app_context():
                record = InferenceTask.query.get(record_id)
                record.status = 'FAILED'
                record.error_message = str(e)
                db.session.commit()
        finally:
            # 清理资源
            self._cleanup_resources(video_path, temp_dir)

    def inference_rtsp(self, rtsp_url: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """RTSP流实时处理，支持低延迟推流"""
        if parameters is None:
            parameters = {}

        record = InferenceTask(
            model_id=self.model_id,
            inference_type='rtsp',
            input_source=rtsp_url,
            status='PROCESSING'
        )
        db.session.add(record)
        db.session.commit()

        try:
            # 生成推流地址
            stream_name = f"stream_{self.model_id}_{int(time.time())}"
            output_url = f"{self.media_server}/live/{stream_name}"

            # 启动流处理线程
            thread = threading.Thread(
                target=self._process_rtsp_stream,
                args=(rtsp_url, output_url, record.id, parameters),
                daemon=True
            )
            thread.start()

            return {
                'stream_url': output_url,
                'record_id': record.id,
                'status': 'streaming_started'
            }

        except Exception as e:
            record.status = 'FAILED'
            record.error_message = str(e)
            db.session.commit()
            logging.error(f"RTSP流启动失败: {str(e)}")
            raise

    def _process_rtsp_stream(self, rtsp_url: str, output_url: str, record_id: int, parameters: Dict[str, Any]):
        """RTSP流处理线程"""
        cap = None
        ffmpeg_process = None

        try:
            model = self.get_model()

            # RTSP流配置
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲区

            # 获取视频参数
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 25

            # FFmpeg推流命令
            command = [
                'ffmpeg',
                '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', f'{width}x{height}',
                '-r', str(fps),
                '-i', '-',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-f', 'flv',
                output_url
            ]

            ffmpeg_process = subprocess.Popen(command, stdin=subprocess.PIPE)

            # 更新状态
            with current_app.app_context():
                record = InferenceTask.query.get(record_id)
                record.stream_output_url = output_url
                record.status = 'RUNNING'
                db.session.commit()

            # 流处理循环
            frame_skip = parameters.get('frame_skip', 2)
            frame_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 跳帧处理
                if frame_count % frame_skip == 0:
                    results = model(frame, verbose=False)
                    processed_frame = results[0].plot()
                    ffmpeg_process.stdin.write(processed_frame.tobytes())
                else:
                    ffmpeg_process.stdin.write(frame.tobytes())

                frame_count += 1

            # 流结束
            with current_app.app_context():
                record = InferenceTask.query.get(record_id)
                record.status = 'COMPLETED'
                db.session.commit()

        except Exception as e:
            logging.error(f"RTSP处理失败: {str(e)}")
            with current_app.app_context():
                record = InferenceTask.query.get(record_id)
                record.status = 'FAILED'
                record.error_message = str(e)
                db.session.commit()
        finally:
            # 清理资源
            if cap and cap.isOpened():
                cap.release()
            if ffmpeg_process:
                ffmpeg_process.stdin.close()
                ffmpeg_process.terminate()
            self._cleanup_memory()

    def _cleanup_memory(self):
        """清理内存和显存资源"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def _cleanup_resources(self, file_path: str, temp_dir: str):
        """清理临时资源"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
            if os.path.exists(temp_dir):
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
