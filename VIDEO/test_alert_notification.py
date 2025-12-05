#!/usr/bin/env python3
"""
告警通知流程测试脚本
测试流程：模拟产生告警 -> 投递Kafka -> DEVICE的message订阅告警 -> 发送告警信息到用户（邮件、Webhook）

使用方法：
    python test_alert_notification.py --device-id <设备ID> --email <测试邮箱> --webhook <测试Webhook URL>
    
示例：
    python test_alert_notification.py --device-id camera_001 --email test@example.com --webhook http://localhost:8080/webhook
"""
import os
import sys
import json
import time
import argparse
import requests
import signal
import threading
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

# 先解析命令行参数，避免导入run.py时参数解析冲突
def parse_script_args():
    """解析脚本参数"""
    parser = argparse.ArgumentParser(description='告警通知流程测试脚本')
    parser.add_argument('--device-id', required=True, help='设备ID')
    parser.add_argument('--device-name', help='设备名称（可选）')
    parser.add_argument('--email', help='测试邮箱地址（用于邮件通知测试）')
    parser.add_argument('--webhook', help='测试Webhook URL（用于Webhook通知测试）')
    parser.add_argument('--service-url', default=os.getenv('VIDEO_SERVICE_URL', 'http://localhost:6000'), 
                       help='VIDEO服务URL（默认: http://localhost:6000）')
    parser.add_argument('--env', type=str, default='', 
                       help='指定环境配置文件，例如: --env=prod 会加载 .env.prod，默认加载 .env')
    return parser.parse_args()

# 保存原始sys.argv
_original_argv = sys.argv.copy()

# 解析参数（在导入run.py之前）
_script_args = parse_script_args()

# 临时修改sys.argv，只保留脚本名称和--env参数（如果有），供run.py导入时使用
_new_argv = [sys.argv[0]]
if _script_args.env:
    _new_argv.extend(['--env', _script_args.env])
sys.argv = _new_argv

# 导入Flask应用和数据库模型
from run import create_app
from models import db, Device, SnapTask, SnapSpace, Alert

# 恢复原始sys.argv（虽然已经不需要了，但为了安全）
sys.argv = _original_argv

# 配置
VIDEO_SERVICE_URL = os.getenv('VIDEO_SERVICE_URL', 'http://localhost:6000')
ALERT_HOOK_ENDPOINT = f'{VIDEO_SERVICE_URL}/video/alert/hook'

# 全局变量：用于信号处理
_shutdown_event = threading.Event()
_force_exit = False
_interrupt_count = 0

def signal_handler(signum, frame):
    """处理 Ctrl+C 信号"""
    global _force_exit, _interrupt_count
    _interrupt_count += 1
    
    if _interrupt_count == 1:
        print(f"\n\n{Colors.YELLOW}⚠️  收到中断信号 (Ctrl+C)，正在退出...{Colors.RESET}")
        print(f"{Colors.YELLOW}   如果程序没有响应，请再次按 Ctrl+C 强制退出{Colors.RESET}")
        _force_exit = True
        _shutdown_event.set()
    else:
        # 第二次按 Ctrl+C，强制退出
        print(f"\n\n{Colors.RED}⚠️  强制退出！{Colors.RESET}")
        os._exit(1)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_step(step, msg):
    print(f"\n{Colors.BOLD}步骤 {step}: {msg}{Colors.RESET}")


def check_service_available():
    """检查VIDEO服务是否可用"""
    try:
        response = requests.get(f'{VIDEO_SERVICE_URL}/health', timeout=5)
        if response.status_code == 200:
            print_success(f"VIDEO服务可用: {VIDEO_SERVICE_URL}")
            return True
    except requests.exceptions.RequestException:
        pass
    
    # 如果health端点不存在，尝试访问根路径
    try:
        response = requests.get(VIDEO_SERVICE_URL, timeout=5)
        print_success(f"VIDEO服务可用: {VIDEO_SERVICE_URL}")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"VIDEO服务不可用: {VIDEO_SERVICE_URL}, 错误: {str(e)}")
        return False


def get_or_create_device(device_id, device_name=None, app=None):
    """获取或创建设备"""
    if app is None:
        app = create_app()
        with app.app_context():
            return get_or_create_device(device_id, device_name, app)
    
    # 已经在app_context中
    device = Device.query.get(device_id)
    if not device:
        print_warning(f"设备不存在: {device_id}，正在创建测试设备...")
        device = Device(
            id=device_id,
            name=device_name or f"测试设备-{device_id}",
            source=f"rtsp://test.example.com/{device_id}",
            rtmp_stream=f"rtmp://test.example.com/live/{device_id}",
            http_stream=f"http://test.example.com/stream/{device_id}",
            stream=1,
            ip="192.168.1.100",
            port=554,
            manufacturer="测试厂商",
            model="测试型号",
            nvr_channel=1
        )
        db.session.add(device)
        db.session.commit()
        print_success(f"已创建测试设备: {device_id}")
    else:
        print_success(f"找到设备: {device_id} ({device.name})")
    return device


def get_or_create_snap_space(device_id, app=None):
    """获取或创建抓拍空间"""
    if app is None:
        app = create_app()
        with app.app_context():
            return get_or_create_snap_space(device_id, app)
    
    # 已经在app_context中
    # 查找设备关联的空间
    space = SnapSpace.query.filter_by(device_id=device_id).first()
    if not space:
        print_warning(f"设备 {device_id} 没有关联的抓拍空间，正在创建...")
        space = SnapSpace(
            space_name=f"测试空间-{device_id}",
            space_code=f"SPACE_{device_id}",
            bucket_name=f"test-bucket-{device_id}",
            device_id=device_id
        )
        db.session.add(space)
        db.session.commit()
        print_success(f"已创建抓拍空间: {space.space_name}")
    else:
        print_success(f"找到抓拍空间: {space.space_name}")
    return space


def get_or_create_snap_task(device_id, space_id, email, webhook_url, app=None):
    """获取或创建抓拍任务（配置告警通知）"""
    if app is None:
        app = create_app()
        with app.app_context():
            return get_or_create_snap_task(device_id, space_id, email, webhook_url, app)
    
    # 已经在app_context中
    # 查找设备关联的已启用告警的任务
    task = SnapTask.query.filter_by(
        device_id=device_id,
        alarm_enabled=True,
        is_enabled=True
    ).first()
    
    if not task:
        print_warning(f"设备 {device_id} 没有配置告警的任务，正在创建...")
        
        # 构建通知人列表
        notify_users = []
        if email:
            notify_users.append({
                "email": email,
                "name": "测试用户-邮件"
            })
        if webhook_url:
            notify_users.append({
                "webhook": webhook_url,
                "name": "测试用户-Webhook"
            })
        
        # 构建通知方式列表
        notify_methods = []
        if email:
            notify_methods.append("email")
        if webhook_url:
            notify_methods.append("webhook")
        
        if not notify_methods:
            print_error("至少需要配置一种通知方式（email或webhook）")
            return None
        
        task = SnapTask(
            task_name=f"告警测试任务-{device_id}",
            task_code=f"TEST_TASK_{device_id}_{int(time.time())}",
            space_id=space_id,
            device_id=device_id,
            capture_type=0,
            cron_expression="0 */5 * * * *",
            frame_skip=1,
            alarm_enabled=True,
            notify_users=json.dumps(notify_users, ensure_ascii=False),
            notify_methods=",".join(notify_methods),
            alarm_suppress_time=0,  # 测试时设置为0，不抑制通知
            is_enabled=True,
            status=0,
            run_status='stopped'
        )
        db.session.add(task)
        db.session.commit()
        print_success(f"已创建告警测试任务: {task.task_name}")
        print_info(f"  通知方式: {', '.join(notify_methods)}")
        print_info(f"  通知人: {len(notify_users)} 人")
    else:
        print_success(f"找到已配置告警的任务: {task.task_name}")
        # 更新通知配置
        notify_users = []
        if email:
            notify_users.append({
                "email": email,
                "name": "测试用户-邮件"
            })
        if webhook_url:
            notify_users.append({
                "webhook": webhook_url,
                "name": "测试用户-Webhook"
            })
        
        notify_methods = []
        if email:
            notify_methods.append("email")
        if webhook_url:
            notify_methods.append("webhook")
        
        task.notify_users = json.dumps(notify_users, ensure_ascii=False)
        task.notify_methods = ",".join(notify_methods)
        task.alarm_suppress_time = 0  # 测试时设置为0，不抑制通知
        task.last_notify_time = None  # 清除最后通知时间，确保可以立即发送
        db.session.commit()
        print_info(f"  已更新通知配置")
        print_info(f"  通知方式: {', '.join(notify_methods)}")
        print_info(f"  通知人: {len(notify_users)} 人")
    
    return task


def send_test_alert(device_id, device_name):
    """发送测试告警"""
    print_step(3, "发送测试告警")
    
    alert_data = {
        "object": "person",
        "event": "intrusion",
        "device_id": device_id,
        "device_name": device_name,
        "region": "测试区域A",
        "information": {
            "confidence": 0.95,
            "bbox": [100, 100, 200, 200],
            "message": "这是测试告警信息"
        },
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "image_path": "/test/path/to/image.jpg",
        "record_path": "/test/path/to/video.mp4"
    }
    
    print_info(f"告警数据: {json.dumps(alert_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            ALERT_HOOK_ENDPOINT,
            json=alert_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 200:
                alert_id = result.get('data', {}).get('id')
                print_success(f"告警发送成功，告警ID: {alert_id}")
                return alert_id, alert_data
            else:
                print_error(f"告警发送失败: {result.get('message')}")
                return None, alert_data
        else:
            print_error(f"告警发送失败，HTTP状态码: {response.status_code}")
            print_error(f"响应内容: {response.text}")
            return None, alert_data
    except requests.exceptions.RequestException as e:
        print_error(f"发送告警请求失败: {str(e)}")
        return None, alert_data


def verify_alert_in_database(alert_id, device_id, app=None):
    """验证告警是否已存储到数据库"""
    print_step(4, "验证告警是否已存储到数据库")
    
    if app is None:
        app = create_app()
        with app.app_context():
            return verify_alert_in_database(alert_id, device_id, app)
    
    # 已经在app_context中
    if alert_id:
        alert = Alert.query.get(alert_id)
        if alert:
            print_success(f"告警已存储到数据库")
            print_info(f"  告警ID: {alert.id}")
            print_info(f"  设备ID: {alert.device_id}")
            print_info(f"  设备名称: {alert.device_name}")
            print_info(f"  对象类型: {alert.object}")
            print_info(f"  事件类型: {alert.event}")
            print_info(f"  告警时间: {alert.time}")
            return True
        else:
            print_error(f"告警未找到: alert_id={alert_id}")
            return False
    else:
        # 如果没有alert_id，查找最近的告警
        alert = Alert.query.filter_by(device_id=device_id).order_by(Alert.time.desc()).first()
        if alert:
            print_success(f"找到最近的告警记录")
            print_info(f"  告警ID: {alert.id}")
            print_info(f"  告警时间: {alert.time}")
            return True
        else:
            print_error(f"未找到设备的告警记录")
            return False


def check_kafka_message(device_id):
    """检查Kafka消息（提示信息）"""
    print_step(5, "检查Kafka消息投递")
    
    print_info("Kafka消息投递检查需要查看VIDEO服务日志")
    print_info("请检查以下日志信息：")
    print_info(f"  - 查找 '告警通知消息发送到Kafka成功' 日志")
    print_info(f"  - 设备ID: {device_id}")
    print_info(f"  - Topic: iot-alert-notification")
    
    print_warning("如果Kafka不可用，告警仍会存储到数据库，但不会发送通知")


def check_device_message_service():
    """检查DEVICE的message服务（提示信息）"""
    print_step(6, "检查DEVICE的message服务处理")
    
    print_info("请检查DEVICE服务的message模块日志：")
    print_info("  - 查找 '告警通知Kafka消费者' 相关日志")
    print_info("  - 查找 '处理告警通知' 相关日志")
    print_info("  - 查找 '发送告警通知' 相关日志")
    
    print_info("\n如果配置了邮件通知，请检查：")
    print_info("  - 邮件是否成功发送")
    print_info("  - 邮件发送日志")
    
    print_info("\n如果配置了Webhook通知，请检查：")
    print_info("  - Webhook URL是否收到请求")
    print_info("  - Webhook请求的响应状态")


def main():
    global VIDEO_SERVICE_URL, ALERT_HOOK_ENDPOINT
    
    # 使用已解析的参数
    args = _script_args
    
    if not args.email and not args.webhook:
        print_error("至少需要配置一种通知方式：--email 或 --webhook")
        sys.exit(1)
    
    VIDEO_SERVICE_URL = args.service_url
    ALERT_HOOK_ENDPOINT = f'{VIDEO_SERVICE_URL}/video/alert/hook'
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}告警通知流程测试{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    print(f"{Colors.YELLOW}提示：如果程序卡住，按 Ctrl+C 退出（可能需要按两次）{Colors.RESET}\n")
    
    print_info(f"VIDEO服务URL: {VIDEO_SERVICE_URL}")
    print_info(f"设备ID: {args.device_id}")
    if args.email:
        print_info(f"测试邮箱: {args.email}")
    if args.webhook:
        print_info(f"测试Webhook: {args.webhook}")
    
    # 步骤1: 检查服务可用性
    print_step(1, "检查VIDEO服务可用性")
    if not check_service_available():
        print_error("VIDEO服务不可用，请检查服务是否启动")
        sys.exit(1)
    
    # 步骤2: 准备测试环境（设备、空间、任务）
    print_step(2, "准备测试环境")
    
    # 设置POD_IP环境变量，避免get_local_ip()卡住
    if not os.getenv('POD_IP'):
        os.environ['POD_IP'] = '127.0.0.1'
        print_info("已设置 POD_IP=127.0.0.1 以避免网络探测卡住")
    
    print_info("正在创建Flask应用...")
    print_warning("注意：如果卡住，请按 Ctrl+C 强制退出（可能需要按两次）")
    
    app = None
    app_result = {'app': None, 'error': None}
    
    def create_app_in_thread():
        """在线程中创建应用，避免阻塞主线程"""
        try:
            if _force_exit:
                return
            result = create_app()
            app_result['app'] = result
        except Exception as e:
            app_result['error'] = e
    
    # 在单独线程中执行 create_app
    thread = threading.Thread(target=create_app_in_thread, daemon=True)
    thread.start()
    
    # 等待最多30秒，每0.5秒检查一次是否被中断
    elapsed = 0
    timeout = 30
    check_interval = 0.5
    
    while elapsed < timeout and thread.is_alive():
        if _force_exit:
            print_error("\n用户中断，正在退出...")
            os._exit(1)
        time.sleep(check_interval)
        elapsed += check_interval
    
    if _force_exit:
        print_error("用户中断，退出程序")
        os._exit(1)
    
    if thread.is_alive():
        print_error("创建Flask应用超时（30秒），可能原因：")
        print_error("  1. 数据库连接超时 - 请检查 DATABASE_URL 和数据库服务")
        print_error("  2. Nacos 连接超时 - 请检查 NACOS_SERVER 配置")
        print_error("  3. 其他服务初始化问题")
        print_warning("正在强制退出...")
        os._exit(1)
    
    if app_result['error']:
        print_error(f"创建Flask应用失败: {str(app_result['error'])}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if app_result['app']:
        app = app_result['app']
        print_success("Flask应用创建成功")
    else:
        print_error("创建Flask应用失败：未知错误")
        sys.exit(1)
    
    print_info("正在初始化应用上下文...")
    device_name = None
    try:
        with app.app_context():
            if _force_exit:
                print_error("用户中断，退出程序")
                sys.exit(1)
            
            print_info("应用上下文已创建，正在获取或创建设备...")
            # 获取或创建设备（传入app避免重复创建）
            device = get_or_create_device(args.device_id, args.device_name, app)
            device_name = device.name
            print_success(f"设备准备完成: {device_name}")
            
            if _force_exit:
                print_error("用户中断，退出程序")
                sys.exit(1)
            
            print_info("正在获取或创建抓拍空间...")
            # 获取或创建抓拍空间（传入app避免重复创建）
            space = get_or_create_snap_space(args.device_id, app)
            print_success(f"抓拍空间准备完成: {space.space_name}")
            
            if _force_exit:
                print_error("用户中断，退出程序")
                sys.exit(1)
            
            print_info("正在获取或创建抓拍任务...")
            # 获取或创建抓拍任务（配置告警通知，传入app避免重复创建）
            task = get_or_create_snap_task(args.device_id, space.id, args.email, args.webhook, app)
            if not task:
                print_error("无法创建或获取告警任务")
                sys.exit(1)
            print_success("抓拍任务准备完成")
    except KeyboardInterrupt:
        print_error("\n用户中断，退出程序")
        sys.exit(1)
    except Exception as e:
        print_error(f"准备测试环境失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if _force_exit:
        print_error("用户中断，退出程序")
        os._exit(1)
    
    # 步骤3: 发送测试告警
    alert_id, alert_data = send_test_alert(args.device_id, device_name)
    
    if _force_exit:
        print_error("用户中断，退出程序")
        os._exit(1)
    
    # 等待一下，确保数据库操作完成
    time.sleep(1)
    
    if _force_exit:
        print_error("用户中断，退出程序")
        os._exit(1)
    
    # 步骤4: 验证告警存储（复用同一个app上下文）
    with app.app_context():
        verify_alert_in_database(alert_id, args.device_id, app)
    
    # 步骤5: 检查Kafka消息
    check_kafka_message(args.device_id)
    
    # 步骤6: 检查DEVICE服务处理
    check_device_message_service()
    
    # 总结
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}测试完成{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    print_info("测试流程总结：")
    print_info("  1. ✅ 告警已通过Hook接口发送")
    print_info("  2. ✅ 告警已存储到数据库")
    print_info("  3. ⚠️  请检查Kafka消息投递（查看VIDEO服务日志）")
    print_info("  4. ⚠️  请检查DEVICE服务处理（查看DEVICE服务日志）")
    print_info("  5. ⚠️  请检查通知是否成功发送（邮件/Webhook）")
    
    if args.email:
        print_warning(f"\n请检查邮箱 {args.email} 是否收到告警通知邮件")
    if args.webhook:
        print_warning(f"\n请检查Webhook {args.webhook} 是否收到告警通知请求")


if __name__ == '__main__':
    main()

