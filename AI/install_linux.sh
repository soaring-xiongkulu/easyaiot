#!/bin/bash

# ============================================
# AI 服务 Docker Compose 管理脚本
# ============================================
# 管理服务：ai-service (5000)，数据集标注已合并至 WEB + /model/dataset API
# 使用方法：
#   ./install_linux.sh [命令]
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
# shellcheck source=../.scripts/docker/deploy_profile.sh
source "${EASYAIOT_ROOT}/.scripts/docker/deploy_profile.sh"

GPU_COMPOSE_OVERRIDE=".docker-compose.gpu.override.yaml"
GPU_LOCAL_ENV=".env.local"

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

# 清理 compose recreate 被中断后遗留的「改名孤儿容器」（形如 <12位hex>_ai-service）。
# recreate 时 compose 先把旧容器改名让出 container_name，中途被打断旧容器就残留；
# 它若仍在运行会占住宿主机端口，新容器起不来。--remove-orphans 清不掉它
# （只清「服务已从 compose 文件移除」的孤儿），须在 up 前按名主动删除。
cleanup_renamed_containers() {
    local names
    names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_ai-service$' || true)
    [ -z "$names" ] && return 0
    print_warning "清理上次中断遗留的改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
}

prepare_cached_resources_for_module() {
    local module="$1"
    init_easyaiot_build_cache_dirs "$EASYAIOT_ROOT"
    local wheels
    wheels="$(pip_wheels_build_context_dir_for "$EASYAIOT_ROOT" "$module")"
    local cache_script="${EASYAIOT_ROOT}/.scripts/docker/cache_python_resources.sh"
    if find "$wheels" -maxdepth 1 -type f 2>/dev/null | grep -q .; then
        print_success "检测到 [${module}] pip-wheels: $wheels"
        return 0
    fi
    if [ "${AUTO_CACHE_PIP:-1}" = "1" ] && [ -f "$cache_script" ]; then
        print_warning "[${module}] 首次需预下载 pip 离线包，可能需要 10–30 分钟..."
        # BASE_IMAGE 可能已是 runtime（供 docker build）；cache 脚本会自行选用 devel 编译 sdist
        "$cache_script" "$module" || /bin/bash "$cache_script" "$module" || true
    fi
}

prepare_cached_resources() {
    prepare_cached_resources_for_module "ai"
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
    fi

    prepare_cached_resources
    print_info "docker build（.build-cache/ai pip-cache/pip-wheels）..."
    set +e
    docker build \
        --build-arg BASE_IMAGE="${BASE_IMAGE:-pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime}" \
        --build-context "pip-cache=$(pip_cache_build_context_dir_for "$EASYAIOT_ROOT" ai)" \
        --build-context "pip-wheels=$(pip_wheels_build_context_dir_for "$EASYAIOT_ROOT" ai)" \
        --target runtime \
        $platform_opts \
        -t ai-service:latest \
        --pull=false \
        --build-arg OFFLINE_MODE=${OFFLINE_MODE:-0} \
        --build-arg APT_MIRROR_URL="${APT_MIRROR_URL:-https://mirrors.tuna.tsinghua.edu.cn}" \
        --build-arg PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}" \
        $no_cache_flag \
        . 2>&1 | tee "$build_log"
    build_status=${PIPESTATUS[0]}
    set -e

    if [ $build_status -ne 0 ]; then
        print_error "AI 服务镜像构建失败"
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

compose_up_or_fail() {
    local compose_log
    local -a compose_args=()
    # 显式 -f 时会忽略 COMPOSE_FILE，需手动拼上桌面端 / GPU / source-free override
    if [ -f "$GPU_COMPOSE_OVERRIDE" ] || [ -f docker-compose.desktop.yaml ] || should_use_source_free_compose; then
        compose_args=(-f docker-compose.yaml)
        if [ -f docker-compose.desktop.yaml ] && { [ -n "${EASYAIOT_DESKTOP_OS:-}" ] || [ "${EASYAIOT_COMPOSE_DESKTOP:-0}" = "1" ]; }; then
            compose_args+=(-f docker-compose.desktop.yaml)
        fi
        if [ -f "$GPU_COMPOSE_OVERRIDE" ]; then
            compose_args+=(-f "$GPU_COMPOSE_OVERRIDE")
        fi
        append_source_free_compose_file compose_args
    fi
    compose_log=$(mktemp)
    if ! $COMPOSE_CMD "${compose_args[@]}" up "$@" >"$compose_log" 2>&1; then
        cat "$compose_log"
        rm -f "$compose_log"
        print_error "Docker Compose 创建/更新容器失败"
        return 1
    fi
    grep -v "^Creating\|^Starting\|^Pulling\|^Waiting\|^Container" "$compose_log" || true
    rm -f "$compose_log"
}

# 检查 GPU 支持
GPU_AVAILABLE=false
GPU_HARDWARE_DETECTED=false

# 架构检测
ARCH=""
DOCKER_PLATFORM=""
BASE_IMAGE=""

# 检测服务器架构并验证是否支持
# ★ 如果 DOCKER_PLATFORM 已由上层（runtime_image.sh 跨架构构建）导出，则信任外部设置
detect_architecture() {
    print_info "检测服务器架构..."
    ARCH=$(uname -m)

    # ★ 跨架构构建：DOCKER_PLATFORM 已由 runtime_image.sh 预设，直接信任
    if [ -n "${DOCKER_PLATFORM:-}" ]; then
        case "$ARCH" in
            x86_64|amd64) ARCH="x86_64" ;;
            aarch64|arm64) ARCH="aarch64" ;;
            *) ARCH="x86_64" ;;
        esac
        BASE_IMAGE="${BASE_IMAGE:-pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime}"
        print_success "检测到宿主机架构: ${ARCH}，使用外部指定平台: ${DOCKER_PLATFORM}"
        print_info "使用 PyTorch CUDA 镜像: $BASE_IMAGE"
        export DOCKER_PLATFORM
        export BASE_IMAGE
        return 0
    fi

    case "$ARCH" in
        x86_64|amd64)
            ARCH="x86_64"
            DOCKER_PLATFORM="linux/amd64"
            BASE_IMAGE="pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime"
            print_success "检测到架构: $ARCH (x86_64)"
            print_info "使用 PyTorch CUDA 镜像: $BASE_IMAGE"
            ;;
        aarch64|arm64|armv7l|armv6l)
            # 桌面端（macOS Apple Silicon）或已拉取预构建镜像：允许 CPU 模式容器部署
            if [ -n "${EASYAIOT_DESKTOP_OS:-}" ] || [ "${EASYAIOT_COMPOSE_DESKTOP:-0}" = "1" ] \
              || [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]; then
                ARCH="aarch64"
                DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/arm64}"
                BASE_IMAGE="${BASE_IMAGE:-pytorch/pytorch:2.1.0-cpu}"
                print_success "检测到 ARM 架构: $ARCH（桌面/镜像部署，CPU 模式）"
                print_info "平台: $DOCKER_PLATFORM，基础镜像: $BASE_IMAGE"
                export DOCKER_PLATFORM
                export BASE_IMAGE
                return 0
            fi
            print_error "检测到 ARM 架构 ($ARCH)"
            print_error "NVIDIA 官方的 CUDA 容器化只支持 x86_64 架构"
            print_error "ARM 服务器不支持容器化部署，部署已终止"
            echo ""
            print_info "如需在 ARM 服务器上运行，请考虑："
            print_info "1. 使用原生 Python 环境直接运行（非容器化）"
            print_info "2. 使用支持 ARM 的 CPU 版本 PyTorch（性能较低）"
            print_info "3. macOS 请使用: .scripts/docker/install_mac.sh（预构建镜像）"
            exit 1
            ;;
        *)
            print_error "未识别的架构: $ARCH"
            print_error "本服务仅支持 x86_64 架构，部署已终止"
            exit 1
            ;;
    esac

    # 导出环境变量供docker-compose使用
    export DOCKER_PLATFORM
    export BASE_IMAGE
}

# 配置架构相关的docker-compose设置
configure_architecture() {
    print_info "配置 Docker Compose 架构设置..."

    # 创建或更新 .env.arch 文件来存储架构配置
    if [ ! -f .env.arch ] || ! grep -q "DOCKER_PLATFORM=" .env.arch 2>/dev/null; then
        echo "# 架构配置（由install_linux.sh自动生成）" > .env.arch
        echo "DOCKER_PLATFORM=$DOCKER_PLATFORM" >> .env.arch
        echo "BASE_IMAGE=$BASE_IMAGE" >> .env.arch
        print_success "已创建架构配置文件 .env.arch"
    else
        # 更新现有配置（临时文件方式，兼容 macOS BSD sed）
        _set_env_docker_kv .env.arch DOCKER_PLATFORM "$DOCKER_PLATFORM"
        _set_env_docker_kv .env.arch BASE_IMAGE "$BASE_IMAGE"
        print_info "已更新架构配置文件 .env.arch"
    fi

    print_success "架构配置完成: $ARCH -> $DOCKER_PLATFORM"
}

# 检查 NVIDIA Container Toolkit 是否安装
check_nvidia_container_toolkit() {
    if dpkg -l | grep -q nvidia-container-toolkit; then
        return 0
    else
        return 1
    fi
}

# 安装 NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    print_info "开始安装 NVIDIA Container Toolkit..."

    # 检查是否有 sudo 权限
    if ! sudo -n true 2>/dev/null; then
        print_error "需要 sudo 权限来安装 NVIDIA Container Toolkit"
        print_info "请手动运行以下命令安装："
        echo ""
        echo "distribution=\$(. /etc/os-release;echo \$ID\$VERSION_ID) \\"
        echo "    && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \\"
        echo "    && curl -s -L https://nvidia.github.io/nvidia-docker/\$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list"
        echo ""
        echo "sudo apt update"
        echo "sudo apt install -y nvidia-container-toolkit"
        echo "sudo systemctl restart docker"
        echo ""
        return 1
    fi

    # 添加 NVIDIA Docker 仓库
    print_info "添加 NVIDIA Docker 仓库..."
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
        && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
        && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

    if [ $? -ne 0 ]; then
        print_error "添加 NVIDIA Docker 仓库失败"
        return 1
    fi

    # 更新软件包列表
    print_info "更新软件包列表..."
    sudo apt update -qq > /dev/null 2>&1

    # 安装 nvidia-container-toolkit
    print_info "安装 nvidia-container-toolkit..."
    sudo apt install -qq -y nvidia-container-toolkit > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        print_error "安装 nvidia-container-toolkit 失败"
        return 1
    fi

    # 配置 Docker daemon.json
    print_info "配置 Docker daemon.json..."
    DOCKER_DAEMON_JSON="/etc/docker/daemon.json"

    # 检查文件是否存在
    if [ -f "$DOCKER_DAEMON_JSON" ]; then
        # 备份原文件
        sudo cp "$DOCKER_DAEMON_JSON" "${DOCKER_DAEMON_JSON}.bak"
        print_info "已备份原 daemon.json 为 ${DOCKER_DAEMON_JSON}.bak"

        # 检查是否已有 nvidia runtime 配置
        if grep -q "nvidia" "$DOCKER_DAEMON_JSON"; then
            print_info "daemon.json 中已存在 nvidia 配置"
        else
            # 使用 Python 或 jq 来添加配置（如果可用）
            if command -v python3 &> /dev/null; then
                sudo python3 << EOF
import json
import sys

try:
    with open('$DOCKER_DAEMON_JSON', 'r') as f:
        config = json.load(f)
except:
    config = {}

# 添加 nvidia runtime 配置
if 'runtimes' not in config:
    config['runtimes'] = {}

config['runtimes']['nvidia'] = {
    "path": "nvidia-container-runtime",
    "runtimeArgs": []
}

# 设置默认 runtime（可选）
if 'default-runtime' not in config:
    config['default-runtime'] = 'nvidia'

with open('$DOCKER_DAEMON_JSON', 'w') as f:
    json.dump(config, f, indent=2)
EOF
            else
                # 如果没有 Python，使用简单的方法
                print_warning "未找到 Python3，将手动配置 daemon.json"
                print_info "请手动编辑 $DOCKER_DAEMON_JSON，添加以下内容："
                echo ""
                echo '{'
                echo '  "default-runtime": "nvidia",'
                echo '  "runtimes": {'
                echo '    "nvidia": {'
                echo '      "path": "nvidia-container-runtime",'
                echo '      "runtimeArgs": []'
                echo '    }'
                echo '  }'
                echo '}'
                echo ""
                print_warning "配置完成后，请运行: sudo systemctl restart docker"
                return 1
            fi
        fi
    else
        # 文件不存在，创建新文件
        sudo tee "$DOCKER_DAEMON_JSON" > /dev/null << EOF
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
EOF
    fi

    # 重启 Docker 服务
    print_info "重启 Docker 服务..."
    sudo systemctl restart docker

    if [ $? -eq 0 ]; then
        print_success "NVIDIA Container Toolkit 安装完成"
        return 0
    else
        print_error "重启 Docker 服务失败"
        return 1
    fi
}

check_gpu() {
    if check_command nvidia-smi; then
        local smi_indexes
        smi_indexes=$(nvidia-smi --query-gpu=index --format=csv,noheader,nounits 2>/dev/null \
            | awk '{$1=$1; print}' | paste -sd, -)
        if ! echo "$smi_indexes" | grep -qE '^[0-9]+(,[0-9]+)*$'; then
            print_warning "检测到 nvidia-smi，但无法与 NVIDIA 驱动通信，将使用 CPU 模式"
            print_warning "$(nvidia-smi 2>&1 | head -n 1 || true)"
            GPU_HARDWARE_DETECTED=false
            GPU_AVAILABLE=false
            return
        fi
        GPU_HARDWARE_DETECTED=true
        print_info "检测到 NVIDIA GPU:"
        nvidia-smi --query-gpu=name,driver_version --format=csv,noheader,nounits 2>/dev/null | while IFS=, read -r name version; do
            echo "  - GPU: $name (驱动版本: $version)"
        done

        # 检查 nvidia-container-toolkit 是否安装
        print_info "检查 NVIDIA Container Toolkit..."

        if check_nvidia_container_toolkit; then
            print_success "NVIDIA Container Toolkit 已安装"
        else
            print_warning "NVIDIA Container Toolkit 未安装"
            # 获取GPU名称用于提示
            GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -1 | xargs)
            print_info "检测到 GPU 硬件（${GPU_NAME}），但 NVIDIA Container Toolkit 未安装"
            echo ""
            print_info "是否自动安装 NVIDIA Container Toolkit？(Y/n)"
            read -t 15 -r response || response="Y"

            if [[ ! "$response" =~ ^([nN][oO]|[nN])$ ]]; then
                if install_nvidia_container_toolkit; then
                    print_success "NVIDIA Container Toolkit 安装成功"
                else
                    print_error "NVIDIA Container Toolkit 安装失败，将使用 CPU 模式"
                    GPU_AVAILABLE=false
                    return
                fi
            else
                print_info "跳过安装，将使用 CPU 模式运行"
                GPU_AVAILABLE=false
                return
            fi
        fi

        # 检查 docker info 中是否有 nvidia runtime
        print_info "检查 Docker NVIDIA runtime 配置..."
        if docker info --format '{{.Runtimes}}' 2>/dev/null | grep -q "nvidia"; then
            print_success "检测到 Docker 支持 NVIDIA runtime"
            # 再测试实际运行
            if docker run --rm --gpus all nvidia/cuda:11.7.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
                print_success "NVIDIA Container Toolkit 已正确配置"
                GPU_AVAILABLE=true
            else
                print_warning "Docker 支持 NVIDIA，但测试运行失败，回退 CPU 模式"
                print_info "常见原因：驱动未加载、权限不足或 CUDA 测试镜像拉取失败"
                GPU_AVAILABLE=false
            fi
        else
            print_warning "Docker daemon.json 中未配置 NVIDIA runtime"
            print_info "尝试配置 Docker daemon.json..."
            if install_nvidia_container_toolkit; then
                # 重新检查
                sleep 2
                if docker info --format '{{.Runtimes}}' 2>/dev/null | grep -q "nvidia"; then
                    print_success "Docker NVIDIA runtime 配置成功"
                    GPU_AVAILABLE=true
                else
                    print_warning "配置后仍无法检测到 NVIDIA runtime，将使用 CPU 模式"
                    GPU_AVAILABLE=false
                fi
            else
                print_warning "配置失败，将使用 CPU 模式"
                GPU_AVAILABLE=false
            fi
        fi
    else
        print_warning "未检测到 NVIDIA GPU，将使用 CPU 模式运行"
        GPU_HARDWARE_DETECTED=false
        GPU_AVAILABLE=false
    fi
}

# 配置 GPU 支持（如果可用）
resolve_gpu_override_devices() {
    local configured="${EASYAIOT_CUDA_VISIBLE_DEVICES:-}"
    if [ -z "$configured" ] && [ -f "$GPU_LOCAL_ENV" ]; then
        configured=$(sed -n 's/^EASYAIOT_CUDA_VISIBLE_DEVICES=//p' "$GPU_LOCAL_ENV" | tail -1)
    fi
    if [ -z "$configured" ] && [ -f .env.docker ]; then
        configured=$(sed -n 's/^EASYAIOT_CUDA_VISIBLE_DEVICES=//p' .env.docker | tail -1)
    fi
    printf '%s' "$configured"
}

write_gpu_compose_override() {
    local override_devices="$1"
    local temp_file="${GPU_COMPOSE_OVERRIDE}.tmp"
    {
        echo 'services:'
        echo '  ai-service:'
        echo '    runtime: nvidia'
        echo '    environment:'
        echo '      USE_GPU: "True"'
        echo '      NVIDIA_VISIBLE_DEVICES: "all"'
        if [ -n "$override_devices" ]; then
            echo "      EASYAIOT_CUDA_VISIBLE_DEVICES: \"${override_devices}\""
        fi
        echo '    deploy:'
        echo '      resources:'
        echo '        reservations:'
        echo '          devices:'
        echo '            - driver: nvidia'
        echo '              count: all'
        echo '              capabilities: [gpu]'
    } > "$temp_file"
    mv "$temp_file" "$GPU_COMPOSE_OVERRIDE"
}

write_cpu_compose_override() {
    local temp_file="${GPU_COMPOSE_OVERRIDE}.tmp"
    # daemon 若 default-runtime=nvidia，而驱动未加载时，带 com.nvidia.volumes.needed
    # 标签的 PyTorch 镜像会在 CDI 阶段失败；强制 runc 才能纯 CPU 启动。
    {
        echo 'services:'
        echo '  ai-service:'
        echo '    runtime: runc'
        echo '    environment:'
        echo '      USE_GPU: "False"'
        echo '      NVIDIA_VISIBLE_DEVICES: ""'
    } > "$temp_file"
    mv "$temp_file" "$GPU_COMPOSE_OVERRIDE"
}

configure_gpu() {

    if [ "$GPU_AVAILABLE" != true ]; then
        write_cpu_compose_override
        print_success "未启用 GPU，容器将使用 CPU 模式（runtime: runc）"
        return 0
    fi

    local host_devices override_devices gpu_id seen_ids
    host_devices=$(nvidia-smi --query-gpu=index --format=csv,noheader,nounits 2>/dev/null \
        | awk '{$1=$1; print}' | paste -sd, -)
    if ! echo "$host_devices" | grep -qE '^[0-9]+(,[0-9]+)*$'; then
        print_warning "无法读取有效的宿主机 GPU 列表，回退 CPU 模式: ${host_devices:-空}"
        GPU_AVAILABLE=false
        write_cpu_compose_override
        return 0
    fi

    override_devices=$(resolve_gpu_override_devices)
    if [ -z "$override_devices" ]; then
        write_gpu_compose_override ""
        print_success "容器 GPU 将按服务器自动探测: ${host_devices}"
        return 0
    fi
    if ! echo "$override_devices" | grep -qE '^[0-9]+(,[0-9]+)*$'; then
        print_error "EASYAIOT_CUDA_VISIBLE_DEVICES 格式无效: ${override_devices}"
        return 1
    fi

    seen_ids=" "
    for gpu_id in ${override_devices//,/ }; do
        if ! printf '%s\n' ",${host_devices}," | grep -q ",${gpu_id},"; then
            print_error "指定 GPU ${gpu_id} 不存在，宿主机可用 GPU: ${host_devices}"
            return 1
        fi
        if [[ "$seen_ids" == *" ${gpu_id} "* ]]; then
            print_error "EASYAIOT_CUDA_VISIBLE_DEVICES 包含重复 GPU: ${gpu_id}"
            return 1
        fi
        seen_ids+="${gpu_id} "
    done
    write_gpu_compose_override "$override_devices"
    print_success "容器 GPU 已按配置限制为: ${override_devices}（宿主机: ${host_devices}）"
}

verify_container_gpu_visibility() {
    if [ "$GPU_AVAILABLE" != true ]; then
        return 0
    fi

    local host_gpu_count expected_gpu_count override_devices container_gpu_count attempt gpu_status_json
    host_gpu_count=$(nvidia-smi --query-gpu=index --format=csv,noheader,nounits 2>/dev/null \
        | sed '/^[[:space:]]*$/d' | wc -l | tr -d ' ')
    if [ -z "$host_gpu_count" ] || [ "$host_gpu_count" -le 0 ]; then
        print_warning "无法读取宿主机 GPU 数量，跳过容器 GPU 数量校验"
        return 0
    fi

    expected_gpu_count="$host_gpu_count"
    override_devices=$(resolve_gpu_override_devices)
    if [ -n "$override_devices" ]; then
        expected_gpu_count=$(printf '%s\n' "$override_devices" | tr ',' '\n' \
            | sed '/^[[:space:]]*$/d' | wc -l | tr -d ' ')
    fi

    container_gpu_count=""
    gpu_status_json=""
    for attempt in $(seq 1 45); do
        gpu_status_json=$(curl -fsS --max-time 3 \
            http://127.0.0.1:5000/model/train_task/gpu/status 2>/dev/null || true)
        if [ -n "$gpu_status_json" ]; then
            container_gpu_count=$(printf '%s' "$gpu_status_json" | python3 -c \
                'import json,sys; print(json.load(sys.stdin).get("data", {}).get("device_count", ""))' \
                2>/dev/null || true)
        fi
        if echo "$container_gpu_count" | grep -qE '^[0-9]+$'; then
            break
        fi
        sleep 2
    done

    if ! echo "$container_gpu_count" | grep -qE '^[0-9]+$'; then
        print_error "无法通过应用接口读取 ai-service GPU 数量"
        return 1
    fi
    if [ "$container_gpu_count" -ne "$expected_gpu_count" ]; then
        print_error "GPU 可见数量不符合预期: 期望=${expected_gpu_count} 张，宿主机=${host_gpu_count} 张，ai-service=${container_gpu_count} 张"
        print_info "容器设备申请: $(docker inspect ai-service --format '{{json .HostConfig.DeviceRequests}}' 2>/dev/null || echo '读取失败')"
        print_info "容器配置环境: $(docker inspect ai-service --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep -E 'CUDA_VISIBLE_DEVICES|EASYAIOT_CUDA_VISIBLE_DEVICES|NVIDIA_VISIBLE_DEVICES|GPU_IDS' | tr '\n' ' ')"
        print_info "应用 GPU 接口: ${gpu_status_json:-无响应}"
        return 1
    fi

    if [ -n "$override_devices" ]; then
        print_success "GPU 暴露校验通过: ai-service 按配置可见 ${container_gpu_count} 张 GPU [${override_devices}]（宿主机 ${host_gpu_count} 张）"
    else
        print_success "GPU 暴露校验通过: ai-service 可见 ${container_gpu_count}/${host_gpu_count} 张 GPU"
    fi
}

# 检查并创建 Docker 网络
check_network() {
    print_info "检查 Docker 网络 easyaiot-network..."

    # 检查网络是否已存在（使用网络名称而不是ID）
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

# 创建 .env.docker 文件（用于Docker部署）
create_env_file() {
    if [ ! -f .env.docker ]; then
        print_info ".env.docker 文件不存在，正在创建..."
        if [ -f env.example ]; then
            cp env.example .env.docker
            print_success ".env.docker 文件已从 env.example 创建"

            # 自动配置中间件连接信息（临时文件写回，兼容 macOS BSD sed）
            print_info "自动配置中间件连接信息..."
            _set_env_docker_kv .env.docker DATABASE_URL "postgresql://postgres:iot45722414822@localhost:5432/iot-ai20"
            _set_env_docker_kv .env.docker NACOS_SERVER "localhost:8848"
            _set_env_docker_kv .env.docker MINIO_ENDPOINT "localhost:9000"
            _set_env_docker_kv .env.docker MINIO_SECRET_KEY "basiclab@iot975248395"
            _set_env_docker_kv .env.docker NACOS_PASSWORD "basiclab@iot78475418754"
            _set_env_docker_kv .env.docker NACOS_NAMESPACE ""

            print_success "中间件连接信息已自动配置"
            print_info "如需修改其他配置，请编辑 .env.docker 文件"
        else
            print_error "env.example 文件不存在，无法创建 .env.docker 文件"
            exit 1
        fi
    else
        print_info ".env.docker 文件已存在"
        if [ -n "${EASYAIOT_DESKTOP_OS:-}" ] || [ "${EASYAIOT_COMPOSE_DESKTOP:-0}" = "1" ]; then
            print_info "桌面端部署：使用容器网络中间件地址（postgres-server / iot-system）"
            _set_env_docker_kv .env.docker DATABASE_URL "postgresql://postgres:iot45722414822@postgres-server:5432/iot-ai20"
            _set_env_docker_kv .env.docker JAVA_BACKEND_URL "http://iot-system:48099"
            _set_env_docker_kv .env.docker REDIS_HOST "redis-server"
        else
            print_info "检查并更新中间件连接信息..."

            # 检查并更新数据库连接（如果使用Docker服务名，改为localhost，因为使用host网络模式）
            if grep -q "DATABASE_URL=.*PostgresSQL" .env.docker || grep -q "DATABASE_URL=.*postgres-server" .env.docker; then
                _set_env_docker_kv .env.docker DATABASE_URL "postgresql://postgres:iot45722414822@localhost:5432/iot-ai20"
                print_info "已更新数据库连接为 localhost:5432（host网络模式）"
            fi

            # 检查并更新Nacos配置（如果使用Docker服务名或IP地址，改为localhost，因为使用host网络模式）
            if grep -q "NACOS_SERVER=.*Nacos" .env.docker || grep -q "NACOS_SERVER=.*14\.18\.122\.2" .env.docker || grep -q "NACOS_SERVER=.*nacos-server" .env.docker; then
                _set_env_docker_kv .env.docker NACOS_SERVER "localhost:8848"
                print_info "已更新Nacos连接为 localhost:8848（host网络模式）"
            fi

            # 检查并更新MinIO配置（如果使用Docker服务名，改为localhost，因为使用host网络模式）
            if grep -q "MINIO_ENDPOINT=.*MinIO" .env.docker || grep -q "MINIO_ENDPOINT=.*minio-server" .env.docker; then
                _set_env_docker_kv .env.docker MINIO_ENDPOINT "localhost:9000"
                print_info "已更新MinIO连接为 localhost:9000（host网络模式）"
            fi
        fi

        # 检查并更新Nacos命名空间（如果设置为local或其他非空值，则重置为空，使用默认命名空间）
        if grep -q "^NACOS_NAMESPACE=.*" .env.docker && ! grep -q "^NACOS_NAMESPACE=$" .env.docker; then
            _set_env_docker_kv .env.docker NACOS_NAMESPACE ""
            print_info "已更新Nacos命名空间为空（使用默认命名空间）"
        fi
    fi

    ensure_deploy_profile
    apply_python_service_deploy_env "${EASYAIOT_ROOT}"
    if is_mini_deploy_profile; then
        print_info "mini 形态：已配置本机部署（JAVA_BACKEND_URL=48099, NODE_REMOTE_DEPLOY=false）"
        migrate_mini_minio_data_to_local_storage "${EASYAIOT_ROOT}"
    else
        print_info "${EASYAIOT_DEPLOY_PROFILE:-full} 形态：已配置网关部署（JAVA_BACKEND_URL=48080, MinIO 启用）"
    fi
}

# 安装服务
install_service() {
    print_info "开始安装 AI 服务..."

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
    detect_architecture
    configure_architecture
    check_network
    check_gpu
    create_directories
    create_env_file
    configure_gpu

    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && docker image inspect ai-service:latest >/dev/null 2>&1; then
        print_success "镜像已从远程拉取 (ai-service:latest)，跳过 pip 离线包下载与 Docker 构建"
    else
        print_info "构建 Docker 镜像（优先复用离线 pip 缓存）..."
        print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
        print_warning "首次构建可能需要较长时间（10-30分钟），请耐心等待..."
        print_info "正在下载基础镜像和安装依赖..."
        print_info "构建进度将实时显示，请勿中断..."
        echo ""

        if ! build_with_cache ""; then
            exit 1
        fi
        echo ""
        print_success "AI 服务镜像构建完成！"
    fi

    print_info "启动服务..."
    cleanup_renamed_containers
    compose_up_or_fail -d --remove-orphans --quiet-pull

    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 5

    # 检查服务状态
    check_status
    verify_container_gpu_visibility

    print_info "AI 服务访问地址: http://localhost:5000"
    print_info "AI 健康检查: http://localhost:5000/actuator/health"
    print_info "数据集标注: WEB 数据集详情 → 图像数据集标注"
    print_info "查看日志: ./install_linux.sh logs"
}

# 启动服务（同步部署形态 env 后 force-recreate，使 compose env_file 注入生效）
start_service() {
    print_info "启动服务..."
    check_docker
    check_docker_compose
    check_network

    if [ ! -f .env.docker ]; then
        print_warning ".env.docker 文件不存在，正在创建..."
        create_env_file
    else
        ensure_deploy_profile
    fi
    check_gpu
    configure_gpu
    cleanup_renamed_containers
    compose_up_or_fail -d --force-recreate --remove-orphans --quiet-pull
    print_success "服务已启动"
    check_status
    verify_container_gpu_visibility
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    check_docker
    check_docker_compose

    $COMPOSE_CMD down --remove-orphans 2>&1 | grep -v "^Stopping\|^Removing\|^Network" || true
    print_success "服务已停止"
}

# 重启服务（同步部署形态 env 后 force-recreate）
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose

    ensure_deploy_profile
    check_gpu
    configure_gpu
    compose_up_or_fail -d --force-recreate --remove-orphans --quiet-pull
    print_success "服务已重启"
    check_status
    verify_container_gpu_visibility
}

# 查看服务状态
check_status() {
    print_info "服务状态:"
    check_docker
    check_docker_compose

    $COMPOSE_CMD ps 2>/dev/null | head -20

    echo ""
    print_info "容器健康状态:"
    local any_running=false
    for svc in ai-service; do
        if docker ps --filter "name=^${svc}$" --format "{{.Names}}" 2>/dev/null | grep -q "^${svc}$"; then
            any_running=true
            docker ps --filter "name=^${svc}$" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null
            HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "N/A")
            if [ "$HEALTH" != "N/A" ]; then
                echo "${svc} 健康状态: $HEALTH"
            fi
        else
            print_warning "${svc} 未运行"
        fi
    done
    if [ "$any_running" = true ]; then
        print_info "AI 服务: http://localhost:5000"
    fi
}

# 查看日志
view_logs() {
    check_docker
    check_docker_compose

    if [ "$1" == "-f" ] || [ "$1" == "--follow" ]; then
        print_info "实时查看日志（按 Ctrl+C 退出）..."
        $COMPOSE_CMD logs -f
    else
        print_info "查看最近日志..."
        $COMPOSE_CMD logs --tail=100
    fi
}

# 构建镜像
build_image() {
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture

    if [ "${FORCE_REBUILD:-0}" != "1" ] && docker image inspect ai-service:latest >/dev/null 2>&1; then
        print_success "ai-service:latest 已存在，跳过 Docker 构建（强制重建请设置 FORCE_REBUILD=1）"
        return 0
    fi

    print_info "重新构建 Docker 镜像..."
    print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
    print_warning "重新构建可能需要较长时间（10-30分钟），请耐心等待..."
    print_info "正在重新下载基础镜像和安装依赖..."
    print_info "构建进度将实时显示，请勿中断..."
    echo ""

    local cache_flag=""
    [ "${FORCE_REBUILD:-0}" = "1" ] && cache_flag="--no-cache"
    if ! build_with_cache "$cache_flag"; then
        exit 1
    fi
    echo ""
    print_success "AI 服务镜像构建完成"
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
        $COMPOSE_CMD down -v --remove-orphans 2>&1 | grep -v "^Stopping\|^Removing\|^Network" || true

        print_info "删除镜像..."
        docker rmi ai-service:latest >/dev/null 2>&1 || true
    print_success "清理完成"
}

# 更新服务
# 性能优化（命令接口/功能不变，与 VIDEO 保持一致）：
#   1. 业务源码经 docker-compose 卷挂载（./:/app）进容器。「仅改业务代码、依赖不变」时，
#      update 完全跳过 docker build：git pull 后只重启容器进程即可加载新代码（秒级），
#      把原先几十分钟的镜像重建从代码更新路径上彻底摘除。
#   2. 仅当以下任一成立时才重建镜像：镜像不存在 / FORCE_REBUILD=1 /
#      本次 git pull 改动了依赖或构建输入（requirements*.txt、Dockerfile、docker-entrypoint.sh）。
#   3. 需要构建时复用 BuildKit 层缓存 + 离线 pip 缓存（build_with_cache 已内置 prepare）。
update_service() {
    print_info "更新服务..."
    check_docker
    check_docker_compose
    detect_architecture
    configure_architecture
    check_network

    # 记录更新前代码版本，用于判断依赖/构建文件是否变化
    local rev_before=""
    rev_before="$(git rev-parse HEAD 2>/dev/null || echo "")"

    print_info "拉取最新代码..."
    # --ff-only：快进失败立即返回，不产生意外合并提交，比默认 pull 更快更安全
    if ! git pull --ff-only; then
        print_error "Git pull 失败，已停止更新，未重建旧版本容器"
        return 1
    fi

    local rev_after=""
    rev_after="$(git rev-parse HEAD 2>/dev/null || echo "")"

    check_gpu
    configure_gpu

    # ---- 判断是否需要重建镜像 ----
    local needs_build=0
    if ! docker image inspect ai-service:latest >/dev/null 2>&1; then
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
        print_info "架构: $ARCH, 平台: $DOCKER_PLATFORM, 基础镜像: $BASE_IMAGE"
        print_warning "构建可能需要较长时间（10-30分钟），请耐心等待..."
        echo ""
        if ! build_with_cache ""; then
            exit 1
        fi
        echo ""
        print_success "AI 服务镜像构建完成！"
        print_info "应用新镜像（仅重建变更服务，最小化停机）..."
        cleanup_renamed_containers
        compose_up_or_fail -d --force-recreate --remove-orphans --no-deps --quiet-pull ai-service
    else
        print_success "依赖未变，跳过镜像构建（业务代码经卷挂载，重建容器即可生效）"
        # update 必须重建容器：docker restart 不会刷新 env_file/environment，
        # 否则 CUDA_VISIBLE_DEVICES 等本地配置修改会继续沿用旧容器环境。
        cleanup_renamed_containers
        compose_up_or_fail -d --force-recreate --remove-orphans --no-deps --quiet-pull ai-service
    fi

    print_success "服务更新完成"
    check_status
    verify_container_gpu_visibility
}

# 显示帮助信息
show_help() {
    echo "AI 服务 Docker Compose 管理脚本"
    echo ""
    echo "管理服务:"
    echo "  - ai-service (端口 5000，含 /model/dataset 自动标注 API)"
    echo ""
    echo "使用方法:"
    echo "  ./install_linux.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  install    - 安装并启动服务（首次运行）"
    echo "  start      - 启动服务"
    echo "  stop       - 停止服务"
    echo "  restart    - 重启服务"
    echo "  status     - 查看服务状态"
    echo "  logs       - 查看服务日志"
    echo "  logs -f    - 实时查看服务日志"
    echo "  build      - 重新构建镜像"
    echo "  clean      - 清理容器和镜像"
    echo "  update     - 更新并重启服务"
    echo "  help       - 显示此帮助信息"
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