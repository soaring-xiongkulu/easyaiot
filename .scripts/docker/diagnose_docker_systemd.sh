#!/bin/bash

# ============================================
# Docker systemd 服务诊断和修复脚本
# ============================================
# 用于诊断和修复 Docker 服务无法启动的问题
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查是否为 root 用户
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "此脚本需要 root 权限运行"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 诊断 systemd 状态
diagnose_systemd() {
    print_section "诊断 systemd 状态"
    
    print_info "检查 systemd 守护进程状态..."
    if systemctl is-system-running &> /dev/null; then
        systemctl_status=$(systemctl is-system-running)
        print_info "systemd 状态: $systemctl_status"
    else
        print_error "无法获取 systemd 状态"
    fi
    
    print_info "检查 systemd 日志..."
    journalctl --since "10 minutes ago" -u systemd --no-pager | tail -20 || true
    
    echo ""
    print_info "检查 systemd 服务超时配置..."
    timeout_config=$(systemctl show -p TimeoutStartSec docker.service 2>/dev/null || echo "未配置")
    print_info "Docker 服务启动超时配置: $timeout_config"
}

# 诊断 Docker 服务
diagnose_docker_service() {
    print_section "诊断 Docker 服务"
    
    print_info "检查 Docker 服务单元文件..."
    if [ -f /etc/systemd/system/docker.service ]; then
        print_success "Docker 服务单元文件存在: /etc/systemd/system/docker.service"
        echo ""
        print_info "服务单元文件内容:"
        cat /etc/systemd/system/docker.service | head -30
    elif [ -f /lib/systemd/system/docker.service ]; then
        print_success "Docker 服务单元文件存在: /lib/systemd/system/docker.service"
        echo ""
        print_info "服务单元文件内容:"
        cat /lib/systemd/system/docker.service | head -30
    else
        print_error "未找到 Docker 服务单元文件"
    fi
    
    echo ""
    print_info "检查 Docker 服务状态..."
    systemctl status docker.service --no-pager -l || true
    
    echo ""
    print_info "检查 Docker 服务日志..."
    journalctl -u docker.service --since "10 minutes ago" --no-pager | tail -30 || true
}

# 诊断系统资源
diagnose_resources() {
    print_section "诊断系统资源"
    
    print_info "检查磁盘空间..."
    df -h / | tail -1
    
    echo ""
    print_info "检查内存使用..."
    free -h
    
    echo ""
    print_info "检查 inotify 限制..."
    if [ -f /proc/sys/fs/inotify/max_user_instances ]; then
        print_info "max_user_instances: $(cat /proc/sys/fs/inotify/max_user_instances)"
    fi
    if [ -f /proc/sys/fs/inotify/max_user_watches ]; then
        print_info "max_user_watches: $(cat /proc/sys/fs/inotify/max_user_watches)"
    fi
    
    echo ""
    print_info "检查进程数量..."
    process_count=$(ps aux | wc -l)
    print_info "当前进程数: $process_count"
}

# 诊断 Docker 相关文件
diagnose_docker_files() {
    print_section "诊断 Docker 相关文件"
    
    print_info "检查 Docker 二进制文件..."
    if command -v docker &> /dev/null; then
        docker_path=$(which docker)
        print_success "Docker 二进制文件: $docker_path"
        ls -lh "$docker_path" || true
    else
        print_error "Docker 二进制文件未找到"
    fi
    
    echo ""
    print_info "检查 Docker 数据目录..."
    if [ -d /var/lib/docker ]; then
        print_info "Docker 数据目录: /var/lib/docker"
        du -sh /var/lib/docker 2>/dev/null || print_warning "无法读取 Docker 数据目录大小"
    else
        print_warning "Docker 数据目录不存在"
    fi
    
    echo ""
    print_info "检查 Docker socket..."
    if [ -S /var/run/docker.sock ]; then
        print_success "Docker socket 存在: /var/run/docker.sock"
        ls -lh /var/run/docker.sock
    else
        print_warning "Docker socket 不存在"
    fi
}

# 修复 systemd 超时问题
fix_systemd_timeout() {
    print_section "修复 systemd 超时问题"
    
    print_info "重新加载 systemd 守护进程..."
    systemctl daemon-reload
    
    print_info "重置失败的 systemd 服务..."
    systemctl reset-failed
    
    print_info "增加 Docker 服务启动超时时间..."
    
    # 创建或更新 Docker 服务覆盖目录
    mkdir -p /etc/systemd/system/docker.service.d
    
    # 创建超时配置文件
    cat > /etc/systemd/system/docker.service.d/timeout.conf << 'EOF'
[Service]
TimeoutStartSec=300
TimeoutStopSec=60
EOF
    
    print_success "已创建超时配置文件: /etc/systemd/system/docker.service.d/timeout.conf"
    
    print_info "重新加载 systemd 配置..."
    systemctl daemon-reload
    
    print_success "systemd 超时配置已更新"
}

# 修复 Docker 服务
fix_docker_service() {
    print_section "修复 Docker 服务"
    
    print_info "停止可能存在的 Docker 进程..."
    pkill -9 dockerd 2>/dev/null || true
    pkill -9 docker-containerd 2>/dev/null || true
    pkill -9 docker-containerd-shim 2>/dev/null || true
    sleep 2
    
    print_info "清理 Docker socket..."
    rm -f /var/run/docker.sock
    rm -f /var/run/docker.pid
    
    print_info "重置 Docker 服务状态..."
    systemctl reset-failed docker.service
    
    print_info "尝试启动 Docker 服务..."
    if systemctl start docker.service; then
        print_success "Docker 服务启动成功"
        sleep 3
        
        print_info "验证 Docker 服务..."
        if systemctl is-active --quiet docker.service; then
            print_success "Docker 服务运行正常"
            docker --version
            return 0
        else
            print_error "Docker 服务启动后未正常运行"
            return 1
        fi
    else
        print_error "Docker 服务启动失败"
        print_info "查看详细错误信息..."
        journalctl -u docker.service --no-pager -n 50
        return 1
    fi
}

# 尝试替代启动方法
try_alternative_start() {
    print_section "尝试替代启动方法"
    
    print_info "尝试直接启动 dockerd..."
    if command -v dockerd &> /dev/null; then
        dockerd_path=$(which dockerd)
        print_info "dockerd 路径: $dockerd_path"
        
        print_warning "尝试在后台启动 dockerd（仅用于测试）..."
        print_warning "如果成功，请检查 systemd 配置"
        
        # 注意：这只是诊断，不应该长期使用
        print_info "检查 dockerd 是否可以手动启动..."
        timeout 5 $dockerd_path --version 2>&1 || print_warning "dockerd 无法直接运行"
    else
        print_error "dockerd 未找到"
    fi
}

# 主诊断流程
main() {
    echo "============================================"
    echo "Docker systemd 服务诊断和修复工具"
    echo "============================================"
    echo ""
    
    # 检查 root 权限
    if [ "$EUID" -ne 0 ]; then
        print_warning "某些操作需要 root 权限"
        print_info "建议使用: sudo $0"
        echo ""
    fi
    
    # 执行诊断
    diagnose_systemd
    diagnose_docker_service
    diagnose_resources
    diagnose_docker_files
    
    echo ""
    print_section "诊断完成"
    echo ""
    echo "如果发现问题，可以尝试以下修复方法："
    echo ""
    echo "1. 修复 systemd 超时问题："
    echo "   sudo $0 fix-timeout"
    echo ""
    echo "2. 修复 Docker 服务："
    echo "   sudo $0 fix-service"
    echo ""
    echo "3. 执行所有修复："
    echo "   sudo $0 fix-all"
    echo ""
}

# 修复流程
fix_all() {
    check_root
    
    print_section "执行所有修复"
    
    fix_systemd_timeout
    fix_docker_service
    
    print_section "修复完成"
    
    print_info "验证 Docker 服务状态..."
    systemctl status docker.service --no-pager -l || true
}

# 命令行参数处理
case "${1:-diagnose}" in
    diagnose)
        main
        ;;
    fix-timeout)
        check_root
        fix_systemd_timeout
        ;;
    fix-service)
        check_root
        fix_docker_service
        ;;
    fix-all)
        fix_all
        ;;
    help|--help|-h)
        echo "Docker systemd 服务诊断和修复工具"
        echo ""
        echo "使用方法:"
        echo "  $0 [命令]"
        echo ""
        echo "可用命令:"
        echo "  diagnose      - 诊断问题（默认）"
        echo "  fix-timeout   - 修复 systemd 超时问题（需要 root）"
        echo "  fix-service   - 修复 Docker 服务（需要 root）"
        echo "  fix-all        - 执行所有修复（需要 root）"
        echo "  help          - 显示此帮助信息"
        echo ""
        ;;
    *)
        print_error "未知命令: $1"
        echo ""
        echo "使用 '$0 help' 查看帮助信息"
        exit 1
        ;;
esac

