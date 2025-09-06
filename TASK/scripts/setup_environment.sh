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
            apt install -y -qq "$pkg" >> "$LOG_FILE" 2>&1
            success_log "已安装 $pkg"
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "基础编译工具安装完成"
}

# 安装OpenCV依赖
install_opencv_deps() {
    log "安装OpenCV依赖..."
    local packages=(
        "libopencv-core-dev"
        "libopencv-videoio-dev"
        "libopencv-highgui-dev"
        "libopencv-imgproc-dev"
        "libopencv-dnn-dev"
        "libopencv-tracking-dev"
        "libopencv-calib3d-dev"
        "libopencv-features2d-dev"
    )

    for pkg in "${packages[@]}"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            apt install -y -qq "$pkg" >> "$LOG_FILE" 2>&1
            success_log "已安装 $pkg"
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
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
            apt install -y -qq "$pkg" >> "$LOG_FILE" 2>&1
            success_log "已安装 $pkg"
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
            apt install -y -qq "$pkg" >> "$LOG_FILE" 2>&1
            success_log "已安装 $pkg"
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "JSON和其他工具库安装完成"
}

# 安装MinIO客户端依赖
install_minio_deps() {
    log "安装MinIO客户端依赖..."
    # 检查minio库是否可用
    if ! dpkg -s "libminio-dev" >/dev/null 2>&1; then
        # 尝试从源码编译安装minio-cpp
        log "尝试安装MinIO C++ SDK..."
        apt install -y -qq \
            libcurl4-openssl-dev \
            libssl-dev \
            libxml2-dev >> "$LOG_FILE" 2>&1

        # 从GitHub克隆和编译minio-cpp
        local temp_dir=$(mktemp -d)
        cd "$temp_dir"
        git clone https://github.com/minio/minio-cpp.git >> "$LOG_FILE" 2>&1
        cd minio-cpp
        mkdir build
        cd build
        cmake .. >> "$LOG_FILE" 2>&1
        make -j$(nproc) >> "$LOG_FILE" 2>&1
        make install >> "$LOG_FILE" 2>&1
        cd /
        rm -rf "$temp_dir"
        success_log "MinIO C++ SDK 安装完成"
    else
        apt install -y -qq libminio-dev >> "$LOG_FILE" 2>&1
        success_log "MinIO依赖安装完成"
    fi
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
            apt install -y -qq "$pkg" >> "$LOG_FILE" 2>&1
            success_log "已安装 $pkg"
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
            apt install -y -qq "$pkg" >> "$LOG_FILE" 2>&1
            success_log "已安装 $pkg"
        else
            log "$pkg 已存在，跳过安装"
        fi
    done
    success_log "调试和测试工具安装完成"
}

# 验证安装
verify_installation() {
    log "验证安装..."

    # 检查CMake
    if command -v cmake >/dev/null 2>&1; then
        success_log "CMake 已安装: $(cmake --version | head -n 1)"
    else
        error_log "CMake 未安装"
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
    echo "5. 运行程序: ./bin/smart_surveillance_system"
    echo ""
    echo "安装日志保存在: $LOG_FILE"
    echo -e "${GREEN}祝你开发顺利!${NC}"
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

    # 创建日志目录和文件[7](@ref)
    LOG_DIR=$(dirname "$LOG_FILE")
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
    fi
    touch "$LOG_FILE"
    echo "安装开始时间: $TIMESTAMP" >> "$LOG_FILE"

    # 执行安装步骤
    check_system
    install_build_tools
    install_opencv_deps
    install_mqtt_deps
    install_utils_deps
    install_minio_deps
    install_video_deps
    install_debug_tools
    verify_installation

    # 显示摘要
    show_summary
}

# 执行主函数
main "$@"