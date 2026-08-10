"""
算法任务集群健康监控：心跳超时或守护进程退出后自动重新拉起。
"""
import logging
import os

from app.utils.node_client import is_remote_deploy_enabled
from app.services.algorithm_task_launcher_service import recover_unhealthy_algorithm_tasks

logger = logging.getLogger(__name__)


def is_health_monitor_enabled() -> bool:
    raw = os.getenv('ALGORITHM_HEALTH_MONITOR_ENABLED', 'true')
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


def run_algorithm_task_health_cycle() -> int:
    """扫描已启用的算法任务，恢复不健康实例。"""
    if not is_health_monitor_enabled():
        return 0
    try:
        return recover_unhealthy_algorithm_tasks()
    except Exception as e:
        logger.error('算法任务健康检查失败: %s', e, exc_info=True)
        return 0
