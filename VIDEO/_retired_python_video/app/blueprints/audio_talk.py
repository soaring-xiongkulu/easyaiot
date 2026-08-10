"""
ONVIF 语音对讲 API（Audio Back Channel）
"""
import base64
import logging
import time
import uuid
from threading import Lock

from flask import Blueprint, jsonify, request

from app.services.camera_service import _get_camera
from app.services.onvif_audio_backchannel import (
    probe_onvif_audio_backchannel_capabilities,
    test_onvif_audio_backchannel,
)

logger = logging.getLogger(__name__)

# 设备对讲能力缓存（能力不常变，避免每次打开播放器都探测摄像机）
_capabilities_cache: dict[str, tuple[float, dict]] = {}
_capabilities_cache_lock = Lock()
_capabilities_cache_ttl = 120.0

audio_talk_bp = Blueprint('audio_talk', __name__)

try:
    from app.services.audio_talk_service_onvif import (
        ONVIFAudioTalkServiceManager,
        ONVIF_AUDIO_AVAILABLE,
    )
    _audio_talk_manager = ONVIFAudioTalkServiceManager()
    AUDIO_TALK_AVAILABLE = True
except ImportError as exc:
    logger.warning('ONVIF 语音对讲服务未加载: %s', exc)
    _audio_talk_manager = None
    AUDIO_TALK_AVAILABLE = False
    ONVIF_AUDIO_AVAILABLE = False


def _resolve_camera(device_id: str):
    try:
        return _get_camera(device_id)
    except Exception:
        return None


@audio_talk_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    device_id = request.args.get('device_id') or request.args.get('camera_id')
    if not device_id:
        return jsonify({'code': 400, 'msg': '缺少设备 ID'}), 400

    camera = _resolve_camera(device_id)
    if not camera:
        return jsonify({'code': 404, 'msg': '设备不存在'}), 404

    rtsp_port = camera.port or 554

    cache_key = f'{device_id}:{camera.ip}:{rtsp_port}'
    now = time.time()
    with _capabilities_cache_lock:
        cached = _capabilities_cache.get(cache_key)
        if cached and now - cached[0] < _capabilities_cache_ttl:
            result = cached[1]
        else:
            result = probe_onvif_audio_backchannel_capabilities(
                camera_ip=camera.ip,
                camera_port=rtsp_port,
                username=camera.username or 'admin',
                password=camera.password or '',
            )
            _capabilities_cache[cache_key] = (now, result)

    capabilities = {
        'supported': bool(result.get('audio_backchannel_supported')),
        'audio_backchannel_supported': bool(result.get('audio_backchannel_supported')),
        'codecs': ['PCMU', 'PCMA'],
        'sample_rate': 8000,
        'channels': 1,
        'onvif_supported': ONVIF_AUDIO_AVAILABLE,
        'audio_tracks': result.get('audio_tracks', []),
    }
    return jsonify({'code': 0, 'msg': 'ok', 'data': {'success': True, 'capabilities': capabilities}})


@audio_talk_bp.route('/start', methods=['POST'])
def start_audio_talk():
    if not AUDIO_TALK_AVAILABLE or not _audio_talk_manager:
        return jsonify({'code': 500, 'msg': 'ONVIF 语音对讲服务未安装'}), 500

    data = request.get_json() or {}
    device_id = data.get('device_id') or data.get('camera_id')
    if not device_id:
        return jsonify({'code': 400, 'msg': '缺少设备 ID'}), 400

    camera = _resolve_camera(device_id)
    if not camera:
        return jsonify({'code': 404, 'msg': '设备不存在'}), 404

    session_id = f'audio_talk_{device_id}_{uuid.uuid4().hex[:8]}'
    rtsp_port = camera.port or 554
    audio_codec = data.get('audio_codec', 'PCMU')
    sample_rate = int(data.get('sample_rate', 8000))
    volume_gain = float(data.get('volume_gain', 1.0))
    noise_suppression = bool(data.get('noise_suppression', True))
    echo_cancellation = bool(data.get('echo_cancellation', True))

    _audio_talk_manager.create_session(
        session_id=session_id,
        camera_id=device_id,
        camera_ip=camera.ip,
        camera_rtsp_port=rtsp_port,
        username=camera.username or 'admin',
        password=camera.password or '',
        audio_codec=audio_codec,
        sample_rate=sample_rate,
        volume_gain=volume_gain,
        noise_suppression=noise_suppression,
        echo_cancellation=echo_cancellation,
    )

    if not _audio_talk_manager.start_session(session_id):
        return jsonify({
            'code': 500,
            'msg': 'Audio Back Channel 建立失败，设备可能不支持',
            'data': {'success': False},
        }), 500

    return jsonify({
        'code': 0,
        'msg': 'ONVIF 语音对讲已启动',
        'data': {
            'success': True,
            'session_id': session_id,
            'device_id': device_id,
            'camera_ip': camera.ip,
            'audio_codec': audio_codec,
            'sample_rate': sample_rate,
            'volume_gain': volume_gain,
            'noise_suppression': noise_suppression,
            'echo_cancellation': echo_cancellation,
        },
    })


@audio_talk_bp.route('/stop', methods=['POST'])
def stop_audio_talk():
    if not _audio_talk_manager:
        return jsonify({'code': 500, 'msg': '服务未初始化'}), 500

    data = request.get_json() or {}
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({'code': 400, 'msg': '缺少 session_id'}), 400

    _audio_talk_manager.stop_session(session_id)
    return jsonify({'code': 0, 'msg': '已停止', 'data': {'success': True, 'session_id': session_id}})


@audio_talk_bp.route('/send', methods=['POST'])
def send_audio_data():
    if not _audio_talk_manager:
        return jsonify({'code': 500, 'msg': '服务未初始化'}), 500

    data = request.get_json() or {}
    session_id = data.get('session_id')
    audio_b64 = data.get('audio_data')
    if not session_id or not audio_b64:
        return jsonify({'code': 400, 'msg': '缺少 session_id 或 audio_data'}), 400

    pcm_data = base64.b64decode(audio_b64)
    ok = _audio_talk_manager.send_audio_to_session(session_id, pcm_data)
    if not ok:
        return jsonify({'code': 500, 'msg': '发送失败', 'data': {'success': False}}), 500
    return jsonify({'code': 0, 'msg': 'ok', 'data': {'success': True}})


@audio_talk_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'code': 0,
        'data': {
            'status': 'ok',
            'onvif_available': ONVIF_AUDIO_AVAILABLE,
            'audio_talk_available': AUDIO_TALK_AVAILABLE,
        },
    })
