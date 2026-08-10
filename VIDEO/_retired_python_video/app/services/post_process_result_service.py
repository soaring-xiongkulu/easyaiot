"""
算法任务 AI 后处理结果查询
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from models import AlgorithmPostProcessResult

logger = logging.getLogger(__name__)


def list_post_process_results(
    task_id: int,
    *,
    page_no: int = 1,
    page_size: int = 20,
    device_id: Optional[str] = None,
    begin_datetime: Optional[datetime] = None,
    end_datetime: Optional[datetime] = None,
) -> dict:
    query = AlgorithmPostProcessResult.query.filter_by(task_id=task_id)

    if device_id:
        query = query.filter(AlgorithmPostProcessResult.device_id == device_id)
    if begin_datetime:
        query = query.filter(AlgorithmPostProcessResult.event_time >= begin_datetime)
    if end_datetime:
        query = query.filter(AlgorithmPostProcessResult.event_time <= end_datetime)

    total = query.count()
    offset = max(page_no - 1, 0) * page_size
    items = (
        query.order_by(AlgorithmPostProcessResult.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return {
        'items': [item.to_dict() for item in items],
        'total': total,
        'page_no': page_no,
        'page_size': page_size,
    }
