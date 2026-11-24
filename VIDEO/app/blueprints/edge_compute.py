"""异构边缘计算盒子管理 API。"""
import hmac
import logging
import os

from flask import Blueprint, jsonify, request

from app.services.edge_compute_service import (
    delete_node,
    enroll_node,
    get_node,
    list_metrics,
    list_nodes,
    runtime_config,
    send_command,
    update_node,
)


edge_compute_bp = Blueprint('edge_compute', __name__)
logger = logging.getLogger(__name__)


def _ok(data=None, msg='success', total=None):
    body = {'code': 0, 'msg': msg, 'data': data}
    if total is not None:
        body['total'] = total
    return jsonify(body)


def _error(message, status=400):
    return jsonify({'code': status, 'msg': str(message), 'data': None}), status


def _bool_arg(name):
    value = request.args.get(name)
    if value is None or value == '':
        return None
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def _check_enroll_token(payload):
    expected = (os.getenv('EDGE_ENROLL_TOKEN') or '').strip()
    if not expected:
        return
    provided = (
        request.headers.get('X-Edge-Join-Token')
        or payload.get('joinToken')
        or payload.get('join_token')
        or ''
    ).strip()
    if not hmac.compare_digest(expected, provided):
        raise PermissionError('边缘节点纳管口令无效')


@edge_compute_bp.route('/enroll', methods=['POST'])
def enroll():
    """一次性纳管；后续持续状态只走 MQTT。"""
    payload = request.get_json(silent=True) or {}
    try:
        _check_enroll_token(payload)
        return _ok(enroll_node(payload, request.remote_addr), '边缘节点纳管成功')
    except PermissionError as exc:
        return _error(exc, 401)
    except FileExistsError as exc:
        return _error(exc, 409)
    except ValueError as exc:
        return _error(exc, 400)
    except Exception as exc:
        logger.exception('边缘节点纳管失败')
        return _error(f'边缘节点纳管失败: {exc}', 500)


@edge_compute_bp.route('/runtime-config', methods=['POST'])
def get_runtime_config():
    payload = request.get_json(silent=True) or {}
    try:
        return _ok(runtime_config(payload.get('nodeId'), payload.get('agentToken')))
    except (TypeError, ValueError) as exc:
        return _error(exc, 401)


@edge_compute_bp.route('/node/page', methods=['GET'])
def page_nodes():
    try:
        result = list_nodes(
            page_no=request.args.get('pageNo', 1),
            page_size=request.args.get('pageSize', 20),
            keyword=request.args.get('keyword'),
            status=request.args.get('status'),
            soc_model=request.args.get('socModel'),
            enabled=_bool_arg('enabled'),
        )
        return _ok(result['list'], total=result['total'])
    except (TypeError, ValueError) as exc:
        return _error(exc, 400)
    except Exception as exc:
        logger.exception('查询边缘节点失败')
        return _error(f'查询边缘节点失败: {exc}', 500)


@edge_compute_bp.route('/node/<int:node_id>', methods=['GET'])
def node_detail(node_id):
    try:
        return _ok(get_node(node_id))
    except ValueError as exc:
        return _error(exc, 404)


@edge_compute_bp.route('/node/<int:node_id>/metrics', methods=['GET'])
def node_metrics(node_id):
    try:
        return _ok(list_metrics(
            node_id,
            minutes=request.args.get('minutes', 60),
            limit=request.args.get('limit', 360),
        ))
    except ValueError as exc:
        return _error(exc, 404)


@edge_compute_bp.route('/node/<int:node_id>', methods=['PUT'])
def edit_node(node_id):
    try:
        return _ok(update_node(node_id, request.get_json(silent=True) or {}), '边缘节点已更新')
    except ValueError as exc:
        return _error(exc, 404)


@edge_compute_bp.route('/node/<int:node_id>', methods=['DELETE'])
def disable_node(node_id):
    try:
        delete_node(node_id)
        return _ok(True, '边缘节点已停用')
    except ValueError as exc:
        return _error(exc, 404)


@edge_compute_bp.route('/node/<int:node_id>/command', methods=['POST'])
def command(node_id):
    payload = request.get_json(silent=True) or {}
    try:
        return _ok(send_command(node_id, payload.get('command'), payload.get('params')), '命令已发送')
    except ValueError as exc:
        return _error(exc, 400)
    except Exception as exc:
        logger.exception('发送边缘节点命令失败')
        return _error(f'发送边缘节点命令失败: {exc}', 502)
