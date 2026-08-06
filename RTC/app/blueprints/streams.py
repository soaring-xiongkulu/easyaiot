"""流管理 API。"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.platform_registry import build_stream_url
from app.services.stream_service import StreamService

streams_bp = Blueprint("streams", __name__, url_prefix="/api/streams")


def _svc() -> StreamService:
    return StreamService()


@streams_bp.route("", methods=["GET"])
def list_streams():
    try:
        return jsonify(_svc().list_streams())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@streams_bp.route("", methods=["POST"])
def create_stream():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error": "缺少 name 字段"}), 400

    platform_id = body.get("platform")
    params = body.get("params") or {}
    source = body.get("source")
    update = bool(body.get("update"))

    try:
        if platform_id:
            result = _svc().register_platform_stream(name, platform_id, params, update=update)
        elif source:
            result = _svc().register_raw_stream(name, source, update=update)
        else:
            return jsonify({"error": "需提供 platform+params 或 source"}), 400
        return jsonify(result), 201 if not update else 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@streams_bp.route("/<name>", methods=["DELETE"])
def delete_stream(name: str):
    try:
        _svc().delete_stream(name)
        return jsonify({"deleted": name})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@streams_bp.route("/<name>/play", methods=["GET"])
def play_urls(name: str):
    try:
        return jsonify({"name": name, "play_urls": _svc().get_play_urls(name)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@streams_bp.route("/build-url", methods=["POST"])
def build_url():
    """预览平台流 URL（不注册到 go2rtc）。"""
    body = request.get_json(silent=True) or {}
    platform_id = body.get("platform")
    params = body.get("params") or {}
    if not platform_id:
        return jsonify({"error": "缺少 platform 字段"}), 400
    try:
        url = build_stream_url(platform_id, params)
        return jsonify({"platform": platform_id, "source": url})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
