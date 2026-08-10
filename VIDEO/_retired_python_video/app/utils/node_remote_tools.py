"""远程计算节点系统工具路径（FFmpeg 等，默认离线安装于 /opt/easyaiot/tools）。"""
import os

FFMPEG_REMOTE_ROOT = os.getenv('NODE_REMOTE_FFMPEG_ROOT', '/opt/easyaiot/tools/ffmpeg')
FFMPEG_REMOTE_BIN = os.path.join(FFMPEG_REMOTE_ROOT, 'bin', 'ffmpeg')
FFPROBE_REMOTE_BIN = os.path.join(FFMPEG_REMOTE_ROOT, 'bin', 'ffprobe')


def apply_remote_toolchain_env(env: dict) -> None:
    """为远程 workload 注入 FFmpeg PATH（bundle 离线安装路径优先）。"""
    ffmpeg = os.getenv('FFMPEG_PATH', '').strip() or FFMPEG_REMOTE_BIN
    ffprobe = os.getenv('FFPROBE_PATH', '').strip() or FFPROBE_REMOTE_BIN
    bin_dir = os.path.dirname(ffmpeg)
    if bin_dir:
        existing = env.get('PATH', os.environ.get('PATH', ''))
        if bin_dir not in existing.split(':'):
            env['PATH'] = f"{bin_dir}:{existing}" if existing else bin_dir
    env.setdefault('FFMPEG_PATH', ffmpeg)
    env.setdefault('FFPROBE_PATH', ffprobe)
