#!/bin/bash

# ============================================
# EasyAIoT 只读文件系统修复脚本
# ============================================
# 用于修复 Docker Compose 挂载路径的文件系统只读问题
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
}

# 检查文件系统是否可写
check_filesystem_writable() {
    local test_path="$1"
    local test_file=""
    
    if [ -d "$test_path" ]; then
        test_file="${test_path}/.write_test_$$"
    else
        local parent_dir=$(dirname "$test_path")
        if [ ! -d "$parent_dir" ]; then
            mkdir -p "$parent_dir" 2>/dev/null || return 1
        fi
        test_file="${parent_dir}/.write_test_$$"
    fi
    
    if touch "$test_file" 2>/dev/null; then
        rm -f "$test_file" 2>/dev/null
        return 0
    else
        return 1
    fi
}

# 检查文件系统挂载状态
check_filesystem_mount_status() {
    local path="$1"
    
    # 获取路径所在的挂载点
    local mount_info=$(df "$path" 2>/dev/null | tail -1)
    local filesystem=$(echo "$mount_info" | awk '{print $1}')
    local mount_point=$(echo "$mount_info" | awk '{print $6}')
    local mount_options=""
    
    # 获取挂载选项
    if [ -f /proc/mounts ]; then
        mount_options=$(grep -E "^${filesystem}[[:space:]]" /proc/mounts 2>/dev/null | awk '{print $4}' | head -1 || echo "")
    fi
    
    echo "$filesystem|$mount_point|$mount_options"
}

# 尝试重新挂载为可写
remount_readwrite() {
    local path="$1"
    
    print_info "尝试重新挂载文件系统为可写模式..."
    
    local mount_info=$(check_filesystem_mount_status "$path")
    local filesystem=$(echo "$mount_info" | cut -d'|' -f1)
    local mount_point=$(echo "$mount_info" | cut -d'|' -f2)
    local mount_options=$(echo "$mount_info" | cut -d'|' -f3)
    
    if [ -z "$filesystem" ] || [ -z "$mount_point" ]; then
        print_error "无法获取文件系统信息"
        return 1
    fi
    
    print_info "文件系统: $filesystem"
    print_info "挂载点: $mount_point"
    print_info "当前挂载选项: $mount_options"
    
    # 检查是否已经是可写模式
    if echo "$mount_options" | grep -qE "(^|,)rw(,|$)"; then
        print_success "文件系统已经是可写模式"
        return 0
    fi
    
    # 检查是否包含 ro (read-only)
    if echo "$mount_options" | grep -qE "(^|,)ro(,|$)"; then
        print_warning "文件系统挂载为只读模式，尝试重新挂载为可写..."
        
        # 尝试重新挂载
        if sudo mount -o remount,rw "$mount_point" 2>/dev/null; then
            print_success "文件系统已重新挂载为可写模式"
            
            # 验证是否成功
            sleep 1
            local new_mount_info=$(check_filesystem_mount_status "$path")
            local new_mount_options=$(echo "$new_mount_info" | cut -d'|' -f3)
            
            if echo "$new_mount_options" | grep -qE "(^|,)rw(,|$)"; then
                print_success "验证成功：文件系统现在可写"
                return 0
            else
                print_error "验证失败：文件系统仍然只读"
                return 1
            fi
        else
            print_error "重新挂载失败"
            print_warning "可能需要检查文件系统错误或磁盘空间"
            return 1
        fi
    else
        print_warning "无法确定文件系统挂载状态"
        return 1
    fi
}

# 创建所有必要的目录
create_required_directories() {
    print_section "创建必要的目录"
    
    local storage_dirs=(
        "${SCRIPT_DIR}/standalone-logs"
        "${SCRIPT_DIR}/db_data/data"
        "${SCRIPT_DIR}/db_data/log"
        "${SCRIPT_DIR}/taos_data/data"
        "${SCRIPT_DIR}/taos_data/log"
        "${SCRIPT_DIR}/redis_data/data"
        "${SCRIPT_DIR}/redis_data/logs"
        "${SCRIPT_DIR}/mq_data/data"
        "${SCRIPT_DIR}/minio_data/data"
        "${SCRIPT_DIR}/minio_data/config"
        "${SCRIPT_DIR}/srs_data/conf"
        "${SCRIPT_DIR}/srs_data/data"
        "${SCRIPT_DIR}/nodered_data/data"
    )
    
    local created_count=0
    local failed_count=0
    
    for dir_path in "${storage_dirs[@]}"; do
        if [ -z "$dir_path" ]; then
            continue
        fi
        
        print_info "创建目录: $dir_path"
        
        # 检查父目录是否可写
        local parent_dir=$(dirname "$dir_path")
        if ! check_filesystem_writable "$parent_dir"; then
            print_error "父目录不可写: $parent_dir"
            failed_count=$((failed_count + 1))
            continue
        fi
        
        # 创建目录
        if mkdir -p "$dir_path" 2>/dev/null; then
            print_success "目录创建成功: $dir_path"
            created_count=$((created_count + 1))
            
            # 尝试设置权限（如果可能）
            if [ "$EUID" -eq 0 ]; then
                chmod -R 777 "$dir_path" 2>/dev/null || true
            elif command -v sudo &> /dev/null; then
                sudo chmod -R 777 "$dir_path" 2>/dev/null || true
            fi
        else
            print_error "目录创建失败: $dir_path"
            failed_count=$((failed_count + 1))
        fi
    done
    
    echo ""
    print_info "创建结果: 成功 $created_count, 失败 $failed_count"
    
    if [ $failed_count -gt 0 ]; then
        return 1
    else
        return 0
    fi
}

# 检查磁盘空间
check_disk_space() {
    local path="$1"
    
    print_info "检查磁盘空间: $path"
    
    local df_output=$(df -h "$path" 2>/dev/null | tail -1)
    if [ -n "$df_output" ]; then
        local total=$(echo "$df_output" | awk '{print $2}')
        local used=$(echo "$df_output" | awk '{print $3}')
        local available=$(echo "$df_output" | awk '{print $4}')
        local use_percent=$(echo "$df_output" | awk '{print $5}' | sed 's/%//')
        
        print_info "  总空间: $total"
        print_info "  已用: $used"
        print_info "  可用: $available"
        print_info "  使用率: ${use_percent}%"
        
        if [ "$use_percent" -ge 100 ]; then
            print_error "  磁盘空间已满（使用率 >= 100%）"
            print_warning "  这可能是文件系统只读的原因"
            return 1
        elif [ "$use_percent" -ge 95 ]; then
            print_error "  磁盘空间严重不足（使用率 >= 95%）"
            return 1
        elif [ "$use_percent" -ge 90 ]; then
            print_warning "  磁盘空间不足（使用率 >= 90%）"
            return 1
        else
            print_success "  磁盘空间充足"
            return 0
        fi
    else
        print_error "  无法获取磁盘空间信息"
        return 1
    fi
}

# 检查文件系统错误
check_filesystem_errors() {
    local path="$1"
    
    print_info "检查文件系统错误..."
    
    local mount_info=$(check_filesystem_mount_status "$path")
    local filesystem=$(echo "$mount_info" | cut -d'|' -f1)
    
    if [ -z "$filesystem" ]; then
        print_error "无法获取文件系统信息"
        return 1
    fi
    
    print_info "文件系统: $filesystem"
    print_warning "运行文件系统检查（只读模式，不会修改）..."
    
    if sudo fsck -n "$filesystem" 2>&1 | grep -q "clean"; then
        print_success "文件系统检查通过，没有错误"
        return 0
    else
        print_warning "文件系统可能存在问题"
        print_info "如果需要修复，请运行: sudo fsck -y $filesystem"
        print_warning "注意：修复文件系统可能需要卸载文件系统，请谨慎操作"
        return 1
    fi
}

# 主修复流程
main_fix() {
    print_section "EasyAIoT 只读文件系统修复工具"
    
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 检查当前目录的文件系统状态
    print_section "检查文件系统状态"
    
    if check_filesystem_writable "$SCRIPT_DIR"; then
        print_success "文件系统可写，无需修复"
        echo ""
        # 即使可写，也尝试创建目录
        create_required_directories
        return 0
    else
        print_error "文件系统不可写，需要修复"
    fi
    
    # 检查磁盘空间
    if ! check_disk_space "$SCRIPT_DIR"; then
        print_error "磁盘空间问题可能导致文件系统只读"
        print_warning "请先解决磁盘空间问题"
        return 1
    fi
    
    # 检查文件系统错误
    check_filesystem_errors "$SCRIPT_DIR"
    echo ""
    
    # 尝试重新挂载为可写
    print_section "尝试修复文件系统"
    
    if remount_readwrite "$SCRIPT_DIR"; then
        print_success "文件系统修复成功"
        echo ""
        
        # 验证是否可写
        if check_filesystem_writable "$SCRIPT_DIR"; then
            print_success "验证成功：文件系统现在可写"
            echo ""
            
            # 创建必要的目录
            if create_required_directories; then
                print_success "所有目录创建成功"
                return 0
            else
                print_error "部分目录创建失败"
                return 1
            fi
        else
            print_error "验证失败：文件系统仍然不可写"
            return 1
        fi
    else
        print_error "文件系统修复失败"
        echo ""
        print_warning "可能的解决方案："
        echo "  1. 检查磁盘空间是否已满"
        echo "  2. 检查文件系统错误: sudo fsck -n $(df \"$SCRIPT_DIR\" 2>/dev/null | tail -1 | awk '{print $1}')"
        echo "  3. 检查文件系统挂载配置: cat /etc/fstab"
        echo "  4. 如果是在容器中，检查容器挂载配置"
        echo "  5. 考虑将数据目录移动到其他可写位置（如 /data 或 /var/lib/docker/volumes）"
        return 1
    fi
}

# 主函数
main() {
    # 检查是否以 root 或 sudo 运行
    if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
        print_warning "某些操作需要 root 权限"
        print_info "如果遇到权限问题，请使用: sudo $0"
        echo ""
    fi
    
    if main_fix; then
        echo ""
        print_section "修复完成"
        print_success "文件系统修复成功，现在可以运行 docker-compose up -d"
        echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
        return 0
    else
        echo ""
        print_section "修复失败"
        print_error "文件系统修复失败，请检查上述错误信息"
        echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
        return 1
    fi
}

# 运行主函数
main "$@"

