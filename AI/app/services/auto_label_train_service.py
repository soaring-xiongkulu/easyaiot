"""
自动标注流水线 — YOLO 自动训练：导出数据集 → 开训 → 轮询 → 发布模型。
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import tempfile
import threading
import time
from datetime import datetime

import requests

from db_models import db, AutoLabelTask, Model, TrainTask
from app.services.auto_label_strategy import (
    get_strategy,
    parse_pipeline_state,
    resolve_model_arch_path,
    resolve_train_pretrained_path,
)

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 30
TRAIN_WAIT_TIMEOUT_SEC = int(os.getenv('AUTO_LABEL_TRAIN_TIMEOUT_SEC', str(6 * 3600)))


def _java_base() -> str:
    return os.getenv(
        'JAVA_BACKEND_URL',
        os.getenv('GATEWAY_URL', 'http://localhost:48080'),
    ).rstrip('/')


def export_annotated_yolo_zip(
    dataset_id: int,
    *,
    text_prompts: list[str],
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
    export_prefix: str | None = None,
) -> str:
    """从 iot-dataset 导出已标注图片为 YOLO zip，返回本地临时文件路径。"""
    if not text_prompts:
        raise ValueError('导出训练集需要 text_prompts（类别词）')

    body = {
        'trainRatio': train_ratio,
        'valRatio': val_ratio,
        'testRatio': test_ratio,
        'sampleSelection': 'annotated',
        'selectedClasses': text_prompts,
        'exportPrefix': export_prefix or f'auto_label_{dataset_id}',
    }
    url = f'{_java_base()}/admin-api/dataset/{dataset_id}/annotation/export'
    resp = requests.post(url, json=body, stream=True, timeout=1800)
    if resp.status_code != 200:
        detail = ''
        try:
            detail = resp.text[:200]
        except Exception:
            pass
        raise RuntimeError(f'导出 YOLO 数据集失败 HTTP {resp.status_code}: {detail}')

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip', prefix=f'al_export_{dataset_id}_')
    try:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                tmp.write(chunk)
        tmp.flush()
    finally:
        tmp.close()

    if os.path.getsize(tmp.name) < 100:
        os.unlink(tmp.name)
        raise RuntimeError('导出的训练集 zip 为空，请确认已有足够标注数据')

    return tmp.name


def split_dataset_usage(dataset_id: int, train_ratio: float, val_ratio: float, test_ratio: float) -> None:
    requests.post(
        f'{_java_base()}/admin-api/dataset/{dataset_id}/split',
        json={'trainRatio': train_ratio, 'valRatio': val_ratio, 'testRatio': test_ratio},
        timeout=120,
    ).raise_for_status()


def start_yolo_train(
    *,
    dataset_zip_path: str,
    dataset_id: int,
    round_no: int,
    strategy: dict,
    pretrained_arch: str | None = None,
) -> TrainTask:
    """创建 TrainTask 并启动训练（集群模式下自动调度到 GPU 节点）。"""
    from app.blueprints.train import _build_train_hyperparameters, _start_train_execution
    from app.blueprints.train_task import build_train_task_name
    from app.services.train_launcher_service import resolve_schedule_policy

    epochs = int(strategy.get('train_epochs') or 50)
    batch_size = int(strategy.get('train_batch_size') or 16)
    img_size = int(strategy.get('train_imgsz') or 640)
    model_arch = pretrained_arch or resolve_model_arch_path(strategy.get('model_arch'))
    use_gpu = bool(strategy.get('use_gpu', True))
    task_base = f'auto-label-ds{dataset_id}-r{round_no}'

    train_task = TrainTask(
        name='',
        dataset_path=dataset_zip_path,
        dataset_name=f'dataset-{dataset_id}',
        dataset_version=f'r{round_no}',
        hyperparameters=_build_train_hyperparameters(
            epochs, model_arch, img_size, batch_size, use_gpu, task_base, None, 'local',
        ),
        start_time=datetime.utcnow(),
        status='preparing',
        train_log='',
        checkpoint_dir='',
        schedule_policy=resolve_schedule_policy(strategy.get('schedule_policy')),
    )
    db.session.add(train_task)
    db.session.flush()
    train_task.name = build_train_task_name(task_base, train_task.dataset_name, train_task.dataset_version, train_task.id)
    db.session.commit()

    ok, msg = _start_train_execution(
        train_task,
        task_id=train_task.id,
        epochs=epochs,
        model_arch=model_arch,
        img_size=img_size,
        batch_size=batch_size,
        use_gpu=use_gpu,
        dataset_zip_path=dataset_zip_path,
        request_gpu_ids=None,
        dataset_source='local',
        is_resume=False,
    )
    if not ok:
        raise RuntimeError(msg)
    return train_task


def wait_train_task(
    train_task_id: int,
    *,
    timeout_sec: int = TRAIN_WAIT_TIMEOUT_SEC,
    cancelled_check=None,
) -> TrainTask | None:
    """轮询训练任务直到完成/失败/取消。"""
    from app.blueprints.train import ACTIVE_TRAIN_STATUSES

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if cancelled_check and cancelled_check():
            return None
        # 训练执行器可能在独立进程中更新任务；清理 identity map，避免一直读到启动时缓存状态。
        db.session.expire_all()
        task = TrainTask.query.get(train_task_id)
        if not task:
            return None
        if task.status == 'completed':
            return task
        if task.status in ('error', 'stopped', 'failed'):
            return task
        if task.status not in ACTIVE_TRAIN_STATUSES and task.status != 'completed':
            return task
        time.sleep(POLL_INTERVAL_SEC)
    db.session.expire_all()
    return TrainTask.query.get(train_task_id)


def extract_map50(train_task: TrainTask) -> float | None:
    """从训练结果 CSV 提取 mAP50（用于 SAM 补充停止策略）。"""
    csv_bytes = None
    metrics_url = (train_task.metrics_path or '').strip()
    if metrics_url.startswith('/api/v1/buckets/'):
        from app.blueprints.train_task import _parse_minio_url
        from app.services.minio_service import ModelService

        bucket, key = _parse_minio_url(metrics_url)
        if bucket and key:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
            tmp.close()
            try:
                ok, _ = ModelService.download_from_minio(bucket, key, tmp.name)
                if ok:
                    with open(tmp.name, 'rb') as f:
                        csv_bytes = f.read()
            finally:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)

    if not csv_bytes:
        from app.blueprints.train import get_project_root, _resolve_train_results_dir
        results_dir = _resolve_train_results_dir(
            os.path.join(get_project_root(), 'data/datasets', f'train_{train_task.id}'),
        )
        csv_path = os.path.join(results_dir, 'results.csv')
        if os.path.isfile(csv_path):
            with open(csv_path, 'rb') as f:
                csv_bytes = f.read()

    if not csv_bytes:
        return None

    try:
        text = csv_bytes.decode('utf-8', errors='replace')
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return None
        last = rows[-1]
        for key in ('metrics/mAP50(B)', 'metrics/mAP50', 'mAP50'):
            if key in last and last[key]:
                return float(last[key])
    except Exception as e:
        logger.warning('解析 mAP50 失败: %s', e)
    return None


def publish_train_to_model(
    train_task: TrainTask,
    *,
    name: str | None = None,
    published_model_id: int | None = None,
    class_names: list[str] | None = None,
    model_origin: str | None = None,
    origin_ref: str | None = None,
) -> int:
    """将训练权重发布到 Model 表，返回 model_id。"""
    from app.blueprints.train_task import publish_train_task_to_model

    return publish_train_task_to_model(
        train_task,
        name=name,
        published_model_id=published_model_id,
        class_names=class_names,
        model_origin=model_origin,
        origin_ref=origin_ref,
    )


def run_auto_train_pipeline(
    auto_task: AutoLabelTask,
    app,
    *,
    round_no: int,
    log_fn,
    cancelled_check=None,
) -> int | None:
    """
    完整自动训练流程。成功返回 model_id，失败返回 None。
    """
    zip_path = None
    try:
        state = parse_pipeline_state(auto_task)
        strategy = get_strategy(auto_task)
        prompts = []
        if auto_task.text_prompts:
            import json
            try:
                prompts = json.loads(auto_task.text_prompts)
            except Exception:
                prompts = []

        train_ratio = float(state.get('export_train_ratio', 0.7))
        val_ratio = float(state.get('export_val_ratio', 0.2))
        test_ratio = float(state.get('export_test_ratio', 0.1))

        log_fn('划分数据集用途…')
        try:
            split_dataset_usage(auto_task.dataset_id, train_ratio, val_ratio, test_ratio)
        except Exception as e:
            log_fn(f'划分用途失败（继续导出）: {e}')

        log_fn('导出已标注图片为 YOLO 训练包…')
        zip_path = export_annotated_yolo_zip(
            auto_task.dataset_id,
            text_prompts=prompts,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            export_prefix=f'auto_label_{auto_task.dataset_id}_r{round_no}',
        )
        log_fn(f'训练包已就绪: {os.path.getsize(zip_path) // 1024} KB')

        pretrained = None
        pretrained_label = ''
        current_mid = state.get('current_model_id') or auto_task.model_id
        try:
            current_mid = int(current_mid) if current_mid else None
        except (TypeError, ValueError):
            current_mid = None

        arch_or_path, pretrained_label = resolve_train_pretrained_path(
            strategy,
            current_model_id=current_mid,
            round_no=round_no,
        )
        if arch_or_path:
            pretrained = arch_or_path
            log_fn(f'训练权重：{pretrained_label}')

        train_task = start_yolo_train(
            dataset_zip_path=zip_path,
            dataset_id=auto_task.dataset_id,
            round_no=round_no,
            strategy=strategy,
            pretrained_arch=pretrained,
        )
        log_fn(f'YOLO 训练已启动 train_task_id={train_task.id}')

        state = parse_pipeline_state(auto_task)
        state['train_task_id'] = train_task.id
        auto_task.pipeline_config = json.dumps(state, ensure_ascii=False)
        db.session.commit()

        finished = wait_train_task(train_task.id, cancelled_check=cancelled_check)
        if not finished:
            log_fn('训练等待超时或任务已取消')
            return None
        if finished.status != 'completed':
            log_fn(f'训练失败: status={finished.status}')
            return None

        map50 = extract_map50(finished)
        if map50 is not None:
            log_fn(f'训练完成 mAP50={map50:.3f}')
            st = parse_pipeline_state(auto_task)
            st['current_map'] = map50
            auto_task.pipeline_config = json.dumps(st, ensure_ascii=False)

        published_id = state.get('current_model_id')
        if published_id:
            try:
                published_id = int(published_id)
            except (TypeError, ValueError):
                published_id = None

        model_name = f'auto-label-ds{auto_task.dataset_id}'
        model_id = publish_train_to_model(
            finished,
            name=model_name,
            published_model_id=published_id,
            class_names=prompts or None,
            model_origin='smart_label',
            origin_ref=f'dataset:{auto_task.dataset_id}/task:{auto_task.id}',
        )
        log_fn(f'模型已发布 model_id={model_id}')

        try:
            from app.services.auto_label_model_service import (
                count_annotated_images,
                fetch_dataset_class_names,
                record_pipeline_model_update,
            )
            class_names_for_hist = prompts or fetch_dataset_class_names(auto_task.dataset_id)
            annotated_n = count_annotated_images(auto_task.dataset_id)
            record_pipeline_model_update(
                auto_task.dataset_id,
                model_id=model_id,
                train_task_id=finished.id,
                annotated_count=annotated_n,
                class_names=class_names_for_hist,
                source_model_id=current_mid,
                map50=map50,
                history_max=strategy.get('model_history_max'),
            )
            log_fn('已写入自动标注模型更新历史并绑定数据集')
        except Exception as e:
            log_fn(f'写入模型更新历史失败（不影响训练结果）: {e}')

        return model_id
    except Exception as e:
        logger.error('自动训练流程失败: %s', e, exc_info=True)
        log_fn(f'自动训练失败: {e}')
        return None
    finally:
        if zip_path and os.path.exists(zip_path):
            try:
                os.unlink(zip_path)
            except OSError:
                pass
