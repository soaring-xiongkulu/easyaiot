"""
Nacos服务发现工具
用于从Nacos获取服务实例并实现集群调用
"""
import os
import random
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

_nacos_client = None


def get_nacos_client():
    """获取Nacos客户端（单例模式）"""
    global _nacos_client
    
    if _nacos_client is not None:
        return _nacos_client
    
    try:
        from nacos import NacosClient
        
        # 获取Nacos配置
        nacos_server = os.getenv('NACOS_SERVER', 'localhost:8848')
        namespace = os.getenv('NACOS_NAMESPACE', '')
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')
        
        # 创建Nacos客户端
        _nacos_client = NacosClient(
            server_addresses=nacos_server,
            namespace=namespace,
            username=username,
            password=password
        )
        
        return _nacos_client
        
    except ImportError:
        logger.error("nacos-sdk-python未安装，无法使用Nacos服务发现")
        return None
    except Exception as e:
        logger.error(f"创建Nacos客户端失败: {str(e)}")
        return None


def get_service_instances(service_name: str, healthy_only: bool = True) -> List[Dict]:
    """从Nacos获取服务实例列表"""
    try:
        nacos_client = get_nacos_client()
        if not nacos_client:
            return []
        
        # 获取服务实例列表
        instances = nacos_client.list_naming_instance(
            service_name=service_name,
            healthy_only=healthy_only
        )
        
        if not instances:
            logger.warning(f"未找到服务实例: {service_name}")
            return []
        
        return instances
        
    except Exception as e:
        logger.error(f"从Nacos获取服务实例失败: {str(e)}")
        return []


def get_random_service_instance(service_name: str, healthy_only: bool = True) -> Optional[Dict]:
    """从Nacos获取服务实例，随机选择一个"""
    instances = get_service_instances(service_name, healthy_only)
    
    if not instances:
        return None
    
    # 随机选择一个实例
    selected_instance = random.choice(instances)
    
    logger.info(f"从Nacos获取到服务实例: {service_name} -> {selected_instance.get('ip')}:{selected_instance.get('port')} (共{len(instances)}个实例)")
    
    return selected_instance


def get_service_url(service_name: str, healthy_only: bool = True) -> Optional[str]:
    """从Nacos获取服务URL（随机选择一个实例）"""
    instance = get_random_service_instance(service_name, healthy_only)
    
    if not instance:
        return None
    
    ip = instance.get('ip', '')
    port = instance.get('port', 8000)
    
    return f"http://{ip}:{port}"


def get_model_service_name(model_id: int, model_format: str, model_version: str) -> str:
    """构建模型服务的Nacos服务名：model_{model_id}_{format}_{version}"""
    return f"model_{model_id}_{model_format}_{model_version}"


def get_model_service_url(model_id: int, model_format: str, model_version: str, healthy_only: bool = True) -> Optional[str]:
    """获取模型服务的URL（通过Nacos服务发现）"""
    service_name = get_model_service_name(model_id, model_format, model_version)
    return get_service_url(service_name, healthy_only)

