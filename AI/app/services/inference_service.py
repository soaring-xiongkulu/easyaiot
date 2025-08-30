import logging
import multiprocessing
import os
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime

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
        self.model_dir = self._get_model_dir()
        self.minio_bucket = "ai-models"
        self.device = self._select_device()
        self.model_cache = {}  # 模型实例缓存
        self.media_server = self._get_media_server_url()  # 从环境变量获取推流服务器地址

    def _get_media_server_url(self):
        """从环境变量获取推流服务器地址"""
        push_url = os.getenv('MODEL_AI_PUSH_URL', 'pro.basiclab.top:1935')
        # 确保URL格式正确
        if not push_url.startswith('rtmp://'):
            push_url = f'rtmp://{push_url}'
        return push_url.rstrip('/')  # 移除末尾斜杠

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

    def _find_local_model(self):
        """在本地目录查找模型文件"""
        model_exts = ('.pt', '.onnx', '.engine')
        for file in os.listdir(self.model_dir):
            if file.endswith(model_exts):
                return os.path.join(self.model_dir, file)
        return None

    def _download_model_from_minio(self):
        """从Minio下载模型文件"""
        model = Model.query.get(self.model_id)
        if not model or not model.minio_model_path:
            return None

        # 下载模型文件
        filename = model.minio_model_path.split('/')[-1]
        local_path = os.path.join(self.model_dir, filename)

        if ModelService.download_from_minio(
                self.minio_bucket,
                model.minio_model_path,
                local_path
        ):
            # 处理压缩文件
            if filename.endswith('.zip'):
                ModelService.extract_zip(local_path, self.model_dir)
                os.remove(local_path)
                return self._find_local_model()  # 返回解压后的模型文件
            return local_path
        return None

    def load_model(self, model_type, system_model, model_file=None):
        """
        加载模型
        :param model_type: 模型类型
        :param system_model: 系统模型标识
        :param model_file: 上传的模型文件（可选）
        """
        try:
            if model_file:
                # 处理上传的模型文件
                model_path = self.save_uploaded_model(model_file)
                self.model = YOLO(model_path)
            else:
                # 处理模型路径 - 使用相对于根路径的model/yolov8n.pt
                if not self.model_id:
                    # 使用默认模型
                    model_arch = os.path.join('model', 'yolov8n.pt')
                    if not os.path.exists(model_arch):
                        raise Exception(f"默认模型不存在于路径: {model_arch}")
                    self.model = YOLO(model_arch)
                else:
                    # 从数据库获取模型路径
                    model_record = Model.query.get(self.model_id)
                    if not model_record or not model_record.model_path:
                        raise Exception("未找到对应的模型记录或模型路径")

                    model_path = model_record.model_path
                    if not os.path.exists(model_path):
                        # 尝试从MinIO下载模型
                        if not self.download_model_from_minio(model_record):
                            raise Exception(f"模型文件不存在且无法从MinIO下载: {model_path}")

                    self.model = YOLO(model_path)

            return self.model

        except Exception as e:
            logging.error(f"加载模型失败: {str(e)}")
            raise

    def download_model_from_minio(self, model_record):
        """
        从MinIO下载模型文件
        """
        try:
            if hasattr(model_record, 'minio_path') and model_record.minio_path:
                local_path = model_record.model_path
                os.makedirs(os.path.dirname(local_path), exist_ok=True)

                # 使用MinIO客户端下载文件
                minio_client = ModelService.get_minio_client()
                minio_client.fget_object(
                    'models',  # 存储桶名称
                    model_record.minio_path,
                    local_path
                )
                return True
        except Exception as e:
            logging.error(f"从MinIO下载模型失败: {str(e)}")

        return False

    def save_uploaded_model(self, model_file):
        """
        保存上传的模型文件
        """
        # 实现文件保存逻辑
        upload_dir = 'uploads/models'
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(model_file.filename)
        filepath = os.path.join(upload_dir, filename)
        model_file.save(filepath)

        return filepath

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
        finally:
            # 显式释放显存
            if 'cuda' in self.device:
                torch.cuda.empty_cache()

    # === 视频推理优化 ===
    def inference_video(self, model, video_file):
        """多进程视频处理框架（避免显存泄漏）"""
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

            # 启动处理进程（多进程隔离显存）
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
        """视频处理子进程（显存自动回收）"""
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

        except Exception as e:
            with current_app.app_context():
                record = InferenceRecord.query.get(record_id)
                record.status = 'FAILED'
                record.error_message = str(e)
                db.session.commit()
        finally:
            # 清理资源
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.unlink(video_path)
            # 显式释放显存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

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
            # 生成唯一推流地址（使用环境变量配置的媒体服务器）
            stream_name = f"stream_{self.model_id}_{int(time.time())}"
            output_url = f"{self.media_server}/live/{stream_name}"

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
        """RTSP处理线程（OpenCV+FFmpeg管道）"""
        cap = None
        process = None
        try:
            # 强制使用TCP传输避免丢包
            cap = cv2.VideoCapture(input_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_RTSP_TRANSPORT, cv2.CAP_RTSP_TRANSPORT_TCP)  # TCP协议
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲区大小降低延迟

            # 获取视频参数（分辨率、帧率）
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30  # 默认帧率

            # 构建FFmpeg推流命令（低延迟优化）
            command = [
                'ffmpeg',
                '-y',
                '-f', 'rawvideo',  # 输入原始帧
                '-vcodec', 'rawvideo',  # 原始视频编码
                '-pix_fmt', 'bgr24',  # OpenCV帧格式
                '-s', f'{width}x{height}',  # 分辨率
                '-r', str(fps),  # 帧率
                '-i', '-',  # 从标准输入读取
                '-c:v', 'libx264',  # H.264编码
                '-preset', 'ultrafast',  # 低延迟预设
                '-tune', 'zerolatency',  # 零延迟优化
                '-f', 'flv',  # FLV输出格式
                '-rtsp_transport', 'tcp',  # 强制TCP传输
                output_url
            ]

            # 启动FFmpeg进程
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 更新记录状态为运行中
            with current_app.app_context():
                record = InferenceRecord.query.get(record_id)
                record.stream_output_url = output_url
                record.status = 'RUNNING'
                db.session.commit()

            # 逐帧处理并推流
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 跳帧策略（每2帧处理1次）
                if frame_count % 2 == 0:
                    # YOLOv8推理
                    results = model(frame)
                    frame = results[0].plot()  # 绘制检测框

                # 将帧写入FFmpeg管道
                process.stdin.write(frame.tobytes())
                frame_count += 1

            # 流正常结束时标记为完成
            with current_app.app_context():
                record = InferenceRecord.query.get(record_id)
                record.status = 'COMPLETED'
                record.processing_time = time.time() - record.start_time.timestamp()
                db.session.commit()

        except Exception as e:
            # 异常时更新状态
            with current_app.app_context():
                record = InferenceRecord.query.get(record_id)
                record.status = 'FAILED'
                record.error_message = str(e)
                db.session.commit()
        finally:
            # 清理资源
            if cap and cap.isOpened():
                cap.release()
            if process:
                process.stdin.close()
                process.terminate()
            # 显式释放显存
            if 'cuda' in self.device:
                torch.cuda.empty_cache()

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
