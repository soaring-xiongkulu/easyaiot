#!/usr/bin/env python3
"""
AI 后处理 Worker：HTTP 服务执行用户脚本（不订阅 Kafka，由 iot-sink 分发请求）。
"""
from __future__ import annotations

import logging
import os
import sys

VIDEO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if VIDEO_ROOT not in sys.path:
    sys.path.insert(0, VIDEO_ROOT)

from app.utils.video_env import load_video_env

load_video_env(override=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger('post-process-worker')

TASK_ID = os.getenv('POST_PROCESS_TASK_ID', '')
REPLICA = os.getenv('POST_PROCESS_REPLICA', '0')
HTTP_HOST = os.getenv('POST_PROCESS_WORKER_HTTP_HOST', '0.0.0.0')
HTTP_PORT = int(os.getenv('POST_PROCESS_WORKER_HTTP_PORT', '19680'))


def _create_app():
    from run import create_app
    return create_app(start_background_tasks=False)


def _message_to_ctx(message: dict) -> dict:
    return {
        'task_id': message.get('taskId') or message.get('task_id'),
        'task_name': message.get('taskName') or message.get('task_name'),
        'task_code': message.get('taskCode') or message.get('task_code'),
        'task_type': message.get('taskType') or message.get('task_type'),
        'device_id': message.get('deviceId') or message.get('device_id'),
        'device_name': message.get('deviceName') or message.get('device_name'),
        'frame_number': message.get('frameNumber') or message.get('frame_number'),
        'timestamp': message.get('timestampEpoch') or message.get('timestamp'),
        'detections': message.get('detections') or [],
        'tracked_detections': message.get('trackedDetections') or message.get('tracked_detections') or [],
        'tracking_enabled': bool(message.get('trackingEnabled') or message.get('tracking_enabled')),
        'regions': message.get('regions') or [],
        'state': message.get('state') or {},
        'model_ids': message.get('modelIds') or message.get('model_ids') or [],
        'alert_class_names': message.get('alertClassNames') or message.get('alert_class_names') or [],
        'alert_image_path': message.get('alertImagePath') or message.get('alert_image_path'),
        'correlation_id': message.get('correlationId') or message.get('correlation_id'),
        'pose_analysis_enabled': bool(
            message.get('poseAnalysisEnabled') or message.get('pose_analysis_enabled')
        ),
    }


def _load_task_config(task_id: int):
    from models import AlgorithmTask
    return AlgorithmTask.query.get(task_id)


def run():
    from flask import Flask, jsonify, request
    from app.utils.post_process_runner import run_post_process

    if not TASK_ID:
        logger.error('缺少环境变量 POST_PROCESS_TASK_ID')
        sys.exit(1)

    task_id = int(TASK_ID)
    flask_app = _create_app()
    worker_app = Flask(__name__)
    task_holder = {'config': None}

    with flask_app.app_context():
        task_holder['config'] = _load_task_config(task_id)
        if not task_holder['config']:
            logger.error('算法任务不存在: %s', task_id)
            sys.exit(1)

    @worker_app.route('/health', methods=['GET'])
    def health():
        return jsonify({'ok': True, 'taskId': task_id, 'replica': REPLICA})

    @worker_app.route('/execute', methods=['POST'])
    def execute():
        body = request.get_json(silent=True) or {}
        req_task_id = body.get('taskId') or body.get('task_id')
        if req_task_id is not None and int(req_task_id) != task_id:
            return jsonify({'error': 'task mismatch'}), 400
        ctx = _message_to_ctx(body)
        with flask_app.app_context():
            result = run_post_process(task_holder['config'], ctx)
        return jsonify({'result': result, 'request': body})

    logger.info(
        '后处理 Worker HTTP 启动 task=%s replica=%s %s:%s',
        task_id, REPLICA, HTTP_HOST, HTTP_PORT,
    )
    worker_app.run(host=HTTP_HOST, port=HTTP_PORT, threaded=True, use_reloader=False)


if __name__ == '__main__':
    run()
