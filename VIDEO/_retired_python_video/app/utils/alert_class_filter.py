"""算法任务告警触发类别过滤。"""
import json
from typing import Any, List, Optional


def normalize_class_name(class_name: str) -> str:
    return str(class_name or '').strip().lower().replace('-', '_').replace(' ', '_')


def parse_alert_class_names(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        names = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            names = parsed if isinstance(parsed, list) else []
        except (TypeError, ValueError, json.JSONDecodeError):
            names = [text]
    else:
        return []
    result = []
    seen = set()
    for name in names:
        label = str(name or '').strip()
        if not label:
            continue
        key = normalize_class_name(label)
        if key in seen:
            continue
        seen.add(key)
        result.append(label)
    return result


def filter_detections_for_alert(detections: list, alert_class_names: Any) -> list:
    """按任务配置的告警标签过滤检测结果；未配置标签时保持兼容（任意检测均可告警）。"""
    if not detections:
        return []
    allowed = parse_alert_class_names(alert_class_names)
    if not allowed:
        return list(detections)
    allowed_set = {normalize_class_name(name) for name in allowed}
    return [
        det for det in detections
        if normalize_class_name(det.get('class_name', '')) in allowed_set
    ]


def get_task_alert_class_names(task_config: Any) -> Optional[Any]:
    if task_config is None:
        return None
    return getattr(task_config, 'alert_class_names', None)
