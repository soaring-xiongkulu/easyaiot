"""
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import argparse
import atexit
import multiprocessing
import os
import socket
import sys
import threading
import time

import netifaces
import pytz
from flask import Flask
from healthcheck import HealthCheck, EnvironmentDump
from nacos import NacosClient
from sqlalchemy import text

from app.utils.ai_env import load_ai_env

_repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
_lib_root = os.path.join(_repo_root, '.scripts', 'lib')
for _p in (_repo_root, _lib_root, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.append(_p)

# 设置multiprocessing启动方法为'spawn'以支持CUDA
# 这必须在导入使用multiprocessing的模块之前设置
# 注意：set_start_method只能在主进程中调用一次
try:
    # 检查当前启动方法
    try:
        current_method = multiprocessing.get_start_method()
    except RuntimeError:
        # 如果还没有设置，尝试设置
        current_method = None
    
    if current_method != 'spawn':
        multiprocessing.set_start_method('spawn', force=True)
        print(f"✅ 已设置multiprocessing启动方法为'spawn'（原方法: {current_method or '未设置'}）")
    else:
        print(f"✅ multiprocessing启动方法已为'spawn'")
except RuntimeError as e:
    # 如果已经设置过或无法设置，记录但不中断程序
    try:
        current_method = multiprocessing.get_start_method()
        print(f"⚠️  无法设置multiprocessing启动方法: {str(e)}，当前方法: {current_method}")
    except RuntimeError:
        print(f"⚠️  无法设置multiprocessing启动方法: {str(e)}")

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='启动模型服务器')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    args = parser.parse_args()
    return args

# 加载环境变量配置文件
def _print_key_config():
    db_url = os.environ.get('DATABASE_URL', '')
    db_host = '未设置'
    if db_url:
        try:
            from urllib.parse import urlparse
            db_host = urlparse(db_url.replace('postgres://', 'postgresql://', 1)).hostname or '未知'
        except Exception:
            db_host = '解析失败'
    print(f"📌 DATABASE_URL 主机: {db_host}")
    print(f"📌 NACOS_SERVER: {os.environ.get('NACOS_SERVER', '未设置')}")
    print(f"📌 FLASK_RUN_PORT: {os.environ.get('FLASK_RUN_PORT', '未设置')}")


def load_env_file(env_name=''):
    if env_name:
        os.environ['AI_ENV'] = env_name
    loaded = load_ai_env(override=True)
    if loaded:
        label = os.path.basename(loaded)
        print(f"✅ 已加载配置文件: {label}（override=True，覆盖已有环境变量）")
        _print_key_config()
    elif env_name:
        print(f"⚠️  配置文件 .env.{env_name} 不存在，且默认 .env 也不存在")
    else:
        print(f"⚠️  默认配置文件 .env 不存在")

# 解析命令行参数并加载配置文件
args = parse_args()
load_env_file(args.env)

# 在导入 ONNX 相关模块前补全 pip 安装的 nvidia CUDA 库路径（非 Docker 直跑也生效）
import app.utils.nvidia_lib_path  # noqa: F401


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
    consecutive_errors = 0
    max_consecutive_errors = 3
    
    while not stop_event.is_set():
        try:
            # 检查客户端是否存在
            if client is None:
                time.sleep(10)  # 如果客户端不存在，等待更长时间
                continue
            
            client.send_heartbeat(service_name=service_name, ip=ip, port=port)
            # 心跳成功，重置错误计数
            consecutive_errors = 0
            # print(f"✅ 心跳发送成功: {service_name}@{ip}:{port}")
        except Exception as e:
            error_msg = str(e)
            consecutive_errors += 1
            
            # 如果是权限错误，尝试重新注册服务
            if "Insufficient privilege" in error_msg or "insufficient privilege" in error_msg.lower():
                # 只在第一次或每10次错误时打印，减少日志噪音
                if consecutive_errors == 1 or consecutive_errors % 10 == 0:
                    print(f"⚠️  Nacos心跳权限错误，尝试重新注册服务 (错误次数: {consecutive_errors})")
                
                # 尝试重新注册服务
                try:
                    if client:
                        client.add_naming_instance(
                            service_name=service_name,
                            ip=ip,
                            port=port,
                            cluster_name="DEFAULT",
                            healthy=True,
                            ephemeral=True
                        )
                        print(f"✅ 服务重新注册成功: {service_name}@{ip}:{port}")
                        consecutive_errors = 0  # 重置错误计数
                except Exception as reg_error:
                    # 重新注册失败，只在每10次错误时打印
                    if consecutive_errors % 10 == 0:
                        print(f"❌ 服务重新注册失败: {str(reg_error)}")
            else:
                # 其他错误，只在每10次错误时打印
                if consecutive_errors % 10 == 0:
                    print(f"⚠️  心跳异常 (错误次数: {consecutive_errors}): {error_msg}")
            
            # 如果连续错误次数过多，增加等待时间
            if consecutive_errors >= max_consecutive_errors:
                time.sleep(30)  # 等待30秒后重试
            else:
                time.sleep(5)
        else:
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
    # 训练任务本地数据集 zip 上传（默认 500MB，可通过环境变量覆盖）
    max_upload_mb = int(os.getenv('TRAIN_DATASET_MAX_UPLOAD_MB', '5120'))
    app.config['MAX_CONTENT_LENGTH'] = max_upload_mb * 1024 * 1024
    
    # 配置 Flask URL 生成（用于在异步任务中使用 url_for）
    # 从环境变量获取配置，如果没有则从运行参数推断
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    
    # 检测是否在容器环境中运行
    def is_containerized():
        """检测是否在容器环境中运行"""
        # 检查常见的容器环境标识
        if os.path.exists('/.dockerenv'):
            return True
        # 检查 cgroup 是否包含容器标识
        try:
            with open('/proc/self/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'kubepods' in content or 'containerd' in content:
                    return True
        except:
            pass
        # 检查环境变量
        if os.getenv('KUBERNETES_SERVICE_HOST') or os.getenv('DOCKER_CONTAINER'):
            return True
        return False
    
    # 如果配置了 SERVER_NAME，使用它；否则根据 host 和 port 构建
    # 如果设置为空字符串、"none" 或 "disable"，则不设置 SERVER_NAME（避免警告）
    server_name = os.getenv('FLASK_SERVER_NAME')
    if server_name and server_name.lower() in ('none', 'disable', ''):
        server_name = None
    elif not server_name:
        # 如果设置了 FLASK_AUTO_SERVER_NAME=false，则不自动设置 SERVER_NAME
        auto_server_name = os.getenv('FLASK_AUTO_SERVER_NAME', 'true').lower()
        if auto_server_name == 'false':
            server_name = None
        else:
            # 在容器环境中，默认不自动设置 SERVER_NAME，避免 Host 不匹配问题
            # 只有在非容器环境或明确配置时才设置
            if is_containerized():
                # 容器环境中，不自动设置 SERVER_NAME，允许通过 localhost、127.0.0.1 或任何 IP 访问
                server_name = None
                print("ℹ️  检测到容器环境，不自动设置 SERVER_NAME（允许灵活访问）")
            else:
                # 非容器环境，按原逻辑设置
                if host == '0.0.0.0':
                    try:
                        actual_ip = os.getenv('POD_IP') or get_local_ip()
                        server_name = f"{actual_ip}:{port}"
                    except Exception as e:
                        # 如果无法获取 IP，不设置 SERVER_NAME（避免 localhost 警告）
                        print(f"⚠️  无法获取本地IP，不设置SERVER_NAME以避免警告: {str(e)}")
                        server_name = None
                else:
                    server_name = f"{host}:{port}"
    
    # 只在设置了 server_name 时才配置，避免 localhost 访问时的警告
    # 注意：在容器环境中，建议不设置 SERVER_NAME 以避免 Host 不匹配的警告
    if server_name:
        app.config['SERVER_NAME'] = server_name
    app.config['APPLICATION_ROOT'] = os.getenv('FLASK_APPLICATION_ROOT', '/')
    app.config['PREFERRED_URL_SCHEME'] = os.getenv('FLASK_PREFERRED_URL_SCHEME', 'http')
    print(f"✅ Flask URL配置: SERVER_NAME={server_name or '(未设置，从请求推断)'}, APPLICATION_ROOT={app.config['APPLICATION_ROOT']}, PREFERRED_URL_SCHEME={app.config['PREFERRED_URL_SCHEME']}")

    try:
        from cluster_storage import apply_cluster_env_defaults, ensure_cluster_dirs, get_ai_datasets_dir, get_ai_models_dir, is_cluster_mode
        applied = apply_cluster_env_defaults()
        if applied:
            print(f'✅ 集群存储环境已应用: {", ".join(applied.keys())}')
        if is_cluster_mode():
            ensure_cluster_dirs()
            app.config['CLUSTER_MODE'] = True
            datasets_dir = get_ai_datasets_dir()
            models_dir = get_ai_models_dir()
            os.makedirs(datasets_dir, exist_ok=True)
            os.makedirs(models_dir, exist_ok=True)
            os.makedirs(os.path.join(datasets_dir, 'uploads'), exist_ok=True)
    except ImportError:
        pass

    # 创建数据目录
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('data/datasets', exist_ok=True)
    os.makedirs('data/models', exist_ok=True)
    os.makedirs('data/inference_results', exist_ok=True)

    # 初始化数据库
    from db_models import db
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
            from db_models import (
                Model,
                TrainTask,
                ExportRecord,
                InferenceTask,
                LLMModel,
                OCRResult,
                SAMInferenceResult,
                AIService,
                AutoLabelTask,
                AutoLabelResult,
                AutoLabelModelHistory,
                ensure_model_table_status_column,
                ensure_model_origin_columns,
                ensure_model_class_columns,
                ensure_train_task_name_column,
                ensure_train_task_dataset_columns,
                ensure_train_task_cluster_columns,
                ensure_auto_label_task_model_id_column,
                ensure_auto_label_task_sam_columns,
                ensure_auto_label_task_pipeline_column,
                ensure_auto_label_task_cluster_columns,
                ensure_auto_label_subtask_table,
                ensure_auto_label_model_history_table,
                AutoLabelSubTask,
            )
            db.create_all()
            ensure_model_table_status_column(db.engine)
            ensure_model_origin_columns(db.engine)
            ensure_model_class_columns(db.engine)
            ensure_train_task_name_column(db.engine)
            ensure_train_task_dataset_columns(db.engine)
            ensure_train_task_cluster_columns(db.engine)
            ensure_auto_label_task_model_id_column(db.engine)
            ensure_auto_label_task_sam_columns(db.engine)
            ensure_auto_label_task_pipeline_column(db.engine)
            ensure_auto_label_task_cluster_columns(db.engine)
            ensure_auto_label_subtask_table(db.engine)
            ensure_auto_label_model_history_table(db.engine)
            # 大模型预置模板数据播种（仅空表时执行，幂等；占位密钥 sk-placeholder-* 填入真实密钥后启用）
            from app.services.llm_template_seed import ensure_llm_template_seed
            seed_result = ensure_llm_template_seed()
            if seed_result.get('inserted'):
                print(f"✅ 已播种 {seed_result['inserted']} 条大模型预置模板数据（填入真实 API 密钥后即可启用）")
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
        from app.blueprints import export, inference, model, train, train_task, llm, llm_deploy, ocr, speech, deploy, auto_label, plate, sam, pose, minio_proxy
        
        app.register_blueprint(minio_proxy.minio_proxy_bp)
        app.register_blueprint(export.export_bp, url_prefix='/model/export')
        app.register_blueprint(inference.inference_task_bp, url_prefix='/model/inference_task')
        app.register_blueprint(model.model_bp, url_prefix='/model')
        app.register_blueprint(train.train_bp, url_prefix='/model/train_task')
        app.register_blueprint(train_task.train_task_bp, url_prefix='/model/train_task')
        app.register_blueprint(llm.llm_bp, url_prefix='/model/llm')
        app.register_blueprint(llm_deploy.llm_deploy_bp, url_prefix='/model/llm_deploy')
        app.register_blueprint(ocr.ocr_bp, url_prefix='/model/ocr')
        app.register_blueprint(speech.speech_bp, url_prefix='/model/speech')
        app.register_blueprint(deploy.deploy_service_bp, url_prefix='/model/deploy_service')
        app.register_blueprint(auto_label.auto_label_bp, url_prefix='/model/dataset')  # 与其他模块保持一致，使用 /model/ 前缀
        app.register_blueprint(plate.plate_bp, url_prefix='/model/plate')
        app.register_blueprint(sam.sam_bp, url_prefix='/model/sam')
        app.register_blueprint(pose.pose_bp, url_prefix='/model/pose')
        
        # SAM 模型预热：在后台线程加载模型，避免首请求因冷加载（3.26GB）超时
        if os.getenv('SAM_ENABLED', 'false').lower() in ('1', 'true', 'yes'):
            try:
                import threading as _sam_warmup_threading
                def _sam_warmup():
                    try:
                        from app.services.sam_service import get_sam_service
                        svc = get_sam_service()
                        svc.warmup_if_needed()
                        print('✅ SAM 模型预热完成')
                    except Exception as _e:
                        print(f'⚠️  SAM 模型预热失败（不影响后续请求，首次推理将冷加载）: {_e}')
                _t = _sam_warmup_threading.Thread(target=_sam_warmup, daemon=True)
                _t.start()
                print('🔄 SAM 模型预热已启动（后台加载中…）')
            except Exception as _e:
                print(f'⚠️  SAM 预热线程启动失败: {_e}')
        
        # 注册集群推理接口（使用不同的路由，不影响原有推理接口）
        from app.blueprints import cluster
        app.register_blueprint(cluster.cluster_inference_bp, url_prefix='/model/cluster')
        print(f"✅ 所有蓝图注册成功")
        
        # 启动心跳超时检查任务
        try:
            from app.blueprints.deploy import start_heartbeat_checker
            start_heartbeat_checker(app)
        except Exception as e:
            print(f"⚠️  启动心跳检查任务失败: {str(e)}")

        # 恢复因容器/进程重启而中断的训练任务
        try:
            from app.blueprints.train import recover_stale_train_tasks
            recovered = recover_stale_train_tasks(app)
            if recovered:
                print(f'✅ 已将 {recovered} 个因服务重启中断的训练任务标记为失败')
        except Exception as e:
            print(f'⚠️  恢复中断训练任务失败: {str(e)}')

        # mini 形态：将 MinIO 磁盘历史数据同步到 flat 本地存储（模型封面/权重等）
        try:
            from app.utils.service_urls import is_mini_deploy_profile
            if is_mini_deploy_profile():
                from app.services.local_storage_service import (
                    get_minio_seed_data_root,
                    migrate_seed_data_to_local_storage,
                )
                seed_root = get_minio_seed_data_root()
                if seed_root:
                    copied, skipped = migrate_seed_data_to_local_storage(
                        buckets=['models'],
                        skip_existing=True,
                    )
                    if copied:
                        print(f'✅ mini 形态：已从种子目录同步 {copied} 个 models 对象到本地存储')
                    elif skipped:
                        print(f'✅ mini 形态：models 本地存储已就绪（{skipped} 个对象）')
                else:
                    print('ℹ️  mini 形态：未找到 MinIO 种子数据目录，跳过历史对象同步')
        except Exception as e:
            print(f'⚠️  mini MinIO 历史数据同步失败: {str(e)}')

        # 启动自动标注队列调度器
        try:
            from app.services.auto_label_cluster_service import start_auto_label_queue_coordinator
            start_auto_label_queue_coordinator(app)
            print('✅ 自动标注队列调度器已启动')
        except Exception as e:
            print(f'⚠️  启动自动标注队列调度器失败: {str(e)}')
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
            from db_models import db
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
