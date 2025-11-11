"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import atexit
import os
import socket
import sys
import threading
import time

import netifaces
import pytz
import requests
from dotenv import load_dotenv
from flask import Flask
from healthcheck import HealthCheck, EnvironmentDump
from nacos import NacosClient
from sqlalchemy import text

from app.blueprints import export, inference_task, model, train, train_task, llm, ocr, speech

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 在加载.env文件之前，检查环境变量是否已存在（来自Docker Compose）
# 这样可以判断环境变量的来源
env_before_dotenv = os.environ.get('DATABASE_URL')

# 检查并修复错误的数据库URL（如果包含iot.basiclab.top或doccano，说明是系统环境变量中的错误配置）
if env_before_dotenv and ('iot.basiclab.top' in env_before_dotenv or 'doccano' in env_before_dotenv):
    print(f"⚠️ 检测到错误的DATABASE_URL: {env_before_dotenv}")
    print("🔄 将使用默认配置或从.env文件加载")
    # 删除错误的环境变量，让后续代码使用正确的配置
    del os.environ['DATABASE_URL']
    env_before_dotenv = None

# 加载.env文件，但不覆盖已存在的环境变量（Docker Compose传入的环境变量优先）
# 注意：Docker Compose传入的环境变量会优先于.env文件
load_dotenv(override=False)

# 保存环境变量来源信息（用于后续调试）
ENV_SOURCE = "Docker Compose环境变量" if env_before_dotenv else ".env文件"


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
    service_name = os.getenv('SERVICE_NAME', 'model-server')
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
    
    # 调试信息：打印环境变量来源
    if database_url:
        print(f"📊 DATABASE_URL来源: {ENV_SOURCE}")
    else:
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
            from models import Model, TrainTask, ExportRecord, InferenceTask, LLMConfig, OCRResult
            db.create_all()
        except Exception as e:
            print(f"❌ 建表失败: {str(e)}")

    # 注册蓝图
    app.register_blueprint(export.export_bp, url_prefix='/model/export')
    app.register_blueprint(inference_task.inference_task_bp, url_prefix='/model/inference_task')
    app.register_blueprint(model.model_bp, url_prefix='/model')
    app.register_blueprint(train.train_bp, url_prefix='/model/train')
    app.register_blueprint(train_task.train_task_bp, url_prefix='/model/train_task')
    app.register_blueprint(llm.llm_bp, url_prefix='/model/llm')
    app.register_blueprint(ocr.ocr_bp, url_prefix='/model/ocr')
    app.register_blueprint(speech.speech_bp, url_prefix='/model/speech')

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
    def test_nacos_connection(server_address, max_retries=3, retry_delay=5):
        """测试Nacos服务器连接"""
        try:
            # 解析服务器地址
            if ':' in server_address:
                host, port = server_address.split(':', 1)
                port = int(port)
            else:
                host = server_address
                port = 8848
            
            print(f"🔍 测试Nacos连接: {host}:{port}")
            
            # 方法1: 测试TCP连接
            for attempt in range(max_retries):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        print(f"✅ TCP连接成功: {host}:{port}")
                        return True
                    else:
                        print(f"⚠️ TCP连接失败 (尝试 {attempt + 1}/{max_retries})")
                except socket.gaierror as e:
                    print(f"⚠️ DNS解析失败: {host} - {str(e)}")
                except Exception as e:
                    print(f"⚠️ 连接测试异常: {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            
            # 方法2: 测试HTTP连接
            try:
                url = f"http://{host}:{port}/nacos/v1/console/health"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ HTTP健康检查成功: {host}:{port}")
                    return True
            except Exception as e:
                print(f"⚠️ HTTP健康检查失败: {str(e)}")
            
            return False
        except Exception as e:
            print(f"⚠️ 连接测试异常: {str(e)}")
            return False

    try:
        # 获取环境变量
        nacos_server = os.getenv('NACOS_SERVER', 'Nacos:8848')
        namespace = os.getenv('NACOS_NAMESPACE', '')
        service_name = os.getenv('SERVICE_NAME', 'model-server')
        port = int(os.getenv('FLASK_RUN_PORT', 5000))
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')

        print(f"📋 Nacos配置信息:")
        print(f"   服务器地址: {nacos_server}")
        print(f"   命名空间: {namespace if namespace else '(默认)'}")
        print(f"   用户名: {username}")
        print(f"   服务名称: {service_name}")

        # 测试Nacos连接（最多等待30秒）
        print(f"🔍 开始测试Nacos连接...")
        connection_ok = False
        for attempt in range(6):  # 最多尝试6次，每次等待5秒
            if test_nacos_connection(nacos_server):
                connection_ok = True
                break
            if attempt < 5:
                print(f"⏳ 等待Nacos服务启动... ({attempt + 1}/6)")
                time.sleep(5)
        
        if not connection_ok:
            print(f"⚠️ Nacos连接测试失败，但将继续尝试注册...")

        # 获取IP地址
        ip = os.getenv('POD_IP') or get_local_ip()
        if not os.getenv('POD_IP'):
            print(f"⚠️ 未配置POD_IP，自动获取局域网IP: {ip}")

        # 创建Nacos客户端（支持重试）
        print(f"🔧 创建Nacos客户端...")
        max_register_retries = 3
        register_success = False
        
        for attempt in range(max_register_retries):
            try:
                app.nacos_client = NacosClient(
                    server_addresses=nacos_server,
                    namespace=namespace if namespace else None,
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
                register_success = True
                break
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ 注册尝试 {attempt + 1}/{max_register_retries} 失败: {error_msg}")
                if attempt < max_register_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    print(f"⏳ {wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"注册失败，已重试{max_register_retries}次: {error_msg}")

        if register_success:
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
        error_msg = str(e)
        print(f"❌ Nacos注册失败: {error_msg}")
        print(f"💡 提示: 请检查以下内容:")
        print(f"   1. Nacos服务是否已启动 (docker ps | grep nacos)")
        print(f"   2. 网络连接是否正常 (ping {nacos_server.split(':')[0]})")
        print(f"   3. 服务地址是否正确: {nacos_server}")
        print(f"   4. 用户名和密码是否正确")
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
                service_name = os.getenv('SERVICE_NAME', 'model-server')
                port = int(os.getenv('FLASK_RUN_PORT', 5000))
                app.nacos_client.remove_naming_instance(
                    service_name=service_name,
                    ip=app.registered_ip,
                    port=port
                )
                print(f"🔴 全局注销成功: {service_name}@{app.registered_ip}:{port}")
            except Exception as e:
                print(f"❌ 注销异常: {str(e)}")

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

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
