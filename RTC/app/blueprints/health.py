"""健康检查。"""

from flask import Blueprint, jsonify

from app.services.stream_service import StreamService

health_bp = Blueprint("health", __name__)


@health_bp.route("/actuator/health", methods=["GET"])
@health_bp.route("/health", methods=["GET"])
def health():
    svc = StreamService()
    go2rtc_ok = False
    go2rtc_version = None
    try:
        info = svc.go2rtc_info()
        go2rtc_ok = True
        go2rtc_version = info.get("version")
    except Exception:
        pass

    status = "UP" if go2rtc_ok else "DEGRADED"
    return jsonify({
        "status": status,
        "service": "rtc-server",
        "go2rtc": {"status": "UP" if go2rtc_ok else "DOWN", "version": go2rtc_version},
    })
