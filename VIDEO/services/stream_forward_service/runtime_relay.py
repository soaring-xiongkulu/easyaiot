"""
RUNTIME forward-only relay supervisor for stream_forward executor=cpp.
One process per device (RTSP -> RTMP).

H.264 源：RUNTIME/ffmpeg copy（低 CPU）
HEVC 等非 H.264：自动 ffmpeg 转码为 H.264（浏览器 FLV 才能播）
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional


def _task_executor(task) -> str:
    from app.services.runtime_config_service import normalize_executor
    raw = getattr(task, 'executor', None) if task is not None else os.getenv('STREAM_FORWARD_EXECUTOR', 'cpp')
    return normalize_executor(raw or 'cpp')


def stream_forward_use_runtime(task=None) -> bool:
    return _task_executor(task) == 'cpp'


def _resolve_ffmpeg_binary() -> str:
    for key in ('STREAM_FORWARD_FFMPEG', 'FFMPEG_PATH', 'FFMPEG_BIN'):
        raw = (os.getenv(key) or '').strip()
        if raw and os.path.isfile(raw) and os.access(raw, os.X_OK):
            return raw
    conda = (os.getenv('CONDA_PREFIX') or '').strip()
    if conda:
        cand = os.path.join(conda, 'bin', 'ffmpeg')
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    if os.path.isfile('/usr/bin/ffmpeg') and os.access('/usr/bin/ffmpeg', os.X_OK):
        return '/usr/bin/ffmpeg'
    return 'ffmpeg'


def _resolve_ffprobe_binary() -> str:
    ffmpeg = _resolve_ffmpeg_binary()
    if ffmpeg.endswith('ffmpeg'):
        probe = ffmpeg[:-6] + 'ffprobe'
        if os.path.isfile(probe) and os.access(probe, os.X_OK):
            return probe
    if os.path.isfile('/usr/bin/ffprobe') and os.access('/usr/bin/ffprobe', os.X_OK):
        return '/usr/bin/ffprobe'
    return 'ffprobe'


def _is_h264_codec(codec: Optional[str]) -> bool:
    if not codec:
        return False
    return codec.strip().lower() in ('h264', 'avc', 'avc1')


def _video_copy_forced_off() -> bool:
    return os.getenv('STREAM_FORWARD_VIDEO_COPY', 'true').strip().lower() in (
        '0', 'false', 'no', 'off',
    )


def probe_rtsp_video_codec(rtsp_url: str, timeout: float = 10.0) -> Optional[str]:
    """探测 RTSP 主视频轨编码。"""
    try:
        analyzeduration = os.getenv('STREAM_FORWARD_ANALYZEDURATION', '3000000').strip() or '3000000'
        probesize = os.getenv('STREAM_FORWARD_PROBESIZE', '3000000').strip() or '3000000'
        cmd = [
            _resolve_ffprobe_binary(),
            '-hide_banner', '-loglevel', 'error',
            '-rtsp_transport', 'tcp',
            '-analyzeduration', analyzeduration,
            '-probesize', probesize,
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            rtsp_url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            return None
        codec = (result.stdout or '').strip().lower()
        return codec or None
    except Exception:
        return None


def _should_transcode(rtsp_url: str, logger) -> bool:
    if _video_copy_forced_off():
        logger.info('STREAM_FORWARD_VIDEO_COPY=false，强制 H.264 转码')
        return True
    codec = probe_rtsp_video_codec(rtsp_url)
    if not codec:
        logger.warning('RTSP 编码探测失败，先尝试 copy；若浏览器黑屏请设 STREAM_FORWARD_VIDEO_COPY=false')
        return False
    if _is_h264_codec(codec):
        logger.info('RTSP 源编码=%s，使用 copy', codec)
        return False
    logger.info('RTSP 源编码=%s（非 H.264），自动转码为 H.264 以便 Web 播放', codec)
    return True


def _build_transcode_ffmpeg_cmd(rtsp_url: str, rtmp_url: str) -> List[str]:
    analyzeduration = os.getenv('STREAM_FORWARD_ANALYZEDURATION', '2000000').strip() or '2000000'
    probesize = os.getenv('STREAM_FORWARD_PROBESIZE', '2000000').strip() or '2000000'
    # 大屏多路场景：只用 STREAM_FORWARD_*，勿回落全局 FFMPEG_*（常见 3500k/veryfast/25fps 会打满 CPU）
    bitrate = (os.getenv('STREAM_FORWARD_TRANSCODE_BITRATE') or '1200k').strip() or '1200k'
    preset = (os.getenv('STREAM_FORWARD_TRANSCODE_PRESET') or 'ultrafast').strip() or 'ultrafast'
    gop = (os.getenv('STREAM_FORWARD_TRANSCODE_GOP') or '30').strip() or '30'
    fps = (os.getenv('STREAM_FORWARD_TRANSCODE_FPS') or '12').strip() or '12'
    scale = (os.getenv('STREAM_FORWARD_TRANSCODE_SCALE') or '960:540').strip() or '960:540'
    cmd = [
        _resolve_ffmpeg_binary(),
        '-hide_banner', '-nostdin', '-loglevel', 'warning',
        '-rtsp_transport', 'tcp',
        '-analyzeduration', analyzeduration,
        '-probesize', probesize,
        '-i', rtsp_url,
        '-an',
    ]
    if scale and scale.lower() not in ('0', 'off', 'none', 'source', 'native'):
        cmd.extend(['-vf', f'scale={scale}:force_original_aspect_ratio=decrease'])
    cmd.extend([
        '-c:v', 'libx264',
        '-b:v', str(bitrate),
        '-maxrate', str(bitrate),
        '-bufsize', str(bitrate),
        '-preset', str(preset),
        '-tune', 'zerolatency',
        '-profile:v', 'main',
        '-g', str(gop),
        '-bf', '0',
        '-pix_fmt', 'yuv420p',
        '-r', str(fps),
        '-threads', os.getenv('STREAM_FORWARD_TRANSCODE_THREADS', '2'),
        '-avoid_negative_ts', 'make_zero',
        '-muxdelay', '0',
        '-muxpreload', '0',
        '-f', 'flv',
        '-flvflags', 'no_duration_filesize',
        rtmp_url,
    ])
    return cmd


def _popen_relay(cmd: List[str], env: dict, cwd: str, logger, device_id: str, mode: str) -> Optional[subprocess.Popen]:
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if os.name != 'nt' else None,
        )
        time.sleep(0.5)
        if proc.poll() is not None:
            logger.error('设备 %s %s 启动失败 exit=%s', device_id, mode, proc.returncode)
            return None
        logger.info('设备 %s %s 已启动 PID=%s', device_id, mode, proc.pid)
        return proc
    except Exception as e:
        logger.error('设备 %s 启动 %s 失败: %s', device_id, mode, e, exc_info=True)
        return None


def start_ffmpeg_transcode_relay(
    device_id: str,
    info: dict,
    *,
    log_path: str,
    check_rtmp_server_connection: Callable[[str], bool],
    check_and_stop_existing_stream: Callable[[str], None],
    logger,
) -> Optional[subprocess.Popen]:
    rtsp_url = (info.get('rtsp_url') or '').strip()
    rtmp_url = (info.get('rtmp_url') or '').strip()
    if not rtsp_url or not rtmp_url:
        return None
    if not check_rtmp_server_connection(rtmp_url):
        logger.warning('设备 %s RTMP/SRS 不可用: %s', device_id, rtmp_url)
        return None
    check_and_stop_existing_stream(rtmp_url)

    device_log = os.path.join(log_path, f'runtime_{device_id}')
    os.makedirs(device_log, exist_ok=True)
    cmd = _build_transcode_ffmpeg_cmd(rtsp_url, rtmp_url)
    env = os.environ.copy()
    # 系统 ffmpeg 避免 conda LD_LIBRARY_PATH 污染
    if cmd[0] in ('/usr/bin/ffmpeg', 'ffmpeg') or cmd[0].endswith('/ffmpeg'):
        env.pop('LD_LIBRARY_PATH', None)
    logger.info(
        '设备 %s 使用 ffmpeg H.264 转码推流 -> %s',
        device_id, rtmp_url,
    )
    return _popen_relay(cmd, env, device_log, logger, device_id, 'ffmpeg-transcode')


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

    if _should_transcode(rtsp_url, logger):
        return start_ffmpeg_transcode_relay(
            device_id,
            info,
            log_path=log_path,
            check_rtmp_server_connection=check_rtmp_server_connection,
            check_and_stop_existing_stream=check_and_stop_existing_stream,
            logger=logger,
        )

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

    proc = _popen_relay(
        [runtime_bin, ini_path],
        env,
        os.path.dirname(runtime_bin) or os.getcwd(),
        logger,
        device_id,
        f'RUNTIME forward copy -> {rtmp_url}',
    )
    return proc


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
    """Supervise per-device RUNTIME/ffmpeg forward processes with auto-restart."""
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
        'RUNTIME 推流模式: %d 路（H.264 copy / 非 H.264 自动转码）, 重启间隔 %.1fs~%.1fs, 错峰 %.1fs/路',
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
                        '设备 %s forward 退出 code=%s',
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
                logger.warning('forward 当前无存活进程，继续重试…')

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
