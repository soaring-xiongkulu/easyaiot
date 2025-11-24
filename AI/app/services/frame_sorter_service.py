"""
帧排序器服务
用于处理视频/RTSP流的帧排序，确保相同service_name的多个模型实例输出的帧按顺序推送
使用滑动窗口算法实现帧排序

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
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple
from collections import OrderedDict
import cv2
import numpy as np

from db_models import db, FrameSorter, beijing_now

logger = logging.getLogger(__name__)

# 保存所有正在运行的排序器守护进程
_sorter_daemons: Dict[int, 'FrameSorterDaemon'] = {}


class FrameBuffer:
    """帧缓冲区，使用滑动窗口管理帧"""
    
    def __init__(self, window_size: int = 10, timeout: float = 5.0, batch_size: int = 5, frame_timeout: float = 2.0):
        """
        初始化帧缓冲区
        
        Args:
            window_size: 滑动窗口大小
            timeout: 超时时间（秒），超过此时间未收到帧则输出窗口中的帧
            batch_size: 批量推送的帧数阈值，达到此数量时批量推送
            frame_timeout: 单个帧的最大等待时间（秒），超过此时间则跳过该帧继续处理
        """
        self.window_size = window_size
        self.timeout = timeout
        self.batch_size = batch_size
        self.frame_timeout = frame_timeout
        self.buffer: OrderedDict[int, Tuple[bytes, float]] = OrderedDict()  # {frame_seq: (frame_data, timestamp)}
        self.expected_seq = 0  # 期望的下一个帧序号
        self.expected_seq_wait_start = time.time()  # 期望序号开始等待的时间
        self.lock = threading.Lock()
        self.last_receive_time = time.time()
        self.instance_frames: Dict[str, int] = {}  # {instance_id: last_seq} 记录每个实例的最后序号
        
    def add_frame(self, frame_seq: int, frame_data: bytes, instance_id: str) -> bool:
        """
        添加帧到缓冲区
        
        Args:
            frame_seq: 帧序号
            frame_data: 帧数据（JPEG编码的图片）
            instance_id: 实例ID（用于追踪）
        
        Returns:
            bool: 是否应该输出帧（当收到期望的帧时返回True）
        """
        with self.lock:
            self.last_receive_time = time.time()
            
            # 更新实例的最后序号
            if instance_id not in self.instance_frames:
                self.instance_frames[instance_id] = frame_seq
            else:
                # 如果序号小于等于已记录的序号，可能是重复帧，忽略
                if frame_seq <= self.instance_frames[instance_id]:
                    logger.warning(f"收到重复帧或乱序帧: instance={instance_id}, seq={frame_seq}, last_seq={self.instance_frames[instance_id]}")
                    return False
                self.instance_frames[instance_id] = frame_seq
            
            # 如果序号小于期望序号，可能是延迟到达的帧，直接忽略
            if frame_seq < self.expected_seq:
                logger.warning(f"收到过期帧: seq={frame_seq}, expected={self.expected_seq}")
                return False
            
            # 添加到缓冲区
            self.buffer[frame_seq] = (frame_data, time.time())
            
            # 如果缓冲区过大，清理过期帧
            if len(self.buffer) > self.window_size * 2:
                # 移除序号小于期望序号的所有帧
                keys_to_remove = [k for k in self.buffer.keys() if k < self.expected_seq]
                for k in keys_to_remove:
                    del self.buffer[k]
            
            # 检查是否收到期望的帧
            if frame_seq == self.expected_seq:
                # 收到期望帧，重置等待时间
                self.expected_seq_wait_start = time.time()
                return True
            else:
                return False
    
    def get_next_frame(self) -> Optional[bytes]:
        """
        获取下一个应该输出的帧（期望序号）
        
        Returns:
            bytes: 帧数据，如果没有则返回None
        """
        with self.lock:
            if self.expected_seq in self.buffer:
                frame_data, _ = self.buffer.pop(self.expected_seq)
                self.expected_seq += 1
                return frame_data
            return None
    
    def should_flush(self) -> bool:
        """
        检查是否应该刷新缓冲区（超时、缓冲区满或达到批量推送阈值）
        
        Returns:
            bool: 是否应该刷新
        """
        with self.lock:
            current_time = time.time()
            
            # 如果超时且缓冲区有帧
            if current_time - self.last_receive_time > self.timeout and len(self.buffer) > 0:
                return True
            
            # 如果缓冲区满了
            if len(self.buffer) >= self.window_size:
                return True
            
            # 如果达到批量推送阈值（有连续的帧达到batch_size个）
            consecutive_count = 0
            seq = self.expected_seq
            while seq in self.buffer and consecutive_count < self.batch_size:
                consecutive_count += 1
                seq += 1
            if consecutive_count >= self.batch_size:
                return True
            
            # 检查是否有超时的帧需要跳过
            if len(self.buffer) > 0:
                oldest_seq = min(self.buffer.keys())
                if oldest_seq in self.buffer:
                    _, frame_timestamp = self.buffer[oldest_seq]
                    if current_time - frame_timestamp > self.frame_timeout:
                        return True
            
            return False
    
    def flush_available_frames(self) -> list:
        """
        刷新缓冲区，实现"只等5帧，然后指针移动到当前窗口最大的index的下一位"的逻辑
        
        Returns:
            list: 可输出的帧列表，每个元素是(frame_data, skipped_count)
                  skipped_count表示跳过的帧数
        """
        frames = []
        skipped_count = 0
        current_time = time.time()
        
        with self.lock:
            # 如果缓冲区中的帧数达到batch_size（5帧），执行跳转逻辑
            if len(self.buffer) >= self.batch_size:
                # 找到当前窗口中的最大index
                max_seq = max(self.buffer.keys())
                
                # 将指针移动到最大index的下一位
                new_expected_seq = max_seq + 1
                
                # 计算跳过的帧数
                skipped_count = new_expected_seq - self.expected_seq
                
                # 丢弃所有index < new_expected_seq的帧
                keys_to_remove = [k for k in self.buffer.keys() if k < new_expected_seq]
                for k in keys_to_remove:
                    self.buffer.pop(k)
                    logger.debug(f"丢弃帧: seq={k} (移动到 {new_expected_seq})")
                
                # 更新期望序号
                self.expected_seq = new_expected_seq
                self.expected_seq_wait_start = current_time
                
                logger.info(f"窗口中有 {len(self.buffer)} 帧，最大index={max_seq}，指针移动到 {new_expected_seq}，跳过了 {skipped_count} 帧")
            
            # 输出连续的可用帧（从新的期望序号开始）
            output_count = 0
            while self.expected_seq in self.buffer and output_count < self.batch_size:
                frame_data, _ = self.buffer.pop(self.expected_seq)
                frames.append((frame_data, skipped_count if output_count == 0 else 0))
                self.expected_seq += 1
                self.expected_seq_wait_start = current_time
                output_count += 1
                skipped_count = 0  # 只在第一批输出时报告跳过的帧数
        
        return frames
    
    def get_stats(self) -> dict:
        """获取缓冲区统计信息"""
        with self.lock:
            current_time = time.time()
            oldest_timestamp = None
            if len(self.buffer) > 0:
                oldest_seq = min(self.buffer.keys())
                if oldest_seq in self.buffer:
                    _, oldest_timestamp = self.buffer[oldest_seq]
            
            return {
                'buffer_size': len(self.buffer),
                'expected_seq': self.expected_seq,
                'window_size': self.window_size,
                'batch_size': self.batch_size,
                'instances': len(self.instance_frames),
                'last_receive_time': self.last_receive_time,
                'oldest_frame_age': current_time - oldest_timestamp if oldest_timestamp else None,
                'frame_timeout': self.frame_timeout
            }


class FrameSorterDaemon:
    """帧排序器守护进程，管理排序器服务"""
    
    def __init__(self, sorter_id: int, service_name: str, port: int, server_ip: str, 
                 output_url: str, window_size: int = 10, batch_size: int = 5, frame_timeout: float = 2.0):
        """
        初始化排序器守护进程
        
        Args:
            sorter_id: 排序器ID
            service_name: 服务名称
            port: 排序器端口
            server_ip: 服务器IP
            output_url: 输出流地址
            window_size: 滑动窗口大小
            batch_size: 批量推送阈值
            frame_timeout: 单个帧超时时间（秒）
        """
        self._sorter_id = sorter_id
        self._service_name = service_name
        self._port = port
        self._server_ip = server_ip
        self._output_url = output_url
        self._window_size = window_size
        self._batch_size = batch_size
        self._frame_timeout = frame_timeout
        self._process = None
        self._running = True
        self._log_path = None
        
        # 启动守护进程
        threading.Thread(target=self._daemon, daemon=True).start()
    
    def _get_log_file_path(self) -> str:
        """获取日志文件路径"""
        if not self._log_path:
            ai_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(ai_root, 'logs', 'sorters')
            os.makedirs(log_base_dir, exist_ok=True)
            log_filename = datetime.now().strftime('%Y-%m-%d.log')
            self._log_path = os.path.join(log_base_dir, f"{self._service_name}_{log_filename}")
        return self._log_path
    
    def _daemon(self):
        """守护进程主循环"""
        log_file_path = self._get_log_file_path()
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        f_log = open(log_file_path, 'a', encoding='utf-8')
        try:
            f_log.write(f'# ========== 帧排序器守护进程启动 ==========\n')
            f_log.write(f'# 排序器ID: {self._sorter_id}\n')
            f_log.write(f'# 服务名称: {self._service_name}\n')
            f_log.write(f'# 启动时间: {datetime.now().isoformat()}\n')
            f_log.write(f'# ===========================================\n\n')
            f_log.flush()
            
            while self._running:
                try:
                    # 获取排序器脚本路径
                    ai_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    sorter_script = os.path.join(ai_root, 'services', 'run_sorter.py')
                    
                    if not os.path.exists(sorter_script):
                        logger.error(f'排序器脚本不存在: {sorter_script}')
                        f_log.write(f'# [{datetime.now().isoformat()}] [ERROR] 排序器脚本不存在: {sorter_script}\n')
                        f_log.flush()
                        time.sleep(10)
                        continue
                    
                    # 准备环境变量
                    env = os.environ.copy()
                    env['SORTER_ID'] = str(self._sorter_id)
                    env['SERVICE_NAME'] = self._service_name
                    env['PORT'] = str(self._port)
                    env['SERVER_IP'] = self._server_ip
                    env['OUTPUT_URL'] = self._output_url
                    env['WINDOW_SIZE'] = str(self._window_size)
                    env['BATCH_SIZE'] = str(self._batch_size)
                    env['FRAME_TIMEOUT'] = str(self._frame_timeout)
                    env['PYTHONUNBUFFERED'] = '1'
                    
                    # 启动排序器进程
                    f_log.write(f'\n# ========== 启动排序器服务 ==========\n')
                    f_log.write(f'# 时间: {datetime.now().isoformat()}\n')
                    f_log.write(f'# 排序器ID: {self._sorter_id}\n')
                    f_log.write(f'# Python解释器: {sys.executable}\n')
                    f_log.write(f'# 排序器脚本: {sorter_script}\n')
                    f_log.write(f'# 环境变量:\n')
                    for key in ['SORTER_ID', 'SERVICE_NAME', 'PORT', 'SERVER_IP', 'OUTPUT_URL', 'WINDOW_SIZE', 'BATCH_SIZE', 'FRAME_TIMEOUT']:
                        if key in env:
                            f_log.write(f'#   {key}={env[key]}\n')
                    f_log.write(f'# ===================================\n\n')
                    f_log.flush()
                    
                    self._process = subprocess.Popen(
                        [sys.executable, sorter_script],
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
                    
                    # 如果异常退出，等待后重启
                    logger.warning(f'排序器服务异常退出（返回码: {return_code}），将在5秒后重启')
                    f_log.write(f'\n# [{datetime.now().isoformat()}] 排序器服务异常退出（返回码: {return_code}），将在5秒后重启......\n')
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
        """停止排序器"""
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


def find_available_port(start_port: int = 9000, max_attempts: int = 100) -> Optional[int]:
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


def start_sorter(service_name: str, output_url: str, window_size: int = 10, 
                 batch_size: int = 5, frame_timeout: float = 2.0) -> dict:
    """
    启动排序器服务
    
    Args:
        service_name: 服务名称
        output_url: 输出流地址
        window_size: 滑动窗口大小
        batch_size: 批量推送阈值
        frame_timeout: 单个帧超时时间（秒）
    
    Returns:
        dict: 启动结果
    """
    try:
        # 检查是否已存在排序器
        existing_sorter = FrameSorter.query.filter_by(service_name=service_name).first()
        
        if existing_sorter:
            # 如果已存在，检查是否在运行
            if existing_sorter.id in _sorter_daemons:
                daemon = _sorter_daemons[existing_sorter.id]
                if daemon._running:
                    logger.info(f'排序器已运行: {service_name}')
                    return {
                        'code': 0,
                        'msg': '排序器已在运行',
                        'data': existing_sorter.to_dict()
                    }
            
            # 重新启动
            sorter = existing_sorter
            sorter.status = 'stopped'
        else:
            # 创建新的排序器记录
            server_ip = get_local_ip()
            port = find_available_port(9000)
            if not port:
                raise ValueError('无法找到可用端口')
            
            receive_url = f"http://{server_ip}:{port}/receive_frame"
            
            sorter = FrameSorter(
                service_name=service_name,
                receive_url=receive_url,
                output_url=output_url,
                port=port,
                server_ip=server_ip,
                window_size=window_size,
                status='stopped'
            )
            db.session.add(sorter)
            db.session.commit()
        
        # 启动守护进程
        _sorter_daemons[sorter.id] = FrameSorterDaemon(
            sorter_id=sorter.id,
            service_name=sorter.service_name,
            port=sorter.port,
            server_ip=sorter.server_ip,
            output_url=sorter.output_url,
            window_size=sorter.window_size,
            batch_size=batch_size,
            frame_timeout=frame_timeout
        )
        
        sorter.status = 'running'
        db.session.commit()
        
        logger.info(f'排序器启动成功: {service_name}, 接收地址: {sorter.receive_url}')
        
        return {
            'code': 0,
            'msg': '排序器启动成功',
            'data': sorter.to_dict()
        }
        
    except Exception as e:
        logger.error(f'启动排序器失败: {str(e)}', exc_info=True)
        db.session.rollback()
        raise


def stop_sorter(service_name: str) -> dict:
    """停止排序器"""
    try:
        sorter = FrameSorter.query.filter_by(service_name=service_name).first()
        if not sorter:
            return {
                'code': 404,
                'msg': '排序器不存在'
            }
        
        if sorter.id in _sorter_daemons:
            _sorter_daemons[sorter.id].stop()
            del _sorter_daemons[sorter.id]
        
        sorter.status = 'stopped'
        db.session.commit()
        
        return {
            'code': 0,
            'msg': '排序器停止成功'
        }
        
    except Exception as e:
        logger.error(f'停止排序器失败: {str(e)}', exc_info=True)
        db.session.rollback()
        raise


def get_sorter(service_name: str) -> Optional[FrameSorter]:
    """获取排序器"""
    return FrameSorter.query.filter_by(service_name=service_name).first()

