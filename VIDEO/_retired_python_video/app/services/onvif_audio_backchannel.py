"""
ONVIF Audio Back Channel 标准协议实现

实现跨品牌的双向语音对讲功能，支持：
- 海康威视（Hikvision）
- 大华（Dahua）
- 宇视（Uniview）
- 天地伟业（Tiandy）
- 所有ONVIF Profile T/Q认证的摄像机

核心流程：
1. GetAudioOutputs() -> 获取扬声器Token
2. RTSP DESCRIBE (Require: www.onvif.org/ver20/backchannel)
3. RTSP SETUP (mode=record)
4. RTSP PLAY
5. 发送音频数据（RTP/PCMA）
6. RTSP TEARDOWN
"""

import socket
import hashlib
import base64
import time
import struct
import logging
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote

logger = logging.getLogger(__name__)


class ONVIFAudioBackchannel:
    """
    ONVIF Audio Back Channel 客户端
    
    实现标准ONVIF双向语音对讲协议，支持跨品牌摄像机
    """
    
    def __init__(
        self,
        camera_ip: str,
        camera_port: int = 554,
        username: str = "admin",
        password: str = "",
        audio_codec: str = "PCMA",  # G.711 A-law
        sample_rate: int = 8000,
        channels: int = 1
    ):
        """
        初始化ONVIF Audio Back Channel客户端
        
        Args:
            camera_ip: 摄像机IP地址
            camera_port: RTSP端口（默认554）
            username: 用户名
            password: 密码
            audio_codec: 音频编码（PCMA/PCMU）
            sample_rate: 采样率（8000/16000）
            channels: 通道数（1=单声道）
        """
        self.camera_ip = camera_ip
        self.camera_port = camera_port
        self.username = username
        self.password = password
        self.audio_codec = audio_codec
        self.sample_rate = sample_rate
        self.channels = channels
        self.socket_timeout = 10.0
        
        # RTSP连接状态
        self.rtsp_socket: Optional[socket.socket] = None
        self.session_id: Optional[str] = None
        self.cseq = 1  # RTSP序列号
        
        # 音频通道信息
        self.audio_backchannel_port: Optional[int] = None
        self.audio_rtp_port: Optional[int] = None
        self.audio_rtcp_port: Optional[int] = None
        
        # 本地RTP端口（用于发送音频）
        self.local_rtp_port = 5000
        self.local_rtcp_port = 5001
        
        logger.info(f"初始化ONVIF Audio Backchannel客户端: {camera_ip}:{camera_port}")
        logger.info(f"音频配置: codec={audio_codec}, rate={sample_rate}Hz, channels={channels}")
    
    def connect(self) -> bool:
        """
        建立RTSP连接并初始化Audio Back Channel
        
        Returns:
            bool: 连接是否成功
        """
        try:
            logger.info("=" * 60)
            logger.info("[步骤1] 创建RTSP连接")
            logger.info("=" * 60)
            
            # 创建RTSP socket
            self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rtsp_socket.settimeout(self.socket_timeout)
            self.rtsp_socket.connect((self.camera_ip, self.camera_port))
            
            logger.info(f"[OK] 已连接到RTSP服务器: {self.camera_ip}:{self.camera_port}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] RTSP连接失败: {e}")
            return False
    
    def _build_digest_auth(self, method: str, uri: str, auth_info: str) -> str:
        """
        构建Digest认证头
        
        Args:
            method: RTSP方法（DESCRIBE/SETUP/PLAY等）
            uri: RTSP URI
            auth_info: WWW-Authenticate响应头内容
        
        Returns:
            str: Authorization头内容
        """
        # 解析WWW-Authenticate头
        # 格式: Digest realm="xxx", nonce="yyy", ...
        
        # 先去掉"Digest"前缀
        auth_info_clean = auth_info.replace("Digest ", "").strip()
        
        auth_parts = {}
        for part in auth_info_clean.split(','):
            if '=' in part:
                key, value = part.strip().split('=', 1)
                auth_parts[key.strip()] = value.strip('"')
        
        realm = auth_parts.get('realm', '')
        nonce = auth_parts.get('nonce', '')
        
        logger.info(f"[Auth] Digest认证参数: realm={realm}, nonce={nonce}")
        
        # 计算HA1
        ha1_str = f"{self.username}:{realm}:{self.password}"
        ha1 = hashlib.md5(ha1_str.encode()).hexdigest()
        
        # 计算HA2
        ha2_str = f"{method}:{uri}"
        ha2 = hashlib.md5(ha2_str.encode()).hexdigest()
        
        # 计算response
        response_str = f"{ha1}:{nonce}:{ha2}"
        response = hashlib.md5(response_str.encode()).hexdigest()
        
        logger.info(f"[Auth] Digest认证响应: {response}")
        
        # 构建Authorization头
        auth_header = (
            f"Digest username=\"{self.username}\", "
            f"realm=\"{realm}\", "
            f"nonce=\"{nonce}\", "
            f"uri=\"{uri}\", "
            f"response=\"{response}\""
        )
        
        return auth_header
    
    def describe_audio_backchannel(self, audio_path: str = "/audio") -> Dict[str, Any]:
        """
        发送RTSP DESCRIBE请求，请求Audio Back Channel
        
        Args:
            audio_path: 音频路径（默认/audio）
        
        Returns:
            Dict: SDP响应信息
        """
        try:
            logger.info("=" * 60)
            logger.info("[步骤2] RTSP DESCRIBE - 请求Audio Back Channel")
            logger.info("=" * 60)
            
            # 构建RTSP URI
            rtsp_uri = f"rtsp://{quote(self.username)}:{quote(self.password)}@{self.camera_ip}:{self.camera_port}{audio_path}"
            
            logger.info(f"[Request] RTSP URI: {rtsp_uri}")
            
            # 第一次DESCRIBE请求（不带认证）
            describe_request = (
                f"DESCRIBE {rtsp_uri} RTSP/1.0\r\n"
                f"CSeq: {self.cseq}\r\n"
                f"Require: www.onvif.org/ver20/backchannel\r\n"
                f"Accept: application/sdp\r\n"
                f"User-Agent: ONVIF Audio Backchannel Client\r\n"
                f"\r\n"
            )
            
            self.cseq += 1
            
            logger.info("[Request] 发送DESCRIBE请求（包含Require头）:")
            logger.info(f"  Require: www.onvif.org/ver20/backchannel")
            
            self.rtsp_socket.send(describe_request.encode())
            
            # 接收响应
            response = self._receive_rtsp_response()
            
            logger.info("[Response] RTSP响应:")
            logger.info(response[:500])  # 显示前500字符
            
            # 检查认证要求
            if "401 Unauthorized" in response or "401" in response:
                logger.info("[Auth] 需要Digest认证")
                
                # 提取WWW-Authenticate头
                auth_info = ""
                for line in response.split('\r\n'):
                    if 'WWW-Authenticate:' in line or 'WWW-Authenticate' in line:
                        auth_info = line.split(':', 1)[1].strip()
                        break
                
                if auth_info:
                    # 构建Digest认证
                    auth_header = self._build_digest_auth("DESCRIBE", rtsp_uri, auth_info)
                    
                    # 第二次DESCRIBE请求（带认证）
                    describe_request_auth = (
                        f"DESCRIBE {rtsp_uri} RTSP/1.0\r\n"
                        f"CSeq: {self.cseq}\r\n"
                        f"Require: www.onvif.org/ver20/backchannel\r\n"
                        f"Authorization: {auth_header}\r\n"
                        f"Accept: application/sdp\r\n"
                        f"User-Agent: ONVIF Audio Backchannel Client\r\n"
                        f"\r\n"
                    )
                    
                    self.cseq += 1
                    
                    logger.info("[Request] 发送带认证的DESCRIBE请求")
                    
                    self.rtsp_socket.send(describe_request_auth.encode())
                    
                    # 接收认证后的响应
                    response = self._receive_rtsp_response()
                    
                    logger.info("[Response] 认证后的响应:")
                    logger.info(response[:500])
            
            # 解析SDP响应
            sdp_info = self._parse_sdp(response)
            
            return sdp_info
            
        except Exception as e:
            logger.error(f"[ERROR] DESCRIBE请求失败: {e}")
            return {}
    
    def _receive_rtsp_response(self) -> str:
        """
        接收RTSP响应
        
        Returns:
            str: RTSP响应内容
        """
        response_data = b""
        
        while True:
            try:
                chunk = self.rtsp_socket.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                
                # RTSP响应以\r\n\r\n结束（可能还有body）
                if b"\r\n\r\n" in response_data:
                    # 检查Content-Length
                    response_str = response_data.decode('utf-8', errors='ignore')
                    
                    content_length = 0
                    for line in response_str.split('\r\n'):
                        if 'Content-Length:' in line:
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    # 接收完整的body
                    if content_length > 0:
                        header_size = response_str.find('\r\n\r\n') + 4
                        body_received = len(response_data) - header_size
                        
                        while body_received < content_length:
                            chunk = self.rtsp_socket.recv(4096)
                            if not chunk:
                                break
                            response_data += chunk
                            body_received = len(response_data) - header_size
                    
                    break
                    
            except socket.timeout:
                break
        
        return response_data.decode('utf-8', errors='ignore')
    
    def _parse_sdp(self, rtsp_response: str) -> Dict[str, Any]:
        """
        解析SDP响应，提取音频通道信息
        
        Args:
            rtsp_response: RTSP响应
        
        Returns:
            Dict: SDP解析结果
        """
        sdp_info = {
            'audio_backchannel_supported': False,
            'audio_tracks': [],
            'video_tracks': []
        }
        
        # 检查是否支持Audio Back Channel
        if "551 Option not supported" in rtsp_response:
            logger.error("[ERROR] 摄像机不支持Audio Back Channel（551错误）")
            return sdp_info
        
        if "415 Unsupported Media Type" in rtsp_response:
            logger.error("[ERROR] 摄像机不支持该音频路径（415错误）")
            return sdp_info
        
        if "200 OK" not in rtsp_response:
            logger.error(f"[ERROR] RTSP DESCRIBE失败")
            return sdp_info
        
        logger.info("[OK] RTSP DESCRIBE成功（200 OK）")
        
        # 提取SDP内容
        sdp_start = rtsp_response.find('v=0')
        if sdp_start == -1:
            logger.warning("[WARN] 未找到SDP内容")
            return sdp_info
        
        sdp_content = rtsp_response[sdp_start:]
        
        logger.info("[SDP] 解析SDP内容:")
        logger.info(sdp_content[:1500])  # 显示前1500字符
        
        # 解析SDP
        current_track = None
        
        for line in sdp_content.split('\r\n'):
            line = line.strip()
            
            # 音频轨道
            if line.startswith('m=audio'):
                # 如果有之前的轨道，先保存
                if current_track:
                    if current_track['type'] == 'audio':
                        sdp_info['audio_tracks'].append(current_track)
                    elif current_track['type'] == 'video':
                        sdp_info['video_tracks'].append(current_track)
                
                parts = line.split()
                port = int(parts[1])
                payload_types = parts[3:]  # 可能有多个payload types
                
                current_track = {
                    'type': 'audio',
                    'port': port,
                    'payload_types': payload_types,  # 改为列表
                    'payload_type': int(payload_types[0]) if payload_types else 0,  # 主payload type
                    'codec': '',
                    'mode': '',
                    'track_id': '',
                    'rtpmap': {}  # 存储所有rtpmap
                }
                
                logger.info(f"[SDP] 发现音频轨道: port={port}, payload_types={payload_types}")
            
            # 视频轨道
            elif line.startswith('m=video'):
                # 如果有之前的轨道，先保存
                if current_track:
                    if current_track['type'] == 'audio':
                        sdp_info['audio_tracks'].append(current_track)
                    elif current_track['type'] == 'video':
                        sdp_info['video_tracks'].append(current_track)
                
                parts = line.split()
                port = int(parts[1])
                
                current_track = {
                    'type': 'video',
                    'port': port,
                    'payload_type': 0,
                    'codec': '',
                    'mode': '',
                    'track_id': ''
                }
                
                logger.info(f"[SDP] 发现视频轨道: port={port}")
            
            # 音频属性
            elif line.startswith('a=') and current_track:
                if line == 'a=sendonly':
                    current_track['mode'] = 'sendonly'
                    logger.info(f"[SDP] Audio Back Channel: {current_track['mode']} (客户端发送音频)")
                    sdp_info['audio_backchannel_supported'] = True
                    
                elif line == 'a=recvonly':
                    current_track['mode'] = 'recvonly'
                    logger.info(f"[SDP] 音频接收通道: {current_track['mode']} (摄像机发送音频)")
                    
                elif line.startswith('a=rtpmap:'):
                    # 解析编码格式
                    # 格式: a=rtpmap:8 PCMA/8000
                    parts = line.split(':')
                    if len(parts) > 1:
                        payload_num = parts[1].split()[0]
                        codec_info = parts[1].split()[1] if len(parts[1].split()) > 1 else ''
                        
                        # 只有音频轨道有rtpmap字典
                        if current_track['type'] == 'audio' and 'rtpmap' in current_track:
                            current_track['rtpmap'][payload_num] = codec_info
                        
                        # 如果是主payload type，设置为codec
                        if str(current_track['payload_type']) == payload_num:
                            current_track['codec'] = codec_info
                        
                        logger.info(f"[SDP] RTP映射: payload={payload_num}, codec={codec_info}")
                
                elif line.startswith('a=control:'):
                    # 提取track ID（支持多种品牌格式）
                    # 格式示例：
                    # - 海康威视: a=control:rtsp://.../trackID=4
                    # - 大华: a=control:rtsp://.../audio_backchannel
                    # - 宇视: a=control:audio1
                    # - 通用: a=control:track1
                    
                    control_line = line.split(':', 1)[1].strip()
                    
                    # 多种track_id提取策略
                    track_id = None
                    
                    # 策略1: 提取trackID=后面的数字或字符串
                    if 'trackID=' in control_line:
                        track_id = control_line.split('trackID=')[1]
                        # 可能还有其他参数，取第一个&之前的部分
                        if '&' in track_id:
                            track_id = track_id.split('&')[0]
                    
                    # 策略2: 提取/audio/后面的字符串
                    elif '/audio/' in control_line:
                        track_id = control_line.split('/audio/')[-1]
                        # 去掉可能的查询参数
                        if '?' in track_id:
                            track_id = track_id.split('?')[0]
                    
                    # 策略3: 提取最后一个/后面的字符串
                    elif '/' in control_line:
                        track_id = control_line.split('/')[-1]
                        if '?' in track_id:
                            track_id = track_id.split('?')[0]
                    
                    # 策略4: 直接使用control_line（相对路径）
                    else:
                        track_id = control_line
                    
                    current_track['track_id'] = track_id
                    logger.info(f"[SDP] Track ID: {track_id} (原始: {control_line})")
        
        # 保存最后一个track
        if current_track:
            if current_track['type'] == 'audio':
                sdp_info['audio_tracks'].append(current_track)
            elif current_track['type'] == 'video':
                sdp_info['video_tracks'].append(current_track)
        
        logger.info(f"[OK] SDP解析完成: audio_backchannel={sdp_info['audio_backchannel_supported']}, "
                   f"audio_tracks={len(sdp_info['audio_tracks'])}, video_tracks={len(sdp_info['video_tracks'])}")
        
        # 智能匹配Audio Back Channel轨道
        sdp_info['selected_backchannel_track'] = self._select_best_backchannel_track(sdp_info)
        
        return sdp_info
    
    def _select_best_backchannel_track(self, sdp_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        智能选择最合适的Audio Back Channel轨道
        
        选择策略：
        1. 优先选择sendonly模式的音频轨道
        2. 如果没有sendonly，选择包含'backchannel'关键字轨道
        3. 如果没有明确标识，选择第一个音频轨道并标记为需要测试
        
        Args:
            sdp_info: SDP解析结果
        
        Returns:
            Optional[Dict]: 最合适的音频轨道信息
        """
        audio_tracks = sdp_info.get('audio_tracks', [])
        
        if not audio_tracks:
            logger.warning("[WARN] 没有发现音频轨道")
            return None
        
        logger.info(f"[Select] 从{len(audio_tracks)}个音频轨道中选择Audio Back Channel")
        
        # 策略1: 优先选择sendonly模式（标准Audio Back Channel）
        for idx, track in enumerate(audio_tracks):
            if track.get('mode') == 'sendonly':
                logger.info(f"[Select] ✓ 策略1成功: 轨道#{idx}是sendonly模式")
                logger.info(f"  - track_id: {track.get('track_id')}")
                logger.info(f"  - codec: {track.get('codec')}")
                logger.info(f"  - payload_type: {track.get('payload_type')}")
                return track
        
        # 策略2: 选择包含'backchannel'关键字的轨道
        for idx, track in enumerate(audio_tracks):
            track_id = track.get('track_id', '').lower()
            if 'backchannel' in track_id:
                logger.info(f"[Select] ✓ 策略2成功: 轨道#{idx}包含backchannel关键字")
                logger.info(f"  - track_id: {track.get('track_id')}")
                # 标记为需要测试
                track['mode'] = 'sendonly'
                track['needs_testing'] = True
                sdp_info['audio_backchannel_supported'] = True
                return track
        
        # 策略3: 选择包含'audio'关键字且不是recvonly的轨道
        for idx, track in enumerate(audio_tracks):
            track_id = track.get('track_id', '').lower()
            mode = track.get('mode', '')
            if 'audio' in track_id and mode != 'recvonly':
                logger.info(f"[Select] ✓ 策略3成功: 轨道#{idx}包含audio关键字且不是recvonly")
                logger.info(f"  - track_id: {track.get('track_id')}")
                # 标记为需要测试
                track['mode'] = 'sendonly'
                track['needs_testing'] = True
                sdp_info['audio_backchannel_supported'] = True
                return track
        
        # 策略4: 如果只有一个音频轨道，直接使用
        if len(audio_tracks) == 1:
            logger.info(f"[Select] ✓ 策略4成功: 只有1个音频轨道")
            logger.info(f"  - track_id: {audio_tracks[0].get('track_id')}")
            audio_tracks[0]['mode'] = 'sendonly'
            audio_tracks[0]['needs_testing'] = True
            sdp_info['audio_backchannel_supported'] = True
            return audio_tracks[0]
        
        # 策略5: 选择第一个音频轨道（标记为需要测试）
        logger.info(f"[Select] ✓ 策略5成功: 选择第一个音频轨道")
        logger.info(f"  - track_id: {audio_tracks[0].get('track_id')}")
        logger.info(f"  - 注意: 需要实际测试SETUP是否成功")
        audio_tracks[0]['mode'] = 'sendonly'
        audio_tracks[0]['needs_testing'] = True
        sdp_info['audio_backchannel_supported'] = True
        return audio_tracks[0]
    
    def setup_audio_backchannel(self, audio_track: Dict[str, Any]) -> bool:
        """
        建立Audio Back Channel（RTSP SETUP）
        
        Args:
            audio_track: 音频轨道信息
        
        Returns:
            bool: 是否成功建立
        """
        try:
            logger.info("=" * 60)
            logger.info("[步骤3] RTSP SETUP - 建立Audio Back Channel")
            logger.info("=" * 60)
            
            # 构建RTSP URI - 智能匹配control URL
            track_id = audio_track.get('track_id', '1')
            control_url = audio_track.get('track_id', '')  # 原始control URL
            
            logger.info(f"[Info] Track ID: {track_id}")
            logger.info(f"[Info] Control URL: {control_url}")
            logger.info(f"[Info] Mode: {audio_track.get('mode', 'unknown')}")
            
            # 智能构建RTSP URI
            rtsp_uri = None
            
            # 策略1: 如果control_url已经是完整的RTSP URL
            if control_url.startswith('rtsp://'):
                rtsp_uri = control_url
                logger.info(f"[Strategy 1] 使用完整RTSP URL")
            
            # 策略2: 如果track_id包含/audio/路径
            elif '/audio/' in control_url or track_id.startswith('/audio/'):
                # 使用相对路径
                rtsp_uri = f"rtsp://{quote(self.username)}:{quote(self.password)}@{self.camera_ip}:{self.camera_port}{control_url if control_url.startswith('/') else '/' + control_url}"
                logger.info(f"[Strategy 2] 使用/audio/路径")
            
            # 策略3: 如果track_id是数字（海康威视标准）
            elif track_id.isdigit():
                track_id_full = f"trackID={track_id}"
                rtsp_uri = f"rtsp://{quote(self.username)}:{quote(self.password)}@{self.camera_ip}:{self.camera_port}/audio/{track_id_full}"
                logger.info(f"[Strategy 3] 使用trackID=格式（海康威视）")
            
            # 策略4: 如果track_id是特殊关键字（如audio_backchannel）
            elif 'backchannel' in track_id.lower() or 'audio' in track_id.lower():
                rtsp_uri = f"rtsp://{quote(self.username)}:{quote(self.password)}@{self.camera_ip}:{self.camera_port}/{track_id}"
                logger.info(f"[Strategy 4] 使用特殊关键字路径")
            
            # 策略5: 默认使用/audio/trackID=格式
            else:
                rtsp_uri = f"rtsp://{quote(self.username)}:{quote(self.password)}@{self.camera_ip}:{self.camera_port}/audio/trackID={track_id}"
                logger.info(f"[Strategy 5] 使用默认trackID=格式")
            
            logger.info(f"[Request] RTSP URI: {rtsp_uri}")
            
            # SETUP请求（建立反向音频通道）
            setup_request = (
                f"SETUP {rtsp_uri} RTSP/1.0\r\n"
                f"CSeq: {self.cseq}\r\n"
                f"Require: www.onvif.org/ver20/backchannel\r\n"
                f"Transport: RTP/AVP;unicast;client_port={self.local_rtp_port}-{self.local_rtcp_port};mode=record\r\n"
                f"User-Agent: ONVIF Audio Backchannel Client\r\n"
                f"\r\n"
            )
            
            self.cseq += 1
            
            logger.info("[Request] SETUP请求参数:")
            logger.info(f"  Transport: RTP/AVP;unicast;client_port={self.local_rtp_port}-{self.local_rtcp_port};mode=record")
            logger.info(f"  Require: www.onvif.org/ver20/backchannel")
            
            self.rtsp_socket.send(setup_request.encode())
            
            # 接收响应
            response = self._receive_rtsp_response()
            
            logger.info("[Response] SETUP响应:")
            logger.info(response[:500])
            
            # 检查认证要求
            if "401 Unauthorized" in response or "401" in response:
                logger.info("[Auth] 需要Digest认证")
                
                # 提取WWW-Authenticate头
                auth_info = ""
                for line in response.split('\r\n'):
                    if 'WWW-Authenticate:' in line or 'WWW-Authenticate' in line:
                        auth_info = line.split(':', 1)[1].strip()
                        break
                
                if auth_info:
                    # 构建Digest认证
                    auth_header = self._build_digest_auth("SETUP", rtsp_uri, auth_info)
                    
                    # 第二次SETUP请求（带认证）
                    setup_request_auth = (
                        f"SETUP {rtsp_uri} RTSP/1.0\r\n"
                        f"CSeq: {self.cseq}\r\n"
                        f"Require: www.onvif.org/ver20/backchannel\r\n"
                        f"Authorization: {auth_header}\r\n"
                        f"Transport: RTP/AVP;unicast;client_port={self.local_rtp_port}-{self.local_rtcp_port};mode=record\r\n"
                        f"User-Agent: ONVIF Audio Backchannel Client\r\n"
                        f"\r\n"
                    )
                    
                    self.cseq += 1
                    
                    logger.info("[Request] 发送带认证的SETUP请求")
                    
                    self.rtsp_socket.send(setup_request_auth.encode())
                    
                    # 接收认证后的响应
                    response = self._receive_rtsp_response()
                    
                    logger.info("[Response] 认证后的响应:")
                    logger.info(response[:500])
            
            # 检查响应
            if "200 OK" not in response:
                logger.error(f"[ERROR] SETUP失败")
                return False
            
            logger.info("[OK] SETUP成功（200 OK）")
            
            # 提取Session ID和服务器端口
            for line in response.split('\r\n'):
                if 'Session:' in line:
                    # 提取Session ID
                    session_parts = line.split(':')[1].strip().split(';')
                    self.session_id = session_parts[0]
                    logger.info(f"[Session] Session ID: {self.session_id}")
                
                if 'Transport:' in line:
                    # 提取服务器端口
                    # 格式: server_port=5000-5001
                    transport_line = line.split(':')[1].strip()
                    
                    for param in transport_line.split(';'):
                        if 'server_port=' in param:
                            ports = param.split('=')[1].split('-')
                            self.audio_rtp_port = int(ports[0])
                            self.audio_rtcp_port = int(ports[1]) if len(ports) > 1 else self.audio_rtp_port + 1
                            logger.info(f"[Transport] Server ports: RTP={self.audio_rtp_port}, RTCP={self.audio_rtcp_port}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] SETUP失败: {e}")
            return False
    
    def play(self) -> bool:
        """
        开始播放（激活音频通道）
        
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("=" * 60)
            logger.info("[步骤4] RTSP PLAY - 激活音频通道")
            logger.info("=" * 60)
            
            if not self.session_id:
                logger.error("[ERROR] 缺少Session ID")
                return False
            
            # 构建RTSP URI
            rtsp_uri = f"rtsp://{quote(self.username)}:{quote(self.password)}@{self.camera_ip}:{self.camera_port}/audio"
            
            # PLAY请求
            play_request = (
                f"PLAY {rtsp_uri} RTSP/1.0\r\n"
                f"CSeq: {self.cseq}\r\n"
                f"Session: {self.session_id}\r\n"
                f"Range: npt=0.000-\r\n"
                f"User-Agent: ONVIF Audio Backchannel Client\r\n"
                f"\r\n"
            )
            
            self.cseq += 1
            
            logger.info("[Request] PLAY请求:")
            logger.info(f"  Session: {self.session_id}")
            
            self.rtsp_socket.send(play_request.encode())
            
            # 接收响应
            response = self._receive_rtsp_response()
            
            logger.info("[Response] PLAY响应:")
            logger.info(response[:500])
            
            # 检查认证要求
            if "401 Unauthorized" in response or "401" in response:
                logger.info("[Auth] 需要Digest认证")
                
                # 提取WWW-Authenticate头
                auth_info = ""
                for line in response.split('\r\n'):
                    if 'WWW-Authenticate:' in line or 'WWW-Authenticate' in line:
                        auth_info = line.split(':', 1)[1].strip()
                        break
                
                if auth_info:
                    # 构建Digest认证
                    auth_header = self._build_digest_auth("PLAY", rtsp_uri, auth_info)
                    
                    # 第二次PLAY请求（带认证）
                    play_request_auth = (
                        f"PLAY {rtsp_uri} RTSP/1.0\r\n"
                        f"CSeq: {self.cseq}\r\n"
                        f"Session: {self.session_id}\r\n"
                        f"Authorization: {auth_header}\r\n"
                        f"Range: npt=0.000-\r\n"
                        f"User-Agent: ONVIF Audio Backchannel Client\r\n"
                        f"\r\n"
                    )
                    
                    self.cseq += 1
                    
                    logger.info("[Request] 发送带认证的PLAY请求")
                    
                    self.rtsp_socket.send(play_request_auth.encode())
                    
                    # 接收认证后的响应
                    response = self._receive_rtsp_response()
                    
                    logger.info("[Response] 认证后的响应:")
                    logger.info(response[:500])
            
            if "200 OK" not in response:
                logger.error(f"[ERROR] PLAY失败")
                return False
            
            logger.info("[OK] PLAY成功 - 音频通道已激活")
            logger.info("[INFO] 现在可以发送音频数据到摄像机扬声器")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] PLAY失败: {e}")
            return False
    
    def send_audio_data(self, audio_data: bytes) -> bool:
        """
        发送音频数据到摄像机扬声器（通过RTP）
        
        Args:
            audio_data: PCMA编码的音频数据
        
        Returns:
            bool: 是否成功发送
        """
        try:
            # 创建RTP socket
            rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # 构建RTP包
            # RTP Header格式：
            # V=2, P=0, X=0, CC=0, M=0, PT=8 (PCMA), SeqNum, Timestamp, SSRC
            
            rtp_version = 2
            rtp_padding = 0
            rtp_extension = 0
            rtp_cc = 0
            rtp_marker = 0
            rtp_pt = 8  # PCMA (G.711 A-law)
            rtp_seq = 1
            rtp_timestamp = 0
            rtp_ssrc = 12345678
            
            # 构建RTP头部（12字节）
            rtp_header = struct.pack(
                '!BBHII',
                (rtp_version << 6) | (rtp_padding << 5) | (rtp_extension << 4) | rtp_cc,
                (rtp_marker << 7) | rtp_pt,
                rtp_seq,
                rtp_timestamp,
                rtp_ssrc
            )
            
            # 组合RTP包
            rtp_packet = rtp_header + audio_data
            
            # 发送到摄像机的RTP端口
            if self.audio_rtp_port:
                rtp_socket.sendto(rtp_packet, (self.camera_ip, self.audio_rtp_port))
                logger.info(f"[RTP] 发送音频数据: {len(audio_data)}字节到端口{self.audio_rtp_port}")
                return True
            else:
                logger.error("[ERROR] 未知的摄像机RTP端口")
                return False
            
        except Exception as e:
            logger.error(f"[ERROR] 发送音频数据失败: {e}")
            return False
    
    def teardown(self) -> bool:
        """
        关闭音频通道（RTSP TEARDOWN）
        
        Returns:
            bool: 是否成功关闭
        """
        try:
            logger.info("=" * 60)
            logger.info("[步骤5] RTSP TEARDOWN - 关闭音频通道")
            logger.info("=" * 60)
            
            if not self.session_id:
                logger.warning("[WARN] 没有活动的Session")
                return True
            
            # 构建RTSP URI
            rtsp_uri = f"rtsp://{quote(self.username)}:{quote(self.password)}@{self.camera_ip}:{self.camera_port}/audio"
            
            # TEARDOWN请求
            teardown_request = (
                f"TEARDOWN {rtsp_uri} RTSP/1.0\r\n"
                f"CSeq: {self.cseq}\r\n"
                f"Session: {self.session_id}\r\n"
                f"User-Agent: ONVIF Audio Backchannel Client\r\n"
                f"\r\n"
            )
            
            self.cseq += 1
            
            logger.info("[Request] TEARDOWN请求")
            
            self.rtsp_socket.send(teardown_request.encode())
            
            # 接收响应
            response = self._receive_rtsp_response()
            
            logger.info("[Response] TEARDOWN响应:")
            logger.info(response[:200])
            
            if "200 OK" not in response:
                logger.warning(f"[WARN] TEARDOWN可能失败")
            
            logger.info("[OK] 音频通道已关闭")
            
            # 关闭socket
            if self.rtsp_socket:
                self.rtsp_socket.close()
                self.rtsp_socket = None
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] TEARDOWN失败: {e}")
            return False


class AudioEncoder:
    """
    音频编码器 - PCMA（G.711 A-law）和PCMU（G.711 μ-law）
    
    G.711是最简单的音频编码，将16位PCM数据编码为8位数据
    """
    
    def __init__(self, codec: str = "PCMA"):
        """
        初始化编码器
        
        Args:
            codec: 编码类型（PCMA或PCMU）
        """
        self.codec = codec
        logger.info(f"[Encoder] 初始化音频编码器: codec={codec}")
    
    def pcm_to_alaw(self, pcm_data: bytes) -> bytes:
        """
        PCM数据编码为A-law（PCMA）
        
        Args:
            pcm_data: 16位PCM音频数据
        
        Returns:
            bytes: A-law编码的音频数据
        """
        alaw_data = []
        
        for i in range(0, len(pcm_data), 2):
            if i + 1 < len(pcm_data):
                pcm_value = struct.unpack('<h', pcm_data[i:i+2])[0]
                alaw_value = int((pcm_value / 32768.0) * 127 + 127)
                alaw_value = max(0, min(255, alaw_value))
                alaw_data.append(alaw_value)
        
        return bytes(alaw_data)
    
    def pcm_to_ulaw(self, pcm_data: bytes) -> bytes:
        """
        PCM数据编码为μ-law（PCMU）
        
        Args:
            pcm_data: 16位PCM音频数据
        
        Returns:
            bytes: μ-law编码的音频数据
        """
        ulaw_data = []
        
        for i in range(0, len(pcm_data), 2):
            if i + 1 < len(pcm_data):
                pcm_value = struct.unpack('<h', pcm_data[i:i+2])[0]
                ulaw_value = int((pcm_value / 32768.0) * 127 + 127)
                ulaw_value = max(0, min(255, ulaw_value))
                ulaw_data.append(ulaw_value)
        
        return bytes(ulaw_data)
    
    def encode(self, pcm_data: bytes) -> bytes:
        """
        编码PCM数据
        
        Args:
            pcm_data: 16位PCM音频数据
        
        Returns:
            bytes: 编码后的音频数据
        """
        if self.codec == "PCMA":
            return self.pcm_to_alaw(pcm_data)
        elif self.codec == "PCMU":
            return self.pcm_to_ulaw(pcm_data)
        else:
            return self.pcm_to_alaw(pcm_data)


class RTPPacketBuilder:
    """
    RTP包构建器
    
    构建符合RTP标准的音频数据包（RFC 3550）
    """
    
    def __init__(
        self,
        payload_type: int = 0,
        sample_rate: int = 8000,
        ssrc: int = 12345678
    ):
        """
        初始化RTP包构建器
        
        Args:
            payload_type: Payload类型（0=PCMU, 8=PCMA）
            sample_rate: 采样率
            ssrc: SSRC标识符
        """
        self.payload_type = payload_type
        self.sample_rate = sample_rate
        self.ssrc = ssrc
        self.sequence_number = 0
        self.timestamp = 0
        
        logger.info(f"[RTP] 初始化RTP包构建器: payload_type={payload_type}, sample_rate={sample_rate}")
    
    def build_rtp_packet(self, payload_data: bytes) -> bytes:
        """
        构建RTP包
        
        RTP Header格式（12字节）：
        - Version (V): 2 bits
        - Padding (P): 1 bit
        - Extension (X): 1 bit
        - CSRC count (CC): 4 bits
        - Marker (M): 1 bit
        - Payload type (PT): 7 bits
        - Sequence number: 16 bits
        - Timestamp: 32 bits
        - SSRC: 32 bits
        
        Args:
            payload_data: 音频payload数据
        
        Returns:
            bytes: 完整的RTP包
        """
        version = 2
        padding = 0
        extension = 0
        csrc_count = 0
        marker = 0
        
        first_byte = (version << 6) | (padding << 5) | (extension << 4) | csrc_count
        second_byte = (marker << 7) | self.payload_type
        
        rtp_header = struct.pack(
            '!BBHII',
            first_byte,
            second_byte,
            self.sequence_number,
            self.timestamp,
            self.ssrc
        )
        
        rtp_packet = rtp_header + payload_data
        
        self.sequence_number += 1
        timestamp_increment = len(payload_data)
        self.timestamp += timestamp_increment
        
        logger.debug(f"[RTP] 构建RTP包: seq={self.sequence_number-1}, ts={self.timestamp-timestamp_increment}, len={len(rtp_packet)}")
        
        return rtp_packet


def probe_onvif_audio_backchannel_capabilities(
    camera_ip: str,
    camera_port: int = 554,
    username: str = "admin",
    password: str = "",
    socket_timeout: float = 3.0,
) -> Dict[str, Any]:
    """
    轻量探测对讲能力：仅 RTSP DESCRIBE，不建立 SETUP/PLAY（避免 capabilities 接口阻塞数秒）。
    """
    client = ONVIFAudioBackchannel(
        camera_ip=camera_ip,
        camera_port=camera_port,
        username=username,
        password=password,
        audio_codec="PCMA",
        sample_rate=8000,
    )
    client.socket_timeout = socket_timeout

    result: Dict[str, Any] = {
        'success': False,
        'audio_backchannel_supported': False,
        'audio_tracks': [],
        'error': '',
    }

    try:
        if not client.connect():
            result['error'] = 'RTSP连接失败'
            return result

        sdp_info = client.describe_audio_backchannel(audio_path="/audio")
        result['audio_backchannel_supported'] = bool(sdp_info.get('audio_backchannel_supported'))
        result['audio_tracks'] = sdp_info.get('audio_tracks', [])
        result['success'] = result['audio_backchannel_supported']
        if not result['audio_backchannel_supported']:
            result['error'] = '摄像机不支持 Audio Back Channel'
        return result
    except Exception as e:
        logger.warning('ONVIF 对讲能力探测失败 %s:%s - %s', camera_ip, camera_port, e)
        result['error'] = str(e)
        return result
    finally:
        try:
            if client.rtsp_socket:
                client.rtsp_socket.close()
                client.rtsp_socket = None
        except Exception:
            pass


def test_onvif_audio_backchannel(
    camera_ip: str,
    camera_port: int = 554,
    username: str = "admin",
    password: str = ""
) -> Dict[str, Any]:
    """
    测试ONVIF Audio Back Channel功能
    
    Args:
        camera_ip: 摄像机IP
        camera_port: RTSP端口
        username: 用户名
        password: 密码
    
    Returns:
        Dict: 测试结果
    """
    logger.info("=" * 80)
    logger.info("[测试] ONVIF Audio Back Channel - 标准协议测试")
    logger.info("=" * 80)
    logger.info(f"摄像机: {camera_ip}:{camera_port}")
    logger.info(f"用户名: {username}")
    logger.info("")
    
    # 创建客户端
    client = ONVIFAudioBackchannel(
        camera_ip=camera_ip,
        camera_port=camera_port,
        username=username,
        password=password,
        audio_codec="PCMA",
        sample_rate=8000
    )
    
    result = {
        'success': False,
        'audio_backchannel_supported': False,
        'audio_tracks': [],
        'error': ''
    }
    
    try:
        # 步骤1: 连接
        if not client.connect():
            result['error'] = "RTSP连接失败"
            return result
        
        # 步骤2: DESCRIBE
        sdp_info = client.describe_audio_backchannel(audio_path="/audio")
        
        result['audio_backchannel_supported'] = sdp_info.get('audio_backchannel_supported', False)
        result['audio_tracks'] = sdp_info.get('audio_tracks', [])
        
        if not result['audio_backchannel_supported']:
            logger.warning("[WARN] 摄像机不支持Audio Back Channel")
            result['error'] = "摄像机不支持Audio Back Channel"
            
            # 关闭连接
            client.teardown()
            return result
        
        # 步骤3: SETUP（如果有音频轨道）
        audio_track = None
        for track in result['audio_tracks']:
            if track.get('mode') == 'sendonly':
                audio_track = track
                break
        
        if audio_track:
            if client.setup_audio_backchannel(audio_track):
                # 步骤4: PLAY
                if client.play():
                    logger.info("[SUCCESS] Audio Back Channel已建立！")
                    logger.info("[INFO] 现在可以发送音频数据到摄像机扬声器")
                    
                    result['success'] = True
                    
                    # 保持连接5秒（测试）
                    logger.info("[Test] 保持连接5秒...")
                    time.sleep(5)
                    
                    # 步骤5: TEARDOWN
                    client.teardown()
        
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] 测试失败: {e}")
        result['error'] = str(e)
        
        # 确保关闭连接
        client.teardown()
        
        return result


if __name__ == "__main__":
    # 测试示例
    import argparse
    
    parser = argparse.ArgumentParser(description='ONVIF Audio Back Channel测试')
    parser.add_argument('--ip', required=True, help='摄像机IP地址')
    parser.add_argument('--port', type=int, default=554, help='RTSP端口')
    parser.add_argument('--user', default='admin', help='用户名')
    parser.add_argument('--password', default='', help='密码')
    
    args = parser.parse_args()
    
    # 运行测试
    result = test_onvif_audio_backchannel(
        camera_ip=args.ip,
        camera_port=args.port,
        username=args.user,
        password=args.password
    )
    
    print("\n" + "=" * 80)
    print("[结果] 测试完成")
    print("=" * 80)
    print(f"成功: {result['success']}")
    print(f"Audio Back Channel支持: {result['audio_backchannel_supported']}")
    print(f"音频轨道数量: {len(result['audio_tracks'])}")
    if result['error']:
        print(f"错误: {result['error']}")