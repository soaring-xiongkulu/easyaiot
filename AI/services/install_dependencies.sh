#!/bin/bash

# ============================================
# 安装部署服务依赖脚本
# ============================================
# 此脚本用于安装部署服务所需的Python依赖包
# 使用方法：
#   sudo ./install_dependencies.sh
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
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

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    print_error "请使用sudo运行此脚本"
    echo "使用方法: sudo ./install_dependencies.sh"
    exit 1
fi

# 检查requirements.txt是否存在
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    print_error "requirements.txt文件不存在: $REQUIREMENTS_FILE"
    exit 1
fi

print_info "开始安装部署服务依赖..."
print_info "依赖文件: $REQUIREMENTS_FILE"

CONDA_ENV_NAME="AI-SVC"
USE_CONDA=false

# 检查conda是否可用
if command -v conda &> /dev/null; then
    print_info "检测到conda，检查conda环境: $CONDA_ENV_NAME"
    
    # 检查conda环境是否存在
    if conda env list | grep -q "^${CONDA_ENV_NAME}\s"; then
        USE_CONDA=true
        print_success "找到conda环境: $CONDA_ENV_NAME"
    else
        print_warning "conda环境 $CONDA_ENV_NAME 不存在，将使用系统pip"
    fi
else
    print_info "conda未找到，将使用系统pip"
fi

# 安装依赖
if [ "$USE_CONDA" = true ]; then
    print_info "在conda环境 $CONDA_ENV_NAME 中安装依赖..."
    if conda run -n "$CONDA_ENV_NAME" pip install -r "$REQUIREMENTS_FILE"; then
        print_success "依赖安装成功（conda环境）！"
        
        # 验证关键依赖是否安装
        print_info "验证关键依赖..."
        if conda run -n "$CONDA_ENV_NAME" python -c "import flask_cors" 2>/dev/null; then
            print_success "flask-cors 已安装"
        else
            print_warning "flask-cors 验证失败，但可能已安装"
        fi
        
        if conda run -n "$CONDA_ENV_NAME" python -c "import flask" 2>/dev/null; then
            print_success "flask 已安装"
        else
            print_warning "flask 验证失败，但可能已安装"
        fi
    else
        print_error "依赖安装失败（conda环境）"
        exit 1
    fi
else
    # 使用系统pip安装（需要--break-system-packages）
    print_info "使用系统pip安装依赖（需要--break-system-packages）..."
    
    # 检查pip3是否可用
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3未找到，请先安装Python3和pip"
        exit 1
    fi
    
    if pip3 install --break-system-packages -r "$REQUIREMENTS_FILE"; then
        print_success "依赖安装成功！"
        
        # 验证关键依赖是否安装
        print_info "验证关键依赖..."
        if python3 -c "import flask_cors" 2>/dev/null; then
            print_success "flask-cors 已安装"
        else
            print_warning "flask-cors 验证失败，但可能已安装"
        fi
        
        if python3 -c "import flask" 2>/dev/null; then
            print_success "flask 已安装"
        else
            print_warning "flask 验证失败，但可能已安装"
        fi
    else
        print_error "依赖安装失败"
        exit 1
    fi
fi

print_info "依赖安装完成！"
print_info "现在可以重启部署服务："
echo "  sudo systemctl restart ai-deploy-service-*.service"
echo "  或通过Web界面重新部署模型"

