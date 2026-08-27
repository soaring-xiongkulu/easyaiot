"""
智能标注编排器：按策略执行 SAM / YOLO / 混合标注，驱动阶段流转。
"""
import json
import logging
import os
import threading
from datetime import datetime

import requests

from db_models import db, AutoLabelTask, Model, TrainTask
from app.services.auto_label_strategy import (
    PHASE_BOOTSTRAP_SAM,
    PHASE_CANCELLED,
    PHASE_COLLECTING,
    PHASE_DONE,
    PHASE_ITERATE,
    PHASE_PACKAGING,
    PHASE_PAUSED,
    PHASE_TRAINING,
    PHASE_YOLO_LABEL,
    advance_phase_after_bootstrap,
    decide_label_mode,
    get_counters,
    get_current_model_id,
    get_pipeline_phase,
    get_strategy,
    initial_pipeline_phase,
    merge_strategy,
    parse_pipeline_state,
    should_trigger_training,
)
from app.services.inference_service import InferenceService
from app.services.sam_service import get_sam_service
from app.utils.sam_result_parser import to_annotations

logger = logging.getLogger(__name__)


def _java_base() -> str:
    return os.getenv(
        'JAVA_BACKEND_URL',
        os.getenv('GATEWAY_URL', 'http://localhost:48080'),
    ).rstrip('/')


def _save_pipeline_state(task: AutoLabelTask, updates: dict) -> dict:
    state = parse_pipeline_state(task)
    state.update(updates)
    if 'logs' in state and isinstance(state['logs'], list):
        state['logs'] = state['logs'][-80:]
    task.pipeline_config = json.dumps(state, ensure_ascii=False)
    return state


def _log(task: AutoLabelTask, message: str) -> None:
    state = parse_pipeline_state(task)
    logs = state.get('logs') if isinstance(state.get('logs'), list) else []
    logs.append({'time': datetime.now().isoformat(timespec='seconds'), 'message': message})
    _save_pipeline_state(task, {'logs': logs})
    logger.info('[orchestrator task=%s] %s', task.id, message)


def is_task_paused_or_cancelled(task: AutoLabelTask) -> bool:
    return get_pipeline_phase(task) in (PHASE_PAUSED, PHASE_CANCELLED) or task.status in ('PAUSED', 'CANCELLED')


def pause_task(task_id: int) -> bool:
    task = AutoLabelTask.query.get(task_id)
    if not task or task.status in ('COMPLETED', 'FAILED', 'CANCELLED'):
        return False
    state = parse_pipeline_state(task)
    task.status = 'PAUSED'
    _save_pipeline_state(task, {
        'pipeline_phase': PHASE_PAUSED,
        'paused_from_phase': state.get('pipeline_phase') or PHASE_YOLO_LABEL,
    })
    _log(task, '任务已暂停')
    db.session.commit()
    return True


def resume_task(task_id: int) -> bool:
    task = AutoLabelTask.query.get(task_id)
    if not task or task.status != 'PAUSED':
        return False
    state = parse_pipeline_state(task)
    prev = state.get('paused_from_phase') or PHASE_YOLO_LABEL
    task.status = 'PROCESSING'
    _save_pipeline_state(task, {'pipeline_phase': prev, 'paused_from_phase': None})
    _log(task, '任务已恢复')
    db.session.commit()
    return True


def cancel_task(task_id: int) -> bool:
    task = AutoLabelTask.query.get(task_id)
    if not task or task.status in ('COMPLETED', 'CANCELLED'):
        return False
    task.status = 'CANCELLED'
    task.completed_at = datetime.now()
    _save_pipeline_state(task, {'pipeline_phase': PHASE_CANCELLED})
    _log(task, '任务已取消')
    from db_models import AutoLabelSubTask
    for st in AutoLabelSubTask.query.filter_by(parent_task_id=task_id).all():
        if st.status not in ('COMPLETED', 'FAILED', 'CANCELLED'):
            st.status = 'CANCELLED'
            st.completed_at = datetime.now()
            if st.workload_id:
                try:
                    from app.utils import node_client
                    from app.services.auto_label_cluster_service import WORKLOAD_TYPE_AUTO_LABEL
                    node_client.release_binding(WORKLOAD_TYPE_AUTO_LABEL, st.workload_id)
                except Exception:
                    pass
    db.session.commit()
    return True


def _parse_text_prompts(task) -> list:
    if not task.text_prompts:
        return []
    try:
        p = json.loads(task.text_prompts) if isinstance(task.text_prompts, str) else task.text_prompts
        return p if isinstance(p, list) else []
    except Exception:
        return []


def _yolo_to_annotations(detections: list, image_width: int, image_height: int) -> list:
    annotations = []
    for det in detections or []:
        bbox = det.get('bbox') or det.get('box')
        if not bbox or len(bbox) < 4:
            continue
        x1, y1, x2, y2 = bbox[:4]
        norm_x1, norm_y1 = float(x1) / image_width, float(y1) / image_height
        norm_x2, norm_y2 = float(x2) / image_width, float(y2) / image_height
        annotations.append({
            'type': 'rectangle',
            'label': det.get('class_name') or det.get('label') or 'object',
            'points': [
                {'x': norm_x1, 'y': norm_y1},
                {'x': norm_x2, 'y': norm_y1},
                {'x': norm_x2, 'y': norm_y2},
                {'x': norm_x1, 'y': norm_y2},
            ],
            'confidence': det.get('confidence') or det.get('conf'),
        })
    return annotations


def label_image_with_strategy(
    task: AutoLabelTask,
    temp_path: str,
    image_width: int,
    image_height: int,
    *,
    sam_service=None,
    inference_service=None,
) -> tuple[list, str]:
    """
    按策略标注单张图。返回 (annotations, mode_used)。
    """
    strategy = get_strategy(task)
    yolo_count = 0
    detections = []

    model_id = get_current_model_id(task)
    mode = decide_label_mode(task, yolo_detection_count=0)

    if mode in ('yolo', 'yolo_sam_supplement') and model_id:
        if inference_service is None:
            inference_service = InferenceService(model_id)
            inference_service.get_model()
        detections = inference_service.detect_image_file(temp_path, {
            'conf_thres': strategy.get('yolo_confidence', 0.5),
            'iou_thres': 0.45,
        })
        yolo_count = len(detections or [])
        mode = decide_label_mode(task, yolo_detection_count=yolo_count)

    if mode == 'sam' or mode == 'yolo_sam_supplement':
        if sam_service is None:
            sam_service = get_sam_service()
        sam_result = sam_service.predict(
            temp_path,
            text=_parse_text_prompts(task),
            return_masks=bool(task.return_masks),
            conf=strategy.get('sam_confidence', 0.45),
        )
        sam_annos = to_annotations(
            sam_result, image_width, image_height,
            annotation_type=task.annotation_type or 'rectangle',
        )
        if mode == 'yolo_sam_supplement' and detections:
            yolo_annos = _yolo_to_annotations(detections, image_width, image_height)
            return yolo_annos + sam_annos, mode
        return sam_annos, mode

    if detections:
        return _yolo_to_annotations(detections, image_width, image_height), 'yolo'

    return [], mode


def _update_counters(task: AutoLabelTask, mode_used: str, *, has_detections: bool = True) -> None:
    state = parse_pipeline_state(task)
    counters = get_counters(task)
    counters['total_labeled'] = counters['total_labeled'] + 1
    if mode_used == 'sam':
        counters['sam_labeled'] += 1
    elif mode_used == 'yolo':
        counters['yolo_labeled'] += 1
    elif mode_used == 'yolo_sam_supplement':
        counters['yolo_labeled'] += 1
        counters['sam_supplemented'] += 1
    updates = dict(counters)
    if mode_used in ('sam', 'yolo_sam_supplement'):
        hit_key = 'sam_hit_count' if has_detections else 'sam_empty_count'
        updates[hit_key] = int(state.get(hit_key) or 0) + 1
    _save_pipeline_state(task, updates)
    task.success_count = counters['total_labeled']


def _trigger_auto_train(task: AutoLabelTask, app) -> None:
    """后台触发 YOLO 训练（首轮或迭代）。"""
    state = parse_pipeline_state(task)
    if state.get('pipeline_phase') == PHASE_TRAINING:
        existing_tid = state.get('train_task_id')
        if existing_tid:
            from app.blueprints.train import ACTIVE_TRAIN_STATUSES
            tt = TrainTask.query.get(int(existing_tid))
            if tt and tt.status in ACTIVE_TRAIN_STATUSES:
                return

    strategy = get_strategy(task)
    if not strategy.get('auto_train_yolo'):
        _log(task, '策略未开启自动训练，直接进入 YOLO 量产')
        init_model = strategy.get('initial_model_id')
        if init_model:
            task.model_id = int(init_model)
            _save_pipeline_state(task, {
                'pipeline_phase': PHASE_YOLO_LABEL,
                'current_model_id': int(init_model),
            })
        else:
            _save_pipeline_state(task, {'pipeline_phase': PHASE_YOLO_LABEL})
        db.session.commit()
        return

    counters = get_counters(task)
    round_no = counters['train_round'] + 1
    _save_pipeline_state(task, {
        'pipeline_phase': PHASE_TRAINING,
        'train_round': round_no,
        'pending_train': True,
    })
    _log(task, f'开始第 {round_no} 轮 YOLO 自动训练（导出→训练→发布模型）…')
    db.session.commit()

    def _run():
        with app.app_context():
            from db_models import TrainTask
            from app.services.auto_label_train_service import run_auto_train_pipeline

            t = AutoLabelTask.query.get(task.id)
            if not t:
                return

            def _cancelled() -> bool:
                fresh = AutoLabelTask.query.get(task.id)
                return fresh is not None and is_task_paused_or_cancelled(fresh)

            model_id = run_auto_train_pipeline(
                t,
                app,
                round_no=round_no,
                log_fn=lambda msg: _log(AutoLabelTask.query.get(task.id), msg),
                cancelled_check=_cancelled,
            )

            t = AutoLabelTask.query.get(task.id)
            if not t or _cancelled():
                if t:
                    _log(t, '训练流程因任务取消/暂停而中止')
                    prev = parse_pipeline_state(t).get('current_model_id')
                    _save_pipeline_state(t, {
                        'pipeline_phase': PHASE_YOLO_LABEL if prev else PHASE_BOOTSTRAP_SAM,
                        'pending_train': False,
                    })
                    db.session.commit()
                return

            if model_id:
                next_phase = PHASE_ITERATE if round_no > 1 else PHASE_YOLO_LABEL
                _save_pipeline_state(t, {
                    'pipeline_phase': next_phase,
                    'current_model_id': model_id,
                    'pending_train': False,
                    'train_task_id': parse_pipeline_state(t).get('train_task_id'),
                })
                t.model_id = model_id
                _log(t, f'第 {round_no} 轮训练完成，已切换至 YOLO 量产（model_id={model_id}）')
            else:
                _log(t, f'第 {round_no} 轮训练未产出可用模型，保持 SAM 冷启动/补充模式')
                _save_pipeline_state(t, {
                    'pipeline_phase': PHASE_BOOTSTRAP_SAM,
                    'pending_train': False,
                })
            db.session.commit()

    threading.Thread(target=_run, daemon=True).start()


def on_label_batch_complete(task: AutoLabelTask, app) -> None:
    """一批标注完成后检查阶段流转。"""
    if is_task_paused_or_cancelled(task):
        return
    counters = get_counters(task)
    strategy = get_strategy(task)
    phase = get_pipeline_phase(task)
    bootstrap = int(strategy['bootstrap_sam_limit'])

    if phase in (PHASE_COLLECTING, PHASE_BOOTSTRAP_SAM) and counters['total_labeled'] >= bootstrap:
        from app.services.sam_bootstrap_quality import assess_sam_bootstrap_quality

        min_hit_rate = float(strategy.get('sam_bootstrap_min_hit_rate') or 0.3)
        quality = assess_sam_bootstrap_quality(task, min_hit_rate)
        _save_pipeline_state(task, {
            'sam_quality': quality,
            'sam_quality_passed': quality['sam_quality_passed'],
        })
        if not quality['sam_quality_passed']:
            _save_pipeline_state(task, {'awaiting_sam_review': True})
            _log(
                task,
                f'SAM 冷启动识别率 {quality["recognition_rate_pct"]}% 低于阈值 '
                f'{quality["min_hit_rate_pct"]}%，建议恢复初始标注并改用手动标注或 YOLO 自动标注',
            )
            db.session.commit()
            return

        next_phase = advance_phase_after_bootstrap(task)
        _save_pipeline_state(task, {
            'pipeline_phase': next_phase,
            'awaiting_sam_review': False,
        })
        _log(task, f'SAM 冷启动完成（{counters["total_labeled"]} 张，识别率 {quality["recognition_rate_pct"]}%），进入阶段：{next_phase}')
        db.session.commit()
        if next_phase == PHASE_TRAINING:
            _trigger_auto_train(task, app)
        return

    if should_trigger_training(task):
        total = counters['total_labeled']
        _save_pipeline_state(task, {'last_iterate_at_labeled': total})
        db.session.commit()
        _trigger_auto_train(task, app)


def init_pipeline_strategy(task: AutoLabelTask, strategy_raw: dict | None) -> None:
    """初始化流水线策略到 pipeline_config。"""
    strategy = merge_strategy(strategy_raw)
    start_phase = initial_pipeline_phase(strategy)
    state = {
        'mode': 'smart_pipeline',
        'strategy': strategy,
        'pipeline_phase': start_phase,
        'current_model_id': strategy.get('initial_model_id'),
        'total_labeled': 0,
        'sam_labeled': 0,
        'yolo_labeled': 0,
        'sam_supplemented': 0,
        'sam_hit_count': 0,
        'sam_empty_count': 0,
        'captured_count': 0,
        'train_round': 0,
        'logs': [],
    }
    if strategy.get('initial_model_id'):
        task.model_id = int(strategy['initial_model_id'])
    task.pipeline_config = json.dumps(state, ensure_ascii=False)


def maybe_kickoff_skip_sam_pipeline(task: AutoLabelTask, app) -> None:
    """跳过 SAM 且需先训练时，启动后立刻触发训练。"""
    strategy = get_strategy(task)
    phase = get_pipeline_phase(task)
    if strategy.get('skip_sam_cold_start') and phase == PHASE_TRAINING:
        _trigger_auto_train(task, app)
