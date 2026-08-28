"""
自动标注集群 Worker：采集 + 按 SAM/YOLO 策略智能标注。
"""
import importlib.util
import io
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

import requests

_ai_root = os.getenv('AI_ROOT', '/opt/easyaiot/AI')
if _ai_root not in sys.path:
    sys.path.insert(0, _ai_root)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [auto_label_worker] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)
_worker_app = None


def _load_env():
    try:
        spec = importlib.util.spec_from_file_location('_ai_env', os.path.join(_ai_root, 'app', 'utils', 'ai_env.py'))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.load_ai_env(override=False)
    except Exception:
        pass


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def _report(status: str, **kwargs):
    subtask_id = os.getenv('SUBTASK_ID')
    base = os.getenv('AI_CONTROL_URL', 'http://127.0.0.1:5000').rstrip('/')
    url = f'{base}/model/dataset/auto-label/subtask/{subtask_id}/heartbeat'
    headers = {'Content-Type': 'application/json'}
    token = os.getenv('JWT_TOKEN')
    if token:
        headers['X-Authorization'] = f'Bearer {token}'
    try:
        requests.post(url, json={'status': status, **kwargs}, headers=headers, timeout=15)
    except Exception as e:
        logger.warning('心跳上报失败: %s', e)


def _capture_frame(stream_url: str, timeout_sec: int = 15) -> bytes | None:
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', stream_url.strip(),
           '-vframes', '1', '-f', 'image2pipe', '-vcodec', 'mjpeg', 'pipe:1']
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout_sec)
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
    except Exception as e:
        logger.debug('抽帧失败: %s', e)
    return None


def _upload_frame(java_url: str, dataset_id: int, image_bytes: bytes, filename: str) -> bool:
    try:
        resp = requests.post(
            f'{java_url.rstrip("/")}/admin-api/dataset/image/upload',
            files={'file': (filename, io.BytesIO(image_bytes), 'image/jpeg')},
            data={'datasetId': str(dataset_id), 'isZip': 'false'},
            timeout=60,
        )
        body = resp.json() if resp.status_code == 200 else {}
        return body.get('code') == 0 and int((body.get('data') or {}).get('successCount') or 0) > 0
    except Exception:
        return False


def _fetch_unlabeled(
    java_url: str,
    dataset_id: int,
    limit: int = 20,
    exclude_ids: set[int] | None = None,
) -> list:
    excluded = exclude_ids or set()
    selected = []
    page_no = 1
    page_size = max(1, limit)
    try:
        while len(selected) < limit:
            resp = requests.get(
                f'{java_url.rstrip("/")}/admin-api/dataset/image/page',
                params={
                    'datasetId': dataset_id,
                    'pageNo': page_no,
                    'pageSize': page_size,
                    'completed': 0,
                },
                timeout=60,
            )
            body = resp.json() if resp.status_code == 200 else {}
            if body.get('code') != 0:
                break
            rows = (body.get('data') or {}).get('list') or []
            selected.extend(
                row for row in rows
                if row.get('id') not in excluded
            )
            if len(rows) < page_size:
                break
            page_no += 1
        return selected[:limit]
    except Exception:
        return []


def _get_worker_app():
    global _worker_app
    if _worker_app is not None:
        return _worker_app

    from flask import Flask
    from db_models import db

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL 环境变量未设置')
    app = Flask('auto_label_worker', root_path=_ai_root)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    _worker_app = app
    return app


def _load_attempted_image_ids(task_id: int) -> set[int]:
    from db_models import AutoLabelResult

    app = _get_worker_app()
    with app.app_context():
        rows = AutoLabelResult.query.with_entities(AutoLabelResult.dataset_image_id).filter_by(
            task_id=task_id,
            status='SUCCESS',
        ).all()
    return {int(row[0]) for row in rows}


def _record_auto_label_result(task_id: int, image_id: int, annotations: str) -> None:
    from db_models import AutoLabelResult, db

    result = AutoLabelResult.query.filter_by(
        task_id=task_id,
        dataset_image_id=image_id,
    ).order_by(AutoLabelResult.id.desc()).first()
    if result is None:
        result = AutoLabelResult(task_id=task_id, dataset_image_id=image_id)
        db.session.add(result)
    result.annotations = annotations
    result.status = 'SUCCESS'
    result.error_message = None
    db.session.commit()


def _label_batch(
    task_proxy,
    images: list,
    java_url: str,
    dataset_id: int,
    attempted_image_ids: set[int] | None = None,
) -> tuple[int, int]:
    app = _get_worker_app()
    with app.app_context():
        return _label_batch_impl(
            task_proxy,
            images,
            java_url,
            dataset_id,
            attempted_image_ids,
        )


def _label_batch_impl(
    task_proxy,
    images: list,
    java_url: str,
    dataset_id: int,
    attempted_image_ids: set[int] | None = None,
) -> tuple[int, int]:
    from app.services.minio_service import ModelService
    from app.services.auto_label_dataset_writer import write_auto_label_result
    from app.services.auto_label_orchestrator import label_image_with_strategy, _update_counters
    from app.services.sam_service import get_sam_service
    import tempfile

    sam = get_sam_service()
    ok = fail = 0
    attempted = attempted_image_ids if attempted_image_ids is not None else set()
    for image in images:
        image_id = image.get('id')
        if image_id in attempted:
            continue
        path = image.get('path')
        if not path:
            fail += 1
            continue
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(path)
        parts = parsed.path.split('/')
        bucket = parts[4] if len(parts) >= 5 and parts[3] == 'buckets' else None
        key = parse_qs(parsed.query).get('prefix', [None])[0]
        if not bucket or not key:
            fail += 1
            continue
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        tmp.close()
        try:
            success, _ = ModelService.download_from_minio(bucket, key, tmp.name)
            if not success:
                fail += 1
                continue
            from PIL import Image as PILImage
            with PILImage.open(tmp.name) as img:
                w, h = img.size
            annos, mode = label_image_with_strategy(task_proxy, tmp.name, w, h, sam_service=sam)
            if mode == 'skip':
                continue
            annotations_json, _ = write_auto_label_result(
                java_url,
                dataset_id,
                image_id,
                annos,
                keep_annotated_images_only=_env_bool(
                    'KEEP_ANNOTATED_IMAGES_ONLY',
                    default=True,
                ),
            )
            _record_auto_label_result(task_proxy.id, image_id, annotations_json)
            attempted.add(image_id)
            _update_counters(task_proxy, mode, has_detections=bool(annos))
            if annos:
                ok += 1
        except Exception as e:
            logger.warning('标注失败 %s: %s', image_id, e)
            fail += 1
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
    return ok, fail


def _parent_task_url(base: str, dataset_id: int, task_id: int) -> str:
    return f'{base.rstrip("/")}/model/dataset/dataset/{dataset_id}/auto-label/task/{task_id}'


class _TaskProxy:
    """Worker 内轻量任务代理，从控制面同步父任务策略状态。"""
    def __init__(self):
        self.id = int(os.getenv('PARENT_TASK_ID', '0'))
        self.dataset_id = int(os.getenv('DATASET_ID', '0'))
        self.annotation_type = os.getenv('ANNOTATION_TYPE', 'rectangle')
        self.return_masks = os.getenv('RETURN_MASKS', 'false').lower() in ('1', 'true')
        self.confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.45'))
        self.text_prompts = os.getenv('TEXT_PROMPTS', '[]')
        self.model_id = None
        self.success_count = 0
        self.status = 'PROCESSING'
        self.pipeline_config = None
        self._load_parent_task()

    def _load_parent_task(self):
        base = os.getenv('AI_CONTROL_URL', 'http://127.0.0.1:5000').rstrip('/')
        headers = {}
        token = os.getenv('JWT_TOKEN')
        if token:
            headers['X-Authorization'] = f'Bearer {token}'
        try:
            resp = requests.get(
                _parent_task_url(base, self.dataset_id, self.id),
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                body = resp.json()
                data = body.get('data') or body
                if data.get('pipeline_config'):
                    self.pipeline_config = json.dumps(data['pipeline_config'], ensure_ascii=False)
                if data.get('model_id'):
                    self.model_id = data['model_id']
                self.text_prompts = json.dumps(data.get('text_prompts') or [], ensure_ascii=False)
                self.annotation_type = data.get('annotation_type') or self.annotation_type
                self.success_count = data.get('success_count') or 0
                return
        except Exception as e:
            logger.warning('拉取父任务状态失败，使用环境变量策略: %s', e)

        strategy = {}
        try:
            strategy = json.loads(os.getenv('STRATEGY_JSON', '{}'))
        except Exception:
            pass
        from app.services.auto_label_orchestrator import init_pipeline_strategy
        init_pipeline_strategy(self, strategy)
        if strategy.get('initial_model_id'):
            self.model_id = int(strategy['initial_model_id'])

    def refresh(self):
        self._load_parent_task()

    def is_stopped(self) -> bool:
        base = os.getenv('AI_CONTROL_URL', 'http://127.0.0.1:5000').rstrip('/')
        headers = {}
        token = os.getenv('JWT_TOKEN')
        if token:
            headers['X-Authorization'] = f'Bearer {token}'
        try:
            resp = requests.get(
                _parent_task_url(base, self.dataset_id, self.id),
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                data = (resp.json().get('data') or resp.json())
                status = data.get('status', '')
                phase = (data.get('pipeline_config') or {}).get('pipeline_phase', '')
                return status in ('PAUSED', 'CANCELLED', 'COMPLETED', 'FAILED') or phase in ('paused', 'cancelled')
        except Exception:
            pass
        return False


def _initial_counters() -> tuple[int, int, int]:
    return (
        int(os.getenv('INITIAL_CAPTURED_COUNT', '0')),
        int(os.getenv('INITIAL_LABELED_COUNT', '0')),
        int(os.getenv('INITIAL_FAILED_COUNT', '0')),
    )


def main():
    _load_env()
    os.environ.setdefault('SAM_ENABLED', 'true')
    stream_url = os.getenv('RTMP_URL', '')
    if not stream_url:
        _report('FAILED', error_message='未配置 RTMP_URL')
        sys.exit(1)

    java_url = os.getenv('JAVA_BACKEND_URL', 'http://localhost:48080')
    dataset_id = int(os.getenv('DATASET_ID', '0'))
    duration_hours = float(os.getenv('DURATION_HOURS', '8'))
    capture_interval = int(os.getenv('CAPTURE_INTERVAL_SEC', '30'))
    deadline = datetime.now() + timedelta(hours=duration_hours)
    task = _TaskProxy()
    attempted_image_ids = _load_attempted_image_ids(task.id)
    captured, labeled, failed = _initial_counters()
    cycle = 0

    _report('RUNNING', log='Worker 已启动（智能 SAM+YOLO 策略）')

    while datetime.now() < deadline:
        if task.is_stopped():
            _report('COMPLETED', captured_count=captured, labeled_count=labeled,
                    failed_count=failed, log='父任务已暂停/取消，Worker 退出')
            return

        cycle += 1
        img_bytes = _capture_frame(stream_url)
        if img_bytes:
            fname = f'cap_{os.getenv("SUBTASK_ID")}_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.jpg'
            if _upload_frame(java_url, dataset_id, img_bytes, fname):
                captured += 1

        task.refresh()
        batch = _fetch_unlabeled(
            java_url,
            dataset_id,
            limit=15,
            exclude_ids=attempted_image_ids,
        )
        if batch:
            ok, fl = _label_batch(
                task,
                batch,
                java_url,
                dataset_id,
                attempted_image_ids,
            )
            labeled += ok
            failed += fl

        _report('RUNNING', captured_count=captured, labeled_count=labeled,
                failed_count=failed, log=f'第{cycle}轮 采{captured} 标{labeled}')

        if datetime.now() >= deadline:
            break
        time.sleep(capture_interval)

    remaining = _fetch_unlabeled(
        java_url,
        dataset_id,
        limit=500,
        exclude_ids=attempted_image_ids,
    )
    if remaining:
        ok, fl = _label_batch(
            task,
            remaining,
            java_url,
            dataset_id,
            attempted_image_ids,
        )
        labeled += ok
        failed += fl

    _report('COMPLETED', captured_count=captured, labeled_count=labeled, failed_count=failed,
            log=f'完成 采{captured} 标{labeled}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception('Worker 异常')
        _report('FAILED', error_message=str(e))
        sys.exit(1)
