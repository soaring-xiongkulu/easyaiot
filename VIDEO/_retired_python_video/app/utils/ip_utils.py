"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import concurrent
import subprocess
import sys
import threading
from typing import Optional

# 虚拟网桥 / 容器接口：Docker host 网络上仍存在 docker0、br-*、veth 等，不适合作为给摄像机 / 浏览器的拉流地址
_SKIP_IFACE_PREFIXES = (
    'docker',
    'br-',
    'veth',
    'virbr',
    'vmnet',
    'vboxnet',
)


def _linux_default_route_interface() -> Optional[str]:
    """Linux 下读取默认路由所在网卡（/proc/net/route），host 网络下与宿主机一致。"""
    if not sys.platform.startswith('linux'):
        return None
    try:
        with open('/proc/net/route', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                iface, dest_hex = parts[0], parts[1]
                if dest_hex == '00000000':
                    return iface
    except OSError:
        return None
    return None


def _score_ipv4_for_lan_streaming(ip: str) -> int:
    """局域网播放地址优先私网 IPv4。"""
    octets = ip.split('.')
    if len(octets) != 4:
        return 0
    try:
        a, b = int(octets[0]), int(octets[1])
    except ValueError:
        return 0
    if a == 192 and b == 168:
        return 400
    if a == 10:
        return 350
    if a == 172 and 16 <= b <= 31:
        return 300
    return 100


def resolve_ipv4_for_stream_urls() -> Optional[str]:
    """探测适合写入 RTMP/HTTP 播放地址的宿主机 IPv4。

    VIDEO 在 Docker ``network_mode: host`` 下与宿主机共用网络命名空间，可直接枚举物理网卡 IPv4。
    策略：优先默认路由网卡上的地址 → 私网地址加权 → 跳过常见虚拟桥接接口。
    不可用时返回 ``None``，由调用方继续其它探测方式。
    """
    try:
        import netifaces
    except ImportError:
        return None

    prefer_iface = _linux_default_route_interface()

    def collect(skip_virtual: bool) -> list[tuple[str, str, int]]:
        rows: list[tuple[str, str, int]] = []
        for iface in netifaces.interfaces():
            if skip_virtual and any(iface.startswith(p) for p in _SKIP_IFACE_PREFIXES):
                continue
            try:
                addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
            except ValueError:
                continue
            for addr in addrs:
                ip = addr.get('addr')
                if not ip or ip == '127.0.0.1' or ip.startswith('169.254.'):
                    continue
                score = _score_ipv4_for_lan_streaming(ip)
                if prefer_iface and iface == prefer_iface:
                    score += 500
                rows.append((iface, ip, score))
        return rows

    best: Optional[tuple[str, str, int]] = None
    for skip_virtual in (True, False):
        for row in collect(skip_virtual):
            if best is None or row[2] > best[2] or (row[2] == best[2] and row[1] < best[1]):
                best = row
        if best is not None:
            break

    return best[1] if best else None

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
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        # 确保 interval_seconds 是整数类型
        if isinstance(interval_seconds, str):
            self._interval_sec = int(interval_seconds)
        else:
            self._interval_sec = int(interval_seconds) if interval_seconds is not None else 10

        def monitor_online_thread():
            def test_online(monitor: IpReachabilityMonitor._Monitor):
                monitor.online = check_ip_reachable(monitor.ip)

            while self._alive:
                monitors = list(self._monitors.values())
                if monitors:
                    try:
                        wait_muti_run(test_online, monitors)
                    except RuntimeError:
                        break
                if self._stop_event.wait(self._interval_sec):
                    break

        self._thread = threading.Thread(
            target=monitor_online_thread,
            daemon=True,
            name='ip-reachability-monitor',
        )
        self._thread.start()

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
        if not self._alive:
            return
        self._alive = False
        self._stop_event.set()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=5)
        self._monitors.clear()

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
    if not items:
        return
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(func, items)
    except RuntimeError:
        # 解释器关闭阶段线程池已不可用，忽略即可
        pass
