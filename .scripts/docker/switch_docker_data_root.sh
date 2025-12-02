#!/bin/bash

# ============================================
# Docker Data-Root 切换脚本
# ============================================
# 用于切换 Docker 的 data-root 目录
# 支持数据迁移和配置更新
# 使用方法：
#   ./switch_docker_data_root.sh <新路径>
#   例如: ./switch_docker_data_root.sh /data/docker
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "此脚本需要 root 权限运行"
        echo ""
        echo "请使用以下命令运行:"
        echo "  sudo $0 $@"
        exit 1
    fi
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        exit 1
    fi
}

# 获取当前 Docker data-root
get_current_data_root() {
    local docker_data_root=""
    
    # 方法1: 从 daemon.json 读取
    if [ -f "/etc/docker/daemon.json" ]; then
        docker_data_root=$(python3 << 'EOF'
import json
try:
    with open('/etc/docker/daemon.json', 'r') as f:
        config = json.load(f)
        data_root = config.get('data-root', '')
        if data_root:
            print(data_root)
except:
    pass
EOF
)
    fi
    
    # 方法2: 从 docker info 获取
    if [ -z "$docker_data_root" ] && docker info &> /dev/null 2>&1; then
        docker_data_root=$(docker info 2>/dev/null | grep -i "Docker Root Dir" | awk '{print $4}' || echo "")
    fi
    
    # 方法3: 默认路径
    if [ -z "$docker_data_root" ]; then
        if [ -d "/var/lib/docker" ]; then
            docker_data_root="/var/lib/docker"
        elif [ -d "/var/snap/docker/common/var-lib-docker" ]; then
            docker_data_root="/var/snap/docker/common/var-lib-docker"
        fi
    fi
    
    echo "$docker_data_root"
}

# 验证新路径
validate_new_path() {
    local new_path=$1
    
    if [ -z "$new_path" ]; then
        print_error "新路径不能为空"
        return 1
    fi
    
    # 检查路径格式
    if [[ ! "$new_path" =~ ^/ ]]; then
        print_error "路径必须是绝对路径（以 / 开头）"
        return 1
    fi
    
    # 检查路径是否包含特殊字符
    if [[ "$new_path" =~ [\ \t] ]]; then
        print_error "路径不能包含空格"
        return 1
    fi
    
    # 检查父目录是否存在
    local parent_dir=$(dirname "$new_path")
    if [ ! -d "$parent_dir" ]; then
        print_warning "父目录不存在: $parent_dir"
        read -p "是否创建父目录? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$parent_dir" || {
                print_error "创建父目录失败"
                return 1
            }
            print_success "已创建父目录: $parent_dir"
        else
            return 1
        fi
    fi
    
    # 检查是否有足够的空间
    local available_space=$(df -B1 "$parent_dir" 2>/dev/null | tail -1 | awk '{print $4}')
    if [ -n "$available_space" ] && [ "$available_space" -lt 1073741824 ]; then  # 小于 1GB
        print_warning "目标目录所在磁盘可用空间不足 1GB"
        read -p "是否继续? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    return 0
}

# 停止 Docker 服务
stop_docker_service() {
    print_section "停止 Docker 服务"
    
    if systemctl is-active --quiet docker 2>/dev/null; then
        print_info "正在停止 Docker 服务..."
        systemctl stop docker || {
            print_error "停止 Docker 服务失败"
            return 1
        }
        print_success "Docker 服务已停止"
    else
        print_warning "Docker 服务未运行"
    fi
    
    # 等待服务完全停止
    sleep 2
    
    # 检查是否还有 docker 进程
    if pgrep -x dockerd > /dev/null 2>&1; then
        print_warning "检测到 Docker 进程仍在运行，强制终止..."
        pkill -9 dockerd || true
        sleep 2
    fi
}

# 迁移数据
migrate_data() {
    local old_path=$1
    local new_path=$2
    local migrate=$3
    
    if [ "$migrate" != "true" ]; then
        print_info "跳过数据迁移（仅更新配置）"
        return 0
    fi
    
    print_section "迁移 Docker 数据"
    
    if [ ! -d "$old_path" ]; then
        print_warning "源目录不存在: $old_path，跳过迁移"
        return 0
    fi
    
    if [ -d "$new_path" ] && [ "$(ls -A $new_path 2>/dev/null)" ]; then
        print_warning "目标目录已存在且不为空: $new_path"
        read -p "是否覆盖? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "迁移已取消"
            return 1
        fi
        print_info "清理目标目录..."
        rm -rf "$new_path"/*
    fi
    
    # 创建目标目录
    mkdir -p "$new_path" || {
        print_error "创建目标目录失败"
        return 1
    }
    
    # 计算源目录大小
    print_info "正在计算需要迁移的数据大小..."
    local source_size=$(du -sb "$old_path" 2>/dev/null | awk '{print $1}')
    if command -v awk &> /dev/null; then
        local source_size_gb=$(awk "BEGIN {printf \"%.2f\", $source_size/1024/1024/1024}")
    else
        local source_size_gb=$((source_size / 1024 / 1024 / 1024))
    fi
    print_info "需要迁移的数据大小: ${source_size_gb} GB"
    
    # 确认迁移
    read -p "确认开始迁移数据? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "迁移已取消"
        return 1
    fi
    
    # 使用 rsync 迁移数据（保留权限和属性）
    print_info "开始迁移数据（这可能需要较长时间）..."
    print_info "使用 rsync 进行迁移，保留所有文件属性和权限..."
    
    rsync -aAXv --progress "$old_path/" "$new_path/" || {
        print_error "数据迁移失败"
        return 1
    }
    
    print_success "数据迁移完成"
    
    # 验证迁移
    print_info "验证迁移结果..."
    local old_count=$(find "$old_path" -type f 2>/dev/null | wc -l)
    local new_count=$(find "$new_path" -type f 2>/dev/null | wc -l)
    
    if [ "$old_count" -eq "$new_count" ]; then
        print_success "文件数量验证通过: $new_count 个文件"
    else
        print_warning "文件数量不一致: 源目录 $old_count 个，目标目录 $new_count 个"
    fi
}

# 更新 Docker 配置
update_docker_config() {
    local new_path=$1
    
    print_section "更新 Docker 配置"
    
    local docker_config_dir="/etc/docker"
    local docker_config_file="$docker_config_dir/daemon.json"
    
    # 创建配置目录
    mkdir -p "$docker_config_dir" || {
        print_error "创建配置目录失败"
        return 1
    }
    
    # 读取现有配置
    local config_content="{}"
    if [ -f "$docker_config_file" ]; then
        config_content=$(cat "$docker_config_file")
        print_info "读取现有配置文件: $docker_config_file"
    else
        print_info "创建新配置文件: $docker_config_file"
    fi
    
    # 使用 Python 更新配置
    python3 << EOF
import json
import sys

config_file = "$docker_config_file"
data_root = "$new_path"

try:
    config = json.loads('''$config_content''')
except:
    config = {}

config["data-root"] = data_root

try:
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("CONFIG_UPDATED")
except Exception as e:
    print(f"CONFIG_ERROR:{e}", file=sys.stderr)
    sys.exit(1)
EOF
    
    if [ $? -ne 0 ]; then
        print_error "更新 Docker 配置失败"
        return 1
    fi
    
    print_success "Docker 配置已更新"
    print_info "新 data-root: $new_path"
}

# 启动 Docker 服务
start_docker_service() {
    print_section "启动 Docker 服务"
    
    print_info "重新加载 systemd 配置..."
    systemctl daemon-reload || {
        print_error "重新加载 systemd 配置失败"
        return 1
    }
    
    print_info "启动 Docker 服务..."
    systemctl start docker || {
        print_error "启动 Docker 服务失败"
        return 1
    }
    
    # 等待服务启动
    sleep 3
    
    # 验证服务状态
    if systemctl is-active --quiet docker; then
        print_success "Docker 服务已启动"
    else
        print_error "Docker 服务启动失败"
        print_info "请检查日志: journalctl -u docker"
        return 1
    fi
    
    # 验证 data-root
    local actual_data_root=$(docker info 2>/dev/null | grep -i "Docker Root Dir" | awk '{print $4}' || echo "")
    if [ -n "$actual_data_root" ]; then
        print_info "实际使用的 data-root: $actual_data_root"
    fi
}

# 显示使用帮助
show_usage() {
    echo "用法: $0 <新路径> [选项]"
    echo ""
    echo "参数:"
    echo "  新路径              新的 Docker data-root 路径（必须是绝对路径）"
    echo ""
    echo "选项:"
    echo "  --no-migrate       不迁移数据，仅更新配置（新目录必须为空或不存在）"
    echo "  --help, -h         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 /data/docker                    # 切换并迁移数据"
    echo "  $0 /data/docker --no-migrate        # 仅切换配置，不迁移数据"
    echo ""
}

# 主函数
main() {
    # 解析参数
    local new_path=""
    local migrate_data=true
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --no-migrate)
                migrate_data=false
                shift
                ;;
            -*)
                print_error "未知选项: $1"
                show_usage
                exit 1
                ;;
            *)
                if [ -z "$new_path" ]; then
                    new_path="$1"
                else
                    print_error "多余参数: $1"
                    show_usage
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # 检查参数
    if [ -z "$new_path" ]; then
        print_error "缺少新路径参数"
        show_usage
        exit 1
    fi
    
    # 显示标题
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  Docker Data-Root 切换工具${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 检查权限
    check_root
    
    # 检查 Docker
    check_docker
    
    # 获取当前 data-root
    local current_data_root=$(get_current_data_root)
    if [ -z "$current_data_root" ]; then
        print_error "无法检测当前 Docker data-root"
        exit 1
    fi
    
    print_info "当前 Docker data-root: $current_data_root"
    print_info "目标 Docker data-root: $new_path"
    
    # 检查是否相同
    if [ "$current_data_root" = "$new_path" ]; then
        print_warning "目标路径与当前路径相同，无需切换"
        exit 0
    fi
    
    # 验证新路径
    if ! validate_new_path "$new_path"; then
        print_error "新路径验证失败"
        exit 1
    fi
    
    # 确认操作
    echo ""
    print_warning "此操作将："
    echo "  1. 停止 Docker 服务"
    if [ "$migrate_data" = "true" ]; then
        echo "  2. 迁移数据从 $current_data_root 到 $new_path"
    else
        echo "  2. 仅更新配置（不迁移数据）"
    fi
    echo "  3. 更新 Docker 配置"
    echo "  4. 重启 Docker 服务"
    echo ""
    read -p "确认继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "操作已取消"
        exit 0
    fi
    
    # 执行切换
    stop_docker_service || exit 1
    migrate_data "$current_data_root" "$new_path" "$migrate_data" || exit 1
    update_docker_config "$new_path" || exit 1
    start_docker_service || exit 1
    
    echo ""
    print_section "切换完成"
    print_success "Docker data-root 已成功切换到: $new_path"
    
    if [ "$migrate_data" = "true" ]; then
        echo ""
        print_warning "注意："
        echo "  1. 原数据目录 $current_data_root 仍然存在"
        echo "  2. 确认新配置正常工作后，可以手动删除原目录以释放空间"
        echo "  3. 删除前请确保已备份重要数据"
    fi
    
    echo ""
    echo "完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# 运行主函数
main "$@"

