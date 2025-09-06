#!/bin/bash

set -e  # 遇到错误立即退出

# 颜色定义用于输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 恢复默认颜色

# 日志文件
LOG_FILE="/var/log/TASK.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# 输出日志函数
log() {
    echo -e "${BLUE}[$TIMESTAMP]${NC} $1" | tee -a "$LOG_FILE"
}

success_log() {
    echo -e "${GREEN}[$TIMESTAMP] ✓${NC} $1" | tee -a "$LOG_FILE"
}

warning_log() {
    echo -e "${YELLOW}[$TIMESTAMP] ⚠${NC} $1" | tee -a "$LOG_FILE"
}

error_log() {
    echo -e "${RED}[$TIMESTAMP] ✗${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

# 检查系统是否为Ubuntu
check_system() {
    log "检查系统环境..."
    if ! grep -q "Ubuntu" /etc/os-release; then
        error_log "此脚本仅适用于 Ubuntu 系统"
    fi

    if ! grep -q "24.04" /etc/os-release; then
        warning_log "此脚本针对 Ubuntu 24.04 优化，当前系统版本可能不同"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    success_log "系统环境检查完成"
}

# 更新系统包列表
update_system() {
    log "更新系统包列表..."
    if ! apt update -y >> "$LOG_FILE" 2>&1; then
        error_log "系统包列表更新失败，命令: apt update -y"
    fi
    success_log "系统包列表更新完成"
}

# 安装基础编译工具
install_build_tools() {
    log "安装基础编译工具..."
    local packages=(
        "build-essential"
        "cmake"
        "pkg-config"
        "curl"
        "wget"
        "git"
        "unzip"
        "tar"
        "libssl-dev"
        "ninja-build"
    )

    for pkg in "${packages[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            if ! apt install -y "$pkg" >> "$LOG_FILE" 2>&1; then
                warning_log "安装 $pkg 失败，命令: apt install -y $pkg"
            else
                success_log "已安装 $pkg"
            fi
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "基础编译工具安装完成"
}

# 安装OpenCV依赖
install_opencv_deps() {
    log "安装OpenCV依赖 (仅安装 libopencv-dev)..."
    local package="libopencv-dev"

    if ! dpkg -s "$package" >/dev/null 2>&1; then
        if ! apt install -y "$package" >> "$LOG_FILE" 2>&1; then
            warning_log "安装 $package 失败，命令: apt install -y $package"
        else
            success_log "已安装 $package"
        fi
    else
        log "$package 已存在，跳过安装"
    fi

    success_log "OpenCV依赖安装完成"
}

# 安装Paho MQTT和网络库
install_mqtt_deps() {
    log "安装MQTT和网络库..."
    local packages=(
        "libpaho-mqttpp-dev"
        "libssl-dev"
        "libcurl4-openssl-dev"
    )

    for pkg in "${packages[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            if ! apt install -y "$pkg" >> "$LOG_FILE" 2>&1; then
                warning_log "安装 $pkg 失败，命令: apt install -y $pkg"
            else
                success_log "已安装 $pkg"
            fi
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "MQTT和网络库安装完成"
}

# 安装JSON和其他工具库
install_utils_deps() {
    log "安装JSON和其他工具库..."
    local packages=(
        "nlohmann-json3-dev"
        "libboost-system-dev"
        "libboost-filesystem-dev"
        "libboost-program-options-dev"
        "libxml2-dev"
        "zlib1g-dev"
    )

    for pkg in "${packages[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            if ! apt install -y "$pkg" >> "$LOG_FILE" 2>&1; then
                warning_log "安装 $pkg 失败，命令: apt install -y $pkg"
            else
                success_log "已安装 $pkg"
            fi
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "JSON和其他工具库安装完成"
}

# 检查端口占用
check_port_conflict() {
    local port=$1
    log "检查端口 $port 是否被占用..."
    if lsof -i :$port >/dev/null 2>&1; then
        warning_log "端口 $port 已被占用，可能导致MinIO启动失败"
        lsof -i :$port | head -n 5 >> "$LOG_FILE" 2>&1
    else
        success_log "端口 $port 未被占用"
    fi
}

# 检查目录权限
check_directory_permissions() {
    local dir=$1
    log "检查目录 $dir 的权限..."
    if [ ! -d "$dir" ]; then
        log "目录 $dir 不存在，将尝试创建"
        if ! mkdir -p "$dir" >> "$LOG_FILE" 2>&1; then
            warning_log "创建目录 $dir 失败，命令: mkdir -p $dir"
            return 1
        fi
    fi

    if [ ! -w "$dir" ]; then
        warning_log "当前用户对目录 $dir 没有写权限"
        return 1
    fi
    success_log "目录 $dir 权限检查通过"
    return 0
}

# 安装MinIO客户端依赖
install_minio_deps() {
    log "安装MinIO客户端依赖..."

    # 检查端口占用[2,7](@ref)
    check_port_conflict 9000
    check_port_conflict 9001

    # 首先安装 libcurlpp-dev
    log "安装 libcurlpp-dev (解决 unofficial-curlpp 依赖问题)..."
    if ! dpkg -s "libcurlpp-dev" >/dev/null 2>&1; then
        if ! apt install -y libcurlpp-dev >> "$LOG_FILE" 2>&1; then
            warning_log "安装 libcurlpp-dev 失败，命令: apt install -y libcurlpp-dev"
        else
            success_log "已安装 libcurlpp-dev"
        fi
    else
        log "libcurlpp-dev 已存在，跳过安装"
    fi

    # 检查minio库是否可用
    if ! dpkg -s "libminio-dev" >/dev/null 2>&1; then
        # 安装其他必要依赖
        log "安装MinIO C++ SDK的编译依赖..."
        local minio_deps=(
            "libcurl4-openssl-dev"
            "libssl-dev"
            "libxml2-dev"
        )

        for dep in "${minio_deps[@]}"; do
            if ! dpkg -s "$dep" >/dev/null 2>&1; then
                if ! apt install -y "$dep" >> "$LOG_FILE" 2>&1; then
                    warning_log "安装依赖 $dep 失败，命令: apt install -y $dep"
                else
                    success_log "已安装 $dep"
                fi
            fi
        done

        # 从GitHub克隆和编译minio-cpp
        log "尝试从源码编译安装MinIO C++ SDK..."
        local temp_dir=$(mktemp -d)
        cd "$temp_dir"

        # 克隆仓库
        log "克隆 minio-cpp 仓库..."
        if ! git clone https://github.com/minio/minio-cpp.git >> "$LOG_FILE" 2>&1; then
            warning_log "克隆 minio-cpp 仓库失败，命令: git clone https://github.com/minio/minio-cpp.git"
            cd /
            rm -rf "$temp_dir"
            return 1
        fi

        cd minio-cpp

        # 创建构建目录并编译
        mkdir build
        cd build

        # 尝试配置
        log "运行 CMake 配置..."
        if ! cmake .. >> "$LOG_FILE" 2>&1; then
            warning_log "MinIO C++ SDK CMake配置失败，命令: cmake .."
            warning_log "这可能表示仍有依赖缺失，请检查 $LOG_FILE 获取详细信息"
            cd /
            rm -rf "$temp_dir"
            return 1
        fi

        # 如果cmake成功，继续编译和安装
        log "编译 MinIO C++ SDK..."
        if ! make -j$(nproc) >> "$LOG_FILE" 2>&1; then
            warning_log "MinIO C++ SDK 编译失败，命令: make -j$(nproc)"
            cd /
            rm -rf "$temp_dir"
            return 1
        fi

        log "安装 MinIO C++ SDK..."
        if ! make install >> "$LOG_FILE" 2>&1; then
            warning_log "MinIO C++ SDK 安装失败，命令: make install"
            cd /
            rm -rf "$temp_dir"
            return 1
        fi

        success_log "MinIO C++ SDK 安装完成"

        # 清理临时目录
        cd /
        rm -rf "$temp_dir"
    else
        if ! apt install -y libminio-dev >> "$LOG_FILE" 2>&1; then
            warning_log "安装 libminio-dev 失败，命令: apt install -y libminio-dev"
            return 1
        else
            success_log "MinIO依赖安装完成"
        fi
    fi

    return 0
}

# 安装视频和摄像头支持
install_video_deps() {
    log "安装视频和摄像头支持..."
    local packages=(
        "v4l-utils"
        "libavcodec-dev"
        "libavformat-dev"
        "libavutil-dev"
        "libswscale-dev"
        "libgstreamer1.0-dev"
        "libgstreamer-plugins-base1.0-dev"
    )

    for pkg in "${packages[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            if ! apt install -y "$pkg" >> "$LOG_FILE" 2>&1; then
                warning_log "安装 $pkg 失败，命令: apt install -y $pkg"
            else
                success_log "已安装 $pkg"
            fi
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "视频和摄像头支持安装完成"
}

# 安装调试和测试工具
install_debug_tools() {
    log "安装调试和测试工具..."
    local packages=(
        "gdb"
        "valgrind"
        "lcov"
        "gcovr"
        "cppcheck"
        "clang-tidy"
    )

    for pkg in "${packages[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            if ! apt install -y "$pkg" >> "$LOG_FILE" 2>&1; then
                warning_log "安装 $pkg 失败，命令: apt install -y $pkg"
            else
                success_log "已安装 $pkg"
            fi
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "调试和测试工具安装完成"
}

# 检查SELinux设置
check_selinux() {
    log "检查SELinux设置..."
    if command -v sestatus >/dev/null 2>&1; then
        local selinux_status=$(sestatus | grep "SELinux status" | awk '{print $3}')
        if [ "$selinux_status" = "enabled" ]; then
            warning_log "SELinux 已启用，可能会影响MinIO运行"
            warning_log "可以考虑临时禁用: sudo setenforce 0 或调整SELinux策略"
        fi
    else
        success_log "SELinux 未安装（正常情况）"
    fi
}

# 验证安装
verify_installation() {
    log "验证安装..."

    # 检查CMake
    if command -v cmake >/dev/null 2>&1; then
        success_log "CMake 已安装: $(cmake --version | head -n 1)"
    else
        warning_log "CMake 未安装"
    fi

    # 检查OpenCV
    if pkg-config --exists opencv4; then
        success_log "OpenCV 已安装: $(pkg-config --modversion opencv4)"
    else
        warning_log "OpenCV 未安装或版本不匹配"
    fi

    # 检查基础开发工具
    local tools=("gcc" "g++" "make" "git")
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            success_log "$tool 已安装: $($tool --version | head -n 1)"
        else
            warning_log "$tool 未安装"
        fi
    done

    # 检查MinIO相关依赖
    if pkg-config --exists libcurl; then
        success_log "libcurl 已安装: $(pkg-config --modversion libcurl)"
    else
        warning_log "libcurl 未安装或版本不匹配"
    fi

    if pkg-config --exists openssl; then
        success_log "OpenSSL 已安装: $(pkg-config --modversion openssl)"
    else
        warning_log "OpenSSL 未安装或版本不匹配"
    fi

    success_log "安装验证完成"
}

# 显示安装摘要
show_summary() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "EasyAIoT TASK模块依赖安装完成!"
    echo "=========================================="
    echo -e "${NC}"
    echo "下一步操作:"
    echo "1. 进入项目目录: cd your-project-directory"
    echo "2. 创建构建目录: mkdir -p build && cd build"
    echo "3. 配置项目: cmake .."
    echo "4. 编译项目: make -j$(nproc)"
    echo "5. 运行程序: ./bin/TASK"
    echo ""
    echo "安装日志保存在: $LOG_FILE"
    echo -e "${GREEN}祝你开发顺利!${NC}"
}

# 显示MinIO故障排除提示
show_minio_troubleshooting() {
    echo -e "${YELLOW}"
    echo "=========================================="
    echo "MinIO 安装故障排除提示"
    echo "=========================================="
    echo -e "${NC}"
    echo "如果MinIO相关功能仍然有问题，请检查:"
    echo "1. 端口占用: 确保端口9000和9001未被其他程序占用"
    echo "2. 权限问题: 确保MinIO有足够的目录访问权限"
    echo "3. 依赖完整性: 运行 'ldd /usr/local/lib/libminio.so' 检查依赖"
    echo "4. 防火墙设置: 确保防火墙允许MinIO端口"
    echo "5. 查看详细日志: cat $LOG_FILE | grep -i minio"
    echo "6. 手动安装: 可尝试从 https://min.io/download 手动下载安装"
    echo -e "${YELLOW}更多帮助参考MinIO官方文档: https://docs.min.io${NC}"
}

# 主执行函数
main() {
    echo -e "${GREEN}"
    echo "=========================================="
    echo "EasyAIoT TASK模块依赖安装脚本"
    echo "适用于 Ubuntu 24.04"
    echo "=========================================="
    echo -e "${NC}"

    if [ "$EUID" -ne 0 ]; then
        error_log "此脚本必须使用 root 权限运行，请使用 sudo 或切换到 root 用户"
    fi

    # 创建日志目录和文件
    LOG_DIR=$(dirname "$LOG_FILE")
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
    fi
    touch "$LOG_FILE"
    echo "安装开始时间: $TIMESTAMP" >> "$LOG_FILE"

    # 执行安装步骤
    check_system
    update_system
    install_build_tools
    install_opencv_deps
    install_mqtt_deps
    install_utils_deps

    # 安装MinIO依赖并检查结果
    if ! install_minio_deps; then
        warning_log "MinIO 依赖安装过程中遇到问题，可能会影响功能"
        warning_log "请查看 $LOG_FILE 获取详细错误信息"
    fi

    install_video_deps
    install_debug_tools
    check_selinux
    verify_installation

    # 显示摘要
    show_summary
    show_minio_troubleshooting
}

# 执行主函数
main "$@"