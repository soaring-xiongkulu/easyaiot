"""edge 单机形态的本机资源监测。

指标直接取宿主机 / 容器可见的 cgroup 与 Linux 资源，不依赖外部监控系统。
网络速率使用相邻两次采样的累计计数差值计算，首个样本速率为 0。
"""
from __future__ import annotations

import os
import platform
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psutil


_NETWORK_LOCK = threading.Lock()
_NETWORK_SAMPLE: Optional[Tuple[float, int, int]] = None


def _round(value: Any, digits: int = 1) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0


def _network_metrics() -> Dict[str, Any]:
    global _NETWORK_SAMPLE
    counters = psutil.net_io_counters()
    now = time.monotonic()
    rx_rate = 0.0
    tx_rate = 0.0
    with _NETWORK_LOCK:
        previous = _NETWORK_SAMPLE
        if previous is not None:
            elapsed = max(now - previous[0], 0.001)
            rx_rate = max(0, counters.bytes_recv - previous[1]) / elapsed
            tx_rate = max(0, counters.bytes_sent - previous[2]) / elapsed
        _NETWORK_SAMPLE = (now, counters.bytes_recv, counters.bytes_sent)
    return {
        'rxBytes': int(counters.bytes_recv),
        'txBytes': int(counters.bytes_sent),
        'rxBytesPerSec': _round(rx_rate),
        'txBytesPerSec': _round(tx_rate),
        'packetsReceived': int(counters.packets_recv),
        'packetsSent': int(counters.packets_sent),
    }


def _temperature_c() -> Optional[float]:
    try:
        groups = psutil.sensors_temperatures(fahrenheit=False) or {}
        preferred = ('soc_thermal', 'cpu_thermal', 'coretemp', 'thermal_zone0')
        readings = []
        for name in preferred:
            readings.extend(groups.get(name) or [])
        if not readings:
            for entries in groups.values():
                readings.extend(entries or [])
        values = [float(item.current) for item in readings if item.current is not None]
        if values:
            return _round(max(values))
    except (AttributeError, OSError):
        pass

    for raw_path in ('/sys/class/thermal/thermal_zone0/temp', '/sys/devices/virtual/thermal/thermal_zone0/temp'):
        try:
            raw = float(Path(raw_path).read_text(encoding='utf-8').strip())
            return _round(raw / 1000.0 if raw > 1000 else raw)
        except (OSError, ValueError):
            continue
    return None


def _disk_metrics() -> Dict[str, Any]:
    candidates = [
        (os.getenv('LOCAL_STORAGE_ROOT') or '').strip(),
        (os.getenv('MEDIA_HOST_DATA_ROOT') or '').strip(),
        '/',
    ]
    target = next((path for path in candidates if path and Path(path).exists()), '/')
    usage = psutil.disk_usage(target)
    return {
        'path': target,
        'percent': _round(usage.percent),
        'usedBytes': int(usage.used),
        'freeBytes': int(usage.free),
        'totalBytes': int(usage.total),
    }


def _runtime_metrics() -> Dict[str, Any]:
    target = (os.getenv('EASYAIOT_RUNTIME_TARGET') or os.getenv('RUNTIME_TARGET') or 'auto').strip().lower()
    try:
        from app.services.runtime_config_service import read_runtime_version_info, resolve_runtime_target

        target = resolve_runtime_target(None)
        info = read_runtime_version_info(runtime_target=target)
    except Exception:
        info = {'ready': False, 'version': None, 'binPath': None}

    enabled = 0
    running = 0
    stream_running = 0
    try:
        from models import AlgorithmTask, AlgorithmTaskStreamRuntime

        enabled = AlgorithmTask.query.filter_by(is_enabled=True).count()
        running = AlgorithmTask.query.filter_by(run_status='running').count()
        stream_running = AlgorithmTaskStreamRuntime.query.filter_by(status='running').count()
    except Exception:
        # 数据库初始化前或单元测试环境中仍返回主机指标。
        pass
    return {
        'target': info.get('target') or target,
        'module': info.get('module'),
        'hardwareOnly': bool(info.get('hardwareOnly')),
        'ready': bool(info.get('ready')),
        'version': info.get('version'),
        'binPath': info.get('binPath'),
        'enabledTasks': enabled,
        'runningTasks': running,
        'runningStreams': stream_running,
    }


def collect_local_metrics() -> Dict[str, Any]:
    """返回一份可直接给 WEB 指标卡消费的本机快照。"""
    cpu_percent = psutil.cpu_percent(interval=None)
    virtual_memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    process = psutil.Process()
    process_memory = process.memory_info()
    boot_time = psutil.boot_time()
    load = os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)

    return {
        'collectedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'host': {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'release': platform.release(),
            'architecture': platform.machine(),
            'uptimeSec': max(0, int(time.time() - boot_time)),
            'bootAt': datetime.fromtimestamp(boot_time, timezone.utc).isoformat().replace('+00:00', 'Z'),
        },
        'cpu': {
            'percent': _round(cpu_percent),
            'logicalCores': int(psutil.cpu_count(logical=True) or 0),
            'physicalCores': int(psutil.cpu_count(logical=False) or 0),
            'load1': _round(load[0], 2),
            'load5': _round(load[1], 2),
            'load15': _round(load[2], 2),
        },
        'memory': {
            'percent': _round(virtual_memory.percent),
            'usedBytes': int(virtual_memory.used),
            'availableBytes': int(virtual_memory.available),
            'totalBytes': int(virtual_memory.total),
            'swapPercent': _round(swap.percent),
        },
        'disk': _disk_metrics(),
        'network': _network_metrics(),
        'temperatureC': _temperature_c(),
        'process': {
            'pid': process.pid,
            'rssBytes': int(process_memory.rss),
            'threads': int(process.num_threads()),
            'processCount': len(psutil.pids()),
        },
        'runtime': _runtime_metrics(),
    }

