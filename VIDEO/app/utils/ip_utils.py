import concurrent
import subprocess
import threading
import time
from typing import Optional

class IpReachabilityMonitor:
    class _Monitor:
        def __init__(self, ip: str):
            self.ip = ip
            self.online = check_ip_reachable(ip)

    def __init__(self, interval_seconds: Optional[int] = 10):
        self._monitors: dict[str, IpReachabilityMonitor._Monitor] = {}
        self._alive = True
        self._interval_sec = interval_seconds

        def monitor_online_thread():
            def test_online(monitor: IpReachabilityMonitor._Monitor):
                monitor.online = check_ip_reachable(monitor.ip)

            while self._alive:
                wait_muti_run(test_online, self._monitors.values())
                time.sleep(self._interval_sec)

        threading.Thread(target=monitor_online_thread, daemon=True).start()

    def update(self, name: str, ip: str) -> bool:
        monitor = IpReachabilityMonitor._Monitor(ip)
        self._monitors[name] = monitor
        return monitor.online

    def delete(self, name: str):
        self._monitors.pop(name, None)

    def is_online(self, name: str) -> bool:
        return self._monitors[name].online

    def is_watching(self, name: str) -> bool:
        return name in self._monitors

    def stop(self):
        self._alive = False
        del self._monitors

    def set_interval_time(self, sec: int):
        self._interval_sec = sec


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
