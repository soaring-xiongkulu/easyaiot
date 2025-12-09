"""
摄像头冲突检查工具
检查同一个摄像头是否同时被推流转发任务和算法任务使用
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
from typing import List, Optional
from sqlalchemy import and_

from models import db, StreamForwardTask, AlgorithmTask, Device

logger = logging.getLogger(__name__)


def check_device_conflict_with_algorithm_tasks(device_ids: List[str], 
                                                exclude_task_id: Optional[int] = None) -> tuple[bool, List[dict]]:
    """
    检查摄像头是否已经在启用的算法任务中使用
    
    Args:
        device_ids: 要检查的摄像头ID列表
        exclude_task_id: 排除的任务ID（用于更新时排除当前任务）
    
    Returns:
        tuple[bool, List[dict]]: (是否有冲突, 冲突详情列表)
        冲突详情格式: [{'device_id': 'xxx', 'device_name': 'xxx', 'task_id': 1, 'task_name': 'xxx', 'task_type': 'realtime'}]
    """
    if not device_ids:
        return False, []
    
    conflicts = []
    
    # 查询所有启用的算法任务（is_enabled=True），因为启用的任务会占用摄像头资源
    enabled_algorithm_tasks = AlgorithmTask.query.filter(
        AlgorithmTask.is_enabled == True
    ).all()
    
    # 如果指定了排除的任务ID，过滤掉
    if exclude_task_id:
        enabled_algorithm_tasks = [t for t in enabled_algorithm_tasks if t.id != exclude_task_id]
    
    # 检查每个摄像头
    for device_id in device_ids:
        device = Device.query.get(device_id)
        if not device:
            continue
        
        # 检查该摄像头是否在这些启用的算法任务中
        for task in enabled_algorithm_tasks:
            if task.devices:
                task_device_ids = [d.id for d in task.devices]
                if device_id in task_device_ids:
                    conflicts.append({
                        'device_id': device_id,
                        'device_name': device.name or device_id,
                        'task_id': task.id,
                        'task_name': task.task_name,
                        'task_type': task.task_type,
                        'task_code': task.task_code
                    })
    
    return len(conflicts) > 0, conflicts


def check_device_conflict_with_stream_forward_tasks(device_ids: List[str],
                                                     exclude_task_id: Optional[int] = None) -> tuple[bool, List[dict]]:
    """
    检查摄像头是否已经在运行的推流转发任务中使用
    
    Args:
        device_ids: 要检查的摄像头ID列表
        exclude_task_id: 排除的任务ID（用于更新时排除当前任务）
    
    Returns:
        tuple[bool, List[dict]]: (是否有冲突, 冲突详情列表)
        冲突详情格式: [{'device_id': 'xxx', 'device_name': 'xxx', 'task_id': 1, 'task_name': 'xxx'}]
    """
    if not device_ids:
        return False, []
    
    conflicts = []
    
    # 查询所有正在运行的推流转发任务（只根据 is_enabled=True 判断）
    running_stream_forward_tasks = StreamForwardTask.query.filter(
        StreamForwardTask.is_enabled == True
    ).all()
    
    # 如果指定了排除的任务ID，过滤掉
    if exclude_task_id:
        running_stream_forward_tasks = [t for t in running_stream_forward_tasks if t.id != exclude_task_id]
    
    # 检查每个摄像头
    for device_id in device_ids:
        device = Device.query.get(device_id)
        if not device:
            continue
        
        # 检查该摄像头是否在这些运行中的推流转发任务中
        for task in running_stream_forward_tasks:
            if task.devices:
                task_device_ids = [d.id for d in task.devices]
                if device_id in task_device_ids:
                    conflicts.append({
                        'device_id': device_id,
                        'device_name': device.name or device_id,
                        'task_id': task.id,
                        'task_name': task.task_name,
                        'task_code': task.task_code
                    })
    
    return len(conflicts) > 0, conflicts


def format_conflict_message(conflicts: List[dict], task_type: str = 'algorithm') -> str:
    """
    格式化冲突消息
    
    Args:
        conflicts: 冲突详情列表
        task_type: 任务类型 ('algorithm' 或 'stream_forward')
    
    Returns:
        str: 格式化的冲突消息
    """
    if not conflicts:
        return ""
    
    if task_type == 'algorithm':
        task_type_name = '算法任务'
    else:
        task_type_name = '推流转发任务'
    
    conflict_details = []
    for conflict in conflicts:
        device_name = conflict.get('device_name', conflict.get('device_id', '未知摄像头'))
        task_name = conflict.get('task_name', f"任务{conflict.get('task_id', '')}")
        if task_type == 'algorithm':
            task_type_info = conflict.get('task_type', '')
            if task_type_info:
                task_type_name_detail = '实时算法任务' if task_type_info == 'realtime' else '抓拍算法任务'
                conflict_details.append(f"摄像头【{device_name}】已在{task_type_name_detail}【{task_name}】中使用")
            else:
                conflict_details.append(f"摄像头【{device_name}】已在{task_type_name}【{task_name}】中使用")
        else:
            conflict_details.append(f"摄像头【{device_name}】已在{task_type_name}【{task_name}】中使用")
    
    return "；".join(conflict_details)
