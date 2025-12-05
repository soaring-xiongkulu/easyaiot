#!/bin/bash
#
# Kafka消费者组快速修复脚本
# 一键修复 video-alert-consumer 消费者组的重平衡问题
#
# 使用方法：
#     bash fix_kafka_quick.sh
#
# @author 翱翔的雄库鲁
# @email andywebjava@163.com
# @wechat EasyAIoT2025

set -o pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Kafka消费者组快速修复脚本${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# 步骤1: 检查是否有运行中的消费者
echo -e "${YELLOW}步骤1: 检查运行中的消费者服务...${NC}"
CONSUMER_PIDS=$(ps aux | grep -E "run\.py|alert_consumer|video.*consumer" | grep -v grep | awk '{print $2}' || true)

if [ -n "$CONSUMER_PIDS" ]; then
    echo -e "${RED}⚠️  发现运行中的消费者进程:${NC}"
    ps aux | grep -E "run\.py|alert_consumer|video.*consumer" | grep -v grep
    echo ""
    read -p "是否要停止这些进程？(yes/no): " stop_confirm
    if [ "$stop_confirm" = "yes" ] || [ "$stop_confirm" = "y" ]; then
        echo -e "${YELLOW}正在停止进程...${NC}"
        for pid in $CONSUMER_PIDS; do
            kill "$pid" 2>/dev/null || true
        done
        sleep 2
        # 强制杀死仍在运行的进程
        for pid in $CONSUMER_PIDS; do
            kill -9 "$pid" 2>/dev/null || true
        done
        echo -e "${GREEN}✅ 进程已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  请手动停止消费者服务后再继续${NC}"
        read -p "按回车键继续（假设已停止服务）..."
    fi
else
    echo -e "${GREEN}✅ 未发现运行中的消费者进程${NC}"
fi

echo ""

# 步骤2: 等待清理
echo -e "${YELLOW}步骤2: 等待Kafka清理消费者组状态（30秒）...${NC}"
for i in {30..1}; do
    echo -ne "\r   剩余 ${i} 秒..."
    sleep 1
done
echo -e "\r   等待完成                              "
echo ""

# 步骤3: 检查问题
echo -e "${YELLOW}步骤3: 检查消费者组状态...${NC}"
if [ -f "fix_kafka_consumer_group.sh" ]; then
    bash fix_kafka_consumer_group.sh --check-only
    CHECK_RESULT=$?
else
    echo -e "${RED}❌ 未找到 fix_kafka_consumer_group.sh 脚本${NC}"
    CHECK_RESULT=1
fi

echo ""

# 步骤4: 执行修复
if [ $CHECK_RESULT -eq 0 ]; then
    echo -e "${YELLOW}步骤4: 执行修复...${NC}"
    read -p "是否要重置消费者组？(yes/no): " reset_confirm
    if [ "$reset_confirm" = "yes" ] || [ "$reset_confirm" = "y" ]; then
        if [ -f "fix_kafka_consumer_group.sh" ]; then
            bash fix_kafka_consumer_group.sh --reset
            RESET_RESULT=$?
        else
            echo -e "${RED}❌ 未找到 fix_kafka_consumer_group.sh 脚本${NC}"
            RESET_RESULT=1
        fi
        
        if [ $RESET_RESULT -eq 0 ]; then
            echo ""
            echo -e "${GREEN}============================================================${NC}"
            echo -e "${GREEN}✅ 修复完成！${NC}"
            echo -e "${GREEN}============================================================${NC}"
            echo ""
            echo -e "${YELLOW}下一步操作:${NC}"
            echo "   1. 重新启动消费者服务"
            echo "   2. 监控日志，确认不再出现重平衡错误"
            echo ""
            echo -e "${BLUE}查看日志命令:${NC}"
            echo "   tail -f logs/app.log | grep -i 'rebalance\\|consumer'"
        else
            echo -e "${RED}❌ 修复失败，请查看错误信息${NC}"
        fi
    else
        echo -e "${YELLOW}已取消修复操作${NC}"
    fi
else
    echo -e "${RED}❌ 检查失败，请先解决连接问题${NC}"
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}脚本执行完成${NC}"
echo -e "${BLUE}============================================================${NC}"

