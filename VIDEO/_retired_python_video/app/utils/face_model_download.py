"""人脸特征提取模型 face_rec.onnx 下载与状态查询"""
import os
import re
import shutil
import threading
import urllib.error
import urllib.request
import zipfile
from typing import Any, Dict

from app.utils.face_model_paths import FACE_MATCH_MODEL_PATH

FACE_REC_DOWNLOAD_URL = os.getenv(
    'FACE_REC_MODEL_DOWNLOAD_URL',
    'https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip',
)
# GitHub v0.7 发行包为根目录 w600k_r50.onnx；部分镜像/旧包为 buffalo_l/ 前缀
ONNX_ZIP_CANDIDATES = ('w600k_r50.onnx', 'buffalo_l/w600k_r50.onnx')
# 完整模型约 167MB，低于此阈值视为未下载或损坏
MIN_MODEL_SIZE_BYTES = 10 * 1024 * 1024
# buffalo_l.zip 约 280MB，用于 Content-Length 缺失时的进度估算
ESTIMATED_ZIP_SIZE_BYTES = 280 * 1024 * 1024
DOWNLOAD_CHUNK_SIZE = 256 * 1024
DOWNLOAD_USER_AGENT = 'EasyAIoT-VIDEO/1.0'
DOWNLOAD_TIMEOUT_SEC = int(os.getenv('FACE_REC_MODEL_DOWNLOAD_TIMEOUT', '300'))

_lock = threading.Lock()
_state: Dict[str, Any] = {
    'status': 'idle',  # idle | downloading | done | error
    'stage': 'idle',  # idle | downloading | extracting | done | error
    'progress': 0,
    'downloaded_bytes': 0,
    'total_bytes': 0,
    'error': None,
}


def _zip_partial_path() -> str:
    return os.path.join(os.path.dirname(FACE_MATCH_MODEL_PATH), 'buffalo_l.zip.downloading')


def _onnx_partial_path() -> str:
    return f'{FACE_MATCH_MODEL_PATH}.downloading'


def _ensure_writable_file_path(path: str) -> None:
    """移除误建为目录的路径（Docker 单独挂载不存在的文件时会建成目录）。"""
    if os.path.isdir(path):
        shutil.rmtree(path)


def _prepare_model_target() -> None:
    """确保模型目标与临时路径均为可写文件路径。"""
    parent = os.path.dirname(FACE_MATCH_MODEL_PATH) or '.'
    os.makedirs(parent, exist_ok=True)
    _ensure_writable_file_path(FACE_MATCH_MODEL_PATH)
    _ensure_writable_file_path(_onnx_partial_path())
    if os.path.isdir(_zip_partial_path()):
        _ensure_writable_file_path(_zip_partial_path())


def _get_zip_partial_bytes() -> int:
    path = _zip_partial_path()
    if not os.path.isfile(path):
        return 0
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def _parse_content_range_total(content_range: str, content_length: int, existing_size: int) -> int:
    if content_range:
        match = re.match(r'bytes\s+\d+-\d+/(\d+|\*)', content_range.strip(), re.I)
        if match and match.group(1) != '*':
            return int(match.group(1))
    if content_length > 0:
        return existing_size + content_length
    return ESTIMATED_ZIP_SIZE_BYTES


def _calc_download_progress(downloaded: int, total: int) -> int:
    if total <= 0:
        return 0
    return min(85, int(downloaded * 85 / total))


def _reset_error_if_idle() -> None:
    if _state['status'] == 'idle':
        _state['error'] = None


def is_face_rec_model_available() -> bool:
    if not os.path.isfile(FACE_MATCH_MODEL_PATH):
        return False
    try:
        return os.path.getsize(FACE_MATCH_MODEL_PATH) >= MIN_MODEL_SIZE_BYTES
    except OSError:
        return False


def _is_zip_complete(zip_path: str) -> bool:
    if not os.path.isfile(zip_path):
        return False
    try:
        with zipfile.ZipFile(zip_path) as zf:
            _resolve_onnx_member(zf)
        return True
    except (zipfile.BadZipFile, KeyError, OSError):
        return False


def _sync_partial_progress_locked() -> None:
    if is_face_rec_model_available():
        return
    partial_bytes = _get_zip_partial_bytes()
    if partial_bytes <= 0:
        return
    total = int(_state['total_bytes']) or ESTIMATED_ZIP_SIZE_BYTES
    if _state['status'] != 'downloading':
        _state['downloaded_bytes'] = partial_bytes
        if partial_bytes < total:
            _state['progress'] = _calc_download_progress(partial_bytes, total)


def _build_status_locked() -> Dict[str, Any]:
    exists = is_face_rec_model_available()
    size_bytes = os.path.getsize(FACE_MATCH_MODEL_PATH) if exists else 0
    zip_partial_bytes = 0 if exists else _get_zip_partial_bytes()
    zip_complete = _is_zip_complete(_zip_partial_path()) if zip_partial_bytes > 0 else False
    resumable = (
        not exists
        and bool(FACE_REC_DOWNLOAD_URL)
        and (zip_partial_bytes > 0 or zip_complete)
    )
    _reset_error_if_idle()
    downloading = _state['status'] == 'downloading'
    stage = _state['stage']
    if exists:
        stage = 'done'
    elif downloading:
        stage = _state['stage'] or 'downloading'
    elif resumable and _state['status'] == 'error':
        stage = 'error'
    elif resumable and zip_complete:
        stage = 'idle'
    elif resumable:
        stage = 'idle'
    elif not downloading and _state['status'] == 'error':
        stage = 'error'
    elif not downloading:
        stage = 'idle'

    total_bytes = int(_state['total_bytes']) or ESTIMATED_ZIP_SIZE_BYTES
    downloaded_bytes = int(_state['downloaded_bytes'])
    if not exists and zip_partial_bytes > downloaded_bytes:
        downloaded_bytes = zip_partial_bytes

    progress = 0
    if exists:
        progress = 100
    elif downloading or resumable:
        if zip_complete and not downloading:
            progress = 85
        else:
            progress = _calc_download_progress(downloaded_bytes, total_bytes)

    return {
        'exists': exists,
        'filename': os.path.basename(FACE_MATCH_MODEL_PATH),
        'path': FACE_MATCH_MODEL_PATH,
        'size_bytes': size_bytes,
        'downloading': downloading,
        'resumable': resumable,
        'stage': stage,
        'progress': progress,
        'downloaded_bytes': downloaded_bytes,
        'total_bytes': total_bytes,
        'error': _state['error'],
    }


def get_face_rec_model_status() -> Dict[str, Any]:
    with _lock:
        _sync_partial_progress_locked()
        return _build_status_locked()


def _set_progress(stage: str, progress: int, downloaded: int = 0, total: int = 0) -> None:
    with _lock:
        _state['stage'] = stage
        _state['downloaded_bytes'] = downloaded
        if total > 0:
            _state['total_bytes'] = total
        _state['progress'] = max(int(_state['progress']), int(progress))


def _download_with_progress(url: str, dest_path: str) -> None:
    existing_size = _get_zip_partial_bytes() if os.path.abspath(dest_path) == os.path.abspath(_zip_partial_path()) else 0
    if os.path.isfile(dest_path) and existing_size == 0:
        try:
            existing_size = os.path.getsize(dest_path)
        except OSError:
            existing_size = 0

    headers = {'User-Agent': DOWNLOAD_USER_AGENT}
    if existing_size > 0:
        headers['Range'] = f'bytes={existing_size}-'

    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT_SEC)
    except urllib.error.HTTPError as exc:
        if exc.code == 416 and existing_size > 0 and _is_zip_complete(dest_path):
            size = os.path.getsize(dest_path)
            _set_progress('downloading', 85, downloaded=size, total=size)
            return
        raise

    with resp:
        status_code = getattr(resp, 'status', None) or resp.getcode()
        content_length = int(resp.headers.get('Content-Length', 0) or 0)
        content_range = resp.headers.get('Content-Range', '') or ''
        total = _parse_content_range_total(content_range, content_length, existing_size)

        if status_code == 200 and existing_size > 0:
            existing_size = 0
            total = content_length or ESTIMATED_ZIP_SIZE_BYTES

        downloaded = existing_size
        _set_progress(
            'downloading',
            max(1, _calc_download_progress(downloaded, total)),
            downloaded=downloaded,
            total=total,
        )

        file_mode = 'ab' if existing_size > 0 and status_code == 206 else 'wb'
        if file_mode == 'wb':
            downloaded = 0

        with open(dest_path, file_mode) as out_file:
            while True:
                chunk = resp.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                _set_progress(
                    'downloading',
                    _calc_download_progress(downloaded, total),
                    downloaded=downloaded,
                    total=total,
                )


def _resolve_onnx_member(zf: zipfile.ZipFile) -> str:
    names = set(zf.namelist())
    for candidate in ONNX_ZIP_CANDIDATES:
        if candidate in names:
            return candidate
    for name in zf.namelist():
        if name.rstrip('/').endswith('w600k_r50.onnx'):
            return name
    onnx_entries = [n for n in zf.namelist() if n.lower().endswith('.onnx')]
    raise KeyError(
        'archive 中未找到 w600k_r50.onnx '
        f'(已尝试 {ONNX_ZIP_CANDIDATES})，当前 onnx 条目: {onnx_entries}'
    )


def _extract_onnx(zip_path: str, target_path: str) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        member = _resolve_onnx_member(zf)
        info = zf.getinfo(member)
        total = info.file_size or MIN_MODEL_SIZE_BYTES
        written = 0
        _set_progress('extracting', 86, downloaded=0, total=total)

        with zf.open(member) as src, open(target_path, 'wb') as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
                written += len(chunk)
                progress = 86 + min(13, int(written * 13 / total))
                _set_progress('extracting', progress, downloaded=written, total=total)


def _cleanup_zip_partial() -> None:
    zip_path = _zip_partial_path()
    if os.path.isfile(zip_path):
        try:
            os.remove(zip_path)
        except OSError:
            pass


def _do_download() -> None:
    zip_path = _zip_partial_path()
    onnx_partial = _onnx_partial_path()
    try:
        resume_bytes = _get_zip_partial_bytes()
        zip_complete = _is_zip_complete(zip_path)
        with _lock:
            _state['status'] = 'downloading'
            _state['stage'] = 'downloading'
            _state['error'] = None
            if zip_complete:
                size = os.path.getsize(zip_path)
                _state['downloaded_bytes'] = size
                _state['total_bytes'] = size
                _state['progress'] = 85
            elif resume_bytes > 0:
                total = int(_state['total_bytes']) or ESTIMATED_ZIP_SIZE_BYTES
                _state['downloaded_bytes'] = resume_bytes
                _state['total_bytes'] = total
                _state['progress'] = _calc_download_progress(resume_bytes, total)
            else:
                _state['progress'] = 0
                _state['downloaded_bytes'] = 0
                _state['total_bytes'] = ESTIMATED_ZIP_SIZE_BYTES

        _prepare_model_target()

        if not zip_complete:
            _download_with_progress(FACE_REC_DOWNLOAD_URL, zip_path)
            if not _is_zip_complete(zip_path):
                raise RuntimeError('模型包下载不完整，请检查网络后点击继续下载')

        with _lock:
            _state['progress'] = max(int(_state['progress']), 85)

        _ensure_writable_file_path(onnx_partial)
        _extract_onnx(zip_path, onnx_partial)
        _ensure_writable_file_path(FACE_MATCH_MODEL_PATH)
        os.replace(onnx_partial, FACE_MATCH_MODEL_PATH)
        _cleanup_zip_partial()

        with _lock:
            _state['status'] = 'done'
            _state['stage'] = 'done'
            _state['progress'] = 100
            _state['downloaded_bytes'] = os.path.getsize(FACE_MATCH_MODEL_PATH)
            _state['total_bytes'] = _state['downloaded_bytes']
            _state['error'] = None
    except Exception as exc:
        if os.path.isfile(onnx_partial):
            try:
                os.remove(onnx_partial)
            except OSError:
                pass
        partial_bytes = _get_zip_partial_bytes()
        with _lock:
            _state['status'] = 'error'
            _state['stage'] = 'error'
            _state['error'] = str(exc)
            if partial_bytes > 0:
                total = int(_state['total_bytes']) or ESTIMATED_ZIP_SIZE_BYTES
                _state['downloaded_bytes'] = partial_bytes
                _state['progress'] = _calc_download_progress(partial_bytes, total)


def start_face_rec_model_download() -> Dict[str, Any]:
    with _lock:
        if is_face_rec_model_available():
            _state['status'] = 'done'
            _state['stage'] = 'done'
            _state['progress'] = 100
            _state['error'] = None
            return {'started': False, 'message': '模型已存在', **_build_status_locked()}

        if _state['status'] == 'downloading':
            return {'started': False, 'message': '模型正在下载中', **_build_status_locked()}

        resume_bytes = _get_zip_partial_bytes()
        zip_complete = _is_zip_complete(_zip_partial_path())
        _state['status'] = 'downloading'
        _state['stage'] = 'downloading'
        _state['error'] = None
        if zip_complete:
            size = os.path.getsize(_zip_partial_path())
            _state['downloaded_bytes'] = size
            _state['total_bytes'] = size
            _state['progress'] = 85
            message = '模型包已下载完整，正在解压安装'
        elif resume_bytes > 0:
            total = int(_state['total_bytes']) or ESTIMATED_ZIP_SIZE_BYTES
            _state['downloaded_bytes'] = resume_bytes
            _state['total_bytes'] = total
            _state['progress'] = _calc_download_progress(resume_bytes, total)
            message = f'已从 {_format_bytes(resume_bytes)} 处续传'
        else:
            _state['progress'] = 0
            _state['downloaded_bytes'] = 0
            _state['total_bytes'] = ESTIMATED_ZIP_SIZE_BYTES
            message = '已开始下载'
        status = _build_status_locked()

    thread = threading.Thread(target=_do_download, name='face-rec-model-download', daemon=True)
    thread.start()
    return {'started': True, 'message': message, **status}


def _format_bytes(num: int) -> str:
    if num >= 1024 * 1024 * 1024:
        return f'{num / (1024 * 1024 * 1024):.1f} GB'
    if num >= 1024 * 1024:
        return f'{num / (1024 * 1024):.1f} MB'
    if num >= 1024:
        return f'{num / 1024:.1f} KB'
    return f'{num} B'
