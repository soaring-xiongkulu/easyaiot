"""
算法模型服务管理
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional

from models import db, AlgorithmModelService, RegionModelService, SnapTask, DetectionRegion

logger = logging.getLogger(__name__)


def create_task_algorithm_service(task_id: int, service_name: str, service_url: str,
                                  service_type: Optional[str] = None, model_id: Optional[int] = None,
                                  threshold: Optional[float] = None, request_method: str = 'POST',
                                  request_headers: Optional[Dict] = None, request_body_template: Optional[Dict] = None,
                                  timeout: int = 30, is_enabled: bool = True, sort_order: int = 0) -> AlgorithmModelService:
    """创建任务级别的算法模型服务配置"""
    try:
        task = SnapTask.query.get_or_404(task_id)
        
        headers_json = json.dumps(request_headers) if request_headers else None
        body_template_json = json.dumps(request_body_template) if request_body_template else None
        
        service = AlgorithmModelService(
            task_id=task_id,
            service_name=service_name,
            service_url=service_url,
            service_type=service_type,
            model_id=model_id,
            threshold=threshold,
            request_method=request_method,
            request_headers=headers_json,
            request_body_template=body_template_json,
            timeout=timeout,
            is_enabled=is_enabled,
            sort_order=sort_order
        )
        
        db.session.add(service)
        db.session.commit()
        
        logger.info(f"创建任务算法服务配置成功: task_id={task_id}, service_name={service_name}")
        return service
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建任务算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建任务算法服务配置失败: {str(e)}")


def update_task_algorithm_service(service_id: int, **kwargs) -> AlgorithmModelService:
    """更新任务级别的算法模型服务配置"""
    try:
        service = AlgorithmModelService.query.get_or_404(service_id)
        
        updatable_fields = [
            'service_name', 'service_url', 'service_type', 'model_id',
            'threshold', 'request_method', 'timeout', 'is_enabled', 'sort_order'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(service, field, kwargs[field])
        
        if 'request_headers' in kwargs:
            service.request_headers = json.dumps(kwargs['request_headers']) if kwargs['request_headers'] else None
        
        if 'request_body_template' in kwargs:
            service.request_body_template = json.dumps(kwargs['request_body_template']) if kwargs['request_body_template'] else None
        
        db.session.commit()
        logger.info(f"更新任务算法服务配置成功: service_id={service_id}")
        return service
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新任务算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新任务算法服务配置失败: {str(e)}")


def delete_task_algorithm_service(service_id: int):
    """删除任务级别的算法模型服务配置"""
    try:
        service = AlgorithmModelService.query.get_or_404(service_id)
        db.session.delete(service)
        db.session.commit()
        logger.info(f"删除任务算法服务配置成功: service_id={service_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除任务算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除任务算法服务配置失败: {str(e)}")


def get_task_algorithm_services(task_id: int) -> List[AlgorithmModelService]:
    """获取任务的所有算法模型服务配置"""
    try:
        services = AlgorithmModelService.query.filter_by(task_id=task_id).order_by(
            AlgorithmModelService.sort_order, AlgorithmModelService.id
        ).all()
        return services
    except Exception as e:
        logger.error(f"获取任务算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取任务算法服务配置失败: {str(e)}")


def create_region_algorithm_service(region_id: int, service_name: str, service_url: str,
                                    service_type: Optional[str] = None, model_id: Optional[int] = None,
                                    threshold: Optional[float] = None, request_method: str = 'POST',
                                    request_headers: Optional[Dict] = None, request_body_template: Optional[Dict] = None,
                                    timeout: int = 30, is_enabled: bool = True, sort_order: int = 0) -> RegionModelService:
    """创建区域级别的算法模型服务配置"""
    try:
        region = DetectionRegion.query.get_or_404(region_id)
        
        headers_json = json.dumps(request_headers) if request_headers else None
        body_template_json = json.dumps(request_body_template) if request_body_template else None
        
        service = RegionModelService(
            region_id=region_id,
            service_name=service_name,
            service_url=service_url,
            service_type=service_type,
            model_id=model_id,
            threshold=threshold,
            request_method=request_method,
            request_headers=headers_json,
            request_body_template=body_template_json,
            timeout=timeout,
            is_enabled=is_enabled,
            sort_order=sort_order
        )
        
        db.session.add(service)
        db.session.commit()
        
        logger.info(f"创建区域算法服务配置成功: region_id={region_id}, service_name={service_name}")
        return service
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建区域算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"创建区域算法服务配置失败: {str(e)}")


def update_region_algorithm_service(service_id: int, **kwargs) -> RegionModelService:
    """更新区域级别的算法模型服务配置"""
    try:
        service = RegionModelService.query.get_or_404(service_id)
        
        updatable_fields = [
            'service_name', 'service_url', 'service_type', 'model_id',
            'threshold', 'request_method', 'timeout', 'is_enabled', 'sort_order'
        ]
        
        for field in updatable_fields:
            if field in kwargs:
                setattr(service, field, kwargs[field])
        
        if 'request_headers' in kwargs:
            service.request_headers = json.dumps(kwargs['request_headers']) if kwargs['request_headers'] else None
        
        if 'request_body_template' in kwargs:
            service.request_body_template = json.dumps(kwargs['request_body_template']) if kwargs['request_body_template'] else None
        
        db.session.commit()
        logger.info(f"更新区域算法服务配置成功: service_id={service_id}")
        return service
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新区域算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"更新区域算法服务配置失败: {str(e)}")


def delete_region_algorithm_service(service_id: int):
    """删除区域级别的算法模型服务配置"""
    try:
        service = RegionModelService.query.get_or_404(service_id)
        db.session.delete(service)
        db.session.commit()
        logger.info(f"删除区域算法服务配置成功: service_id={service_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除区域算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"删除区域算法服务配置失败: {str(e)}")


def get_region_algorithm_services(region_id: int) -> List[RegionModelService]:
    """获取区域的所有算法模型服务配置"""
    try:
        services = RegionModelService.query.filter_by(region_id=region_id).order_by(
            RegionModelService.sort_order, RegionModelService.id
        ).all()
        return services
    except Exception as e:
        logger.error(f"获取区域算法服务配置失败: {str(e)}", exc_info=True)
        raise RuntimeError(f"获取区域算法服务配置失败: {str(e)}")


def call_algorithm_service(service: AlgorithmModelService or RegionModelService, image_data: bytes, 
                          additional_params: Optional[Dict] = None) -> Dict:
    """调用算法模型服务进行推理
    
    Args:
        service: 算法服务配置对象（任务级别或区域级别）
        image_data: 图片数据（bytes）
        additional_params: 额外的参数（如区域坐标等）
    
    Returns:
        dict: 推理结果
    """
    try:
        import base64
        
        # 准备请求数据
        headers = {}
        if service.request_headers:
            try:
                headers = json.loads(service.request_headers)
            except:
                pass
        
        # 构建请求体
        body = {}
        if service.request_body_template:
            try:
                body = json.loads(service.request_body_template)
                # 替换变量
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                body_str = json.dumps(body)
                body_str = body_str.replace('${image_base64}', image_base64)
                body_str = body_str.replace('${image_base64}', image_base64)  # 支持多种变量名
                if additional_params:
                    for key, value in additional_params.items():
                        body_str = body_str.replace(f'${{{key}}}', str(value))
                body = json.loads(body_str)
            except Exception as e:
                logger.warning(f"解析请求体模板失败，使用默认格式: {str(e)}")
                body = {'image': base64.b64encode(image_data).decode('utf-8')}
        else:
            # 默认格式
            body = {'image': base64.b64encode(image_data).decode('utf-8')}
        
        # 发送请求
        if service.request_method.upper() == 'GET':
            response = requests.get(service.service_url, params=body, headers=headers, timeout=service.timeout)
        else:
            response = requests.post(service.service_url, json=body, headers=headers, timeout=service.timeout)
        
        response.raise_for_status()
        result = response.json()
        
        logger.debug(f"算法服务调用成功: service_id={service.id}, result={result}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"算法服务调用失败: service_id={service.id}, error={str(e)}")
        raise RuntimeError(f"算法服务调用失败: {str(e)}")
    except Exception as e:
        logger.error(f"算法服务调用异常: service_id={service.id}, error={str(e)}", exc_info=True)
        raise RuntimeError(f"算法服务调用异常: {str(e)}")

