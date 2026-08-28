"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
自动化标注功能蓝图
"""
import os
import json
import logging
import tempfile
import threading
import random
import time
import io
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from urllib.parse import quote
import requests
from flask import Blueprint, request, jsonify, Response
from sqlalchemy import text

from db_models import db, AutoLabelTask, AutoLabelResult, AIService, Model, beijing_now
from app.services.inference_service import InferenceService
from app.services.minio_service import ModelService
from app.services.sam_service import get_sam_service
from app.utils.sam_result_parser import to_annotations

auto_label_bp = Blueprint('auto_label', __name__)
logger = logging.getLogger(__name__)

# 与 Java PageParam.PAGE_SIZE_MAX 保持一致
_DATASET_IMAGE_PAGE_SIZE = 1000
# 批量标注进度落库间隔（减少 DB 写入）
_AUTO_LABEL_PROGRESS_COMMIT_INTERVAL = int(os.getenv('AUTO_LABEL_PROGRESS_COMMIT_INTERVAL', '10'))


def _fetch_all_dataset_images(java_backend_url: str, dataset_id: int, extra_params: dict | None = None) -> list:
    """分页拉取数据集全部图片（单页最多 1000 条）"""
    import requests

    all_images: list = []
    page_no = 1
    extra_params = extra_params or {}

    while True:
        params = {
            'datasetId': dataset_id,
            'pageNo': page_no,
            'pageSize': _DATASET_IMAGE_PAGE_SIZE,
            **extra_params,
        }
        response = requests.get(
            f"{java_backend_url}/admin-api/dataset/image/page",
            params=params,
            timeout=60,
        )
        if response.status_code != 200:
            raise RuntimeError(f'获取图片列表失败: HTTP {response.status_code}, {response.text}')

        body = response.json()
        if body.get('code') != 0:
            raise RuntimeError(f'获取图片列表失败: {body.get("msg")}')

        data = body.get('data') or {}
        batch = data.get('list') or []
        total = data.get('total') or 0
        all_images.extend(batch)

        if not batch or len(all_images) >= total or len(batch) < _DATASET_IMAGE_PAGE_SIZE:
            break
        page_no += 1

    return all_images


def _dataset_java_base() -> str:
    return os.getenv(
        'JAVA_BACKEND_URL',
        os.getenv('GATEWAY_URL', 'http://localhost:48080'),
    ).rstrip('/')


def _find_active_task(dataset_id: int) -> AutoLabelTask | None:
    return AutoLabelTask.query.filter_by(dataset_id=dataset_id).filter(
        AutoLabelTask.status.in_(['PENDING', 'PROCESSING'])
    ).order_by(AutoLabelTask.created_at.desc()).first()


def _active_task_conflict_response(active: AutoLabelTask):
    return jsonify({
        'code': 409,
        'msg': f'已有进行中的任务 #{active.id}，请等待完成或在任务面板查看进度',
        'data': {'task_id': active.id, 'status': active.status},
    }), 409


def _parse_pipeline_config(task: AutoLabelTask) -> dict:
    if not task.pipeline_config:
        return {}
    try:
        cfg = json.loads(task.pipeline_config) if isinstance(task.pipeline_config, str) else task.pipeline_config
        return cfg if isinstance(cfg, dict) else {}
    except Exception:
        return {}


def _save_pipeline_config(task: AutoLabelTask, updates: dict) -> dict:
    cfg = _parse_pipeline_config(task)
    cfg.update(updates)
    if 'logs' in cfg and isinstance(cfg['logs'], list):
        cfg['logs'] = cfg['logs'][-80:]
    task.pipeline_config = json.dumps(cfg, ensure_ascii=False)
    return cfg


def _pipeline_log(task: AutoLabelTask, message: str) -> None:
    cfg = _parse_pipeline_config(task)
    logs = cfg.get('logs') if isinstance(cfg.get('logs'), list) else []
    logs.append({'time': beijing_now().isoformat(timespec='seconds'), 'message': message})
    _save_pipeline_config(task, {'logs': logs})
    logger.info(f'[pipeline task={task.id}] {message}')


def _dataset_annotation_url(dataset_id: int, suffix: str) -> str:
    return f"{_dataset_java_base()}/admin-api/dataset/{dataset_id}/annotation/{suffix}"


def _forward_request_headers() -> dict:
    headers = {}
    for key in ('Authorization', 'X-Authorization', 'tenant-id'):
        val = request.headers.get(key)
        if val:
            headers[key] = val
    return headers


def _model_has_weights(model: Model) -> bool:
    return bool(
        model.model_path or model.onnx_model_path or model.torchscript_model_path
        or model.tensorrt_model_path or model.openvino_model_path
    )


def _resolve_model_id(data: dict) -> tuple[int | None, str | None]:
    """解析标注所用模型：优先 model_id，兼容旧版 model_service_id。"""
    raw_model_id = data.get('model_id')
    if raw_model_id is not None and raw_model_id != '':
        try:
            model_id = int(raw_model_id)
        except (TypeError, ValueError):
            return None, 'model_id 无效'
        if model_id <= 0:
            return None, '请选择有效模型'
        model = Model.query.get(model_id)
        if not model:
            return None, '模型不存在'
        if not _model_has_weights(model):
            return None, '模型无可用的权重文件，请先上传或导出模型'
        return model_id, None

    model_service_id = data.get('model_service_id')
    if model_service_id:
        ai_service = AIService.query.get(model_service_id)
        if not ai_service:
            return None, 'AI服务不存在'
        if ai_service.status != 'running':
            return None, 'AI服务未运行，请改用 model_id 直连模型推理'
        if not ai_service.model_id:
            return None, 'AI服务未关联模型'
        return ai_service.model_id, None

    return None, '请选择模型（model_id）'


def _attach_model_info(task_dict: dict, task: AutoLabelTask) -> None:
    if task.model_id and task.model:
        task_dict['model'] = {
            'id': task.model.id,
            'name': task.model.name,
            'version': task.model.version,
        }
    elif task.model_service:
        task_dict['model_service'] = task.model_service.to_dict()


def _proxy_dataset_json_response(resp: requests.Response):
    try:
        body = resp.json()
    except ValueError:
        return jsonify({'code': 500, 'msg': resp.text or '数据集服务响应异常'}), 500
    if resp.ok:
        return jsonify(body), resp.status_code
    msg = body.get('msg') if isinstance(body, dict) else str(body)
    return jsonify({'code': body.get('code', resp.status_code) if isinstance(body, dict) else resp.status_code, 'msg': msg}), resp.status_code


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/start', methods=['POST'])
def start_auto_label(dataset_id):
    """启动自动化标注任务（YOLO 直连 / SAM 开放词汇）"""
    try:
        active = _find_active_task(dataset_id)
        if active:
            return _active_task_conflict_response(active)

        data = request.json or {}
        label_mode = (data.get('label_mode') or 'yolo').lower()
        confidence_threshold = float(data.get('confidence_threshold', 0.5 if label_mode == 'yolo' else 0.45))

        model_id = None
        legacy_service_id = data.get('model_service_id')
        text_prompts = data.get('text_prompts') or []
        annotation_type = data.get('annotation_type') or 'rectangle'
        return_masks = bool(data.get('return_masks', annotation_type == 'polygon'))
        sample_selection = data.get('sample_selection')

        if label_mode == 'sam':
            if not text_prompts:
                return jsonify({'code': 400, 'msg': 'SAM 模式需提供 text_prompts'}), 400
            sam_svc = get_sam_service()
            if not sam_svc.enabled:
                return jsonify({'code': 503, 'msg': 'SAM 未启用，请设置 SAM_ENABLED=true'}), 503
        else:
            model_id, err = _resolve_model_id(data)
            if err:
                return jsonify({'code': 400, 'msg': err}), 400

        task = AutoLabelTask(
            dataset_id=dataset_id,
            model_id=model_id,
            model_service_id=legacy_service_id if legacy_service_id else None,
            confidence_threshold=confidence_threshold,
            label_mode=label_mode,
            text_prompts=json.dumps(text_prompts, ensure_ascii=False) if text_prompts else None,
            annotation_type=annotation_type,
            phase='PRODUCTION',
            return_masks=return_masks,
            bootstrap_selection=sample_selection or 'all',
            status='PENDING',
        )
        db.session.add(task)
        db.session.commit()

        from flask import current_app
        app = current_app._get_current_object()
        thread = threading.Thread(target=execute_auto_label_task, args=(app, task.id))
        thread.daemon = True
        thread.start()

        return jsonify({
            'code': 0,
            'msg': '自动化标注任务已启动',
            'data': {
                'task_id': task.id,
                'model_id': model_id,
                'label_mode': label_mode,
            }
        })

    except Exception as e:
        logger.error(f"启动自动化标注任务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'启动任务失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/bootstrap/start', methods=['POST'])
def start_bootstrap_auto_label(dataset_id):
    """SAM 冷启动批量标注（首批 N 张）"""
    try:
        active = _find_active_task(dataset_id)
        if active:
            return _active_task_conflict_response(active)

        data = request.json or {}
        text_prompts = data.get('text_prompts') or []
        if not text_prompts:
            return jsonify({'code': 400, 'msg': '请提供 text_prompts'}), 400

        sam_svc = get_sam_service()
        if not sam_svc.enabled:
            return jsonify({'code': 503, 'msg': 'SAM 未启用，请设置 SAM_ENABLED=true'}), 503

        bootstrap_limit = int(data.get('bootstrap_limit', 200))
        bootstrap_selection = data.get('bootstrap_selection', 'unlabeled_first')
        annotation_type = data.get('annotation_type', 'rectangle')
        confidence_threshold = float(data.get('confidence_threshold', 0.45))
        return_masks = bool(data.get('return_masks', annotation_type == 'polygon'))

        task = AutoLabelTask(
            dataset_id=dataset_id,
            confidence_threshold=confidence_threshold,
            label_mode='sam',
            text_prompts=json.dumps(text_prompts, ensure_ascii=False),
            annotation_type=annotation_type,
            phase='BOOTSTRAP',
            bootstrap_limit=bootstrap_limit,
            bootstrap_selection=bootstrap_selection,
            return_masks=return_masks,
            status='PENDING',
        )
        db.session.add(task)
        db.session.commit()

        from flask import current_app
        app = current_app._get_current_object()
        thread = threading.Thread(target=execute_auto_label_task, args=(app, task.id))
        thread.daemon = True
        thread.start()

        return jsonify({
            'code': 0,
            'msg': 'SAM 冷启动标注任务已启动',
            'data': {'task_id': task.id, 'bootstrap_limit': bootstrap_limit},
        })
    except Exception as e:
        logger.error(f"启动 SAM 冷启动任务失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'启动失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/pipeline/start', methods=['POST'])
def start_pipeline_auto_label(dataset_id):
    """
    无人值守标注流水线：多路摄像头抽帧 → 模型自动打标 → 写入数据集（可选打包导出）。

    与在线推理/告警（VIDEO AlgorithmTask）无关；集群模式按摄像头分片调度到多台计算节点。
    """
    try:
        data = request.json or {}
        execution_mode = (data.get('execution_mode') or 'local').lower()
        frame_task_ids = data.get('frame_task_ids') or []

        if execution_mode == 'local':
            active = _find_active_task(dataset_id)
            if active:
                return _active_task_conflict_response(active)

        text_prompts = data.get('text_prompts') or []
        if not text_prompts:
            return jsonify({'code': 400, 'msg': '请提供检测类别词 text_prompts'}), 400

        strategy_pre = data.get('strategy') or {}
        skip_sam_cold_start = bool(
            data.get('skip_sam_cold_start') or strategy_pre.get('skip_sam_cold_start')
        )
        initial_model_id = (
            data.get('initial_model_id')
            or data.get('model_id')
            or strategy_pre.get('initial_model_id')
        )
        sam_svc = get_sam_service()
        if (
            not sam_svc.enabled
            and execution_mode == 'local'
            and not (skip_sam_cold_start and initial_model_id)
        ):
            return jsonify({
                'code': 503,
                'msg': 'SAM 未启用：请设置 SAM_ENABLED=true，或指定 model_id 并 skip_sam_cold_start',
            }), 503

        duration_hours = max(1, min(48, int(data.get('duration_hours', 8))))
        capture_interval_sec = max(5, min(600, int(data.get('capture_interval_sec', 30))))
        annotation_type = data.get('annotation_type', 'rectangle')
        confidence_threshold = float(data.get('confidence_threshold', 0.45))
        return_masks = bool(data.get('return_masks', annotation_type == 'polygon'))
        auto_export = bool(data.get('auto_export', True))
        keep_annotated_images_only = bool(data.get('keep_annotated_images_only', True))
        queue_priority = int(data.get('queue_priority', 0))

        java_url = _dataset_java_base()
        selected_tasks = _fetch_frame_tasks(
            java_url,
            dataset_id,
            frame_task_ids=frame_task_ids if frame_task_ids else None,
        )

        if execution_mode == 'cluster' and not selected_tasks:
            return jsonify({
                'code': 400,
                'msg': '集群模式需至少选择一个摄像头（帧捕获任务），请先在数据来源中配置',
            }), 400

        if execution_mode == 'cluster':
            unavailable_streams = []
            for frame_task in selected_tasks:
                stream_url, stream_error = _resolve_frame_task_stream(java_url, frame_task)
                if stream_url:
                    frame_task['rtmpUrl'] = stream_url
                else:
                    unavailable_streams.append(
                        f'{frame_task.get("taskName") or frame_task.get("id")}: '
                        f'{stream_error or "无可用视频流地址"}'
                    )
            if unavailable_streams:
                return jsonify({
                    'code': 400,
                    'msg': f'摄像头流解析失败：{"；".join(unavailable_streams[:3])}',
                }), 400

        from app.services.auto_label_orchestrator import init_pipeline_strategy
        strategy_raw = data.get('strategy') or {
            'bootstrap_sam_limit': int(data.get('bootstrap_sam_limit', 200)),
            'yolo_iterate_every': int(data.get('yolo_iterate_every', 500)),
            'auto_train_yolo': bool(data.get('auto_train_yolo', True)),
            'initial_model_id': data.get('initial_model_id') or data.get('model_id'),
            'skip_sam_cold_start': bool(data.get('skip_sam_cold_start', False)),
            'sam_supplement_enabled': bool(data.get('sam_supplement_enabled', True)),
            'sam_supplement_until_labeled': int(data.get('sam_supplement_until_labeled', 500)),
            'sam_supplement_stop_map': float(data.get('sam_supplement_stop_map', 0)),
            'sam_supplement_min_detections': int(data.get('sam_supplement_min_detections', 1)),
            'pretrain_model_id': data.get('pretrain_model_id'),
            'model_arch': data.get('model_arch', '@AI/yolo26n.pt'),
            'yolo_confidence': float(data.get('yolo_confidence', 0.5)),
            'sam_confidence': confidence_threshold,
        }

        pipeline_config = {
            'duration_hours': duration_hours,
            'capture_interval_sec': capture_interval_sec,
            'auto_export': auto_export,
            'keep_annotated_images_only': keep_annotated_images_only,
            'export_train_ratio': float(data.get('train_ratio', 0.7)),
            'export_val_ratio': float(data.get('val_ratio', 0.2)),
            'export_test_ratio': float(data.get('test_ratio', 0.1)),
            'pipeline_status': 'queued' if execution_mode == 'cluster' else 'pending',
            'captured_count': 0,
            'labeled_count': 0,
            'packaged': False,
            'camera_count': len(selected_tasks),
        }

        task = AutoLabelTask(
            dataset_id=dataset_id,
            confidence_threshold=confidence_threshold,
            label_mode='smart',
            text_prompts=json.dumps(text_prompts, ensure_ascii=False),
            annotation_type=annotation_type,
            phase='PIPELINE',
            bootstrap_selection='unlabeled_only',
            return_masks=return_masks,
            execution_mode=execution_mode,
            queue_priority=queue_priority,
            selected_frame_task_ids=json.dumps([ft.get('id') for ft in selected_tasks], ensure_ascii=False),
            status='PENDING',
            model_id=int(strategy_raw['initial_model_id']) if strategy_raw.get('initial_model_id') else None,
        )
        init_pipeline_strategy(task, strategy_raw)
        state = json.loads(task.pipeline_config)
        state.update(pipeline_config)
        task.pipeline_config = json.dumps(state, ensure_ascii=False)
        db.session.add(task)
        db.session.commit()

        from flask import current_app
        from app.services.auto_label_orchestrator import maybe_kickoff_skip_sam_pipeline
        app = current_app._get_current_object()
        maybe_kickoff_skip_sam_pipeline(task, app)

        if execution_mode == 'cluster':
            from app.services.auto_label_cluster_service import (
                create_camera_subtasks,
                start_cluster_pipeline,
            )
            create_camera_subtasks(task, selected_tasks, json.loads(task.pipeline_config))
            db.session.commit()
            thread = threading.Thread(target=start_cluster_pipeline, args=(app, task.id))
            thread.daemon = True
            thread.start()
            msg = f'集群流水线已入队，{len(selected_tasks)} 路摄像头将按负载均衡分发到计算节点'
        else:
            thread = threading.Thread(target=execute_pipeline_task, args=(app, task.id))
            thread.daemon = True
            thread.start()
            msg = '无人值守流水线已启动（本机模式）'

        return jsonify({
            'code': 0,
            'msg': msg,
            'data': {
                'task_id': task.id,
                'execution_mode': execution_mode,
                'camera_count': len(selected_tasks),
                'duration_hours': duration_hours,
                'capture_interval_sec': capture_interval_sec,
            },
        })
    except Exception as e:
        logger.error(f'启动无人值守流水线失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'启动失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/task/<int:task_id>/subtasks', methods=['GET'])
def list_auto_label_subtasks(dataset_id, task_id):
    """获取任务的摄像头子任务列表（含节点分配与进度）"""
    try:
        from db_models import AutoLabelSubTask
        task = AutoLabelTask.query.filter_by(id=task_id, dataset_id=dataset_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务不存在'}), 404
        subtasks = (
            AutoLabelSubTask.query.filter_by(parent_task_id=task_id)
            .order_by(AutoLabelSubTask.queue_position.asc(), AutoLabelSubTask.id.asc())
            .all()
        )
        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': {
                'task': task.to_dict(),
                'subtasks': [s.to_dict() for s in subtasks],
            },
        })
    except Exception as e:
        logger.error(f'获取子任务列表失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/queue', methods=['GET'])
def list_auto_label_queue(dataset_id):
    """获取数据集自动标注任务队列（含集群子任务摘要）"""
    try:
        from db_models import AutoLabelSubTask
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        status_filter = request.args.get('status')

        query = AutoLabelTask.query.filter_by(dataset_id=dataset_id)
        if status_filter:
            query = query.filter(AutoLabelTask.status == status_filter)
        query = query.order_by(AutoLabelTask.created_at.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        items = []
        for task in pagination.items:
            td = task.to_dict()
            subtasks = AutoLabelSubTask.query.filter_by(parent_task_id=task.id).all()
            td['subtask_summary'] = {
                'total': len(subtasks),
                'queued': sum(1 for s in subtasks if s.status == 'QUEUED'),
                'running': sum(1 for s in subtasks if s.status in ('DISPATCHING', 'RUNNING')),
                'completed': sum(1 for s in subtasks if s.status == 'COMPLETED'),
                'failed': sum(1 for s in subtasks if s.status == 'FAILED'),
            }
            td['nodes'] = list({
                s.assigned_node_host: s.assigned_node_id
                for s in subtasks if s.assigned_node_host
            }.items())
            items.append(td)

        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': {
                'list': items,
                'total': pagination.total,
                'page': page,
                'page_size': page_size,
            },
        })
    except Exception as e:
        logger.error(f'获取任务队列失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/auto-label/subtask/<int:subtask_id>/heartbeat', methods=['POST'])
def auto_label_subtask_heartbeat(subtask_id):
    """集群 Worker 进度心跳（节点 Agent 下发的 Worker 调用）"""
    try:
        from flask import current_app
        from app.services.auto_label_cluster_service import update_subtask_progress
        payload = request.json or {}
        subtask = update_subtask_progress(subtask_id, payload, app=current_app._get_current_object())
        if not subtask:
            return jsonify({'code': 404, 'msg': '子任务不存在'}), 404
        return jsonify({'code': 0, 'msg': 'ok', 'data': subtask.to_dict()})
    except Exception as e:
        logger.error(f'子任务心跳失败: {str(e)}', exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/task/<int:task_id>/pause', methods=['POST'])
def pause_auto_label_task(dataset_id, task_id):
    from app.services.auto_label_orchestrator import pause_task
    if not pause_task(task_id):
        return jsonify({'code': 400, 'msg': '无法暂停该任务'}), 400
    return jsonify({'code': 0, 'msg': '任务已暂停'})


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/task/<int:task_id>/resume', methods=['POST'])
def resume_auto_label_task(dataset_id, task_id):
    from app.services.auto_label_orchestrator import resume_task
    if not resume_task(task_id):
        return jsonify({'code': 400, 'msg': '无法恢复该任务'}), 400
    from flask import current_app
    app = current_app._get_current_object()
    from app.services.auto_label_cluster_service import process_queue_once
    process_queue_once(app)
    return jsonify({'code': 0, 'msg': '任务已恢复'})


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/task/<int:task_id>/cancel', methods=['POST'])
def cancel_auto_label_task(dataset_id, task_id):
    from app.services.auto_label_orchestrator import cancel_task
    if not cancel_task(task_id):
        return jsonify({'code': 400, 'msg': '无法取消该任务'}), 400
    return jsonify({'code': 0, 'msg': '任务已取消'})


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/bootstrap/status', methods=['GET'])
def bootstrap_status(dataset_id):
    """冷启动进度、识别率与训练就绪状态"""
    try:
        from app.services.auto_label_strategy import get_strategy, parse_pipeline_state
        from app.services.sam_bootstrap_quality import assess_sam_bootstrap_quality

        task = AutoLabelTask.query.filter_by(
            dataset_id=dataset_id,
        ).filter(
            AutoLabelTask.phase.in_(['BOOTSTRAP', 'PIPELINE'])
        ).order_by(AutoLabelTask.created_at.desc()).first()
        if not task:
            return jsonify({'code': 0, 'msg': '暂无冷启动任务', 'data': {'has_task': False}})

        labeled = task.success_count or 0
        limit = task.bootstrap_limit or 200
        if task.phase == 'PIPELINE':
            strategy = get_strategy(task)
            limit = int(strategy.get('bootstrap_sam_limit') or limit)
            state = parse_pipeline_state(task)
            labeled = int(state.get('sam_hit_count') or 0) + int(state.get('sam_empty_count') or 0)
            if labeled == 0:
                labeled = int(state.get('sam_labeled') or task.success_count or 0)

        strategy = get_strategy(task) if task.phase == 'PIPELINE' else {}
        min_hit_rate = float(strategy.get('sam_bootstrap_min_hit_rate') or 0.3)
        quality = assess_sam_bootstrap_quality(task, min_hit_rate)
        bootstrap_done = (
            task.status == 'COMPLETED'
            or (task.phase == 'PIPELINE' and labeled >= limit)
            or (task.phase == 'BOOTSTRAP' and (task.processed_images or 0) >= limit)
        )
        ready_for_train = (
            bootstrap_done
            and quality['sam_quality_passed']
            and bool(task.review_passed)
        )
        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': {
                'has_task': True,
                'task_id': task.id,
                'status': task.status,
                'phase': task.phase,
                'processed_images': task.processed_images,
                'total_images': task.total_images,
                'success_count': task.success_count,
                'bootstrap_limit': limit,
                'review_passed': bool(task.review_passed),
                'bootstrap_done': bootstrap_done,
                'ready_for_train': ready_for_train,
                'awaiting_sam_review': bool(parse_pipeline_state(task).get('awaiting_sam_review')),
                **quality,
            },
        })
    except Exception as e:
        logger.error(f"获取冷启动状态失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/bootstrap/complete-review', methods=['POST'])
def bootstrap_complete_review(dataset_id):
    """标记冷启动抽检通过"""
    try:
        data = request.json or {}
        review_passed = bool(data.get('review_passed', True))
        task = AutoLabelTask.query.filter_by(
            dataset_id=dataset_id, phase='BOOTSTRAP', status='COMPLETED'
        ).order_by(AutoLabelTask.created_at.desc()).first()
        if not task:
            task = AutoLabelTask.query.filter_by(
                dataset_id=dataset_id, phase='PIPELINE'
            ).order_by(AutoLabelTask.created_at.desc()).first()
        if not task:
            return jsonify({'code': 404, 'msg': '未找到已完成的冷启动任务'}), 404

        from app.services.sam_bootstrap_quality import assess_sam_bootstrap_quality
        from app.services.auto_label_strategy import get_strategy, parse_pipeline_state

        strategy = get_strategy(task)
        quality = assess_sam_bootstrap_quality(
            task, float(strategy.get('sam_bootstrap_min_hit_rate') or 0.3),
        )
        if review_passed and not quality['sam_quality_passed']:
            return jsonify({
                'code': 400,
                'msg': (
                    f'SAM 识别率 {quality["recognition_rate_pct"]}% 低于阈值 '
                    f'{quality["min_hit_rate_pct"]}%，请先恢复冷启动标注或改用手动/YOLO 自动标注'
                ),
                'data': quality,
            }), 400

        task.review_passed = review_passed
        state = parse_pipeline_state(task)
        if review_passed:
            state['awaiting_sam_review'] = False
            task.pipeline_config = json.dumps(state, ensure_ascii=False)
        db.session.commit()
        return jsonify({
            'code': 0,
            'msg': '抽检状态已更新',
            'data': {'task_id': task.id, 'review_passed': review_passed, **quality},
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/bootstrap/reset', methods=['POST'])
def bootstrap_reset_annotations(dataset_id):
    """恢复冷启动 SAM 自动标注到初始状态（清空标注、重置抽检）"""
    try:
        task = AutoLabelTask.query.filter_by(dataset_id=dataset_id).filter(
            AutoLabelTask.phase.in_(['BOOTSTRAP', 'PIPELINE']),
        ).order_by(AutoLabelTask.created_at.desc()).first()
        if not task:
            return jsonify({'code': 404, 'msg': '未找到冷启动任务'}), 404

        java_backend_url = _dataset_java_base()
        reset_count = 0
        for row in AutoLabelResult.query.filter_by(task_id=task.id, status='SUCCESS').all():
            try:
                resp = requests.put(
                    f'{java_backend_url}/admin-api/dataset/image/update',
                    json={
                        'id': row.dataset_image_id,
                        'datasetId': dataset_id,
                        'annotations': '[]',
                        'completed': 0,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    reset_count += 1
            except Exception as e:
                logger.warning('恢复图片 %s 失败: %s', row.dataset_image_id, e)

        from app.services.auto_label_strategy import parse_pipeline_state
        from app.services.auto_label_orchestrator import _save_pipeline_state

        task.review_passed = False
        state = parse_pipeline_state(task)
        for key in ('sam_hit_count', 'sam_empty_count', 'sam_labeled', 'total_labeled', 'sam_quality'):
            state.pop(key, None)
        state['awaiting_sam_review'] = False
        state['sam_quality_passed'] = None
        if task.phase == 'PIPELINE':
            from app.services.auto_label_strategy import PHASE_BOOTSTRAP_SAM
            state['pipeline_phase'] = PHASE_BOOTSTRAP_SAM
            _save_pipeline_state(task, state)
        elif task.pipeline_config:
            task.pipeline_config = json.dumps(state, ensure_ascii=False)

        task.success_count = 0
        task.processed_images = 0
        if task.phase == 'BOOTSTRAP':
            task.status = 'PENDING'
            task.completed_at = None
        db.session.commit()

        return jsonify({
            'code': 0,
            'msg': f'已恢复 {reset_count} 张图片到未标注状态',
            'data': {'task_id': task.id, 'reset_count': reset_count},
        })
    except Exception as e:
        db.session.rollback()
        logger.error('恢复冷启动标注失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/model/history', methods=['GET'])
def list_auto_label_model_history(dataset_id):
    """获取数据集自动标注模型更新历史（条数上限可配置）"""
    try:
        from app.services.auto_label_model_service import (
            get_model_history_max,
            get_dataset_bound_model_id,
            list_model_history,
        )

        max_history = get_model_history_max()
        limit_arg = request.args.get('limit')
        limit = max_history if limit_arg is None else int(limit_arg)
        limit = min(max(1, limit), max_history)
        history = list_model_history(dataset_id, limit=limit)
        current_model_id = get_dataset_bound_model_id(dataset_id)
        model_info = None
        if current_model_id:
            m = Model.query.get(current_model_id)
            if m:
                model_info = {
                    'id': m.id,
                    'name': m.name,
                    'version': m.version,
                }
        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': {
                'current_model_id': current_model_id,
                'current_model': model_info,
                'history': history,
                'max_history': max_history,
            },
        })
    except Exception as e:
        logger.error('获取模型更新历史失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/model/update', methods=['POST'])
def update_auto_label_model(dataset_id):
    """根据当前已标注数据微调并更新数据集自动标注模型"""
    try:
        from app.services.auto_label_model_service import start_dataset_model_update

        data = request.json or {}
        base_model_id = data.get('base_model_id') or data.get('model_id')
        if base_model_id is not None:
            try:
                base_model_id = int(base_model_id)
            except (TypeError, ValueError):
                base_model_id = None

        strategy_raw = data.get('strategy') if isinstance(data.get('strategy'), dict) else None
        if data.get('train_epochs') is not None:
            strategy_raw = strategy_raw or {}
            strategy_raw['train_epochs'] = int(data['train_epochs'])
        if data.get('model_history_max') is not None:
            strategy_raw = strategy_raw or {}
            strategy_raw['model_history_max'] = int(data['model_history_max'])

        from flask import current_app
        app = current_app._get_current_object()
        record = start_dataset_model_update(
            dataset_id,
            app,
            base_model_id=base_model_id,
            strategy_raw=strategy_raw,
        )
        return jsonify({
            'code': 0,
            'msg': '模型更新任务已启动，请稍后在历史记录中查看进度',
            'data': record.to_dict(),
        })
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'code': 409, 'msg': str(e)}), 409
    except Exception as e:
        logger.error('启动模型更新失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': str(e)}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/task/<int:task_id>', methods=['GET'])
def get_auto_label_task(dataset_id, task_id):
    """获取自动化标注任务状态"""
    try:
        task = AutoLabelTask.query.filter_by(id=task_id, dataset_id=dataset_id).first()
        if not task:
            return jsonify({'code': 404, 'msg': '任务不存在'}), 404

        task_dict = task.to_dict()
        _attach_model_info(task_dict, task)

        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': task_dict
        })

    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/tasks', methods=['GET'])
def list_auto_label_tasks(dataset_id):
    """获取数据集的所有自动化标注任务列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        tasks = AutoLabelTask.query.filter_by(dataset_id=dataset_id)\
            .order_by(AutoLabelTask.created_at.desc())\
            .paginate(page=page, per_page=page_size, error_out=False)

        # 构建任务列表，包含关联的AI服务信息
        task_list = []
        for task in tasks.items:
            task_dict = task.to_dict()
            _attach_model_info(task_dict, task)
            task_list.append(task_dict)

        return jsonify({
            'code': 0,
            'msg': '获取成功',
            'data': {
                'list': task_list,
                'total': tasks.total,
                'page': page,
                'page_size': page_size
            }
        })

    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'获取失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/image/<int:image_id>', methods=['POST'])
def label_single_image(dataset_id, image_id):
    """单张图片AI标注（直连模型推理）"""
    try:
        data = request.json or {}
        confidence_threshold = float(data.get('confidence_threshold', 0.5))

        model_id, err = _resolve_model_id(data)
        if err:
            return jsonify({'code': 400, 'msg': err}), 400

        java_backend_url = _dataset_java_base()
        image_response = requests.get(
            f"{java_backend_url}/admin-api/dataset/image/get",
            params={'id': image_id},
            timeout=10
        )

        if image_response.status_code != 200:
            return jsonify({'code': 404, 'msg': '图片不存在'}), 404

        image_data = image_response.json()
        if image_data.get('code') != 0:
            return jsonify({'code': 404, 'msg': '获取图片信息失败'}), 404

        image_info = image_data.get('data', {})
        image_path = image_info.get('path')

        if not image_path:
            return jsonify({'code': 400, 'msg': '图片路径不存在'}), 400

        bucket_name, object_key = _parse_minio_path(image_path)
        if not bucket_name or not object_key:
            return jsonify({'code': 400, 'msg': '无法解析图片路径'}), 400

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.close()

        success, error_msg = ModelService.download_from_minio(bucket_name, object_key, temp_file.name)
        if not success:
            return jsonify({'code': 500, 'msg': f'下载图片失败: {error_msg}'}), 500

        try:
            from PIL import Image as PILImage
            with PILImage.open(temp_file.name) as img:
                image_width, image_height = img.size

            inference_service = InferenceService(model_id)
            detections = inference_service.detect_image_file(temp_file.name, {
                'conf_thres': confidence_threshold,
                'iou_thres': 0.45,
            })
            annotations = _parse_inference_result({'detections': detections}, image_width, image_height)

            update_response = requests.put(
                f"{java_backend_url}/admin-api/dataset/image/update",
                json={
                    'id': image_id,
                    'datasetId': dataset_id,
                    'annotations': json.dumps(annotations, ensure_ascii=False),
                    'completed': 1 if annotations else 0
                },
                timeout=10
            )

            if update_response.status_code != 200:
                logger.warning(f"更新图片标注失败: {image_id}")
                return jsonify({'code': 500, 'msg': '更新图片标注失败'}), 500

            return jsonify({
                'code': 0,
                'msg': '标注成功',
                'data': {
                    'annotations': annotations,
                    'count': len(annotations)
                }
            })

        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    except Exception as e:
        logger.error(f"单张图片AI标注失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'标注失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/auto-label/export', methods=['POST'])
def export_labeled_dataset(dataset_id):
    """导出标注数据集（转发至 iot-dataset /annotation/export）"""
    try:
        data = request.json or {}
        if data.get('task_id'):
            logger.warning('export task_id 已由 iot-dataset 统一导出，旧参数 task_id 已忽略')
        export_format = (data.get('format') or 'yolo').lower()
        if export_format not in ('yolo', ''):
            return jsonify({'code': 400, 'msg': f'导出格式 {export_format} 已下线，请使用 YOLO 导出'}), 400
        body = {
            'trainRatio': float(data.get('train_ratio', 0.7)),
            'valRatio': float(data.get('val_ratio', 0.2)),
            'testRatio': float(data.get('test_ratio', 0.1)),
            'sampleSelection': data.get('sample_selection') or data.get('sample_type', 'all'),
            'selectedClasses': data.get('selected_classes') or [],
            'exportPrefix': data.get('export_prefix') or data.get('file_prefix') or '',
        }
        if not body['selectedClasses']:
            return jsonify({'code': 400, 'msg': '请至少选择一个导出类别'}), 400
        resp = requests.post(
            _dataset_annotation_url(dataset_id, 'export'),
            json=body,
            headers=_forward_request_headers(),
            timeout=1800,
            stream=True,
        )
        if not resp.ok:
            return _proxy_dataset_json_response(resp)
        headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() in ('content-type', 'content-disposition', 'content-length')
        }
        return Response(resp.iter_content(chunk_size=8192), status=resp.status_code, headers=headers)
    except Exception as e:
        logger.error(f"导出数据集失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'导出失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/extract-frames', methods=['POST'])
def extract_frames_from_video(dataset_id):
    """视频抽帧（转发至 iot-dataset /annotation/extract-frames）"""
    try:
        if 'file' not in request.files:
            return jsonify({'code': 400, 'msg': '未找到视频文件'}), 400
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'code': 400, 'msg': '未选择视频文件'}), 400
        frame_interval = request.form.get('frame_interval', '30')
        resp = requests.post(
            _dataset_annotation_url(dataset_id, 'extract-frames'),
            files={'file': (file.filename, file.stream, file.content_type or 'video/mp4')},
            data={'frame_interval': frame_interval},
            headers=_forward_request_headers(),
            timeout=1800,
        )
        return _proxy_dataset_json_response(resp)
    except Exception as e:
        logger.error(f"视频抽帧失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'抽帧失败: {str(e)}'}), 500


@auto_label_bp.route('/dataset/<int:dataset_id>/import-labelme', methods=['POST'])
def import_labelme_dataset(dataset_id):
    """导入 LabelMe（转发至 iot-dataset /annotation/import-labelme）"""
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'code': 400, 'msg': '未选择文件'}), 400
        multipart = []
        for f in files:
            multipart.append(('files', (f.filename, f.stream, f.content_type or 'application/octet-stream')))
        resp = requests.post(
            _dataset_annotation_url(dataset_id, 'import-labelme'),
            files=multipart,
            headers=_forward_request_headers(),
            timeout=1800,
        )
        if not resp.ok:
            return _proxy_dataset_json_response(resp)
        body = resp.json()
        data = body.get('data') if isinstance(body, dict) else {}
        images = (data or {}).get('imagesCopied') or (data or {}).get('imported_count') or 0
        return jsonify({
            'code': 0,
            'msg': body.get('msg') or f'导入完成，共导入 {images} 个文件',
            'data': {'imported_count': images, **(data or {})},
        })
    except Exception as e:
        logger.error(f"导入labelme数据集失败: {str(e)}", exc_info=True)
        return jsonify({'code': 500, 'msg': f'导入失败: {str(e)}'}), 500


def _download_dataset_image(image: dict) -> tuple[int | None, str | None, int, int]:
    """下载数据集图片到临时文件，返回 (image_id, temp_path, width, height)。"""
    from PIL import Image as PILImage

    image_id = image.get('id')
    image_path = image.get('path')
    if not image_path:
        return image_id, None, 0, 0

    bucket_name, object_key = _parse_minio_path(image_path)
    if not bucket_name or not object_key:
        return image_id, None, 0, 0

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    temp_file.close()

    success, error_msg = ModelService.download_from_minio(bucket_name, object_key, temp_file.name)
    if not success:
        logger.error(f"下载图片失败 image_id={image_id}: {error_msg}")
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        return image_id, None, 0, 0

    try:
        with PILImage.open(temp_file.name) as img:
            image_width, image_height = img.size
    except Exception as e:
        logger.error(f"读取图片尺寸失败 image_id={image_id}: {e}")
        os.unlink(temp_file.name)
        return image_id, None, 0, 0

    return image_id, temp_file.name, image_width, image_height


def _select_bootstrap_images(all_images, task):
    """按冷启动策略筛选图片子集。"""
    selection = task.bootstrap_selection or 'unlabeled_first'
    limit = task.bootstrap_limit or len(all_images)

    if selection == 'unlabeled_first':
        pool = [img for img in all_images if not img.get('completed')]
    elif selection == 'random':
        pool = list(all_images)
        random.shuffle(pool)
        return pool[:limit]
    elif selection == 'unlabeled_only':
        pool = [img for img in all_images if not img.get('completed')]
    else:
        pool = list(all_images)
    return pool[:limit]


def _parse_text_prompts(task) -> list:
    if not task.text_prompts:
        return []
    try:
        parsed = json.loads(task.text_prompts) if isinstance(task.text_prompts, str) else task.text_prompts
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _resolve_frame_task_stream(java_backend_url: str, frame_task: dict) -> tuple[str | None, str | None]:
    stream_url = str(frame_task.get('rtmpUrl') or '').strip()
    if stream_url:
        return stream_url, None

    try:
        task_type = int(frame_task.get('taskType') or 0)
    except (TypeError, ValueError):
        task_type = 0
    if task_type != 1:
        return None, '未配置 RTMP/RTSP 流地址'

    device_id = str(frame_task.get('deviceId') or '').strip()
    channel_id = str(frame_task.get('channelId') or '').strip()
    if not device_id or not channel_id:
        return None, 'GB28181 任务缺少设备 ID 或通道 ID'

    virtual_device_id = quote(f'gb28181_{device_id}_{channel_id}', safe='')
    resolve_url = (
        f'{java_backend_url}/admin-api/video/camera/device/'
        f'{virtual_device_id}/inference-input'
    )
    try:
        timeout_sec = int(os.getenv('AUTO_LABEL_STREAM_RESOLVE_TIMEOUT_SEC', '130'))
    except (TypeError, ValueError):
        timeout_sec = 130
    timeout_sec = max(10, min(300, timeout_sec))
    try:
        response = requests.get(resolve_url, timeout=timeout_sec)
        if response.status_code != 200:
            return None, f'视频服务解析失败: HTTP {response.status_code}'
        body = response.json()
        if body.get('code') != 0:
            return None, f'视频服务解析失败: {body.get("msg") or "未知错误"}'
        data = body.get('data') or {}
        for key in ('resolved_source', 'rtsp_direct', 'rtmp_stream', 'http_stream'):
            candidate = str(data.get(key) or '').strip()
            if candidate:
                return candidate, None
        return None, 'GB28181 点播未返回可用流地址，请先在摄像头页面验证该通道可正常播放'
    except Exception as e:
        return None, f'GB28181 流解析异常: {e}'


def _fetch_frame_tasks(
    java_backend_url: str,
    dataset_id: int,
    frame_task_ids: list | None = None,
    resolve_streams: bool = False,
) -> list:
    """拉取数据集下已配置的视频流帧捕获任务。"""
    try:
        resp = requests.get(
            f'{java_backend_url}/admin-api/dataset/frame-task/page',
            params={'datasetId': dataset_id, 'pageNo': 1, 'pageSize': 100},
            timeout=30,
        )
        if resp.status_code != 200:
            logger.warning(f'获取帧捕获任务失败: HTTP {resp.status_code}')
            return []
        body = resp.json()
        if body.get('code') != 0:
            return []
        frame_tasks = (body.get('data') or {}).get('list') or []
        if frame_task_ids is not None:
            selected_ids = set()
            for value in frame_task_ids:
                try:
                    selected_ids.add(int(value))
                except (TypeError, ValueError):
                    continue
            frame_tasks = [
                frame_task for frame_task in frame_tasks
                if int(frame_task.get('id') or 0) in selected_ids
            ]

        result = []
        for frame_task in frame_tasks:
            item = dict(frame_task)
            if resolve_streams:
                stream_url, stream_error = _resolve_frame_task_stream(java_backend_url, item)
                if stream_url:
                    item['rtmpUrl'] = stream_url
                elif stream_error:
                    item['_streamError'] = stream_error
            result.append(item)
        return result
    except Exception as e:
        logger.warning(f'获取帧捕获任务异常: {e}')
        return []


def _capture_stream_frame(stream_url: str, timeout_sec: int = 15) -> bytes | None:
    """从 RTSP/RTMP 流抓取一帧 JPEG。"""
    if not stream_url or not stream_url.strip():
        return None
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', stream_url.strip(),
        '-vframes', '1',
        '-f', 'image2pipe',
        '-vcodec', 'mjpeg',
        'pipe:1',
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout_sec)
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
        if proc.stderr:
            logger.debug(f'ffmpeg stderr: {proc.stderr.decode("utf-8", errors="ignore")[:200]}')
    except subprocess.TimeoutExpired:
        logger.warning(f'抽帧超时: {stream_url}')
    except Exception as e:
        logger.warning(f'抽帧失败 {stream_url}: {e}')
    return None


def _upload_frame_to_dataset(java_backend_url: str, dataset_id: int, image_bytes: bytes, filename: str) -> bool:
    """上传单帧到数据集。"""
    try:
        resp = requests.post(
            f'{java_backend_url}/admin-api/dataset/image/upload',
            files={'file': (filename, io.BytesIO(image_bytes), 'image/jpeg')},
            data={'datasetId': str(dataset_id), 'isZip': 'false'},
            timeout=60,
        )
        if resp.status_code != 200:
            return False
        body = resp.json()
        if body.get('code') != 0:
            return False
        data = body.get('data') or {}
        return int(data.get('successCount') or 0) > 0
    except Exception as e:
        logger.warning(f'上传帧到数据集失败: {e}')
        return False


def _sam_label_images(
    task: AutoLabelTask,
    task_id: int,
    sam_service,
    java_backend_url: str,
    images: list,
    app=None,
) -> tuple[int, int]:
    """按智能策略标注图片列表，返回 (success_count, failed_count)。"""
    from app.services.auto_label_orchestrator import (
        is_task_paused_or_cancelled,
        label_image_with_strategy,
        on_label_batch_complete,
        _update_counters,
    )
    from app.services.auto_label_dataset_writer import write_auto_label_result

    success_count = 0
    failed_count = 0
    keep_annotated_images_only = bool(
        _parse_pipeline_config(task).get('keep_annotated_images_only', True)
    )
    inference_service = None
    model_id = None
    try:
        from app.services.auto_label_strategy import get_current_model_id
        model_id = get_current_model_id(task)
        if model_id:
            from app.services.inference_service import InferenceService
            inference_service = InferenceService(model_id)
            inference_service.get_model()
    except Exception as e:
        logger.warning('YOLO 模型加载跳过: %s', e)

    for image in images:
        if is_task_paused_or_cancelled(task):
            break
        image_id, temp_path, image_width, image_height = _download_dataset_image(image)
        if not temp_path:
            failed_count += 1
            db.session.add(AutoLabelResult(
                task_id=task_id,
                dataset_image_id=image_id or image.get('id', 0),
                status='FAILED',
                error_message='下载或解析图片失败',
            ))
            continue
        try:
            annotations, mode_used = label_image_with_strategy(
                task, temp_path, image_width, image_height,
                sam_service=sam_service,
                inference_service=inference_service,
            )
            if mode_used == 'skip':
                continue
            has_detections = len(annotations) > 0
            annotations_json, _ = write_auto_label_result(
                java_backend_url,
                task.dataset_id,
                image_id,
                annotations,
                keep_annotated_images_only=keep_annotated_images_only,
                timeout=10,
            )
            db.session.add(AutoLabelResult(
                task_id=task_id,
                dataset_image_id=image_id,
                annotations=annotations_json,
                status='SUCCESS',
            ))
            if has_detections:
                success_count += 1
            _update_counters(task, mode_used, has_detections=has_detections)
        except Exception as e:
            logger.error(f'处理图片失败: {e}', exc_info=True)
            failed_count += 1
            db.session.add(AutoLabelResult(
                task_id=task_id,
                dataset_image_id=image_id or image.get('id', 0),
                status='FAILED',
                error_message=str(e),
            ))
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    if app and success_count > 0:
        on_label_batch_complete(task, app)
    return success_count, failed_count


def _successful_auto_label_image_ids(task_id: int) -> set[int]:
    rows = AutoLabelResult.query.with_entities(AutoLabelResult.dataset_image_id).filter_by(
        task_id=task_id,
        status='SUCCESS',
    ).all()
    return {int(row[0]) for row in rows}


def execute_pipeline_task(app, task_id: int):
    """无人值守流水线：循环采集 → 标注 → 结束后打包。"""
    task = None
    with app.app_context():
        try:
            task = AutoLabelTask.query.get(task_id)
            if not task:
                logger.error(f'流水线任务不存在: {task_id}')
                return

            cfg = _parse_pipeline_config(task)
            duration_hours = int(cfg.get('duration_hours', 8))
            capture_interval = int(cfg.get('capture_interval_sec', 30))
            auto_export = bool(cfg.get('auto_export', True))
            deadline = beijing_now() + timedelta(hours=duration_hours)

            java_backend_url = _dataset_java_base()
            sam_service = get_sam_service()
            sam_service.warmup_if_needed()

            task.status = 'PROCESSING'
            task.started_at = beijing_now()
            _save_pipeline_config(task, {'pipeline_status': 'collecting'})
            _pipeline_log(task, f'流水线已启动，计划运行 {duration_hours} 小时')
            db.session.commit()

            captured_total = 0
            labeled_total = 0
            cycle = 0

            selected_frame_task_ids = None
            if task.selected_frame_task_ids:
                try:
                    parsed_ids = json.loads(task.selected_frame_task_ids)
                    if isinstance(parsed_ids, list) and parsed_ids:
                        selected_frame_task_ids = parsed_ids
                except (TypeError, ValueError, json.JSONDecodeError):
                    selected_frame_task_ids = None

            while beijing_now() < deadline:
                db.session.refresh(task)
                from app.services.auto_label_orchestrator import is_task_paused_or_cancelled
                if is_task_paused_or_cancelled(task):
                    _pipeline_log(task, '任务已暂停或取消，流水线停止')
                    db.session.commit()
                    return

                cycle += 1
                remaining_min = int((deadline - beijing_now()).total_seconds() / 60)
                _pipeline_log(task, f'第 {cycle} 轮采集开始（剩余约 {remaining_min} 分钟）')

                frame_tasks = _fetch_frame_tasks(
                    java_backend_url,
                    task.dataset_id,
                    frame_task_ids=selected_frame_task_ids,
                    resolve_streams=True,
                )
                if not frame_tasks:
                    _pipeline_log(
                        task,
                        '未找到视频流帧捕获任务，请在「添加 → 视频流抽帧任务」中配置 RTMP/RTSP 地址',
                    )
                else:
                    for ft in frame_tasks:
                        stream_url = (ft.get('rtmpUrl') or '').strip()
                        if not stream_url:
                            task_name = ft.get('taskName') or f'任务 {ft.get("id")}'
                            stream_error = ft.get('_streamError') or '未配置可用流地址'
                            _pipeline_log(task, f'无法抽帧: {task_name}，{stream_error}')
                            continue
                        img_bytes = _capture_stream_frame(stream_url)
                        if not img_bytes:
                            _pipeline_log(task, f'抽帧失败: {ft.get("taskName") or stream_url[:40]}')
                            continue
                        fname = f'cap_{beijing_now().strftime("%Y%m%d%H%M%S%f")}.jpg'
                        if _upload_frame_to_dataset(java_backend_url, task.dataset_id, img_bytes, fname):
                            captured_total += 1
                            _save_pipeline_config(task, {'captured_count': captured_total})
                            task.processed_images = captured_total + labeled_total
                            db.session.commit()

                all_images = _fetch_all_dataset_images(java_backend_url, task.dataset_id)
                attempted_image_ids = _successful_auto_label_image_ids(task_id)
                unlabeled = [
                    img for img in all_images
                    if not img.get('completed') and img.get('id') not in attempted_image_ids
                ]
                batch = unlabeled[:30]

                if batch:
                    _save_pipeline_config(task, {'pipeline_status': 'labeling'})
                    _pipeline_log(task, f'开始标注 {len(batch)} 张（待标注共 {len(unlabeled)} 张）')
                    db.session.commit()

                    ok, fail = _sam_label_images(task, task_id, sam_service, java_backend_url, batch, app)
                    labeled_total += ok
                    task.success_count = labeled_total
                    task.failed_count = (task.failed_count or 0) + fail
                    task.total_images = captured_total
                    task.processed_images = captured_total + labeled_total
                    _save_pipeline_config(task, {
                        'pipeline_status': 'collecting',
                        'labeled_count': labeled_total,
                    })
                    _pipeline_log(task, f'本轮标注完成：成功 {ok}，失败 {fail}')
                    db.session.commit()

                if beijing_now() >= deadline:
                    break
                time.sleep(capture_interval)

            _pipeline_log(task, '采集阶段结束，执行最终全量标注')
            _save_pipeline_config(task, {'pipeline_status': 'labeling'})
            db.session.commit()

            all_images = _fetch_all_dataset_images(java_backend_url, task.dataset_id)
            attempted_image_ids = _successful_auto_label_image_ids(task_id)
            unlabeled = [
                img for img in all_images
                if not img.get('completed') and img.get('id') not in attempted_image_ids
            ]
            if unlabeled:
                ok, fail = _sam_label_images(task, task_id, sam_service, java_backend_url, unlabeled, app)
                labeled_total += ok
                task.failed_count = (task.failed_count or 0) + fail
                _pipeline_log(task, f'最终标注：成功 {ok}，失败 {fail}')

            all_images = _fetch_all_dataset_images(java_backend_url, task.dataset_id)

            task.success_count = labeled_total
            task.total_images = max(captured_total, len(all_images))
            task.processed_images = task.total_images

            if auto_export and labeled_total > 0:
                _save_pipeline_config(task, {'pipeline_status': 'packaging'})
                _pipeline_log(task, '开始自动划分用途并打包导出')
                db.session.commit()
                try:
                    text_prompts = _parse_text_prompts(task)
                    export_body = {
                        'trainRatio': float(cfg.get('export_train_ratio', 0.7)),
                        'valRatio': float(cfg.get('export_val_ratio', 0.2)),
                        'testRatio': float(cfg.get('export_test_ratio', 0.1)),
                        'sampleSelection': 'all',
                        'selectedClasses': text_prompts,
                        'exportPrefix': f'sam_pipeline_{task.dataset_id}',
                    }
                    resp = requests.post(
                        _dataset_annotation_url(task.dataset_id, 'export'),
                        json=export_body,
                        timeout=1800,
                    )
                    if resp.ok:
                        _save_pipeline_config(task, {'packaged': True})
                        _pipeline_log(task, '数据集已自动打包导出')
                    else:
                        _pipeline_log(task, f'自动打包失败: HTTP {resp.status_code}')
                except Exception as e:
                    _pipeline_log(task, f'自动打包异常: {e}')

            task.status = 'COMPLETED'
            task.completed_at = beijing_now()
            _save_pipeline_config(task, {'pipeline_status': 'done'})
            _pipeline_log(task, f'流水线完成：采集 {captured_total} 张，标注 {labeled_total} 张')
            db.session.commit()

        except Exception as e:
            logger.error(f'执行无人值守流水线失败: {str(e)}', exc_info=True)
            if task:
                task.status = 'FAILED'
                task.error_message = str(e)
                task.completed_at = beijing_now()
                _save_pipeline_config(task, {'pipeline_status': 'failed'})
                _pipeline_log(task, f'流水线失败: {e}')
                db.session.commit()


def execute_auto_label_task(app, task_id):
    """执行自动化标注任务：YOLO 直连 InferenceService 或 SAM 进程内推理。"""
    task = None
    with app.app_context():
        try:
            task = AutoLabelTask.query.get(task_id)
            if not task:
                logger.error(f"任务不存在: {task_id}")
                return

            label_mode = (task.label_mode or 'yolo').lower()
            inference_service = None
            sam_service = None

            if label_mode == 'sam':
                sam_service = get_sam_service()
                sam_service.warmup_if_needed()
                text_prompts = _parse_text_prompts(task)
                if not text_prompts:
                    raise Exception('SAM 任务缺少 text_prompts')
            else:
                model_id = task.model_id
                if not model_id and task.model_service_id:
                    ai_service = AIService.query.get(task.model_service_id)
                    model_id = ai_service.model_id if ai_service else None
                if not model_id:
                    raise Exception('任务未关联有效模型')
                inference_service = InferenceService(model_id)
                inference_service.get_model()

            task.status = 'PROCESSING'
            task.started_at = beijing_now()
            db.session.commit()

            java_backend_url = _dataset_java_base()
            logger.info(f"开始获取数据集图片列表: dataset_id={task.dataset_id}, label_mode={label_mode}")

            images = _fetch_all_dataset_images(java_backend_url, task.dataset_id)

            if task.phase == 'BOOTSTRAP' or (task.bootstrap_limit and label_mode == 'sam' and task.phase != 'PIPELINE'):
                images = _select_bootstrap_images(images, task)
            elif task.bootstrap_selection == 'unlabeled_only':
                images = [img for img in images if not img.get('completed')]

            task.total_images = len(images)
            task.processed_images = 0
            task.success_count = 0
            task.failed_count = 0
            db.session.commit()

            if not images:
                if task.phase == 'BOOTSTRAP':
                    raise RuntimeError(
                        '数据集中暂无待标注图片。请先通过「添加 → 视频流抽帧任务」配置摄像头采集，'
                        '或导入图片后再启动 SAM 标注。'
                    )
                logger.info(f'数据集 {task.dataset_id} 无待处理图片，任务直接完成')
                task.status = 'COMPLETED'
                task.completed_at = beijing_now()
                db.session.commit()
                return

            logger.info(f"数据集 {task.dataset_id} 本批 {len(images)} 张，label_mode={label_mode}")

            success_count = 0
            failed_count = 0
            sam_hit_count = 0
            sam_empty_count = 0
            prefetch_workers = int(os.getenv('AUTO_LABEL_PREFETCH_WORKERS', '2'))
            annotation_type = task.annotation_type or 'rectangle'
            return_masks = bool(task.return_masks)

            def _iter_with_prefetch(items):
                def _download_in_app_context(image):
                    with app.app_context():
                        return _download_dataset_image(image)

                if prefetch_workers <= 1 or len(items) <= 1:
                    for item in items:
                        yield _download_dataset_image(item)
                    return
                with ThreadPoolExecutor(max_workers=prefetch_workers) as pool:
                    futures = {
                        pool.submit(_download_in_app_context, img): idx
                        for idx, img in enumerate(items)
                    }
                    results = [None] * len(items)
                    for future in as_completed(futures):
                        results[futures[future]] = future.result()
                    for row in results:
                        yield row

            for idx, (image_id, temp_path, image_width, image_height) in enumerate(_iter_with_prefetch(images)):
                image = images[idx]
                if not temp_path:
                    failed_count += 1
                    db.session.add(AutoLabelResult(
                        task_id=task_id,
                        dataset_image_id=image_id or image.get('id', 0),
                        status='FAILED',
                        error_message='下载或解析图片失败',
                    ))
                else:
                    try:
                        if label_mode == 'sam':
                            sam_result = sam_service.predict(
                                temp_path,
                                text=_parse_text_prompts(task),
                                return_masks=return_masks,
                                conf=task.confidence_threshold,
                            )
                            annotations = to_annotations(
                                sam_result, image_width, image_height,
                                annotation_type=annotation_type,
                            )
                        else:
                            detections = inference_service.detect_image_file(temp_path, {
                                'conf_thres': task.confidence_threshold,
                                'iou_thres': 0.45,
                            })
                            annotations = _parse_inference_result(
                                {'detections': detections}, image_width, image_height
                            )
                        db.session.add(AutoLabelResult(
                            task_id=task_id,
                            dataset_image_id=image_id,
                            annotations=json.dumps(annotations, ensure_ascii=False),
                            status='SUCCESS',
                        ))
                        update_response = requests.put(
                            f"{java_backend_url}/admin-api/dataset/image/update",
                            json={
                                'id': image_id,
                                'datasetId': task.dataset_id,
                                'annotations': json.dumps(annotations, ensure_ascii=False),
                                'completed': 1 if annotations else 0,
                            },
                            timeout=10,
                        )
                        if update_response.status_code != 200:
                            logger.warning(f"更新图片标注失败: {image_id}")
                        success_count += 1
                        if label_mode == 'sam':
                            if annotations:
                                sam_hit_count += 1
                            else:
                                sam_empty_count += 1
                    except Exception as e:
                        logger.error(f"处理图片失败: {e}", exc_info=True)
                        failed_count += 1
                        db.session.add(AutoLabelResult(
                            task_id=task_id,
                            dataset_image_id=image_id or image.get('id', 0),
                            status='FAILED',
                            error_message=str(e),
                        ))
                    finally:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)

                task.processed_images = idx + 1
                task.success_count = success_count
                task.failed_count = failed_count
                if (idx + 1) % _AUTO_LABEL_PROGRESS_COMMIT_INTERVAL == 0 or idx + 1 == len(images):
                    db.session.commit()

            task.status = 'COMPLETED'
            task.completed_at = beijing_now()
            if label_mode == 'sam' and (sam_hit_count + sam_empty_count) > 0:
                from app.services.sam_bootstrap_quality import assess_sam_bootstrap_quality

                cfg = {}
                if task.pipeline_config:
                    try:
                        cfg = json.loads(task.pipeline_config)
                    except Exception:
                        cfg = {}
                cfg['sam_hit_count'] = sam_hit_count
                cfg['sam_empty_count'] = sam_empty_count
                task.pipeline_config = json.dumps(cfg, ensure_ascii=False)
                db.session.flush()
                quality = assess_sam_bootstrap_quality(task, 0.3)
                cfg['sam_quality'] = quality
                cfg['sam_quality_passed'] = quality['sam_quality_passed']
                cfg['awaiting_sam_review'] = not quality['sam_quality_passed']
                task.pipeline_config = json.dumps(cfg, ensure_ascii=False)
            db.session.commit()

            logger.info(
                f"自动化标注完成: task_id={task_id}, success={success_count}, failed={failed_count}"
            )

        except Exception as e:
            logger.error(f"执行自动化标注任务失败: {str(e)}", exc_info=True)
            if task:
                task.status = 'FAILED'
                task.error_message = str(e)
                task.completed_at = beijing_now()
                db.session.commit()


def _parse_minio_path(path):
    """解析MinIO路径，返回bucket和object_key"""
    # 格式: /api/v1/buckets/{bucket}/objects/download?prefix={object_key}
    from urllib.parse import urlparse, parse_qs

    try:
        parsed = urlparse(path)
        path_parts = parsed.path.split('/')

        if len(path_parts) >= 5 and path_parts[3] == 'buckets':
            bucket_name = path_parts[4]
        else:
            return None, None

        query_params = parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]

        return bucket_name, object_key
    except Exception as e:
        logger.error(f"解析MinIO路径失败: {path}, 错误: {str(e)}")
        return None, None


def _parse_inference_result(result, image_width, image_height):
    """解析推理结果，转换为标注格式（归一化坐标 + {x,y}格式）"""
    annotations = []

    try:
        if not result:
            return annotations

        # 检查返回格式：可能是 {'code': 0, 'data': {...}} 或直接是 data
        if isinstance(result, dict) and 'code' in result:
            if result.get('code') != 0:
                logger.warning(f"推理返回错误: {result.get('msg', '未知错误')}")
                return annotations
            predictions = result.get('data', {}).get('predictions', [])
        elif isinstance(result, dict) and 'data' in result:
            predictions = result.get('data', {}).get('predictions', [])
        elif isinstance(result, dict) and 'predictions' in result:
            predictions = result.get('predictions', [])
        elif isinstance(result, dict) and 'detections' in result:
            predictions = result.get('detections', [])
        else:
            logger.warning(f"无法识别的推理结果格式: {type(result)}")
            return annotations

        # 验证图片尺寸
        if not image_width or not image_height or image_width <= 0 or image_height <= 0:
            logger.error(f"图片尺寸无效: width={image_width}, height={image_height}")
            return annotations

        for pred in predictions:
            try:
                # 推理结果格式: {'class': int, 'class_name': str, 'confidence': float, 'bbox': [x1, y1, x2, y2]}
                class_id = pred.get('class')
                class_name = pred.get('class_name', '')
                confidence = float(pred.get('confidence', 0))
                bbox = pred.get('bbox', [])

                # 如果没有class_name，尝试使用class_id
                if not class_name and class_id is not None:
                    class_name = str(class_id)

                if not class_name or not bbox or len(bbox) < 4:
                    continue

                x1, y1, x2, y2 = bbox[:4]

                # 确保坐标在图片范围内
                x1 = max(0, min(x1, image_width))
                y1 = max(0, min(y1, image_height))
                x2 = max(0, min(x2, image_width))
                y2 = max(0, min(y2, image_height))

                # **关键修复**: 将像素坐标归一化为0-1范围
                norm_x1 = x1 / image_width
                norm_y1 = y1 / image_height
                norm_x2 = x2 / image_width
                norm_y2 = y2 / image_height

                # **关键修复**: 转换为前端期望的格式 - 归一化坐标 + {x, y}对象格式 + label字段
                annotation = {
                    'label': class_name,  # 使用label字段而不是class，匹配手动标注
                    'confidence': confidence,
                    'points': [
                        {'x': norm_x1, 'y': norm_y1},
                        {'x': norm_x2, 'y': norm_y1},
                        {'x': norm_x2, 'y': norm_y2},
                        {'x': norm_x1, 'y': norm_y2}
                    ],
                    'type': 'rectangle',
                    'auto': True,
                    'color': '#52c41a'  # AI标注使用绿色
                }
                annotations.append(annotation)

                logger.debug(f"转换标注: {class_name}, 像素[{x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}] -> 归一化[{norm_x1:.3f},{norm_y1:.3f},{norm_x2:.3f},{norm_y2:.3f}]")

            except Exception as e:
                logger.error(f"解析单个预测结果失败: {str(e)}, pred: {pred}")
                continue
            
    except Exception as e:
        logger.error(f"解析推理结果失败: {str(e)}", exc_info=True)
    
    return annotations
    