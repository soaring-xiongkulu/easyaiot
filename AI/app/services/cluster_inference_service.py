"""
集群推理服务
通过Nacos发现services实例并实现集群推理
"""
import os
import logging
import requests
import tempfile
from typing import Dict, Any, Optional
from flask import request

from app.utils.nacos_service_discovery import get_model_service_url

logger = logging.getLogger(__name__)


class ClusterInferenceService:
    """集群推理服务类"""
    
    @staticmethod
    def get_model_format(model_path: str) -> str:
        """推断模型格式"""
        if not model_path:
            return 'pytorch'
        
        model_path_lower = model_path.lower()
        if model_path_lower.endswith('.onnx') or 'onnx' in model_path_lower:
            return 'onnx'
        elif model_path_lower.endswith(('.pt', '.pth')):
            return 'pytorch'
        elif 'openvino' in model_path_lower:
            return 'openvino'
        elif 'tensorrt' in model_path_lower:
            return 'tensorrt'
        else:
            return 'pytorch'  # 默认
    
    @staticmethod
    def inference_via_cluster(
        model_id: int,
        model_format: str,
        model_version: str,
        file_path: Optional[str] = None,
        file_obj=None,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        通过集群services实例进行推理
        
        Args:
            model_id: 模型ID
            model_format: 模型格式 (onnx, pytorch等)
            model_version: 模型版本
            file_path: 文件路径（可选）
            file_obj: 文件对象（可选）
            parameters: 推理参数
        
        Returns:
            推理结果
        """
        # 从Nacos获取services实例
        service_url = get_model_service_url(model_id, model_format, model_version)
        
        if not service_url:
            raise Exception(f"未找到模型服务实例: model_{model_id}_{model_format}_{model_version}")
        
        logger.info(f"通过Nacos发现services实例: {service_url}，使用集群推理")
        
        # 准备文件上传
        files = {}
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                files['file'] = (os.path.basename(file_path), f, 'application/octet-stream')
        elif file_obj:
            # 重置文件指针
            file_obj.seek(0)
            files['file'] = (file_obj.filename, file_obj.stream, file_obj.content_type)
        
        if not files:
            raise Exception("未提供文件")
        
        # 准备参数
        params = parameters or {}
        
        try:
            # 调用services实例的推理接口
            response = requests.post(
                f"{service_url}/inference",
                files=files,
                data=params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                raise Exception(f"调用services实例失败: {response.status_code}, {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"调用services实例异常: {str(e)}")
        finally:
            # 关闭文件
            if 'file' in files:
                files['file'][1].close()

