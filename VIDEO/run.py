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

from app.utils.video_env import load_video_env

from app.blueprints import camera, alert, snap, playback, record, algorithm_task, stream_forward, face

_repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
_lib_root = os.path.join(_repo_root, '.scripts', 'lib')
for _p in (_repo_root, _lib_root, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.append(_p)

# 解析命令行参数
def parse_args():
    parser = argparse.ArgumentParser(description='VIDEO服务启动脚本')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    args = parser.parse_args()
    return args

# 加载环境变量配置文件
def _print_key_config():
    """启动时打印关键连接配置（便于排查仍连 localhost 的问题）"""
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
    print(f"📌 KAFKA_BOOTSTRAP_SERVERS: {os.environ.get('KAFKA_BOOTSTRAP_SERVERS', '未设置')}")


def load_env_file(env_name=''):
    # 显式 --env=prod 时必须 override=True，否则 shell/systemd 里旧的 localhost 会盖掉 .env.prod
    if env_name:
        os.environ['VIDEO_ENV'] = env_name
    loaded = load_video_env(override=True)
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
logging.getLogger('nacos').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)  # 禁用 Werkzeug 访问日志

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


def create_app(start_background_tasks=None):
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
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # 连接前检测连接是否有效
        'pool_recycle': 3600,   # 1小时后回收连接
        'pool_size': 10,        # 连接池大小
        'max_overflow': 20,     # 最大溢出连接数
        'connect_args': {
            'connect_timeout': 10,  # 连接超时时间（秒）
        }
    }
    app.config['TIMEZONE'] = 'Asia/Shanghai'
    
    # MinIO对象存储配置
    app.config['MINIO_ENDPOINT'] = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
    app.config['MINIO_ACCESS_KEY'] = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    app.config['MINIO_SECRET_KEY'] = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
    app.config['MINIO_SECURE'] = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'
    
    # Kafka配置
    # 重要：VIDEO服务使用 host 网络模式，必须使用 localhost 访问 Kafka
    # 如果环境变量中配置了容器名（如 Kafka:9092），需要强制覆盖为 localhost:9092
    kafka_bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    if 'Kafka' in kafka_bootstrap_servers or 'kafka-server' in kafka_bootstrap_servers:
        print(f'⚠️  检测到 Kafka 配置使用容器名，强制覆盖为 localhost:9092（VIDEO服务使用 host 网络模式）')
        kafka_bootstrap_servers = 'localhost:9092'
    app.config['KAFKA_BOOTSTRAP_SERVERS'] = kafka_bootstrap_servers
    app.config['KAFKA_ALERT_TOPIC'] = os.environ.get('KAFKA_ALERT_TOPIC', 'iot-alert-notification')
    app.config['KAFKA_ALERT_NOTIFICATION_TOPIC'] = os.environ.get('KAFKA_ALERT_NOTIFICATION_TOPIC', 'iot-alert-notification')
    app.config['KAFKA_SNAPSHOT_ALERT_TOPIC'] = os.environ.get('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
    app.config['KAFKA_FACE_MATCHING_TOPIC'] = os.environ.get('KAFKA_FACE_MATCHING_TOPIC', 'iot-face-matching')
    app.config['KAFKA_FACE_MATCHING_RESULT_TOPIC'] = os.environ.get('KAFKA_FACE_MATCHING_RESULT_TOPIC', 'iot-face-matching-result')
    app.config['KAFKA_PLATE_MATCHING_TOPIC'] = os.environ.get('KAFKA_PLATE_MATCHING_TOPIC', 'iot-plate-matching')
    app.config['KAFKA_PLATE_MATCHING_RESULT_TOPIC'] = os.environ.get('KAFKA_PLATE_MATCHING_RESULT_TOPIC', 'iot-plate-matching-result')
    app.config['KAFKA_REQUEST_TIMEOUT_MS'] = int(os.environ.get('KAFKA_REQUEST_TIMEOUT_MS', '5000'))
    app.config['KAFKA_RETRIES'] = int(os.environ.get('KAFKA_RETRIES', '1'))
    app.config['KAFKA_RETRY_BACKOFF_MS'] = int(os.environ.get('KAFKA_RETRY_BACKOFF_MS', '100'))
    app.config['KAFKA_METADATA_MAX_AGE_MS'] = int(os.environ.get('KAFKA_METADATA_MAX_AGE_MS', '300000'))
    app.config['KAFKA_INIT_RETRY_INTERVAL'] = int(os.environ.get('KAFKA_INIT_RETRY_INTERVAL', '60'))
    app.config['MEDIA_UPLOAD_MODE'] = os.environ.get('MEDIA_UPLOAD_MODE', 'sync')
    app.config['MEDIA_KAFKA_DVR_TOPIC'] = os.environ.get('MEDIA_KAFKA_DVR_TOPIC', 'media.dvr.completed')
    app.config['MEDIA_HOST_DATA_ROOT'] = os.environ.get('MEDIA_HOST_DATA_ROOT', '/mnt/easyaiot-media')
    app.config['MEDIA_RECORD_DIR'] = os.environ.get('MEDIA_RECORD_DIR', '')
    app.config['MEDIA_SNAP_DIR'] = os.environ.get('MEDIA_SNAP_DIR', '')
    app.config['MEDIA_SNAP_UPLOAD_MODE'] = os.environ.get('MEDIA_SNAP_UPLOAD_MODE', '')
    app.config['MEDIA_KAFKA_SNAP_TOPIC'] = os.environ.get('MEDIA_KAFKA_SNAP_TOPIC', 'media.snap.completed')

    try:
        from cluster_storage import apply_cluster_env_defaults, ensure_cluster_dirs, is_cluster_mode
        applied = apply_cluster_env_defaults()
        if applied:
            print(f'✅ 集群存储环境已应用: {", ".join(applied.keys())}')
        if is_cluster_mode():
            ensure_cluster_dirs()
            app.config['CLUSTER_MODE'] = True
            app.config['MEDIA_HOST_DATA_ROOT'] = os.environ.get('MEDIA_HOST_DATA_ROOT', '/mnt/easyaiot-media')
            app.config['MEDIA_RECORD_DIR'] = os.environ.get('MEDIA_RECORD_DIR', '')
            app.config['MEDIA_SNAP_DIR'] = os.environ.get('MEDIA_SNAP_DIR', '')
            app.config['MEDIA_UPLOAD_MODE'] = os.environ.get('MEDIA_UPLOAD_MODE', 'kafka')
    except ImportError:
        pass

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
            from models import (
                Device, Image, DeviceDirectory, Nvr, SnapSpace, SnapTask, DetectionRegion,
                AlgorithmModelService, RegionModelService, DeviceStorageConfig, Playback,
                RecordSpace,                 AlgorithmTask, FrameExtractor, Sorter, Pusher, DeviceDetectionRegion,
                DeviceTrackSession, DeviceTrackPoint, PatrolSession, AlgorithmPostProcessResult,
            )
            db.create_all()
            from models import (
                ensure_algorithm_task_sam_columns,
                ensure_algorithm_task_pose_columns,
                ensure_algorithm_task_pose_intent_columns,
                ensure_algorithm_task_post_process_columns,
                ensure_algorithm_task_alert_class_columns,
                ensure_algorithm_task_detect_conf_column,
                ensure_algorithm_task_executor_columns,
                ensure_stream_forward_task_executor_columns,
            )
            ensure_algorithm_task_sam_columns(db.engine)
            ensure_algorithm_task_pose_columns(db.engine)
            ensure_algorithm_task_pose_intent_columns(db.engine)
            ensure_algorithm_task_post_process_columns(db.engine)
            ensure_algorithm_task_alert_class_columns(db.engine)
            ensure_algorithm_task_detect_conf_column(db.engine)
            ensure_algorithm_task_executor_columns(db.engine)
            ensure_stream_forward_task_executor_columns(db.engine)
            
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
                
                # 检查 device 表的 auto_snap_enabled 列是否存在
                result = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'device' 
                        AND column_name = 'auto_snap_enabled'
                    );
                """))
                auto_snap_enabled_exists = result.scalar()
                
                if not auto_snap_enabled_exists:
                    print("⚠️  device.auto_snap_enabled 列不存在，正在添加...")
                    # 添加 auto_snap_enabled 列，默认值为 false
                    db.session.execute(text("""
                        ALTER TABLE device 
                        ADD COLUMN auto_snap_enabled BOOLEAN NOT NULL DEFAULT FALSE;
                    """))
                    db.session.commit()
                    print("✅ device.auto_snap_enabled 列添加成功")
                
                # 检查 device 表的 cover_image_path 列是否存在
                result = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'device' 
                        AND column_name = 'cover_image_path'
                    );
                """))
                cover_image_path_exists = result.scalar()
                
                if not cover_image_path_exists:
                    print("⚠️  device.cover_image_path 列不存在，正在添加...")
                    db.session.execute(text("""
                        ALTER TABLE device 
                        ADD COLUMN cover_image_path VARCHAR(500);
                    """))
                    db.session.commit()
                    print("✅ device.cover_image_path 列添加成功")

                # nvr 表及扩展字段
                result = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'nvr'
                    );
                """))
                if not result.scalar():
                    print("⚠️  nvr 表不存在，正在创建...")
                    db.create_all()
                    print("✅ nvr 表创建成功")
                else:
                    for col_name, col_def in (
                        ('port', 'SMALLINT NOT NULL DEFAULT 80'),
                        ('vendor', 'VARCHAR(32)'),
                        ('serial_number', 'VARCHAR(300)'),
                        ('firmware_version', 'VARCHAR(100)'),
                        ('device_type', 'VARCHAR(100)'),
                        ('mac', 'VARCHAR(17)'),
                        ('scheme', 'VARCHAR(8)'),
                        ('rtsp_url', 'TEXT'),
                        ('source', 'VARCHAR(32)'),
                        ('created_at', 'TIMESTAMP WITHOUT TIME ZONE'),
                        ('updated_at', 'TIMESTAMP WITHOUT TIME ZONE'),
                    ):
                        r = db.session.execute(text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_schema = 'public'
                                AND table_name = 'nvr' AND column_name = :col
                            );
                        """), {'col': col_name})
                        if not r.scalar():
                            print(f"⚠️  nvr.{col_name} 列不存在，正在添加...")
                            db.session.execute(text(f'ALTER TABLE nvr ADD COLUMN {col_name} {col_def};'))
                            db.session.commit()
                            print(f"✅ nvr.{col_name} 列添加成功")

                for col_name, col_def in (
                    ('rtsp_direct', 'TEXT'),
                    ('channel_online', 'BOOLEAN'),
                    ('connection_status', 'VARCHAR(100)'),
                    ('longitude', 'DOUBLE PRECISION'),
                    ('latitude', 'DOUBLE PRECISION'),
                    ('altitude', 'DOUBLE PRECISION'),
                    ('address', 'VARCHAR(500)'),
                    ('location_source', 'VARCHAR(20)'),
                    ('location_updated_at', 'TIMESTAMP WITHOUT TIME ZONE'),
                    ('heading', 'DOUBLE PRECISION'),
                    ('ptz_type', 'SMALLINT'),
                    ('direction_type', 'SMALLINT'),
                    ('position_type', 'SMALLINT'),
                    ('room_type', 'SMALLINT'),
                    ('use_type', 'SMALLINT'),
                    ('supply_light_type', 'SMALLINT'),
                    ('resolution', 'VARCHAR(100)'),
                    ('skylink_token', 'TEXT'),
                ):
                    r = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_schema = 'public'
                            AND table_name = 'device' AND column_name = :col
                        );
                    """), {'col': col_name})
                    if not r.scalar():
                        print(f"⚠️  device.{col_name} 列不存在，正在添加...")
                        db.session.execute(text(f'ALTER TABLE device ADD COLUMN {col_name} {col_def};'))
                        db.session.commit()
                        print(f"✅ device.{col_name} 列添加成功")
                
                # 检查 device_detection_region 表是否存在
                result = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'device_detection_region'
                    );
                """))
                device_detection_region_exists = result.scalar()
                
                if not device_detection_region_exists:
                    print("⚠️  device_detection_region 表不存在，正在创建...")
                    db.create_all()  # 这会创建所有缺失的表
                    print("✅ device_detection_region 表创建成功")
                
                # 检查 device_detection_region 表的 model_ids 列是否存在
                if device_detection_region_exists:
                    result = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'device_detection_region' 
                            AND column_name = 'model_ids'
                        );
                    """))
                    model_ids_exists = result.scalar()
                    
                    if not model_ids_exists:
                        print("⚠️  device_detection_region.model_ids 列不存在，正在添加...")
                        db.session.execute(text("""
                            ALTER TABLE device_detection_region 
                            ADD COLUMN model_ids TEXT;
                        """))
                        db.session.commit()
                        print("✅ device_detection_region.model_ids 列添加成功")

                # 轨迹回放表：device_track_session / device_track_point
                for track_table in ('device_track_session', 'device_track_point'):
                    r = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = :tbl
                        );
                    """), {'tbl': track_table})
                    if not r.scalar():
                        print(f"⚠️  {track_table} 表不存在，正在创建...")
                        db.create_all()
                        print(f"✅ {track_table} 表创建成功")

                # NVR / GB28181 分组存储策略表
                group_policy_table = 'space_group_save_policy'
                r = db.session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = :tbl
                    );
                """), {'tbl': group_policy_table})
                if not r.scalar():
                    print(f"⚠️  {group_policy_table} 表不存在，正在创建...")
                    db.create_all()
                    print(f"✅ {group_policy_table} 表创建成功")

                # 目录/空间保存时间字段
                for table_name, col_name, col_def in (
                    ('device_directory', 'snap_save_time', 'INTEGER NOT NULL DEFAULT 1'),
                    ('device_directory', 'record_save_time', 'INTEGER NOT NULL DEFAULT 1'),
                    ('snap_space', 'save_time_custom', 'BOOLEAN NOT NULL DEFAULT FALSE'),
                    ('record_space', 'save_time_custom', 'BOOLEAN NOT NULL DEFAULT FALSE'),
                ):
                    r = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_schema = 'public'
                            AND table_name = :tbl AND column_name = :col
                        );
                    """), {'tbl': table_name, 'col': col_name})
                    if not r.scalar():
                        print(f"⚠️  {table_name}.{col_name} 列不存在，正在添加...")
                        db.session.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def};'))
                        db.session.commit()
                        print(f"✅ {table_name}.{col_name} 列添加成功")

                if directory_id_exists and auto_snap_enabled_exists and cover_image_path_exists and device_detection_region_exists:
                    print("✅ 数据库迁移检查完成，所有列和表已存在")

                try:
                    from app.services.camera_service import sync_unassigned_devices_to_default_directory
                    synced = sync_unassigned_devices_to_default_directory()
                    print(f"✅ 默认分组已就绪（已归入未分配设备 {synced} 台）")
                except Exception as default_dir_err:
                    print(f"⚠️  初始化默认分组失败: {default_dir_err}")
                
                # 检查 algorithm_task 表的新字段
                try:
                    # 检查 task_type 字段
                    result = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'algorithm_task' 
                            AND column_name = 'task_type'
                        );
                    """))
                    task_type_exists = result.scalar()
                    
                    if not task_type_exists:
                        print("⚠️  algorithm_task.task_type 列不存在，正在添加...")
                        db.session.execute(text("""
                            ALTER TABLE algorithm_task 
                            ADD COLUMN task_type VARCHAR(20) NOT NULL DEFAULT 'realtime';
                        """))
                        db.session.commit()
                        print("✅ algorithm_task.task_type 列添加成功")
                    
                    # 检查其他新增字段
                    for col_name, col_def in [
                        ('space_id', 'INTEGER REFERENCES snap_space(id) ON DELETE CASCADE'),
                        ('cron_expression', 'VARCHAR(255)'),
                        ('frame_skip', 'INTEGER NOT NULL DEFAULT 1'),
                        ('total_captures', 'INTEGER NOT NULL DEFAULT 0'),
                        ('last_capture_time', 'TIMESTAMP'),
                        ('face_detection_enabled', 'BOOLEAN NOT NULL DEFAULT TRUE'),
                        ('plate_detection_enabled', 'BOOLEAN NOT NULL DEFAULT TRUE'),
                        ('face_matching_enabled', 'BOOLEAN NOT NULL DEFAULT FALSE'),
                        ('face_library_id', 'INTEGER REFERENCES face_library(id) ON DELETE SET NULL'),
                        ('face_matching_threshold', 'DOUBLE PRECISION'),
                        ('plate_matching_enabled', 'BOOLEAN NOT NULL DEFAULT FALSE'),
                        ('plate_library_id', 'INTEGER REFERENCES plate_library(id) ON DELETE SET NULL'),
                        ('face_library_ids', 'TEXT'),
                        ('plate_library_ids', 'TEXT'),
                        ('matching_business_tags', 'TEXT'),
                        ('alert_event_suppress_time', 'INTEGER NOT NULL DEFAULT 5'),
                        ('service_server_ip', 'VARCHAR(512)'),
                        ('service_port', 'INTEGER'),
                        ('service_process_id', 'INTEGER'),
                        ('service_last_heartbeat', 'TIMESTAMP'),
                        ('service_log_path', 'VARCHAR(500)'),
                        ('schedule_policy', "VARCHAR(20) NOT NULL DEFAULT 'local'"),
                        ('prefer_gpu', 'BOOLEAN NOT NULL DEFAULT TRUE'),
                        ('target_node_id', 'BIGINT'),
                        ('node_id', 'BIGINT'),
                        ('device_deployments', 'TEXT'),
                    ]:
                        result = db.session.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_schema = 'public' 
                                AND table_name = 'algorithm_task' 
                                AND column_name = '{col_name}'
                            );
                        """))
                        col_exists = result.scalar()
                        
                        if not col_exists:
                            print(f"⚠️  algorithm_task.{col_name} 列不存在，正在添加...")
                            db.session.execute(text(f"""
                                ALTER TABLE algorithm_task 
                                ADD COLUMN {col_name} {col_def};
                            """))
                            db.session.commit()
                            print(f"✅ algorithm_task.{col_name} 列添加成功")

                    # 与边缘节点字段级隔离：algorithm_task 不再持有 edge_node_*
                    for drop_col in ('edge_node_id', 'edge_node_name', 'edge_node_host'):
                        result = db.session.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_schema = 'public'
                                AND table_name = 'algorithm_task'
                                AND column_name = '{drop_col}'
                            );
                        """))
                        if result.scalar():
                            print(f"⚠️  移除 algorithm_task.{drop_col}（与边缘节点隔离）...")
                            db.session.execute(text(
                                f'ALTER TABLE algorithm_task DROP COLUMN IF EXISTS {drop_col};'
                            ))
                            db.session.commit()
                            print(f"✅ algorithm_task.{drop_col} 已删除")

                    print("✅ algorithm_task 表迁移检查完成")
                except Exception as e:
                    print(f"⚠️  algorithm_task 表迁移检查失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()

                # stream_forward_task 节点调度字段
                try:
                    for col_name, col_def in [
                        ('schedule_policy', "VARCHAR(20) NOT NULL DEFAULT 'local'"),
                        ('prefer_gpu', 'BOOLEAN NOT NULL DEFAULT TRUE'),
                        ('target_node_id', 'BIGINT'),
                        ('node_id', 'BIGINT'),
                        ('device_deployments', 'TEXT'),
                    ]:
                        result = db.session.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_schema = 'public'
                                AND table_name = 'stream_forward_task'
                                AND column_name = '{col_name}'
                            );
                        """))
                        col_exists = result.scalar()
                        if not col_exists:
                            print(f"⚠️  stream_forward_task.{col_name} 列不存在，正在添加...")
                            db.session.execute(text(f"""
                                ALTER TABLE stream_forward_task
                                ADD COLUMN {col_name} {col_def};
                            """))
                            db.session.commit()
                            print(f"✅ stream_forward_task.{col_name} 列添加成功")
                    print("✅ stream_forward_task 表迁移检查完成")
                except Exception as e:
                    print(f"⚠️  stream_forward_task 表迁移检查失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()
                
                # 检查 alert 表的 task_type 字段
                try:
                    result = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'alert' 
                            AND column_name = 'task_type'
                        );
                    """))
                    alert_task_type_exists = result.scalar()
                    
                    if not alert_task_type_exists:
                        print("⚠️  alert.task_type 列不存在，正在添加...")
                        db.session.execute(text("""
                            ALTER TABLE alert 
                            ADD COLUMN task_type VARCHAR(20) NULL;
                        """))
                        db.session.commit()
                        print("✅ alert.task_type 列添加成功")
                        
                        # 尝试从 information 字段中提取 task_type 并填充（兼容旧数据）
                        try:
                            # 使用 PostgreSQL 的 JSON 函数提取 task_type
                            db.session.execute(text("""
                                UPDATE alert 
                                SET task_type = (
                                    CASE 
                                        WHEN information IS NOT NULL 
                                             AND information::text LIKE '%"task_type"%' 
                                             AND information::text LIKE '%"realtime"%' THEN 'realtime'
                                        WHEN information IS NOT NULL 
                                             AND information::text LIKE '%"task_type"%' 
                                             AND (information::text LIKE '%"snap"%' OR information::text LIKE '%"snapshot"%') THEN 'snap'
                                        ELSE 'realtime'
                                    END
                                )
                                WHERE task_type IS NULL;
                            """))
                            db.session.commit()
                            print("✅ 已从 information 字段迁移 task_type 数据")
                        except Exception as e:
                            print(f"⚠️  迁移 task_type 数据失败（不影响功能）: {str(e)}")
                            db.session.rollback()
                            
                            # 如果迁移失败，至少设置默认值
                            try:
                                db.session.execute(text("""
                                    UPDATE alert 
                                    SET task_type = 'realtime'
                                    WHERE task_type IS NULL;
                                """))
                                db.session.commit()
                                print("✅ 已设置默认 task_type 值")
                            except:
                                pass
                    
                    # MinIO 告警图 URL、任务关联字段（与 models.Alert 一致；旧库缺列会导致列表/统计查询失败）
                    for col_name, col_def in [
                        ('image_url', 'VARCHAR(500)'),
                        ('task_id', 'INTEGER'),
                        ('task_name', 'VARCHAR(255)'),
                        ('business_tags', 'TEXT'),
                        ('edge_node_id', 'BIGINT'),
                        ('edge_node_name', 'VARCHAR(128)'),
                        ('edge_node_host', 'VARCHAR(128)'),
                        ('node_id', 'BIGINT'),
                    ]:
                        result = db.session.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_schema = 'public'
                                AND table_name = 'alert'
                                AND column_name = '{col_name}'
                            );
                        """))
                        if not result.scalar():
                            print(f"⚠️  alert.{col_name} 列不存在，正在添加...")
                            db.session.execute(text(f"""
                                ALTER TABLE alert
                                ADD COLUMN {col_name} {col_def} NULL;
                            """))
                            db.session.commit()
                            print(f"✅ alert.{col_name} 列添加成功")

                    print("✅ alert 表迁移检查完成")
                except Exception as e:
                    print(f"⚠️  alert 表迁移检查失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()

                # correlation_id：同一帧算法告警 / 人脸匹配 / 车牌匹配关联
                try:
                    for tbl in ('alert', 'face_match_record', 'plate_match_record'):
                        result = db.session.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_schema = 'public'
                                AND table_name = '{tbl}'
                                AND column_name = 'correlation_id'
                            );
                        """))
                        if not result.scalar():
                            print(f"⚠️  {tbl}.correlation_id 列不存在，正在添加...")
                            db.session.execute(text(f"""
                                ALTER TABLE {tbl}
                                ADD COLUMN correlation_id VARCHAR(36) NULL;
                            """))
                            db.session.commit()
                            print(f"✅ {tbl}.correlation_id 列添加成功")
                        db.session.execute(text(f"""
                            CREATE INDEX IF NOT EXISTS idx_{tbl}_correlation_id
                            ON {tbl} (correlation_id);
                        """))
                        db.session.commit()
                    print("✅ correlation_id 关联字段迁移检查完成")
                except Exception as e:
                    print(f"⚠️  correlation_id 迁移检查失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()

                # alert.time：列表排序、今日统计、时间范围筛选
                try:
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_alert_time
                        ON alert (time DESC);
                    """))
                    db.session.commit()
                    print("✅ alert.time 索引检查完成")
                except Exception as e:
                    print(f"⚠️  alert.time 索引检查失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()

                # GB28181 等设备 ID 超过原 VARCHAR(30)，会导致 iot-sink 写入 alert 失败，前端告警列表为空
                try:
                    widen_specs = [
                        ('alert', 'device_id', 100),
                        ('alert', 'device_name', 100),
                        ('playback', 'device_id', 100),
                        ('playback', 'device_name', 100),
                        ('playback', 'file_path', 500),
                        ('playback', 'thumbnail_path', 500),
                        ('stream_forward_task', 'service_server_ip', 512),
                        ('algorithm_task', 'service_server_ip', 512),
                    ]
                    for tbl, col, target_len in widen_specs:
                        result = db.session.execute(text("""
                            SELECT character_maximum_length
                            FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = :t
                              AND column_name = :c
                        """), {'t': tbl, 'c': col})
                        row = result.fetchone()
                        if row is None:
                            continue
                        cur = row[0]
                        if cur is not None and cur < target_len:
                            print(f"⚠️  {tbl}.{col} 当前长度 {cur}，正在扩展为 VARCHAR({target_len})...")
                            db.session.execute(text(
                                f'ALTER TABLE {tbl} ALTER COLUMN {col} TYPE VARCHAR({target_len})'
                            ))
                            db.session.commit()
                            print(f"✅ {tbl}.{col} 扩展成功")
                    print("✅ alert/playback 字符列长度检查完成（GB28181 长设备 ID / MinIO URL）")
                except Exception as e:
                    print(f"⚠️  alert/playback 字符列扩展失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()

                # algorithm_task 巡检字段 & patrol_session 表
                try:
                    for col_name, col_def in (
                        ('patrol_mode', "VARCHAR(20) DEFAULT 'pool'"),
                        ('patrol_interval_sec', 'INTEGER DEFAULT 10'),
                        ('patrol_pool_size', 'INTEGER DEFAULT 4'),
                        ('focus_device_id', 'VARCHAR(100)'),
                    ):
                        result = db.session.execute(text("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns
                                WHERE table_schema = 'public'
                                  AND table_name = 'algorithm_task'
                                  AND column_name = :c
                            );
                        """), {'c': col_name})
                        if not result.scalar():
                            print(f"⚠️  algorithm_task.{col_name} 列不存在，正在添加...")
                            db.session.execute(text(
                                f'ALTER TABLE algorithm_task ADD COLUMN {col_name} {col_def};'
                            ))
                            db.session.commit()
                            print(f"✅ algorithm_task.{col_name} 添加成功")
                    result = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_name = 'patrol_session'
                        );
                    """))
                    if not result.scalar():
                        print("⚠️  patrol_session 表不存在，正在创建...")
                        db.create_all()
                        print("✅ patrol_session 表创建成功")
                    print("✅ 巡检相关数据库结构检查完成")
                except Exception as e:
                    print(f"⚠️  巡检数据库迁移失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()

                # face_person 归一化人员表 & face_entry.person_id
                try:
                    result = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_name = 'face_person'
                        );
                    """))
                    if not result.scalar():
                        print("⚠️  face_person 表不存在，正在创建...")
                        db.create_all()
                        print("✅ face_person 表创建成功")

                    result = db.session.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_schema = 'public'
                              AND table_name = 'face_entry'
                              AND column_name = 'person_id'
                        );
                    """))
                    if not result.scalar():
                        print("⚠️  face_entry.person_id 列不存在，正在添加...")
                        db.session.execute(text("""
                            ALTER TABLE face_entry
                            ADD COLUMN person_id INTEGER REFERENCES face_person(id) ON DELETE CASCADE;
                        """))
                        db.session.commit()
                        print("✅ face_entry.person_id 列添加成功")

                    from app.services import face_library_service as _face_lib_svc
                    libs = db.session.execute(text("SELECT id FROM face_library")).fetchall()
                    for (lib_id,) in libs:
                        _face_lib_svc.ensure_person_records(int(lib_id))
                    print("✅ 人脸归一化人员数据迁移检查完成")
                except Exception as e:
                    print(f"⚠️  人脸归一化表迁移失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()
                
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
        from app.blueprints import audio_talk
        app.register_blueprint(audio_talk.audio_talk_bp, url_prefix='/video/camera/audio/talk')
        print(f"✅ Audio Talk Blueprint 注册成功")
    except Exception as e:
        print(f"⚠️  Audio Talk Blueprint 注册失败: {str(e)}")

    try:
        from app.blueprints import media_hook
        app.register_blueprint(media_hook.media_hook_bp, url_prefix='/video/media')
        print(f"✅ Media Hook Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Media Hook Blueprint 注册失败: {str(e)}")
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
    
    try:
        app.register_blueprint(algorithm_task.algorithm_task_bp, url_prefix='/video/algorithm')
        print(f"✅ Algorithm Task Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Algorithm Task Blueprint 注册失败: {str(e)}")

    try:
        from app.blueprints import patrol
        app.register_blueprint(patrol.patrol_bp, url_prefix='/video/patrol')
        print(f"✅ Patrol Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Patrol Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    try:
        app.register_blueprint(stream_forward.stream_forward_bp, url_prefix='/video/stream-forward')
        print(f"✅ Stream Forward Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Algorithm Task Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()

    try:
        app.register_blueprint(face.face_bp, url_prefix='/video/face')
        print(f"✅ Face Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Face Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()

    try:
        from app.blueprints import plate
        app.register_blueprint(plate.plate_bp, url_prefix='/video/plate')
        print(f"✅ Plate Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Plate Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()

    try:
        from app.blueprints import scenario_pose
        app.register_blueprint(scenario_pose.scenario_pose_bp, url_prefix='/video/scenario-pose')
        print(f"✅ Scenario Pose Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Scenario Pose Blueprint 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()

    try:
        from app.blueprints import device_detection_region
        app.register_blueprint(device_detection_region.device_detection_region_bp, url_prefix='/video/device-detection')
        print(f"✅ Device Detection Region Blueprint 注册成功")
    except Exception as e:
        print(f"❌ Device Detection Region Blueprint 注册失败: {str(e)}")
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

    if start_background_tasks is None:
        skip = os.getenv('VIDEO_SKIP_BACKGROUND_TASKS', '').strip().lower()
        start_background_tasks = skip not in ('1', 'true', 'yes', 'on')

    if start_background_tasks:
        try:
            from app.services.srs_container_guard_service import maybe_fix_srs_on_startup
            maybe_fix_srs_on_startup()
        except Exception as e:
            logger.warning('SRS 启动自检失败（可忽略）: %s', e)

        # 本地 IDEA / run.py：缺失 RUNTIME 时默认自动编译（容器内跳过）
        try:
            from app.services.runtime_config_service import ensure_runtime_on_video_startup
            ensure_runtime_on_video_startup()
        except Exception as e:
            logger.warning('RUNTIME 启动自检失败（可忽略，executor=python 仍可用）: %s', e)

    if not start_background_tasks:
        return app

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
        
        # 停止自动抽帧线程
        try:
            from app.services.auto_frame_extraction_service import stop_auto_frame_extraction
            stop_auto_frame_extraction()
        except Exception as e:
            print(f"❌ 停止自动抽帧线程失败: {str(e)}")

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
        from app.services.camera_service import (
            _start_search,
            scheduler,
        )
        _start_search(app)
        # 安全关闭所有任务 worker 守护进程（算法 + 推流转发）
        def safe_shutdown_daemons():
            try:
                from app.services.algorithm_task_launcher_service import stop_all_daemons as stop_algorithm_daemons
                stop_algorithm_daemons()
                print('✅ 所有算法任务守护进程已安全关闭')
            except Exception as e:
                print(f'⚠️  关闭算法守护进程时出错: {str(e)}')
            try:
                from app.services.stream_forward_launcher_service import stop_all_daemons as stop_stream_forward_daemons
                stop_stream_forward_daemons()
                print('✅ 所有推流转发 worker 已安全关闭')
            except Exception as e:
                print(f'⚠️  关闭推流转发 worker 时出错: {str(e)}')
        atexit.register(safe_shutdown_daemons)

    # 应用启动后自动启动需要推流的设备
    with app.app_context():
        try:
            from app.blueprints.camera import auto_start_streaming
            auto_start_streaming()
        except Exception as e:
            print(f"❌ 自动启动推流设备失败: {str(e)}")
    
    # 启动抓拍/录像空间自动清理任务
    with app.app_context():
        # 周期任务通用参数：合并错过的触发、避免并发堆积
        _interval_job_kwargs = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 30,
        }

        try:
            from app.services.camera_service import ensure_scheduler_running, scheduler
            from app.services.snap_space_service import auto_cleanup_all_spaces
            
            ensure_scheduler_running()
            
            # 创建包装函数，确保在应用上下文中执行
            def cleanup_wrapper():
                """包装函数，确保传入app参数"""
                return auto_cleanup_all_spaces(app=app)
            
            # 每 30 分钟执行自动清理（默认保留 1 小时时需及时删除过期文件）
            scheduler.add_job(
                cleanup_wrapper,
                'interval',
                minutes=30,
                id='auto_cleanup_snap_spaces',
                replace_existing=True,
                **_interval_job_kwargs,
            )
            print('✅ 抓拍空间自动清理任务已启动（每 30 分钟执行）')

            from app.services.record_space_service import auto_cleanup_all_record_spaces

            def record_cleanup_wrapper():
                return auto_cleanup_all_record_spaces(app=app)

            scheduler.add_job(
                record_cleanup_wrapper,
                'interval',
                minutes=30,
                id='auto_cleanup_record_spaces',
                replace_existing=True,
                **_interval_job_kwargs,
            )
            print('✅ 录像空间自动清理任务已启动（每 30 分钟执行）')
            try:
                snap_boot = cleanup_wrapper()
                print(f'✅ 抓拍空间启动清理完成: {snap_boot}')
            except Exception as boot_snap_err:
                print(f'⚠️ 抓拍空间启动清理失败: {boot_snap_err}')
            try:
                record_boot = record_cleanup_wrapper()
                print(f'✅ 录像空间启动清理完成: {record_boot}')
            except Exception as boot_record_err:
                print(f'⚠️ 录像空间启动清理失败: {boot_record_err}')
        except Exception as e:
            print(f"❌ 启动空间自动清理任务失败: {str(e)}")
            import traceback
            traceback.print_exc()

        # SRS 本地回放磁盘守护（默认每 10 分钟；磁盘紧张时可配合紧急阈值自动删最旧文件）
        try:
            from app.services.playback_disk_guard_service import run_playback_disk_guard

            guard_interval_min = int(os.getenv('PLAYBACK_GUARD_INTERVAL_MINUTES', '10'))

            def playback_disk_guard_wrapper():
                with app.app_context():
                    return run_playback_disk_guard()

            scheduler.add_job(
                playback_disk_guard_wrapper,
                'interval',
                minutes=guard_interval_min,
                id='playback_disk_guard',
                replace_existing=True,
                **_interval_job_kwargs,
            )
            print(f'✅ SRS回放磁盘守护任务已启动（每 {guard_interval_min} 分钟执行）')
            try:
                playback_disk_guard_wrapper()
                print('✅ SRS回放磁盘守护已执行启动时首次清理')
            except Exception as boot_guard_err:
                print(f'⚠️ SRS回放磁盘守护启动清理失败: {boot_guard_err}')
        except Exception as e:
            print(f'❌ 启动SRS回放磁盘守护任务失败: {str(e)}')
            import traceback
            traceback.print_exc()

        # 媒体 Janitor：孤儿 DVR/抓拍重入队 + 磁盘紧急保护
        try:
            from app.services.media_janitor_service import is_janitor_enabled, run_janitor_cycle

            if is_janitor_enabled():
                janitor_interval = int(os.getenv('JANITOR_INTERVAL_SECONDS', '60'))

                def media_janitor_wrapper():
                    with app.app_context():
                        return run_janitor_cycle()

                scheduler.add_job(
                    media_janitor_wrapper,
                    'interval',
                    seconds=janitor_interval,
                    id='media_janitor',
                    replace_existing=True,
                    **_interval_job_kwargs,
                )
                print(f'✅ 媒体 Janitor 已启动（每 {janitor_interval} 秒）')
        except Exception as e:
            print(f'❌ 启动媒体 Janitor 失败: {str(e)}')
            import traceback
            traceback.print_exc()

        # 推流转发集群健康监控：离线节点分片迁移
        try:
            from app.services.stream_forward_health_service import (
                is_health_monitor_enabled,
                run_stream_forward_health_cycle,
            )

            if is_health_monitor_enabled():
                health_interval = int(os.getenv('STREAM_FORWARD_HEALTH_INTERVAL_SECONDS', '60'))

                def stream_forward_health_wrapper():
                    with app.app_context():
                        return run_stream_forward_health_cycle()

                scheduler.add_job(
                    stream_forward_health_wrapper,
                    'interval',
                    seconds=health_interval,
                    id='stream_forward_health',
                    replace_existing=True,
                    **_interval_job_kwargs,
                )
                print(f'✅ 推流转发健康监控已启动（每 {health_interval} 秒）')
        except Exception as e:
            print(f'❌ 启动推流转发健康监控失败: {str(e)}')
            import traceback
            traceback.print_exc()

        # 算法任务健康监控：守护进程退出 / 心跳超时后重新拉起
        try:
            from app.services.algorithm_task_health_service import (
                is_health_monitor_enabled as is_algorithm_health_enabled,
                run_algorithm_task_health_cycle,
            )

            if is_algorithm_health_enabled():
                algorithm_health_interval = int(os.getenv('ALGORITHM_HEALTH_INTERVAL_SECONDS', '60'))

                def algorithm_task_health_wrapper():
                    with app.app_context():
                        return run_algorithm_task_health_cycle()

                scheduler.add_job(
                    algorithm_task_health_wrapper,
                    'interval',
                    seconds=algorithm_health_interval,
                    id='algorithm_task_health',
                    replace_existing=True,
                    **_interval_job_kwargs,
                )
                print(f'✅ 算法任务健康监控已启动（每 {algorithm_health_interval} 秒）')
        except Exception as e:
            print(f'❌ 启动算法任务健康监控失败: {str(e)}')
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
        
        # 启动自动抽帧线程（每分钟从所有在线摄像头的RTSP流中抽帧）
        # 已禁用：由算法任务来处理抽帧，不再单独启动自动抽帧
        # try:
        #     from app.services.auto_frame_extraction_service import start_auto_frame_extraction
        #     start_auto_frame_extraction(app)
        #     print("✅ 自动抽帧线程启动成功（每分钟执行一次）")
        # except Exception as e:
        #     print(f"❌ 启动自动抽帧线程失败: {str(e)}")
        #     import traceback
        #     traceback.print_exc()
        
        # 启动心跳超时检查任务（每分钟检查一次）
        try:
            from app.services.camera_service import ensure_scheduler_running, scheduler
            from models import FrameExtractor, Sorter, Pusher
            
            ensure_scheduler_running()
            
            def check_heartbeat_timeout():
                """定时检查心跳超时，超过1分钟没上报则更新状态为stopped"""
                try:
                    with app.app_context():
                        from datetime import datetime, timedelta
                        from models import db, AlgorithmTask
                        from sqlalchemy.exc import OperationalError, DisconnectionError
                        
                        timeout_threshold = datetime.utcnow() - timedelta(minutes=1)
                        
                        try:
                            # 检查抽帧器
                            timeout_extractors = FrameExtractor.query.filter(
                                FrameExtractor.status.in_(['running']),
                                (FrameExtractor.last_heartbeat < timeout_threshold) | (FrameExtractor.last_heartbeat.is_(None))
                            ).all()
                            
                            for extractor in timeout_extractors:
                                old_status = extractor.status
                                extractor.status = 'stopped'
                                logger.info(f"抽帧器心跳超时，状态从 {old_status} 更新为 stopped: {extractor.extractor_name}")
                            
                            # 检查排序器
                            timeout_sorters = Sorter.query.filter(
                                Sorter.status.in_(['running']),
                                (Sorter.last_heartbeat < timeout_threshold) | (Sorter.last_heartbeat.is_(None))
                            ).all()
                            
                            for sorter in timeout_sorters:
                                old_status = sorter.status
                                sorter.status = 'stopped'
                                logger.info(f"排序器心跳超时，状态从 {old_status} 更新为 stopped: {sorter.sorter_name}")
                            
                            # 检查推送器
                            timeout_pushers = Pusher.query.filter(
                                Pusher.status.in_(['running']),
                                (Pusher.last_heartbeat < timeout_threshold) | (Pusher.last_heartbeat.is_(None))
                            ).all()
                            
                            for pusher in timeout_pushers:
                                old_status = pusher.status
                                pusher.status = 'stopped'
                                logger.info(f"推送器心跳超时，状态从 {old_status} 更新为 stopped: {pusher.pusher_name}")
                            
                            # 检查算法任务（实时算法任务）
                            timeout_algorithm_tasks = AlgorithmTask.query.filter(
                                AlgorithmTask.run_status.in_(['running', 'restarting']),
                                AlgorithmTask.task_type == 'realtime',
                                ((AlgorithmTask.service_last_heartbeat < timeout_threshold) | (AlgorithmTask.service_last_heartbeat.is_(None)))
                            ).all()
                            
                            for task in timeout_algorithm_tasks:
                                old_status = task.run_status
                                task.run_status = 'stopped'
                                logger.info(f"算法任务心跳超时，状态从 {old_status} 更新为 stopped: task_id={task.id}, task_name={task.task_name}")
                            
                            if timeout_extractors or timeout_sorters or timeout_pushers or timeout_algorithm_tasks:
                                db.session.commit()
                                total = len(timeout_extractors) + len(timeout_sorters) + len(timeout_pushers) + len(timeout_algorithm_tasks)
                                logger.info(f"已更新 {total} 个服务状态为stopped")
                            
                            # 清理已停止的进程
                            try:
                                from app.services.algorithm_task_launcher_service import cleanup_stopped_processes
                                cleanup_stopped_processes()
                            except Exception as e:
                                logger.warning(f"清理已停止的进程失败: {str(e)}")
                                
                        except (OperationalError, DisconnectionError) as db_error:
                            # 数据库连接异常，尝试回滚并记录错误
                            logger.warning(f"数据库连接异常，尝试重新连接: {str(db_error)}")
                            try:
                                db.session.rollback()
                                # 尝试重新连接
                                db.session.execute(text("SELECT 1"))
                            except Exception as reconnect_error:
                                logger.error(f"数据库重连失败: {str(reconnect_error)}")
                                # 不抛出异常，让定时任务继续运行
                except Exception as e:
                    # 记录详细错误信息，但不中断定时任务
                    logger.error(f"检查心跳超时失败: {str(e)}", exc_info=True)
                    try:
                        with app.app_context():
                            from models import db
                            db.session.rollback()
                    except:
                        pass
            
            # 每分钟执行一次心跳超时检查
            scheduler.add_job(
                check_heartbeat_timeout,
                'interval',
                minutes=1,
                id='check_heartbeat_timeout',
                replace_existing=True,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=30,
            )
            print('✅ 心跳超时检查任务已启动（每分钟执行一次）')

            # 服务重启后重置遗留的运行中自动录入任务（不自动恢复）
            from models import FaceAutoEnrollTask, PlateAutoEnrollTask, db
            face_reset = FaceAutoEnrollTask.query.filter_by(is_running=True).update({'is_running': False})
            plate_reset = PlateAutoEnrollTask.query.filter_by(is_running=True).update({'is_running': False})
            if face_reset or plate_reset:
                db.session.commit()
                print(f'ℹ️  已重置遗留自动录入任务（人脸 {face_reset}，车牌 {plate_reset}）')
        except Exception as e:
            print(f"❌ 启动心跳超时检查任务失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 自动启动所有启用的算法任务的服务
        try:
            from app.services.algorithm_task_launcher_service import auto_start_all_tasks
            auto_start_all_tasks(app)
            print("✅ 算法任务服务自动启动完成")
        except Exception as e:
            print(f"❌ 自动启动算法任务服务失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 自动启动所有启用的推流转发任务的服务
        try:
            from app.services.stream_forward_launcher_service import auto_start_all_tasks
            auto_start_all_tasks(app)
            print("✅ 推流转发任务服务自动启动完成")
        except Exception as e:
            print(f"❌ 自动启动推流转发任务服务失败: {str(e)}")
            import traceback
            traceback.print_exc()

        # 启动后立即做一次健康恢复（不等待定时任务，避免重启后长时间无推流/无 AI）
        try:
            from app.services.stream_forward_health_service import run_stream_forward_health_cycle
            sf_stats = run_stream_forward_health_cycle()
            if sf_stats.get('migrated'):
                print(f"ℹ️  推流转发启动恢复: migrated={sf_stats.get('migrated')}")
        except Exception as e:
            print(f"⚠️  推流转发启动恢复失败: {str(e)}")

        try:
            from app.services.algorithm_task_health_service import run_algorithm_task_health_cycle
            alg_recovered = run_algorithm_task_health_cycle()
            if alg_recovered:
                print(f"ℹ️  算法任务启动恢复: recovered={alg_recovered}")
        except Exception as e:
            print(f"⚠️  算法任务启动恢复失败: {str(e)}")

    # 最后注册退出钩子，确保 LIFO 下最先执行：停止监控线程与调度器
    from app.services.camera_service import register_scheduler_shutdown
    register_scheduler_shutdown()

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
    import signal

    app = create_app()
    # 从环境变量读取主机和端口配置
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 6000))

    def _graceful_shutdown(signum, frame):
        from app.services.camera_service import shutdown_background_services
        shutdown_background_services(wait=True)
        sys.exit(0)

    # Flask 启动后会覆盖信号处理，因此在 run 前注册并在退出路径上依赖 atexit
    for _sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(_sig, _graceful_shutdown)
        except Exception:
            pass
    
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
