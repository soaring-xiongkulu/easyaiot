"""
LLM 研判视频窗口切片服务：按事件时间前后窗口从源录像（MinIO 下载路径）切片。

语义说明：告警录像（record_path）通常为 DVR 按事件预录的事件片段，事件发生在
片段尾部附近。因此默认取"片段末尾 pre+post 秒"作为研判窗口，受 max_seconds 上限
保护；如需精确事件时刻偏移，可由调用方传入 start_offset_seconds（录像内事件偏移）。
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

MAX_SOURCE_BYTES = 512 * 1024 * 1024  # 源录像下载上限 512MB
FFMPEG = os.getenv('LLM_JUDGE_FFMPEG_BIN', 'ffmpeg')
FFPROBE = os.getenv('LLM_JUDGE_FFPROBE_BIN', 'ffprobe')


def download_to_temp(url: str, suffix: str = '.mp4') -> str:
    """下载媒体到临时文件，返回路径（调用方负责删除）。"""
    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    total = 0
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'wb') as out:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                total += len(chunk)
                if total > MAX_SOURCE_BYTES:
                    raise ValueError(f'源媒体超过 {MAX_SOURCE_BYTES} 字节限制: {url}')
                out.write(chunk)
    except Exception:
        if os.path.exists(path):
            os.unlink(path)
        raise
    return path


def probe_duration(path: str) -> Optional[float]:
    """ffprobe 读取视频时长（秒），失败返回 None。"""
    try:
        result = subprocess.run(
            [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', path],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            logger.warning('ffprobe 失败: %s', result.stderr[-500:])
            return None
        return float(result.stdout.strip())
    except Exception as exc:
        logger.warning('ffprobe 异常: %s', exc)
        return None


def slice_tail_window(source_path: str, window_seconds: float, output_path: str) -> bool:
    """截取源视频末尾 window_seconds 秒，重编码输出 mp4。"""
    duration = probe_duration(source_path)
    if not duration or duration <= 0:
        return False
    start = max(0.0, duration - window_seconds)
    cmd = [
        FFMPEG, '-y',
        '-ss', f'{start:.3f}',
        '-i', source_path,
        '-t', f'{window_seconds:.3f}',
        '-c:v', 'libx264', '-preset', 'veryfast',
        '-an', '-movflags', '+faststart',
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.warning('ffmpeg 切片失败: %s', result.stderr[-500:])
            return False
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as exc:
        logger.warning('ffmpeg 切片异常: %s', exc)
        return False


def make_video_clip(
    video_url: str,
    pre_seconds: int,
    post_seconds: int,
    max_seconds: int,
    start_offset_seconds: Optional[float] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """生成研判视频切片。

    Returns:
        (clip_path, error_msg)：clip_path 为 None 时 error_msg 说明原因。
        调用方必须在 finally 中删除 clip_path。
    """
    window = min(pre_seconds + post_seconds, max_seconds)
    if window <= 0:
        return None, '视频窗口为空（pre+post 需大于 0）'
    source_path = None
    try:
        source_path = download_to_temp(video_url, '.mp4')
        duration = probe_duration(source_path)
        if not duration or duration <= 0:
            return None, '无法读取源录像时长'
        if duration <= window:
            # 源本身已短于窗口：整段即为事件片段，直接使用（所有权转交调用方）
            clip_path = source_path
            source_path = None
            return clip_path, None
        fd, clip_path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd)
        if not slice_tail_window(source_path, window, clip_path):
            if os.path.exists(clip_path):
                os.unlink(clip_path)
            return None, '视频窗口切片失败'
        return clip_path, None
    except Exception as exc:
        logger.warning('make_video_clip 异常: %s', exc)
        return None, f'视频处理异常: {exc}'
    finally:
        if source_path and os.path.exists(source_path):
            os.unlink(source_path)
