#!/bin/bash

# ============================================
# EasyAIoT 文件系统诊断脚本
# ============================================
# 用于诊断 Docker Compose 挂载路径错误和文件系统只读问题
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
    
    print_info "检查路径: $path"
    
    # 获取路径所在的挂载点
    local mount_point=$(df "$path" 2>/dev/null | tail -1 | awk '{print $6}')
    local mount_info=$(df -h "$path" 2>/dev/null | tail -1)
    local filesystem=$(echo "$mount_info" | awk '{print $1}')
    local mount_options=""
    
    print_info "  挂载点: $mount_point"
    print_info "  文件系统: $filesystem"
    
    # 获取挂载选项
    if [ -f /proc/mounts ]; then
        mount_options=$(grep -E "^${filesystem}[[:space:]]" /proc/mounts 2>/dev/null | awk '{print $4}' | head -1 || echo "")
        if [ -n "$mount_options" ]; then
            print_info "  挂载选项: $mount_options"
        fi
    fi
    
    # 检查是否包含 ro (read-only)
    if echo "$mount_options" | grep -qE "(^|,)ro(,|$)"; then
        print_error "  文件系统挂载为只读模式 (ro)"
        return 1
    else
        print_success "  文件系统挂载为可写模式 (rw)"
        return 0
    fi
}

# 检查路径是否存在
check_path_exists() {
    local path="$1"
    local path_type="$2"
    
    if [ -e "$path" ]; then
        if [ -d "$path" ]; then
            print_success "  目录存在: $path"
            return 0
        elif [ -f "$path" ]; then
            print_warning "  路径是文件而非目录: $path"
            return 1
        fi
    else
        print_error "  路径不存在: $path"
        return 1
    fi
}

# 检查路径权限
check_path_permissions() {
    local path="$1"
    
    if [ -e "$path" ]; then
        local perms=$(stat -c "%a" "$path" 2>/dev/null || stat -f "%OLp" "$path" 2>/dev/null || echo "unknown")
        local owner=$(stat -c "%U:%G" "$path" 2>/dev/null || stat -f "%Su:%Sg" "$path" 2>/dev/null || echo "unknown")
        
        print_info "  权限: $perms"
        print_info "  所有者: $owner"
        
        # 检查是否可写
        if [ -w "$path" ]; then
            print_success "  当前用户可写"
        else
            print_error "  当前用户不可写"
        fi
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
        
        if [ "$use_percent" -ge 95 ]; then
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

# 检查 Docker 挂载路径
check_docker_mount_paths() {
    print_section "检查 Docker Compose 挂载路径"
    
    local compose_file="${SCRIPT_DIR}/docker-compose.yml"
    
    if [ ! -f "$compose_file" ]; then
        print_error "docker-compose.yml 文件不存在: $compose_file"
        return 1
    fi
    
    print_info "解析 docker-compose.yml 中的挂载路径..."
    
    # 提取所有 volumes 挂载路径
    local volumes=$(grep -E "^\s+-\s+\"\./" "$compose_file" | sed 's/.*"\(.*\)".*/\1/' | sed 's/:.*//' || echo "")
    
    if [ -z "$volumes" ]; then
        print_warning "未找到挂载路径"
        return 1
    fi
    
    local failed_paths=()
    local success_count=0
    local total_count=0
    
    while IFS= read -r volume_path; do
        if [ -z "$volume_path" ]; then
            continue
        fi
        
        total_count=$((total_count + 1))
        
        # 处理相对路径
        local full_path=""
        if [[ "$volume_path" =~ ^\./ ]]; then
            full_path="${SCRIPT_DIR}/${volume_path#./}"
        elif [[ "$volume_path" =~ ^/ ]]; then
            full_path="$volume_path"
        else
            full_path="${SCRIPT_DIR}/${volume_path}"
        fi
        
        # 规范化路径（移除多余斜杠）
        full_path=$(echo "$full_path" | sed 's|//|/|g')
        
        echo ""
        print_info "检查挂载路径 [$total_count]: $volume_path"
        print_info "  完整路径: $full_path"
        
        # 检查路径中是否有空格（可能导致问题）
        if echo "$volume_path" | grep -q " "; then
            print_error "  路径包含空格，可能导致挂载失败: $volume_path"
            print_info "  建议: 将空格替换为下划线，例如 'srs data' -> 'srs_data'"
            failed_paths+=("$volume_path (包含空格)")
            continue
        fi
        
        # 检查路径是否存在
        local parent_dir=$(dirname "$full_path")
        if [ ! -d "$parent_dir" ]; then
            print_error "  父目录不存在: $parent_dir"
            print_info "  尝试创建父目录..."
            if mkdir -p "$parent_dir" 2>/dev/null; then
                print_success "  父目录创建成功"
            else
                print_error "  父目录创建失败"
                failed_paths+=("$full_path (父目录创建失败)")
                continue
            fi
        fi
        
        # 检查路径是否存在
        if ! check_path_exists "$full_path" "directory"; then
            print_info "  尝试创建目录..."
            if mkdir -p "$full_path" 2>/dev/null; then
                print_success "  目录创建成功"
            else
                print_error "  目录创建失败"
                failed_paths+=("$full_path (创建失败)")
                continue
            fi
        fi
        
        # 检查文件系统是否可写
        if ! check_filesystem_writable "$full_path"; then
            print_error "  文件系统不可写"
            failed_paths+=("$full_path (文件系统不可写)")
            check_filesystem_mount_status "$full_path"
            continue
        fi
        
        # 检查权限
        check_path_permissions "$full_path"
        
        # 检查挂载状态
        check_filesystem_mount_status "$full_path"
        
        success_count=$((success_count + 1))
        print_success "  路径检查通过: $full_path"
        
    done <<< "$volumes"
    
    echo ""
    print_section "挂载路径检查结果"
    print_info "成功: ${GREEN}$success_count${NC} / $total_count"
    
    if [ ${#failed_paths[@]} -gt 0 ]; then
        print_error "失败的路径:"
        for failed_path in "${failed_paths[@]}"; do
            print_error "  - $failed_path"
        done
        return 1
    else
        print_success "所有挂载路径检查通过！"
        return 0
    fi
}

# 检查项目根目录路径
check_project_root() {
    print_section "检查项目根目录路径"
    
    local project_root="/opt/projects/easyaiot"
    local error_path="/opt/eayaiot"  # 错误的路径（拼写错误）
    
    print_info "检查正确的项目路径: $project_root"
    if [ -d "$project_root" ]; then
        print_success "项目根目录存在: $project_root"
        check_filesystem_mount_status "$project_root"
        check_disk_space "$project_root"
    else
        print_error "项目根目录不存在: $project_root"
    fi
    
    echo ""
    print_info "检查错误的项目路径: $error_path"
    if [ -d "$error_path" ]; then
        print_warning "发现错误的路径（拼写错误）: $error_path"
        print_info "  这可能是导致挂载失败的原因"
        print_info "  建议: 检查 docker-compose.yml 中的路径配置"
    else
        print_info "错误的路径不存在（正常）"
    fi
}

# 检查 Docker 服务状态
check_docker_service() {
    print_section "检查 Docker 服务状态"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        return 1
    fi
    
    print_success "Docker 已安装: $(docker --version)"
    
    # 检查 Docker 服务是否运行
    if systemctl is-active --quiet docker 2>/dev/null || pgrep -x dockerd > /dev/null 2>&1; then
        print_success "Docker 服务正在运行"
    else
        print_error "Docker 服务未运行"
        print_info "启动命令: sudo systemctl start docker"
        return 1
    fi
    
    # 检查 Docker 权限
    if docker ps &> /dev/null; then
        print_success "Docker 权限正常"
    else
        print_error "Docker 权限不足"
        print_info "解决方案: sudo usermod -aG docker $USER"
        return 1
    fi
}

# 提供修复建议
provide_fix_suggestions() {
    print_section "修复建议"
    
    echo ""
    print_warning "如果文件系统是只读的，请尝试以下方法："
    echo ""
    print_info "1. 检查文件系统挂载状态:"
    print_info "   mount | grep $(df "$SCRIPT_DIR" 2>/dev/null | tail -1 | awk '{print $1}')"
    echo ""
    print_info "2. 如果是只读挂载，重新挂载为可写:"
    print_info "   sudo mount -o remount,rw $(df "$SCRIPT_DIR" 2>/dev/null | tail -1 | awk '{print $1}')"
    echo ""
    print_info "3. 检查磁盘空间是否已满:"
    print_info "   df -h"
    echo ""
    print_info "4. 检查文件系统错误:"
    print_info "   sudo fsck -n $(df "$SCRIPT_DIR" 2>/dev/null | tail -1 | awk '{print $1}')"
    echo ""
    print_warning "如果路径包含空格，请修改 docker-compose.yml:"
    echo ""
    print_info "  将 'srs data' 改为 'srs_data'"
    print_info "  将路径中的空格替换为下划线"
    echo ""
    print_warning "如果路径拼写错误，请检查:"
    echo ""
    print_info "  确保路径为: /opt/projects/easyaiot"
    print_info "  而不是: /opt/eayaiot 或其他错误路径"
    echo ""
}

# 主函数
main() {
    print_section "EasyAIoT 文件系统诊断工具"
    
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 检查 Docker 服务
    check_docker_service
    echo ""
    
    # 检查项目根目录
    check_project_root
    echo ""
    
    # 检查 Docker 挂载路径
    check_docker_mount_paths
    echo ""
    
    # 提供修复建议
    provide_fix_suggestions
    
    echo ""
    print_section "诊断完成"
    echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
}

# 运行主函数
main "$@"

