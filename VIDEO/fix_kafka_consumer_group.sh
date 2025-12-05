#!/bin/bash
#
# Kafka消费者组修复脚本（Shell版本）
# 用于诊断和修复 video-alert-consumer 消费者组的重平衡问题
#
# 使用方法：
#     bash fix_kafka_consumer_group.sh [--reset] [--check-only]
#
# @author 翱翔的雄库鲁
# @email andywebjava@163.com
# @wechat EasyAIoT2025

# 不使用 set -e，以便更好地处理错误
set -o pipefail

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_CONSUMER_GROUP="video-alert-consumer"
DEFAULT_TOPIC="iot-alert-notification"
DEFAULT_BOOTSTRAP_SERVERS="localhost:9092"

# 从环境变量或.env文件获取配置
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -E '^KAFKA_' | xargs)
fi

CONSUMER_GROUP="${KAFKA_ALERT_CONSUMER_GROUP:-$DEFAULT_CONSUMER_GROUP}"
TOPIC="${KAFKA_ALERT_TOPIC:-$DEFAULT_TOPIC}"
BOOTSTRAP_SERVERS="${KAFKA_BOOTSTRAP_SERVERS:-$DEFAULT_BOOTSTRAP_SERVERS}"

# 查找kafka-consumer-groups.sh
find_kafka_scripts() {
    local kafka_home="${KAFKA_HOME:-}"
    
    if [ -n "$kafka_home" ] && [ -f "$kafka_home/bin/kafka-consumer-groups.sh" ]; then
        echo "$kafka_home/bin"
        return 0
    fi
    
    # 尝试常见路径
    local common_paths=(
        "/opt/kafka/bin"
        "/usr/local/kafka/bin"
        "/kafka/bin"
        "$HOME/kafka/bin"
        "/usr/bin"
        "/usr/local/bin"
    )
    
    for path in "${common_paths[@]}"; do
        if [ -f "$path/kafka-consumer-groups.sh" ]; then
            echo "$path"
            return 0
        fi
    done
    
    # 尝试在PATH中查找
    if command -v kafka-consumer-groups.sh &> /dev/null; then
        local script_path=$(command -v kafka-consumer-groups.sh)
        echo "$(dirname "$script_path")"
        return 0
    fi
    
    return 1
}

# 检查Kafka连接
check_kafka_connection() {
    echo -e "${BLUE}🔍 检查Kafka连接: ${BOOTSTRAP_SERVERS}${NC}"
    
    local kafka_bin=$(find_kafka_scripts 2>/dev/null)
    if [ -z "$kafka_bin" ]; then
        echo -e "${YELLOW}⚠️  未找到kafka-consumer-groups.sh工具，跳过连接检查${NC}"
        return 0
    fi
    
    if "$kafka_bin/kafka-consumer-groups.sh" --bootstrap-server "$BOOTSTRAP_SERVERS" --list &>/dev/null; then
        echo -e "${GREEN}✅ Kafka连接成功${NC}"
        return 0
    else
        echo -e "${RED}❌ Kafka连接失败${NC}"
        return 1
    fi
}

# 列出所有消费者组
list_consumer_groups() {
    echo -e "\n${BLUE}📋 列出所有消费者组...${NC}"
    
    local kafka_bin=$(find_kafka_scripts 2>/dev/null)
    if [ -z "$kafka_bin" ]; then
        echo -e "${YELLOW}⚠️  未找到kafka-consumer-groups.sh工具${NC}"
        return 1
    fi
    
    "$kafka_bin/kafka-consumer-groups.sh" --bootstrap-server "$BOOTSTRAP_SERVERS" --list
}

# 描述消费者组
describe_consumer_group() {
    local group_id="$1"
    echo -e "\n${BLUE}📊 检查消费者组: ${group_id}${NC}"
    
    local kafka_bin=$(find_kafka_scripts 2>/dev/null)
    if [ -z "$kafka_bin" ]; then
        echo -e "${YELLOW}⚠️  未找到kafka-consumer-groups.sh工具${NC}"
        return 1
    fi
    
    if "$kafka_bin/kafka-consumer-groups.sh" --bootstrap-server "$BOOTSTRAP_SERVERS" --group "$group_id" --describe &>/dev/null; then
        echo -e "${GREEN}✅ 消费者组存在${NC}"
        echo ""
        "$kafka_bin/kafka-consumer-groups.sh" --bootstrap-server "$BOOTSTRAP_SERVERS" --group "$group_id" --describe
        return 0
    else
        echo -e "${YELLOW}⚠️  消费者组不存在或无法访问${NC}"
        return 1
    fi
}

# 重置消费者组
reset_consumer_group() {
    local group_id="$1"
    echo -e "\n${BLUE}🔄 重置消费者组: ${group_id}${NC}"
    
    local kafka_bin=$(find_kafka_scripts 2>/dev/null)
    if [ -z "$kafka_bin" ]; then
        echo -e "${RED}❌ 未找到kafka-consumer-groups.sh工具${NC}"
        echo -e "${YELLOW}💡 请安装Kafka或设置KAFKA_HOME环境变量${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}⚠️  这将删除消费者组及其所有偏移量信息${NC}"
    echo -e "${YELLOW}⚠️  请确保已停止所有运行中的消费者服务！${NC}"
    echo ""
    read -p "确定要继续吗？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
        echo -e "${YELLOW}❌ 已取消操作${NC}"
        return 1
    fi
    
    echo -e "${BLUE}正在删除消费者组...${NC}"
    if "$kafka_bin/kafka-consumer-groups.sh" --bootstrap-server "$BOOTSTRAP_SERVERS" --delete --group "$group_id"; then
        echo -e "${GREEN}✅ 消费者组已删除${NC}"
        echo -e "${GREEN}   建议：重新启动消费者服务${NC}"
        return 0
    else
        echo -e "${RED}❌ 删除消费者组失败${NC}"
        return 1
    fi
}

# 诊断问题
diagnose() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}🔍 诊断消费者组问题${NC}"
    echo -e "${BLUE}============================================================${NC}"
    
    # 检查Kafka连接
    if ! check_kafka_connection; then
        echo -e "\n${RED}❌ 无法连接到Kafka，请检查:${NC}"
        echo -e "   1. Kafka服务是否运行"
        echo -e "   2. 服务器地址是否正确: ${BOOTSTRAP_SERVERS}"
        echo -e "   3. 网络连接是否正常"
        return 1
    fi
    
    # 列出所有消费者组
    list_consumer_groups
    
    # 描述目标消费者组
    describe_consumer_group "$CONSUMER_GROUP"
    
    # 提供建议
    echo -e "\n${YELLOW}⚠️  常见问题检查:${NC}"
    echo -e "   1. 是否有多个服务实例在运行？"
    echo -e "   2. 消费者是否频繁重启？"
    echo -e "   3. 网络是否稳定？"
    echo -e "   4. Kafka集群是否正常？"
    
    echo -e "\n${BLUE}📝 修复建议:${NC}"
    echo -e "   1. 停止所有运行中的消费者实例"
    echo -e "   2. 等待30秒，让消费者组完全清理"
    echo -e "   3. 使用此脚本重置消费者组: bash $0 --reset"
    echo -e "   4. 重新启动消费者服务"
    echo -e "   5. 监控日志，确认不再出现重平衡"
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}Kafka消费者组修复脚本${NC}"
    echo ""
    echo -e "${GREEN}快速使用:${NC}"
    echo "  $0 --check-only          # 仅检查问题"
    echo "  $0 --reset               # 检查并修复（需要确认）"
    echo ""
    echo -e "${GREEN}完整参数:${NC}"
    echo "  --reset              重置消费者组（删除组）"
    echo "  --check-only         仅检查问题，不执行修复"
    echo "  --group GROUP_ID     指定消费者组ID（默认: $DEFAULT_CONSUMER_GROUP）"
    echo "  --topic TOPIC        指定主题名称（默认: $DEFAULT_TOPIC）"
    echo "  --bootstrap-servers SERVERS  指定Kafka服务器（默认: $DEFAULT_BOOTSTRAP_SERVERS）"
    echo "  -h, --help           显示帮助信息"
    echo ""
    echo -e "${GREEN}示例:${NC}"
    echo "  $0 --check-only"
    echo "  $0 --reset"
    echo "  $0 --group my-group --reset"
    echo ""
    echo -e "${YELLOW}💡 提示: 执行修复前请先停止所有消费者服务！${NC}"
}

# 主函数
main() {
    local reset=false
    local check_only=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --reset)
                reset=true
                shift
                ;;
            --check-only)
                check_only=true
                shift
                ;;
            --group)
                CONSUMER_GROUP="$2"
                shift 2
                ;;
            --topic)
                TOPIC="$2"
                shift 2
                ;;
            --bootstrap-servers)
                BOOTSTRAP_SERVERS="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知参数: $1${NC}"
                echo ""
                show_usage
                exit 1
                ;;
        esac
    done
    
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}Kafka消费者组修复脚本${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo -e "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "消费者组: ${GREEN}${CONSUMER_GROUP}${NC}"
    echo -e "主题: ${GREEN}${TOPIC}${NC}"
    echo -e "Kafka服务器: ${GREEN}${BOOTSTRAP_SERVERS}${NC}"
    echo -e "${BLUE}============================================================${NC}"
    
    # 如果没有参数，显示使用说明
    if [ "$reset" = false ] && [ "$check_only" = false ]; then
        echo ""
        show_usage
        exit 0
    fi
    
    # 诊断问题
    diagnose
    
    # 如果需要重置
    if [ "$reset" = true ] && [ "$check_only" != true ]; then
        echo ""
        echo -e "${YELLOW}⚠️  重要提示：${NC}"
        echo -e "   1. 请确保已停止所有运行中的消费者服务"
        echo -e "   2. 重置操作会删除消费者组及其偏移量"
        echo -e "   3. 消费者重启后会从最新位置开始消费"
        echo ""
        reset_consumer_group "$CONSUMER_GROUP"
    elif [ "$check_only" = true ]; then
        echo -e "\n${GREEN}✅ 检查完成（未执行修复）${NC}"
        echo -e "${YELLOW}💡 如需修复，请运行: $0 --reset${NC}"
    fi
    
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}脚本执行完成${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# 运行主函数
main "$@"

