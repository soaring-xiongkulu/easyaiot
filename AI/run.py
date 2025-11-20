"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import argparse
import atexit
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

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='启动模型服务器')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    args = parser.parse_args()
    return args

# 加载环境变量配置文件（参考VIDEO模块的实现）
def load_env_file(env_name=''):
    """
    加载环境变量配置文件
    使用 override=True 确保配置文件中的值能够覆盖系统环境变量
    """
    if env_name:
        env_file = f'.env.{env_name}'
        if os.path.exists(env_file):
            # 使用 override=True 确保配置文件中的值覆盖已存在的环境变量
            load_dotenv(env_file, override=True)
            print(f"✅ 已加载配置文件: {env_file} (覆盖模式)")
            
            # 显示关键配置信息（用于调试）
            database_url = os.getenv('DATABASE_URL', '未设置')
            nacos_server = os.getenv('NACOS_SERVER', '未设置')
            flask_port = os.getenv('FLASK_RUN_PORT', '未设置')
            print(f"   📊 DATABASE_URL: {database_url[:50]}..." if len(database_url) > 50 else f"   📊 DATABASE_URL: {database_url}")
            print(f"   📊 NACOS_SERVER: {nacos_server}")
            print(f"   📊 FLASK_RUN_PORT: {flask_port}")
        else:
            print(f"⚠️  配置文件 {env_file} 不存在，尝试加载默认 .env 文件")
            if os.path.exists('.env'):
                load_dotenv('.env', override=True)
                print(f"✅ 已加载默认配置文件: .env (覆盖模式)")
            else:
                print(f"❌ 默认配置文件 .env 也不存在")
    else:
        if os.path.exists('.env'):
            load_dotenv('.env', override=True)
            print(f"✅ 已加载默认配置文件: .env (覆盖模式)")
        else:
            print(f"⚠️  默认配置文件 .env 不存在")

# 解析命令行参数并加载配置文件
args = parse_args()
load_env_file(args.env)


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
    
    # 从环境变量获取数据库URL
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL环境变量未设置，请检查docker-compose.yaml配置或.env文件")
    
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
        database_uri = app.config['SQLALCHEMY_DATABASE_URI']
        try:
            # 隐藏密码显示（安全考虑）
            safe_uri = database_uri
            if '@' in database_uri:
                parts = database_uri.split('@')
                if len(parts) == 2:
                    user_pass = parts[0].split('://')[-1]
                    if ':' in user_pass:
                        user = user_pass.split(':')[0]
                        safe_uri = database_uri.replace(user_pass, f"{user}:***")
            print(f"数据库连接: {safe_uri}")
            from models import Model, TrainTask, ExportRecord, InferenceTask, LLMConfig, OCRResult
            db.create_all()
            print(f"✅ 数据库连接成功，表结构已创建/验证")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ 数据库连接失败: {error_msg}")
            if "Connection refused" in error_msg:
                print(f"💡 提示: 请检查数据库服务是否运行，以及 DATABASE_URL 配置是否正确")
                db_host = database_uri.split('@')[1].split('/')[0] if '@' in database_uri else '未知'
                print(f"   当前 DATABASE_URL 主机: {db_host}")
            elif "No module named" in error_msg:
                print(f"💡 提示: 缺少数据库驱动，请运行: pip install psycopg2-binary")

    # 注册蓝图（延迟导入，避免在环境变量加载前就导入）
    try:
        from app.blueprints import export, inference_task, model, train, train_task, llm, ocr, speech
        
        app.register_blueprint(export.export_bp, url_prefix='/model/export')
        app.register_blueprint(inference_task.inference_task_bp, url_prefix='/model/inference_task')
        app.register_blueprint(model.model_bp, url_prefix='/model')
        app.register_blueprint(train.train_bp, url_prefix='/model/train')
        app.register_blueprint(train_task.train_task_bp, url_prefix='/model/train_task')
        app.register_blueprint(llm.llm_bp, url_prefix='/model/llm')
        app.register_blueprint(ocr.ocr_bp, url_prefix='/model/ocr')
        app.register_blueprint(speech.speech_bp, url_prefix='/model/speech')
        print(f"✅ 所有蓝图注册成功")
    except Exception as e:
        print(f"❌ 蓝图注册失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

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

    # Nacos注册与心跳线程管理（参考VIDEO模块的简洁实现）
    try:
        # 获取环境变量
        nacos_server = os.getenv('NACOS_SERVER', 'localhost:8848')
        namespace = os.getenv('NACOS_NAMESPACE', '')
        service_name = os.getenv('SERVICE_NAME', 'model-server')
        port = int(os.getenv('FLASK_RUN_PORT', 5000))
        username = os.getenv('NACOS_USERNAME', 'nacos')
        password = os.getenv('NACOS_PASSWORD', 'basiclab@iot78475418754')

        # 获取IP地址
        ip = os.getenv('POD_IP') or get_local_ip()
        if not os.getenv('POD_IP'):
            print(f"⚠️ 未配置POD_IP，自动获取局域网IP: {ip}")

        # 创建Nacos客户端（直接使用字符串，参考VIDEO模块）
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


def check_port_available(host, port):
    """检查端口是否可用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        return True
    except OSError:
        return False
    finally:
        try:
            sock.close()
        except:
            pass


if __name__ == '__main__':
    app = create_app()
    # 从环境变量读取主机和端口配置
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    
    # 检查端口是否可用
    if not check_port_available(host, port):
        print(f"❌ 错误: 端口 {port} 已被占用")
        print(f"💡 解决方案:")
        print(f"   1. 检查是否有其他进程在使用端口 {port}: lsof -i :{port} 或 netstat -tulpn | grep {port}")
        print(f"   2. 停止占用端口的进程")
        print(f"   3. 或者修改环境变量 FLASK_RUN_PORT 使用其他端口")
        sys.exit(1)
    
    # 获取实际IP地址
    ip = getattr(app, 'registered_ip', None) or get_local_ip()
    print(f"🚀 服务启动: http://{ip}:{port}")
    
    try:
        app.run(host=host, port=port)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ 错误: 端口 {port} 已被占用")
            print(f"💡 请检查是否有其他进程在使用该端口")
        else:
            print(f"❌ 启动失败: {str(e)}")
        sys.exit(1)
