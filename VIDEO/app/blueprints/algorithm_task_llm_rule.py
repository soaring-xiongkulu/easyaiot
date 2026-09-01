"""
算法任务大模型（LLM）后处理规则 CRUD。

路由挂载前缀：/video/algorithm/llm-rule（见 run.py）
- GET    /task/<task_id>/rules       查询任务规则列表
- POST   /task/<task_id>/rule        新增规则（自动开启任务级总开关）
- PUT    /rule/<rule_id>             更新规则
- DELETE /rule/<rule_id>             删除规则（无启用规则时自动关闭总开关）
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.services import algorithm_task_llm_rule_service as svc

logger = logging.getLogger(__name__)

algorithm_task_llm_rule_bp = Blueprint('algorithm_task_llm_rule', __name__)


@algorithm_task_llm_rule_bp.route('/task/<int:task_id>/rules', methods=['GET'])
def list_rules(task_id: int):
    try:
        return jsonify({'code': 0, 'msg': 'success', 'data': svc.list_llm_rules(task_id)})
    except Exception as exc:
        logger.error('查询 LLM 规则失败 task_id=%s: %s', task_id, exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@algorithm_task_llm_rule_bp.route('/task/<int:task_id>/rule', methods=['POST'])
def create_rule(task_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        return jsonify({'code': 0, 'msg': 'success', 'data': svc.create_llm_rule(task_id, payload)})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        logger.error('新增 LLM 规则失败 task_id=%s: %s', task_id, exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@algorithm_task_llm_rule_bp.route('/rule/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        return jsonify({'code': 0, 'msg': 'success', 'data': svc.update_llm_rule(rule_id, payload)})
    except ValueError as exc:
        return jsonify({'code': 400, 'msg': str(exc)}), 400
    except Exception as exc:
        logger.error('更新 LLM 规则失败 rule_id=%s: %s', rule_id, exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500


@algorithm_task_llm_rule_bp.route('/rule/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id: int):
    try:
        svc.delete_llm_rule(rule_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': None})
    except Exception as exc:
        logger.error('删除 LLM 规则失败 rule_id=%s: %s', rule_id, exc, exc_info=True)
        return jsonify({'code': 500, 'msg': str(exc)}), 500
