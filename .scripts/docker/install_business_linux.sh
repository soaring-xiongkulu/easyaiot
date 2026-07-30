#!/bin/bash

# ============================================
# EasyAIoT 业务系统统一管理脚本
# ============================================
# 管理模块: DEVICE、AI、VIDEO、WEB、APP、VISUALIZE、TRANSFORM、PANEL（不含中间件；APP/VISUALIZE/TRANSFORM 仅 full；PANEL 全形态）
# 各模块实际逻辑委托给对应目录下的 install_linux.sh
#
# 用法:
#   ./install_business_linux.sh <命令> [选项] [模块...]
#
# 部署形态（EASYAIOT_DEPLOY_PROFILE）：
#   mini(1)     - 4G：iot-system + VIDEO/AI/WEB（无可视化）
#   standard(2) - 16G：不含 TDengine/iot-device/iot-tdengine/iot-visualize 等（含 EMQX）
#   full(3)     - 全量（默认，约 20G；含 iot-visualize/VISUALIZE、TRANSFORM）
#
# 示例:
#   ./install_business_linux.sh install              # 安装全部业务模块
#   ./install_business_linux.sh update DEVICE WEB    # 仅更新 DEVICE 与 WEB
#   ./install_business_linux.sh -m AI,VIDEO clean    # 清理 AI 与 VIDEO
#   ./install_business_linux.sh clean-all -y         # 完全清理（含 DEVICE 镜像）
#   ./install_business_linux.sh verify               # 验证全部业务服务健康
#   ./install_business_linux.sh logs DEVICE iot-gateway
# ============================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"

# shellcheck source=runtime_image_common.sh
source "${SCRIPT_DIR}/runtime_image_common.sh"

# shellcheck source=docker_mirror_common.sh
source "${SCRIPT_DIR}/docker_mirror_common.sh"

# shellcheck source=docker_compose_bundled.sh
source "${SCRIPT_DIR}/docker_compose_bundled.sh"

# shellcheck source=node/ensure_platform_agent_invoke.sh
source "${PROJECT_ROOT}/.scripts/node/ensure_platform_agent_invoke.sh"

_ensure_platform_agent_info() { print_info "$1"; }
_ensure_platform_agent_ok() { print_success "$1"; }
_ensure_platform_agent_warn() { print_warning "$1"; }

ensure_platform_agent_after_business_stack() {
    ENSURE_PLATFORM_AGENT_INFO=_ensure_platform_agent_info \
    ENSURE_PLATFORM_AGENT_OK=_ensure_platform_agent_ok \
    ENSURE_PLATFORM_AGENT_WARN=_ensure_platform_agent_warn \
    ensure_platform_agent_if_needed || true
}

ensure_mqtt_demo_after_business_stack() {
    local demo_dir="${PROJECT_ROOT}/.scripts/mqtt-demo"
    local starter="${demo_dir}/start_mqtt_demo.sh"
    if [ "${EASYAIOT_ENABLE_MQTT_DEMO:-1}" = "0" ]; then
        print_info "跳过 mqtt-demo 自动启动（EASYAIOT_ENABLE_MQTT_DEMO=0）"
        return 0
    fi
    if [ "${EASYAIOT_ENABLE_EMQX:-1}" = "0" ]; then
        print_info "跳过 mqtt-demo 自动启动（EMQX 未启用）"
        return 0
    fi
    if [ -f "$starter" ]; then
        chmod +x "$starter" "${demo_dir}/stop_mqtt_demo.sh" 2>/dev/null || true
        print_info "启动 MQTT 演示设备（01/02/03 并行）..."
        bash "$starter" || print_warning "mqtt-demo 启动未完全成功，可手动: bash ${starter}"
    fi
}

ensure_industrial_demo_after_business_stack() {
    local demo_dir="${PROJECT_ROOT}/.scripts/industrial-demo"
    local starter="${demo_dir}/start_industrial_demo.sh"
    ensure_deploy_profile
    if ! is_full_deploy_profile; then
        print_info "跳过工业协议演示（仅 full 形态，当前: ${EASYAIOT_DEPLOY_PROFILE}）"
        return 0
    fi
    if [ "${EASYAIOT_ENABLE_INDUSTRIAL_DEMO:-1}" = "0" ]; then
        print_info "跳过工业协议演示（EASYAIOT_ENABLE_INDUSTRIAL_DEMO=0）"
        return 0
    fi
    if [ -f "$starter" ]; then
        chmod +x "$starter" "${demo_dir}/stop_industrial_demo.sh" 2>/dev/null || true
        print_info "启动工业协议演示（Modbus TCP / RTU / OPC UA）..."
        bash "$starter" || print_warning "industrial-demo 启动未完全成功，可手动: bash ${starter}"
    fi
}

# 业务模块（按依赖顺序：网关/微服务 -> AI/视频 -> 前端 -> 全量模块 -> 运维控制台）
ALL_MODULES=(DEVICE AI VIDEO WEB APP VISUALIZE TRANSFORM PANEL)

declare -A MODULE_NAMES=(
    [DEVICE]="Device 服务"
    [AI]="AI 服务"
    [VIDEO]="Video 服务"
    [WEB]="Web 前端"
    [APP]="App 移动端 H5"
    [VISUALIZE]="可视化编辑器"
    [TRANSFORM]="系统对接"
    [PANEL]="运维控制台"
)

declare -A MODULE_PORTS=(
    [DEVICE]="48080"
    [AI]="5000"
    [VIDEO]="6000"
    [WEB]="8888"
    [APP]="9010"
    [VISUALIZE]="8002"
    [TRANSFORM]="48096"
    [PANEL]="9200"
)

declare -A MODULE_HEALTH_ENDPOINTS=(
    [DEVICE]="/actuator/health"
    [AI]="/actuator/health"
    [VIDEO]="/actuator/health"
    [WEB]="/health"
    [APP]="/health"
    [VISUALIZE]="/health"
    [TRANSFORM]="/actuator/health"
    [PANEL]="/health"
)

LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/install_business_$(date +%Y%m%d_%H%M%S).log"

SELECTED_MODULES=()
MODULE_POSITIONAL=()
COMMAND=""
EXTRA_ARGS=()
AUTO_YES=false
STOP_ON_ERROR=true

log_to_file() {
    local clean
    clean=$(echo "$1" | sed -r 's/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g')
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $clean" >> "$LOG_FILE"
}

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; log_to_file "[INFO] $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; log_to_file "[OK] $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; log_to_file "[WARN] $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; log_to_file "[ERROR] $1"; }

# 模块日志分隔
print_module_banner() {
    local module="$1"
    local cmd="$2"
    local title="${MODULE_NAMES[$module]:-$module}"
    echo ""
    echo "================================================================"
    printf " [%s] %-12s  %s\n" "$module" "$cmd" "$title"
    echo "================================================================"
    echo ""
    log_to_file ""
    log_to_file "======== $module | $cmd | $title ========"
}

print_module_end() {
    local module="$1"
    local cmd="$2"
    local status="$3"
    echo "----------------------------------------------------------------"
    if [ "$status" = "ok" ]; then
        printf " [%s] %-12s  done\n" "$module" "$cmd"
        log_to_file "-------- $module | $cmd | done --------"
    else
        printf " [%s] %-12s  failed\n" "$module" "$cmd"
        log_to_file "-------- $module | $cmd | failed --------"
    fi
    echo "----------------------------------------------------------------"
    echo ""
}

check_command() {
    command -v "$1" &>/dev/null
}

check_docker() {
    if ! check_command docker; then
        print_error "未安装 Docker"
        exit 1
    fi
    if ! docker info &>/dev/null; then
        print_error "无法连接 Docker daemon，请确认服务已启动且当前用户有权限"
        exit 1
    fi
}

check_docker_compose() {
    local _need_fix=false
    if ! check_command docker-compose && ! docker compose version &>/dev/null 2>&1; then
        _need_fix=true
    elif ! compose_version_meets_requirement_quiet; then
        _need_fix=true
    fi

    if [ "$_need_fix" = true ]; then
        if bundled_compose_available; then
            local _bundled_ver
            _bundled_ver=$(get_bundled_compose_version 2>/dev/null || echo "未知")
            print_warning "Docker Compose 未安装或版本过低（需要 v${COMPOSE_MIN_VERSION}+）"
            print_info "将使用项目内置 Docker Compose v${_bundled_ver} 离线安装/升级（架构: $(uname -m)）"
            if [ "$EUID" -ne 0 ]; then
                print_error "请使用 sudo 运行以自动安装/升级 Docker Compose"
                exit 1
            fi
            if ! install_bundled_docker_compose || ! compose_version_meets_requirement_quiet; then
                print_error "内置 Docker Compose 安装/升级失败"
                exit 1
            fi
            print_success "Docker Compose 已就绪: $(docker compose version 2>/dev/null || docker-compose --version)"
            return 0
        fi
        print_error "未安装 Docker Compose 或版本过低，且当前架构无内置离线包"
        exit 1
    fi
}

create_network() {
    if docker network ls --format '{{.Name}}' | grep -qx 'easyaiot-network'; then
        print_info "网络 easyaiot-network 已存在"
        return 0
    fi
    print_info "创建网络 easyaiot-network..."
    if docker network create easyaiot-network &>/dev/null; then
        print_success "网络 easyaiot-network 已创建"
    else
        print_warning "创建网络失败或网络已存在，继续执行"
    fi
}

warn_middleware() {
    local ok=true
    ensure_deploy_profile
    if middleware_service_enabled Nacos; then
        if ! docker ps --format '{{.Names}}' | grep -q 'nacos-server'; then
            print_warning "未检测到 nacos-server，业务服务可能依赖中间件，请先执行: .scripts/docker/install_linux.sh install"
            ok=false
        fi
    fi
    if ! docker ps --format '{{.Names}}' | grep -q 'postgres-server'; then
        print_warning "未检测到 postgres-server"
        ok=false
    fi
    $ok
}

wait_for_service() {
    local port=$1
    local health_endpoint=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if [ -n "$health_endpoint" ]; then
            if curl -s --connect-timeout 2 "http://localhost:${port}${health_endpoint}" >/dev/null 2>&1; then
                return 0
            fi
        else
            if check_command nc && nc -z localhost "$port" 2>/dev/null; then
                return 0
            elif check_command timeout && timeout 1 bash -c "cat < /dev/null > /dev/tcp/localhost/$port" 2>/dev/null; then
                return 0
            elif curl -s --connect-timeout 1 "http://localhost:$port" >/dev/null 2>&1; then
                return 0
            fi
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    return 1
}

verify_module_health() {
    local module=$1
    local module_name="${MODULE_NAMES[$module]}"
    local port="${MODULE_PORTS[$module]}"
    local health_endpoint="${MODULE_HEALTH_ENDPOINTS[$module]}"

    ensure_deploy_profile
    if [ "$module" = "DEVICE" ] && is_mini_deploy_profile; then
        port="48099"
        health_endpoint=""
    fi

    print_module_banner "$module" "verify"
    print_info "检查 http://localhost:$port${health_endpoint} ..."

    if wait_for_service "$port" "$health_endpoint"; then
        if [ -n "$health_endpoint" ]; then
            local response
            response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}${health_endpoint}" 2>/dev/null || echo "000")
            if [ "$response" = "200" ] || [ "$response" = "000" ]; then
                print_success "$module_name 运行正常"
                print_module_end "$module" "verify" "ok"
                return 0
            fi
            print_warning "$module_name 响应异常 (HTTP $response)"
            print_module_end "$module" "verify" "fail"
            return 1
        fi
        print_success "$module_name 运行正常"
        print_module_end "$module" "verify" "ok"
        return 0
    fi

    print_error "$module_name 未就绪"
    print_module_end "$module" "verify" "fail"
    return 1
}

verify_all() {
    check_docker

    local success_count=0
    local total_count=${#SELECTED_MODULES[@]}
    local failed_modules=()
    local module

    for module in "${SELECTED_MODULES[@]}"; do
        if verify_module_health "$module"; then
            success_count=$((success_count + 1))
        else
            failed_modules+=("${MODULE_NAMES[$module]}")
        fi
    done

    echo ""
    if [ "$success_count" -eq "$total_count" ]; then
        print_success "验证通过 ($success_count/$total_count)"
        return 0
    fi

    print_error "验证失败 ($success_count/$total_count)"
    local name
    for name in "${failed_modules[@]}"; do
        echo "  ✗ $name"
    done
    return 1
}

fix_line_endings() {
    local script_file="$1"
    [ -f "$script_file" ] || return 1
    if grep -q $'\r' "$script_file" 2>/dev/null; then
        sed -i 's/\r$//' "$script_file" 2>/dev/null || tr -d '\r' <"$script_file" >"${script_file}.tmp" && mv "${script_file}.tmp" "$script_file"
        chmod u+x "$script_file" 2>/dev/null || true
    fi
}

is_valid_module() {
    local m="$1"
    local x
    for x in "${ALL_MODULES[@]}"; do
        [ "$x" = "$m" ] && return 0
    done
    return 1
}

normalize_module_name() {
    echo "$1" | tr '[:lower:]' '[:upper:]'
}

resolve_modules() {
    ensure_deploy_profile
    local tokens=("$@")
    local resolved=()
    local t norm

    if [ ${#tokens[@]} -eq 0 ]; then
        SELECTED_MODULES=()
        local mod
        for mod in "${ALL_MODULES[@]}"; do
            module_enabled_for_deploy_profile "$mod" || continue
            SELECTED_MODULES+=("$mod")
        done
        return 0
    fi

    for t in "${tokens[@]}"; do
        norm=$(normalize_module_name "$t")
        if ! is_valid_module "$norm"; then
            print_error "未知模块: $t（可选: ${ALL_MODULES[*]}）"
            exit 1
        fi
        if ! module_enabled_for_deploy_profile "$norm"; then
            print_warning "模块 $norm 在当前部署形态 ${EASYAIOT_DEPLOY_PROFILE:-full} 下不可用，已跳过"
            continue
        fi
        resolved+=("$norm")
    done

    SELECTED_MODULES=()
    local mod
    for mod in "${ALL_MODULES[@]}"; do
        for t in "${resolved[@]}"; do
            if [ "$mod" = "$t" ]; then
                SELECTED_MODULES+=("$mod")
                break
            fi
        done
    done
}

reverse_modules() {
    local reversed=()
    local i
    for ((i=${#SELECTED_MODULES[@]}-1; i>=0; i--)); do
        reversed+=("${SELECTED_MODULES[i]}")
    done
    SELECTED_MODULES=("${reversed[@]}")
}

map_module_command() {
    local module="$1"
    local cmd="$2"

    case "$cmd" in
        clean-all)
            if [ "$module" = "DEVICE" ]; then
                echo "clean-all"
            else
                echo "clean"
            fi
            ;;
        build-base)
            if [ "$module" = "DEVICE" ]; then
                echo "build-base"
            else
                echo ""
            fi
            ;;
        *)
            echo "$cmd"
            ;;
    esac
}

execute_module() {
    local module="$1"
    local cmd="$2"
    shift 2
    local mapped
    local module_dir="$PROJECT_ROOT/$module"
    local install_script="$module_dir/install_linux.sh"

    mapped=$(map_module_command "$module" "$cmd")
    [ -n "$mapped" ] || return 0

    if [ ! -d "$module_dir" ]; then
        if [ "$module" = "TRANSFORM" ]; then
            print_info "未检测到 TRANSFORM 目录，跳过系统对接部署"
            return 0
        fi
        if [ "$module" = "PANEL" ]; then
            print_info "未检测到 PANEL 目录，跳过运维控制台部署"
            return 0
        fi
        print_warning "目录不存在，跳过: $module"
        return 1
    fi

    if [ ! -f "$install_script" ]; then
        if [ "$module" = "TRANSFORM" ]; then
            print_info "未检测到 TRANSFORM/install_linux.sh，跳过系统对接部署"
            return 0
        fi
        if [ "$module" = "PANEL" ]; then
            print_info "未检测到 PANEL/install_linux.sh，跳过运维控制台部署"
            return 0
        fi
        print_warning "未找到 $install_script，跳过 $module"
        return 1
    fi

    fix_line_endings "$install_script"

    print_module_banner "$module" "$mapped"
    (
        cd "$module_dir"
        export EASYAIOT_AUTO_YES="${EASYAIOT_AUTO_YES:-0}"
        export EASYAIOT_DEFER_PLATFORM_AGENT_SYNC=1
        export EASYAIOT_DEPLOY_PROFILE
        export EASYAIOT_SKIP_PROFILE_PROMPT
        export EASYAIOT_SKIP_IMAGE_PROMPT
        export EASYAIOT_SKIP_BUILD
        bash install_linux.sh "$mapped" "$@"
    ) 2>&1 | tee -a "$LOG_FILE"

    local exit_code=${PIPESTATUS[0]}
    if [ "$exit_code" -ne 0 ]; then
        print_module_end "$module" "$mapped" "fail"
        print_error "$module 失败 (exit $exit_code)"
        return "$exit_code"
    fi
    print_module_end "$module" "$mapped" "ok"
    return 0
}

run_on_modules() {
    local cmd="$1"
    shift
    local module mapped_cmd
    local failed=()
    local need_network=false

    case "$cmd" in
        install|start|restart|update|build|build-base)
            need_network=true
            ;;
    esac

    check_docker
    check_docker_compose
    configure_docker_mirror

    if $need_network; then
        create_network
    fi

    if [[ "$cmd" == install || "$cmd" == start || "$cmd" == update ]]; then
        warn_middleware || true
    fi

    for module in "${SELECTED_MODULES[@]}"; do
        mapped_cmd=$(map_module_command "$module" "$cmd")
        if [ -z "$mapped_cmd" ]; then
            continue
        fi
        if execute_module "$module" "$mapped_cmd" "$@"; then
            :
        else
            failed+=("$module")
            if $STOP_ON_ERROR; then
                break
            fi
        fi
    done

    if [ ${#failed[@]} -gt 0 ]; then
        print_error "失败模块: ${failed[*]}"
        return 1
    fi

    case "$cmd" in
        install|start|restart|update)
            ensure_platform_agent_after_business_stack
            ensure_mqtt_demo_after_business_stack
            ensure_industrial_demo_after_business_stack
            ;;
    esac
    return 0
}

is_yes() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
        y|yes) return 0 ;;
        *) return 1 ;;
    esac
}

is_no() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
        n|no|'') return 0 ;;
        *) return 1 ;;
    esac
}

# 镜像获取（install 时由 runtime_image_common 统一处理）
init_runtime_images_for_install() {
    export EASYAIOT_INSTALL_SCRIPT=".scripts/docker/install_business_linux.sh"
    runtime_images_acquire
}

# 镜像更新（update 时由 runtime_image_common 统一处理）
init_runtime_images_for_update() {
    export EASYAIOT_INSTALL_SCRIPT=".scripts/docker/install_business_linux.sh"
    runtime_images_acquire_for_update
}

init_deploy_profile_for_command() {
    local cmd="$1"
    case "$cmd" in
        install)
            select_deploy_profile_for_install
            check_docker
            configure_docker_mirror
            init_runtime_images_for_install
            print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
            ;;
        update)
            ensure_deploy_profile
            check_docker
            configure_docker_mirror
            init_runtime_images_for_update
            if runtime_images_should_skip_build; then
                print_info "镜像已从远程拉取，业务模块将跳过 docker build"
            else
                print_info "将进行本地重建更新（各模块 docker build，耗时较长）"
            fi
            warn_web_rebuild_if_profile_changed
            print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
            ;;
        start|restart|verify|status|build|build-base|pull|build-runtime)
            ensure_deploy_profile
            warn_web_rebuild_if_profile_changed
            print_info "部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
            ;;
    esac
}

confirm_once() {
    $AUTO_YES && return 0
    local response
    while true; do
        read -r -p "确认继续? [y/n] " response
        if is_yes "$response"; then
            return 0
        fi
        if is_no "$response"; then
            print_info "已取消"
            return 1
        fi
        echo "请输入 y/yes 或 n/no"
    done
}

usage() {
    cat <<EOF
EasyAIoT 业务系统统一管理脚本

管理模块: DEVICE、AI、VIDEO、WEB、APP、VISUALIZE、TRANSFORM、PANEL（不含 Nacos/PostgreSQL 等中间件；APP/VISUALIZE/TRANSFORM 仅 full；PANEL 全形态）

用法:
  $0 <命令> [选项] [模块...]

命令:
  install       安装并启动（首次部署）
  start         启动服务
  stop          停止服务（逆序）
  restart       重启服务
  status        查看状态
  logs [服务名] 查看日志（可指定模块后接服务名，如 logs DEVICE iot-gateway）
  build         重新构建镜像（各模块本地构建）
  build-runtime 构建/推送运行时镜像到远程仓库
  pull          从远程仓库拉取预构建运行时镜像（交互式，默认 full）
  build-base    仅 DEVICE：Maven 编译并提取 Jar（第一阶段）
  clean         清理容器（DEVICE 保留镜像）
  clean-all     完全清理（DEVICE 含镜像；其他模块等同 clean）
  update        更新镜像并重启（交互可选拉取/本地重建）
  verify        验证服务健康（HTTP 健康检查 / 端口探测）
  profile       显示当前部署形态与服务范围
  help          显示帮助

选项:
  -m, --modules <列表>   逗号分隔模块，如 DEVICE,WEB
  -y, --yes              清理操作无需确认
  --continue-on-error    某模块失败后继续执行其余模块

模块:
  未指定时默认全部（按部署形态过滤），顺序为 DEVICE -> AI -> VIDEO -> WEB -> APP -> VISUALIZE -> TRANSFORM -> PANEL
  stop / clean / clean-all 时自动逆序执行

示例:
  $0 install
  $0 update WEB
  $0 pull
  $0 build-runtime
  $0 verify
  $0 verify DEVICE WEB
  $0 -m DEVICE,AI status
  $0 clean-all -y
  $0 logs VIDEO

说明:
  中间件请使用 .scripts/docker/install_linux.sh 或 install_middleware_linux.sh
  运行时镜像仓库配置: .scripts/docker/runtime_registry.conf
  环境变量 EASYAIOT_DEPLOY_PROFILE: mini(1) | standard(2) | full(3，默认)
  build-runtime 可选 EASYAIOT_RUNTIME_BUILD_ARCH: all(默认) | amd64 | arm64（单架构时跳过 manifest）
  build-runtime 可选 EASYAIOT_RUNTIME_BUILD_MODULE: all(默认) | DEVICE | AI | VIDEO | WEB | APP | VISUALIZE | TRANSFORM | PANEL
  日志: $LOG_DIR/
EOF
}

parse_args() {
    local positional=()
    local arg

    while [ $# -gt 0 ]; do
        arg="$1"
        case "$arg" in
            -h|--help|help)
                COMMAND="help"
                shift
                ;;
            -y|--yes)
                AUTO_YES=true
                shift
                ;;
            --continue-on-error)
                STOP_ON_ERROR=false
                shift
                ;;
            -m|--modules)
                [ -n "${2:-}" ] || { print_error "-m 需要模块列表"; exit 1; }
                IFS=',' read -r -a _mods <<<"$2"
                positional+=("${_mods[@]}")
                shift 2
                ;;
            install|start|stop|restart|status|logs|build|build-base|clean|clean-all|update|verify|profile|pull|build-runtime|images-pull|images-build)
                COMMAND="$arg"
                shift
                ;;
            -*)
                print_error "未知选项: $arg"
                usage
                exit 1
                ;;
            *)
                positional+=("$arg")
                shift
                ;;
        esac
    done

    if [ -z "$COMMAND" ]; then
        COMMAND="help"
        return 0
    fi

    if [ "$COMMAND" = "help" ]; then
        return 0
    fi

    MODULE_POSITIONAL=("${positional[@]}")

    if [ "$COMMAND" = "logs" ] && [ ${#positional[@]} -gt 0 ]; then
        local first
        first=$(normalize_module_name "${positional[0]}")
        if is_valid_module "$first"; then
            resolve_modules "$first"
            EXTRA_ARGS=("${positional[@]:1}")
            return 0
        fi
    fi

    # install 需在交互选定部署形态后再 resolve（见 main）
    if [ "$COMMAND" = "install" ]; then
        return 0
    fi

    resolve_modules "${positional[@]}"
}

main() {
    echo "=========================================" >>"$LOG_FILE"
    echo "install_business_linux.sh $*" >>"$LOG_FILE"
    echo "开始: $(date '+%Y-%m-%d %H:%M:%S')" >>"$LOG_FILE"
    echo "=========================================" >>"$LOG_FILE"

    parse_args "$@"

    case "$COMMAND" in
        help|"")
            usage
            ;;
        profile)
            ensure_deploy_profile
            print_deploy_profile_summary
            ;;
        verify)
            init_deploy_profile_for_command verify
            verify_all || exit 1
            ;;
        install)
            init_deploy_profile_for_command install
            resolve_modules "${MODULE_POSITIONAL[@]}"
            run_on_modules install "${EXTRA_ARGS[@]}" || exit 1
            ;;
        start|restart|update|build|build-base|status)
            init_deploy_profile_for_command "$COMMAND"
            run_on_modules "$COMMAND" "${EXTRA_ARGS[@]}" || exit 1
            ;;
        pull|images-pull)
            init_deploy_profile_for_command pull
            check_docker
            configure_docker_mirror
            runtime_images_prepare_pull_interactive
            runtime_images_export_for_invoke
            runtime_images_invoke pull || exit 1
            export EASYAIOT_SKIP_BUILD=1
            export EASYAIOT_SKIP_IMAGE_PROMPT=1
            ;;
        build-runtime|images-build)
            init_deploy_profile_for_command build-runtime
            check_docker
            runtime_images_prepare_build_interactive
            runtime_images_export_for_invoke
            runtime_images_invoke build || exit 1
            ;;
        stop|clean|clean-all)
            if [[ "$COMMAND" == clean* ]]; then
                confirm_once || exit 0
                export EASYAIOT_AUTO_YES=1
            fi
            reverse_modules
            run_on_modules "$COMMAND" "${EXTRA_ARGS[@]}" || exit 1
            ;;
        logs)
            run_on_modules "logs" "${EXTRA_ARGS[@]}" || exit 1
            ;;
        *)
            print_error "未知命令: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

main "$@"
