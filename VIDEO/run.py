"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import argparse
import os
import socket
import sys
import threading
import time
import logging

import netifaces
import pytz
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from healthcheck import HealthCheck, EnvironmentDump
from nacos import NacosClient
from sqlalchemy import text

from app.blueprints import camera, alert, snap, playback, record

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='VIDEO服务启动脚本')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    args = parser.parse_args()
    return args

# 加载环境变量配置文件
def load_env_file(env_name=''):
    if env_name:
        env_file = f'.env.{env_name}'
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ 已加载配置文件: {env_file}")
        else:
            print(f"⚠️  配置文件 {env_file} 不存在，尝试加载默认 .env 文件")
            if os.path.exists('.env'):
                load_dotenv('.env')
                print(f"✅ 已加载默认配置文件: .env")
            else:
                print(f"❌ 默认配置文件 .env 也不存在")
    else:
        if os.path.exists('.env'):
            load_dotenv('.env')
            print(f"✅ 已加载默认配置文件: .env")
        else:
            print(f"⚠️  默认配置文件 .env 不存在")

# 解析命令行参数并加载配置文件
args = parse_args()
load_env_file(args.env)

# 配置日志级别，减少第三方库的详细输出
logging.getLogger('nacos').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

# 配置主应用日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
    
    # 配置 CORS - 允许跨域请求
    CORS(app, resources={
        r"/video/*": {"origins": "*"},
        r"/actuator/*": {"origins": "*"}
    })
    
    # 从环境变量获取数据库URL，优先使用Docker Compose传入的环境变量
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL环境变量未设置，请检查docker-compose.yaml配置")
    
    # 转换postgres://为postgresql://（SQLAlchemy要求）
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TIMEZONE'] = 'Asia/Shanghai'
    
    # MinIO对象存储配置
    app.config['MINIO_ENDPOINT'] = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
    app.config['MINIO_ACCESS_KEY'] = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    app.config['MINIO_SECRET_KEY'] = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
    app.config['MINIO_SECURE'] = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'

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
            from models import Device, Image, DeviceDirectory, SnapSpace, SnapTask, DetectionRegion, AlgorithmModelService, RegionModelService, DeviceStorageConfig, Playback, RecordSpace
            db.create_all()
            
            # 迁移：检查并添加缺失的列和表
            try:
                # 确保所有表都存在（包括 device_directory）
                db.create_all()
                
                # 检查 device 表的 directory_id 列是否存在
                result = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'device' 
                        AND column_name = 'directory_id'
                    );
                """))
                directory_id_exists = result.scalar()
                
                if not directory_id_exists:
                    print("⚠️  device.directory_id 列不存在，正在添加...")
                    # 确保 device_directory 表存在
                    db.create_all()
                    # 添加 directory_id 列
                    db.session.execute(text("""
                        ALTER TABLE device 
                        ADD COLUMN directory_id INTEGER 
                        REFERENCES device_directory(id) ON DELETE SET NULL;
                    """))
                    db.session.commit()
                    print("✅ device.directory_id 列添加成功")
                else:
                    print("✅ 数据库迁移检查完成，所有列已存在")
            except Exception as e:
                print(f"⚠️  数据库迁移检查失败: {str(e)}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
        except Exception as e:
            print(f"❌ 建表失败: {str(e)}")

    # 注册蓝图
    try:
        app.register_blueprint(camera.camera_bp, url_prefix='/video/camera')
        print(f"✅ Camera Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Camera Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    try:
        app.register_blueprint(alert.alert_bp, url_prefix='/video/alert')
        print(f"✅ Alert Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Alert Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    try:
        app.register_blueprint(snap.snap_bp, url_prefix='/video/snap')
        app.register_blueprint(record.record_bp, url_prefix='/video/record')
        print(f"✅ Snap Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Snap Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    try:
        app.register_blueprint(playback.playback_bp, url_prefix='/video/playback')
        print(f"✅ Playback Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Playback Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()

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
        _start_search(app)
        import atexit
        # 安全关闭调度器：检查调度器是否正在运行
        def safe_shutdown_scheduler():
            try:
                if scheduler.running:
                    scheduler.shutdown(wait=False)
                    print('✅ 调度器已安全关闭')
            except Exception as e:
                # 忽略调度器未运行或已关闭的异常
                pass
        atexit.register(safe_shutdown_scheduler)

    # 应用启动后自动启动需要推流的设备
    with app.app_context():
        try:
            from app.blueprints.camera import auto_start_streaming
            auto_start_streaming()
        except Exception as e:
            print(f"❌ 自动启动推流设备失败: {str(e)}")
    
    # 启动抓拍空间自动清理任务（每天凌晨2点执行）
    with app.app_context():
        try:
            from app.services.camera_service import scheduler
            from app.services.snap_space_service import auto_cleanup_all_spaces
            
            if scheduler and not scheduler.running:
                scheduler.start()
            
            # 每天凌晨2点执行自动清理
            scheduler.add_job(
                auto_cleanup_all_spaces,
                'cron',
                hour=2,
                minute=0,
                id='auto_cleanup_snap_spaces',
                replace_existing=True
            )
            print('✅ 抓拍空间自动清理任务已启动（每天凌晨2点执行）')
        except Exception as e:
            print(f"❌ 启动抓拍空间自动清理任务失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 初始化抓拍任务调度器
        try:
            from app.services.snap_task_service import init_all_tasks
            init_all_tasks()
            print("✅ 抓拍任务调度器初始化成功")
        except Exception as e:
            print(f"❌ 初始化抓拍任务调度器失败: {str(e)}")
            import traceback
            traceback.print_exc()

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
    port = int(os.getenv('FLASK_RUN_PORT', 6000))
    
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