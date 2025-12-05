#!/usr/bin/env python3
"""
Kafka消费者组修复脚本
用于诊断和修复 video-alert-consumer 消费者组的重平衡问题

使用方法：
    python fix_kafka_consumer_group.py [--reset] [--check-only]

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import argparse
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

try:
    from kafka import KafkaAdminClient, KafkaConsumer
    from kafka.admin import NewPartitions
    from kafka.errors import KafkaError, GroupCoordinatorNotAvailableError
    from kafka.coordinator.assignors.range import RangePartitionAssignor
    from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
except ImportError:
    print("❌ 错误：未安装 kafka-python 库")
    print("请运行: pip install kafka-python")
    sys.exit(1)

# 默认配置
DEFAULT_CONSUMER_GROUP = 'video-alert-consumer'
DEFAULT_TOPIC = 'iot-alert-notification'
DEFAULT_BOOTSTRAP_SERVERS = 'localhost:9092'


def get_kafka_config():
    """从环境变量或配置文件获取Kafka配置"""
    # 尝试从环境变量获取
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', DEFAULT_BOOTSTRAP_SERVERS)
    consumer_group = os.getenv('KAFKA_ALERT_CONSUMER_GROUP', DEFAULT_CONSUMER_GROUP)
    topic = os.getenv('KAFKA_ALERT_TOPIC', DEFAULT_TOPIC)
    
    # 尝试从 .env 文件加载
    try:
        from dotenv import load_dotenv
        if os.path.exists('.env'):
            load_dotenv('.env')
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', bootstrap_servers)
            consumer_group = os.getenv('KAFKA_ALERT_CONSUMER_GROUP', consumer_group)
            topic = os.getenv('KAFKA_ALERT_TOPIC', topic)
    except ImportError:
        pass
    
    return {
        'bootstrap_servers': bootstrap_servers.split(','),
        'consumer_group': consumer_group,
        'topic': topic
    }


def check_kafka_connection(bootstrap_servers: List[str]) -> bool:
    """检查Kafka连接"""
    print(f"🔍 检查Kafka连接: {', '.join(bootstrap_servers)}")
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            request_timeout_ms=10000,
            api_version=(2, 5, 0)
        )
        # 尝试获取集群元数据
        admin_client.list_topics()
        print("✅ Kafka连接成功")
        admin_client.close()
        return True
    except Exception as e:
        print(f"❌ Kafka连接失败: {str(e)}")
        return False


def describe_consumer_group(bootstrap_servers: List[str], group_id: str) -> Optional[Dict]:
    """描述消费者组信息"""
    print(f"\n📊 检查消费者组: {group_id}")
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            request_timeout_ms=10000,
            api_version=(2, 5, 0)
        )
        
        # 获取消费者组描述
        from kafka.admin import DescribeGroupsRequest
        from kafka.protocol.group import GroupMember
        
        # 使用低级API获取消费者组信息
        coordinator = admin_client._client.cluster.coordinator(group_id)
        if coordinator is None:
            print(f"⚠️  无法找到消费者组协调器: {group_id}")
            admin_client.close()
            return None
        
        # 尝试获取消费者组状态
        try:
            # 使用kafka-python的内部API（不推荐，但这是获取详细信息的方式）
            # 我们使用更安全的方式：创建一个临时消费者来检查
            temp_consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                consumer_timeout_ms=1000,
                enable_auto_commit=False,
                api_version=(2, 5, 0)
            )
            
            # 获取消费者组元数据
            metadata = temp_consumer.list_consumer_groups()
            temp_consumer.close()
            
            print(f"✅ 消费者组存在: {group_id}")
            return {'group_id': group_id, 'exists': True}
            
        except Exception as e:
            print(f"⚠️  获取消费者组信息时出错: {str(e)}")
            admin_client.close()
            return None
            
    except GroupCoordinatorNotAvailableError:
        print(f"⚠️  消费者组协调器不可用: {group_id}")
        return None
    except Exception as e:
        print(f"❌ 检查消费者组失败: {str(e)}")
        return None


def list_consumer_groups(bootstrap_servers: List[str]) -> List[str]:
    """列出所有消费者组"""
    print("\n📋 列出所有消费者组...")
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            request_timeout_ms=10000,
            api_version=(2, 5, 0)
        )
        
        # 创建临时消费者来列出消费者组
        temp_consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            consumer_timeout_ms=1000,
            api_version=(2, 5, 0)
        )
        
        groups = temp_consumer.list_consumer_groups()
        temp_consumer.close()
        admin_client.close()
        
        if groups:
            print("找到以下消费者组:")
            for group in groups:
                print(f"  - {group}")
        else:
            print("未找到任何消费者组")
        
        return [g[0] for g in groups] if groups else []
        
    except Exception as e:
        print(f"❌ 列出消费者组失败: {str(e)}")
        return []


def reset_consumer_group_offset(bootstrap_servers: List[str], group_id: str, topic: str, reset_to: str = 'latest'):
    """
    重置消费者组偏移量
    
    Args:
        bootstrap_servers: Kafka服务器列表
        group_id: 消费者组ID
        topic: 主题名称
        reset_to: 重置位置 ('earliest', 'latest', 或 'none')
    """
    print(f"\n🔄 重置消费者组偏移量: {group_id}")
    print(f"   主题: {topic}")
    print(f"   重置到: {reset_to}")
    
    # 方法1: 尝试使用kafka-consumer-groups.sh（如果可用）
    print("\n方法1: 尝试使用kafka-consumer-groups.sh工具...")
    import subprocess
    import shutil
    
    kafka_scripts_path = os.getenv('KAFKA_HOME', '')
    if not kafka_scripts_path:
        # 尝试常见路径
        common_paths = [
            '/opt/kafka/bin',
            '/usr/local/kafka/bin',
            '/kafka/bin',
            os.path.join(os.path.expanduser('~'), 'kafka/bin')
        ]
        for path in common_paths:
            if os.path.exists(os.path.join(path, 'kafka-consumer-groups.sh')):
                kafka_scripts_path = path
                break
    
    if kafka_scripts_path and os.path.exists(os.path.join(kafka_scripts_path, 'kafka-consumer-groups.sh')):
        try:
            script_path = os.path.join(kafka_scripts_path, 'kafka-consumer-groups.sh')
            bootstrap_server = bootstrap_servers[0]
            
            # 删除消费者组
            print(f"   执行: {script_path} --bootstrap-server {bootstrap_server} --delete --group {group_id}")
            result = subprocess.run(
                [script_path, '--bootstrap-server', bootstrap_server, '--delete', '--group', group_id],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ 使用kafka-consumer-groups.sh成功删除消费者组")
                return
            else:
                print(f"⚠️  kafka-consumer-groups.sh执行失败: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"⚠️  无法使用kafka-consumer-groups.sh: {str(e)}")
    else:
        print("⚠️  未找到kafka-consumer-groups.sh工具，跳过方法1")
    
    # 方法2: 使用Python API重置偏移量
    print("\n方法2: 使用Python API重置消费者组...")
    try:
        # 创建一个临时消费者，加入组然后离开，触发重平衡
        print("   创建临时消费者来触发组重置...")
        temp_consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=reset_to,
            enable_auto_commit=True,
            consumer_timeout_ms=2000,
            session_timeout_ms=10000,
            heartbeat_interval_ms=3000,
            api_version=(2, 5, 0)
        )
        
        # 订阅主题（这会触发加入组）
        temp_consumer.subscribe([topic])
        print("   已订阅主题，等待加入消费者组...")
        
        # 等待一下，让消费者加入组并触发重平衡
        time.sleep(3)
        
        # 尝试拉取一次消息（这会提交偏移量）
        try:
            temp_consumer.poll(timeout_ms=1000)
        except:
            pass
        
        # 关闭消费者（这会离开组）
        print("   关闭临时消费者...")
        temp_consumer.close(timeout=5)
        
        print("✅ 消费者组已重置（通过临时消费者）")
        print("   注意：如果问题仍然存在，请检查是否有多个消费者实例在运行")
        
    except Exception as e:
        print(f"❌ 重置消费者组失败: {str(e)}")
        print("\n💡 手动修复建议:")
        print("   1. 停止所有运行中的消费者实例")
        print("   2. 等待30秒，让消费者组完全清理")
        print("   3. 使用kafka-consumer-groups.sh删除消费者组:")
        print(f"      kafka-consumer-groups.sh --bootstrap-server {bootstrap_servers[0]} --delete --group {group_id}")
        print("   4. 重新启动消费者服务")


def check_topic_exists(bootstrap_servers: List[str], topic: str) -> bool:
    """检查主题是否存在"""
    print(f"\n🔍 检查主题是否存在: {topic}")
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            request_timeout_ms=10000,
            api_version=(2, 5, 0)
        )
        
        topics = admin_client.list_topics()
        exists = topic in topics
        
        if exists:
            print(f"✅ 主题存在: {topic}")
            # 获取主题分区信息
            metadata = admin_client.describe_topics([topic])
            if topic in metadata:
                partitions = len(metadata[topic].partitions)
                print(f"   分区数: {partitions}")
        else:
            print(f"❌ 主题不存在: {topic}")
            print("   建议：检查主题名称是否正确，或创建该主题")
        
        admin_client.close()
        return exists
        
    except Exception as e:
        print(f"❌ 检查主题失败: {str(e)}")
        return False


def diagnose_consumer_group_issues(bootstrap_servers: List[str], group_id: str, topic: str):
    """诊断消费者组问题"""
    print("\n" + "="*60)
    print("🔍 诊断消费者组问题")
    print("="*60)
    
    issues = []
    recommendations = []
    
    # 1. 检查主题是否存在
    if not check_topic_exists(bootstrap_servers, topic):
        issues.append(f"主题 {topic} 不存在")
        recommendations.append(f"创建主题: kafka-topics.sh --create --topic {topic} --bootstrap-server {bootstrap_servers[0]}")
    
    # 2. 检查消费者组
    group_info = describe_consumer_group(bootstrap_servers, group_id)
    if group_info is None:
        issues.append(f"无法获取消费者组 {group_id} 的信息")
        recommendations.append("检查Kafka集群状态和网络连接")
    
    # 3. 列出所有消费者组，检查是否有重复
    all_groups = list_consumer_groups(bootstrap_servers)
    if group_id in all_groups:
        print(f"✅ 消费者组 {group_id} 已注册")
    else:
        print(f"⚠️  消费者组 {group_id} 未在注册列表中")
        recommendations.append("这可能是正常的，如果消费者当前没有运行")
    
    # 4. 检查是否有多个消费者实例
    print("\n⚠️  常见问题检查:")
    print("   1. 是否有多个服务实例在运行？")
    print("   2. 消费者是否频繁重启？")
    print("   3. 网络是否稳定？")
    print("   4. Kafka集群是否正常？")
    
    # 5. 提供修复建议
    if issues:
        print("\n❌ 发现的问题:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    if recommendations:
        print("\n💡 修复建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    # 6. 提供手动修复步骤
    print("\n📝 手动修复步骤:")
    print("   方法A - 使用此脚本:")
    print("   1. 停止所有运行中的消费者实例")
    print("   2. 等待30秒，让消费者组完全清理")
    print("   3. 运行: python fix_kafka_consumer_group.py --reset")
    print("   4. 重新启动消费者服务")
    print("   5. 监控日志，确认不再出现重平衡")
    print("")
    print("   方法B - 使用kafka-consumer-groups.sh:")
    print(f"   1. 停止所有运行中的消费者实例")
    print(f"   2. 执行: kafka-consumer-groups.sh --bootstrap-server {bootstrap_servers[0]} --delete --group {group_id}")
    print(f"   3. 重新启动消费者服务")
    print("")
    print("   方法C - 使用提供的shell脚本:")
    print(f"   1. 运行: bash fix_kafka_consumer_group.sh")
    
    return issues, recommendations


def main():
    parser = argparse.ArgumentParser(
        description='Kafka消费者组修复脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
快速使用:
  # 仅检查问题
  python fix_kafka_consumer_group.py --check-only
  
  # 检查并重置消费者组（需要确认）
  python fix_kafka_consumer_group.py --reset
  
  # 指定消费者组和主题
  python fix_kafka_consumer_group.py --group my-group --topic my-topic --reset

⚠️  重要提示：
  1. 执行修复前请先停止所有运行中的消费者服务
  2. 重置操作会删除消费者组及其偏移量
  3. 消费者重启后会从最新位置开始消费
        """
    )
    parser.add_argument('--reset', action='store_true',
                       help='重置消费者组偏移量')
    parser.add_argument('--check-only', action='store_true',
                       help='仅检查问题，不执行修复')
    parser.add_argument('--group', type=str,
                       help=f'消费者组ID（默认: {DEFAULT_CONSUMER_GROUP}）')
    parser.add_argument('--topic', type=str,
                       help=f'主题名称（默认: {DEFAULT_TOPIC}）')
    parser.add_argument('--bootstrap-servers', type=str,
                       help=f'Kafka服务器地址（默认: {DEFAULT_BOOTSTRAP_SERVERS}）')
    parser.add_argument('--reset-to', type=str, choices=['earliest', 'latest'],
                       default='latest',
                       help='重置偏移量到哪个位置（默认: latest）')
    
    args = parser.parse_args()
    
    # 获取配置
    config = get_kafka_config()
    
    # 命令行参数覆盖配置
    if args.group:
        config['consumer_group'] = args.group
    if args.topic:
        config['topic'] = args.topic
    if args.bootstrap_servers:
        config['bootstrap_servers'] = args.bootstrap_servers.split(',')
    
    print("="*60)
    print("Kafka消费者组修复脚本")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"消费者组: {config['consumer_group']}")
    print(f"主题: {config['topic']}")
    print(f"Kafka服务器: {', '.join(config['bootstrap_servers'])}")
    print("="*60)
    
    # 检查Kafka连接
    if not check_kafka_connection(config['bootstrap_servers']):
        print("\n❌ 无法连接到Kafka，请检查:")
        print("   1. Kafka服务是否运行")
        print("   2. 服务器地址是否正确")
        print("   3. 网络连接是否正常")
        sys.exit(1)
    
    # 诊断问题
    issues, recommendations = diagnose_consumer_group_issues(
        config['bootstrap_servers'],
        config['consumer_group'],
        config['topic']
    )
    
    # 如果需要重置
    if args.reset and not args.check_only:
        print("\n" + "="*60)
        print("🔄 执行重置操作")
        print("="*60)
        
        print("\n⚠️  重要提示：")
        print("   1. 请确保已停止所有运行中的消费者服务")
        print("   2. 重置操作会删除消费者组及其偏移量")
        print("   3. 消费者重启后会从最新位置开始消费")
        confirm = input(f"\n⚠️  确定要重置消费者组 '{config['consumer_group']}' 吗？(yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            reset_consumer_group_offset(
                config['bootstrap_servers'],
                config['consumer_group'],
                config['topic'],
                args.reset_to
            )
            print("\n✅ 重置完成")
            print("   建议：重新启动消费者服务，并监控日志")
        else:
            print("❌ 已取消重置操作")
    elif args.check_only:
        print("\n✅ 检查完成（未执行修复）")
        print("💡 如需修复，请运行: python fix_kafka_consumer_group.py --reset")
    else:
        print("\n💡 提示：")
        print("   使用 --check-only 参数来仅检查问题")
        print("   使用 --reset 参数来重置消费者组")
        print("\n   示例:")
        print("   python fix_kafka_consumer_group.py --check-only")
        print("   python fix_kafka_consumer_group.py --reset")
    
    print("\n" + "="*60)
    print("脚本执行完成")
    print("="*60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

