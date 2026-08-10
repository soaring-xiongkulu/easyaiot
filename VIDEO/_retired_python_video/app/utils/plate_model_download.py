"""车牌识别模型 plate_detect.onnx / plate_rec.onnx 下载与状态查询"""
import os
import shutil
import threading
import urllib.request
from typing import Any, Dict

from app.utils.plate_model_paths import PLATE_DETECT_MODEL_PATH, PLATE_REC_MODEL_PATH

PLATE_DETECT_DOWNLOAD_URL = os.getenv(
    'PLATE_DETECT_MODEL_DOWNLOAD_URL',
    '',
)
PLATE_REC_DOWNLOAD_URL = os.getenv(
    'PLATE_REC_MODEL_DOWNLOAD_URL',
    '',
)
MIN_DETECT_SIZE_BYTES = 10 * 1024 * 1024
MIN_REC_SIZE_BYTES = 10 * 1024
DOWNLOAD_USER_AGENT = 'EasyAIoT-VIDEO/1.0'

_lock = threading.Lock()
_state: Dict[str, Any] = {
    'status': 'idle',
    'stage': 'idle',
    'progress': 0,
    'error': None,
}


def _model_ready() -> bool:
    if not os.path.isfile(PLATE_DETECT_MODEL_PATH):
        return False
    if not os.path.isfile(PLATE_REC_MODEL_PATH):
        return False
    try:
        if os.path.getsize(PLATE_DETECT_MODEL_PATH) < MIN_DETECT_SIZE_BYTES:
            return False
        if os.path.getsize(PLATE_REC_MODEL_PATH) < MIN_REC_SIZE_BYTES:
            return False
    except OSError:
        return False
    data_path = f'{PLATE_REC_MODEL_PATH}.data'
    return os.path.isfile(data_path)


def get_plate_model_status() -> Dict[str, Any]:
    with _lock:
        exists = _model_ready()
        downloading = _state['status'] == 'downloading'
        stage = 'done' if exists else (_state['stage'] if downloading or _state['status'] == 'error' else 'idle')
        return {
            'exists': exists,
            'detect_model': os.path.basename(PLATE_DETECT_MODEL_PATH),
            'rec_model': os.path.basename(PLATE_REC_MODEL_PATH),
            'detect_path': PLATE_DETECT_MODEL_PATH,
            'rec_path': PLATE_REC_MODEL_PATH,
            'downloading': downloading,
            'stage': stage,
            'progress': int(_state['progress']) if downloading or exists else 0,
            'error': _state['error'],
        }


def _download_file(url: str, dest_path: str) -> None:
    req = urllib.request.Request(url, headers={'User-Agent': DOWNLOAD_USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest_path, 'wb') as out:
        shutil.copyfileobj(resp, out)


def _do_download() -> None:
    try:
        with _lock:
            _state['status'] = 'downloading'
            _state['stage'] = 'downloading'
            _state['progress'] = 0
            _state['error'] = None

        if not PLATE_DETECT_DOWNLOAD_URL or not PLATE_REC_DOWNLOAD_URL:
            raise RuntimeError('未配置车牌模型下载地址，请手动放置 plate_detect.onnx 与 plate_rec.onnx')

        detect_tmp = f'{PLATE_DETECT_MODEL_PATH}.downloading'
        rec_tmp = f'{PLATE_REC_MODEL_PATH}.downloading'
        _download_file(PLATE_DETECT_DOWNLOAD_URL, detect_tmp)
        with _lock:
            _state['progress'] = 50
        _download_file(PLATE_REC_DOWNLOAD_URL, rec_tmp)
        os.replace(detect_tmp, PLATE_DETECT_MODEL_PATH)
        os.replace(rec_tmp, PLATE_REC_MODEL_PATH)

        with _lock:
            _state['status'] = 'done'
            _state['stage'] = 'done'
            _state['progress'] = 100
            _state['error'] = None
    except Exception as exc:
        with _lock:
            _state['status'] = 'error'
            _state['stage'] = 'error'
            _state['error'] = str(exc)


def start_plate_model_download() -> Dict[str, Any]:
    with _lock:
        if _model_ready():
            _state['status'] = 'done'
            _state['stage'] = 'done'
            _state['progress'] = 100
            return {'started': False, 'message': '模型已存在', **get_plate_model_status()}

        if _state['status'] == 'downloading':
            return {'started': False, 'message': '模型正在下载中', **get_plate_model_status()}

        _state['status'] = 'downloading'
        status = get_plate_model_status()

    thread = threading.Thread(target=_do_download, name='plate-model-download', daemon=True)
    thread.start()
    return {'started': True, 'message': '已开始下载', **status}
