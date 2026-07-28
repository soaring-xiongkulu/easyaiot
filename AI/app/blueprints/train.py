"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import csv
import json
import os
import shutil
import subprocess
import threading
import time
import traceback
import uuid
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import torch
import yaml
from flask import current_app, jsonify, Blueprint, request
from ultralytics import YOLO

from app.blueprints.train_task import build_train_task_name, resolve_task_base_name
from app.services.minio_service import ModelService
from app.utils.train_checkpoint import (
    CHECKPOINT_ACTION_FINALIZE,
    CHECKPOINT_ACTION_REJECT,
    cleanup_staged_checkpoint,
    find_yolo_checkpoint,
    prepare_yolo_resume_checkpoint,
    stage_yolo_checkpoint,
)
from app.utils.train_dataset_name import resolve_dataset_display_name, save_upload_meta
from app.utils.train_dataset_layout import repair_flat_coco_yolo_layout
from app.utils.train_process_control import terminate_task_ddp_processes
from app.utils.yolo_chinese_font import ensure_ultralytics_training_fonts
from app.utils.gpu_utils import (
    check_gpu_status,
    format_device_for_log,
    release_cuda_memory,
    resolve_request_gpu_ids,
    resolve_train_dataloader_workers,
    resolve_yolo_train_device,
)
from db_models import db, TrainTask

train_bp = Blueprint('train', __name__)

# 本地数据集 zip 上传上限（与前端一致，5GB）
MAX_LOCAL_DATASET_UPLOAD_BYTES = 5 * 1024 * 1024 * 1024

# 全局训练状态和进程
train_status = {}
train_processes = {}

# 数据库中表示「进行中」的状态（容器重启后需 recover_stale_train_tasks 清理）
ACTIVE_TRAIN_STATUSES = ('preparing', 'train', 'Train', 'running', 'stopping')
RESUMABLE_TRAIN_STATUSES = ('stopped', 'error', 'failed')


def _train_log_timestamp() -> str:
    timezone_name = (os.getenv('TRAIN_LOG_TIMEZONE') or os.getenv('TZ') or 'Asia/Shanghai').strip()
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        timezone = ZoneInfo('Asia/Shanghai')
    return datetime.now(timezone).strftime('%Y-%m-%d %H:%M:%S')


def _is_stop_requested(task_id, train_task=None) -> bool:
    """仅读内存态 stop 标志，避免后台线程访问已 detach 的 ORM 实例。"""
    status_entry = train_status.get(task_id) or {}
    if status_entry.get('stop_requested'):
        return True
    if (status_entry.get('status') or '').lower() == 'stopping':
        return True
    return False


def _raise_if_train_stop_requested(task_id) -> None:
    """Abort at a trainer callback boundary so single-GPU jobs stop promptly."""
    if _is_stop_requested(task_id):
        raise RuntimeError('训练已被用户停止')


def _watch_task_ddp_stop(task_id, model_dir, stop_event, log_fn=None) -> None:
    """轮询停止标志，并终止该训练目录对应的 Ultralytics DDP 进程树。"""
    stop_requested_at = None
    while not stop_event.wait(0.5):
        if not _is_stop_requested(task_id):
            continue
        if stop_requested_at is None:
            stop_requested_at = time.monotonic()
        try:
            terminated_pids = terminate_task_ddp_processes(
                model_dir,
                timeout=2,
            )
        except Exception as terminate_error:
            if log_fn:
                log_fn(f'DDP 训练进程终止失败: {terminate_error}')
            return
        if terminated_pids:
            if log_fn:
                log_fn(
                    '已终止 DDP 训练进程: '
                    + ','.join(str(pid) for pid in terminated_pids)
                )
            return
        if time.monotonic() - stop_requested_at >= 10:
            if log_fn:
                log_fn('未发现仍在运行的 DDP 子进程，等待训练线程退出')
            return


def _release_train_model(yolo_model, log_fn=None) -> None:
    """断开 YOLO/trainer 引用并释放 CUDA 显存。"""
    if yolo_model is None:
        release_cuda_memory(log_fn=log_fn)
        return
    try:
        trainer = getattr(yolo_model, 'trainer', None)
        if trainer is not None:
            for attr in ('model', 'optimizer', 'ema', 'scaler', 'validator'):
                if hasattr(trainer, attr):
                    setattr(trainer, attr, None)
            yolo_model.trainer = None
    except Exception:
        pass
    try:
        del yolo_model
    except Exception:
        pass
    release_cuda_memory(log_fn=log_fn)


def _apply_train_schedule_fields(train_task: TrainTask, data: dict) -> None:
    from app.services.train_launcher_service import resolve_schedule_policy

    explicit_policy = data.get('schedulePolicy') or data.get('schedule_policy')
    train_task.schedule_policy = resolve_schedule_policy(explicit_policy)
    raw_target = data.get('targetNodeId') if 'targetNodeId' in data else data.get('target_node_id')
    if raw_target is not None and str(raw_target).strip() != '':
        train_task.target_node_id = int(raw_target)
    elif train_task.schedule_policy != 'node':
        train_task.target_node_id = None


def _start_train_execution(
    train_task: TrainTask,
    *,
    task_id: int,
    epochs,
    model_arch,
    img_size,
    batch_size,
    use_gpu,
    dataset_zip_path,
    request_gpu_ids,
    dataset_source,
    is_resume: bool,
) -> tuple[bool, str]:
    """本机线程或集群远程下发训练。"""
    from app.services.train_launcher_service import (
        TRAIN_DISPATCH_ERROR,
        TRAIN_DISPATCH_REMOTE,
        dispatch_train_to_node,
        use_remote_deploy,
    )

    train_status[task_id] = {
        'status': 'preparing',
        'message': '准备训练数据...',
        'progress': 0,
        'log': '',
        'stop_requested': False,
    }

    local_launch_msg = '训练已启动'
    if use_remote_deploy(train_task.schedule_policy):
        dispatch_mode, msg = dispatch_train_to_node(
            train_task,
            epochs=int(epochs),
            model_arch=model_arch,
            img_size=int(img_size),
            batch_size=int(batch_size),
            use_gpu=bool(use_gpu),
            dataset_zip_path=dataset_zip_path,
            dataset_source=dataset_source,
            resume_mode=is_resume,
            gpu_ids=request_gpu_ids,
        )
        if dispatch_mode == TRAIN_DISPATCH_ERROR:
            train_task.status = 'error'
            train_task.train_log = (train_task.train_log or '') + f'集群调度失败: {msg}\n'
            db.session.commit()
            train_status.pop(task_id, None)
            return False, msg
        if dispatch_mode == TRAIN_DISPATCH_REMOTE:
            train_status[task_id]['message'] = msg
            return True, msg

        train_task.node_id = None
        train_task.service_server_ip = None
        train_task.service_process_id = None
        db.session.commit()
        train_status[task_id]['message'] = msg
        local_launch_msg = msg

    train_thread = threading.Thread(
        target=train_model,
        args=(
            task_id, epochs, model_arch, img_size, batch_size,
            use_gpu, dataset_zip_path, train_task.id, request_gpu_ids, dataset_source,
            is_resume,
        ),
    )
    train_thread.daemon = True
    train_thread.start()
    return True, local_launch_msg


def _build_train_hyperparameters(
    epochs,
    model_arch,
    img_size,
    batch_size,
    use_gpu,
    task_base_name,
    gpu_ids=None,
    dataset_source=None,
    gpu_selection_manual=False,
):
    base = (task_base_name or 'train').strip() or 'train'
    hp = {
        'epochs': epochs,
        'model_arch': model_arch,
        'img_size': img_size,
        'batch_size': batch_size,
        'use_gpu': use_gpu,
        'task_base_name': base,
        'dataset_source': _normalize_dataset_source(dataset_source),
    }
    if gpu_ids is not None:
        hp['gpu_ids'] = gpu_ids
    if gpu_selection_manual:
        hp['gpu_selection_manual'] = True
    return json.dumps(hp)


def _normalize_dataset_source(value) -> str:
    source = (value or 'local').strip().lower()
    return source if source in ('local', 'cloud') else 'local'


def _is_cloud_dataset_path(dataset_path: str) -> bool:
    if not dataset_path:
        return False
    if dataset_path.startswith('/api/v1/buckets/'):
        return True
    return '://' in dataset_path and not dataset_path.startswith('file://')


def _resolve_split_path(raw_path, split_name, yaml_dir, dataset_root):
    candidate_bases = [
        dataset_root,
        yaml_dir,
        os.path.dirname(dataset_root),
    ]

    if raw_path is not None and str(raw_path).strip():
        normalized_raw = str(raw_path).replace('\\', '/')
        for base in candidate_bases:
            candidate = os.path.normpath(os.path.join(base, normalized_raw))
            if os.path.exists(candidate):
                return os.path.abspath(candidate)

    split_alias = {
        'train': ['train', 'training'],
        'val': ['val', 'valid', 'validation'],
        'test': ['test', 'testing'],
    }

    def _child_dir(parent, expected_name):
        if not os.path.isdir(parent):
            return None
        expected = expected_name.lower()
        for entry in os.listdir(parent):
            if entry.lower() == expected:
                candidate = os.path.join(parent, entry)
                if os.path.isdir(candidate):
                    return candidate
        return None

    for alias in split_alias.get(split_name, [split_name]):
        for base in candidate_bases:
            split_dir = _child_dir(base, alias)
            img_candidate = _child_dir(split_dir, 'images') if split_dir else None
            if img_candidate:
                return os.path.abspath(img_candidate)
            images_dir = _child_dir(base, 'images')
            alt_candidate = _child_dir(images_dir, alias) if images_dir else None
            if alt_candidate:
                return os.path.abspath(alt_candidate)

    return None


def _resolve_dataset_root(cfg, yaml_dir):
    """解析 YAML 中 path 字段，得到数据集根目录（兼容 COCO 原生格式）。"""
    path_val = cfg.get('path')
    if path_val is None or path_val == '':
        return yaml_dir
    path_str = str(path_val).strip()
    if path_str in ('.', './'):
        return yaml_dir
    candidate = os.path.normpath(os.path.join(yaml_dir, path_str))
    if os.path.isdir(candidate):
        return os.path.abspath(candidate)
    return yaml_dir


def _looks_like_dataset_yaml(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        return isinstance(cfg, dict) and ('train' in cfg or 'names' in cfg)
    except Exception:
        return False


def _find_dataset_yaml(root_dir):
    """查找数据集 YAML：优先 data.yaml，否则匹配任意含 train/names 的 .yaml/.yml。"""
    preferred = os.path.join(root_dir, 'data.yaml')
    if os.path.isfile(preferred):
        return preferred

    candidates = []
    for root, _, files in os.walk(root_dir):
        depth = root[len(root_dir):].count(os.sep)
        for file_name in files:
            lower = file_name.lower()
            if not lower.endswith(('.yaml', '.yml')):
                continue
            candidates.append((depth, file_name.lower(), os.path.join(root, file_name)))

    for _, _, candidate in sorted(candidates):
        if _looks_like_dataset_yaml(candidate):
            return candidate
    return None


def _parse_class_names(names_raw):
    """解析 names 字段，支持列表与 COCO 风格的「序号: 类型」字典。"""
    if names_raw is None:
        return ['object']
    if isinstance(names_raw, dict):
        if not names_raw:
            return ['object']
        max_idx = max(int(k) for k in names_raw.keys())
        result = [''] * (max_idx + 1)
        for key, value in names_raw.items():
            result[int(key)] = str(value)
        return [name for name in result if name] or ['object']
    if isinstance(names_raw, list):
        return [str(name) for name in names_raw if str(name).strip()] or ['object']
    return [str(names_raw)]


def _normalize_dataset_yaml(dataset_root, output_dir=None):
    """
    将数据集 YAML 中的 train/val/test 转为绝对路径，并生成标准 data.yaml。
    兼容：本地 YOLO 导出、MinIO 同步、COCO 原生（path + 外层 yaml）等格式。
    """
    dataset_yaml = _find_dataset_yaml(dataset_root)
    if not dataset_yaml:
        raise ValueError('未找到数据集 YAML 配置文件，无法开始训练')

    with open(dataset_yaml, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f) or {}

    yaml_dir = os.path.dirname(dataset_yaml)
    effective_root = _resolve_dataset_root(cfg, yaml_dir)
    train_path = _resolve_split_path(cfg.get('train'), 'train', yaml_dir, effective_root)
    val_path = _resolve_split_path(cfg.get('val'), 'val', yaml_dir, effective_root)
    test_path = _resolve_split_path(cfg.get('test'), 'test', yaml_dir, effective_root)

    if not train_path:
        raise ValueError('数据集 train 路径无效，请检查 YAML 配置或目录结构')
    if not val_path:
        raise ValueError('数据集 val/valid 路径无效，请检查 YAML 配置或目录结构')

    names = _parse_class_names(cfg.get('names'))
    normalized_cfg = {
        'train': train_path,
        'val': val_path,
        'nc': len(names),
        'names': names,
    }
    if test_path:
        normalized_cfg['test'] = test_path

    target_dir = output_dir or dataset_root
    os.makedirs(target_dir, exist_ok=True)
    normalized_yaml_path = os.path.join(target_dir, 'data.yaml')
    with open(normalized_yaml_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(normalized_cfg, f, allow_unicode=True, sort_keys=False)

    return normalized_yaml_path


def _prepare_train_dataset_in_dir(dataset_path: str, model_dir: str, log_fn):
    """将本地路径/zip 或云端 MinIO 数据集准备到 model_dir。"""
    os.makedirs(model_dir, exist_ok=True)

    if not _is_cloud_dataset_path(dataset_path):
        if not os.path.exists(dataset_path):
            raise RuntimeError(f'本地数据集不存在: {dataset_path}')
        source_abs = os.path.abspath(dataset_path)
        if os.path.isdir(source_abs):
            if not _find_dataset_yaml(source_abs):
                raise RuntimeError(f'本地数据集目录缺少 YAML 配置文件: {source_abs}')
            if source_abs != os.path.abspath(model_dir):
                for name in os.listdir(source_abs):
                    src = os.path.join(source_abs, name)
                    dst = os.path.join(model_dir, name)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
            log_fn(f'已使用本地数据集目录: {source_abs}')
            return
        if source_abs.lower().endswith('.zip'):
            log_fn(f'正在解压本地数据集: {source_abs}')
            if not ModelService.extract_zip(source_abs, model_dir):
                raise RuntimeError(f'本地数据集 zip 解压失败: {source_abs}')
            log_fn('本地数据集解压成功')
            return
        raise RuntimeError('本地数据集路径仅支持目录或 zip 文件')

    parsed_url = urlparse(dataset_path)
    query_params = parse_qs(parsed_url.query)
    object_key = query_params.get('prefix', [None])[0]
    path_parts = parsed_url.path.split('/')
    if len(path_parts) >= 5 and path_parts[3] == 'buckets':
        bucket_name = path_parts[4]
    else:
        bucket_name = 'datasets'

    local_zip_path = os.path.join(model_dir, 'dataset.zip')
    log_fn(f'从 MinIO 下载数据集: bucket={bucket_name}, object={object_key}')
    success, error_msg = ModelService.download_from_minio(
        bucket_name=bucket_name,
        object_name=object_key,
        destination_path=local_zip_path,
    )
    if not success:
        raise RuntimeError(f'数据集下载失败: {error_msg or "未知错误"}')
    log_fn('数据集下载成功，开始解压...')
    if not ModelService.extract_zip(local_zip_path, model_dir):
        raise RuntimeError('数据集解压失败')
    if os.path.exists(local_zip_path):
        os.remove(local_zip_path)
    log_fn('云端数据集解压成功')


TRAIN_ARTIFACTS_BUCKET = 'models'


def _train_artifact_object_key(model_id, task_id, filename):
    """与历史 best.pt 路径一致：models/model_{model_id}/train_{task_id}/{filename}"""
    return f"models/model_{model_id}/train_{task_id}/{filename}"


def _build_minio_download_url(bucket_name, object_key):
    return f"/api/v1/buckets/{bucket_name}/objects/download?prefix={object_key}"


def _resolve_train_results_dir(model_dir):
    """定位 YOLO 训练输出目录（exist_ok 时可能为 train_results2 等）。"""
    parent = model_dir
    if not os.path.isdir(parent):
        return os.path.join(model_dir, 'train_results')
    candidates = []
    for name in os.listdir(parent):
        if not name.startswith('train_results'):
            continue
        path = os.path.join(parent, name)
        if os.path.isdir(path):
            candidates.append(name)
    for name in sorted(candidates, reverse=True):
        path = os.path.join(parent, name)
        if os.path.isfile(os.path.join(path, 'results.png')) or os.path.isfile(
            os.path.join(path, 'results.csv')
        ) or os.path.isfile(os.path.join(path, 'weights', 'last.pt')):
            return path
    if candidates:
        return os.path.join(parent, sorted(candidates, reverse=True)[0])
    return os.path.join(model_dir, 'train_results')


def _parse_train_hyperparameters(hp_text):
    if not hp_text:
        return {}
    try:
        return json.loads(hp_text)
    except (json.JSONDecodeError, TypeError):
        return {}


def _get_completed_epochs(hp_text):
    return int(_parse_train_hyperparameters(hp_text).get('completed_epochs') or 0)


def _get_total_epochs_from_hp(hp_text, default=20):
    return int(_parse_train_hyperparameters(hp_text).get('epochs') or default)


def _format_model_loading_message(model_arch, resume_mode):
    if resume_mode:
        return '准备加载训练断点...'
    return f'准备加载预训练模型: {model_arch}'


def _update_hyperparameters_field(hp_text, **fields):
    hp = _parse_train_hyperparameters(hp_text)
    hp.update(fields)
    return json.dumps(hp)


def _resolve_train_checkpoint_path(model_dir):
    """定位 YOLO 断点权重 last.pt。"""
    return find_yolo_checkpoint(model_dir)


def _clear_train_results_dirs(model_dir, log_fn=None):
    """重新训练前清理历史 YOLO 输出目录。"""
    if not model_dir or not os.path.isdir(model_dir):
        return

    def _log(msg):
        if log_fn:
            log_fn(msg)

    for name in os.listdir(model_dir):
        if not name.startswith('train_results'):
            continue
        path = os.path.join(model_dir, name)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                _log(f'已清理历史训练输出: {name}')
            except OSError as e:
                _log(f'清理 {name} 失败: {e}')


def _download_checkpoint_from_minio(train_task, dest_path, log_fn):
    """本地断点缺失时尝试从 MinIO 拉取 last.pt。"""
    model_id = train_task.model_id
    minio_path = _train_artifact_object_key(model_id, train_task.id, 'last.pt')
    success, error_msg = ModelService.download_from_minio(
        bucket_name=TRAIN_ARTIFACTS_BUCKET,
        object_name=minio_path,
        destination_path=dest_path,
    )
    if success and os.path.isfile(dest_path):
        log_fn(f'已从 MinIO 恢复断点权重: {dest_path}')
        return dest_path
    if error_msg:
        log_fn(f'从 MinIO 恢复断点失败: {error_msg}')
    return None


def _resolve_resume_checkpoint(train_task, model_dir, log_fn=None):
    """解析可用于续训的断点路径（本地优先，MinIO 兜底）。"""
    def _log(msg):
        if log_fn:
            log_fn(msg)

    staging_root = os.path.join(get_datasets_root(), '.resume_checkpoints')

    def _stage(checkpoint_path):
        try:
            staged_path = stage_yolo_checkpoint(
                checkpoint_path,
                staging_root,
                train_task.id,
            )
            if os.path.abspath(checkpoint_path) != staged_path:
                _log(f'已将训练断点暂存到独立目录: {staged_path}')
            return staged_path
        except OSError as stage_error:
            _log(f'训练断点暂存失败: {stage_error}')
            return None

    checkpoint = (train_task.checkpoint_dir or '').strip()
    if checkpoint and os.path.isfile(checkpoint):
        return _stage(checkpoint)

    checkpoint = _resolve_train_checkpoint_path(model_dir)
    if checkpoint:
        return _stage(checkpoint)

    dest = os.path.join(staging_root, f'train_{train_task.id}', 'last.pt')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    return _download_checkpoint_from_minio(train_task, dest, _log)


def _persist_stop_checkpoint(train_task, model_dir, completed_epochs, update_log_fn):
    """停止训练时记录断点路径并上传 last.pt。"""
    checkpoint_path = _resolve_train_checkpoint_path(model_dir)
    if not checkpoint_path:
        update_log_fn('未找到 last.pt，无法保存断点（需至少完成 1 个 epoch）')
        return

    train_task.checkpoint_dir = checkpoint_path
    train_task.hyperparameters = _update_hyperparameters_field(
        train_task.hyperparameters,
        completed_epochs=completed_epochs,
    )
    total_epochs = _get_total_epochs_from_hp(train_task.hyperparameters)
    update_log_fn(
        f'已保存训练断点: epoch {completed_epochs}/{total_epochs}, 权重={checkpoint_path}'
    )

    model_id = train_task.model_id
    minio_path = _train_artifact_object_key(model_id, train_task.id, 'last.pt')
    success, error = ModelService.upload_to_minio(
        bucket_name=TRAIN_ARTIFACTS_BUCKET,
        object_name=minio_path,
        file_path=checkpoint_path,
    )
    if success:
        update_log_fn(
            f'断点权重已上传至 MinIO: '
            f'{_build_minio_download_url(TRAIN_ARTIFACTS_BUCKET, minio_path)}'
        )
    else:
        update_log_fn(f'断点权重上传 MinIO 失败: {error or "未知错误"}')


def _is_uploaded_dataset_zip(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False
    uploads_root = os.path.join(get_datasets_root(), 'uploads')
    try:
        return os.path.commonpath([
            os.path.abspath(path),
            os.path.abspath(uploads_root),
        ]) == os.path.abspath(uploads_root)
    except ValueError:
        return False


def _cleanup_train_dataset_artifacts(
    model_dir,
    dataset_zip_path,
    log_fn=None,
    *,
    remove_uploaded_zip=True,
):
    """删除已准备的数据集文件，保留 train_results 与已导出的权重。"""
    def _log(msg):
        if log_fn:
            log_fn(msg)

    freed = []

    if remove_uploaded_zip and dataset_zip_path and _is_uploaded_dataset_zip(dataset_zip_path):
        try:
            os.remove(dataset_zip_path)
            freed.append(f'上传压缩包: {dataset_zip_path}')
        except OSError as e:
            _log(f'删除上传压缩包失败: {e}')

    if not model_dir or not os.path.isdir(model_dir):
        if freed:
            _log(f'已清理训练数据集: {"; ".join(freed)}')
        return

    train_results_dir = os.path.join(model_dir, 'train_results')
    for name in os.listdir(model_dir):
        if name.startswith('train_results'):
            continue
        target = os.path.join(model_dir, name)
        if os.path.isdir(target):
            try:
                shutil.rmtree(target)
                freed.append(name + '/')
            except OSError as e:
                _log(f'删除 {name}/ 失败: {e}')
        elif os.path.isfile(target):
            try:
                os.remove(target)
                freed.append(name)
            except OSError as e:
                _log(f'删除 {name} 失败: {e}')

    # 清理 train_results 内可能残留的中间缓存，保留 weights 与结果文件
    if os.path.isdir(train_results_dir):
        for sub in ('images', 'labels'):
            target = os.path.join(train_results_dir, sub)
            if os.path.isdir(target):
                try:
                    shutil.rmtree(target)
                    freed.append(f'train_results/{sub}/')
                except OSError:
                    pass

    if freed:
        _log(f'已清理训练数据集以释放磁盘: {", ".join(freed)}')
    else:
        _log('未发现需清理的本地数据集文件')


@train_bp.route('/dataset/upload', methods=['POST'])
def api_upload_train_dataset():
    """上传本地 YOLO 数据集压缩包（zip），供训练使用。"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'code': 400, 'msg': '未找到文件'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'code': 400, 'msg': '未选择文件'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != '.zip':
        return jsonify({'success': False, 'code': 400, 'msg': '仅支持 ZIP 格式数据集'}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_LOCAL_DATASET_UPLOAD_BYTES:
        return jsonify({
            'success': False,
            'code': 400,
            'msg': '数据集压缩包不能超过 5GB',
        }), 400

    upload_dir = os.path.join(get_datasets_root(), 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    unique_name = f'{uuid.uuid4().hex}.zip'
    local_path = os.path.join(upload_dir, unique_name)
    file.save(local_path)
    save_upload_meta(local_path, file.filename)

    return jsonify({
        'success': True,
        'code': 0,
        'msg': '上传成功',
        'data': {
            'path': local_path,
            'fileName': file.filename,
        },
    }), 200


@train_bp.route('/start', methods=['POST'])
def api_start_train():
    train_task = None
    is_new_record = False  # 标记是否是新创建的记录
    try:
        # 获取训练参数
        data = request.get_json() or {}

        record_id = data.get('taskId')
        is_resume = bool(data.get('resume'))
        task_name = (data.get('taskName') or data.get('task_name') or '').strip()
        epochs = data.get('epochs', 20)
        batch_size = data.get('batch_size', 16)
        img_size = data.get('imgsz', 640)
        model_arch = data.get('modelPath', 'yolov8n.pt')
        dataset_url = data.get('datasetPath') or data.get('dataset_path')
        dataset_zip_path = dataset_url
        dataset_source = _normalize_dataset_source(
            data.get('datasetSource') or data.get('dataset_source')
        )
        if dataset_source == 'local' and dataset_zip_path and _is_cloud_dataset_path(dataset_zip_path):
            dataset_source = 'cloud'
        elif dataset_source == 'cloud' and dataset_zip_path and not _is_cloud_dataset_path(dataset_zip_path):
            dataset_source = 'local'
        dataset_name = (data.get('datasetName') or data.get('dataset_name') or '').strip() or None
        dataset_name = resolve_dataset_display_name(dataset_zip_path, dataset_name)
        dataset_version = (data.get('datasetVersion') or data.get('dataset_version') or '').strip() or None
        use_gpu = data.get('use_gpu', True)
        gpu_selection_manual = bool(use_gpu) and (
            data.get('gpu_selection_manual') is True
            or data.get('gpuSelectionManual') is True
        )
        try:
            request_gpu_ids = resolve_request_gpu_ids(
                data.get('gpu_ids'),
                manual_selection=gpu_selection_manual,
            )
        except ValueError as gpu_err:
            return jsonify({'success': False, 'code': 400, 'msg': str(gpu_err)}), 400

        schedule_data = data

        if not dataset_zip_path:
            return jsonify({'success': False, 'code': 400, 'msg': '缺少数据集路径'}), 400

        from app.services.train_launcher_service import resolve_schedule_policy, use_remote_deploy
        resolved_policy = resolve_schedule_policy(
            data.get('schedulePolicy') or data.get('schedule_policy')
        )
        if dataset_source == 'local' and not os.path.exists(dataset_zip_path):
            if not use_remote_deploy(resolved_policy):
                return jsonify({'success': False, 'code': 400, 'msg': '本地数据集文件不存在，请重新上传'}), 400

        if record_id:
            train_task = TrainTask.query.get(record_id)
            if train_task:
                in_memory = (
                    train_task.id in train_status
                    and train_status[train_task.id]['status'] in ['preparing', 'train']
                )
                in_db = train_task.status in ACTIVE_TRAIN_STATUSES
                if in_memory or in_db:
                    return jsonify({'success': False, 'code': 0, 'msg': '该训练任务已在进行中'}), 200

                task_base_name = task_name or resolve_task_base_name(train_task)
                model_dir = get_train_task_dir(train_task.id)

                if is_resume:
                    if train_task.status not in RESUMABLE_TRAIN_STATUSES:
                        return jsonify({
                            'success': False,
                            'code': 400,
                            'msg': '仅已停止或存在断点的失败任务可继续训练',
                        }), 400

                    completed_epochs = _get_completed_epochs(train_task.hyperparameters)
                    if int(epochs) <= completed_epochs:
                        return jsonify({
                            'success': False,
                            'code': 400,
                            'msg': (
                                f'总 epochs({epochs}) 必须大于已完成 epoch({completed_epochs})，'
                                '请增大迭代次数或使用重新训练'
                            ),
                        }), 400

                    checkpoint_path = _resolve_resume_checkpoint(train_task, model_dir)
                    if not checkpoint_path:
                        return jsonify({
                            'success': False,
                            'code': 400,
                            'msg': '未找到可用训练断点，请使用重新训练',
                        }), 400

                    train_task.checkpoint_dir = checkpoint_path
                    train_task.start_time = datetime.utcnow()
                    train_task.end_time = None
                    train_task.status = 'preparing'
                    train_task.hyperparameters = _update_hyperparameters_field(
                        _build_train_hyperparameters(
                            epochs, model_arch, img_size, batch_size, use_gpu, task_base_name,
                            request_gpu_ids, dataset_source, gpu_selection_manual,
                        ),
                        completed_epochs=completed_epochs,
                    )
                    train_task.name = build_train_task_name(
                        task_base_name,
                        train_task.dataset_name,
                        train_task.dataset_version,
                        train_task.id,
                    )
                    _apply_train_schedule_fields(train_task, schedule_data)
                    db.session.commit()
                else:
                    train_task.dataset_path = dataset_zip_path
                    if dataset_name:
                        train_task.dataset_name = dataset_name
                    if dataset_version is not None:
                        train_task.dataset_version = dataset_version
                    train_task.start_time = datetime.utcnow()
                    train_task.status = 'preparing'
                    train_task.train_log = ''
                    train_task.progress = 0
                    train_task.checkpoint_dir = ''
                    train_task.hyperparameters = _update_hyperparameters_field(
                        _build_train_hyperparameters(
                            epochs, model_arch, img_size, batch_size, use_gpu, task_base_name,
                            request_gpu_ids, dataset_source, gpu_selection_manual,
                        ),
                        completed_epochs=0,
                    )
                    train_task.name = build_train_task_name(
                        task_base_name,
                        train_task.dataset_name,
                        train_task.dataset_version,
                        train_task.id,
                    )
                    _clear_train_results_dirs(model_dir)
                    _apply_train_schedule_fields(train_task, schedule_data)
                    db.session.commit()
                is_new_record = False

        if not train_task:
            task_base_name = task_name or 'train'
            train_task = TrainTask(
                name='',
                dataset_path=dataset_zip_path,
                dataset_name=dataset_name,
                dataset_version=dataset_version,
                hyperparameters=_build_train_hyperparameters(
                    epochs, model_arch, img_size, batch_size, use_gpu, task_base_name,
                    request_gpu_ids, dataset_source, gpu_selection_manual,
                ),
                start_time=datetime.utcnow(),
                status='preparing',
                train_log='',
                checkpoint_dir=''
            )
            db.session.add(train_task)
            db.session.flush()
            train_task.name = build_train_task_name(
                task_base_name, dataset_name, dataset_version, train_task.id
            )
            _apply_train_schedule_fields(train_task, schedule_data)
            db.session.commit()
            is_new_record = True

        task_id = train_task.id
        if task_id in train_status and train_status[task_id]['status'] in ['preparing', 'train']:
            return jsonify({'success': False, 'code': 0, 'msg': '训练已在进行中'}), 200

        if is_resume:
            dataset_zip_path = dataset_zip_path or train_task.dataset_path

        _apply_train_schedule_fields(train_task, schedule_data)
        db.session.commit()

        ok, launch_msg = _start_train_execution(
            train_task,
            task_id=task_id,
            epochs=epochs,
            model_arch=model_arch,
            img_size=img_size,
            batch_size=batch_size,
            use_gpu=use_gpu,
            dataset_zip_path=dataset_zip_path,
            request_gpu_ids=request_gpu_ids,
            dataset_source=dataset_source,
            is_resume=is_resume,
        )
        if not ok:
            return jsonify({'success': False, 'code': 400, 'msg': launch_msg}), 400

        start_msg = launch_msg if launch_msg != '训练已启动' else (
            '训练已继续' if is_resume else ('重新训练已启动' if record_id else '训练已启动')
        )
        return jsonify({
            'success': True,
            'code': 0,
            'msg': start_msg,
            'record_id': train_task.id
        }), 200
    except Exception as e:
        # 如果创建了训练记录但在启动线程前失败，需要回滚或删除记录
        if train_task:
            try:
                if is_new_record:
                    # 如果是新创建的记录，删除它
                    db.session.delete(train_task)
                    db.session.commit()
                else:
                    # 如果是更新的记录，标记为错误状态
                    train_task.status = 'error'
                    train_task.error_log = f'启动训练失败: {str(e)}'
                    db.session.commit()
            except Exception as rollback_error:
                print(f'回滚训练记录失败: {str(rollback_error)}')
                db.session.rollback()

        return jsonify({'success': False, 'code': 400, 'msg': f'启动训练失败: {str(e)}'}), 400


def get_project_root():
    """获取项目根目录"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))


def get_datasets_root():
    """训练数据集根目录（集群模式下为 CephFS 共享路径）。"""
    try:
        from cluster_storage import get_ai_datasets_dir
        return get_ai_datasets_dir()
    except ImportError:
        return os.path.join(get_project_root(), 'data', 'datasets')


def get_train_task_dir(task_id):
    """单个训练任务的工作目录。"""
    try:
        from cluster_storage import get_ai_train_dir
        return get_ai_train_dir(task_id)
    except ImportError:
        return os.path.join(get_project_root(), 'data', 'datasets', f'train_{task_id}')


def recover_stale_train_tasks(app=None):
    """
    服务重启后，将数据库中仍为进行中、但本进程无训练线程的任务标记为失败。
    避免进度长期卡在 15% 等中间态。
    """
    from run import create_app

    application = app or create_app()
    recovered = 0
    with application.app_context():
        stale_tasks = TrainTask.query.filter(
            TrainTask.status.in_(ACTIVE_TRAIN_STATUSES)
        ).all()
        if not stale_tasks:
            return 0

        interrupt_msg = (
            f"[{_train_log_timestamp()}] "
            "训练进程因服务重启或异常退出而中断。"
        )
        for task in stale_tasks:
            if task.id in train_status:
                continue
            if task.node_id and (task.status or '').lower() in ACTIVE_TRAIN_STATUSES:
                continue
            model_dir = get_train_task_dir(task.id)
            checkpoint_path = _resolve_resume_checkpoint(task, model_dir)
            if checkpoint_path:
                completed_epochs = _get_completed_epochs(task.hyperparameters)
                task.status = 'stopped'
                task.checkpoint_dir = checkpoint_path
                task.hyperparameters = _update_hyperparameters_field(
                    task.hyperparameters,
                    completed_epochs=completed_epochs,
                )
                resume_hint = '可点击「继续训练」从断点恢复。'
            else:
                task.status = 'error'
                resume_hint = '未找到可用断点，请重新训练。'
            task.end_time = datetime.utcnow()
            task.train_log = (task.train_log or '') + interrupt_msg + resume_hint + '\n'
            recovered += 1

        if recovered:
            db.session.commit()
    return recovered


def _parse_minio_download_url(url: str):
    """解析 MinIO 下载 URL，返回 (bucket_name, object_key)。"""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        if len(path_parts) >= 5 and path_parts[3] == 'buckets':
            bucket_name = path_parts[4]
        else:
            return None, None
        query_params = parse_qs(parsed.query)
        object_key = query_params.get('prefix', [None])[0]
        return bucket_name, object_key
    except Exception:
        return None, None


def _resolve_pretrained_model_path(model_arch: str, task_id: int):
    """
    将 model_arch 解析为 YOLO 可用的本地路径或标准权重名。
    返回 (resolved_path, error_message)，成功时 error_message 为 None。
    """
    model_arch = (model_arch or 'yolov8n.pt').strip()
    ai_root = get_project_root()

    if model_arch.startswith('@AI/'):
        rel = model_arch[4:].lstrip('/')
        local = os.path.join(ai_root, rel)
        if os.path.exists(local):
            return os.path.abspath(local), None
        return None, f'预训练模型不存在: {local}'

    if model_arch.startswith('/api/v1/buckets/'):
        bucket_name, object_key = _parse_minio_download_url(model_arch)
        if not bucket_name or not object_key:
            return None, f'预训练模型 URL 格式无效: {model_arch}'

        storage_dir = os.path.join(ai_root, 'data', 'pretrained', f'train_{task_id}')
        os.makedirs(storage_dir, exist_ok=True)
        filename = os.path.basename(object_key) or 'pretrained.pt'
        local_path = os.path.join(storage_dir, filename)

        if os.path.exists(local_path):
            return local_path, None

        success, error_msg = ModelService.download_from_minio(
            bucket_name=bucket_name,
            object_name=object_key,
            destination_path=local_path,
        )
        if success:
            return local_path, None
        return None, f'从 MinIO 下载预训练模型失败: {error_msg or "未知错误"}'

    if os.path.isabs(model_arch) and os.path.exists(model_arch):
        return model_arch, None

    for candidate in (
        os.path.join(ai_root, model_arch),
        os.path.join(ai_root, 'model', model_arch),
    ):
        if os.path.exists(candidate):
            return os.path.abspath(candidate), None

    # 标准 ultralytics 权重名（如 yolov8n.pt），由 YOLO 自行解析
    if '://' not in model_arch and not model_arch.startswith('/'):
        return model_arch, None

    return None, f'预训练模型路径不可用: {model_arch}'


@train_bp.route('/<int:task_id>/stop', methods=['POST'])
def api_stop_train(task_id):
    update_log(f"收到停止训练请求，任务ID: {task_id}", task_id)

    train_task = TrainTask.query.get(task_id)

    if task_id in train_status:
        train_status[task_id]['stop_requested'] = True
        train_status[task_id]['status'] = 'stopping'
        train_status[task_id]['message'] = '正在停止训练...'
        update_log("设置停止请求标志", task_id)

        if train_task and train_task.node_id:
            from app.services.train_launcher_service import stop_remote_train
            stop_remote_train(train_task)
        else:
            try:
                terminated_pids = terminate_task_ddp_processes(
                    get_train_task_dir(task_id),
                    timeout=1,
                )
                if terminated_pids:
                    update_log(
                        '已向 DDP 训练进程发送终止信号: '
                        + ','.join(str(pid) for pid in terminated_pids),
                        task_id,
                    )
            except Exception as terminate_error:
                update_log(f'DDP 训练进程终止失败: {terminate_error}', task_id)

        return jsonify({'success': True, 'code': 0, 'msg': '停止请求已发送'}), 200

    if train_task and train_task.status in ACTIVE_TRAIN_STATUSES:
        if train_task.node_id:
            from app.services.train_launcher_service import stop_remote_train
            stop_remote_train(train_task)
            return jsonify({'success': True, 'code': 0, 'msg': '已向远程训练节点发送停止请求'}), 200

        stop_msg = (
            f"[{_train_log_timestamp()}] "
            "训练已停止（训练进程不在当前服务实例中）。"
        )
        train_task.status = 'stopped'
        train_task.end_time = datetime.utcnow()
        train_task.train_log = (train_task.train_log or '') + stop_msg + '\n'
        db.session.commit()
        return jsonify({'success': True, 'code': 0, 'msg': '训练任务已标记为停止'}), 200

    update_log("没有找到训练状态", task_id)
    return jsonify({'success': False, 'code': 0, 'msg': '没有正在进行的训练'}), 200


@train_bp.route('/<int:task_id>/status')
def api_train_status(task_id):
    if task_id in train_status:
        status = train_status[task_id]
    else:
        train_task = TrainTask.query.get(task_id)
        if train_task:
            status = {
                'status': train_task.status or 'idle',
                'message': '远程训练中' if train_task.node_id else '等待开始',
                'progress': train_task.progress or 0,
            }
        else:
            status = {
                'status': 'idle',
                'message': '等待开始',
                'progress': 0,
            }
    return jsonify({'status': status, 'code': 0, 'msg': 'success'}), 200


@train_bp.route('/gpu/status', methods=['GET'])
def api_gpu_status():
    """查询当前环境可见 GPU（与算法任务多卡探测逻辑一致）。"""
    return jsonify({
        'success': True,
        'code': 0,
        'msg': 'success',
        'data': check_gpu_status(),
    }), 200


@train_bp.route('/<int:task_id>/logs')
def api_train_log(task_id):
    """训练日志轮询接口，先返回内存中的日志数据，如果为空则查询数据库"""
    log_content = train_status.get(task_id, {}).get('log', '') if train_status.get(task_id) else ''

    # 如果缓存中日志为空，则从数据库查询最新训练记录
    if not log_content:
        try:
            train_task = TrainTask.query.filter_by(id=task_id).first()
            if train_task:
                log_content = train_task.train_log or ''

        except Exception as e:
            current_app.logger.error(f"查询训练记录失败: {str(e)}")

    # 返回日志数据
    return jsonify({
        'success': True,
        'code': 0,
        'data': log_content
    }), 200


def update_log(message, task_id=None, progress=None, train_task=None):
    """统一的日志记录函数"""
    log_message = f"[{_train_log_timestamp()}] {message}"
    print(log_message)

    if task_id is not None and task_id in train_status:
        train_status[task_id]['log'] += log_message + '\n'
        if progress is not None:
            train_status[task_id]['progress'] = progress

    # 如果提供了train_task，更新数据库记录
    if train_task is not None:
        train_task.train_log += log_message + '\n'
        if progress is not None:
            train_task.progress = progress
        try:
            db.session.commit()
        except Exception as e:
            print(f"数据库提交失败: {str(e)}")


def _read_completed_result_epochs(model_dir) -> int:
    results_csv = os.path.join(_resolve_train_results_dir(model_dir), 'results.csv')
    if not os.path.isfile(results_csv):
        return 0
    try:
        with open(results_csv, 'r', encoding='utf-8', newline='') as csv_file:
            return sum(
                1
                for row in csv.DictReader(csv_file)
                if any(str(value or '').strip() for value in row.values())
            )
    except (OSError, csv.Error):
        return 0


def _progress_for_completed_epochs(completed_epochs: int, total_epochs: int) -> int:
    total = max(1, int(total_epochs))
    completed = max(0, min(int(completed_epochs), total))
    progress_delta = (completed * 74 + total - 1) // total
    return min(89, 15 + progress_delta)


def _monitor_training_progress(
    application,
    task_id,
    record_id,
    model_dir,
    total_epochs,
    stop_event,
):
    heartbeat_seconds = max(
        5,
        int(os.getenv('TRAIN_PROGRESS_HEARTBEAT_SECONDS', '30')),
    )
    log_seconds = max(
        heartbeat_seconds,
        int(os.getenv('TRAIN_PROGRESS_LOG_SECONDS', '60')),
    )
    started_at = time.monotonic()
    last_log_elapsed = 0

    while not stop_event.wait(heartbeat_seconds):
        if _is_stop_requested(task_id):
            return
        elapsed_seconds = int(time.monotonic() - started_at)
        try:
            with application.app_context():
                task = TrainTask.query.get(record_id or task_id)
                status_entry = train_status.get(task_id)
                if not task or not status_entry:
                    return
                if task.status not in ('preparing', 'train', 'Train', 'running'):
                    return
                if status_entry.get('status') in ('completed', 'error', 'stopped', 'stopping'):
                    return

                completed_epochs = _read_completed_result_epochs(model_dir)
                progress = max(
                    16,
                    int(task.progress or 0),
                    int(status_entry.get('progress') or 0),
                    _progress_for_completed_epochs(completed_epochs, total_epochs),
                )
                if completed_epochs > 0:
                    message = (
                        f'训练运行中，已完成 epoch '
                        f'{completed_epochs}/{max(1, int(total_epochs))}...'
                    )
                else:
                    message = f'训练运行中，首个 epoch 计算中，已持续 {elapsed_seconds} 秒...'

                status_entry.update({
                    'progress': progress,
                    'message': message,
                })
                task.progress = progress
                saved_epochs = _get_completed_epochs(task.hyperparameters)
                if completed_epochs > saved_epochs:
                    task.hyperparameters = _update_hyperparameters_field(
                        task.hyperparameters,
                        completed_epochs=completed_epochs,
                    )
                    checkpoint_path = _resolve_train_checkpoint_path(model_dir)
                    if checkpoint_path:
                        task.checkpoint_dir = checkpoint_path

                if elapsed_seconds - last_log_elapsed >= log_seconds:
                    log_message = f'[{_train_log_timestamp()}] 训练心跳: {message}'
                    print(log_message)
                    status_entry['log'] = status_entry.get('log', '') + log_message + '\n'
                    task.train_log = (task.train_log or '') + log_message + '\n'
                    last_log_elapsed = elapsed_seconds
                db.session.commit()
        except Exception as monitor_err:
            print(f'训练进度监控更新失败: {monitor_err}')


def train_model(task_id, epochs=20, model_arch='yolov8n.pt',
                img_size=640, batch_size=16, use_gpu=True,
                dataset_zip_path=None, record_id=None, gpu_ids=None,
                dataset_source='local', resume_mode=False):
    """增强版训练函数，集成数据集下载和解压功能"""
    update_log(f"训练函数被调用，任务ID: {task_id}", task_id)
    train_task = None
    model_dir_for_cleanup = None
    dataset_path_for_cleanup = dataset_zip_path
    dataset_cleaned = False
    yolo_model = None

    try:
        from run import create_app
        application = create_app()

        with application.app_context():
            # 在函数内部通过record_id获取训练记录
            train_task = TrainTask.query.get(record_id)

            # 重新获取train_task以确保在当前会话中
            db.session.refresh(train_task)

            # 更新日志函数
            def update_log_local(message, progress=None):
                update_log(message, task_id, progress, train_task)

            task_label = train_task.name if train_task and train_task.name else f'任务{task_id}'
            update_log_local(f"开始准备训练数据，任务: {task_label}")

            if _is_stop_requested(task_id, train_task):
                log_msg = '训练已停止'
                train_status[task_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': train_status[task_id].get('log', '') + log_msg + '\n'
                }
                update_log_local(log_msg)
                return

            # 支持 YOLO 标准目录（images/labels + data.yaml）与 COCO 原生（path + 外层 yaml）
            model_dir = get_train_task_dir(task_id)
            model_dir_for_cleanup = model_dir
            dataset_path_for_cleanup = dataset_zip_path
            data_yaml_path = os.path.join(model_dir, 'data.yaml')
            dataset_yaml = _find_dataset_yaml(model_dir)

            if dataset_yaml and os.path.exists(data_yaml_path):
                update_log_local(f"数据集验证成功，使用原始路径: {dataset_zip_path}")

            update_log_local(f"项目目录: {model_dir}")
            update_log_local(f"数据配置文件路径: {dataset_yaml or data_yaml_path}")
            update_log_local("检查数据集配置文件...")

            if not dataset_yaml and not os.path.exists(data_yaml_path):
                source_label = '本地' if dataset_source == 'local' else '云端'
                log_msg = f'数据集配置文件不存在，正在准备{source_label}数据集...'
                train_status[task_id].update({
                    'message': '正在准备数据集...',
                    'progress': 5
                })
                update_log_local(log_msg, progress=5)

                if dataset_zip_path:
                    _prepare_train_dataset_in_dir(
                        dataset_zip_path, model_dir, update_log_local
                    )
                else:
                    raise RuntimeError('未提供数据集路径，无法准备训练数据')

            repair_flat_coco_yolo_layout(model_dir, update_log_local)

            # 检查是否应该停止训练
            if _is_stop_requested(task_id, train_task):
                log_msg = '训练已停止'
                train_status[task_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': train_status[task_id].get('log', '') + log_msg + '\n'
                }
                update_log_local(log_msg)
                return

            try:
                data_yaml_path = _normalize_dataset_yaml(model_dir, output_dir=model_dir)
                update_log_local(f'已标准化 data.yaml 路径: {data_yaml_path}')
            except Exception as norm_err:
                error_msg = f'数据集 YAML 标准化失败: {norm_err}'
                update_log_local(error_msg)
                train_task.status = 'error'
                train_task.error_log = error_msg
                db.session.commit()
                raise Exception(error_msg) from norm_err

            if not ensure_ultralytics_training_fonts():
                error_msg = (
                    '无法离线准备 Ultralytics 训练字体，已阻止多卡训练联网下载字体；'
                    '请设置 ULTRALYTICS_FONT_PATH 指向本地字体文件'
                )
                update_log_local(error_msg)
                train_task.status = 'error'
                train_task.error_log = error_msg
                db.session.commit()
                raise RuntimeError(error_msg)
            update_log_local('已离线准备 Ultralytics 训练字体，DDP 子进程无需联网下载')

            # 更新状态：开始加载模型
            model_loading_message = _format_model_loading_message(
                model_arch,
                resume_mode,
            )
            train_status[task_id].update({
                'message': model_loading_message,
                'progress': 10
            })
            update_log_local(model_loading_message, progress=10)

            resume_train = False
            finalized_checkpoint_path = None
            if resume_mode:
                checkpoint_path = _resolve_resume_checkpoint(
                    train_task, model_dir, update_log_local
                )
                if not checkpoint_path:
                    error_msg = '找不到训练断点文件，无法继续训练'
                    update_log_local(error_msg)
                    train_task.status = 'error'
                    train_task.error_log = error_msg
                    db.session.commit()
                    raise Exception(error_msg)

                completed_epochs = _get_completed_epochs(train_task.hyperparameters)
                try:
                    prepared_checkpoint = prepare_yolo_resume_checkpoint(
                        checkpoint_path,
                        os.path.join(get_datasets_root(), '.resume_checkpoints'),
                        task_id=task_id,
                        completed_epochs=completed_epochs,
                        target_epochs=epochs,
                    )
                except Exception as checkpoint_error:
                    error_msg = f'训练断点元数据读取失败: {checkpoint_error}'
                    update_log_local(error_msg)
                    train_task.status = 'error'
                    train_task.error_log = error_msg
                    db.session.commit()
                    raise Exception(error_msg) from checkpoint_error

                checkpoint_path = prepared_checkpoint.path
                train_task.checkpoint_dir = checkpoint_path
                db.session.commit()
                update_log_local(
                    f'从断点恢复训练: {checkpoint_path} '
                    f'(已完成 {completed_epochs}/{epochs} epoch)'
                )
                if prepared_checkpoint.action == CHECKPOINT_ACTION_REJECT:
                    checkpoint_state = prepared_checkpoint.state
                    error_msg = (
                        '该断点仅包含模型权重，缺少可续训的 epoch/optimizer 状态，'
                        '已阻止 DDP 将其当作新训练并删除；请重新训练，或使用更早的 '
                        'epoch*.pt 完整断点继续训练'
                    )
                    if checkpoint_state.configured_epochs:
                        error_msg += (
                            f'（断点原目标 epochs={checkpoint_state.configured_epochs}）'
                        )
                    update_log_local(error_msg)
                    train_task.status = 'error'
                    train_task.error_log = error_msg
                    db.session.commit()
                    raise Exception(error_msg)
                try:
                    yolo_model = YOLO(checkpoint_path)
                    if prepared_checkpoint.action == CHECKPOINT_ACTION_FINALIZE:
                        finalized_checkpoint_path = checkpoint_path
                        update_log_local(
                            '检测到训练已进入最终权重阶段，数据库进度最多滞后 1 个 epoch；'
                            '将跳过重复 DDP 训练并直接保存最终模型'
                        )
                    else:
                        resume_train = True
                        update_log_local('断点权重加载成功，将从下一 epoch 继续训练')
                except Exception as e:
                    error_msg = f'断点权重加载失败: {str(e)}'
                    update_log_local(error_msg)
                    train_task.status = 'error'
                    train_task.error_log = error_msg
                    db.session.commit()
                    raise Exception(error_msg)
            else:
                update_log_local(f"尝试加载预训练模型: {model_arch}")
                local_model_arch, resolve_error = _resolve_pretrained_model_path(model_arch, task_id)
                if resolve_error:
                    update_log_local(resolve_error)
                    train_task.status = 'error'
                    train_task.error_log = resolve_error
                    db.session.commit()
                    raise Exception(resolve_error)
                if local_model_arch != model_arch:
                    update_log_local(f"预训练模型已解析为本地路径: {local_model_arch}")

                try:
                    yolo_model = YOLO(local_model_arch)
                    update_log_local("预训练模型加载成功!")
                except Exception as e:
                    error_msg = f"预训练模型加载失败: {str(e)}"
                    update_log_local(error_msg)
                    train_task.status = 'error'
                    train_task.error_log = error_msg
                    db.session.commit()
                    raise Exception(error_msg)

            # 保存模型引用以便可能的停止操作
            train_processes[task_id] = yolo_model

            # 更新状态：开始训练
            train_status[task_id].update({
                'status': 'train',
                'message': '正在训练模型...',
                'progress': 15
            })
            train_task.status = 'train'
            db.session.commit()
            if finalized_checkpoint_path:
                update_log_local(
                    '断点已包含最终模型权重，开始补齐训练结果保存流程...',
                    progress=89,
                )
            elif resume_mode:
                completed_epochs = _get_completed_epochs(train_task.hyperparameters)
                update_log_local(
                    f"继续训练模型，目标共 {epochs} 个 epochs（已完成 {completed_epochs}）...",
                    progress=15,
                )
            else:
                update_log_local(f"开始训练模型，共{epochs}个epochs...", progress=15)

            def on_train_epoch_end(trainer):
                try:
                    db.session.refresh(train_task)
                except Exception:
                    pass
                _raise_if_train_stop_requested(task_id)
                total_epochs_count = max(1, int(getattr(trainer, 'epochs', epochs)))
                now_epoch = int(getattr(trainer, 'epoch', 0)) + 1
                progress_delta = (
                    now_epoch * 74 + total_epochs_count - 1
                ) // total_epochs_count
                progress = min(89, 15 + progress_delta)
                train_status[task_id].update({
                    'progress': progress,
                    'message': f'训练中 epoch {now_epoch}/{total_epochs_count}...',
                })
                train_task.progress = progress
                train_task.hyperparameters = _update_hyperparameters_field(
                    train_task.hyperparameters,
                    completed_epochs=now_epoch,
                )
                checkpoint_path = _resolve_train_checkpoint_path(model_dir)
                if checkpoint_path:
                    train_task.checkpoint_dir = checkpoint_path
                if now_epoch == 1 or now_epoch == total_epochs_count or now_epoch % 5 == 0:
                    update_log_local(
                        f'训练进度: epoch {now_epoch}/{total_epochs_count} ({progress}%)',
                        progress=progress,
                    )
                else:
                    try:
                        db.session.commit()
                    except Exception as commit_err:
                        print(f'更新训练进度失败: {commit_err}')

            batch_heartbeat = {
                'last_log_at': 0.0,
                'epoch_index': None,
                'batch_count': 0,
            }

            def on_train_batch_end(trainer):
                _raise_if_train_stop_requested(task_id)
                now_monotonic = time.monotonic()
                train_loader = getattr(trainer, 'train_loader', None)
                try:
                    total_batches = len(train_loader) if train_loader is not None else 0
                except TypeError:
                    total_batches = 0
                if total_batches <= 0:
                    return
                epoch_index = int(getattr(trainer, 'epoch', 0)) + 1
                if batch_heartbeat['epoch_index'] != epoch_index:
                    batch_heartbeat['epoch_index'] = epoch_index
                    batch_heartbeat['batch_count'] = 0
                batch_heartbeat['batch_count'] += 1
                batch_index = min(total_batches, batch_heartbeat['batch_count'])
                if batch_index < total_batches and now_monotonic - batch_heartbeat['last_log_at'] < 30:
                    return

                total_epochs_count = max(1, int(getattr(trainer, 'epochs', epochs)))
                completed_batches = (epoch_index - 1) * total_batches + batch_index
                total_train_batches = total_epochs_count * total_batches
                progress_delta = (
                    completed_batches * 74 + total_train_batches - 1
                ) // total_train_batches
                progress = min(89, 15 + progress_delta)
                batch_heartbeat['last_log_at'] = now_monotonic
                train_status[task_id].update({
                    'progress': progress,
                    'message': (
                        f'训练中 epoch {epoch_index}/{total_epochs_count}, '
                        f'batch {batch_index}/{total_batches}...'
                    ),
                })
                update_log_local(
                    f'训练心跳: epoch {epoch_index}/{total_epochs_count}, '
                    f'batch {batch_index}/{total_batches}',
                    progress=progress,
                )

            def on_val_start(_trainer):
                # 验证阶段 DataLoader pin_memory 容易触发显存峰值，先同步并释放训练残留缓存
                release_cuda_memory(synchronize=True)

            yolo_model.add_callback('on_train_epoch_end', on_train_epoch_end)
            yolo_model.add_callback('on_train_batch_end', on_train_batch_end)
            yolo_model.add_callback('on_val_start', on_val_start)

            if finalized_checkpoint_path:
                train_status[task_id].update({
                    'message': '最终权重已确认，正在保存训练结果...',
                    'progress': 90,
                })
                update_log_local(
                    '最终权重校验通过，未启动 DDP 子进程',
                    progress=90,
                )
            else:
                update_log_local(
                    f"开始训练模型，配置: 数据文件={data_yaml_path}, epochs={epochs}, "
                    f"图像尺寸={img_size}x{img_size}, 批次大小={batch_size}"
                )

                gpu_status = check_gpu_status()
                update_log_local(
                    f"GPU状态检查: {json.dumps(gpu_status, indent=2, ensure_ascii=False)}"
                )

                device = resolve_yolo_train_device(use_gpu, gpu_ids)
                if device == 'cpu':
                    if use_gpu:
                        if not gpu_status.get('use_gpu_env'):
                            update_log_local(
                                "警告: 请求使用GPU，但环境变量 USE_GPU=False，已回退到 CPU 训练。"
                            )
                        else:
                            update_log_local(
                                "警告: 请求使用GPU，但当前无可用 CUDA 设备，回退到 CPU 训练。"
                            )
                        update_log_local(
                            f"GPU诊断: USE_GPU={gpu_status.get('use_gpu_env')}, "
                            f"CUDA可用={gpu_status.get('cuda_available')}, "
                            f"设备数={gpu_status.get('device_count')}, "
                            f"PyTorch={torch.__version__}, "
                            f"CUDA={getattr(torch.version, 'cuda', '未知')}"
                        )
                    else:
                        update_log_local("使用 CPU 进行训练")
                elif isinstance(device, list):
                    if batch_size % len(device) != 0:
                        raise ValueError(
                            f'多卡训练 batch_size={batch_size} 必须能被 GPU 数量 '
                            f'{len(device)} 整除；请选择较少 GPU，或将 batch_size 调整为 '
                            f'{((batch_size + len(device) - 1) // len(device)) * len(device)}'
                        )
                    names = []
                    for idx in device:
                        try:
                            names.append(f"GPU{idx}({torch.cuda.get_device_name(idx)})")
                        except Exception:
                            names.append(f"GPU{idx}")
                    update_log_local(
                        f"多卡并行训练 (DDP): {len(device)} 张 GPU "
                        f"[{format_device_for_log(device)}] — " + ', '.join(names)
                    )
                    update_log_local(
                        f"提示: batch_size={batch_size} 为总批次大小，将分配到 "
                        f"{len(device)} 张 GPU"
                    )
                else:
                    try:
                        gpu_name = torch.cuda.get_device_name(device)
                    except Exception:
                        gpu_name = 'unknown'
                    update_log_local(f"单卡 GPU 训练: GPU{device} ({gpu_name})")

                train_workers = resolve_train_dataloader_workers(use_gpu)
                use_amp = bool(use_gpu and device != 'cpu')
                update_log_local(
                    f'DataLoader workers={train_workers}，AMP={use_amp} '
                    f'（workers 可通过 TRAIN_DATALOADER_WORKERS 覆盖）'
                )
                update_log_local('已进入训练计算阶段，等待首个 batch 完成...', progress=16)
                progress_monitor_stop = threading.Event()
                ddp_stop_watcher_thread = None
                if isinstance(device, list):
                    ddp_stop_watcher_thread = threading.Thread(
                        target=_watch_task_ddp_stop,
                        args=(
                            task_id,
                            model_dir,
                            progress_monitor_stop,
                            lambda message: update_log(message, task_id),
                        ),
                        daemon=True,
                    )
                    ddp_stop_watcher_thread.start()
                progress_monitor_thread = threading.Thread(
                    target=_monitor_training_progress,
                    args=(
                        application,
                        task_id,
                        record_id,
                        model_dir,
                        epochs,
                        progress_monitor_stop,
                    ),
                    daemon=True,
                )
                progress_monitor_thread.start()
                try:
                    yolo_model.train(
                        data=data_yaml_path,
                        epochs=epochs,
                        imgsz=img_size,
                        batch=batch_size,
                        project=model_dir,
                        name='train_results',
                        exist_ok=True,
                        device=device,
                        save_period=5,
                        resume=resume_train,
                        workers=train_workers,
                        cache=False,
                        amp=use_amp,
                    )
                finally:
                    progress_monitor_stop.set()
                    progress_monitor_thread.join(timeout=2)
                    if ddp_stop_watcher_thread is not None:
                        ddp_stop_watcher_thread.join(timeout=2)

            train_output_dir = _resolve_train_results_dir(model_dir)
            model_id = train_task.model_id
            artifact_bucket = TRAIN_ARTIFACTS_BUCKET

            # 存储 results.csv（上传 Minio models 桶），路径写入 metrics_path
            results_csv_path = os.path.join(train_output_dir, 'results.csv')
            if os.path.exists(results_csv_path):
                minio_csv_path = _train_artifact_object_key(model_id, task_id, 'results.csv')
                csv_success, csv_error = ModelService.upload_to_minio(
                    bucket_name=artifact_bucket,
                    object_name=minio_csv_path,
                    file_path=results_csv_path,
                )
                if csv_success:
                    accessible_csv_url = _build_minio_download_url(artifact_bucket, minio_csv_path)
                    update_log_local(f"训练结果CSV已上传至Minio: {accessible_csv_url}")
                    train_task.metrics_path = accessible_csv_url
                else:
                    update_log_local(f"训练结果CSV上传Minio失败: {csv_error or '请检查日志'}")
            else:
                update_log_local(f"未找到训练结果CSV文件: {results_csv_path}")

            # 存储 results.png，路径写入 train_results_path
            results_png_path = os.path.join(train_output_dir, 'results.png')
            if os.path.exists(results_png_path):
                minio_png_path = _train_artifact_object_key(model_id, task_id, 'results.png')
                png_success, png_error = ModelService.upload_to_minio(
                    bucket_name=artifact_bucket,
                    object_name=minio_png_path,
                    file_path=results_png_path,
                )
                if png_success:
                    accessible_url = _build_minio_download_url(artifact_bucket, minio_png_path)
                    update_log_local(f"训练结果图表已上传至Minio: {accessible_url}")
                    train_task.train_results_path = accessible_url
                    db.session.commit()
                else:
                    update_log_local(f"训练结果图表上传Minio失败: {png_error or '请检查日志'}")
            else:
                update_log_local(f"未找到训练结果图表文件: {results_png_path}")

            # 检查是否应该停止训练
            if _is_stop_requested(task_id, train_task):
                log_msg = '训练已停止'
                train_status[task_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': train_status[task_id].get('log', '') + log_msg + '\n'
                }
                update_log_local(log_msg)
                return

            # 更新训练状态 - 训练完成
            train_status[task_id].update({
                'status': 'completed',
                'message': '训练完成，正在保存结果...',
                'progress': 90
            })
            update_log_local("训练完成，正在保存结果...", progress=90)

            update_log_local("模型训练完成!")
            update_log_local(f"训练结果保存路径: {train_output_dir}")

            # 保存最佳模型
            best_model_path = finalized_checkpoint_path or os.path.join(
                train_output_dir, 'weights', 'best.pt'
            )
            if finalized_checkpoint_path:
                update_log_local(
                    f'使用已完成训练的最终断点作为最佳模型: {best_model_path}'
                )
            update_log_local(f"检查最佳模型文件是否存在: {best_model_path}")

            if os.path.exists(best_model_path):
                update_log_local(f"找到最佳模型文件，开始复制到保存目录: {best_model_path}")

                # 将最佳模型复制到模型存储目录
                model_save_dir = os.path.join(current_app.root_path, 'static', 'train_tasks', str(task_id), 'weights')
                os.makedirs(model_save_dir, exist_ok=True)
                local_model_path = os.path.join(model_save_dir, 'best.pt')
                shutil.copy(best_model_path, local_model_path)

                update_log_local(f"模型文件已成功复制到保存目录: {model_save_dir}")

                # ================= Minio上传功能 =================
                update_log_local("开始上传最佳模型到Minio...", progress=95)

                # 上传最佳模型
                minio_model_path = _train_artifact_object_key(model_id, task_id, 'best.pt')
                model_success, model_error = ModelService.upload_to_minio(
                    bucket_name=artifact_bucket,
                    object_name=minio_model_path,
                    file_path=local_model_path
                )

                if model_success:
                    accessible_model_url = _build_minio_download_url(artifact_bucket, minio_model_path)
                    update_log_local(f"模型已成功上传至Minio: {accessible_model_url}")
                    train_task.minio_model_path = accessible_model_url
                    db.session.commit()
                else:
                    update_log_local("模型上传Minio失败，请检查日志")
                    train_task.best_model_path = local_model_path
                    db.session.commit()

                # 上传训练日志，参照results.png的写法
                log_content = train_task.train_log
                log_path = os.path.join(model_save_dir, f"train_log_{train_task.id}.txt")
                with open(log_path, 'w') as f:
                    f.write(log_content)

                minio_log_path = _train_artifact_object_key(model_id, task_id, 'train_log.txt')
                log_success, log_error = ModelService.upload_to_minio(
                    bucket_name=artifact_bucket,
                    object_name=minio_log_path,
                    file_path=log_path
                )

                if log_success:
                    accessible_log_url = _build_minio_download_url(artifact_bucket, minio_log_path)
                    update_log_local(f"训练日志已上传至Minio: {accessible_log_url}")
                    train_task.minio_log_path = accessible_log_url  # 保存URL而不是路径
                else:
                    update_log_local("训练日志上传Minio失败，请检查日志")
                # ================= Minio上传完成 =================

                # 更新训练记录中的本地模型路径
                train_task.best_model_path = local_model_path

            else:
                error_msg = "未找到训练完成的最佳模型文件"
                update_log_local(error_msg)
                train_task.status = 'error'
                train_task.error_log = error_msg
                db.session.commit()
                raise Exception(error_msg)

            # 更新训练状态 - 完成
            train_status[task_id].update({
                'status': 'completed',
                'message': '模型训练完成并已保存',
                'progress': 100
            })

            # 更新训练记录状态
            staged_checkpoint_path = (train_task.checkpoint_dir or '').strip()
            train_task.status = 'completed'
            train_task.end_time = datetime.utcnow()
            train_task.progress = 100
            train_task.checkpoint_dir = ''
            train_task.hyperparameters = _update_hyperparameters_field(
                train_task.hyperparameters,
                completed_epochs=epochs,
            )
            db.session.commit()
            cleanup_staged_checkpoint(
                staged_checkpoint_path,
                os.path.join(get_datasets_root(), '.resume_checkpoints'),
            )
            update_log_local("模型训练完成并已保存", progress=100)

            _cleanup_train_dataset_artifacts(
                model_dir, dataset_zip_path, update_log_local
            )
            dataset_cleaned = True

    except Exception as e:
        from run import create_app
        user_stopped = (
            '训练已被用户停止' in str(e)
            or _is_stop_requested(task_id)
        )
        application = create_app()
        with application.app_context():
            task = TrainTask.query.get(record_id) if record_id else None
            error_msg = '训练已停止' if user_stopped else f'训练出错: {str(e)}'
            log_msg = f'[{_train_log_timestamp()}] {error_msg}'
            terminal_progress = train_status.get(task_id, {}).get('progress', 0) or 0

            if task:
                task.status = 'stopped' if user_stopped else 'error'
                task.end_time = datetime.utcnow()
                task.train_log = (task.train_log or '') + log_msg + '\n'
                model_dir = get_train_task_dir(task_id)
                completed_epochs = max(
                    _get_completed_epochs(task.hyperparameters),
                    _read_completed_result_epochs(model_dir),
                )
                if user_stopped:
                    if completed_epochs <= 0 and task_id in train_status:
                        progress = train_status[task_id].get('progress', 0) or 0
                        total_epochs = _get_total_epochs_from_hp(task.hyperparameters, epochs)
                        if total_epochs > 0 and progress > 15:
                            completed_epochs = max(
                                1,
                                int((progress - 15) * total_epochs / 74),
                            )
                    _persist_stop_checkpoint(
                        task,
                        model_dir,
                        completed_epochs,
                        lambda msg: update_log(msg, task_id, train_task=task),
                    )
                else:
                    task.error_log = f"{str(e)}\n{traceback.format_exc()}"
                    checkpoint_path = _resolve_train_checkpoint_path(model_dir)
                    if checkpoint_path:
                        total_epochs = _get_total_epochs_from_hp(task.hyperparameters, epochs)
                        terminal_progress = max(
                            terminal_progress,
                            _progress_for_completed_epochs(completed_epochs, total_epochs),
                        )
                        task.progress = terminal_progress
                        _persist_stop_checkpoint(
                            task,
                            model_dir,
                            completed_epochs,
                            lambda msg: update_log(msg, task_id, train_task=task),
                        )
                        update_log(
                            '训练异常退出，但已保留可用断点；可选择单张 GPU 继续训练',
                            task_id,
                            train_task=task,
                        )
                    if isinstance(e, subprocess.CalledProcessError) and any(
                        'torch.distributed' in str(part)
                        for part in (e.cmd if isinstance(e.cmd, (list, tuple)) else [e.cmd])
                    ):
                        update_log(
                            'DDP 子进程异常退出；完整 rank/CUDA/NCCL 原因请查看 '
                            'ai-service 容器同期标准输出',
                            task_id,
                            train_task=task,
                        )
                db.session.commit()

            update_log(error_msg, task_id, train_task=task)
            if not user_stopped:
                traceback.print_exc()

            if task_id in train_status:
                train_status[task_id].update({
                    'status': 'stopped' if user_stopped else 'error',
                    'message': error_msg,
                    'progress': terminal_progress,
                    **({} if user_stopped else {
                        'error_details': str(e),
                        'traceback': traceback.format_exc(),
                    }),
                    'log': train_status[task_id].get('log', '') + log_msg + '\n'
                    + ('' if user_stopped else traceback.format_exc()),
                })
    finally:
        yolo_model_ref = train_processes.pop(task_id, None)
        if yolo_model_ref is not None:
            yolo_model = yolo_model_ref
        try:
            _release_train_model(
                yolo_model,
                log_fn=lambda msg: update_log(msg, task_id),
            )
        except Exception:
            release_cuda_memory()
        # 异常时清理已解压的数据集；停止状态保留数据集供断点续训
        if not dataset_cleaned and model_dir_for_cleanup:
            terminal = train_status.get(task_id, {}).get('status')
            if terminal == 'error':
                ds_path = dataset_path_for_cleanup

                def _log_cleanup(msg):
                    update_log(msg, task_id)

                try:
                    _cleanup_train_dataset_artifacts(
                        model_dir_for_cleanup,
                        ds_path,
                        _log_cleanup,
                        remove_uploaded_zip=False,
                    )
                except Exception:
                    pass
