import os
import shutil
import tempfile
import traceback
from datetime import datetime

import torch
from oss2 import Auth, Bucket
from ultralytics import YOLO

from .exception import DatasetDownloadError, InvalidDatasetError, TrainingError, ModelNotFoundError, ExportError
from model import db, Model, ExportRecord

# OSS配置
OSS_ACCESS_KEY_ID = 'your_access_key_id'
OSS_ACCESS_KEY_SECRET = 'your_access_key_secret'
OSS_ENDPOINT = 'your_oss_endpoint'
OSS_BUCKET_NAME = 'your_bucket_name'

# 全局变量用于存储训练状态和训练进程
training_status = {}
training_processes = {}


def download_dataset_from_oss(model_id, oss_dataset_path):
    """从OSS下载数据集到临时目录"""
    temp_dir = tempfile.mkdtemp(prefix=f'dataset_{model_id}_')
    try:
        # 初始化OSS客户端
        auth = Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        bucket = Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

        # 列出OSS上的所有文件
        for obj in bucket.list_objects(oss_dataset_path).object_list:
            # 构建本地文件路径
            relative_path = os.path.relpath(obj.key, oss_dataset_path)
            local_path = os.path.join(temp_dir, relative_path)

            # 确保目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 下载文件
            bucket.get_object_to_file(obj.key, local_path)

        return temp_dir

    except Exception as e:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise DatasetDownloadError(f"从OSS下载数据集失败: {str(e)}")


def train_model(model_id, epochs=20, model_arch='yolov8n.pt', img_size=640, batch_size=16, use_gpu=True,
                oss_dataset_path=None):
    """训练YOLO模型，数据源来自OSS"""
    temp_dir = None
    try:
        # 从OSS下载数据集
        if not oss_dataset_path:
            raise InvalidDatasetError("OSS数据集路径未提供")

        temp_dir = download_dataset_from_oss(model_id, oss_dataset_path)

        # 初始化训练状态
        training_status[model_id] = {
            'status': 'preparing',
            'message': '准备训练数据...',
            'progress': 0,
            'log': ''
        }

        # 检查数据集配置文件
        data_yaml_path = os.path.join(temp_dir, 'data.yaml')
        if not os.path.exists(data_yaml_path):
            raise InvalidDatasetError("数据集配置文件中缺少data.yaml文件")

        # 加载预训练模型
        model = YOLO(model_arch)
        training_processes[model_id] = model

        # 训练模型
        results = model.train(
            data=data_yaml_path,
            epochs=epochs,
            imgsz=img_size,
            batch=batch_size,
            project=temp_dir,
            name='train_results',
            exist_ok=True,
            device=0 if use_gpu and torch.cuda.is_available() else 'cpu'
        )

        # 保存最佳模型
        best_model_path = os.path.join(temp_dir, 'train_results', 'weights', 'best.pt')
        if os.path.exists(best_model_path):
            model_save_dir = os.path.join('static/models', str(model_id), 'train', 'weights')
            os.makedirs(model_save_dir, exist_ok=True)
            shutil.copy(best_model_path, os.path.join(model_save_dir, 'best.pt'))

            project = Model.query.get(model_id)
            project.model_path = os.path.join('models', str(model_id), 'train', 'weights', 'best.pt')
            project.last_trained = datetime.now()
            db.session.commit()

        training_status[model_id].update({
            'status': 'completed',
            'message': '模型训练完成并已保存',
            'progress': 100
        })

    except Exception as e:
        training_status[model_id].update({
            'status': 'error',
            'message': f'训练出错: {str(e)}',
            'progress': 0,
            'error_details': str(e),
            'traceback': traceback.format_exc()
        })
        raise TrainingError(str(e))
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        if model_id in training_processes:
            del training_processes[model_id]


def export_model(model_id, format):
    """导出训练好的模型到指定格式"""
    try:
        # 检查模型文件
        model_path = os.path.join('static/models', str(model_id), 'train', 'weights', 'best.pt')
        if not os.path.exists(model_path):
            raise ModelNotFoundError('模型文件不存在，请先训练模型')

        # 准备导出目录
        export_dir = os.path.join('static/models', str(model_id), 'export')
        os.makedirs(export_dir, exist_ok=True)

        # 导出模型
        model = YOLO(model_path)
        export_filepath = os.path.join(export_dir, f'model.{format}')

        if format == 'onnx':
            model.export(format='onnx', project=export_dir, name='model')
        elif format == 'torchscript':
            model.export(format='torchscript', project=export_dir, name='model')
        else:
            raise ExportError(f'不支持的导出格式: {format}')

        # 保存导出记录
        export_record = ExportRecord(
            model_id=model_id,
            format=format,
            path=export_filepath
        )
        db.session.add(export_record)
        db.session.commit()

        return export_filepath

    except Exception as e:
        raise ExportError(str(e))


def get_training_status(model_id):
    """获取训练状态"""
    return training_status.get(model_id, {
        'status': 'idle',
        'message': '等待开始',
        'progress': 0
    })


def stop_training(model_id):
    """停止训练"""
    if model_id in training_status:
        training_status[model_id]['stop_requested'] = True
        training_status[model_id]['status'] = 'stopping'
        training_status[model_id]['message'] = '正在停止训练...'
