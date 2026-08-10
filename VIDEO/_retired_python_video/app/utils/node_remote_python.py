"""远程计算节点 Python 启动器路径（bundle 离线运行时）。"""
import os


def resolve_video_bundle_python(bundle_type: str, video_root: str | None = None) -> str:
    """NODE_REMOTE_PYTHON 未设置时，使用 bundle 离线 run-python.sh。"""
    explicit = os.getenv('NODE_REMOTE_PYTHON', '').strip()
    if explicit:
        return explicit
    root = video_root or os.getenv('NODE_REMOTE_VIDEO_ROOT', '/opt/easyaiot/VIDEO')
    return os.path.join(root, '.bundles', bundle_type, 'run-python.sh')


def resolve_ai_bundle_python(ai_root: str | None = None) -> str:
    explicit = os.getenv('NODE_REMOTE_PYTHON', '').strip()
    if explicit:
        return explicit
    root = ai_root or os.getenv('NODE_REMOTE_AI_ROOT', '/opt/easyaiot/AI')
    return os.path.join(root, '.bundles', 'ai_service', 'run-python.sh')
