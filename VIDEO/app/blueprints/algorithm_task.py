"""
算法任务、抽帧器、排序器管理路由
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify

from models import (
    db,
    AlgorithmTask,
    AlgorithmTaskStreamRuntime,
    FrameExtractor,
    Sorter,
    Pusher,
    Device,
    utc_isoformat_z,
)
from app.utils.algorithm_task_identity import build_task_stream_key, rewrite_task_stream_url
from app.utils.algorithm_task_runtime import (
    resolve_heartbeat_server_ip,
    resolve_heartbeat_stream_state,
    resolve_task_run_status_from_heartbeat,
)
from app.utils.camera_source_client import camera_source_mode, get_camera_source_status
from app.services.algorithm_task_service import (
    create_algorithm_task, update_algorithm_task, delete_algorithm_task,
    get_algorithm_task, list_algorithm_tasks, start_algorithm_task,
    stop_algorithm_task, restart_algorithm_task
)

algorithm_task_bp = Blueprint('algorithm_task', __name__)
logger = logging.getLogger(__name__)


@algorithm_task_bp.route('/runtime/info', methods=['GET'])
def runtime_info():
    """本机 RUNTIME 版本与就绪状态（供 WEB / 运维对照）。"""
    try:
        from app.services.runtime_config_service import read_runtime_version_info
        info = read_runtime_version_info()
        return jsonify({'code': 0, 'msg': 'success', 'data': info})
    except Exception as e:
        logger.error('读取 RUNTIME 信息失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e), 'data': None}), 500


# ====================== 算法任务管理接口 ======================
@algorithm_task_bp.route('/task/list', methods=['GET'])
def list_tasks():
    """查询算法任务列表"""
    try:
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 10))
        search = request.args.get('search', '').strip() or None
        device_id = request.args.get('device_id', '').strip() or None
        task_type = request.args.get('task_type', '').strip() or None
        is_enabled = request.args.get('is_enabled')
        is_enabled = bool(int(is_enabled)) if is_enabled else None
        
        result = list_algorithm_tasks(page_no, page_size, search, device_id, task_type, is_enabled)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result['items'],
            'total': result['total']
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'查询算法任务列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取算法任务详情"""
    try:
        task = get_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'获取算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task', methods=['POST'])
def create_task():
    """创建算法任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        task_name = data.get('task_name')
        if not task_name:
            return jsonify({'code': 400, 'msg': '任务名称不能为空'}), 400
        
        task_type = data.get('task_type', 'realtime')
        if task_type not in ['realtime', 'snap', 'patrol']:
            return jsonify({'code': 400, 'msg': '任务类型必须是 realtime、snap 或 patrol'}), 400
        
        task = create_algorithm_task(
            task_name=task_name,
            task_type=task_type,
            device_ids=data.get('device_ids'),
            model_ids=data.get('model_ids'),  # 模型ID列表
            extract_interval=data.get('extract_interval', 12),
            # rtmp_input_url和rtmp_output_url不再从请求中获取，改为从摄像头列表获取
            tracking_enabled=data.get('tracking_enabled', False),
            tracking_similarity_threshold=data.get('tracking_similarity_threshold', 0.2),
            tracking_max_age=data.get('tracking_max_age', 25),
            tracking_smooth_alpha=data.get('tracking_smooth_alpha', 0.25),
            alert_event_enabled=data.get('alert_event_enabled', False),
            alert_event_suppress_time=data.get('alert_event_suppress_time', 5),
            alert_class_names=data.get('alert_class_names'),
            face_detection_enabled=data.get(
                'face_detection_enabled',
                data.get('face_matching_enabled', True),
            ),
            plate_detection_enabled=data.get(
                'plate_detection_enabled',
                data.get('plate_matching_enabled', False),
            ),
            face_matching_enabled=data.get('face_matching_enabled', False),
            face_library_ids=data.get('face_library_ids'),
            face_matching_threshold=data.get('face_matching_threshold'),
            plate_matching_enabled=data.get('plate_matching_enabled', False),
            plate_library_ids=data.get('plate_library_ids'),
            matching_business_tags=data.get('matching_business_tags'),
            alert_notification_enabled=data.get('alert_notification_enabled', False),
            alert_notification_config=data.get('alert_notification_config'),
            alarm_suppress_time=data.get('alarm_suppress_time', 300),
            cron_expression=data.get('cron_expression'),
            frame_skip=data.get('frame_skip', 25),
            is_enabled=data.get('is_enabled', False),
            defense_mode=data.get('defense_mode'),
            defense_schedule=data.get('defense_schedule'),
            schedule_policy=data.get('schedule_policy', 'local'),
            prefer_gpu=data.get('prefer_gpu', True),
            target_node_id=data.get('target_node_id'),
            patrol_mode=data.get('patrol_mode', 'pool'),
            patrol_interval_sec=data.get('patrol_interval_sec', 10),
            patrol_pool_size=data.get('patrol_pool_size', 4),
            focus_device_id=data.get('focus_device_id'),
            sam_supplement_enabled=data.get('sam_supplement_enabled', False),
            sam_supplement_config=data.get('sam_supplement_config'),
            motion_gate_enabled=data.get('motion_gate_enabled', False),
            motion_gate_config=data.get('motion_gate_config'),
            detect_conf=data.get('detect_conf', 0.5),
            pose_analysis_enabled=data.get('pose_analysis_enabled', False),
            pose_analysis_config=data.get('pose_analysis_config'),
            pose_intent_enabled=data.get('pose_intent_enabled', False),
            pose_library_ids=data.get('pose_library_ids'),
            pose_intent_threshold=data.get('pose_intent_threshold'),
            pose_intent_config=data.get('pose_intent_config'),
            post_process_enabled=data.get('post_process_enabled', False),
            post_process_replicas=data.get('post_process_replicas', 1),
            post_pipeline=data.get('post_pipeline'),
            executor=data.get('executor', 'cpp'),
            runtime_bin_path=data.get('runtime_bin_path'),
            runtime_control_port=data.get('runtime_control_port'),
        )
        
        return jsonify({
            'code': 0,
            'msg': '创建成功',
            'data': task.to_dict()
        })
    except (ValueError, RuntimeError) as e:
        # 提取错误消息，如果是 RuntimeError 包装的 ValueError，提取原始消息
        error_msg = str(e)
        if isinstance(e, RuntimeError) and '创建算法任务失败:' in error_msg:
            # 提取冒号后的消息
            error_msg = error_msg.split('创建算法任务失败:', 1)[-1].strip()
        return jsonify({'code': 400, 'msg': error_msg}), 400
    except Exception as e:
        logger.error(f'创建算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新算法任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': '请求数据不能为空'}), 400
        
        # 校验：只有在停用状态下才能编辑（排除 is_enabled；运行中允许仅改 post_pipeline）
        task = AlgorithmTask.query.get_or_404(task_id)
        if task.is_enabled and 'is_enabled' not in data:
            keys = set(data.keys())
            if keys - {'post_pipeline'}:
                return jsonify({'code': 400, 'msg': '任务运行中，无法编辑，请先停止任务'}), 400
            if 'post_pipeline' in data and not task.alert_event_enabled:
                return jsonify({'code': 400, 'msg': '未启用告警事件，无法配置后处理规则链'}), 400
        
        task = update_algorithm_task(task_id, **data)
        
        return jsonify({
            'code': 0,
            'msg': '更新成功',
            'data': task.to_dict()
        })
    except (ValueError, RuntimeError) as e:
        # 提取错误消息，如果是 RuntimeError 包装的 ValueError，提取原始消息
        error_msg = str(e)
        if isinstance(e, RuntimeError) and '更新算法任务失败:' in error_msg:
            # 提取冒号后的消息
            error_msg = error_msg.split('更新算法任务失败:', 1)[-1].strip()
        return jsonify({'code': 400, 'msg': error_msg}), 400
    except Exception as e:
        logger.error(f'更新算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除算法任务"""
    try:
        # 校验：只有在停用状态下才能删除
        task = AlgorithmTask.query.get_or_404(task_id)
        if task.is_enabled:
            return jsonify({'code': 400, 'msg': '任务运行中，无法删除，请先停止任务'}), 400
        
        delete_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '删除成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'删除算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """启动算法任务"""
    try:
        task, message, already_running = start_algorithm_task(task_id)
        # 将任务数据转换为字典，并添加 already_running 字段
        task_dict = task.to_dict()
        task_dict['already_running'] = already_running
        
        return jsonify({
            'code': 0,
            'msg': message,  # "任务运行中" 或 "启动成功"
            'data': task_dict
        })
    except (ValueError, RuntimeError) as e:
        # 提取错误消息，如果是 RuntimeError 包装的 ValueError，提取原始消息
        error_msg = str(e)
        if isinstance(e, RuntimeError) and '启动算法任务失败:' in error_msg:
            # 提取冒号后的消息
            error_msg = error_msg.split('启动算法任务失败:', 1)[-1].strip()
        return jsonify({'code': 400, 'msg': error_msg}), 400
    except Exception as e:
        logger.error(f'启动算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止算法任务"""
    try:
        task = stop_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '停止成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'停止算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/restart', methods=['POST'])
def restart_task(task_id):
    """重启算法任务"""
    try:
        task = restart_algorithm_task(task_id)
        return jsonify({
            'code': 0,
            'msg': '重启成功',
            'data': task.to_dict()
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f'重启算法任务失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 抽帧器、排序器、推送器、算法服务管理接口已移除 ======================
# 新架构统一使用realtime_algorithm_service，不再需要这些独立的服务管理接口


# ====================== 心跳接收接口 ======================
# 新架构统一使用实时算法服务心跳接口，旧的抽帧器、排序器、推送器心跳接口已移除


@algorithm_task_bp.route('/heartbeat/realtime', methods=['POST'])
def receive_realtime_heartbeat():
    """接收实时算法服务心跳"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        server_ip = data.get('server_ip')
        port = data.get('port')
        process_id = data.get('process_id')
        log_path = data.get('log_path')
        has_stream_runtime = isinstance(data.get('stream_runtime'), list)
        stream_runtime = data.get('stream_runtime') or []
        
        if not task_id:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数：task_id'
            }), 400
        
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({
                'code': 400,
                'msg': f'算法任务不存在：task_id={task_id}'
            }), 400
        
        # 更新心跳信息
        task.service_last_heartbeat = datetime.utcnow()
        task.service_server_ip = resolve_heartbeat_server_ip(
            server_ip,
            task.service_server_ip,
            task.node_id,
        )
        if port:
            task.service_port = port
        if process_id:
            task.service_process_id = process_id
        if log_path:
            # cpp 多路：RUNTIME 上报 runtime_{deviceId} 子目录；
            # 裁剪到 task_{id}[/shard_N]，保留分片目录，避免 UI 只读任务根导致「日志不存在」。
            norm = str(log_path).replace('\\', '/').rstrip('/')
            marker = f'task_{task_id}'
            if marker in norm:
                parts = norm.split('/')
                for i, part in enumerate(parts):
                    if part == marker:
                        end = i + 1
                        if i + 1 < len(parts) and str(parts[i + 1]).startswith('shard_'):
                            end = i + 2
                        norm = '/'.join(parts[:end])
                        break
            task.service_log_path = norm
        elif not task.service_log_path:
            # 如果没有log_path，根据task_id生成
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            log_base_dir = os.path.join(video_root, 'logs')
            task.service_log_path = os.path.join(log_base_dir, f'task_{task_id}')
        
        # 启用任务收到 Worker 心跳后必须进入运行态；停用任务的迟到心跳不得重新激活任务。
        task.run_status = resolve_task_run_status_from_heartbeat(task.is_enabled)

        # Worker 上报的是任务与设备维度的实际状态，避免播放接口根据
        # CameraSourceManager 的订阅关系猜测是否已经进入推理、推流。
        reported_device_ids = set()
        now = datetime.utcnow()

        def _epoch_to_datetime(value):
            if value in (None, ''):
                return None
            try:
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            except (TypeError, ValueError, OverflowError):
                return None

        if isinstance(stream_runtime, list):
            for item in stream_runtime:
                if not isinstance(item, dict):
                    continue
                device_id = str(item.get('device_id') or '').strip()
                if not device_id:
                    continue
                reported_device_ids.add(device_id)
                runtime = AlgorithmTaskStreamRuntime.query.filter_by(
                    task_id=task.id,
                    device_id=device_id,
                ).first()
                if runtime is None:
                    runtime = AlgorithmTaskStreamRuntime(
                        task_id=task.id,
                        device_id=device_id,
                        stream_key=str(
                            item.get('stream_key')
                            or build_task_stream_key(task.id, device_id)
                        ),
                    )
                    db.session.add(runtime)
                runtime.node_id = task.node_id
                runtime.stream_key = str(
                    item.get('stream_key')
                    or build_task_stream_key(task.id, device_id)
                )
                runtime.source_mode, runtime.status = resolve_heartbeat_stream_state(
                    task.is_enabled,
                    item.get('source_mode'),
                    item.get('status'),
                )
                if task.is_enabled:
                    runtime.last_frame_time = _epoch_to_datetime(item.get('last_frame_time'))
                    runtime.last_detection_time = _epoch_to_datetime(item.get('last_detection_time'))
                    runtime.last_alert_time = _epoch_to_datetime(item.get('last_alert_time'))
                    runtime.error_message = str(item.get('error_message') or '')[:500] or None
                else:
                    runtime.error_message = None
                runtime.updated_at = now

        if has_stream_runtime:
            stale_rows = AlgorithmTaskStreamRuntime.query.filter_by(task_id=task.id).all()
            for runtime in stale_rows:
                if runtime.device_id not in reported_device_ids:
                    runtime.status = 'stopped'
                    runtime.updated_at = now
        
        db.session.commit()
        
        return jsonify({
            'code': 0,
            'msg': '心跳接收成功',
            'data': {
                'task_id': task.id,
                'task_name': task.task_name
            }
        })
    except Exception as e:
        logger.error(f"接收实时算法服务心跳失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器内部错误: {str(e)}'
        }), 500


@algorithm_task_bp.route('/heartbeat/patrol', methods=['POST'])
def receive_patrol_task_heartbeat():
    """接收巡检算法任务（持久化 AlgorithmTask）心跳"""
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        if not task_id:
            return jsonify({'code': 400, 'msg': '缺少必要参数：task_id'}), 400

        task = AlgorithmTask.query.get(int(task_id))
        if not task or task.task_type != 'patrol':
            return jsonify({'code': 400, 'msg': f'巡检任务不存在：task_id={task_id}'}), 400

        task.service_last_heartbeat = datetime.utcnow()
        task.service_server_ip = resolve_heartbeat_server_ip(
            data.get('server_ip'),
            task.service_server_ip,
            task.node_id,
        )
        if data.get('process_id'):
            task.service_process_id = data['process_id']
        if data.get('log_path'):
            task.service_log_path = data['log_path']
        elif not task.service_log_path:
            video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            task.service_log_path = os.path.join(video_root, 'logs', f'task_{task_id}')
        if data.get('total_patrols') is not None:
            task.total_captures = int(data.get('total_patrols') or 0)
        if data.get('total_detections') is not None:
            task.total_detections = int(data.get('total_detections') or 0)
        task.last_process_time = datetime.utcnow()
        if task.run_status != 'stopped':
            task.run_status = 'running'
        db.session.commit()
        return jsonify({'code': 0, 'msg': '心跳接收成功', 'data': {'task_id': task.id}})
    except Exception as e:
        logger.error('接收巡检任务心跳失败: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ====================== 服务状态查询接口 ======================
@algorithm_task_bp.route('/task/<int:task_id>/services/status', methods=['GET'])
def get_task_services_status(task_id):
    """获取算法任务的所有服务状态信息"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        result = {
            'realtime_service': None,
            'snap_service': None,
            'patrol_service': None,
            'extractor': None,
            'sorter': None,
            'pusher': None
        }
        
        # 检查守护进程是否在运行（即使心跳未上报）
        daemon_running = False
        try:
            from app.services.algorithm_task_launcher_service import _running_daemons, _daemons_lock
            with _daemons_lock:
                if task_id in _running_daemons:
                    daemon = _running_daemons[task_id]
                    if daemon._running and daemon._process and daemon._process.poll() is None:
                        daemon_running = True
        except Exception as e:
            logger.debug(f"检查守护进程状态失败: {str(e)}")
        
        # 根据心跳和守护进程状态判断服务状态
        has_recent_heartbeat = task.service_last_heartbeat and (datetime.utcnow() - task.service_last_heartbeat).total_seconds() < 60
        if has_recent_heartbeat:
            service_status = 'running'
        elif daemon_running:
            # 守护进程在运行但心跳未上报（可能是刚启动，心跳还未上报）
            service_status = 'running'
        else:
            service_status = 'stopped'
        
        # 实时算法任务：返回统一服务的状态
        if task.task_type == 'realtime':
            # 构建实时算法服务状态信息
            realtime_service = {
                'task_id': task.id,
                'task_name': task.task_name,
                'server_ip': task.service_server_ip,
                'port': task.service_port,
                'process_id': task.service_process_id,
                'last_heartbeat': utc_isoformat_z(task.service_last_heartbeat),
                'log_path': task.service_log_path,
                'status': service_status,
                'run_status': task.run_status
            }
            result['realtime_service'] = realtime_service
        elif task.task_type == 'snap':
            # 抓拍算法任务：返回统一服务的状态（类似实时算法任务）
            snap_service = {
                'task_id': task.id,
                'task_name': task.task_name,
                'server_ip': task.service_server_ip,
                'port': task.service_port,
                'process_id': task.service_process_id,
                'last_heartbeat': utc_isoformat_z(task.service_last_heartbeat),
                'log_path': task.service_log_path,
                'status': service_status,
                'run_status': task.run_status
            }
            result['snap_service'] = snap_service
        elif task.task_type == 'patrol':
            patrol_service = {
                'task_id': task.id,
                'task_name': task.task_name,
                'server_ip': task.service_server_ip,
                'port': task.service_port,
                'process_id': task.service_process_id,
                'last_heartbeat': utc_isoformat_z(task.service_last_heartbeat),
                'log_path': task.service_log_path,
                'status': service_status,
                'run_status': task.run_status,
                'patrol_mode': task.patrol_mode,
                'patrol_interval_sec': task.patrol_interval_sec,
                'patrol_pool_size': task.patrol_pool_size,
            }
            result['patrol_service'] = patrol_service
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"获取算法任务服务状态失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def _algorithm_task_log_dirs(task: AlgorithmTask) -> list:
    """解析算法任务日志目录。

    - 有分片时：只读 shard_* / deployments.log_dir
    - 无分片时：读现行非分片路径 service_log_path 或 logs/task_{id}
      （launcher 非集群部署仍写任务根，不是历史兼容）
    """
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    task_root = os.path.join(video_root, 'logs', f'task_{task.id}')
    dirs = []
    seen = set()

    def _add(path: str):
        if not path:
            return
        norm = os.path.abspath(str(path).rstrip('/\\'))
        if norm in seen or not os.path.isdir(norm):
            return
        seen.add(norm)
        dirs.append(norm)

    try:
        deployments = []
        if hasattr(task, '_parse_device_deployments'):
            deployments = task._parse_device_deployments() or []
        elif getattr(task, 'device_deployments', None):
            import json
            raw = task.device_deployments
            deployments = json.loads(raw) if isinstance(raw, str) else (raw or [])
        for dep in deployments or []:
            log_dir = dep.get('log_dir') or ''
            if log_dir and os.path.basename(os.path.abspath(str(log_dir).rstrip('/\\'))).startswith('shard_'):
                _add(log_dir)
    except Exception as e:
        logger.debug('解析算法任务分片日志目录失败 task_id=%s: %s', task.id, e)

    if os.path.isdir(task_root):
        try:
            for name in sorted(os.listdir(task_root)):
                if name.startswith('shard_'):
                    _add(os.path.join(task_root, name))
        except OSError:
            pass

    # 无分片时才用现行非分片目录
    if not dirs:
        _add(task.service_log_path or '')
        _add(task_root)
    return dirs


def _read_log_file_lines(log_file_path: str):
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(log_file_path, 'r', encoding='gbk') as f:
            return f.readlines()


def get_service_logs_from_dirs(log_dirs, lines: int = 100, date: str = None, task_id: int = None):
    """从多个日志目录聚合读取（算法任务分片场景）。"""
    try:
        log_filename = f"{date}.log" if date else datetime.now().strftime('%Y-%m-%d.log')
        found_files = []
        for log_dir in [d for d in (log_dirs or []) if d]:
            path = os.path.join(log_dir, log_filename)
            if os.path.isfile(path):
                found_files.append((os.path.basename(log_dir.rstrip('/\\')) or log_dir, path))

        if not found_files:
            hint = '（已检查分片或现行非分片日志目录）' if task_id is not None else ''
            return jsonify({
                'code': 0,
                'msg': 'success',
                'data': {
                    'logs': f'日志文件不存在: {log_filename}{hint}\n请等待服务运行后生成日志。',
                    'total_lines': 0,
                    'log_file': log_filename,
                    'is_all_file': not bool(date),
                }
            })

        merged = []
        total_lines = 0
        for label, path in found_files:
            try:
                file_lines = _read_log_file_lines(path)
            except Exception as e:
                logger.error('读取日志文件失败 %s: %s', path, e)
                continue
            total_lines += len(file_lines)
            if len(found_files) > 1:
                merged.append(f'===== {label}/{log_filename} =====\n')
            merged.extend(file_lines)

        if not merged:
            return jsonify({'code': 500, 'msg': f'读取日志文件失败: {log_filename}'}), 500

        log_lines = merged[-lines:] if len(merged) > lines else merged
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'logs': ''.join(log_lines),
                'total_lines': total_lines,
                'log_file': log_filename,
                'is_all_file': not bool(date),
                'log_dirs': [label for label, _ in found_files],
            }
        })
    except Exception as e:
        logger.error(f"获取服务日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


# ====================== 日志查看接口 ======================
@algorithm_task_bp.route('/task/<int:task_id>/extractor/logs', methods=['GET'])
def get_task_extractor_logs(task_id):
    """获取算法任务的抽帧器日志"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        # 新架构统一使用算法服务，对于实时算法任务和抓拍算法任务，都使用统一的日志路径
        if task.task_type in ['realtime', 'snap']:
            lines = int(request.args.get('lines', 100))
            date = request.args.get('date', '').strip()
            return get_service_logs_from_dirs(
                _algorithm_task_log_dirs(task),
                lines,
                date if date else None,
                task_id=task_id,
            )
        else:
            # 未知的任务类型
            return jsonify({
                'code': 400,
                'msg': f'不支持的任务类型: {task.task_type}'
            }), 400
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取抽帧器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/sorter/logs', methods=['GET'])
def get_task_sorter_logs(task_id):
    """获取算法任务的排序器日志"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        # 新架构统一使用 realtime 算法服务日志（含分片聚合）
        if task.task_type == 'realtime':
            lines = int(request.args.get('lines', 100))
            date = request.args.get('date', '').strip()
            return get_service_logs_from_dirs(
                _algorithm_task_log_dirs(task),
                lines,
                date if date else None,
                task_id=task_id,
            )
        else:
            return jsonify({
                'code': 400,
                'msg': '新架构已统一使用实时算法服务，请使用realtime日志接口'
            }), 400
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取排序器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/pusher/logs', methods=['GET'])
def get_task_pusher_logs(task_id):
    """获取算法任务的推送器日志"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        if task.task_type == 'realtime':
            lines = int(request.args.get('lines', 100))
            date = request.args.get('date', '').strip()
            return get_service_logs_from_dirs(
                _algorithm_task_log_dirs(task),
                lines,
                date if date else None,
                task_id=task_id,
            )
        else:
            return jsonify({
                'code': 400,
                'msg': '新架构已统一使用实时算法服务，请使用realtime日志接口'
            }), 400
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取推送器日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/realtime/logs', methods=['GET'])
def get_task_realtime_logs(task_id):
    """获取算法任务的日志（支持实时算法任务和抓拍算法任务）"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        if task.task_type not in ['realtime', 'snap', 'patrol']:
            return jsonify({'code': 400, 'msg': f'不支持的任务类型: {task.task_type}'}), 400
        
        lines = int(request.args.get('lines', 100))
        date = request.args.get('date', '').strip()
        resp = get_service_logs_from_dirs(
            _algorithm_task_log_dirs(task),
            lines,
            date if date else None,
            task_id=task_id,
        )
        # 附带任务运行状态，便于前端在任务关闭后停止日志轮询
        resp_obj, status_code = resp if isinstance(resp, tuple) else (resp, 200)
        payload = resp_obj.get_json(silent=True)
        if isinstance(payload, dict) and isinstance(payload.get('data'), dict):
            payload['data']['task_enabled'] = bool(task.is_enabled)
            payload['data']['task_run_status'] = task.run_status or 'stopped'
            return jsonify(payload), status_code
        return resp
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error(f"获取实时算法服务日志失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

# ====================== 推流地址查询接口 ======================
def _camera_source_status_map():
    """源流状态查询失败时返回空映射，不影响播放地址生成。"""
    if camera_source_mode() != 'shared':
        return {}
    try:
        return {
            str(item.get('device_id')): item
            for item in (get_camera_source_status() or [])
            if item.get('device_id')
        }
    except Exception as exc:
        logger.debug('查询 CameraSourceManager 状态失败: %s', exc)
        return {}


def _build_task_stream_info(task, device, source_status_by_device):
    """构建任务与设备唯一的播放流信息。"""
    task_id = int(task.id)
    stream_key = build_task_stream_key(task_id, device.id)
    ai_http_stream = device.ai_http_stream or device.http_stream
    ai_rtmp_stream = device.ai_rtmp_stream or device.rtmp_stream
    source_status = source_status_by_device.get(str(device.id), {})
    configured_source_mode = camera_source_mode()
    runtime = AlgorithmTaskStreamRuntime.query.filter_by(
        task_id=task_id,
        device_id=str(device.id),
    ).first()
    runtime_fresh = bool(
        runtime
        and runtime.updated_at
        and (datetime.utcnow() - runtime.updated_at).total_seconds() <= 30
    )
    if not task.is_enabled:
        effective_source_mode = runtime.source_mode if runtime_fresh else (
            'direct' if configured_source_mode == 'direct' else 'pending'
        )
        effective_status = 'stopped'
    elif runtime_fresh:
        effective_source_mode = runtime.source_mode
        effective_status = runtime.status
    else:
        effective_source_mode = 'direct' if configured_source_mode == 'direct' else 'pending'
        effective_status = 'stopped' if not task.is_enabled else 'starting'
    return {
        'task_id': task_id,
        'task_name': task.task_name,
        'model_names': task.model_names,
        'stream_key': stream_key,
        'device_id': device.id,
        'device_name': device.name or device.id,
        'http_stream': device.http_stream,
        'rtmp_stream': device.rtmp_stream,
        'ai_http_stream': rewrite_task_stream_url(ai_http_stream, task_id, device.id),
        'ai_rtmp_stream': rewrite_task_stream_url(ai_rtmp_stream, task_id, device.id),
        'source': device.source,
        'cover_image_path': device.cover_image_path,
        'source_mode': effective_source_mode,
        'configured_source_mode': configured_source_mode,
        'source_status': effective_status,
        'source_subscriber_count': source_status.get('subscriber_count', 0),
        'source_decode_fps': source_status.get('decode_fps', 0),
        'last_frame_time': (
            utc_isoformat_z(runtime.last_frame_time)
            if runtime_fresh else None
        ),
        'last_detection_time': (
            utc_isoformat_z(runtime.last_detection_time)
            if runtime_fresh else None
        ),
        'last_alert_time': (
            utc_isoformat_z(runtime.last_alert_time)
            if runtime_fresh else None
        ),
        'runtime_error': runtime.error_message if runtime_fresh else None,
    }


@algorithm_task_bp.route('/task/<int:task_id>/streams', methods=['GET'])
def get_task_streams(task_id):
    """获取算法任务关联的摄像头推流地址列表"""
    try:
        task = AlgorithmTask.query.get(task_id)
        if not task:
            return jsonify({'code': 400, 'msg': '算法任务不存在'}), 400
        
        # 获取关联的摄像头列表
        device_list = task.devices if task.devices else []
        if not device_list:
            return jsonify({
                'code': 0,
                'msg': 'success',
                'data': []
            })
        
        # 源流状态查询失败不影响任务独立播放地址返回。
        source_status_by_device = _camera_source_status_map()

        # 构建摄像头推流地址列表
        streams = []
        for device in device_list:
            streams.append(_build_task_stream_info(task, device, source_status_by_device))
        
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': streams
        })
    except Exception as e:
        logger.error(f"获取算法任务推流地址失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/device/<string:device_id>/task-streams', methods=['GET'])
def get_device_task_streams(device_id):
    """获取摄像头所有运行中实时算法任务的独立画框流。"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({'code': 404, 'msg': '摄像头不存在', 'data': []}), 404
        tasks = AlgorithmTask.query.filter(
            AlgorithmTask.devices.any(Device.id == device_id),
            AlgorithmTask.task_type == 'realtime',
            AlgorithmTask.is_enabled == True,
        ).order_by(AlgorithmTask.id.asc()).all()
        source_status_by_device = _camera_source_status_map()
        streams = [
            _build_task_stream_info(task, device, source_status_by_device)
            for task in tasks
        ]
        return jsonify({'code': 0, 'msg': 'success', 'data': streams})
    except Exception as exc:
        logger.error('获取摄像头任务流失败: device_id=%s error=%s', device_id, exc, exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(exc)}', 'data': []}), 500


@algorithm_task_bp.route('/source/status', methods=['GET'])
def get_camera_source_runtime_status():
    """查询本节点共享摄像头源流状态。"""
    try:
        device_id = request.args.get('device_id', '').strip() or None
        if camera_source_mode() != 'shared':
            data = []
        else:
            source_status = get_camera_source_status(device_id)
            if device_id:
                data = [source_status] if source_status else []
            else:
                data = source_status or []
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as exc:
        logger.warning('查询共享摄像头源流状态失败: %s', exc)
        return jsonify({
            'code': 503,
            'msg': f'共享源流服务不可用: {str(exc)}',
            'data': [],
        }), 503


def get_service_logs(service_obj, lines: int = 100, date: str = None):
    """获取服务日志（单目录入口；内部复用分片聚合逻辑）。"""
    video_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    log_base_dir = os.path.join(video_root, 'logs')
    if not getattr(service_obj, 'log_path', None):
        service_log_dir = os.path.join(log_base_dir, f'task_{service_obj.id}')
    else:
        service_log_dir = service_obj.log_path
    return get_service_logs_from_dirs(
        [service_log_dir],
        lines,
        date,
        task_id=getattr(service_obj, 'id', None),
    )


# ====================== AI 后处理 ======================
@algorithm_task_bp.route('/task/<int:task_id>/post-process/status', methods=['GET'])
def get_post_process_status(task_id):
    """获取算法任务后处理状态与 IDE 地址"""
    try:
        from app.services.post_process_service import get_post_process_status as _status
        task = AlgorithmTask.query.get_or_404(task_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': _status(task)})
    except Exception as e:
        logger.error('获取后处理状态失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/post-process/init', methods=['POST'])
def init_post_process_workspace(task_id):
    """初始化后处理工作区并启用后处理"""
    try:
        from app.services.post_process_service import ensure_task_workspace
        task = AlgorithmTask.query.get_or_404(task_id)
        data = ensure_task_workspace(task)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as e:
        logger.error('初始化后处理工作区失败: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/post-process/ide-url', methods=['GET'])
def get_post_process_ide_url(task_id):
    """获取 VSCode IDE 打开地址"""
    try:
        from app.services.post_process_service import ensure_task_workspace, build_ide_url
        task = AlgorithmTask.query.get_or_404(task_id)
        ensure_task_workspace(task)
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'ide_url': build_ide_url(task_id),
                'task_id': task_id,
                'task_name': task.task_name,
            },
        })
    except Exception as e:
        logger.error('获取 IDE 地址失败: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/post-process/toggle', methods=['PUT'])
def toggle_post_process(task_id):
    """启用/停用后处理"""
    try:
        data = request.get_json() or {}
        enabled = data.get('enabled')
        if enabled is None:
            return jsonify({'code': 400, 'msg': '缺少 enabled 参数'}), 400
        task = AlgorithmTask.query.get_or_404(task_id)
        task.post_process_enabled = bool(enabled)
        if data.get('post_process_script'):
            task.post_process_script = str(data['post_process_script']).strip() or 'post_process.py'
        if data.get('post_process_replicas') is not None:
            try:
                task.post_process_replicas = max(1, int(data['post_process_replicas']))
            except (TypeError, ValueError):
                pass
        db.session.commit()
        return jsonify({'code': 0, 'msg': 'success', 'data': task.to_dict()})
    except Exception as e:
        logger.error('切换后处理状态失败: %s', e, exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/post-process/results', methods=['GET'])
def list_post_process_results(task_id):
    """查询后处理结果（Kafka 消费者异步入库）"""
    try:
        from app.services.post_process_result_service import list_post_process_results as _list
        page_no = int(request.args.get('pageNo', 1))
        page_size = int(request.args.get('pageSize', 20))
        device_id = request.args.get('device_id', '').strip() or None
        begin_raw = request.args.get('begin_datetime', '').strip() or None
        end_raw = request.args.get('end_datetime', '').strip() or None

        begin_dt = None
        end_dt = None
        if begin_raw:
            begin_dt = datetime.fromisoformat(begin_raw.replace('Z', '+00:00'))
        if end_raw:
            end_dt = datetime.fromisoformat(end_raw.replace('Z', '+00:00'))

        result = _list(
            task_id,
            page_no=page_no,
            page_size=page_size,
            device_id=device_id,
            begin_datetime=begin_dt,
            end_datetime=end_dt,
        )
        return jsonify({'code': 0, 'msg': 'success', **result})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('查询后处理结果失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500

# ====================== POST 后处理规则链 ======================
@algorithm_task_bp.route('/task/post-pipeline/catalog', methods=['GET'])
def get_post_pipeline_catalog():
    """插件库：内置 + 已登记外置插件"""
    try:
        from app.services.post_plugin_service import list_plugin_catalog
        return jsonify({'code': 0, 'msg': 'success', 'data': list_plugin_catalog()})
    except Exception as e:
        logger.error('获取规则链插件库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


def _debug_post_pipeline_body(task, data: dict):
    from app.services.post_template_client import (
        debug_pipeline,
        build_sample_event,
        build_template_from_task,
        _task_regions,
    )

    if task and not getattr(task, 'alert_event_enabled', False):
        return 400, {'error': '未启用告警事件，后处理规则链不可用'}

    event = data.get('event')
    if not event:
        event = build_sample_event(task) if task else {
            'schema': 'infer_event.v1',
            'event_kind': 'infer',
            'correlation_id': 'debug-preview',
            'task_id': int(data.get('task_id') or 0),
            'task_name': data.get('task_name') or 'preview',
            'task_type': data.get('task_type') or 'realtime',
            'device_id': (data.get('device_ids') or ['demo-device'])[0],
            'timestamp': utc_isoformat_z(datetime.utcnow()),
            'frame_width': 1920,
            'frame_height': 1080,
            'detections': [{
                'bbox': [0.42, 0.38, 0.58, 0.72],
                'class_id': 0,
                'class_name': 'person',
                'confidence': 0.86,
                'track_id': 1,
            }],
        }

    body = {
        'event': event,
        'pipeline_override': data.get('pipeline_override'),
        'until_plugin': data.get('until_plugin') or '',
    }
    if task and not data.get('pipeline_override'):
        tpl = build_template_from_task(task)
        body['task'] = tpl['task']
        body['regions'] = tpl['regions']
    else:
        if data.get('task'):
            body['task'] = data['task']
        elif task:
            tpl = build_template_from_task(task)
            body['task'] = tpl['task']
        if data.get('regions') is not None:
            body['regions'] = data['regions']
        elif task:
            body['regions'] = _task_regions(task)
        else:
            body['regions'] = []

    status, payload = debug_pipeline(body)
    return status, payload


@algorithm_task_bp.route('/task/post-pipeline/debug', methods=['POST'])
def debug_post_pipeline_preview():
    """规则链调试（新建任务预览，无需 task_id）"""
    try:
        data = request.get_json() or {}
        status, payload = _debug_post_pipeline_body(None, data)
        if status >= 400:
            return jsonify({'code': status, 'msg': payload.get('error') if isinstance(payload, dict) else str(payload), 'data': payload}), status
        return jsonify({'code': 0, 'msg': 'success', 'data': payload})
    except Exception as e:
        logger.error('规则链调试失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500


@algorithm_task_bp.route('/task/<int:task_id>/post-pipeline/debug', methods=['POST'])
def debug_post_pipeline(task_id):
    """规则链调试（带任务上下文与区域）"""
    try:
        task = AlgorithmTask.query.get_or_404(task_id)
        data = request.get_json() or {}
        status, payload = _debug_post_pipeline_body(task, data)
        if status >= 400:
            return jsonify({'code': status, 'msg': payload.get('error') if isinstance(payload, dict) else str(payload), 'data': payload}), status
        return jsonify({'code': 0, 'msg': 'success', 'data': payload})
    except Exception as e:
        logger.error('规则链调试失败 task=%s: %s', task_id, e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'服务器内部错误: {str(e)}'}), 500
