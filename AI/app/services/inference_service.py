import multiprocessing
import os
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime, time

import cv2
import torch
from flask import current_app
from ultralytics import YOLO
from werkzeug.utils import secure_filename

from app.services.model_service import ModelService
from models import Model, InferenceRecord, db


class InferenceService:
    def __init__(self, model_id):
        self.model_id = model_id
        self.model_dir = ModelService.get_model_dir(model_id)
        self.minio_bucket = "ai-models"
        self.device = self._select_device()

        # 多进程共享资源
        self.frame_queue = multiprocessing.Queue(maxsize=10)
        self.result_queue = multiprocessing.Queue(maxsize=10)
        self.stop_event = multiprocessing.Event()

        # 模型实例缓存（避免重复加载）
        self.model_cache = {}

    def _select_device(self):
        """自动选择最优计算设备"""
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        return 'cpu'

    def _load_model(self, model_path):
        """加载模型并启用半精度"""
        if model_path in self.model_cache:
            return self.model_cache[model_path]

        model = YOLO(model_path)
        model.to(self.device)

        # 启用半精度推理（GPU环境）
        if 'cuda' in self.device:
            model.model.half()

        self.model_cache[model_path] = model
        return model

    def _download_model_if_missing(self):
        """检查并下载缺失的模型"""
        model_files = ['best.pt', 'best.onnx']
        model_path = None

        # 检查本地模型文件
        for file in model_files:
            candidate_path = os.path.join(self.model_dir, file)
            if os.path.exists(candidate_path):
                model_path = candidate_path
                break

        # 从Minio下载缺失模型
        if not model_path:
            model = Model.query.get(self.model_id)
            if model.minio_model_path:
                object_name = model.minio_model_path.split('/')[-1]
                local_path = os.path.join(self.model_dir, object_name)

                if ModelService.download_from_minio(
                        self.minio_bucket,
                        model.minio_model_path,
                        local_path
                ):
                    # 解压ZIP格式模型
                    if local_path.endswith('.zip'):
                        ModelService.extract_zip(local_path, self.model_dir)
                        os.remove(local_path)
                    model_path = self._find_model_file()

        return model_path

    def _find_model_file(self):
        """在目录中查找模型文件"""
        for file in os.listdir(self.model_dir):
            if file.endswith(('.pt', '.onnx')):
                return os.path.join(self.model_dir, file)
        return None

    def load_model(self, model_type, system_model=None, model_file=None):
        """加载模型（带缓存和自动下载）"""
        model_path = None

        if model_type == 'system':
            if not system_model:
                raise ValueError('未指定系统模型')
            model_path = os.path.join(self.model_dir, 'train', 'weights', system_model)
        elif model_type == 'upload':
            if not model_file or not model_file.filename:
                raise ValueError('未提供上传的模型文件')
            model_path = self._save_uploaded_model(model_file)
        else:
            raise ValueError(f'不支持的模型类型: {model_type}')

        # 检查模型是否存在
        if not os.path.exists(model_path):
            model_path = self._download_model_if_missing()
            if not model_path:
                raise FileNotFoundError(f"模型文件不存在: {model_path}")

        return self._load_model(model_path)

    # === 异步处理框架 ===
    def _start_processing_thread(self, process_func):
        """启动后台处理线程"""
        processor = threading.Thread(
            target=process_func,
            daemon=True
        )
        processor.start()
        return processor

    # === 图片推理优化 ===
    def inference_image(self, model, image_file):
        """优化后的图片推理（带显存管理）"""
        record = InferenceRecord(
            model_id=self.model_id,
            inference_type='image',
            input_source=image_file.filename,
            status='PROCESSING'
        )
        db.session.add(record)
        db.session.commit()

        try:
            start_time = time.time()

            # 使用临时文件避免内存累积
            with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_img:
                image_file.save(temp_img.name)
                results = model(temp_img.name)

            # 处理结果并上传
            result_url = self._process_and_upload(results, image_file.filename)

            # 更新推理记录
            record.output_path = result_url
            record.status = 'COMPLETED'
            record.processing_time = time.time() - start_time
            db.session.commit()

            return {'image_url': result_url}
        except Exception as e:
            record.status = 'FAILED'
            record.error_message = str(e)
            db.session.commit()
            raise

    # === 视频推理优化 ===
    def inference_video(self, model, video_file):
        """多进程视频处理框架"""
        record = InferenceRecord(
            model_id=self.model_id,
            inference_type='video',
            input_source=video_file.filename,
            status='PROCESSING'
        )
        db.session.add(record)
        db.session.commit()

        try:
            # 保存视频到临时文件
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            video_file.save(temp_video.name)
            temp_video.close()

            # 启动处理进程
            processor = multiprocessing.Process(
                target=self._video_processor,
                args=(model, temp_video.name, record.id)
            )
            processor.start()

            return {
                'status': 'processing',
                'record_id': record.id,
                'message': '视频处理已启动'
            }
        except Exception as e:
            record.status = 'FAILED'
            record.error_message = str(e)
            db.session.commit()
            raise

    def _video_processor(self, model, video_path, record_id):
        """视频处理子进程（避免显存泄漏）"""
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            output_path = os.path.join(temp_dir, 'processed.mp4')

            # 使用OpenCV处理视频
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_size = (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )

            # 创建输出视频
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, frame_size)

            # 帧处理循环
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 跳帧策略（每3帧处理1次）
                if frame_count % 3 == 0:
                    results = model(frame)
                    frame = results[0].plot()

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

            # 更新数据库记录
            with current_app.app_context():
                record = InferenceRecord.query.get(record_id)
                record.output_path = result_url
                record.status = 'COMPLETED'
                record.processing_time = time.time() - record.start_time.timestamp()
                db.session.commit()

        finally:
            # 清理资源
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.unlink(video_path)

    # === RTSP流处理优化 ===
    def inference_rtsp(self, model, rtsp_url):
        """RTSP流异步处理（FFmpeg推流）"""
        record = InferenceRecord(
            model_id=self.model_id,
            inference_type='rtsp',
            input_source=rtsp_url,
            status='PROCESSING'
        )
        db.session.add(record)
        db.session.commit()

        try:
            # 生成唯一推流地址
            output_url = f"rtmp://media-server/live/stream_{self.model_id}_{record.id}"

            # 启动异步处理线程
            threading.Thread(
                target=self._rtsp_processor,
                args=(model, rtsp_url, output_url, record.id),
                daemon=True
            ).start()

            return {
                'stream_url': output_url,
                'record_id': record.id
            }
        except Exception as e:
            record.status = 'FAILED'
            record.error_message = str(e)
            db.session.commit()
            raise

    def _rtsp_processor(self, model, input_url, output_url, record_id):
        """RTSP处理线程（FFmpeg管道）"""
        try:
            # FFmpeg处理管道
            command = [
                'ffmpeg',
                '-i', input_url,
                '-vf', f"yolov8={model}",
                '-c:v', 'libx264',
                '-f', 'flv',
                output_url
            ]

            # 启动FFmpeg进程
            process = subprocess.Popen(command, stderr=subprocess.PIPE)

            # 监控进程状态
            while process.poll() is None:
                time.sleep(1)

            # 更新记录状态
            with current_app.app_context():
                record = InferenceRecord.query.get(record_id)
                record.status = 'COMPLETED'
                record.stream_output_url = output_url
                db.session.commit()

        except Exception as e:
            with current_app.app_context():
                record = InferenceRecord.query.get(record_id)
                record.status = 'FAILED'
                record.error_message = str(e)
                db.session.commit()

    # === 辅助方法 ===
    def _process_and_upload(self, results, filename):
        """处理结果并上传到Minio"""
        # 保存结果图像
        temp_dir = tempfile.mkdtemp()
        result_path = os.path.join(temp_dir, f'result_{filename}')
        results[0].save(filename=result_path)

        # 上传到Minio
        minio_path = f"inference/{self.model_id}/{datetime.now().strftime('%Y%m%d')}/{filename}"
        ModelService.upload_to_minio(self.minio_bucket, minio_path, result_path)

        # 清理临时文件
        shutil.rmtree(temp_dir)

        return f"{current_app.config['MINIO_PUBLIC_URL']}/{minio_path}"

    def _save_uploaded_model(self, model_file):
        """保存上传的模型文件"""
        filename = secure_filename(model_file.filename)
        model_path = os.path.join(self.model_dir, filename)
        model_file.save(model_path)
        return model_path
