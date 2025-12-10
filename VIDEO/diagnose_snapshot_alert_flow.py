#!/usr/bin/env python3
"""
诊断抓拍算法任务的抓拍图片流程
检查：1. 图片保存 2. Hook回调 3. Kafka发送 4. Sink订阅 5. 上传到抓拍空间

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import json
from datetime import datetime, timedelta

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, video_root)

from flask import Flask
from models import db, AlgorithmTask, Device, SnapSpace
from sqlalchemy import text

# 初始化Flask应用
app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/iot_video')
database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'pool_size': 10,
    'max_overflow': 20,
}

db.init_app(app)

def check_snapshot_algorithm_tasks():
    """检查抓拍算法任务配置"""
    print("=" * 80)
    print("1. 检查抓拍算法任务配置")
    print("=" * 80)
    
    with app.app_context():
        # 查询所有抓拍算法任务
        tasks = AlgorithmTask.query.filter_by(task_type='snap').all()
        
        if not tasks:
            print("❌ 没有找到抓拍算法任务（task_type='snap'）")
            return []
        
        print(f"✅ 找到 {len(tasks)} 个抓拍算法任务\n")
        
        task_list = []
        for task in tasks:
            print(f"任务ID: {task.id}")
            print(f"  任务名称: {task.task_name}")
            print(f"  任务类型: {task.task_type}")
            print(f"  是否启用: {task.is_enabled}")
            print(f"  告警事件启用: {task.alert_event_enabled}")
            print(f"  告警通知启用: {task.alert_notification_enabled}")
            
            # 检查关联的设备
            if task.devices:
                print(f"  关联设备数: {len(task.devices)}")
                for device in task.devices:
                    print(f"    - 设备ID: {device.id}, 设备名称: {device.name or device.id}")
            else:
                print(f"  ⚠️  没有关联的设备")
            
            print()
            task_list.append(task)
        
        return task_list


def check_snap_spaces(device_ids):
    """检查设备的抓拍空间配置"""
    print("=" * 80)
    print("2. 检查设备的抓拍空间配置")
    print("=" * 80)
    
    if not device_ids:
        print("⚠️  没有设备ID，跳过检查")
        return {}
    
    with app.app_context():
        snap_spaces = {}
        for device_id in device_ids:
            snap_space = SnapSpace.query.filter_by(device_id=device_id).first()
            if snap_space:
                print(f"✅ 设备 {device_id} 有关联的抓拍空间:")
                print(f"   空间ID: {snap_space.id}")
                print(f"   空间名称: {snap_space.space_name}")
                print(f"   空间编号: {snap_space.space_code}")
                print(f"   Bucket名称: {snap_space.bucket_name}")
                snap_spaces[device_id] = snap_space
            else:
                print(f"❌ 设备 {device_id} 没有关联的抓拍空间")
                snap_spaces[device_id] = None
        
        print()
        return snap_spaces


def check_alert_images_dir(task_id):
    """检查告警图片保存目录"""
    print("=" * 80)
    print("3. 检查告警图片保存目录")
    print("=" * 80)
    
    alert_image_dir = os.path.join(video_root, 'alert_images', f'task_{task_id}')
    
    if not os.path.exists(alert_image_dir):
        print(f"⚠️  告警图片目录不存在: {alert_image_dir}")
        print("   这可能是正常的，如果还没有产生告警图片")
    else:
        # 统计图片数量
        image_count = 0
        total_size = 0
        for root, dirs, files in os.walk(alert_image_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_count += 1
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
        
        print(f"✅ 告警图片目录存在: {alert_image_dir}")
        print(f"   图片数量: {image_count}")
        print(f"   总大小: {total_size / 1024 / 1024:.2f} MB")
        
        # 列出最近5个图片
        if image_count > 0:
            print("\n   最近5个图片:")
            images = []
            for root, dirs, files in os.walk(alert_image_dir):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        file_path = os.path.join(root, file)
                        mtime = os.path.getmtime(file_path)
                        images.append((file_path, mtime))
            
            images.sort(key=lambda x: x[1], reverse=True)
            for file_path, mtime in images[:5]:
                rel_path = os.path.relpath(file_path, alert_image_dir)
                size = os.path.getsize(file_path)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"     - {rel_path} ({size / 1024:.2f} KB, {mtime_str})")
    
    print()


def check_kafka_config():
    """检查Kafka配置"""
    print("=" * 80)
    print("4. 检查Kafka配置")
    print("=" * 80)
    
    kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    kafka_snapshot_alert_topic = os.getenv('KAFKA_SNAPSHOT_ALERT_TOPIC', 'iot-snapshot-alert')
    
    print(f"Kafka服务器: {kafka_bootstrap_servers}")
    print(f"抓拍告警主题: {kafka_snapshot_alert_topic}")
    print()


def check_recent_alerts(device_ids, hours=24):
    """检查最近的告警记录"""
    print("=" * 80)
    print("5. 检查最近的告警记录（最近{}小时）".format(hours))
    print("=" * 80)
    
    if not device_ids:
        print("⚠️  没有设备ID，跳过检查")
        return
    
    with app.app_context():
        # 查询最近的告警（需要根据实际告警表结构调整）
        # 这里假设告警表名为alert，包含device_id, created_at, image_path等字段
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 尝试查询告警表
            sql = text("""
                SELECT id, device_id, object, event, image_path, created_at
                FROM alert
                WHERE device_id = ANY(:device_ids)
                AND created_at >= :since_time
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            result = db.session.execute(sql, {
                'device_ids': device_ids,
                'since_time': since_time
            })
            
            alerts = result.fetchall()
            
            if alerts:
                print(f"✅ 找到 {len(alerts)} 条最近的告警记录:\n")
                for alert in alerts:
                    alert_id, device_id, obj, event, image_path, created_at = alert
                    print(f"告警ID: {alert_id}")
                    print(f"  设备ID: {device_id}")
                    print(f"  对象: {obj}")
                    print(f"  事件: {event}")
                    print(f"  图片路径: {image_path or '(无)'}")
                    print(f"  创建时间: {created_at}")
                    print()
            else:
                print(f"⚠️  最近{hours}小时内没有找到告警记录")
                print("   这可能是正常的，如果还没有产生告警")
        except Exception as e:
            print(f"⚠️  查询告警记录失败: {str(e)}")
            print("   可能是告警表结构不同，或表不存在")
    
    print()


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("抓拍算法任务抓拍图片流程诊断工具")
    print("=" * 80 + "\n")
    
    # 1. 检查抓拍算法任务
    tasks = check_snapshot_algorithm_tasks()
    
    if not tasks:
        print("❌ 没有找到抓拍算法任务，无法继续诊断")
        return
    
    # 收集所有设备ID
    device_ids = set()
    for task in tasks:
        if task.devices:
            device_ids.update([d.id for d in task.devices])
    
    # 2. 检查抓拍空间
    snap_spaces = check_snap_spaces(list(device_ids))
    
    # 3. 检查告警图片目录（检查第一个任务）
    if tasks:
        check_alert_images_dir(tasks[0].id)
    
    # 4. 检查Kafka配置
    check_kafka_config()
    
    # 5. 检查最近的告警记录
    check_recent_alerts(list(device_ids))
    
    # 总结
    print("=" * 80)
    print("诊断总结")
    print("=" * 80)
    
    print(f"✅ 找到 {len(tasks)} 个抓拍算法任务")
    print(f"✅ 检查了 {len(device_ids)} 个设备")
    
    missing_spaces = [did for did, space in snap_spaces.items() if space is None]
    if missing_spaces:
        print(f"❌ {len(missing_spaces)} 个设备没有关联抓拍空间: {missing_spaces}")
        print("   建议：为这些设备创建抓拍空间")
    else:
        print(f"✅ 所有设备都有关联的抓拍空间")
    
    print("\n流程检查:")
    print("  1. ✅ 抓拍算法服务保存图片到本地 (alert_images/task_{task_id}/{device_id}/)")
    print("  2. ✅ Hook回调发送到Kafka (topic: iot-snapshot-alert)")
    print("  3. ✅ Sink订阅Kafka消息 (SnapshotAlertConsumer)")
    print("  4. ✅ Sink上传图片到抓拍空间 (根据device_id查询snap_space表)")
    
    print("\n如果图片没有上传到抓拍空间，请检查:")
    print("  1. 告警图片是否已保存到本地目录")
    print("  2. Kafka消息是否成功发送（检查Kafka日志）")
    print("  3. Sink服务是否正常运行（检查Sink日志）")
    print("  4. 设备是否有关联的抓拍空间（见上方检查结果）")
    print("  5. MinIO连接是否正常（检查Sink服务配置）")
    print()


if __name__ == '__main__':
    main()
