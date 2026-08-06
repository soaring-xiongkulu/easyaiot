"""RTC 管理服务入口。"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.blueprints.health import health_bp
from app.blueprints.platforms import platforms_bp
from app.blueprints.streams import streams_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EasyAIoT RTC 服务")
    parser.add_argument("--env", type=str, default="", help="加载 .env.{name} 配置文件")
    return parser.parse_args()


def load_env(env_name: str = "") -> None:
    rtc_dir = os.path.dirname(os.path.abspath(__file__))
    if env_name:
        path = os.path.join(rtc_dir, f".env.{env_name}")
        if os.path.isfile(path):
            load_dotenv(path, override=True)
            logger.info("已加载 %s", path)
            return
    for name in (".env", "env.example"):
        path = os.path.join(rtc_dir, name)
        if os.path.isfile(path):
            load_dotenv(path, override=True)
            logger.info("已加载 %s", path)
            return


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "rtc-dev-secret")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.register_blueprint(health_bp)
    app.register_blueprint(platforms_bp)
    app.register_blueprint(streams_bp)

    @app.route("/")
    def index():
        return {
            "service": "EasyAIoT RTC",
            "description": "go2rtc 二次开发模块 — 消费级摄像头桥接",
            "platforms": [
                "tapo", "tuya", "ring", "nest", "xiaomi",
                "wyze", "doorbird", "gopro", "roborock",
            ],
            "docs": "/api/platforms",
        }

    return app


def main() -> None:
    args = parse_args()
    load_env(args.env)

    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", "6100"))
    debug = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

    app = create_app()
    logger.info("RTC 管理服务启动 %s:%s", host, port)
    logger.info("go2rtc API: %s", os.getenv("GO2RTC_API_URL", "http://127.0.0.1:1984"))
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    main()
