"""
模型部署服务业务逻辑
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import socket
import uuid
import logging
from datetime import datetime

from db_models import db, Model, AIService, beijing_now
from .deploy_daemon import DeployServiceDaemon

logger = logging.getLogger(__name__)


# 保存当前正在运行的所有守护进程对象
_deploy_daemons: dict[int, DeployServiceDaemon] = {}


def _get_log_file_path(service_id: int) -> str:
    """获取日志文件路径"""
    service = AIService.query.get(service_id)
    if service and service.log_path:
        return os.path.join(service.log_path, f'{service.service_name}.log')
    else:
        log_dir = os.path.join('data', 'deploy_logs')
        os.makedirs(log_dir, exist_ok=True)
        service_name = service.service_name if service else f'service_{service_id}'
        return os.path.join(log_dir, f'{service_name}.log')


def _get_service(service_id: int) -> AIService:
    """获取服务对象"""
    service = AIService.query.get(service_id)
    if not service:
        raise ValueError(f'服务[{service_id}]不存在')
    return service


def _get_model(model_id: int) -> Model:
    """获取模型对象"""
    model = Model.query.get(model_id)
    if not model:
        raise ValueError(f'模型[{model_id}]不存在')
    return model


def _get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def _get_mac_address():
    """获取MAC地址"""
    try:
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
    except:
        return 'unknown'


def _check_port_available(host, port):
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def _find_available_port(start_port=8000, max_attempts=100):
    """查找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        if _check_port_available('0.0.0.0', port):
            return port
    return None


def _download_model_to_local(model_path: str, model_id: int) -> str:
    """下载模型文件到本地（如果是MinIO URL）
    
    Args:
        model_path: 模型文件路径（可能是MinIO URL或本地路径）
        model_id: 模型ID（用于创建存储目录）
    
    Returns:
        str: 本地模型文件路径（绝对路径）
    """
    # 获取AI模块根目录
    ai_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    # 如果不是MinIO URL，处理本地路径
    if not model_path.startswith('/api/v1/buckets/'):
        # 如果是相对路径，转换为绝对路径（相对于AI模块根目录）
        if not os.path.isabs(model_path):
            model_path = os.path.join(ai_root, model_path)
        else:
            model_path = os.path.abspath(model_path)
        
        if os.path.exists(model_path):
            logger.info(f'模型文件已存在（本地路径）: {model_path}')
            return model_path
        else:
            logger.error(f'模型文件不存在: {model_path}')
            raise ValueError(f'模型文件不存在: {model_path}')
    
    # 解析MinIO URL
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(model_path)
        path_parts = parsed.path.split('/')
        
        # 提取bucket名称: /api/v1/buckets/{bucket_name}/objects/...
        if len(path_parts) >= 5 and path_parts[3] == 'buckets':
            bucket_name = path_parts[4]
        else:
            raise ValueError(f'URL格式不正确，无法提取bucket名称: {model_path}')
        
        # 提取object_key
        query_params = urllib.parse.parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]
        
        if not object_key:
            raise ValueError(f'URL中缺少prefix参数: {model_path}')
        
        # 创建模型存储目录（使用模型ID，而不是服务ID）
        # 使用绝对路径，相对于AI模块根目录
        model_storage_dir = os.path.join(ai_root, 'data', 'models', str(model_id))
        os.makedirs(model_storage_dir, exist_ok=True)
        
        # 从object_key中提取文件名
        filename = os.path.basename(object_key) or f"model_{model_id}"
        local_path = os.path.join(model_storage_dir, filename)
        
        # 如果文件已存在，直接返回（避免重复下载）
        if os.path.exists(local_path):
            file_size = os.path.getsize(local_path)
            logger.info(f'模型文件已存在，跳过下载: {local_path}, 大小: {file_size} 字节')
            return local_path
        
        # 下载文件
        logger.info(f'开始从MinIO下载模型文件...')
        logger.info(f'  Bucket: {bucket_name}')
        logger.info(f'  Object: {object_key}')
        logger.info(f'  目标路径: {local_path}')
        
        from app.services.minio_service import ModelService
        success, error_msg = ModelService.download_from_minio(
            bucket_name, object_key, local_path
        )
        
        if success:
            file_size = os.path.getsize(local_path)
            logger.info(f'模型文件下载成功: {local_path}, 大小: {file_size} 字节')
            return local_path
        else:
            logger.error(f'模型文件下载失败: {error_msg}')
            raise ValueError(f'模型文件下载失败: {error_msg}')
            
    except Exception as e:
        logger.error(f'下载模型文件异常: {str(e)}', exc_info=True)
        raise


def _infer_model_format(model: Model, model_path: str) -> str:
    """推断模型格式"""
    model_path_lower = model_path.lower()
    if model_path_lower.endswith('.onnx') or 'onnx' in model_path_lower:
        return 'onnx'
    elif model_path_lower.endswith(('.pt', '.pth')) or 'pytorch' in model_path_lower or 'torch' in model_path_lower:
        return 'pytorch'
    elif 'openvino' in model_path_lower:
        return 'openvino'
    elif 'tensorrt' in model_path_lower or model_path_lower.endswith('.trt'):
        return 'tensorrt'
    elif model_path_lower.endswith('.tflite'):
        return 'tflite'
    elif 'coreml' in model_path_lower or model_path_lower.endswith('.mlmodel'):
        return 'coreml'
    else:
        # 根据路径字段判断
        if model.onnx_model_path:
            return 'onnx'
        elif model.torchscript_model_path:
            return 'torchscript'
        elif model.tensorrt_model_path:
            return 'tensorrt'
        elif model.openvino_model_path:
            return 'openvino'
        else:
            return 'pytorch'  # 默认


def deploy_model(model_id: int, start_port: int = 8000) -> dict:
    """部署模型服务"""
    logger.info(f'========== 开始部署模型服务 ==========')
    logger.info(f'模型ID: {model_id}, 起始端口: {start_port}')
    
    try:
        model = _get_model(model_id)
        logger.info(f'模型信息: {model.name}, 版本: {model.version}')
        
        # 检查模型路径
        model_path = (model.model_path or model.onnx_model_path or 
                     model.torchscript_model_path or model.tensorrt_model_path or 
                     model.openvino_model_path)
        if not model_path:
            logger.error('模型没有可用的模型文件路径')
            raise ValueError('模型没有可用的模型文件路径')
        
        logger.info(f'模型路径: {model_path}')
        
        # 推断模型格式
        model_format = _infer_model_format(model, model_path)
        logger.info(f'推断模型格式: {model_format}')
        
        # 生成唯一的服务名称
        service_name = f"{model.name}_{model.version}_{int(datetime.now().timestamp())}"
        # 检查服务名称是否已存在
        max_attempts = 10
        for attempt in range(max_attempts):
            existing_service = AIService.query.filter_by(service_name=service_name).first()
            if not existing_service:
                break
            if attempt < max_attempts - 1:
                service_name = f"{model.name}_{model.version}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
                logger.debug(f'服务名称冲突，生成新名称: {service_name}')
        else:
            service_name = uuid.uuid4().hex
            logger.warning(f'多次尝试后仍冲突，使用UUID作为服务名称: {service_name}')
        
        logger.info(f'生成服务名称: {service_name}')
        
        # 查找可用端口
        logger.info(f'查找可用端口，起始端口: {start_port}')
        port = _find_available_port(start_port)
        if not port:
            logger.error(f'无法找到可用端口（从{start_port}开始尝试了100个端口）')
            raise ValueError(f'无法找到可用端口（从{start_port}开始尝试了100个端口）')
        
        logger.info(f'找到可用端口: {port}')
        
        # 获取服务器信息
        server_ip = _get_local_ip()
        mac_address = _get_mac_address()
        logger.info(f'服务器信息: IP={server_ip}, MAC={mac_address}')
        
        # 创建日志目录
        log_base_dir = os.path.join('data', 'deploy_logs')
        log_dir = os.path.join(log_base_dir, service_name)
        os.makedirs(log_dir, exist_ok=True)
        logger.info(f'日志目录: {log_dir}')
        
        # 创建部署服务记录
        logger.info('创建部署服务记录...')
        ai_service = AIService(
            model_id=model_id,
            service_name=service_name,
            server_ip=server_ip,
            port=port,
            inference_endpoint=f"http://{server_ip}:{port}/inference",
            status='offline',
            mac_address=mac_address,
            deploy_time=beijing_now(),
            log_path=log_dir,
            model_version=model.version,
            format=model_format
        )
        db.session.add(ai_service)
        db.session.commit()
        logger.info(f'服务记录已创建，服务ID: {ai_service.id}')
        
        # 检查部署脚本是否存在
        deploy_service_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services')
        deploy_script = os.path.join(deploy_service_dir, 'run_deploy.py')
        logger.info(f'检查部署脚本: {deploy_script}')
        
        if not os.path.exists(deploy_script):
            logger.warning(f'部署脚本不存在: {deploy_script}')
            return {
                'code': 0,
                'msg': '服务记录已创建，但部署脚本不存在，请检查部署服务目录',
                'data': ai_service.to_dict()
            }
        
        # 下载模型文件到本地（如果是MinIO URL）
        local_model_path = _download_model_to_local(model_path, model_id)
        
        # 启动守护进程（传入所有必要参数，不需要数据库连接）
        logger.info(f'启动守护进程，服务ID: {ai_service.id}')
        _deploy_daemons[ai_service.id] = DeployServiceDaemon(
            service_id=ai_service.id,
            service_name=ai_service.service_name,
            log_path=ai_service.log_path,
            model_id=ai_service.model_id,
            model_path=local_model_path,  # 已经是本地路径
            port=ai_service.port,
            server_ip=ai_service.server_ip,
            model_version=ai_service.model_version or model.version or 'V1.0.0',
            model_format=ai_service.format or model_format
        )
        ai_service.status = 'offline'  # 初始状态，等待心跳上报后变为running
        db.session.commit()
        
        logger.info(f'部署成功，服务ID: {ai_service.id}, 服务名称: {service_name}, 端口: {port}')
        logger.info(f'========== 模型服务部署完成 ==========')
        
        return {
            'code': 0,
            'msg': '部署成功，服务正在启动中，请稍后查看服务状态',
            'data': ai_service.to_dict()
        }
    except Exception as e:
        logger.error(f'部署模型服务失败: {str(e)}', exc_info=True)
        raise


def start_service(service_id: int) -> dict:
    """启动服务"""
    logger.info(f'========== 启动服务 ==========')
    logger.info(f'服务ID: {service_id}')
    
    try:
        service = _get_service(service_id)
        logger.info(f'服务信息: {service.service_name}, 当前状态: {service.status}')
        
        # 检查模型id是否存在
        if not service.model_id:
            logger.error('服务未关联模型，无法启动')
            raise ValueError('服务未关联模型，无法启动')
        
        model = _get_model(service.model_id)
        logger.info(f'模型信息: {model.name}, 版本: {model.version}')
        
        # 检查模型路径
        model_path = (model.model_path or model.onnx_model_path or 
                     model.torchscript_model_path or model.tensorrt_model_path or 
                     model.openvino_model_path)
        if not model_path:
            logger.error('模型没有可用的模型文件路径')
            raise ValueError('模型没有可用的模型文件路径')
        
        logger.info(f'模型路径: {model_path}')
        
        # 检查端口是否可用
        if service.port and not _check_port_available('0.0.0.0', service.port):
            logger.warning(f'端口 {service.port} 已被占用，查找新端口...')
            new_port = _find_available_port(service.port)
            if new_port:
                logger.info(f'找到新端口: {new_port}')
                service.port = new_port
                service.inference_endpoint = f"http://{service.server_ip}:{new_port}/inference"
            else:
                logger.error('无法找到可用端口')
                raise ValueError('无法找到可用端口')
        elif not service.port:
            logger.info('服务未设置端口，查找可用端口...')
            port = _find_available_port(8000)
            if not port:
                logger.error('无法找到可用端口')
                raise ValueError('无法找到可用端口')
            logger.info(f'找到可用端口: {port}')
            service.port = port
            service.inference_endpoint = f"http://{service.server_ip}:{port}/inference"
        else:
            logger.info(f'使用现有端口: {service.port}')
        
        # 确保日志目录存在
        if not service.log_path:
            log_base_dir = os.path.join('data', 'deploy_logs')
            log_path = os.path.join(log_base_dir, service.service_name)
            os.makedirs(log_path, exist_ok=True)
            service.log_path = log_path
            logger.info(f'创建日志目录: {log_path}')
        else:
            logger.info(f'使用现有日志目录: {service.log_path}')
        
        # 检查是否已有守护进程在运行
        if service_id in _deploy_daemons:
            daemon = _deploy_daemons[service_id]
            # 检查守护进程是否还在运行（通过检查进程状态）
            if daemon._running:
                logger.info('服务已在运行中')
                service.status = 'offline'  # 等待心跳上报
                db.session.commit()
                return {
                    'code': 0,
                    'msg': '服务已在运行中',
                    'data': service.to_dict()
                }
            else:
                logger.info('守护进程已停止，重新启动...')
        
        # 下载模型文件到本地（如果是MinIO URL）
        local_model_path = _download_model_to_local(model_path, service.model_id)
        
        # 启动守护进程（传入所有必要参数，不需要数据库连接）
        logger.info('启动守护进程...')
        _deploy_daemons[service_id] = DeployServiceDaemon(
            service_id=service.id,
            service_name=service.service_name,
            log_path=service.log_path,
            model_id=service.model_id,
            model_path=local_model_path,  # 已经是本地路径
            port=service.port,
            server_ip=service.server_ip,
            model_version=service.model_version or model.version or 'V1.0.0',
            model_format=service.format or _infer_model_format(model, model_path)
        )
        service.status = 'offline'  # 初始状态，等待心跳上报后变为running
        db.session.commit()
        
        logger.info(f'服务启动成功，服务ID: {service_id}, 端口: {service.port}')
        logger.info(f'========== 服务启动完成 ==========')
        
        return {
            'code': 0,
            'msg': '服务启动成功，正在启动中，请稍后查看服务状态',
            'data': service.to_dict()
        }
    except Exception as e:
        logger.error(f'启动服务失败: {str(e)}', exc_info=True)
        raise


def stop_service(service_id: int) -> dict:
    """停止服务"""
    service = _get_service(service_id)
    
    # 如果服务不在线，不需要停止
    if service.status not in ['running', 'offline']:
        return {
            'code': 0,
            'msg': '服务未在线，无需停止',
            'data': service.to_dict()
        }
    
    # 停止守护进程
    if service_id in _deploy_daemons:
        _deploy_daemons[service_id].stop()
        del _deploy_daemons[service_id]
    else:
        # 如果没有守护进程，尝试直接杀死进程
        if service.process_id:
            try:
                import psutil
                if psutil.pid_exists(service.process_id):
                    process = psutil.Process(service.process_id)
                    process.kill()
            except:
                pass
    
    # 更新状态为停止
    service.status = 'stopped'
    service.process_id = None
    db.session.commit()
    
    return {
        'code': 0,
        'msg': '服务停止成功',
        'data': service.to_dict()
    }


def restart_service(service_id: int) -> dict:
    """重启服务"""
    service = _get_service(service_id)
    
    if service_id in _deploy_daemons:
        _deploy_daemons[service_id].restart()
        service.status = 'offline'  # 等待心跳上报
        db.session.commit()
        return {
            'code': 0,
            'msg': '服务重启成功',
            'data': service.to_dict()
        }
    else:
        # 如果没有守护进程，先启动
        return start_service(service_id)


def delete_service(service_id: int) -> dict:
    """删除服务"""
    service = _get_service(service_id)
    service_name = service.service_name
    
    # 先停止守护进程
    if service_id in _deploy_daemons:
        _deploy_daemons[service_id].stop()
        del _deploy_daemons[service_id]
    else:
        # 如果没有守护进程，尝试直接杀死进程
        if service.process_id:
            try:
                import psutil
                if psutil.pid_exists(service.process_id):
                    process = psutil.Process(service.process_id)
                    process.kill()
            except:
                pass
    
    # 删除服务记录
    db.session.delete(service)
    db.session.commit()
    
    return {
        'code': 0,
        'msg': '服务删除成功'
    }


def get_service_logs(service_id: int, lines: int = 100, date: str = None) -> dict:
    """获取服务日志"""
    service = _get_service(service_id)
    
    # 确定日志文件路径
    if not service.log_path:
        log_base_dir = os.path.join('data', 'deploy_logs')
        service_log_dir = os.path.join(log_base_dir, service.service_name)
    else:
        service_log_dir = service.log_path
    
    # 根据参数选择日志文件
    if date:
        log_filename = f"{service.service_name}_{date}.log"
    else:
        log_filename = f"{service.service_name}.log"
    
    log_file_path = os.path.join(service_log_dir, log_filename)
    
    # 检查日志文件是否存在
    if not os.path.exists(log_file_path):
        return {
            'code': 0,
            'msg': 'success',
            'data': {
                'logs': f'日志文件不存在: {log_filename}\n请等待服务运行后生成日志。',
                'total_lines': 0,
                'log_file': log_filename,
                'is_all_file': not bool(date)
            }
        }
    
    # 读取日志文件最后N行
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            log_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            'code': 0,
            'msg': 'success',
            'data': {
                'logs': ''.join(log_lines),
                'total_lines': len(all_lines),
                'log_file': log_filename,
                'is_all_file': not bool(date)
            }
        }
    except Exception as e:
        raise ValueError(f'读取日志文件失败: {str(e)}')

