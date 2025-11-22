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
            logger.warning(f"Nacos客户端未初始化，无法获取服务实例: {service_name}")
            return []
        
        logger.info(f"从Nacos查询服务实例: {service_name}, healthy_only={healthy_only}")
        
        # 获取服务实例列表
        try:
            instances = nacos_client.list_naming_instance(
                service_name=service_name,
                healthy_only=healthy_only
            )
        except Exception as e:
            logger.error(f"调用list_naming_instance失败: {str(e)}", exc_info=True)
            return []
        
        if not instances:
            logger.warning(f"未找到服务实例: {service_name} (healthy_only={healthy_only})")
            return []
        
        # 检查返回的数据格式并处理
        logger.debug(f"Nacos返回的数据类型: {type(instances)}")
        
        # 如果返回的是字典，尝试提取实例列表
        if isinstance(instances, dict):
            logger.debug(f"Nacos返回字典，键: {list(instances.keys())}")
            # 常见的字段名：hosts, instances, data, list
            if 'hosts' in instances:
                instances = instances['hosts']
                logger.debug(f"从 'hosts' 字段提取到 {len(instances) if instances else 0} 个实例")
            elif 'instances' in instances:
                instances = instances['instances']
                logger.debug(f"从 'instances' 字段提取到 {len(instances) if instances else 0} 个实例")
            elif 'data' in instances:
                instances = instances['data']
                logger.debug(f"从 'data' 字段提取到 {len(instances) if instances else 0} 个实例")
            elif 'list' in instances:
                instances = instances['list']
                logger.debug(f"从 'list' 字段提取到 {len(instances) if instances else 0} 个实例")
            else:
                # 如果字典中没有常见的字段，尝试将整个字典作为单个实例处理
                logger.warning(f"字典中没有找到常见的实例字段，尝试将整个字典作为单个实例: {list(instances.keys())}")
                # 检查是否包含IP和端口信息
                if 'ip' in instances or 'IP' in instances or 'port' in instances or 'PORT' in instances:
                    instances = [instances]
                else:
                    logger.error(f"无法从字典中提取服务实例: {instances}")
                    return []
        
        # 如果返回的是字符串，尝试解析为JSON
        elif isinstance(instances, str):
            logger.warning(f"Nacos返回字符串，尝试解析为JSON")
            try:
                import json
                instances = json.loads(instances)
                # 递归处理解析后的数据
                if isinstance(instances, dict):
                    # 再次尝试从字典中提取
                    if 'hosts' in instances:
                        instances = instances['hosts']
                    elif 'instances' in instances:
                        instances = instances['instances']
                    elif 'data' in instances:
                        instances = instances['data']
                    elif 'list' in instances:
                        instances = instances['list']
                    else:
                        if 'ip' in instances or 'IP' in instances:
                            instances = [instances]
                        else:
                            logger.error(f"解析后仍无法提取实例: {instances}")
                            return []
            except Exception as e:
                logger.error(f"无法解析返回的字符串: {str(e)}")
                return []
        
        # 确保现在是列表类型
        if not isinstance(instances, list):
            logger.error(f"处理后仍不是列表类型: {type(instances)}, 值: {instances}")
            return []
        
        if len(instances) == 0:
            logger.warning(f"服务实例列表为空: {service_name}")
            return []
        
        # 处理每个实例
        processed_instances = []
        for i, inst in enumerate(instances):
            try:
                if isinstance(inst, dict):
                    # 已经是字典格式，直接使用
                    ip = inst.get('ip') or inst.get('IP') or ''
                    port = inst.get('port') or inst.get('PORT') or 8000
                    if ip:
                        processed_instances.append({
                            'ip': ip,
                            'port': int(port) if isinstance(port, (int, str)) else 8000
                        })
                        logger.debug(f"  实例 {i+1}: {ip}:{port}")
                    else:
                        logger.warning(f"  实例 {i+1} 缺少IP地址: {inst}")
                elif isinstance(inst, str):
                    # 如果是字符串，尝试解析为JSON
                    try:
                        import json
                        parsed = json.loads(inst)
                        if isinstance(parsed, dict):
                            ip = parsed.get('ip') or parsed.get('IP') or ''
                            port = parsed.get('port') or parsed.get('PORT') or 8000
                            if ip:
                                processed_instances.append({
                                    'ip': ip,
                                    'port': int(port) if isinstance(port, (int, str)) else 8000
                                })
                                logger.debug(f"  实例 {i+1} (解析后): {ip}:{port}")
                            else:
                                logger.warning(f"  实例 {i+1} 解析后缺少IP地址: {parsed}")
                        else:
                            logger.warning(f"  实例 {i+1} 解析后不是字典: {type(parsed)}")
                    except json.JSONDecodeError:
                        logger.warning(f"  实例 {i+1} 无法解析为JSON: {inst[:100]}")
                elif hasattr(inst, 'ip') and hasattr(inst, 'port'):
                    # 对象格式，使用属性访问
                    ip = getattr(inst, 'ip', '') or getattr(inst, 'IP', '')
                    port = getattr(inst, 'port', 8000) or getattr(inst, 'PORT', 8000)
                    if ip:
                        processed_instances.append({
                            'ip': str(ip),
                            'port': int(port) if isinstance(port, (int, str)) else 8000
                        })
                        logger.debug(f"  实例 {i+1} (对象): {ip}:{port}")
                else:
                    logger.warning(f"  实例 {i+1} 格式未知: {type(inst)}, 值: {str(inst)[:100]}")
            except Exception as e:
                logger.warning(f"处理实例 {i+1} 时出错: {str(e)}")
                continue
        
        if not processed_instances:
            logger.warning(f"未能处理任何服务实例: {service_name} (原始数据: {instances[:3] if instances else 'None'})")
            return []
        
        logger.info(f"找到 {len(processed_instances)} 个可用的服务实例: {service_name}")
        return processed_instances
        
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"从Nacos获取服务实例失败 [{error_type}]: {str(e)}", exc_info=True)
        return []


def get_random_service_instance(service_name: str, healthy_only: bool = True) -> Optional[Dict]:
    """从Nacos获取服务实例，随机选择一个"""
    instances = get_service_instances(service_name, healthy_only)
    
    if not instances:
        logger.warning(f"未找到可用的服务实例: {service_name}")
        return None
    
    # 随机选择一个实例
    selected_instance = random.choice(instances)
    ip = selected_instance.get('ip', '')
    port = selected_instance.get('port', 8000)
    
    logger.info(f"从Nacos随机选择服务实例: {service_name} -> {ip}:{port} (共{len(instances)}个实例)")
    
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
    """构建模型服务的Nacos服务名：model_{model_id}_{model_version}_{model_format}
    
    注意：此格式必须与 run_deploy.py 中的 generate_service_name 函数保持一致
    注册格式：model_{model_id}_{model_version}_{model_type}
    """
    return f"model_{model_id}_{model_version}_{model_format}"


def get_model_service_url(model_id: int, model_format: str, model_version: str, healthy_only: bool = True) -> Optional[str]:
    """获取模型服务的URL（通过Nacos服务发现）"""
    service_name = get_model_service_name(model_id, model_format, model_version)
    return get_service_url(service_name, healthy_only)

