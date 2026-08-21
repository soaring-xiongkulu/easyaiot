#!/bin/bash

# ============================================
# VIDEO服务 Docker Compose 管理脚本
# ============================================
# 使用方法：
#   ./install_all.sh [命令]
#
# 可用命令：
#   install    - 安装并启动服务（首次运行）
#   start      - 启动服务
#   stop       - 停止服务
#   restart    - 重启服务
#   status     - 查看服务状态
#   logs       - 查看服务日志
#   build      - 重新构建镜像
#   clean      - 清理容器和镜像
#   update     - 更新并重启服务
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
EASYAIOT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=../.scripts/docker/init-build-cache-dirs.sh
source "${EASYAIOT_ROOT}/.scripts/docker/init-build-cache-dirs.sh"
# shellcheck source=../.scripts/docker/gpu_compose_helpers.sh
source "${EASYAIOT_ROOT}/.scripts/docker/gpu_compose_helpers.sh"
# shellcheck source=../.scripts/docker/deploy_profile.sh
source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh"
# shellcheck source=../.scripts/docker/module_update_helpers.sh
source "${EASYAIOT_ROOT}/.scripts/docker/module_update_helpers.sh"

# 带 GPU/CPU / RUNTIME / source-free override 的 compose 调用
video_compose() {
    local -a files=(-f docker-compose.yaml)
    if [ -f .docker-compose.gpu.override.yaml ]; then
        files+=(-f .docker-compose.gpu.override.yaml)
    fi
    if [ -f .docker-compose.runtime.override.yaml ]; then
        files+=(-f .docker-compose.runtime.override.yaml)
    fi
    append_source_free_compose_file files
    $COMPOSE_CMD "${files[@]}" "$@"
}

# compose up；若媒体 bind 源 mkdir file exists 则修复后重试一次
video_compose_up_or_fail() {
    local compose_log _rc
    compose_log=$(mktemp)
    set +e
    video_compose up "$@" >"$compose_log" 2>&1
    _rc=$?
    set -e
    cat "$compose_log"
    if [ "$_rc" -ne 0 ] && repair_media_bind_after_compose_error "$(cat "$compose_log")"; then
        print_warning "媒体挂载源已修复（EASYAIOT_MEDIA_ROOT=${EASYAIOT_MEDIA_ROOT}），重试 VIDEO 启动..."
        : >"$compose_log"
        set +e
        video_compose up "$@" >"$compose_log" 2>&1
        _rc=$?
        set -e
        cat "$compose_log"
    fi
    rm -f "$compose_log"
    return "$_rc"
}

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

# 编译并挂载 RUNTIME（高性能算法任务默认依赖；实现见 scripts/ensure_runtime_cpp.sh）
ensure_cpp_runtime() {
    bash "${EASYAIOT_ROOT}/VIDEO/scripts/ensure_runtime_cpp.sh" install
}

wire_cpp_runtime_override() {
    bash "${EASYAIOT_ROOT}/VIDEO/scripts/ensure_runtime_cpp.sh" wire || true
}

# 清理 compose recreate 被中断后遗留的「改名孤儿容器」（形如 <12位hex>_video-service）。
# recreate 时 compose 先把旧容器改名让出 container_name，中途被打断旧容器就残留；
# 它若仍在运行会占住宿主机端口，新容器起不来。--remove-orphans 清不掉它
# （只清「服务已从 compose 文件移除」的孤儿），须在 up 前按名主动删除。
cleanup_renamed_containers() {
    local names
    names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_video-service$' || true)
    [ -z "$names" ] && return 0
    print_warning "清理上次中断遗留的改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

prepare_cached_resources() {
    init_easyaiot_build_cache_dirs "$EASYAIOT_ROOT"
    local wheels
    wheels="$(pip_wheels_build_context_dir_for "$EASYAIOT_ROOT" video)"
    local cache_script="${EASYAIOT_ROOT}/.scripts/docker/cache_python_resources.sh"

    if find "$wheels" -maxdepth 1 -type f \( -name "*.whl" -o -name "*.tar.gz" -o -name "*.zip" \) 2>/dev/null | grep -q .; then
        print_success "检测到 [video] pip-wheels: $wheels"
        return 0
    fi
    if [ "${AUTO_CACHE_PIP:-1}" != "1" ] || [ ! -f "$cache_script" ]; then
        print_info "构建时将使用 [video] pip-cache 在线安装（清华源）"
        return 0
    fi
    print_warning "[video] 首次需预下载 pip 离线包，可能需要 10–30 分钟..."
    "$cache_script" video || /bin/bash "$cache_script" video || print_warning "预下载失败，将在线安装"
}

build_with_cache() {
    local no_cache_flag="$1"
    local build_log="/tmp/docker_build_$$.log"
    local build_status=0
    local platform_opts=""

    init_easyaiot_build_cache_dirs "$EASYAIOT_ROOT"
    enable_docker_buildkit
    if [ -n "${DOCKER_PLATFORM:-}" ]; then
        platform_opts="--platform $DOCKER_PLATFORM"
        print_info "构建目标平台: ${DOCKER_PLATFORM}"
    fi

    # 与 AI 一致：build/install/build-runtime 均先准备 pip-wheels，避免空缓存走在线下载
    prepare_cached_resources
    print_info "docker build（.build-cache/video pip-cache/pip-wheels）..."
    set +e
    docker build \
        --build-context "pip-cache=$(pip_cache_build_context_dir_for "$EASYAIOT_ROOT" video)" \
        --build-context "pip-wheels=$(pip_wheels_build_context_dir_for "$EASYAIOT_ROOT" video)" \
        --target runtime \
        -t video-service:latest \
        $platform_opts \
        --pull=false \
        --build-arg OFFLINE_MODE=${OFFLINE_MODE:-0} \
        --build-arg APT_MIRROR_URL="${APT_MIRROR_URL:-https://mirrors.tuna.tsinghua.edu.cn}" \
        --build-arg PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}" \
        $no_cache_flag \
        . 2>&1 | tee "$build_log"
    build_status=${PIPESTATUS[0]}
    set -e

    if [ $build_status -ne 0 ]; then
        print_error "镜像构建失败"
        grep -iE "(error|warning|failed|失败|警告)" "$build_log" | tail -20 || true
        rm -f "$build_log"
        return 1
    fi
    rm -f "$build_log"
    return 0
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# 检查 Docker 是否安装
# 单次脚本运行内只实际检测一次（DOCKER_CHECKED 守卫），避免 update 等流程里
# check_status 末尾重复触发 docker --version，减少冗余进程与刷屏。
DOCKER_CHECKED=0
check_docker() {
    [ "$DOCKER_CHECKED" = "1" ] && return 0
    if ! check_command docker; then
        print_error "Docker 未安装，请先安装 Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker 已安装: $(docker --version)"
    DOCKER_CHECKED=1
}

# 检查 Docker Compose 是否安装
check_docker_compose() {
    # 已检测过（COMPOSE_CMD 已确定）则直接复用，避免重复执行 docker compose version
    if [ -n "$COMPOSE_CMD" ]; then
        return 0
    fi
    # 先检查 docker-compose 命令
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
        return 0
    fi
    
    # 再检查 docker compose 插件
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
        return 0
    fi
    
    # 如果都不存在，报错
    print_error "Docker Compose 未安装，请先安装 Docker Compose"
    echo "安装指南: https://docs.docker.com/compose/install/"
    exit 1
}

# 检查并创建 Docker 网络（注意：使用host网络模式后，此函数不再需要，但保留以兼容其他服务）
check_network() {
    print_info "检查 Docker 网络 easyaiot-network..."
    print_info "注意：VIDEO服务使用host网络模式，不需要加入easyaiot-network网络"
    print_info "但中间件服务仍需要此网络，检查网络是否存在..."
    
    # 检查网络是否已存在（使用网络名称）
    if docker network ls --format "{{.Name}}" 2>/dev/null | grep -q "^easyaiot-network$"; then
        print_info "网络 easyaiot-network 已存在"
        return 0
    fi
    
    # 网络不存在，尝试创建
    print_info "网络 easyaiot-network 不存在，正在创建..."
    local create_output=$(docker network create easyaiot-network 2>&1)
    local create_exit_code=$?
    
    if [ $create_exit_code -eq 0 ]; then
        print_success "网络 easyaiot-network 已创建"
        return 0
    else
        # 检查错误原因
        if echo "$create_output" | grep -qi "already exists"; then
            print_info "网络 easyaiot-network 已存在（可能在检查后创建）"
            return 0
        elif echo "$create_output" | grep -qi "permission denied"; then
            print_error "没有权限创建 Docker 网络"
            print_info "请确保当前用户在 docker 组中，或使用 sudo 运行脚本"
            print_info "解决方案："
            echo "  1. 将当前用户添加到 docker 组："
            echo "     sudo usermod -aG docker $USER"
            echo "     然后重新登录或运行: newgrp docker"
            echo ""
            echo "  2. 或者使用 sudo 运行此脚本："
            echo "     sudo ./install_linux.sh $*"
            exit 1
        elif echo "$create_output" | grep -qi "network with name.*already exists"; then
            print_warning "网络名称冲突，但网络已存在，继续使用现有网络"
            return 0
        else
            print_error "无法创建网络 easyaiot-network"
            print_error "错误信息: $create_output"
            print_info "诊断建议："
            print_info "  1. 检查 Docker 服务是否正常运行: sudo systemctl status docker"
            print_info "  2. 检查当前用户是否有权限: docker network ls"
            print_info "  3. 查看 Docker 日志: sudo journalctl -u docker.service"
            exit 1
        fi
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p data/uploads
    mkdir -p data/datasets
    mkdir -p data/models
    mkdir -p data/inference_results
    mkdir -p static/models
    mkdir -p temp_uploads
    mkdir -p model
    print_success "目录创建完成"
}

# 检查人脸特征提取模型（face_rec.onnx，约 167MB；安装时不自动下载，请登录 WEB 人脸库页下载）
download_face_rec_model() {
    local target="${SCRIPT_DIR}/face_rec.onnx"
    if [ -d "$target" ]; then
        print_warning "face_rec.onnx 误为目录（Docker 文件卷导致），正在清理..."
        rm -rf "$target"
    fi
    if [ -f "$target" ] && [ "$(stat -c%s "$target" 2>/dev/null || stat -f%z "$target" 2>/dev/null || echo 0)" -ge 10485760 ]; then
        print_success "人脸特征模型 face_rec.onnx 已存在"
        return 0
    fi
    print_warning "人脸特征模型 face_rec.onnx 未安装（约 167MB），安装过程不自动下载"
    print_info "请登录系统后进入「摄像头 → 人脸库」，按页面提示下载并安装模型"
}

# 清理 VIDEO 服务的 compose 容器网络缓存
clean_compose_cache() {
    print_info "清理 VIDEO 服务的 compose 容器网络缓存..."
    
    # 确保 COMPOSE_CMD 已设置
    if [ -z "$COMPOSE_CMD" ]; then
        if check_command docker-compose; then
            COMPOSE_CMD="docker-compose"
        elif docker compose version &> /dev/null; then
            COMPOSE_CMD="docker compose"
        else
            print_warning "无法确定 docker-compose 命令，跳过缓存清理"
            return 0
        fi
    fi
    
    local compose_file=""
    
    # 查找 compose 文件
    if [ -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
        compose_file="${SCRIPT_DIR}/docker-compose.yml"
    elif [ -f "${SCRIPT_DIR}/docker-compose.yaml" ]; then
        compose_file="${SCRIPT_DIR}/docker-compose.yaml"
    else
        print_info "未找到 docker-compose 文件，跳过缓存清理"
        return 0
    fi
    
    cd "$SCRIPT_DIR"
    
    # 1. 停止并清理容器和网络连接
    print_info "执行 docker-compose down 清理容器和网络连接..."
    # 使用 eval 来正确处理包含空格的 COMPOSE_CMD
    if eval "$COMPOSE_CMD down" 2>/dev/null; then
        print_success "容器和网络连接已清理"
    else
        print_info "docker-compose down 执行完成（可能没有运行的容器）"
    fi
    sleep 1
    
    # 2. 强制重新读取配置（这会清除 docker-compose 的配置缓存）
    print_info "强制重新读取配置以清除缓存..."
    if eval "$COMPOSE_CMD config" > /dev/null 2>&1; then
        print_success "配置已重新验证"
    else
        print_warning "配置验证失败，但继续执行"
    fi
    
    # 3. 清理可能的网络残留连接
    print_info "检查并清理网络残留连接..."
    local network_name="easyaiot-network"
    if docker network inspect "$network_name" &> /dev/null; then
        # 获取连接到该网络的所有容器
        local containers=$(docker network inspect "$network_name" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
        
        # 检查是否有VIDEO相关的容器残留
        if echo "$containers" | grep -q "video"; then
            print_info "发现残留的网络连接，正在清理..."
            echo "$containers" | tr ' ' '\n' | grep -v '^$' | grep -i "video" | while read -r container; do
                if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
                    print_info "断开容器网络连接: $container"
                    docker network disconnect -f "$network_name" "$container" 2>/dev/null || true
                fi
            done
        fi
    fi
    
    # 4. 清理 docker-compose 的临时文件（如果存在）
    print_info "清理 docker-compose 临时文件..."
    find . -maxdepth 1 -name ".docker-compose.*" -type f \
        ! -name ".docker-compose.gpu.override.yaml" \
        ! -name ".docker-compose.runtime.override.yaml" \
        -delete 2>/dev/null || true
    find . -maxdepth 1 -name "docker-compose.override.yml" -type f -delete 2>/dev/null || true
    find . -maxdepth 1 -name "docker-compose.override.yaml" -type f -delete 2>/dev/null || true
    
    print_success "VIDEO 服务的 compose 缓存已清理完成"
}

# 创建 .env.docker 文件（用于Docker部署）
create_env_file() {
    if [ ! -f .env.docker ]; then
        print_info ".env.docker 文件不存在，正在创建..."
        if [ -f env.example ]; then
            cp env.example .env.docker
            print_success ".env.docker 文件已从 env.example 创建"
            
            # 自动配置中间件连接信息（使用localhost，因为使用host网络模式）
            print_info "自动配置中间件连接信息（使用host网络模式，通过localhost访问中间件）..."
            
            # 临时文件写回，兼容 macOS BSD sed
            _set_env_docker_kv .env.docker DATABASE_URL "postgresql://postgres:iot45722414822@localhost:5432/iot-video20"
            _set_env_docker_kv .env.docker NACOS_SERVER "localhost:8848"
            _set_env_docker_kv .env.docker MINIO_ENDPOINT "localhost:9000"
            _set_env_docker_kv .env.docker MINIO_SECRET_KEY "basiclab@iot975248395"
            _set_env_docker_kv .env.docker REDIS_HOST "localhost"
            _set_env_docker_kv .env.docker KAFKA_BOOTSTRAP_SERVERS "localhost:9092"
            _set_env_docker_kv .env.docker TDENGINE_HOST "localhost"
            _set_env_docker_kv .env.docker NACOS_PASSWORD "basiclab@iot78475418754"
            
            print_success "中间件连接信息已自动配置（使用host网络模式）"
            print_info "注意：使用host网络模式后，容器可以直接访问宿主机局域网，支持ONVIF摄像头发现"
            print_info "如需修改其他配置，请编辑 .env.docker 文件"
        else
            print_error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        fi
    else
        print_info ".env.docker 文件已存在"
        # Docker Desktop 使用 bridge + 服务名，不能改回 localhost（host 网络在 Desktop 无效）
        if [ -n "${EASYAIOT_DESKTOP_OS:-}" ] || [ "${EASYAIOT_COMPOSE_DESKTOP:-0}" = "1" ]; then
            print_info "桌面端部署：保留/使用容器网络中间件地址（postgres-server 等）"
            _set_env_docker_kv .env.docker DATABASE_URL "postgresql://postgres:iot45722414822@postgres-server:5432/iot-video20"
            _set_env_docker_kv .env.docker REDIS_HOST "redis-server"
        else
            print_info "检查并更新中间件连接信息（使用host网络模式）..."
            
            # 检查并更新数据库连接（如果还是旧的服务名，改为localhost）
            if grep -q "DATABASE_URL=.*PostgresSQL" .env.docker || grep -q "DATABASE_URL=.*postgres-server" .env.docker; then
                _set_env_docker_kv .env.docker DATABASE_URL "postgresql://postgres:iot45722414822@localhost:5432/iot-video20"
                print_info "已更新数据库连接为 localhost:5432（host网络模式）"
            fi
            
            # 检查并更新Nacos配置（如果还是IP地址或旧的服务名，改为localhost）
            if grep -q "NACOS_SERVER=.*14\.18\.122\.2" .env.docker || grep -q "NACOS_SERVER=.*Nacos" .env.docker || grep -q "NACOS_SERVER=.*nacos-server" .env.docker; then
                _set_env_docker_kv .env.docker NACOS_SERVER "localhost:8848"
                print_info "已更新Nacos连接为 localhost:8848（host网络模式）"
            fi
            
            # 检查并更新MinIO配置（如果还是旧的服务名，改为localhost）
            if grep -q "MINIO_ENDPOINT=.*MinIO" .env.docker || grep -q "MINIO_ENDPOINT=.*minio-server" .env.docker; then
                _set_env_docker_kv .env.docker MINIO_ENDPOINT "localhost:9000"
                print_info "已更新MinIO连接为 localhost:9000（host网络模式）"
            fi
            
            # 检查并更新Redis配置（如果还是旧的服务名，改为localhost）
            if grep -q "REDIS_HOST=.*Redis" .env.docker || grep -q "REDIS_HOST=.*redis-server" .env.docker; then
                _set_env_docker_kv .env.docker REDIS_HOST "localhost"
                print_info "已更新Redis连接为 localhost（host网络模式）"
            fi
            
            # 检查并更新Kafka配置（如果还是旧的服务名，改为localhost）
            if grep -q "KAFKA_BOOTSTRAP_SERVERS=.*Kafka" .env.docker || grep -q "KAFKA_BOOTSTRAP_SERVERS=.*kafka-server" .env.docker; then
                _set_env_docker_kv .env.docker KAFKA_BOOTSTRAP_SERVERS "localhost:9092"
                print_info "已更新Kafka连接为 localhost:9092（host网络模式）"
            fi
            
            # 检查并更新TDengine配置（如果还是旧的服务名，改为localhost）
            if grep -q "TDENGINE_HOST=.*TDengine" .env.docker || grep -q "TDENGINE_HOST=.*tdengine-server" .env.docker; then
                _set_env_docker_kv .env.docker TDENGINE_HOST "localhost"
                print_info "已更新TDengine连接为 localhost（host网络模式）"
            fi
        fi
    fi

    ensure_deploy_profile
    apply_python_service_deploy_env "${EASYAIOT_ROOT}"
    if is_edge_deploy_profile; then
        print_info "edge 形态：零 DEVICE + 本地存储；告警/DVR 由 VIDEO 本地消化"
    elif is_mini_deploy_profile; then
        print_info "mini 形态：已配置 Gateway 部署（48080）+ MQTT→iot-sink 统一事件面"
    else
        print_info "${EASYAIOT_DEPLOY_PROFILE:-full} 形态：已配置网关部署（JAVA_BACKEND_URL=48080, MinIO 启用）"
    fi

    # RTC / go2rtc（存量 .env.docker 可能缺项）
    _set_env_docker_kv .env.docker RTC_SERVICE_URL "http://127.0.0.1:6100"
    _set_env_docker_kv .env.docker RTC_GO2RTC_WEB_URL "/dev-api/go2rtc/"
    _set_env_docker_kv .env.docker RTC_RTSP_HOST "127.0.0.1"
    _set_env_docker_kv .env.docker RTC_RTSP_PORT "8554"

}

# 安装服务
install_service() {
    print_info "开始安装 VIDEO 服务..."

    # 镜像获取方式（install_business_linux.sh 已统一询问时跳过）
    if [ "${EASYAIOT_SKIP_IMAGE_PROMPT:-0}" != "1" ]; then
        local _do_local_build=0
        if [ -t 0 ]; then
            print_info "========================================"
            print_info "  镜像获取方式"
            print_info "========================================"
            print_info "  1) 拉取预构建镜像：从远程仓库下载（快速，默认）"
            print_info "  2) 本地构建：编译并制作 Docker 镜像（耗时较长）"
            echo ""
            read -r -p "是否从远程仓库下载预构建的镜像？(Y/n) " _pull_response
            case "${_pull_response:-Y}" in
                n|N|no|NO) _do_local_build=1 ;;
                *) _do_local_build=0 ;;
            esac
        else
            print_info "非交互模式，默认拉取预构建镜像"
        fi

        if [ "$_do_local_build" -eq 0 ]; then
            print_info "正在拉取预构建镜像..."
            if bash "${EASYAIOT_ROOT}/.scripts/docker/runtime_image.sh" pull; then
                print_success "预构建镜像拉取成功"
                export EASYAIOT_SKIP_BUILD=1
            else
                print_warning "预构建镜像拉取失败，将尝试本地构建"
                _do_local_build=1
            fi
        fi
    fi

    check_docker
    check_docker_compose
    clean_compose_cache
    check_network
    create_directories
    download_face_rec_model
    create_env_file
    ensure_cpp_runtime || true
    check_gpu
    configure_compose_gpu "docker-compose.yaml" ".env.docker"

    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && docker image inspect video-service:latest >/dev/null 2>&1; then
        print_success "镜像已从远程拉取 (video-service:latest)，跳过 pip 离线包下载与 Docker 构建"
    else
        print_info "构建 Docker 镜像（优先复用离线 pip 缓存）..."
        if ! build_with_cache ""; then
            exit 1
        fi
    fi
    
    print_info "启动服务..."
    cleanup_renamed_containers
    if ! video_compose_up_or_fail -d --remove-orphans; then
        print_error "VIDEO 服务启动失败"
        exit 1
    fi

    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 5
    
    # 检查服务状态
    check_status
    
    print_info "服务访问地址: http://localhost:6000"
    print_info "健康检查地址: http://localhost:6000/actuator/health"
    print_info "查看日志: ./install_linux.sh logs"
}

# 启动服务
start_service() {
    print_info "启动服务..."
    check_docker
    check_docker_compose
    clean_compose_cache
    check_network
    
    if [ ! -f .env.docker ]; then
        print_warning ".env.docker 文件不存在，正在创建..."
        create_env_file
    else
        ensure_deploy_profile
    fi

    check_gpu
    configure_compose_gpu "docker-compose.yaml" ".env.docker"
    wire_cpp_runtime_override

    cleanup_renamed_containers
    video_compose_up_or_fail -d --force-recreate --remove-orphans
    print_success "服务已启动"
    check_status
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    check_docker
    check_docker_compose
    
    video_compose down
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose

    if [ ! -f .env.docker ]; then
        print_warning ".env.docker 文件不存在，正在创建..."
        create_env_file
    else
        ensure_deploy_profile
    fi
    check_gpu
    configure_compose_gpu "docker-compose.yaml" ".env.docker"
    wire_cpp_runtime_override

    cleanup_renamed_containers
    video_compose_up_or_fail -d --force-recreate --remove-orphans
    print_success "服务已重启"
    check_status
}

# 查看服务状态
check_status() {
    print_info "服务状态:"
    check_docker
    check_docker_compose
    
    video_compose ps
    
    echo ""
    print_info "容器健康状态:"
    if docker ps --filter "name=video-service" --format "table {{.Names}}\t{{.Status}}" | grep -q video-service; then
        docker ps --filter "name=video-service" --format "table {{.Names}}\t{{.Status}}"
        
        # 检查健康检查
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' video-service 2>/dev/null || echo "N/A")
        if [ "$HEALTH" != "N/A" ]; then
            echo "健康状态: $HEALTH"
        fi
    else
        print_warning "服务未运行"
    fi
}

# 查看日志
view_logs() {
    check_docker
    check_docker_compose
    
    if [ "$1" == "-f" ] || [ "$1" == "--follow" ]; then
        print_info "实时查看日志（按 Ctrl+C 退出）..."
        video_compose logs -f --tail=50
    else
        print_info "查看最近日志（最近50行）..."
        video_compose logs --tail=50
    fi
}

# 构建镜像
build_image() {
    check_docker
    check_docker_compose

    if [ "${FORCE_REBUILD:-0}" != "1" ] && docker image inspect video-service:latest >/dev/null 2>&1; then
        print_success "video-service:latest 已存在，跳过 Docker 构建（强制重建请设置 FORCE_REBUILD=1）"
        return 0
    fi

    print_info "重新构建 Docker 镜像..."
    local cache_flag=""
    [ "${FORCE_REBUILD:-0}" = "1" ] && cache_flag="--no-cache"
    if ! build_with_cache "$cache_flag"; then
        exit 1
    fi
    print_success "镜像构建完成"
}

# 清理服务
clean_service() {
    if [ "${EASYAIOT_AUTO_YES:-}" != "1" ]; then
        print_warning "这将删除容器、镜像和数据卷，确定要继续吗？"
        local response
        while true; do
            read -r -p "确认继续? [y/n] " response
            case "$(echo "$response" | tr '[:upper:]' '[:lower:]')" in
                y|yes) break ;;
                n|no|'')
                    print_info "已取消清理操作"
                    return
                    ;;
                *) echo "请输入 y/yes 或 n/no" ;;
            esac
        done
    fi

    check_docker
    check_docker_compose
    print_info "停止并删除容器..."
        video_compose down -v
        
        print_info "删除镜像..."
        docker rmi video-service:latest 2>/dev/null || true
        
    print_success "清理完成"
}

# 更新服务
# 性能优化要点（命令接口/功能保持不变）：
#   1. 业务源码经 docker-compose 卷挂载（./:/app）进容器。因此「仅改业务代码、依赖不变」时，
#      update 完全跳过 docker build：git pull 后只重启容器进程即可加载新代码（秒级），
#      把原先几十分钟的镜像重建从代码更新路径上彻底摘除。
#   2. 仅当以下任一成立时才重建镜像：镜像不存在 / FORCE_REBUILD=1 /
#      本次 git pull 改动了依赖或构建输入（requirements*.txt、Dockerfile、docker-entrypoint.sh）。
#   3. 需要构建时：旧容器在 git pull + build 全程持续运行，构建完成后才 up -d 触发重建，
#      并复用 BuildKit 层缓存 + 离线 pip 缓存，停机最小化。
#   注：VIDEO 用 host 网络模式，从不加入 easyaiot-network，更新流程无需 clean_compose_cache。
update_service() {
    print_info "更新服务..."
    check_docker
    check_docker_compose
    check_network
    ensure_cpp_runtime || true

    # 拉取预构建 / 无 git：禁止 git pull，仅 recreate
    if easyaiot_update_should_recreate_only video-service:latest; then
        check_gpu
        configure_compose_gpu "docker-compose.yaml" ".env.docker"
        cleanup_renamed_containers
        if ! video_compose_up_or_fail -d --force-recreate --remove-orphans --no-deps video-service; then
            print_error "VIDEO 服务更新失败"
            return 1
        fi
        print_success "服务更新完成"
        return 0
    fi

    if ! easyaiot_have_git; then
        print_warning "未安装 git 且本地无 video-service 镜像，将基于当前目录源码构建"
        check_gpu
        configure_compose_gpu "docker-compose.yaml" ".env.docker"
        if ! build_with_cache ""; then
            exit 1
        fi
        cleanup_renamed_containers
        video_compose_up_or_fail -d --force-recreate --remove-orphans --no-deps video-service || return 1
        print_success "服务更新完成"
        return 0
    fi

    # 记录更新前代码版本，用于判断依赖/构建文件是否变化
    local rev_before=""
    rev_before="$(easyaiot_git_rev_parse_head)"

    print_info "拉取最新代码..."
    # --ff-only：快进失败立即返回，不产生意外合并提交，比默认 pull 更快更安全
    easyaiot_git_pull_ff_only

    local rev_after=""
    rev_after="$(easyaiot_git_rev_parse_head)"

    # ---- 判断是否需要重建镜像 ----
    local needs_build=0
    if ! docker image inspect video-service:latest >/dev/null 2>&1; then
        needs_build=1
        print_info "镜像不存在，需要构建"
    elif [ "${FORCE_REBUILD:-0}" = "1" ]; then
        needs_build=1
        print_info "FORCE_REBUILD=1，强制重建镜像"
    elif [ -z "$rev_before" ]; then
        # 无法获取 git 版本（无法判断变化），保守重建
        needs_build=1
        print_warning "无法获取 git 版本信息，保守起见重建镜像"
    elif [ "$rev_before" != "$rev_after" ]; then
        # 比较本次更新是否改动依赖/构建输入文件。
        # 注意：git diff --name-only 仅在「出错」时返回非 0（有无差异都返回 0），
        # 故可据返回码区分「确无变化」与「无法判断」；用 || 捕获以避开 set -e。
        local dep_changes dep_diff_rc=0
        dep_changes="$(git diff --name-only "$rev_before" "$rev_after" -- \
            requirements.txt requirements-base.txt requirements-docker.txt \
            Dockerfile docker-entrypoint.sh 2>/dev/null)" || dep_diff_rc=$?
        if [ "$dep_diff_rc" -ne 0 ]; then
            needs_build=1
            print_warning "无法比较依赖变化（git diff 失败），保守起见重建镜像"
        elif [ -n "$dep_changes" ]; then
            needs_build=1
            print_info "检测到依赖/构建文件变化，需要重建镜像："
            echo "$dep_changes" | sed 's/^/    /'
        fi
    fi

    if [ "$needs_build" = "1" ]; then
        print_info "重新构建镜像（复用 BuildKit 层缓存 + 离线 pip 缓存）..."
        if ! build_with_cache ""; then
            exit 1
        fi
        # 构建完成后才重建容器：compose 检测到镜像变化「先停旧、再起新」，停机仅数秒
        print_info "应用新镜像（仅重建变更服务，最小化停机）..."
        cleanup_renamed_containers
        video_compose_up_or_fail -d --remove-orphans --no-deps video-service
    else
        print_success "依赖未变，跳过镜像构建（业务代码经卷挂载，重启进程即可生效）"
        # 确保容器存在并应用任何 compose 配置变更（首次启用源码挂载时会在此处重建一次）
        cleanup_renamed_containers
        video_compose_up_or_fail -d --remove-orphans --no-deps video-service

        # 是否需要重启进程以加载新源码：有新提交，或本地有未提交改动（git diff 脏）。
        # git diff --quiet HEAD 仅在出错或有已跟踪改动时返回非 0，用于捕获“改了代码没 commit”的场景；
        # 不受未跟踪文件干扰。出错时按“脏”处理（重启代价仅数秒，宁可多重启）。
        local code_changed=0
        if [ -n "$rev_before" ] && [ "$rev_before" != "$rev_after" ]; then
            code_changed=1
        elif ! easyaiot_git_worktree_clean; then
            code_changed=1
        fi

        if [ "$code_changed" = "1" ]; then
            print_info "重启容器进程以加载最新源码（秒级）..."
            video_compose restart video-service
        else
            print_info "代码无变更，无需重启"
        fi
    fi

    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "VIDEO服务 Docker Compose 管理脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install_linux.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  install    - 安装并启动服务（首次运行；含 RUNTIME 高性能执行器编译）"
    echo "  start      - 启动服务"
    echo "  stop       - 停止服务"
    echo "  restart    - 重启服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看服务日志（最近50行）"
    echo "  logs -f    - 实时查看服务日志（最近50行）"
    echo "  build      - 重新构建镜像"
    echo "  clean      - 清理容器和镜像"
    echo "  update     - 更新并重启服务（含 RUNTIME 重编译）"
    echo "  help       - 显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  EASYAIOT_RUNTIME_SKIP=1      跳过 RUNTIME 编译"
    echo "  EASYAIOT_RUNTIME_REQUIRED=1  RUNTIME 失败则中止 VIDEO 安装"
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            install_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            check_status
            ;;
        logs)
            view_logs "$2"
            ;;
        build)
            build_image
            ;;
        clean)
            clean_service
            ;;
        update)
            update_service
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

