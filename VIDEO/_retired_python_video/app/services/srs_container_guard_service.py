"""
SRS 容器数据目录与当前进程用户一致性检查。

宿主机直跑 VIDEO 时，若 SRS 曾以 root/sudo 创建，compose 中 ~/easyaiot/data 会挂到
/root/easyaiot/data，与当前用户的 $HOME/easyaiot/data 不一致，导致 DVR 录像找不到。
启动时检测到不一致则自动执行 VIDEO/fix_srs.sh 重建容器。
"""
from __future__ import annotations

import logging
import os
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_CONTAINER_NAME = 'srs-server'


def _env_disabled() -> bool:
    return os.getenv('SRS_AUTO_FIX_ON_START', 'true').strip().lower() in (
        '0', 'false', 'no', 'off',
    )


def _running_inside_container() -> bool:
    return os.path.exists('/.dockerenv')


def get_expected_srs_host_data_dir() -> str:
    explicit = (os.getenv('EASYAIOT_HOST_DATA_DIR') or '').strip()
    if explicit:
        return os.path.normpath(os.path.expanduser(os.path.expandvars(explicit)))
    from app.services.media_dvr_utils import DEFAULT_SRS_HOST_DATA_ROOT
    return os.path.normpath(os.path.expanduser(DEFAULT_SRS_HOST_DATA_ROOT))


def get_srs_container_data_mount_source(
    container_name: str = DEFAULT_CONTAINER_NAME,
) -> Optional[str]:
    """返回 SRS 容器 /data 卷在宿主机上的源路径；容器不存在或无法解析时返回 None。"""
    try:
        result = subprocess.run(
            [
                'docker', 'inspect', container_name,
                '--format', '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}',
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.debug('docker inspect SRS 失败: %s', exc)
        return None
    if result.returncode != 0:
        return None
    source = (result.stdout or '').strip()
    return os.path.normpath(source) if source else None


def srs_data_mount_mismatch(container_name: str = DEFAULT_CONTAINER_NAME) -> bool:
    """SRS 已存在且 /data 挂载源路径与当前用户期望目录不一致时返回 True。"""
    actual = get_srs_container_data_mount_source(container_name)
    if not actual:
        return False
    expected = get_expected_srs_host_data_dir()
    return actual != expected


def _video_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_fix_srs_script(timeout: int = 180) -> bool:
    """执行 VIDEO/fix_srs.sh，成功返回 True。"""
    script = os.path.join(_video_root(), 'fix_srs.sh')
    if not os.path.isfile(script):
        logger.warning('未找到 fix_srs.sh: %s', script)
        return False
    try:
        result = subprocess.run(
            ['bash', script],
            cwd=_video_root(),
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.error('执行 fix_srs.sh 失败: %s', exc)
        return False
    if result.returncode != 0:
        logger.error('fix_srs.sh 退出码: %s', result.returncode)
        return False
    return True


def maybe_fix_srs_on_startup(container_name: str = DEFAULT_CONTAINER_NAME) -> None:
    """VIDEO 主进程启动前调用：挂载不一致时自动重建 SRS。"""
    if _env_disabled():
        logger.debug('SRS 启动自检已禁用（SRS_AUTO_FIX_ON_START=false）')
        return
    if _running_inside_container():
        logger.debug('运行于容器内，跳过 SRS 挂载自检')
        return
    try:
        subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            timeout=10,
            check=True,
        )
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        logger.debug('Docker 不可用，跳过 SRS 挂载自检')
        return

    expected = get_expected_srs_host_data_dir()
    actual = get_srs_container_data_mount_source(container_name)
    if not actual:
        return
    if actual == expected:
        logger.debug('SRS 数据目录与当前用户一致: %s', expected)
        return

    logger.warning(
        'SRS 容器 %s 的 /data 挂载为 %s，与当前用户期望 %s 不一致，正在执行 fix_srs.sh ...',
        container_name,
        actual,
        expected,
    )
    if run_fix_srs_script():
        logger.info('SRS 已按当前用户重建，数据目录: %s', expected)
    else:
        logger.error(
            '自动修复 SRS 失败，请手动执行: cd %s && ./fix_srs.sh',
            _video_root(),
        )
