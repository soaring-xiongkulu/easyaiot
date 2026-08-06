"""平台能力 API。"""

from flask import Blueprint, jsonify

from app.services.platform_registry import get_platform, list_platforms

platforms_bp = Blueprint("platforms", __name__, url_prefix="/api/platforms")


@platforms_bp.route("", methods=["GET"])
def get_platforms():
    return jsonify({"platforms": list_platforms()})


@platforms_bp.route("/<platform_id>", methods=["GET"])
def get_platform_detail(platform_id: str):
    platform = get_platform(platform_id)
    if not platform:
        return jsonify({"error": f"平台不存在: {platform_id}"}), 404
    return jsonify(platform.to_dict())
