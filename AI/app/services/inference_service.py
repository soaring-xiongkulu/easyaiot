"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import multiprocessing
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np
import torch
from flask import current_app
from ultralytics import YOLO

from app.services.minio_service import ModelService
from db_models import Model, InferenceTask, db
from app.utils.onnx_inference import ONNXInference


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
           - AI目录下的默认模型文件（yolov8n.pt或yolo11n.pt）
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
            
            # 如果用户模型不存在，记录警告但继续尝试默认模型
            logging.warning(f"用户模型 ID {self.model_id} 不存在，将尝试使用默认模型")

        # 3. 使用默认模型（当 model_id 为 None 或 <= 0，或用户模型不存在时）
        # 3.1 查找AI目录下的默认模型文件（yolov8n.pt或yolo11n.pt）
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

    def _find_default_models(self) -> list:
        """查找AI目录下的默认模型文件（yolo11n.pt或yolov8n.pt）
        优先级：yolo11n.pt > yolov8n.pt
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
            
            # 查找模型文件，优先yolo11n.pt，其次yolov8n.pt
            for ai_dir in possible_ai_dirs:
                for model_name in ['yolo11n.pt', 'yolov8n.pt']:
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

            # 获取模型路径：优先使用onnx_model_path，其次使用model_path，最后从TrainTask获取minio_model_path
            minio_path = None
            if model.onnx_model_path:
                minio_path = model.onnx_model_path
            elif model.model_path:
                minio_path = model.model_path
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

            # 获取模型路径：优先使用onnx_model_path，其次使用model_path，最后从TrainTask获取minio_model_path
            minio_path = None
            if model.onnx_model_path:
                minio_path = model.onnx_model_path
            elif model.model_path:
                minio_path = model.model_path
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
                    logging.warning(f"模型 ID {self.model_id} 不存在，将使用默认模型")
                    actual_model_id = None
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
            conf_thres = parameters.get('conf_thres', 0.25)
            iou_thres = parameters.get('iou_thres', 0.45)
            
            if is_onnx:
                # 使用新的ONNX推理模块
                output_image, detections = model.detect(
                    temp_path,
                    conf_threshold=conf_thres,
                    iou_threshold=iou_thres,
                    draw=True
                )
                # 将ONNX结果转换为与YOLO结果兼容的格式
                # 创建一个模拟的Results对象
                class ONNXResults:
                    def __init__(self, image, detections):
                        self.image = image
                        self.detections = detections
                
                results = [ONNXResults(output_image, detections)]
            else:
                # 使用YOLO模型推理
                inference_kwargs = {
                    'conf': conf_thres,
                    'iou': iou_thres,
                    'verbose': False
                }
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
                # YOLO推理结果
                # 保存结果图像到临时文件
                results[0].save(filename=result_image_path)

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
                    logging.warning(f"模型 ID {self.model_id} 不存在，将使用默认模型")
                    actual_model_id = None
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
                conf_thres = parameters.get('conf_thres', 0.25) if parameters else 0.25
                iou_thres = parameters.get('iou_thres', 0.45) if parameters else 0.45
                
                if is_onnx:
                    logging.info(f"视频推理：使用ONNX模型")
                else:
                    inference_kwargs = {
                        'conf': conf_thres,
                        'iou': iou_thres,
                        'verbose': False
                    }
                
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
                            # 使用新的ONNX推理模块
                            annotated_frame, _ = model.detect(
                                frame,
                                conf_threshold=conf_thres,
                                iou_threshold=iou_thres,
                                draw=True
                            )
                            # 将标注后的帧调整回原始尺寸
                            annotated_frame = cv2.resize(annotated_frame, frame_size, interpolation=cv2.INTER_LINEAR)
                        else:
                            # 使用YOLO模型推理
                            results = model(frame, **inference_kwargs)
                            annotated_frame = results[0].plot()
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
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',  # 覆盖输出文件
                    '-i', temp_output_path,  # 输入文件
                    '-c:v', 'libx264',  # 使用H.264视频编码
                    '-preset', 'medium',  # 编码速度和质量平衡
                    '-crf', '23',  # 质量控制（18-28，23是默认值）
                    '-pix_fmt', 'yuv420p',  # 像素格式，确保浏览器兼容
                    '-movflags', '+faststart',  # 优化网络播放（将moov atom移到文件开头）
                    '-c:a', 'aac',  # 音频编码（如果有音频轨道）
                    '-b:a', '128k',  # 音频比特率
                    output_path  # 输出文件
                ]
                
                try:
                    result = subprocess.run(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=300  # 5分钟超时
                    )
                    if result.returncode != 0:
                        error_msg = result.stderr.decode('utf-8', errors='ignore')
                        logging.warning(f"FFmpeg转换失败，使用原始视频: {error_msg}")
                        # 如果FFmpeg失败，使用原始视频（可能浏览器不支持，但至少不会报错）
                        if os.path.exists(temp_output_path):
                            shutil.copy2(temp_output_path, output_path)
                    else:
                        logging.info(f"FFmpeg转换成功: {output_path}")
                        # 删除临时文件
                        if os.path.exists(temp_output_path):
                            os.unlink(temp_output_path)
                except subprocess.TimeoutExpired:
                    logging.error("FFmpeg转换超时，使用原始视频")
                    if os.path.exists(temp_output_path):
                        shutil.copy2(temp_output_path, output_path)
                except FileNotFoundError:
                    logging.warning("FFmpeg未找到，使用原始视频（可能浏览器不支持mp4v编码）")
                    if os.path.exists(temp_output_path):
                        shutil.copy2(temp_output_path, output_path)
                except Exception as e:
                    logging.error(f"FFmpeg转换出错: {str(e)}，使用原始视频")
                    if os.path.exists(temp_output_path):
                        shutil.copy2(temp_output_path, output_path)

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
                    result_url = None
                    logging.error(f"视频结果上传到MinIO失败: {object_key}")

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
        """RTSP流实时处理，支持低延迟推流"""
        if parameters is None:
            parameters = {}

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
                    logging.warning(f"模型 ID {self.model_id} 不存在，将使用默认模型")
                    actual_model_id = None
            else:
                logging.info(f"使用默认模型（model_id={self.model_id}）")
                actual_model_id = None

            record = InferenceTask(
                model_id=actual_model_id,
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
            
            # 判断是否为ONNX模型（通过检查model是否为ONNXInference实例）
            is_onnx = isinstance(model, ONNXInference)
            
            # 构建推理参数
            conf_thres = parameters.get('conf_thres', 0.25) if parameters else 0.25
            iou_thres = parameters.get('iou_thres', 0.45) if parameters else 0.45
            
            if is_onnx:
                logging.info(f"RTSP流推理：使用ONNX模型")
            else:
                inference_kwargs = {
                    'conf': conf_thres,
                    'iou': iou_thres,
                    'verbose': False
                }

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
                    if is_onnx:
                        # 使用新的ONNX推理模块
                        processed_frame, _ = model.detect(
                            frame,
                            conf_threshold=conf_thres,
                            iou_threshold=iou_thres,
                            draw=True
                        )
                        # 将标注后的帧调整回原始尺寸
                        processed_frame = cv2.resize(processed_frame, (width, height), interpolation=cv2.INTER_LINEAR)
                    else:
                        # 使用YOLO模型推理
                        results = model(frame, **inference_kwargs)
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
