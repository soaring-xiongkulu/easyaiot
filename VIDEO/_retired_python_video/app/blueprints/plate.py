"""车牌库管理与识别路由"""
import logging
import subprocess

import cv2
import numpy as np
from flask import Blueprint, jsonify, request

from app.services import plate_auto_enroll_service, plate_library_service
from app.utils.plate_model_download import get_plate_model_status, start_plate_model_download
from models import Device

plate_bp = Blueprint('plate', __name__)
logger = logging.getLogger(__name__)


def _read_upload_bytes() -> bytes:
    if 'file' not in request.files:
        raise ValueError('请上传文件字段 file')
    file_obj = request.files['file']
    if file_obj is None or file_obj.filename is None or not file_obj.filename.strip():
        raise ValueError('上传文件不能为空')
    return file_obj.read()


def _capture_frame_from_source(source: str) -> np.ndarray:
    source = (source or '').strip()
    if not source:
        raise ValueError('设备视频源为空')

    if source.lower().startswith('rtmp://'):
        ffmpeg_cmd = [
            'ffmpeg', '-i', source, '-vframes', '1', '-f', 'image2',
            '-vcodec', 'mjpeg', '-q:v', '2', 'pipe:1',
        ]
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=10)
        if process.returncode != 0 or not stdout:
            error_msg = stderr.decode('utf-8', errors='ignore') if stderr else '未知错误'
            raise RuntimeError(f'RTMP 抓帧失败: {error_msg}')
        frame = cv2.imdecode(np.frombuffer(stdout, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise RuntimeError('RTMP 图像解码失败')
        return frame

    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError('RTSP 抓帧失败')
    return frame


@plate_bp.route('/health', methods=['GET'])
def plate_health():
    try:
        model_status = get_plate_model_status()
        return jsonify({'code': 0, 'msg': 'success', 'data': model_status})
    except Exception as e:
        logger.error('车牌服务健康检查失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'车牌服务初始化失败: {str(e)}'}), 500


@plate_bp.route('/model/status', methods=['GET'])
def plate_model_status():
    try:
        return jsonify({'code': 0, 'msg': 'success', 'data': get_plate_model_status()})
    except Exception as e:
        logger.error('查询车牌模型状态失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@plate_bp.route('/model/download', methods=['POST'])
def plate_model_download():
    try:
        data = start_plate_model_download()
        return jsonify({'code': 0, 'msg': data.pop('message', 'success'), 'data': data})
    except Exception as e:
        logger.error('下载车牌模型失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'下载失败: {str(e)}'}), 500


# ====================== 车牌库管理 ======================

@plate_bp.route('/libraries', methods=['GET'])
def list_plate_libraries():
    try:
        search = request.args.get('search', '').strip() or None
        is_enabled_raw = request.args.get('is_enabled')
        is_enabled = None
        if is_enabled_raw is not None and is_enabled_raw != '':
            is_enabled = str(is_enabled_raw).lower() in {'1', 'true', 'yes'}
        data = plate_library_service.list_libraries(search=search, is_enabled=is_enabled)
        return jsonify({'code': 0, 'msg': 'success', 'data': data, 'total': len(data)})
    except Exception as e:
        logger.error('查询车牌库列表失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>', methods=['GET'])
def get_plate_library(library_id: int):
    try:
        include_entries = str(request.args.get('include_entries', 'false')).lower() in {'1', 'true', 'yes'}
        data = plate_library_service.get_library(library_id, include_entries=include_entries)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as e:
        logger.error('查询车牌库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@plate_bp.route('/libraries', methods=['POST'])
def create_plate_library():
    try:
        data = request.get_json(silent=True) or {}
        library = plate_library_service.create_library(
            name=data.get('name'),
            business_tags=data.get('business_tags'),
            description=data.get('description'),
            is_enabled=data.get('is_enabled', True),
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': library.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('创建车牌库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'创建失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>', methods=['PUT'])
def update_plate_library(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        library = plate_library_service.update_library(library_id, **data)
        return jsonify({'code': 0, 'msg': 'success', 'data': library.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('更新车牌库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'更新失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>', methods=['DELETE'])
def delete_plate_library(library_id: int):
    try:
        plate_library_service.delete_library(library_id)
        return jsonify({'code': 0, 'msg': 'success'})
    except Exception as e:
        logger.error('删除车牌库失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>/entries', methods=['GET'])
def list_plate_entries(library_id: int):
    try:
        search = request.args.get('search', '').strip() or None
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        data = plate_library_service.list_entries(library_id, search=search, page=page, page_size=page_size)
        return jsonify({'code': 0, 'msg': 'success', **data})
    except Exception as e:
        logger.error('查询车牌条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>/entries', methods=['POST'])
def add_plate_entry(library_id: int):
    try:
        plate_no = request.form.get('plate_no') or (request.get_json(silent=True) or {}).get('plate_no')
        image_bytes = _read_upload_bytes() if 'file' in request.files else None
        data = request.form if request.form else (request.get_json(silent=True) or {})
        entry = plate_library_service.add_entry(
            library_id=library_id,
            plate_no=plate_no,
            plate_color=data.get('plate_color'),
            owner_name=data.get('owner_name'),
            owner_phone=data.get('owner_phone'),
            remark=data.get('remark'),
            image_bytes=image_bytes,
            is_enabled=str(data.get('is_enabled', 'true')).lower() in {'1', 'true', 'yes'},
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': entry.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('添加车牌条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'添加失败: {str(e)}'}), 500


@plate_bp.route('/entries/<int:entry_id>', methods=['PUT'])
def update_plate_entry(entry_id: int):
    try:
        image_bytes = _read_upload_bytes() if 'file' in request.files else None
        data = request.form if request.form else (request.get_json(silent=True) or {})
        kwargs = dict(data)
        if image_bytes:
            kwargs['image_bytes'] = image_bytes
        entry = plate_library_service.update_entry(entry_id, **kwargs)
        return jsonify({'code': 0, 'msg': 'success', 'data': entry.to_dict()})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('更新车牌条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'更新失败: {str(e)}'}), 500


@plate_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
def delete_plate_entry(entry_id: int):
    try:
        plate_library_service.delete_entry(entry_id)
        return jsonify({'code': 0, 'msg': 'success'})
    except Exception as e:
        logger.error('删除车牌条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'}), 500


@plate_bp.route('/entries/batch-delete', methods=['POST'])
def batch_delete_plate_entries():
    try:
        data = request.get_json(silent=True) or {}
        entry_ids = data.get('entry_ids') or []
        count = plate_library_service.batch_delete_entries(entry_ids)
        return jsonify({'code': 0, 'msg': 'success', 'data': {'deleted': count}})
    except Exception as e:
        logger.error('批量删除车牌条目失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'删除失败: {str(e)}'}), 500


# ====================== 车牌归一化 ======================

@plate_bp.route('/libraries/<int:library_id>/normalize/preview', methods=['GET'])
def preview_plate_normalize(library_id: int):
    try:
        threshold_raw = request.args.get('threshold')
        threshold = float(threshold_raw) if threshold_raw not in (None, '') else 1.0
        groups = plate_library_service.preview_normalize_groups(library_id, threshold=threshold)
        return jsonify({'code': 0, 'msg': 'success', 'data': groups, 'total': len(groups)})
    except Exception as e:
        logger.error('车牌归一化预览失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'预览失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>/normalize/merge', methods=['POST'])
def merge_plate_normalize(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        target_entry_id = data.get('target_entry_id') or data.get('targetEntryId')
        source_entry_ids = data.get('source_entry_ids') or data.get('sourceEntryIds') or []
        if not target_entry_id:
            return jsonify({'code': 400, 'msg': 'target_entry_id 不能为空'}), 400
        result = plate_library_service.merge_plate_entries(
            int(target_entry_id),
            [int(x) for x in source_entry_ids],
        )
        return jsonify({'code': 0, 'msg': '合并成功', 'data': result})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('车牌归一化合并失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'合并失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>/normalize/merge-all', methods=['POST'])
def merge_all_plate_normalize(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        threshold_raw = data.get('threshold') or request.args.get('threshold')
        threshold = float(threshold_raw) if threshold_raw not in (None, '') else 1.0
        result = plate_library_service.merge_all_normalize_groups(library_id, threshold=threshold)
        msg = (
            f"已合并 {result.get('merged_groups', 0)} 组、"
            f"{result.get('merged_entries', 0)} 条重复车牌"
        )
        return jsonify({'code': 0, 'msg': msg, 'data': result})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('车牌批量归一化失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'批量合并失败: {str(e)}'}), 500


# ====================== 自动录入 ======================

@plate_bp.route('/libraries/<int:library_id>/auto-enroll', methods=['GET'])
def get_plate_auto_enroll(library_id: int):
    try:
        data = plate_auto_enroll_service.get_auto_enroll_task(library_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except Exception as e:
        logger.error('查询车牌自动录入配置失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>/auto-enroll', methods=['PUT'])
def save_plate_auto_enroll(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        result = plate_auto_enroll_service.save_auto_enroll_config(
            library_id=library_id,
            device_ids=data.get('device_ids') or [],
            duration_minutes=data.get('duration_minutes', 60),
            capture_interval_sec=data.get('capture_interval_sec', 5),
        )
        return jsonify({'code': 0, 'msg': 'success', 'data': result})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('保存车牌自动录入配置失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'保存失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>/auto-enroll/start', methods=['POST'])
def start_plate_auto_enroll(library_id: int):
    try:
        data = plate_auto_enroll_service.start_auto_enroll(library_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('启动车牌自动录入失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'启动失败: {str(e)}'}), 500


@plate_bp.route('/libraries/<int:library_id>/auto-enroll/stop', methods=['POST'])
def stop_plate_auto_enroll(library_id: int):
    try:
        data = plate_auto_enroll_service.stop_auto_enroll(library_id)
        return jsonify({'code': 0, 'msg': 'success', 'data': data})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('停止车牌自动录入失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'停止失败: {str(e)}'}), 500


# ====================== 匹配 / Kafka ======================

@plate_bp.route('/libraries/<int:library_id>/match', methods=['POST'])
def match_plate_in_library(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        plate_no = data.get('plate_no') or data.get('plateNo')
        if not plate_no and 'file' in request.files:
            image_bytes = _read_upload_bytes()
            plates = plate_library_service.recognize_plates_in_image(image_bytes)
            if not plates:
                return jsonify({'code': 0, 'msg': 'success', 'data': {'matched': False, 'plates': []}})
            plate_no = plates[0].get('plate_no')
        result = plate_library_service.match_plate_in_library(library_id, plate_no or '')
        return jsonify({'code': 0, 'msg': 'success', 'data': result})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('车牌匹配失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'匹配失败: {str(e)}'}), 500


@plate_bp.route('/matching/publish', methods=['POST'])
def publish_plate_matching():
    try:
        from app.services.plate_matching_kafka_service import build_plate_matching_message, send_plate_matching_to_kafka
        data = request.get_json(silent=True) or {}
        task_id = data.get('taskId') or data.get('task_id')
        plate_no = data.get('plateNo') or data.get('plate_no')
        if not task_id:
            return jsonify({'code': 400, 'msg': 'taskId 不能为空'}), 400
        if not plate_no:
            return jsonify({'code': 400, 'msg': 'plateNo 不能为空'}), 400
        library_id = data.get('libraryId') or data.get('library_id')
        message = build_plate_matching_message(
            task_id=int(task_id),
            task_name=data.get('taskName') or data.get('task_name'),
            task_type=data.get('taskType') or data.get('task_type'),
            device_id=data.get('deviceId') or data.get('device_id'),
            device_name=data.get('deviceName') or data.get('device_name'),
            library_id=int(library_id) if library_id is not None else None,
            library_name=data.get('libraryName') or data.get('library_name'),
            plate_no=data.get('plateNo') or data.get('plate_no'),
            plate_color=data.get('plateColor') or data.get('plate_color'),
            plate_image_path=data.get('plateImagePath') or data.get('plate_image_path'),
            detect_conf=data.get('detectConf') or data.get('detect_conf'),
            alert_id=data.get('alertId') or data.get('alert_id'),
            correlation_id=data.get('correlationId') or data.get('correlation_id'),
            rect=data.get('rect'),
            landmarks=data.get('landmarks'),
        )
        ok = send_plate_matching_to_kafka(message)
        return jsonify({'code': 0, 'msg': 'success' if ok else 'Kafka不可用，消息未发送', 'data': {'sent': ok}})
    except Exception as e:
        logger.error('车牌匹配消息发布失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'发布失败: {str(e)}'}), 500


@plate_bp.route('/matching/process', methods=['POST'])
def process_plate_matching():
    """Kafka消费端 / iot-sink 调用的异步匹配处理接口"""
    try:
        payload = request.get_json(silent=True) or {}
        record = plate_library_service.process_plate_matching_message(payload)
        return jsonify({'code': 0, 'msg': 'success', 'data': record.to_dict()})
    except Exception as e:
        logger.error('车牌匹配消息处理失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'处理失败: {str(e)}'}), 500


@plate_bp.route('/matching/records', methods=['GET'])
def list_plate_match_records():
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        library_id = request.args.get('library_id')
        device_id = request.args.get('device_id')
        matched_raw = request.args.get('matched')
        correlation_id = request.args.get('correlation_id') or request.args.get('correlationId')
        matched = None
        if matched_raw is not None and matched_raw != '':
            matched = str(matched_raw).lower() in {'1', 'true', 'yes'}
        data = plate_library_service.list_match_records(
            page=page,
            page_size=page_size,
            library_id=int(library_id) if library_id else None,
            device_id=device_id,
            matched=matched,
            correlation_id=correlation_id,
        )
        return jsonify({'code': 0, 'msg': 'success', **data})
    except Exception as e:
        logger.error('查询车牌匹配记录失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'查询失败: {str(e)}'}), 500


@plate_bp.route('/recognize/image', methods=['POST'])
def recognize_plate_image():
    try:
        image_bytes = _read_upload_bytes()
        results = plate_library_service.recognize_plates_in_image(image_bytes)
        return jsonify({'code': 0, 'msg': 'success', 'data': results})
    except ValueError as e:
        return jsonify({'code': 400, 'msg': str(e)}), 400
    except Exception as e:
        logger.error('车牌识别失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'识别失败: {str(e)}'}), 500


@plate_bp.route('/recognize/device/<device_id>/snapshot', methods=['POST'])
def recognize_plate_device_snapshot(device_id: str):
    try:
        device = Device.query.get_or_404(device_id)
        frame = _capture_frame_from_source(device.source)
        _, encoded = cv2.imencode('.jpg', frame)
        results = plate_library_service.recognize_plates_in_image(encoded.tobytes())
        return jsonify({'code': 0, 'msg': 'success', 'data': results})
    except Exception as e:
        logger.error('设备抓帧车牌识别失败: %s', e, exc_info=True)
        return jsonify({'code': 500, 'msg': f'识别失败: {str(e)}'}), 500
