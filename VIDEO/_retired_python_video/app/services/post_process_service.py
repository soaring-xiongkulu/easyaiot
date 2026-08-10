"""
算法任务 AI 后处理工作区与 IDE 访问服务
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

from models import db, AlgorithmTask
from app.utils.post_process_runner import get_task_workspace_dir, get_task_script_path

logger = logging.getLogger(__name__)

POST_PROCESS_TEMPLATE = '''"""
算法任务 AI 后处理脚本

实现 process(ctx) 函数，接收每次算法检测的通用入参，可编写：
- 目标计数（按类别/区域统计）
- 越线检测（结合 ctx["regions"] 中 line 类型区域）
- 停留时间（利用 ctx["tracked_detections"] 的 duration / track_id）
- 自定义告警（返回 alerts 列表）

返回值 dict 字段说明：
- detections: 可选，覆盖用于默认告警的检测列表
- suppress_default_alert: 可选，为 True 时跳过系统默认告警
- alerts: 可选，自定义告警列表，每项含 object/event/information 等字段
- counts: 可选，统计结果（会写入 ctx["state"] 供下一帧使用）
- events: 可选，业务事件列表
- suppress_sink: 可选，为 True 时不投递结果（由 iot-sink 处理）
- publish_sink: 可选，为 True 时强制投递结果

后处理经 iot-sink 异步处理：算法检测 HTTP 入队 → iot-sink 对接 Kafka → Worker 执行脚本 → 落库与告警。
- suppress_kafka / publish_kafka 为兼容旧字段，同 suppress_sink / publish_sink
"""

from typing import Any, Dict, List


def process(ctx: Dict[str, Any]) -> Dict[str, Any]:
  """算法任务后处理入口。"""
  detections = ctx.get("detections") or []
  tracked = ctx.get("tracked_detections") or detections
  regions = ctx.get("regions") or []
  state = ctx.setdefault("state", {})

  # 人体姿态（启用 pose_analysis_enabled 时可用）
  pose_persons = ctx.get("pose_persons") or []
  pose_count = len(pose_persons)

  # 示例：按类别计数
  counts: Dict[str, int] = {}
  for det in detections:
    name = det.get("class_name") or "unknown"
    counts[name] = counts.get(name, 0) + 1

  # 示例：停留超过 5 秒的目标
  dwell_events: List[Dict[str, Any]] = []
  for det in tracked:
    duration = float(det.get("duration") or 0)
    if duration >= 5.0:
      dwell_events.append({
        "track_id": det.get("track_id"),
        "class_name": det.get("class_name"),
        "duration": duration,
        "device_id": ctx.get("device_id"),
      })

  state["last_counts"] = counts
  state["last_pose_count"] = pose_count
  return {
    "counts": counts,
    "events": dwell_events,
    "pose_count": pose_count,
    # "suppress_default_alert": False,
    # "alerts": [],
  }
'''

README_TEMPLATE = '''# 算法任务后处理工作区

## 文件说明

- `post_process.py`：后处理入口，实现 `process(ctx)` 函数
- `sdk/context_types.py`：入参类型参考（仅文档用途）

## 通用入参 ctx

| 字段 | 说明 |
|------|------|
| task_id / task_name / task_code / task_type | 算法任务信息 |
| device_id / device_name | 当前摄像头 |
| frame_number / timestamp | 帧序号与时间戳 |
| detections | 当前帧检测结果 |
| tracked_detections | 带 track_id、duration 的追踪结果 |
| regions | 设备检测区域（多边形/越线） |
| state | 跨帧状态字典，可在脚本内读写 |
| alert_class_names | 任务配置的告警触发标签；默认告警仅匹配这些类别 |
| pose_analysis_enabled | 是否启用人体姿态分析（由 iot-sink Worker 异步执行，算法任务仅投递请求） |
| pose_persons | Worker 执行后的 COCO-17 关键点列表 |
| pose_result | 姿态汇总：count / persons / poseType(body17) |

## 启用

在平台「算法任务」列表点击「AI后处理」保存并启用后，任务运行时会自动加载本目录脚本。

## 结果持久化（iot-sink 集群解耦）

`process()` 返回的 `counts` / `events` / `alerts` 由 **iot-sink** 经 Kafka 异步入库并派发告警：
1. 算法检测 → HTTP 入队 iot-sink
2. iot-sink → 分发 Worker 执行脚本 → 结果落库
3. 表 `algorithm_post_process_result` + 告警 Hook

查询接口：`GET /video/algorithm/task/{taskId}/post-process/results`
节点部署：在节点管理批量部署 bundle 类型 `post_process`（Worker 为 HTTP 服务，不订阅 Kafka）
'''


def _default_workspace_root() -> Path:
    from app.utils.post_process_runner import get_workspace_root
    return get_workspace_root()


def get_public_ide_base_url() -> str:
    return (os.getenv('VSCODE_IDE_PUBLIC_URL') or '/dev-api/vscode').rstrip('/')


def get_container_workspace_path(task_id: int) -> str:
    return f'/home/workspace/task_{task_id}'


def ensure_task_workspace(task: AlgorithmTask) -> Dict[str, Any]:
    workspace = get_task_workspace_dir(task.id)
    workspace.mkdir(parents=True, exist_ok=True)

    script_name = (task.post_process_script or 'post_process.py').strip() or 'post_process.py'
    script_path = workspace / script_name
    created_files = []

    if not script_path.exists():
        script_path.write_text(POST_PROCESS_TEMPLATE, encoding='utf-8')
        created_files.append(script_name)

    readme_path = workspace / 'README.md'
    if not readme_path.exists():
        readme_path.write_text(README_TEMPLATE, encoding='utf-8')
        created_files.append('README.md')

    sdk_dir = workspace / 'sdk'
    sdk_dir.mkdir(parents=True, exist_ok=True)
    types_path = sdk_dir / 'context_types.py'
    if not types_path.exists():
        types_path.write_text(
            '"""后处理入参类型参考，运行时由平台注入实际 dict。"""\n'
            'from typing import Any, Dict, List, TypedDict\n\n\n'
            'class Detection(TypedDict, total=False):\n'
            '    class_id: int\n'
            '    class_name: str\n'
            '    confidence: float\n'
            '    bbox: List[int]\n'
            '    track_id: int\n'
            '    duration: float\n\n\n'
            'class TaskContext(TypedDict, total=False):\n'
            '    task_id: int\n'
            '    task_name: str\n'
            '    task_type: str\n'
            '    device_id: str\n'
            '    device_name: str\n'
            '    frame_number: int\n'
            '    timestamp: float\n'
            '    detections: List[Detection]\n'
            '    tracked_detections: List[Detection]\n'
            '    regions: List[Dict[str, Any]]\n'
            '    state: Dict[str, Any]\n',
            encoding='utf-8',
        )
        created_files.append('sdk/context_types.py')

    vscode_dir = workspace / '.vscode'
    vscode_dir.mkdir(parents=True, exist_ok=True)
    settings_path = vscode_dir / 'settings.json'
    if not settings_path.exists():
        settings_path.write_text(
            json.dumps({
                'python.analysis.extraPaths': ['.'],
                'files.encoding': 'utf8',
            }, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        created_files.append('.vscode/settings.json')

    if not task.post_process_script:
        task.post_process_script = script_name
    if not task.post_process_replicas or int(task.post_process_replicas) < 1:
        task.post_process_replicas = 1
    task.post_process_enabled = True
    db.session.commit()

    return {
        'workspace_path': str(workspace),
        'container_path': get_container_workspace_path(task.id),
        'script_path': str(script_path),
        'created_files': created_files,
        'post_process_enabled': True,
    }


def build_ide_url(task_id: int) -> str:
    folder = quote(get_container_workspace_path(task_id), safe='')
    return f'{get_public_ide_base_url()}/?folder={folder}'


def get_post_process_status(task: AlgorithmTask) -> Dict[str, Any]:
    script_name = (task.post_process_script or 'post_process.py').strip() or 'post_process.py'
    script_path = get_task_script_path(task.id, script_name)
    return {
        'task_id': task.id,
        'post_process_enabled': bool(task.post_process_enabled),
        'post_process_script': script_name,
        'post_process_replicas': int(getattr(task, 'post_process_replicas', None) or 1),
        'script_exists': script_path.is_file(),
        'workspace_path': str(get_task_workspace_dir(task.id)),
        'ide_url': build_ide_url(task.id),
        'workspace_root': str(_default_workspace_root()),
    }
