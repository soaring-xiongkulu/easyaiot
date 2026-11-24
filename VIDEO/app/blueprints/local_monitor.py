"""edge 本机资源监测 API。"""
import logging
import os

from flask import Blueprint, jsonify

from app.services.local_monitor_service import collect_local_metrics


local_monitor_bp = Blueprint('local_monitor', __name__)
logger = logging.getLogger(__name__)


@local_monitor_bp.route('/metrics', methods=['GET'])
def metrics():
    profile = (os.getenv('EASYAIOT_DEPLOY_PROFILE') or 'full').strip().lower()
    if profile != 'edge':
        return jsonify({
            'code': 403,
            'msg': '本机监测仅在 edge 单机形态启用',
            'data': None,
        }), 403
    try:
        return jsonify({'code': 0, 'msg': 'success', 'data': collect_local_metrics()})
    except Exception as exc:
        logger.exception('采集本机资源指标失败')
        return jsonify({'code': 500, 'msg': f'采集本机资源指标失败: {exc}', 'data': None}), 500

