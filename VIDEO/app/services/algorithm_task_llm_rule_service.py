"""
算法任务大模型（LLM）后处理规则 CRUD 与校验。

规则 = 事件规则 × 智能体绑定：按检测对象/事件类别匹配告警，绑定 AI 模块智能体
（rag_expert），配置判断方式（图片/事件间隔视频）、视频窗口与是否二次判断（门控）。
iot-sink 侧按本表规则投递独立队列执行研判。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from models import db, AlgorithmTask, AlgorithmTaskLlmRule

logger = logging.getLogger(__name__)

VALID_JUDGE_MODES = ('image', 'video')
VALID_FAIL_POLICIES = ('skip', 'confirm', 'reject')
VALID_RULE_FIELDS = {
    'rule_name', 'match_objects', 'match_events', 'agent_id', 'model_id',
    'judge_mode', 'video_pre_seconds', 'video_post_seconds', 'video_max_seconds',
    'secondary_judge', 'fail_policy', 'prompt_override', 'require_json',
    'min_interval_sec', 'priority', 'enabled',
}


def _serialize_string_list(value, field: str) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise ValueError(f'{field} 必须是 JSON 数组或 null')
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    return json.dumps(cleaned, ensure_ascii=False) if cleaned else None


def _parse_string_list(raw) -> Optional[List[str]]:
    if not raw:
        return None
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return None
    return parsed if isinstance(parsed, list) else None


def _normalize_rule_payload(payload: Dict[str, Any], task: AlgorithmTask) -> Dict[str, Any]:
    """校验并规范化规则入参（非法字段忽略，与算法任务更新语义一致）。"""
    data: Dict[str, Any] = {}
    unknown = set(payload) - VALID_RULE_FIELDS
    if unknown:
        logger.warning('llm_rule 忽略未知字段: %s', sorted(unknown))

    rule_name = payload.get('rule_name')
    if rule_name is None:
        raise ValueError('rule_name 必填')
    data['rule_name'] = str(rule_name).strip()
    if not data['rule_name']:
        raise ValueError('rule_name 不能为空')

    data['match_objects'] = _serialize_string_list(payload.get('match_objects'), 'match_objects')
    data['match_events'] = _serialize_string_list(payload.get('match_events'), 'match_events')

    agent_id = payload.get('agent_id')
    if agent_id is None:
        raise ValueError('agent_id 必填（智能体，AI 模块 rag_expert.id）')
    data['agent_id'] = int(agent_id)

    model_id = payload.get('model_id')
    data['model_id'] = int(model_id) if model_id not in (None, '', 0) else None

    judge_mode = str(payload.get('judge_mode', 'image') or 'image').lower()
    if judge_mode not in VALID_JUDGE_MODES:
        raise ValueError(f'judge_mode 必须为 {"|".join(VALID_JUDGE_MODES)}')
    data['judge_mode'] = judge_mode

    data['video_pre_seconds'] = max(0, int(payload.get('video_pre_seconds', 5) or 5))
    data['video_post_seconds'] = max(0, int(payload.get('video_post_seconds', 10) or 10))
    data['video_max_seconds'] = max(1, min(int(payload.get('video_max_seconds', 30) or 30), 300))
    if data['video_pre_seconds'] + data['video_post_seconds'] == 0:
        # 窗口为空时回退图片研判，避免视频模式空跑
        data['judge_mode'] = 'image'
    if data['video_pre_seconds'] + data['video_post_seconds'] > data['video_max_seconds']:
        data['video_max_seconds'] = data['video_pre_seconds'] + data['video_post_seconds']

    data['secondary_judge'] = bool(payload.get('secondary_judge', False))

    fail_policy = str(payload.get('fail_policy', 'skip') or 'skip').lower()
    if fail_policy not in VALID_FAIL_POLICIES:
        raise ValueError(f'fail_policy 必须为 {"|".join(VALID_FAIL_POLICIES)}')
    data['fail_policy'] = fail_policy

    prompt_override = payload.get('prompt_override')
    data['prompt_override'] = str(prompt_override).strip() if prompt_override else None

    data['require_json'] = bool(payload.get('require_json', True))
    data['min_interval_sec'] = max(0, int(payload.get('min_interval_sec', 0) or 0))
    data['priority'] = max(0, min(int(payload.get('priority', 5) or 5), 100))
    data['enabled'] = bool(payload.get('enabled', True))

    if 'task_id' in payload:
        tid = int(payload['task_id'])
        if tid != task.id:
            raise ValueError('task_id 与路径不一致')
    return data


def list_llm_rules(task_id: int) -> List[Dict[str, Any]]:
    """查询任务的大模型后处理规则（按优先级降序）。"""
    task = AlgorithmTask.query.get_or_404(task_id)
    rules = (AlgorithmTaskLlmRule.query
             .filter_by(task_id=task.id)
             .order_by(AlgorithmTaskLlmRule.priority.desc(), AlgorithmTaskLlmRule.id.asc())
             .all())
    return [rule.to_dict() for rule in rules]


def create_llm_rule(task_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """新增规则，同时开启任务级大模型后处理总开关。"""
    task = AlgorithmTask.query.get_or_404(task_id)
    data = _normalize_rule_payload(payload, task)
    duplicate = (AlgorithmTaskLlmRule.query
                 .filter_by(task_id=task.id, rule_name=data['rule_name'])
                 .first())
    if duplicate:
        raise ValueError(f'规则名称已存在: {data["rule_name"]}')
    rule = AlgorithmTaskLlmRule(task_id=task.id, **data)
    db.session.add(rule)
    task.llm_post_process_enabled = True
    db.session.commit()
    return rule.to_dict()


def update_llm_rule(rule_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """更新规则（rule_name 不变时按现有名称；整体覆盖语义）。"""
    rule = AlgorithmTaskLlmRule.query.get_or_404(rule_id)
    task = AlgorithmTask.query.get_or_404(rule.task_id)
    data = _normalize_rule_payload(payload, task)
    if 'rule_name' in data and data['rule_name'] != rule.rule_name:
        duplicate = (AlgorithmTaskLlmRule.query
                     .filter(AlgorithmTaskLlmRule.task_id == task.id,
                             AlgorithmTaskLlmRule.rule_name == data['rule_name'],
                             AlgorithmTaskLlmRule.id != rule.id)
                     .first())
        if duplicate:
            raise ValueError(f'规则名称已存在: {data["rule_name"]}')
    for key, value in data.items():
        setattr(rule, key, value)
    db.session.commit()
    return rule.to_dict()


def delete_llm_rule(rule_id: int) -> None:
    """删除规则；删除后若任务无规则，自动关闭任务级总开关。"""
    rule = AlgorithmTaskLlmRule.query.get_or_404(rule_id)
    task_id = rule.task_id
    db.session.delete(rule)
    db.session.commit()
    remaining = (AlgorithmTaskLlmRule.query
                 .filter_by(task_id=task_id, enabled=True)
                 .count())
    if remaining == 0:
        task = AlgorithmTask.query.get(task_id)
        if task:
            task.llm_post_process_enabled = False
            db.session.commit()
