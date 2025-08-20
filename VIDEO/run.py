import os
import sys
import threading
import time

import pytz
from dotenv import load_dotenv
from flask import Flask
from nacos import NacosClient

from app.blueprints import camera

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TIMEZONE'] = 'Asia/Shanghai'
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/datasets', exist_ok=True)
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/inference_results', exist_ok=True)

    from models import db
    db.init_app(app)

    with app.app_context():
        try:
            print(app.config['SQLALCHEMY_DATABASE_URI'])
            from models import Project, Image, Label, Annotation, ExportRecord
            db.create_all()
        except Exception as e:
            print(f"建表失败: {str(e)}")

    app.register_blueprint(camera.camera_bp)

    from app.services.camera_service import CameraService
    app.camera_capture = CameraService()

    @app.template_filter('beijing_time')
    def beijing_time_filter(dt):
        if dt:
            utc = pytz.timezone('UTC')
            beijing = pytz.timezone('Asia/Shanghai')
            utc_time = utc.localize(dt)
            beijing_time = utc_time.astimezone(beijing)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        return '未知'

    return app

def register_to_nacos():
    try:
        # 获取环境变量
        nacos_server = os.getenv('NACOS_SERVER', 'iot.basiclab.top:8848')
        namespace = os.getenv('NACOS_NAMESPACE', 'local')
        service_name = os.getenv('SERVICE_NAME', 'easyaiot-video')
        ip = os.getenv('POD_IP', 'localhost')
        port = int(os.getenv('FLASK_RUN_PORT', 5000))
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')

        # 创建客户端
        client = NacosClient(
            server_addresses=nacos_server,
            namespace=namespace,
            username=username,
            password=password
        )

        client.add_naming_instance(
            service_name=service_name,
            ip=ip,
            port=port,
            cluster_name="DEFAULT",
            healthy=True,
            ephemeral=True
        )
        print(f"✅ 服务注册成功: {service_name}@{ip}:{port}")

        def heartbeat():
            while True:
                try:
                    client.send_heartbeat(
                        service_name=service_name,
                        ip=ip,
                        port=port
                    )
                    print(f"心跳发送成功: {service_name}")
                except Exception as e:
                    print(f"心跳异常: {str(e)}")
                time.sleep(5)  # 间隔5秒

        threading.Thread(target=heartbeat, daemon=True).start()
        return client

    except Exception as e:
        print(f"❌ 注册失败: {str(e)}")
        return None


if __name__ == '__main__':
    app = create_app()
    try:
        nacos_client = register_to_nacos()
        app.run(host='0.0.0.0', port=5000)
    finally:
        # 优雅注销服务:cite[2]
        if nacos_client:
            nacos_client.remove_naming_instance(
                service_name=os.getenv('SERVICE_NAME'),
                ip=os.getenv('POD_IP'),
                port=int(os.getenv('FLASK_RUN_PORT'))
            )
            print("服务已注销")