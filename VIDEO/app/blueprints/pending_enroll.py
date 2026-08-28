"""待入库工作台路由：未匹配人脸/车牌目标的批量管理与确认入库。

人脸线与车牌线是两条独立业务线，路由同构：
  /video/face/pending-enroll/...   人脸（特征向量入库）
  /video/plate/pending-enroll/...  车牌（车牌号入库）
"""

from flask import Blueprint, Response, current_app, jsonify, request

from app.services import pending_enroll_service


def create_pending_enroll_blueprint(kind: str) -> Blueprint:
    bp = Blueprint(f"pending_enroll_{kind}", __name__)

    def _error(msg: str, code: int = 400):
        return jsonify({"code": code, "msg": msg}), code

    @bp.route("/records", methods=["GET"])
    def list_pending_records():
        try:
            page = int(request.args.get("page", 1))
            page_size = int(request.args.get("pageSize", request.args.get("page_size", 24)))
            data = pending_enroll_service.list_records(
                kind,
                status=request.args.get("status", "pending") or "pending",
                page=page,
                page_size=page_size,
                search=request.args.get("search", "").strip() or None,
                device_id=request.args.get("device_id", "").strip() or None,
                task_id=int(request.args["task_id"]) if request.args.get("task_id") else None,
            )
            return jsonify({"code": 0, "msg": "success", **data})
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"查询待入库记录失败: {exc}", exc_info=True)
            return _error(f"查询失败: {exc}", 500)

    @bp.route("/stats", methods=["GET"])
    def pending_stats():
        try:
            return jsonify({"code": 0, "msg": "success", "data": pending_enroll_service.get_stats(kind)})
        except Exception as exc:
            current_app.logger.error(f"查询待入库统计失败: {exc}", exc_info=True)
            return _error(f"查询失败: {exc}", 500)

    @bp.route("/records/<int:record_id>", methods=["GET"])
    def get_pending_record(record_id: int):
        try:
            data = pending_enroll_service.get_record_detail(kind, record_id)
            return jsonify({"code": 0, "msg": "success", "data": data})
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"查询待入库记录详情失败: {exc}", exc_info=True)
            return _error(f"查询失败: {exc}", 500)

    @bp.route("/records/batch-discard", methods=["POST"])
    def batch_discard_records():
        try:
            data = request.get_json(silent=True) or {}
            ids = data.get("ids") or data.get("record_ids") or []
            if not isinstance(ids, list) or not ids:
                return _error("ids 不能为空")
            changed = pending_enroll_service.discard_records(kind, [int(x) for x in ids])
            return jsonify({"code": 0, "msg": f"已忽略 {changed} 条", "data": {"changed": changed}})
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"批量忽略失败: {exc}", exc_info=True)
            return _error(f"操作失败: {exc}", 500)

    @bp.route("/records/batch-restore", methods=["POST"])
    def batch_restore_records():
        try:
            data = request.get_json(silent=True) or {}
            ids = data.get("ids") or data.get("record_ids") or []
            if not isinstance(ids, list) or not ids:
                return _error("ids 不能为空")
            changed = pending_enroll_service.restore_records(kind, [int(x) for x in ids])
            return jsonify({"code": 0, "msg": f"已恢复 {changed} 条", "data": {"changed": changed}})
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"批量恢复失败: {exc}", exc_info=True)
            return _error(f"操作失败: {exc}", 500)

    @bp.route("/records/batch-delete", methods=["POST"])
    def batch_delete_records():
        try:
            data = request.get_json(silent=True) or {}
            ids = data.get("ids") or data.get("record_ids") or []
            if not isinstance(ids, list) or not ids:
                return _error("ids 不能为空")
            deleted = pending_enroll_service.delete_records(kind, [int(x) for x in ids])
            return jsonify({"code": 0, "msg": f"已删除 {deleted} 条", "data": {"deleted": deleted}})
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"批量删除失败: {exc}", exc_info=True)
            return _error(f"操作失败: {exc}", 500)

    @bp.route("/records/<int:record_id>/extract-preview", methods=["POST"])
    def extract_preview(record_id: int):
        """按（修正后的）标注框返回提取区域 JPEG 预览"""
        try:
            data = request.get_json(silent=True) or {}
            crop_bytes, info = pending_enroll_service.extract_preview_bytes(
                kind, record_id, bbox=data.get("bbox"),
            )
            return Response(crop_bytes, mimetype="image/jpeg", headers={
                "X-Extract-Source": info.get("source", ""),
            })
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"提取预览失败: {exc}", exc_info=True)
            return _error(f"提取失败: {exc}", 500)

    @bp.route("/records/<int:record_id>/enroll", methods=["POST"])
    def enroll_record(record_id: int):
        try:
            payload = request.get_json(silent=True) or {}
            result = pending_enroll_service.enroll_record(kind, record_id, payload)
            msg = (
                f"已录入 {result['entry'].get('person_name', '')}"
                if kind == "face"
                else f"已录入车牌 {result['entry'].get('plate_no', '')}"
            )
            return jsonify({"code": 0, "msg": msg, "data": result})
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"待入库记录入库失败: {exc}", exc_info=True)
            return _error(f"入库失败: {exc}", 500)

    @bp.route("/records/batch-enroll", methods=["POST"])
    def batch_enroll_records():
        try:
            data = request.get_json(silent=True) or {}
            items = data.get("items") or []
            if not isinstance(items, list) or not items:
                return _error("items 不能为空")
            result = pending_enroll_service.batch_enroll_records(kind, items)
            msg = f"成功入库 {result['success_count']} 条"
            if result["failed_count"]:
                msg += f"，{result['failed_count']} 条失败"
            return jsonify({"code": 0, "msg": msg, "data": result})
        except ValueError as exc:
            return _error(str(exc))
        except Exception as exc:
            current_app.logger.error(f"批量入库失败: {exc}", exc_info=True)
            return _error(f"批量入库失败: {exc}", 500)

    return bp


pending_enroll_face_bp = create_pending_enroll_blueprint(pending_enroll_service.KIND_FACE)
pending_enroll_plate_bp = create_pending_enroll_blueprint(pending_enroll_service.KIND_PLATE)
