"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import concurrent
import subprocess
import threading
import time
from typing import Optional

class IpReachabilityMonitor:
    class _Monitor:
        def __init__(self, ip: str, default_online: bool = True):
            self.ip = ip
            # 如果设置了默认在线，则先设置为True，否则立即检查IP可达性
            if default_online:
                self.online = True
            else:
                self.online = check_ip_reachable(ip)

    def __init__(self, interval_seconds: Optional[int] = 10):
        self._monitors: dict[str, IpReachabilityMonitor._Monitor] = {}
        self._alive = True
        # 确保 interval_seconds 是整数类型
        if isinstance(interval_seconds, str):
            self._interval_sec = int(interval_seconds)
        else:
            self._interval_sec = int(interval_seconds) if interval_seconds is not None else 10

        def monitor_online_thread():
            def test_online(monitor: IpReachabilityMonitor._Monitor):
                monitor.online = check_ip_reachable(monitor.ip)

            while self._alive:
                wait_muti_run(test_online, self._monitors.values())
                time.sleep(self._interval_sec)

        threading.Thread(target=monitor_online_thread, daemon=True).start()

    def update(self, name: str, ip: str, default_online: bool = True) -> bool:
        """更新或添加设备监控
        
        Args:
            name: 设备名称/ID
            ip: 设备IP地址
            default_online: 是否默认在线（新增设备时默认为True）
        
        Returns:
            设备的在线状态
        """
        monitor = IpReachabilityMonitor._Monitor(ip, default_online=default_online)
        self._monitors[name] = monitor
        return monitor.online

    def delete(self, name: str):
        self._monitors.pop(name, None)

    def is_online(self, name: str) -> bool:
        if name not in self._monitors:
            return False
        return self._monitors[name].online

    def is_watching(self, name: str) -> bool:
        return name in self._monitors

    def stop(self):
        self._alive = False
        del self._monitors

    def set_interval_time(self, sec: int):
        # 确保 sec 是整数类型
        self._interval_sec = int(sec) if isinstance(sec, str) else int(sec)


def check_ip_reachable(ip: str) -> bool:
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '1', ip],
                                capture_output=True, text=True, timeout=2)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def wait_muti_run(func, items):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(func, items)
