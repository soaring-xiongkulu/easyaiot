"""
推流转发集群健康监控：离线节点分片自动迁移、心跳超时重部署。
"""
import logging
import os
from typing import Dict

from models import StreamForwardTask
from app.utils.node_client import is_remote_deploy_enabled
from app.services.stream_forward_launcher_service import (
    _use_remote_deploy,
    migrate_unhealthy_stream_forward_task,
)

logger = logging.getLogger(__name__)


def is_health_monitor_enabled() -> bool:
    if not is_remote_deploy_enabled():
        return False
    raw = os.getenv('STREAM_FORWARD_HEALTH_MONITOR_ENABLED', 'true')
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


def run_stream_forward_health_cycle() -> Dict[str, int]:
    """扫描运行中的远程推流转发任务，迁移不健康分片。"""
    if not is_health_monitor_enabled():
        return {'checked': 0, 'migrated': 0}

    tasks = StreamForwardTask.query.filter_by(is_enabled=True).all()
    checked = 0
    migrated_total = 0

    for task in tasks:
        if not _use_remote_deploy(task):
            continue
        checked += 1
        try:
            migrated_total += migrate_unhealthy_stream_forward_task(task.id)
        except Exception as e:
            logger.error('推流转发健康检查失败 task_id=%s: %s', task.id, e, exc_info=True)

    if migrated_total:
        logger.info('推流转发健康检查完成: checked=%s migrated=%s', checked, migrated_total)

    return {'checked': checked, 'migrated': migrated_total}
