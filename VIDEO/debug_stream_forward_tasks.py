#!/usr/bin/env python3
"""
调试脚本：检查推流转发任务状态
用于诊断为什么系统显示"没有需要启动的推流转发任务"

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
from dotenv import load_dotenv

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, video_root)

# 加载环境变量
load_dotenv()

from flask import Flask
from models import db, StreamForwardTask

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 从环境变量获取数据库URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL环境变量未设置")
    
    # 转换postgres://为postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("推流转发任务状态检查")
        print("=" * 80)
        
        # 查询所有推流转发任务
        all_tasks = StreamForwardTask.query.all()
        print(f"\n📊 总任务数: {len(all_tasks)}")
        
        if not all_tasks:
            print("❌ 数据库中没有推流转发任务")
            return
        
        # 查询符合自动启动条件的任务（只根据 is_enabled 判断）
        auto_start_tasks = StreamForwardTask.query.filter(
            StreamForwardTask.is_enabled == True
        ).all()
        
        print(f"\n✅ 符合自动启动条件的任务数: {len(auto_start_tasks)}")
        print("   条件: is_enabled=True（运行中）")
        
        # 详细显示每个任务的状态
        print("\n" + "-" * 80)
        print("所有任务详细信息:")
        print("-" * 80)
        
        for task in all_tasks:
            device_count = len(task.devices) if task.devices else 0
            print(f"\n任务 ID: {task.id}")
            print(f"  任务名称: {task.task_name}")
            print(f"  任务编号: {task.task_code}")
            print(f"  is_enabled: {task.is_enabled} ({'运行中' if task.is_enabled else '已停止'})")
            print(f"  关联设备数: {device_count}")
            print(f"  服务进程ID: {task.service_process_id}")
            print(f"  服务IP: {task.service_server_ip}")
            print(f"  服务端口: {task.service_port}")
            
            # 检查是否符合自动启动条件（只根据 is_enabled 判断）
            is_auto_start = task.is_enabled == True
            
            if is_auto_start:
                print(f"  ✅ 符合自动启动条件（is_enabled=True）")
                if not task.devices or len(task.devices) == 0:
                    print(f"  ⚠️  但没有关联的摄像头，会被跳过")
            else:
                print(f"  ❌ 不符合自动启动条件")
                print(f"     原因: is_enabled={task.is_enabled} (需要True)")
        
        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
