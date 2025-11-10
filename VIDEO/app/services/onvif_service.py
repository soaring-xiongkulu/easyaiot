"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import onvif
import requests

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, Optional, Union

logger = logging.getLogger(__name__)

class PTZController:
    """统一PTZ控制策略实现"""
    _executor = ThreadPoolExecutor(max_workers=4)  # 共享线程池

    def __init__(self, ptz_svc: onvif.ONVIFService, token: str):
        self._ptz_svc = ptz_svc
        self._token = token
        self._capabilities = self._detect_capabilities()
        logger.info(f"PTZ capabilities detected: {self._capabilities}")

    def _detect_capabilities(self) -> Dict[str, bool]:
        """动态检测设备支持的PTZ功能"""
        try:
            conf = self._ptz_svc.GetConfigurationOptions({'ConfigurationToken': self._token})
            spaces = conf.Spaces
            return {
                'continuous_move': bool(spaces.ContinuousPanTiltVelocitySpace),
                'relative_move': bool(spaces.RelativePanTiltTranslationSpace),
                'zoom': bool(spaces.ContinuousZoomVelocitySpace or spaces.RelativeZoomTranslationSpace)
            }
        except Exception as e:
            logger.error(f"Capability detection failed: {e}")
            return {'continuous_move': False, 'relative_move': False, 'zoom': False}

    def move(self, translation: Iterable[float]):
        """根据设备能力选择移动方式"""
        if not any(translation):
            return

        if self._capabilities['continuous_move']:
            self._execute_threaded(self._continuous_move, translation)
        elif self._capabilities['relative_move']:
            self._relative_move(translation)

    def _execute_threaded(self, func, *args):
        """使用线程池执行任务"""
        future = self._executor.submit(func, *args)
        try:
            future.result(timeout=10)  # 设置超时防止阻塞
        except TimeoutError:
            logger.warning("PTZ operation timed out")

    def _generate_vector(self, translation: Iterable[float]) -> Optional[Dict]:
        """生成PTZ控制向量"""
        vector = {}
        if any(translation[:2]):
            vector['PanTilt'] = {'x': translation[0], 'y': translation[1]}
        if translation[2]:
            vector['Zoom'] = {'x': translation[2]}
        return vector or None

    def _continuous_move(self, translation: Iterable[float]):
        """连续移动实现"""
        duration = max(map(abs, translation))
        scaled = [x / duration for x in translation] if duration > 0 else translation

        vector = self._generate_vector(scaled)
        if not vector:
            return

        try:
            self._ptz_svc.ContinuousMove({
                'ProfileToken': self._token,
                'Velocity': vector
            })
            time.sleep(duration)
            self._ptz_svc.Stop({'ProfileToken': self._token})
        except Exception as e:
            logger.error(f"ContinuousMove failed: {e.fault_string}")

    def _relative_move(self, translation: Iterable[float]):
        """相对移动实现"""
        vector = self._generate_vector(translation)
        if not vector:
            return

        try:
            self._ptz_svc.RelativeMove({
                'ProfileToken': self._token,
                'Translation': vector,
                'Speed': self._generate_vector([1.0, 1.0, 1.0])
            })
        except Exception as e:
            logger.error(f"RelativeMove failed: {e.fault_string}")

    # 预置位管理功能
    def save_preset(self, name: str) -> Optional[str]:
        """保存当前位置为预置位"""
        try:
            response = self._ptz_svc.SetPreset({
                'ProfileToken': self._token,
                'PresetName': name
            })
            return response.PresetToken
        except Exception:
            logger.warning("Preset save not supported")
            return None

    def goto_preset(self, token: str):
        """移动到指定预置位"""
        try:
            self._ptz_svc.GotoPreset({
                'ProfileToken': self._token,
                'PresetToken': token
            })
        except Exception:
            logger.error("Preset move failed")


class OnvifCamera:
    """ONVIF摄像机控制主类"""
    _connection_pool = {}  # 连接池缓存

    def __new__(cls, ip: str, port: Any, username: str, password: str):
        key = f"{ip}:{port}:{username}"
        if key not in cls._connection_pool:
            instance = super().__new__(cls)
            instance._init_camera(ip, port, username, password)
            cls._connection_pool[key] = instance
        return cls._connection_pool[key]

    def _init_camera(self, ip: str, port: Any, username: str, password: str):
        """初始化摄像机连接"""
        try:
            self._camera = onvif.ONVIFCamera(ip, port, username, password, adjust_time=True)
            self._ip = ip
            self._port = int(port)
            self._username = username
            self._password = password

            # 获取设备基础信息
            self._media_svc = self._camera.create_media_service()
            self._media_profile = self._media_svc.GetProfiles()[0]
            self._media_token = self._media_profile.token

            # 初始化PTZ控制器
            try:
                ptz_svc = self._camera.create_ptz_service()
                self._ptz_controller = PTZController(ptz_svc, self._media_profile.PTZConfiguration.token)
            except Exception:
                self._ptz_controller = None
                logger.warning("PTZ service not available")

            # 获取MAC地址
            self._mac = self._camera.devicemgmt.GetNetworkInterfaces()[0].Info.HwAddress
        except Exception as e:
            logger.critical(f"Camera initialization failed: {str(e)}")
            raise ConnectionError("Camera connection failed") from e

    def get_info(self) -> Dict[str, Union[str, bool]]:
        """获取摄像机完整信息字典"""
        dev_info = self._camera.devicemgmt.GetDeviceInformation()

        # 获取视频流URL
        stream_uri = self._media_svc.GetStreamUri({
            'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}},
            'ProfileToken': self._media_token
        }).Uri

        # 处理认证信息嵌入
        if self._username:
            rtsp_url = f"rtsp://{self._username}:{self._password}@{stream_uri.split('//')[1]}"
        else:
            rtsp_url = stream_uri

        return {
            'ip': self._ip,
            'port': self._port,
            'username': self._username,
            'password': self._password,
            'mac': self._mac,
            'manufacturer': dev_info.Manufacturer,
            'model': dev_info.Model,
            'firmware_version': dev_info.FirmwareVersion,
            'serial_number': dev_info.SerialNumber,
            'hardware_id': dev_info.HardwareId,
            'source': rtsp_url,
            'support_move': self._ptz_controller is not None,
            'support_zoom': self._ptz_controller is not None and self._ptz_controller._capabilities['zoom']
        }

    def move(self, translation: Iterable[float]):
        """执行PTZ移动操作"""
        if not self._ptz_controller:
            logger.warning("PTZ not supported")
            return

        try:
            # 检查摄像机状态
            status = self._camera.ptz.GetStatus({'ProfileToken': self._media_token})
            if status.MoveStatus != "IDLE":
                logger.warning("Camera busy, movement skipped")
                return

            self._ptz_controller.move(translation)
        except Exception as e:
            logger.error(f"Move command failed: {e.fault_string}")
        except requests.exceptions.ConnectionError:
            logger.critical("Camera connection lost")

    # 预置位快捷方法
    def save_position(self, name: str) -> Optional[str]:
        """保存当前位置为预置位"""
        return self._ptz_controller.save_preset(name) if self._ptz_controller else None

    def goto_position(self, token: str):
        """移动到指定预置位"""
        if self._ptz_controller:
            self._ptz_controller.goto_preset(token)

    # 视频流获取
    def get_stream_uri(self, protocol: str = 'RTSP') -> str:
        """获取视频流URL"""
        return self._media_svc.GetStreamUri({
            'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': protocol}},
            'ProfileToken': self._media_token
        }).Uri