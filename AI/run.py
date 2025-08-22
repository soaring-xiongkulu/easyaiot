import os
import socket
import sys
import threading
import time

import pytz
from dotenv import load_dotenv
from flask import Flask
from nacos import NacosClient

from app.blueprints import export, inference, model, training, training_record

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()
def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        # 创建UDP套接字连接到外部地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))  # 使用Google DNS
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'  # 失败时使用回环地址
    finally:
        s.close()
    return ip

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
            from models import Model, TrainingRecord, ExportRecord
            db.create_all()
        except Exception as e:
            print(f"建表失败: {str(e)}")

    app.register_blueprint(export.export_bp)
    app.register_blueprint(inference.inference_bp)
    app.register_blueprint(model.model_bp)
    app.register_blueprint(training.training_bp)
    app.register_blueprint(training_record.training_record_bp)

    # 注册服务
    app.nacos_client = register_to_nacos()

    @app.template_filter('beijing_time')
    def beijing_time_filter(dt):
        if dt:
            utc = pytz.timezone('UTC')
            beijing = pytz.timezone('Asia/Shanghai')
            utc_time = utc.localize(dt)
            beijing_time = utc_time.astimezone(beijing)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        return '未知'

    @app.teardown_appcontext
    def deregister_on_shutdown(exception=None):
        if hasattr(app, 'nacos_client') and app.nacos_client:
            service_name = os.getenv('SERVICE_NAME', 'model-server')
            ip = os.getenv('POD_IP', 'localhost')
            port = int(os.getenv('FLASK_RUN_PORT', 5000))
            app.nacos_client.remove_naming_instance(
                service_name=service_name,
                ip=ip,
                port=port
            )
            print("✅ 服务已注销")

    return app

def register_to_nacos():
    try:
        # 获取环境变量
        nacos_server = os.getenv('NACOS_SERVER', 'iot.basiclab.top:8848')
        namespace = os.getenv('NACOS_NAMESPACE', 'local')
        service_name = os.getenv('SERVICE_NAME', 'model-server')
        port = int(os.getenv('FLASK_RUN_PORT', 5000))
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')

        # 获取IP：优先使用环境变量，否则自动获取
        ip = os.getenv('POD_IP')
        if not ip:
            ip = get_local_ip()
            print(f"⚠️ 未配置POD_IP，自动获取局域网IP: {ip}")

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
                    # print(f"心跳发送成功: {service_name}")
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
    app.run(host='0.0.0.0', port=5000)
