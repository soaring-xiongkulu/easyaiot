"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import socket
import sys
import threading
import time

import netifaces
import pytz
from dotenv import load_dotenv
from flask import Flask
from healthcheck import HealthCheck, EnvironmentDump
from nacos import NacosClient
from sqlalchemy import text

from app.blueprints import camera, nvr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


def get_local_ip():
    # 方案1: 环境变量优先
    if ip := os.getenv('POD_IP'):
        return ip

    # 方案2: 多网卡探测
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
        for addr in addrs:
            ip = addr['addr']
            if ip != '127.0.0.1' and not ip.startswith('169.254.'):
                return ip

    # 方案3: 原始方式（仅在无代理时启用）
    if not (os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    raise RuntimeError("无法确定本地IP，请配置POD_IP环境变量")


def send_heartbeat(client, ip, port, stop_event):
    """独立的心跳发送函数（支持安全停止）"""
    service_name = os.getenv('SERVICE_NAME', 'video-server')
    while not stop_event.is_set():
        try:
            client.send_heartbeat(service_name=service_name, ip=ip, port=port)
            # print(f"✅ 心跳发送成功: {service_name}@{ip}:{port}")
        except Exception as e:
            print(f"❌ 心跳异常: {str(e)}")
        time.sleep(5)


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    
    # 从环境变量获取数据库URL，优先使用Docker Compose传入的环境变量
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL环境变量未设置，请检查docker-compose.yaml配置")
    
    # 转换postgres://为postgresql://（SQLAlchemy要求）
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TIMEZONE'] = 'Asia/Shanghai'

    # 创建数据目录
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/datasets', exist_ok=True)
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/inference_results', exist_ok=True)

    # 初始化数据库
    from models import db
    db.init_app(app)
    with app.app_context():
        try:
            print(f"数据库连接: {app.config['SQLALCHEMY_DATABASE_URI']}")
            from models import Device, Image, Nvr
            db.create_all()
        except Exception as e:
            print(f"❌ 建表失败: {str(e)}")

    # 注册蓝图
    app.register_blueprint(camera.camera_bp, url_prefix='/video/camera')
    app.register_blueprint(nvr.nvr_bp, url_prefix='/video/nvr')

    # 健康检查路由初始化
    def init_health_check(app):
        health = HealthCheck()
        envdump = EnvironmentDump()

        # 添加数据库检查 - 使用text()包装SQL语句
        def database_available():
            from models import db
            try:
                db.session.execute(text('SELECT 1'))
                return True, "Database OK"
            except Exception as e:
                return False, str(e)

        health.add_check(database_available)

        # 显式绑定路由
        app.add_url_rule('/actuator/health', 'healthcheck', view_func=health.run)
        app.add_url_rule('/actuator/info', 'envdump', view_func=envdump.run)

        # 处理所有OPTIONS请求
        @app.route('/actuator/<path:subpath>', methods=['OPTIONS'])
        def handle_options(subpath):
            return '', 204

    init_health_check(app)

    # Nacos注册与心跳线程管理
    try:
        # 获取环境变量
        nacos_server = os.getenv('NACOS_SERVER', 'Nacos:8848')
        namespace = os.getenv('NACOS_NAMESPACE', '')
        service_name = os.getenv('SERVICE_NAME', 'video-server')
        port = int(os.getenv('FLASK_RUN_PORT', 6000))
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')

        # 获取IP地址
        ip = os.getenv('POD_IP') or get_local_ip()
        if not os.getenv('POD_IP'):
            print(f"⚠️ 未配置POD_IP，自动获取局域网IP: {ip}")

        # 创建Nacos客户端
        app.nacos_client = NacosClient(
            server_addresses=nacos_server,
            namespace=namespace,
            username=username,
            password=password
        )

        # 注册服务实例
        app.nacos_client.add_naming_instance(
            service_name=service_name,
            ip=ip,
            port=port,
            cluster_name="DEFAULT",
            healthy=True,
            ephemeral=True
        )
        print(f"✅ 服务注册成功: {service_name}@{ip}:{port}")

        # 存储注册IP到主应用对象
        app.registered_ip = ip

        # 启动心跳线程
        app.heartbeat_stop_event = threading.Event()
        app.heartbeat_thread = threading.Thread(
            target=send_heartbeat,
            args=(app.nacos_client, ip, port, app.heartbeat_stop_event),
            daemon=True
        )
        app.heartbeat_thread.start()
        print(f"🚀 心跳线程已启动，间隔: 5秒")

    except Exception as e:
        print(f"❌ Nacos注册失败: {str(e)}")
        app.nacos_client = None

    # Nacos初始化标记
    has_setup_nacos = False

    @app.before_request
    def setup_nacos_once():
        nonlocal has_setup_nacos
        if not has_setup_nacos:
            app.nacos_registered = True if hasattr(app, 'nacos_client') else False
            has_setup_nacos = True

    # 应用退出时注销服务
    def deregister_service():
        if hasattr(app, 'nacos_registered') and app.nacos_registered:
            try:
                # 停止心跳线程
                if hasattr(app, 'heartbeat_stop_event'):
                    app.heartbeat_stop_event.set()
                    app.heartbeat_thread.join(timeout=3.0)
                    print("🛑 心跳线程已停止")

                # 注销服务实例
                service_name = os.getenv('SERVICE_NAME', 'video-server')
                port = int(os.getenv('FLASK_RUN_PORT', 6000))
                app.nacos_client.remove_naming_instance(
                    service_name=service_name,
                    ip=app.registered_ip,
                    port=port
                )
                print(f"🔴 全局注销成功: {service_name}@{app.registered_ip}:{port}")
            except Exception as e:
                print(f"❌ 注销异常: {str(e)}")

    import atexit
    atexit.register(deregister_service)

    # 时间格式化过滤器
    @app.template_filter('beijing_time')
    def beijing_time_filter(dt):
        if dt:
            utc = pytz.timezone('UTC')
            beijing = pytz.timezone('Asia/Shanghai')
            utc_time = utc.localize(dt)
            beijing_time = utc_time.astimezone(beijing)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        return '未知'

    # 启动摄像头搜索服务
    with app.app_context():
        from app.services.camera_service import _start_search, scheduler
        _start_search()

        # 确保调度器在应用退出时正确关闭
        import atexit
        atexit.register(lambda: scheduler.shutdown())

    # 应用启动后自动启动需要推流的设备
    with app.app_context():
        try:
            # 导入auto_start_streaming函数
            from app.blueprints.camera import auto_start_streaming
            # 调用函数启动所有需要推流的设备
            auto_start_streaming()
            print("✅ 已自动启动所有需要推流的设备")
        except Exception as e:
            print(f"❌ 自动启动推流设备失败: {str(e)}")
            import traceback
            traceback.print_exc()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=6000)