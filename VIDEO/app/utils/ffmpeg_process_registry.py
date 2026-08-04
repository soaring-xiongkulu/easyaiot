"""FFmpeg 守护进程注册表操作。"""


def stop_registered_process(processes: dict, lock, device_id: str) -> bool:
    """停止并移除设备对应的守护进程，不存在时保持幂等。"""
    with lock:
        daemon = processes.get(device_id)
        if daemon is None:
            return False
        try:
            daemon.stop()
        finally:
            # 子进程可能已在停止前退出；即使 stop 报错，也不能留下失效注册项。
            processes.pop(device_id, None)
        return True
