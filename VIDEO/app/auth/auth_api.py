"""
VIDEO 认证 API。

1) VIDEO 原生 REST：/video/auth/login|logout|check|users
2) WEB 兼容（CommonResult）：/video/system/auth/* 、tenant/captcha 桩

云边一体单机合装（edge）下 nginx 将 /dev-api/system/auth 等到本蓝图。
"""

from __future__ import annotations

import logging
import os
from functools import wraps

from flask import Blueprint, jsonify, request

from app.auth.auth_manager import get_auth_manager
from app.auth.token_service import (
    create_token_pair,
    extract_bearer,
    refresh_access_token,
    revoke_token,
    verify_access_token,
)

logger = logging.getLogger(__name__)

auth_bp = Blueprint("video_auth", __name__)
system_auth_bp = Blueprint("video_system_auth", __name__)


def _ok(data=None, msg: str = "success"):
    return jsonify({"code": 0, "msg": msg, "data": data})


def _fail(msg: str, code: int = 400, http_status: int = 200):
    # WEB axios 约定业务 code；HTTP 仍常用 200
    return jsonify({"code": code, "msg": msg, "data": None}), http_status


def _edge_menus():
    """edge 单机合装菜单（监控大屏由前端静态 dashboard 路由提供）。"""
    return [
        {
            "id": 200,
            "parentId": 0,
            "name": "流媒体管理",
            "path": "/camera/index",
            "component": "camera/index",
            "componentName": "CAMERA",
            "icon": "ant-design:video-camera-outlined",
            "visible": True,
            "keepAlive": True,
            "alwaysShow": False,
            "sort": 20,
            "children": None,
        },
        {
            "id": 250,
            "parentId": 0,
            "name": "模型管理",
            "path": "/train/index",
            "component": "train/index",
            "componentName": "TRAIN",
            "icon": "hugeicons:ai-brain-03",
            "visible": True,
            "keepAlive": True,
            "alwaysShow": False,
            "sort": 25,
            "children": None,
        },
        {
            "id": 300,
            "parentId": 0,
            "name": "告警管理",
            "path": "/alert/index",
            "component": "alert/index",
            "componentName": "Alarm",
            "icon": "ant-design:alert-outlined",
            "visible": True,
            "keepAlive": True,
            "alwaysShow": False,
            "sort": 30,
            "children": None,
        },
    ]


def _permission_info_from_payload(payload: dict):
    manager = get_auth_manager()
    user = manager.get_user(int(payload["uid"]))
    if not user or user.enabled != 1:
        return None
    role = user.role or "user"
    perms = ["*:*:*"] if role == "admin" else ["video:view"]
    return {
        "user": {
            "id": user.id,
            "nickname": user.display_name or user.username,
            "avatar": "",
            "deptId": None,
        },
        "roles": [role],
        "permissions": perms,
        "menus": _edge_menus(),
    }


def login_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = verify_access_token(extract_bearer(request.headers))
        if not payload:
            return jsonify({"error": "未登录", "code": "UNAUTHORIZED"}), 401
        request.video_auth_user = payload  # type: ignore[attr-defined]
        return f(*args, **kwargs)

    return decorated


# ---------- VIDEO 原生 /video/auth/* ----------


@auth_bp.route("/login", methods=["POST"])
def native_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400
    user = get_auth_manager().authenticate(username, password)
    if not user:
        logger.warning("VIDEO 登录失败: username=%s", username)
        return jsonify({"error": "用户名或密码错误"}), 401
    tokens = create_token_pair(user.id, user.username, user.role)
    logger.info("VIDEO 用户登录成功: %s role=%s", user.username, user.role)
    return jsonify({"message": "登录成功", "user": user.to_dict(), **tokens}), 200


@auth_bp.route("/logout", methods=["POST"])
def native_logout():
    revoke_token(extract_bearer(request.headers), (request.get_json(silent=True) or {}).get("refreshToken", ""))
    return jsonify({"message": "登出成功"}), 200


@auth_bp.route("/check", methods=["GET"])
def native_check():
    payload = verify_access_token(extract_bearer(request.headers))
    if not payload:
        return jsonify({"logged_in": False}), 200
    user = get_auth_manager().get_user(int(payload["uid"]))
    if not user or user.enabled != 1:
        return jsonify({"logged_in": False}), 200
    return jsonify({"logged_in": True, "user": user.to_dict()}), 200


@auth_bp.route("/users", methods=["GET"])
@login_required_api
def list_users():
    payload = request.video_auth_user  # type: ignore[attr-defined]
    if payload.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    users = get_auth_manager().get_all_users()
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@auth_bp.route("/users", methods=["POST"])
@login_required_api
def create_user():
    payload = request.video_auth_user  # type: ignore[attr-defined]
    if payload.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    data = request.get_json(silent=True) or {}
    try:
        user = get_auth_manager().create_user(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required_api
def update_user(user_id: int):
    payload = request.video_auth_user  # type: ignore[attr-defined]
    if payload.get("role") != "admin" and int(payload.get("uid") or 0) != user_id:
        return jsonify({"error": "权限不足"}), 403
    data = request.get_json(silent=True) or {}
    if payload.get("role") != "admin":
        data.pop("role", None)
        data.pop("enabled", None)
    user = get_auth_manager().update_user(user_id, data)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@login_required_api
def delete_user(user_id: int):
    payload = request.video_auth_user  # type: ignore[attr-defined]
    if payload.get("role") != "admin":
        return jsonify({"error": "权限不足"}), 403
    try:
        ok = get_auth_manager().delete_user(user_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if not ok:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify({"message": "删除成功"}), 200


# ---------- WEB 兼容 /video/system/* ----------


@system_auth_bp.route("/auth/login", methods=["POST"])
def system_login():
    data = request.get_json(silent=True) or {}
    # 兼容 form / json；忽略 captchaVerification（edge 关闭或桩）
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return _fail("用户名和密码不能为空", code=400)
    user = get_auth_manager().authenticate(username, password)
    if not user:
        logger.warning("VIDEO(system) 登录失败: username=%s", username)
        return _fail("账号或密码不正确", code=401)
    tokens = create_token_pair(user.id, user.username, user.role)
    logger.info("VIDEO(system) 登录成功: %s", user.username)
    return _ok(tokens)


@system_auth_bp.route("/auth/logout", methods=["POST", "DELETE"])
def system_logout():
    data = request.get_json(silent=True) or {}
    revoke_token(extract_bearer(request.headers), data.get("refreshToken") or "")
    return _ok(True)


@system_auth_bp.route("/auth/refresh-token", methods=["POST"])
def system_refresh():
    refresh = request.args.get("refreshToken") or ""
    if not refresh:
        data = request.get_json(silent=True) or {}
        refresh = data.get("refreshToken") or ""
    tokens = refresh_access_token(refresh)
    if not tokens:
        return _fail("刷新令牌已失效", code=401)
    return _ok(tokens)


@system_auth_bp.route("/auth/get-permission-info", methods=["GET"])
def system_permission_info():
    payload = verify_access_token(extract_bearer(request.headers))
    if not payload:
        return _fail("账号未登录", code=401)
    info = _permission_info_from_payload(payload)
    if not info:
        return _fail("账号未登录", code=401)
    return _ok(info)


@system_auth_bp.route("/user/profile/update-password", methods=["PUT"])
def system_update_password():
    payload = verify_access_token(extract_bearer(request.headers))
    if not payload:
        return _fail("账号未登录", code=401)
    data = request.get_json(silent=True) or {}
    old_password = data.get("oldPassword") or ""
    new_password = data.get("newPassword") or ""
    if not old_password or not new_password:
        return _fail("请填写当前密码与新密码", code=400)
    try:
        get_auth_manager().change_password(int(payload["uid"]), old_password, new_password)
    except ValueError as exc:
        return _fail(str(exc), code=400)
    logger.info("VIDEO(system) 用户 %s 修改密码成功", payload.get("username"))
    return _ok(True)


@system_auth_bp.route("/tenant/get-id-by-name", methods=["GET"])
def tenant_id_by_name():
    # edge 单租户桩：固定 1
    return _ok(1)


@system_auth_bp.route("/tenant/get-by-website", methods=["GET"])
def tenant_by_website():
    return _ok({"id": 1, "name": "Admin-IoT"})


@system_auth_bp.route("/captcha/get", methods=["POST"])
def captcha_get():
    return jsonify(
        {
            "repCode": "0000",
            "repMsg": None,
            "repData": {
                "captchaId": "edge-bypass",
                "projectCode": "easyaiot",
                "captchaType": "blockPuzzle",
                "captchaOriginalPath": "",
                "captchaFontType": "WenQuanZhengHei",
                "captchaFontSize": 0,
                "secretKey": "edge",
                "originalImageBase64": "",
                "point": None,
                "jigsawImageBase64": "",
                "wordList": None,
                "pointList": None,
                "pointJson": None,
                "token": "edge-bypass",
                "result": False,
                "captchaVerification": None,
                "clientUid": None,
                "ts": 0,
            },
            "success": True,
        }
    )


@system_auth_bp.route("/captcha/check", methods=["POST"])
def captcha_check():
    return jsonify({"repCode": "0000", "repMsg": None, "repData": {"result": True}, "success": True})


def is_video_auth_enabled() -> bool:
    """edge 规格默认开启；也可 VIDEO_AUTH_ENABLED=1 强制开启。"""
    flag = (os.environ.get("VIDEO_AUTH_ENABLED") or "").strip().lower()
    if flag in ("1", "true", "yes", "on"):
        return True
    if flag in ("0", "false", "no", "off"):
        return False
    return (os.environ.get("EASYAIOT_DEPLOY_PROFILE") or "").strip().lower() == "edge"


def register_auth_blueprints(app):
    """始终注册路由；edge nginx 才会把 WEB 登录流量打过来。"""
    get_auth_manager()  # 确保默认 admin 种子
    app.register_blueprint(auth_bp, url_prefix="/video/auth")
    app.register_blueprint(system_auth_bp, url_prefix="/video/system")
    logger.info(
        "VIDEO auth 已注册 (profile=%s enabled=%s)",
        os.environ.get("EASYAIOT_DEPLOY_PROFILE"),
        is_video_auth_enabled(),
    )
