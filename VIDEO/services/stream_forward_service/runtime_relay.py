"""
RUNTIME forward-only relay supervisor for stream_forward executor=cpp.
One RUNTIME process per device (RTSP -> RTMP codec copy).
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from typing import Any, Callable, Dict, Optional


def _task_executor(task) -> str:
    from app.services.runtime_config_service import normalize_executor
    raw = getattr(task, 'executor', None) if task is not None else os.getenv('STREAM_FORWARD_EXECUTOR', 'cpp')
    return normalize_executor(raw or 'cpp')


def stream_forward_use_runtime(task=None) -> bool:
    return _task_executor(task) == 'cpp'


def start_runtime_relay_process(
    task,
    device_id: str,
    info: dict,
    *,
    device_index: int,
    log_path: str,
    check_rtmp_server_connection: Callable[[str], bool],
    check_and_stop_existing_stream: Callable[[str], None],
    logger,
) -> Optional[subprocess.Popen]:
    from app.services.runtime_config_service import (
        generate_stream_forward_runtime_ini,
        resolve_runtime_bin,
        runtime_library_path_env,
    )

    class _DeviceStub:
        __slots__ = ('id', 'name')

        def __init__(self, did: str, dname: str):
            self.id = did
            self.name = dname

    rtsp_url = (info.get('rtsp_url') or '').strip()
    rtmp_url = (info.get('rtmp_url') or '').strip()
    if not rtsp_url or not rtmp_url:
        return None

    if not check_rtmp_server_connection(rtmp_url):
        logger.warning('设备 %s RTMP/SRS 不可用: %s', device_id, rtmp_url)
        return None

    check_and_stop_existing_stream(rtmp_url)

    device = _DeviceStub(device_id, info.get('device_name') or device_id)
    device_log = os.path.join(log_path, f'runtime_{device_id}')
    os.makedirs(device_log, exist_ok=True)
    try:
        ini_path = generate_stream_forward_runtime_ini(
            task,
            device,
            rtsp_url,
            rtmp_url,
            device_log,
            device_index=device_index,
        )
    except Exception as e:
        logger.error('设备 %s 生成 RUNTIME ini 失败: %s', device_id, e, exc_info=True)
        return None

    runtime_bin = resolve_runtime_bin(task)
    if not runtime_bin or not os.path.isfile(runtime_bin):
        logger.error('RUNTIME 二进制不存在: %s', runtime_bin)
        return None

    env = os.environ.copy()
    env['TASK_ID'] = str(getattr(task, 'id', ''))
    env['LOG_PATH'] = device_log
    env['RUNTIME_BIN'] = runtime_bin
    env['RUNTIME_FORCE_CPU'] = 'true'
    env['RUNTIME_FORCE_SOFT_AV'] = 'true'
    lib_path = runtime_library_path_env()
    if lib_path:
        existing = (env.get('LD_LIBRARY_PATH') or '').strip()
        env['LD_LIBRARY_PATH'] = f'{lib_path}:{existing}' if existing else lib_path

    try:
        proc = subprocess.Popen(
            [runtime_bin, ini_path],
            cwd=os.path.dirname(runtime_bin) or os.getcwd(),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if os.name != 'nt' else None,
        )
        time.sleep(0.5)
        if proc.poll() is not None:
            logger.error('设备 %s RUNTIME forward 启动失败 exit=%s', device_id, proc.returncode)
            return None
        logger.info(
            '设备 %s RUNTIME forward 已启动 PID=%s -> %s (copy)',
            device_id, proc.pid, rtmp_url,
        )
        return proc
    except Exception as e:
        logger.error('设备 %s 启动 RUNTIME forward 失败: %s', device_id, e, exc_info=True)
        return None


def run_runtime_forward_relay_mode(
    *,
    task,
    device_streams: Dict[str, dict],
    stop_event,
    device_pushers: Dict[str, Any],
    logger,
    log_path: str,
    check_rtmp_server_connection: Callable[[str], bool],
    check_and_stop_existing_stream: Callable[[str], None],
    update_task_status: Callable[..., None],
    heartbeat_worker: Callable[[], None],
    mark_quality_success: Optional[Callable[[], None]] = None,
) -> None:
    """Supervise per-device RUNTIME forward processes with auto-restart."""
    restart_delay_sec = max(0.3, float(os.getenv('STREAM_FORWARD_RELAY_RESTART_DELAY_SEC', '0.5')))
    max_backoff_sec = max(restart_delay_sec, float(os.getenv('STREAM_FORWARD_RELAY_MAX_BACKOFF_SEC', '15')))
    stagger_sec = max(0.0, float(os.getenv('STREAM_FORWARD_RELAY_STAGGER_SEC', '0.3')))
    relay_fail_counts: Dict[str, int] = {}
    relay_next_retry: Dict[str, float] = {}
    success_counts: Dict[str, int] = {}

    device_ids_ordered = list(device_streams.keys())
    start_base = time.time()
    for idx, device_id in enumerate(device_ids_ordered):
        relay_fail_counts[device_id] = 0
        relay_next_retry[device_id] = start_base + idx * stagger_sec
        success_counts[device_id] = 0

    logger.info(
        'RUNTIME 高性能推流模式: %d 路, 重启间隔 %.1fs~%.1fs, 错峰 %.1fs/路',
        len(device_streams), restart_delay_sec, max_backoff_sec, stagger_sec,
    )

    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()

    try:
        while not stop_event.is_set():
            now = time.time()
            alive_count = 0

            for idx, device_id in enumerate(device_ids_ordered):
                proc = device_pushers.get(device_id)
                if proc and proc.poll() is None:
                    alive_count += 1
                    relay_fail_counts[device_id] = 0
                    success_counts[device_id] = success_counts.get(device_id, 0) + 1
                    if mark_quality_success and success_counts[device_id] % 60 == 0:
                        mark_quality_success()
                    continue

                if proc is not None and proc.poll() is not None:
                    logger.warning(
                        '设备 %s RUNTIME forward 退出 code=%s',
                        device_id, proc.returncode,
                    )
                    device_pushers.pop(device_id, None)
                    relay_fail_counts[device_id] = relay_fail_counts.get(device_id, 0) + 1
                    backoff = min(
                        max_backoff_sec,
                        restart_delay_sec * (2 ** min(relay_fail_counts[device_id] - 1, 4)),
                    )
                    relay_next_retry[device_id] = now + backoff
                    continue

                if now < relay_next_retry.get(device_id, 0):
                    continue

                new_proc = start_runtime_relay_process(
                    task,
                    device_id,
                    device_streams[device_id],
                    device_index=idx,
                    log_path=log_path,
                    check_rtmp_server_connection=check_rtmp_server_connection,
                    check_and_stop_existing_stream=check_and_stop_existing_stream,
                    logger=logger,
                )
                if new_proc:
                    device_pushers[device_id] = new_proc
                    alive_count += 1
                    relay_fail_counts[device_id] = 0
                else:
                    relay_fail_counts[device_id] = relay_fail_counts.get(device_id, 0) + 1
                    backoff = min(
                        max_backoff_sec,
                        restart_delay_sec * (2 ** min(relay_fail_counts[device_id] - 1, 4)),
                    )
                    relay_next_retry[device_id] = now + backoff

            if alive_count == 0 and len(device_streams) > 0:
                logger.warning('RUNTIME forward 当前无存活进程，继续重试…')

            time.sleep(0.5)
    finally:
        stop_event.set()
        for device_id, proc in list(device_pushers.items()):
            if proc and proc.poll() is None:
                try:
                    if os.name != 'nt':
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    else:
                        proc.terminate()
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            device_pushers.pop(device_id, None)
        try:
            update_task_status(status=0, exception_reason=None)
        except Exception as e:
            logger.warning('更新任务停止状态失败: %s', e)
        logger.info('RUNTIME forward 推流模式已停止')
