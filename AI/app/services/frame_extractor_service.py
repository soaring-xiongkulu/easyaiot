"""
抽帧器服务管理
用于管理视频/RTSP流的抽帧服务，每个摄像头配置1个抽帧器

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import socket
import threading
import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, Optional
from collections import OrderedDict

from db_models import db, FrameExtractor, beijing_now

logger = logging.getLogger(__name__)

# 保存所有正在运行的抽帧器守护进程
_extractor_daemons: Dict[int, 'FrameExtractorDaemon'] = {}


class FrameExtractorDaemon:
    """抽帧器守护进程，管理抽帧服务"""
    
    def __init__(self, extractor_id: int, camera_name: str, port: int, server_ip: str,
                 input_source: str, input_type: str, service_name: str, 
                 sorter_receive_url: str, frame_skip: int = 1):
        """
        初始化抽帧器守护进程
        
        Args:
            extractor_id: 抽帧器ID
            camera_name: 摄像头名称
            port: 抽帧器端口
            server_ip: 服务器IP
            input_source: 输入源（视频文件路径或RTSP地址）
            input_type: 输入类型（video/rtsp）
            service_name: 服务名称（用于查找推理器）
            sorter_receive_url: 排序器接收地址
            frame_skip: 抽帧间隔（每N帧抽1帧）
        """
        self._extractor_id = extractor_id
        self._camera_name = camera_name
        self._port = port
        self._server_ip = server_ip
        self._input_source = input_source
        self._input_type = input_type
        self._service_name = service_name
        self._sorter_receive_url = sorter_receive_url
        self._frame_skip = frame_skip
        self._process = None
        self._running = True
        self._log_path = None
        
        # 启动守护进程
        threading.Thread(target=self._daemon, daemon=True).start()
    
    def _get_log_file_path(self) -> str:
        """获取日志文件路径"""
        if not self._log_path:
            ai_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(ai_root, 'logs', 'extractors')
            os.makedirs(log_base_dir, exist_ok=True)
            log_filename = datetime.now().strftime('%Y-%m-%d.log')
            self._log_path = os.path.join(log_base_dir, f"{self._camera_name}_{log_filename}")
        return self._log_path
    
    def _daemon(self):
        """守护进程主循环"""
        log_file_path = self._get_log_file_path()
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        f_log = open(log_file_path, 'a', encoding='utf-8')
        try:
            f_log.write(f'# ========== 抽帧器守护进程启动 ==========\n')
            f_log.write(f'# 抽帧器ID: {self._extractor_id}\n')
            f_log.write(f'# 摄像头名称: {self._camera_name}\n')
            f_log.write(f'# 启动时间: {datetime.now().isoformat()}\n')
            f_log.write(f'# ===========================================\n\n')
            f_log.flush()
            
            while self._running:
                try:
                    # 检查抽帧器是否启用（从数据库查询）
                    with db.session.begin():
                        extractor = FrameExtractor.query.get(self._extractor_id)
                        if not extractor:
                            logger.warning(f'抽帧器不存在: ID={self._extractor_id}')
                            f_log.write(f'# [{datetime.now().isoformat()}] [WARNING] 抽帧器不存在，等待10秒后重试...\n')
                            f_log.flush()
                            time.sleep(10)
                            continue
                        
                        # 如果抽帧器未启用，不运行，等待一段时间后重新检查
                        if not extractor.is_enabled:
                            logger.debug(f'抽帧器 {self._camera_name} 未启用，等待30秒后重新检查...')
                            f_log.write(f'# [{datetime.now().isoformat()}] [INFO] 抽帧器未启用，等待30秒后重新检查...\n')
                            f_log.flush()
                            time.sleep(30)
                            continue
                    
                    # 获取抽帧器脚本路径
                    ai_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    extractor_script = os.path.join(ai_root, 'services', 'run_extractor.py')
                    
                    if not os.path.exists(extractor_script):
                        logger.error(f'抽帧器脚本不存在: {extractor_script}')
                        f_log.write(f'# [{datetime.now().isoformat()}] [ERROR] 抽帧器脚本不存在: {extractor_script}\n')
                        f_log.flush()
                        time.sleep(10)
                        continue
                    
                    # 准备环境变量
                    env = os.environ.copy()
                    env['EXTRACTOR_ID'] = str(self._extractor_id)
                    env['CAMERA_NAME'] = self._camera_name
                    env['PORT'] = str(self._port)
                    env['SERVER_IP'] = self._server_ip
                    env['INPUT_SOURCE'] = self._input_source
                    env['INPUT_TYPE'] = self._input_type
                    env['SERVICE_NAME'] = self._service_name
                    env['SORTER_RECEIVE_URL'] = self._sorter_receive_url or ''
                    env['FRAME_SKIP'] = str(self._frame_skip)
                    env['API_BASE_URL'] = os.getenv('API_BASE_URL', 'http://127.0.0.1:5000')
                    env['PYTHONUNBUFFERED'] = '1'
                    
                    # 启动抽帧器进程
                    f_log.write(f'\n# ========== 启动抽帧器服务 ==========\n')
                    f_log.write(f'# 时间: {datetime.now().isoformat()}\n')
                    f_log.write(f'# 抽帧器ID: {self._extractor_id}\n')
                    f_log.write(f'# Python解释器: {sys.executable}\n')
                    f_log.write(f'# 抽帧器脚本: {extractor_script}\n')
                    f_log.write(f'# 环境变量:\n')
                    for key in ['EXTRACTOR_ID', 'CAMERA_NAME', 'PORT', 'SERVER_IP', 'INPUT_SOURCE', 
                                'INPUT_TYPE', 'SERVICE_NAME', 'SORTER_RECEIVE_URL', 'FRAME_SKIP', 'API_BASE_URL']:
                        if key in env:
                            f_log.write(f'#   {key}={env[key]}\n')
                    f_log.write(f'# ===================================\n\n')
                    f_log.flush()
                    
                    self._process = subprocess.Popen(
                        [sys.executable, extractor_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        env=env,
                        text=True,
                        bufsize=1
                    )
                    
                    f_log.write(f'# 进程PID: {self._process.pid}\n')
                    f_log.flush()
                    
                    # 读取输出
                    for line in iter(self._process.stdout.readline, ''):
                        if not line:
                            break
                        f_log.write(line)
                        f_log.flush()
                    
                    # 等待进程结束
                    return_code = self._process.wait()
                    f_log.write(f'\n# 进程退出，返回码: {return_code}\n')
                    f_log.flush()
                    
                    if not self._running:
                        break
                    
                    # 如果异常退出，等待后重启（但需要检查is_enabled状态）
                    logger.warning(f'抽帧器服务异常退出（返回码: {return_code}），将在5秒后检查是否重启')
                    f_log.write(f'\n# [{datetime.now().isoformat()}] 抽帧器服务异常退出（返回码: {return_code}），将在5秒后检查是否重启......\n')
                    f_log.flush()
                    time.sleep(5)
                    
                except Exception as e:
                    import traceback
                    error_msg = f'守护进程异常: {str(e)}\n{traceback.format_exc()}'
                    logger.error(error_msg)
                    f_log.write(f'\n# [{datetime.now().isoformat()}] [ERROR] {error_msg}\n')
                    f_log.flush()
                    time.sleep(10)
        finally:
            if f_log:
                f_log.close()
    
    def stop(self):
        """停止抽帧器"""
        self._running = False
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()


def get_local_ip():
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def find_available_port(start_port: int = 9100, max_attempts: int = 100) -> Optional[int]:
    """查找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
            return port
        except OSError:
            sock.close()
            continue
    return None


def start_extractor(camera_name: str, input_source: str, input_type: str, 
                   model_id: int, service_name: str, frame_skip: int = 1) -> dict:
    """
    启动抽帧器服务
    
    Args:
        camera_name: 摄像头名称
        input_source: 输入源（视频文件路径或RTSP地址）
        input_type: 输入类型（video/rtsp）
        model_id: 模型ID
        service_name: 服务名称（用于查找推理器和排序器）
        frame_skip: 抽帧间隔（每N帧抽1帧）
    
    Returns:
        dict: 启动结果
    """
    try:
        # 检查是否已存在抽帧器（每个摄像头只能有一个抽帧器）
        existing_extractor = FrameExtractor.query.filter_by(camera_name=camera_name).first()
        
        if existing_extractor:
            # 如果已存在，检查是否在运行
            if existing_extractor.id in _extractor_daemons:
                daemon = _extractor_daemons[existing_extractor.id]
                if daemon._running:
                    logger.info(f'抽帧器已运行: {camera_name}')
                    return {
                        'code': 0,
                        'msg': '抽帧器已在运行',
                        'data': existing_extractor.to_dict()
                    }
            
            # 更新配置并重新启动
            extractor = existing_extractor
            extractor.input_source = input_source
            extractor.input_type = input_type
            extractor.model_id = model_id
            extractor.service_name = service_name
            extractor.frame_skip = frame_skip
            extractor.is_enabled = True  # 开启抽帧器
            extractor.status = 'stopped'
            
            # 如果当前输入源是视频则从头抽帧，如果是rtsp流也是取当前流去抽帧
            # 对于视频，重置帧索引；对于RTSP，保持当前索引（从当前流开始）
            if input_type == 'video':
                extractor.current_frame_index = 0  # 视频从头抽帧
            # RTSP不需要重置索引，从当前流开始抽帧
        else:
            # 创建新的抽帧器记录
            server_ip = get_local_ip()
            port = find_available_port(9100)
            if not port:
                raise ValueError('无法找到可用端口')
            
            # 获取排序器接收地址
            from .frame_sorter_service import get_sorter
            sorter = get_sorter(service_name)
            sorter_receive_url = sorter.receive_url if sorter else None
            
            extractor = FrameExtractor(
                camera_name=camera_name,
                input_source=input_source,
                input_type=input_type,
                model_id=model_id,
                service_name=service_name,
                sorter_receive_url=sorter_receive_url,
                port=port,
                server_ip=server_ip,
                frame_skip=frame_skip,
                current_frame_index=0,
                is_enabled=True,  # 新创建的抽帧器默认开启
                status='stopped'
            )
            db.session.add(extractor)
            db.session.commit()
        
        # 获取排序器接收地址（如果还没有）
        if not extractor.sorter_receive_url:
            from .frame_sorter_service import get_sorter
            sorter = get_sorter(service_name)
            if sorter:
                extractor.sorter_receive_url = sorter.receive_url
                db.session.commit()
        
        # 启动守护进程
        _extractor_daemons[extractor.id] = FrameExtractorDaemon(
            extractor_id=extractor.id,
            camera_name=extractor.camera_name,
            port=extractor.port,
            server_ip=extractor.server_ip,
            input_source=extractor.input_source,
            input_type=extractor.input_type,
            service_name=extractor.service_name,
            sorter_receive_url=extractor.sorter_receive_url or '',
            frame_skip=extractor.frame_skip
        )
        
        extractor.status = 'running'
        db.session.commit()
        
        logger.info(f'抽帧器启动成功: {camera_name}, 端口: {extractor.port}, 输入类型: {input_type}')
        
        return {
            'code': 0,
            'msg': '抽帧器启动成功',
            'data': extractor.to_dict()
        }
        
    except Exception as e:
        logger.error(f'启动抽帧器失败: {str(e)}', exc_info=True)
        db.session.rollback()
        raise


def stop_extractor(camera_name: str) -> dict:
    """停止抽帧器（关闭开关）"""
    try:
        extractor = FrameExtractor.query.filter_by(camera_name=camera_name).first()
        if not extractor:
            return {
                'code': 404,
                'msg': '抽帧器不存在'
            }
        
        if extractor.id in _extractor_daemons:
            _extractor_daemons[extractor.id].stop()
            del _extractor_daemons[extractor.id]
        
        extractor.status = 'stopped'
        extractor.is_enabled = False  # 关闭开关
        db.session.commit()
        
        return {
            'code': 0,
            'msg': '抽帧器已关闭'
        }
        
    except Exception as e:
        logger.error(f'停止抽帧器失败: {str(e)}', exc_info=True)
        db.session.rollback()
        raise


def get_extractor(camera_name: str) -> Optional[FrameExtractor]:
    """获取抽帧器"""
    return FrameExtractor.query.filter_by(camera_name=camera_name).first()
