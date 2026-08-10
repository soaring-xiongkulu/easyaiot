"""
人脸管理与识别路由
"""
import logging
import subprocess
from datetime import datetime

import cv2
import numpy as np
from flask import Blueprint, jsonify, request

from app.services.face_recognition_service import decode_image_bytes, get_face_recognition_service
from app.services.face_vector_store import get_face_vector_store
from app.services import face_library_service
from app.services import face_auto_enroll_service
from app.utils.face_model_download import get_face_rec_model_status, start_face_rec_model_download
from models import Device

face_bp = Blueprint("face", __name__)
logger = logging.getLogger(__name__)


def _read_upload_image() -> np.ndarray:
    if "file" not in request.files:
        raise ValueError("请上传文件字段 file")
    file_obj = request.files["file"]
    if file_obj is None or file_obj.filename is None or not file_obj.filename.strip():
        raise ValueError("上传文件不能为空")
    return decode_image_bytes(file_obj.read())


def _read_upload_bytes() -> bytes:
    if "file" not in request.files:
        raise ValueError("请上传文件字段 file")
    file_obj = request.files["file"]
    if file_obj is None or file_obj.filename is None or not file_obj.filename.strip():
        raise ValueError("上传文件不能为空")
    return file_obj.read()


def _capture_frame_from_source(source: str) -> np.ndarray:
    source = (source or "").strip()
    if not source:
        raise ValueError("设备视频源为空")

    if source.lower().startswith("rtmp://"):
        ffmpeg_cmd = [
            "ffmpeg",
            "-i",
            source,
            "-vframes",
            "1",
            "-f",
            "image2",
            "-vcodec",
            "mjpeg",
            "-q:v",
            "2",
            "pipe:1",
        ]
        try:
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=10)
            if process.returncode != 0 or not stdout:
                error_msg = stderr.decode("utf-8", errors="ignore") if stderr else "未知错误"
                raise RuntimeError(f"RTMP 抓帧失败: {error_msg}")
            frame = cv2.imdecode(np.frombuffer(stdout, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise RuntimeError("RTMP 图像解码失败")
            return frame
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("RTMP 抓帧超时") from exc

    cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError("RTSP 抓帧失败")
    return frame


@face_bp.route("/health", methods=["GET"])
def face_health():
    try:
        data = get_face_vector_store().ping()
        model_status = get_face_rec_model_status()
        data["recognition_model_loaded"] = bool(model_status.get("exists"))
        data["recognition_model_downloading"] = bool(model_status.get("downloading"))
        return jsonify({"code": 0, "msg": "success", "data": data})
    except Exception as e:
        logger.error(f"人脸服务健康检查失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"人脸向量库初始化失败: {str(e)}"}), 500


@face_bp.route("/model/status", methods=["GET"])
def face_rec_model_status():
    try:
        return jsonify({"code": 0, "msg": "success", "data": get_face_rec_model_status()})
    except Exception as e:
        logger.error(f"查询人脸特征模型状态失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/model/download", methods=["POST"])
def face_rec_model_download():
    try:
        data = start_face_rec_model_download()
        return jsonify({"code": 0, "msg": data.pop("message", "success"), "data": data})
    except Exception as e:
        logger.error(f"下载人脸特征模型失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"下载失败: {str(e)}"}), 500


# ====================== 人脸库管理 ======================

@face_bp.route("/libraries", methods=["GET"])
def list_face_libraries():
    try:
        search = request.args.get("search", "").strip() or None
        is_enabled_raw = request.args.get("is_enabled")
        is_enabled = None
        if is_enabled_raw is not None and is_enabled_raw != "":
            is_enabled = str(is_enabled_raw).lower() in {"1", "true", "yes"}
        data = face_library_service.list_libraries(search=search, is_enabled=is_enabled)
        return jsonify({"code": 0, "msg": "success", "data": data, "total": len(data)})
    except Exception as e:
        logger.error(f"查询人脸库列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>", methods=["GET"])
def get_face_library(library_id: int):
    try:
        include_entries = str(request.args.get("include_entries", "false")).lower() in {"1", "true", "yes"}
        data = face_library_service.get_library(library_id, include_entries=include_entries)
        return jsonify({"code": 0, "msg": "success", "data": data})
    except Exception as e:
        logger.error(f"查询人脸库失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/libraries", methods=["POST"])
def create_face_library():
    try:
        data = request.get_json(silent=True) or {}
        library = face_library_service.create_library(
            name=data.get("name"),
            business_tags=data.get("business_tags"),
            description=data.get("description"),
            similarity_threshold=data.get("similarity_threshold", 0.55),
            is_enabled=data.get("is_enabled", True),
        )
        return jsonify({"code": 0, "msg": "创建成功", "data": library.to_dict()})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"创建人脸库失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"创建失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>", methods=["PUT"])
def update_face_library(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        library = face_library_service.update_library(library_id, **data)
        return jsonify({"code": 0, "msg": "更新成功", "data": library.to_dict()})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"更新人脸库失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"更新失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>", methods=["DELETE"])
def delete_face_library(library_id: int):
    try:
        face_library_service.delete_library(library_id)
        return jsonify({"code": 0, "msg": "删除成功"})
    except Exception as e:
        logger.error(f"删除人脸库失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"删除失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/entries", methods=["GET"])
def list_face_entries(library_id: int):
    try:
        search = request.args.get("search", "").strip() or None
        data = face_library_service.list_entries(library_id, search=search)
        return jsonify({"code": 0, "msg": "success", "data": data, "total": len(data)})
    except Exception as e:
        logger.error(f"查询人脸条目失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/persons", methods=["GET"])
def list_face_persons(library_id: int):
    try:
        search = request.args.get("search", "").strip() or None
        page = int(request.args.get("page", request.args.get("pageNo", 1)))
        page_size = int(request.args.get("pageSize", request.args.get("page_size", 18)))
        data = face_library_service.list_persons(
            library_id, search=search, page=page, page_size=page_size,
        )
        return jsonify({"code": 0, "msg": "success", **data})
    except Exception as e:
        logger.error(f"查询归一化人员列表失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/persons/<int:person_id>", methods=["GET"])
def get_face_person(person_id: int):
    try:
        include_entries = str(request.args.get("include_entries", "true")).lower() in {"1", "true", "yes"}
        data = face_library_service.get_person(person_id, include_entries=include_entries)
        return jsonify({"code": 0, "msg": "success", "data": data})
    except Exception as e:
        logger.error(f"查询人员详情失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/persons/<int:person_id>", methods=["DELETE"])
def delete_face_person(person_id: int):
    try:
        face_library_service.delete_person(person_id)
        return jsonify({"code": 0, "msg": "删除成功"})
    except Exception as e:
        logger.error(f"删除人员失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"删除失败: {str(e)}"}), 500


@face_bp.route("/persons/batch-delete", methods=["POST"])
def batch_delete_face_persons():
    try:
        data = request.get_json(silent=True) or {}
        person_ids = data.get("person_ids") or data.get("personIds") or []
        if not isinstance(person_ids, list) or not person_ids:
            return jsonify({"code": 400, "msg": "person_ids 不能为空"}), 400
        deleted = face_library_service.batch_delete_persons([int(x) for x in person_ids])
        return jsonify({"code": 0, "msg": "删除成功", "data": {"deleted": deleted}})
    except Exception as e:
        logger.error(f"批量删除人员失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"删除失败: {str(e)}"}), 500


@face_bp.route("/persons/<int:person_id>/cover", methods=["PUT"])
def set_face_person_cover(person_id: int):
    try:
        data = request.get_json(silent=True) or {}
        entry_id = data.get("entry_id") or data.get("entryId")
        if not entry_id:
            return jsonify({"code": 400, "msg": "entry_id 不能为空"}), 400
        result = face_library_service.set_person_cover(person_id, int(entry_id))
        return jsonify({"code": 0, "msg": "封面设置成功", "data": result})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"设置人员封面失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"设置失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/entries", methods=["POST"])
def add_face_entry(library_id: int):
    try:
        person_name = (request.form.get("person_name") or request.form.get("name") or "").strip()
        person_code = (request.form.get("person_code") or "").strip() or None
        remark = (request.form.get("remark") or "").strip() or None
        is_enabled = str(request.form.get("is_enabled", "true")).lower() in {"1", "true", "yes"}
        person_id_raw = request.form.get("person_id")
        person_id = int(person_id_raw) if person_id_raw not in (None, "") else None
        image_bytes = _read_upload_bytes()
        entry = face_library_service.add_entry(
            library_id=library_id,
            person_name=person_name,
            image_bytes=image_bytes,
            person_code=person_code,
            remark=remark,
            person_id=person_id,
            is_enabled=is_enabled,
        )
        return jsonify({"code": 0, "msg": "录入成功", "data": entry.to_dict()})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"录入人脸失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"录入失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/entries/batch", methods=["POST"])
def add_face_entries_batch(library_id: int):
    """批量录入：同一人多张人脸照片"""
    try:
        person_name = (request.form.get("person_name") or request.form.get("name") or "").strip()
        person_code = (request.form.get("person_code") or "").strip() or None
        remark = (request.form.get("remark") or "").strip() or None
        is_enabled = str(request.form.get("is_enabled", "true")).lower() in {"1", "true", "yes"}
        person_id_raw = request.form.get("person_id")
        person_id = int(person_id_raw) if person_id_raw not in (None, "") else None

        files = request.files.getlist("files")
        if not files:
            single = request.files.get("file")
            files = [single] if single and single.filename else []

        image_files = []
        for f in files:
            if f and f.filename:
                image_files.append(f.read())

        result = face_library_service.add_entries_batch(
            library_id=library_id,
            person_name=person_name,
            image_files=image_files,
            person_code=person_code,
            remark=remark,
            person_id=person_id,
            is_enabled=is_enabled,
        )
        msg = f"成功录入 {result['success_count']} 张"
        if result.get("failed_count"):
            msg += f"，{result['failed_count']} 张失败"
        return jsonify({"code": 0, "msg": msg, "data": result})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"批量录入人脸失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"批量录入失败: {str(e)}"}), 500


@face_bp.route("/entries/<int:entry_id>", methods=["PUT"])
def update_face_entry(entry_id: int):
    try:
        image_bytes = None
        if "file" in request.files and request.files["file"].filename:
            image_bytes = _read_upload_bytes()
        data = {}
        if request.form.get("person_name") is not None:
            data["person_name"] = request.form.get("person_name")
        if request.form.get("person_code") is not None:
            data["person_code"] = request.form.get("person_code")
        if request.form.get("remark") is not None:
            data["remark"] = request.form.get("remark")
        if request.form.get("is_enabled") is not None:
            data["is_enabled"] = str(request.form.get("is_enabled")).lower() in {"1", "true", "yes"}
        entry = face_library_service.update_entry(entry_id, image_bytes=image_bytes, **data)
        return jsonify({"code": 0, "msg": "更新成功", "data": entry.to_dict()})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"更新人脸失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"更新失败: {str(e)}"}), 500


@face_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
def delete_face_entry(entry_id: int):
    try:
        face_library_service.delete_entry(entry_id)
        return jsonify({"code": 0, "msg": "删除成功"})
    except Exception as e:
        logger.error(f"删除人脸失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"删除失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/auto-enroll", methods=["GET"])
def get_face_auto_enroll(library_id: int):
    try:
        data = face_auto_enroll_service.get_auto_enroll_task(library_id)
        return jsonify({"code": 0, "msg": "success", "data": data})
    except Exception as e:
        logger.error(f"查询自动录入配置失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/auto-enroll", methods=["PUT"])
def save_face_auto_enroll(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        result = face_auto_enroll_service.save_auto_enroll_config(
            library_id=library_id,
            device_ids=data.get("device_ids") or data.get("deviceIds") or [],
            duration_minutes=data.get("duration_minutes") or data.get("durationMinutes") or 60,
            capture_interval_sec=data.get("capture_interval_sec") or data.get("captureIntervalSec") or 5,
            person_name_prefix=data.get("person_name_prefix") or data.get("personNamePrefix") or "摄像头自动录入",
        )
        return jsonify({"code": 0, "msg": "保存成功", "data": result})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"保存自动录入配置失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"保存失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/auto-enroll/start", methods=["POST"])
def start_face_auto_enroll(library_id: int):
    try:
        data = face_auto_enroll_service.start_auto_enroll(library_id)
        return jsonify({"code": 0, "msg": "摄像头自动录入已开启", "data": data})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"开启自动录入失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"开启失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/auto-enroll/stop", methods=["POST"])
def stop_face_auto_enroll(library_id: int):
    try:
        data = face_auto_enroll_service.stop_auto_enroll(library_id)
        return jsonify({"code": 0, "msg": "摄像头自动录入已关闭", "data": data})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"停止自动录入失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"停止失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/normalize/preview", methods=["GET"])
def preview_face_normalize(library_id: int):
    try:
        threshold_raw = request.args.get("threshold")
        threshold = float(threshold_raw) if threshold_raw not in (None, "") else 0.75
        groups = face_library_service.preview_normalize_groups(library_id, threshold=threshold)
        return jsonify({"code": 0, "msg": "success", "data": groups, "total": len(groups)})
    except Exception as e:
        logger.error(f"归一化预览失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"预览失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/normalize/merge", methods=["POST"])
def merge_face_normalize(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        target_person_id = data.get("target_person_id") or data.get("targetPersonId")
        source_person_ids = data.get("source_person_ids") or data.get("sourcePersonIds") or []
        target_entry_id = data.get("target_entry_id") or data.get("targetEntryId")
        source_entry_ids = data.get("source_entry_ids") or data.get("sourceEntryIds") or []

        if target_person_id:
            result = face_library_service.merge_persons(
                int(target_person_id),
                [int(x) for x in source_person_ids],
            )
        elif target_entry_id:
            result = face_library_service.merge_face_entries(int(target_entry_id), source_entry_ids)
        else:
            return jsonify({"code": 400, "msg": "target_person_id 或 target_entry_id 不能为空"}), 400
        return jsonify({"code": 0, "msg": "合并成功", "data": result})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"归一化合并失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"合并失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/normalize/merge-all", methods=["POST"])
def merge_all_face_normalize(library_id: int):
    try:
        data = request.get_json(silent=True) or {}
        threshold_raw = data.get("threshold") or request.args.get("threshold")
        threshold = float(threshold_raw) if threshold_raw not in (None, "") else 0.75
        result = face_library_service.merge_all_normalize_groups(library_id, threshold=threshold)
        msg = f"已合并 {result.get('merged_groups', 0)} 组、{result.get('merged_persons', 0)} 人"
        return jsonify({"code": 0, "msg": msg, "data": result})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"批量归一化合并失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"批量合并失败: {str(e)}"}), 500


@face_bp.route("/libraries/<int:library_id>/match", methods=["POST"])
def match_face_in_library(library_id: int):
    try:
        threshold = request.form.get("threshold")
        threshold = float(threshold) if threshold not in (None, "") else None
        top_k = int(request.form.get("top_k", 5))
        image_bytes = _read_upload_bytes()
        result = face_library_service.match_face_in_library(
            library_id=library_id,
            image_bytes=image_bytes,
            threshold=threshold,
            top_k=top_k,
        )
        return jsonify({"code": 0, "msg": "匹配完成", "data": result})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"人脸匹配失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"匹配失败: {str(e)}"}), 500


@face_bp.route("/matching/publish", methods=["POST"])
def publish_face_matching():
    """算法任务进程调用：将人脸匹配请求投递到 Kafka"""
    try:
        from app.services.face_matching_kafka_service import build_face_matching_message, send_face_matching_to_kafka

        data = request.get_json(silent=True) or {}
        task_id = data.get('taskId') or data.get('task_id')
        face_image_path = data.get('faceImagePath') or data.get('face_image_path')
        if not task_id:
            return jsonify({"code": 400, "msg": "taskId 不能为空"}), 400
        if not face_image_path:
            return jsonify({"code": 400, "msg": "faceImagePath 不能为空"}), 400
        library_id = data.get('libraryId') or data.get('library_id')
        message = build_face_matching_message(
            task_id=int(task_id),
            task_name=data.get('taskName') or data.get('task_name') or '',
            task_type=data.get('taskType') or data.get('task_type') or 'realtime',
            device_id=data.get('deviceId') or data.get('device_id') or '',
            device_name=data.get('deviceName') or data.get('device_name'),
            library_id=int(library_id) if library_id is not None else None,
            library_name=data.get('libraryName') or data.get('library_name'),
            face_image_path=face_image_path,
            threshold=data.get('threshold') or data.get('faceMatchingThreshold') or data.get('face_matching_threshold'),
            alert_id=data.get('alertId') or data.get('alert_id'),
            correlation_id=data.get('correlationId') or data.get('correlation_id'),
            source_event=data.get('sourceEvent') or data.get('source_event'),
            bbox=data.get('bbox'),
            confidence=data.get('confidence'),
        )
        ok = send_face_matching_to_kafka(message)
        if not ok:
            return jsonify({"code": 500, "msg": "Kafka 投递失败"}), 500
        return jsonify({"code": 0, "msg": "投递成功", "data": message})
    except Exception as e:
        logger.error(f"人脸匹配 Kafka 投递失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"投递失败: {str(e)}"}), 500


@face_bp.route("/matching/process", methods=["POST"])
def process_face_matching():
    """Kafka消费端 / iot-sink 调用的异步匹配处理接口"""
    try:
        payload = request.get_json(silent=True) or {}
        record = face_library_service.process_face_matching_message(payload)
        return jsonify({"code": 0, "msg": "处理成功", "data": record.to_dict()})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"异步人脸匹配处理失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"处理失败: {str(e)}"}), 500


@face_bp.route("/matching/records", methods=["GET"])
def list_face_match_records():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", request.args.get("page_size", 20)))
        library_id = request.args.get("library_id")
        device_id = request.args.get("device_id")
        matched_raw = request.args.get("matched")
        correlation_id = request.args.get("correlation_id") or request.args.get("correlationId")
        matched = None
        if matched_raw is not None and matched_raw != "":
            matched = str(matched_raw).lower() in {"1", "true", "yes"}
        data = face_library_service.list_match_records(
            page=page,
            page_size=page_size,
            library_id=int(library_id) if library_id else None,
            device_id=device_id,
            matched=matched,
            correlation_id=correlation_id,
        )
        return jsonify({"code": 0, "msg": "success", **data})
    except Exception as e:
        logger.error(f"查询匹配记录失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


# ====================== 兼容旧版单库 API ======================

@face_bp.route("/library", methods=["GET"])
def list_library():
    try:
        store = get_face_vector_store()
        label = request.args.get("label", "").strip() or None
        limit = int(request.args.get("limit", 1000))
        data = store.list_faces(label=label, limit=limit)
        return jsonify({"code": 0, "msg": "success", "data": data})
    except Exception as e:
        logger.error(f"查询人脸库失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"}), 500


@face_bp.route("/library", methods=["POST"])
def add_library():
    try:
        label = (request.form.get("label") or "").strip()
        if not label:
            return jsonify({"code": 400, "msg": "label 不能为空"}), 400
        image = _read_upload_image()
        service = get_face_recognition_service()
        result = service.add_face(label=label, image=image)
        return jsonify({"code": 0, "msg": "录入成功", "data": {"label": label, **result}})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"录入人脸失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"录入失败: {str(e)}"}), 500


@face_bp.route("/library/<string:label>", methods=["PUT"])
def update_library(label: str):
    try:
        label = label.strip()
        if not label:
            return jsonify({"code": 400, "msg": "label 不能为空"}), 400
        image = _read_upload_image()
        service = get_face_recognition_service()
        result = service.update_face(label=label, image=image)
        return jsonify({"code": 0, "msg": "更新成功", "data": {"label": label, **result}})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"更新人脸失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"更新失败: {str(e)}"}), 500


@face_bp.route("/library/<string:label>", methods=["DELETE"])
def delete_library(label: str):
    try:
        label = label.strip()
        if not label:
            return jsonify({"code": 400, "msg": "label 不能为空"}), 400
        deleted = get_face_vector_store().delete_face(label=label)
        return jsonify({"code": 0, "msg": "删除成功", "data": {"label": label, "deleted": deleted}})
    except Exception as e:
        logger.error(f"删除人脸失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"删除失败: {str(e)}"}), 500


@face_bp.route("/recognize/image", methods=["POST"])
def recognize_image():
    try:
        top_k = int(request.form.get("top_k", 3))
        library_id = request.form.get("library_id")
        threshold = request.form.get("threshold")
        image = _read_upload_image()
        service = get_face_recognition_service()
        result = service.recognize(
            image=image,
            top_k=top_k,
            library_id=int(library_id) if library_id else None,
            threshold=float(threshold) if threshold not in (None, "") else None,
        )
        return jsonify({"code": 0, "msg": "识别完成", "data": result})
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"图片识别失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"识别失败: {str(e)}"}), 500


@face_bp.route("/recognize/device/<string:device_id>/snapshot", methods=["POST"])
def recognize_device_snapshot(device_id: str):
    try:
        body = request.get_json(silent=True) or {}
        top_k = int(body.get("top_k", 3))
        library_id = body.get("library_id")
        threshold = body.get("threshold")
        device = Device.query.get(device_id)
        if not device:
            return jsonify({"code": 400, "msg": f"设备不存在: ID={device_id}"}), 400

        frame = _capture_frame_from_source(device.source)
        service = get_face_recognition_service()
        result = service.recognize(
            image=frame,
            top_k=top_k,
            library_id=int(library_id) if library_id else None,
            threshold=float(threshold) if threshold not in (None, "") else None,
        )
        return jsonify(
            {
                "code": 0,
                "msg": "识别完成",
                "data": {
                    "device_id": device_id,
                    "captured_at": datetime.utcnow().isoformat(),
                    **result,
                },
            }
        )
    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e)}), 400
    except Exception as e:
        logger.error(f"设备抓帧识别失败: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": f"识别失败: {str(e)}"}), 500
