#!/bin/bash
#
# 安装 PostgreSQL pg_hba.conf 自动修复服务
# 用于设置开机自启动
#
# 使用方法：
#     sudo bash install_fix_postgresql_service.sh
#
# @author 翱翔的雄库鲁
# @email andywebjava@163.com
# @wechat EasyAIoT2025

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
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

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then
    print_error "请使用 sudo 运行此脚本"
    echo "使用方法: sudo bash install_fix_postgresql_service.sh"
    exit 1
fi

print_section "安装 PostgreSQL pg_hba.conf 自动修复服务"

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/fix_postgresql_pg_hba.service"
AUTO_SCRIPT="$SCRIPT_DIR/fix_postgresql_pg_hba_auto.sh"
FIX_SCRIPT="$SCRIPT_DIR/fix_postgresql_pg_hba.sh"

# 检查必要文件是否存在
print_info "检查必要文件..."
if [ ! -f "$SERVICE_FILE" ]; then
    print_error "服务文件不存在: $SERVICE_FILE"
    exit 1
fi

if [ ! -f "$AUTO_SCRIPT" ]; then
    print_error "自动修复脚本不存在: $AUTO_SCRIPT"
    exit 1
fi

if [ ! -f "$FIX_SCRIPT" ]; then
    print_error "修复脚本不存在: $FIX_SCRIPT"
    exit 1
fi

print_success "所有必要文件都存在"

# 获取当前用户（如果不是 root）
if [ -n "$SUDO_USER" ]; then
    SERVICE_USER="$SUDO_USER"
    SERVICE_GROUP="$SUDO_USER"
else
    # 如果没有 SUDO_USER，尝试从环境变量获取
    SERVICE_USER="${USER:-basiclab}"
    SERVICE_GROUP="${USER:-basiclab}"
fi

print_info "服务将使用用户: $SERVICE_USER"

# 更新服务文件中的用户和组
print_info "更新服务文件配置..."
sed -i "s/^User=.*/User=$SERVICE_USER/" "$SERVICE_FILE"
sed -i "s/^Group=.*/Group=$SERVICE_GROUP/" "$SERVICE_FILE"

# 复制服务文件到 systemd 目录
print_info "复制服务文件到 /etc/systemd/system/..."
cp "$SERVICE_FILE" /etc/systemd/system/fix_postgresql_pg_hba.service
print_success "服务文件已复制"

# 重新加载 systemd
print_info "重新加载 systemd 配置..."
systemctl daemon-reload
print_success "systemd 配置已重新加载"

# 启用服务（开机自启动）
print_info "启用服务（开机自启动）..."
systemctl enable fix_postgresql_pg_hba.service
print_success "服务已设置为开机自启动"

# 显示服务状态
print_section "服务状态"
systemctl status fix_postgresql_pg_hba.service --no-pager || true

print_section "安装完成"
print_success "PostgreSQL pg_hba.conf 自动修复服务已安装并启用"
echo ""
print_info "服务管理命令："
echo "  查看状态: sudo systemctl status fix_postgresql_pg_hba.service"
echo "  手动启动: sudo systemctl start fix_postgresql_pg_hba.service"
echo "  停止服务: sudo systemctl stop fix_postgresql_pg_hba.service"
echo "  禁用服务: sudo systemctl disable fix_postgresql_pg_hba.service"
echo "  查看日志: sudo journalctl -u fix_postgresql_pg_hba.service -f"
echo ""
print_info "服务将在系统启动后自动运行，等待 PostgreSQL 容器启动后执行修复"
echo ""

