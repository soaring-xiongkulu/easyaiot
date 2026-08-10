"""
ONVIF语音对讲服务 - 标准Audio Back Channel实现

基于ONVIF标准协议实现跨品牌的双向语音对讲功能。
支持海康威视、大华、宇视、天地伟业等所有ONVIF认证摄像机。

核心优势：
- 跨品牌兼容（标准ONVIF协议）
- 无需WebRTC复杂信令
- 直接通过RTSP Audio Back Channel推送音频
- 简化架构，降低部署难度

实现流程：
1. 前端麦克风 → 平台 → ONVIF Audio Back Channel → 摄像机扬声器
2. 摄像机麦克风 → RTSP音频流 → 平台 → 前端播放器
"""

import logging
import threading
import time
import socket
import struct
import hashlib
import numpy as np
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from urllib.parse import quote

logger = logging.getLogger(__name__)

# 导入ONVIF Audio Back Channel核心实现
try:
    from app.services.onvif_audio_backchannel import (
        ONVIFAudioBackchannel,
        test_onvif_audio_backchannel,
        AudioEncoder,
        RTPPacketBuilder
    )
    ONVIF_AUDIO_AVAILABLE = True
    logger.info("✓ ONVIF Audio Back Channel模块已加载")
except ImportError as e:
    ONVIF_AUDIO_AVAILABLE = False
    logger.warning(f"⚠ ONVIF Audio Back Channel模块未加载: {e}")


@dataclass
class AudioTalkSessionConfig:
    """语音对讲会话配置"""
    session_id: str
    camera_id: str
    camera_ip: str
    camera_rtsp_port: int = 554
    username: str = "admin"
    password: str = ""
    audio_codec: str = "PCMU"  # PCMU or PCMA
    sample_rate: int = 8000
    channels: int = 1

    # 音频增强参数
    volume_gain: float = 1.0  # 音量增益（0-2.0）
    noise_suppression: bool = True  # 噪音抑制
    echo_cancellation: bool = True  # 回声消除


class ONVIFAudioTalkSession:
    """
    ONVIF语音对讲会话
    
    管理单个摄像机的双向语音对讲会话
    """
    
    def __init__(self, config: AudioTalkSessionConfig):
        """
        初始化语音对讲会话
        
        Args:
            config: 会话配置
        """
        self.config = config
        
        # ONVIF Audio Back Channel客户端
        self.backchannel_client: Optional[ONVIFAudioBackchannel] = None
        
        # 音频发送器
        self.audio_sender: Optional[AudioSender] = None
        
        # 状态
        self.is_active = False
        self.session_id = config.session_id
        
        logger.info(f"ONVIF语音对讲会话已创建: session_id={config.session_id}, camera={config.camera_ip}")
    
    def start(self) -> bool:
        """
        启动语音对讲会话
        
        Returns:
            bool: 是否成功启动
        """
        try:
            logger.info("=" * 80)
            logger.info(f"[启动会话] ONVIF Audio Back Channel: session_id={self.session_id}")
            logger.info("=" * 80)
            
            if not ONVIF_AUDIO_AVAILABLE:
                logger.error("[ERROR] ONVIF Audio Back Channel模块未加载")
                return False
            
            # 步骤1: 创建ONVIF Audio Backchannel客户端
            logger.info("[步骤1] 创建ONVIF Audio Backchannel客户端")
            
            self.backchannel_client = ONVIFAudioBackchannel(
                camera_ip=self.config.camera_ip,
                camera_port=self.config.camera_rtsp_port,
                username=self.config.username,
                password=self.config.password,
                audio_codec=self.config.audio_codec,
                sample_rate=self.config.sample_rate
            )
            
            # 步骤2: 连接RTSP服务器
            logger.info("[步骤2] 连接RTSP服务器")
            
            if not self.backchannel_client.connect():
                logger.error("[ERROR] RTSP连接失败")
                return False
            
            # 步骤3: DESCRIBE - 检测Audio Back Channel支持
            logger.info("[步骤3] RTSP DESCRIBE - 检测Audio Back Channel")
            
            sdp_info = self.backchannel_client.describe_audio_backchannel(audio_path="/audio")
            
            if not sdp_info.get('audio_backchannel_supported'):
                logger.error("[ERROR] 摄像机不支持Audio Back Channel")
                self.backchannel_client.teardown()
                return False
            
            # 步骤4: SETUP - 建立Audio Back Channel（自动选择最佳轨道）
            logger.info("[步骤4] RTSP SETUP - 建立Audio Back Channel")
            
            # 使用智能选择的Audio Back Channel轨道
            audio_track = sdp_info.get('selected_backchannel_track')
            
            if not audio_track:
                logger.error("[ERROR] 智能选择失败，未找到合适的Audio Back Channel轨道")
                self.backchannel_client.teardown()
                return False
            
            # 显示轨道信息
            logger.info(f"[Info] 自动选择的Audio Back Channel轨道:")
            logger.info(f"  - track_id: {audio_track.get('track_id')}")
            logger.info(f"  - mode: {audio_track.get('mode')}")
            logger.info(f"  - codec: {audio_track.get('codec')}")
            logger.info(f"  - payload_type: {audio_track.get('payload_type')}")
            
            # 如果是需要测试的轨道，记录警告
            if audio_track.get('needs_testing'):
                logger.warning("[WARN] 该轨道未经明确标识，需要实际测试SETUP是否成功")
            
            if not self.backchannel_client.setup_audio_backchannel(audio_track):
                logger.error("[ERROR] SETUP失败")
                self.backchannel_client.teardown()
                return False
            
            logger.info(f"[OK] Session ID: {self.backchannel_client.session_id}")
            logger.info(f"[OK] Server RTP端口: {self.backchannel_client.audio_rtp_port}")
            
            # 步骤5: PLAY - 激活音频通道
            logger.info("[步骤5] RTSP PLAY - 激活音频通道")
            
            if not self.backchannel_client.play():
                logger.error("[ERROR] PLAY失败")
                self.backchannel_client.teardown()
                return False
            
            logger.info("[OK] Audio Back Channel已激活")
            
            # 步骤6: 创建音频发送器
            if self.backchannel_client.audio_rtp_port:
                self.audio_sender = AudioSender(
                    camera_ip=self.config.camera_ip,
                    camera_rtp_port=self.backchannel_client.audio_rtp_port,
                    codec=self.config.audio_codec,
                    sample_rate=self.config.sample_rate,
                    volume_gain=self.config.volume_gain,
                    noise_suppression=self.config.noise_suppression
                )
            
            self.is_active = True
            
            logger.info("=" * 80)
            logger.info("[SUCCESS] ✓ ONVIF语音对讲会话已启动")
            logger.info("=" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] 启动会话失败: {e}")
            return False
    
    def stop(self):
        """
        停止语音对讲会话
        """
        try:
            logger.info("=" * 80)
            logger.info(f"[停止会话] ONVIF Audio Back Channel: session_id={self.session_id}")
            logger.info("=" * 80)
            
            # 关闭音频发送器
            if self.audio_sender:
                self.audio_sender.close()
                self.audio_sender = None
            
            # TEARDOWN - 关闭音频通道
            if self.backchannel_client:
                self.backchannel_client.teardown()
                self.backchannel_client = None
            
            self.is_active = False
            
            logger.info("[OK] ✓ ONVIF语音对讲会话已停止")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"[ERROR] 停止会话失败: {e}")
    
    def send_audio(self, pcm_data: bytes) -> bool:
        """
        发送音频数据到摄像机扬声器
        
        Args:
            pcm_data: 16位PCM音频数据
        
        Returns:
            bool: 是否成功发送
        """
        try:
            if not self.is_active or not self.audio_sender:
                logger.warning("[WARN] 会话未激活或音频发送器未初始化")
                return False
            
            # 发送音频数据
            return self.audio_sender.send_audio_data(pcm_data)
            
        except Exception as e:
            logger.error(f"[ERROR] 发送音频失败: {e}")
            return False


class AudioSender:
    """
    音频发送器

    将编码后的音频数据通过RTP发送到摄像机
    """

    def __init__(
        self,
        camera_ip: str,
        camera_rtp_port: int,
        codec: str = "PCMU",
        sample_rate: int = 8000,
        volume_gain: float = 1.0,
        noise_suppression: bool = True
    ):
        """
        初始化音频发送器

        Args:
            camera_ip: 摄像机IP
            camera_rtp_port: 摄像机RTP端口
            codec: 音频编码
            sample_rate: 采样率
            volume_gain: 音量增益（0-2.0）
            noise_suppression: 是否启用噪音抑制
        """
        self.camera_ip = camera_ip
        self.camera_rtp_port = camera_rtp_port
        self.codec = codec
        self.sample_rate = sample_rate
        self.volume_gain = volume_gain
        self.noise_suppression = noise_suppression

        # 创建编码器和RTP构建器
        self.encoder = AudioEncoder(codec=codec)

        # Payload type: 0=PCMU, 8=PCMA
        payload_type = 0 if codec == "PCMU" else 8
        self.rtp_builder = RTPPacketBuilder(payload_type=payload_type, sample_rate=sample_rate)

        # 创建UDP socket（用于发送RTP）
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        logger.info(f"[Sender] 初始化音频发送器: camera={camera_ip}:{camera_rtp_port}, codec={codec}, volume={volume_gain}")

    def apply_audio_enhancement(self, pcm_data: bytes) -> bytes:
        """
        应用音频增强处理（音量增益和噪音抑制）

        Args:
            pcm_data: 16位PCM音频数据

        Returns:
            bytes: 处理后的PCM数据
        """
        # 将PCM数据转换为Int16数组
        samples = np.frombuffer(pcm_data, dtype=np.int16)

        # 1. 应用音量增益
        if self.volume_gain != 1.0:
            samples = samples * self.volume_gain
            # 防止溢出（限制在-32768到32767之间）
            samples = np.clip(samples, -32768, 32767)

        # 2. 噪音抑制（简单的阈值过滤）
        if self.noise_suppression:
            # 设置噪音阈值（小于该绝对值的样本被视为噪音，设为0）
            noise_threshold = 500  # 可根据实际情况调整
            samples = np.where(np.abs(samples) < noise_threshold, 0, samples)

        # 转换回bytes
        return samples.astype(np.int16).tobytes()
    
    def send_audio_data(self, pcm_data: bytes) -> bool:
        """
        发送音频数据
        
        Args:
            pcm_data: 16位PCM音频数据
        
        Returns:
            bool: 是否成功发送
        """
        try:
            # 1. 应用音频增强处理（音量增益、噪音抑制）
            enhanced_pcm_data = self.apply_audio_enhancement(pcm_data)

            # 2. 编码PCM数据
            encoded_data = self.encoder.encode(enhanced_pcm_data)

            # 3. 构建RTP包
            rtp_packet = self.rtp_builder.build_rtp_packet(encoded_data)

            # 4. 发送RTP包到摄像机
            self.rtp_socket.sendto(rtp_packet, (self.camera_ip, self.camera_rtp_port))

            logger.info(f"[Sender] 发送RTP包: {len(rtp_packet)}字节")

            return True

        except Exception as e:
            logger.error(f"[ERROR] 发送音频数据失败: {e}")
            return False
    
    def close(self):
        """
        关闭发送器
        """
        if self.rtp_socket:
            self.rtp_socket.close()
            logger.info("[Sender] 关闭RTP socket")


class ONVIFAudioTalkServiceManager:
    """
    ONVIF语音对讲服务管理器
    
    管理所有摄像机的语音对讲会话
    """
    
    def __init__(self):
        """
        初始化服务管理器
        """
        self.sessions: Dict[str, ONVIFAudioTalkSession] = {}
        logger.info("ONVIF语音对讲服务管理器已创建")
    
    def create_session(
        self,
        session_id: str,
        camera_id: str,
        camera_ip: str,
        camera_rtsp_port: int = 554,
        username: str = "admin",
        password: str = "",
        audio_codec: str = "PCMU",
        sample_rate: int = 8000,
        volume_gain: float = 1.0,
        noise_suppression: bool = True,
        echo_cancellation: bool = True
    ) -> ONVIFAudioTalkSession:
        """
        创建语音对讲会话
        
        Args:
            session_id: 会话ID
            camera_id: 摄像机ID
            camera_ip: 摄像机IP
            camera_rtsp_port: RTSP端口
            username: 用户名
            password: 密码
            audio_codec: 音频编码
            sample_rate: 采样率
            volume_gain: 音量增益（0-2.0）
            noise_suppression: 噪音抑制开关
            echo_cancellation: 回声消除开关
        
        Returns:
            ONVIFAudioTalkSession: 会话实例
        """
        config = AudioTalkSessionConfig(
            session_id=session_id,
            camera_id=camera_id,
            camera_ip=camera_ip,
            camera_rtsp_port=camera_rtsp_port,
            username=username,
            password=password,
            audio_codec=audio_codec,
            sample_rate=sample_rate,
            volume_gain=volume_gain,
            noise_suppression=noise_suppression,
            echo_cancellation=echo_cancellation
        )
        
        session = ONVIFAudioTalkSession(config)
        self.sessions[session_id] = session
        
        logger.info(f"创建语音对讲会话: session_id={session_id}, camera_id={camera_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ONVIFAudioTalkSession]:
        """
        获取语音对讲会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[ONVIFAudioTalkSession]: 会话实例
        """
        return self.sessions.get(session_id)
    
    def start_session(self, session_id: str) -> bool:
        """
        启动语音对讲会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            bool: 是否成功启动
        """
        session = self.sessions.get(session_id)
        
        if session:
            return session.start()
        else:
            logger.error(f"会话不存在: session_id={session_id}")
            return False
    
    def stop_session(self, session_id: str):
        """
        停止语音对讲会话
        
        Args:
            session_id: 会话ID
        """
        session = self.sessions.get(session_id)
        
        if session:
            session.stop()
            del self.sessions[session_id]
            logger.info(f"移除语音对讲会话: session_id={session_id}")
    
    def send_audio_to_session(self, session_id: str, pcm_data: bytes) -> bool:
        """
        发送音频数据到指定会话
        
        Args:
            session_id: 会话ID
            pcm_data: PCM音频数据
        
        Returns:
            bool: 是否成功发送
        """
        session = self.sessions.get(session_id)
        
        if session:
            return session.send_audio(pcm_data)
        else:
            logger.error(f"会话不存在: session_id={session_id}")
            return False
    
    def stop_all_sessions(self):
        """
        停止所有语音对讲会话
        """
        for session_id, session in self.sessions.items():
            session.stop()
        
        self.sessions.clear()
        logger.info("所有语音对讲会话已停止")
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """
        获取所有活动会话
        
        Returns:
            Dict: 活动会话列表
        """
        active_sessions = {}
        
        for session_id, session in self.sessions.items():
            if session.is_active:
                active_sessions[session_id] = {
                    'session_id': session_id,
                    'camera_id': session.config.camera_id,
                    'camera_ip': session.config.camera_ip,
                    'is_active': session.is_active,
                    'audio_codec': session.config.audio_codec,
                    'sample_rate': session.config.sample_rate
                }
        
        return active_sessions


def get_onvif_audio_talk_manager() -> ONVIFAudioTalkServiceManager:
    """
    获取ONVIF语音对讲服务管理器实例
    
    Returns:
        ONVIFAudioTalkServiceManager: 服务管理器实例
    """
    return ONVIFAudioTalkServiceManager()


# 测试代码
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ONVIF语音对讲服务测试')
    parser.add_argument('--ip', required=True, help='摄像机IP地址')
    parser.add_argument('--port', type=int, default=554, help='RTSP端口')
    parser.add_argument('--user', default='admin', help='用户名')
    parser.add_argument('--password', default='', help='密码')
    
    args = parser.parse_args()
    
    # 创建服务管理器
    manager = get_onvif_audio_talk_manager()
    
    # 创建会话
    session_id = "test_session_001"
    session = manager.create_session(
        session_id=session_id,
        camera_id="test_camera",
        camera_ip=args.ip,
        camera_rtsp_port=args.port,
        username=args.user,
        password=args.password
    )
    
    # 启动会话
    if manager.start_session(session_id):
        print(f"✓ 会话已启动: {session_id}")
        
        # 保持连接5秒
        time.sleep(5)
        
        # 停止会话
        manager.stop_session(session_id)
        print(f"✓ 会话已停止: {session_id}")
    else:
        print(f"✗ 会话启动失败: {session_id}")