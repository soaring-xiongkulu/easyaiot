#!/bin/bash

# ============================================
# WEB服务 Docker Compose 管理脚本
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
#   build-frontend - 构建前端项目
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
# shellcheck source=../.scripts/docker/module_update_helpers.sh
source "${EASYAIOT_ROOT}/.scripts/docker/module_update_helpers.sh"

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

# 清理 compose recreate 被中断后遗留的「改名孤儿容器」（形如 <12位hex>_web-service）。
# recreate 时 compose 先把旧容器改名让出 container_name，中途被打断旧容器就残留；
# 它若仍在运行会占住宿主机端口，新容器起不来。--remove-orphans 清不掉它
# （只清「服务已从 compose 文件移除」的孤儿），须在 up 前按名主动删除。
cleanup_renamed_containers() {
    local names
    names=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E '^[0-9a-f]{12}_web-service$' || true)
    [ -z "$names" ] && return 0
    print_warning "清理上次中断遗留的改名孤儿容器: $(echo "$names" | tr '\n' ' ')"
    echo "$names" | xargs -r docker rm -f >/dev/null 2>&1 || true
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
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # 检查是 docker-compose 还是 docker compose
    if check_command docker-compose; then
        COMPOSE_CMD="docker-compose"
        print_success "Docker Compose 已安装: $(docker-compose --version)"
    else
        COMPOSE_CMD="docker compose"
        print_success "Docker Compose 已安装: $(docker compose version)"
    fi
}

# 检查当前部署形态是否与已记录的 WEB 镜像构建形态一致
# 返回 0 表示一致（可安全复用镜像），1 表示不一致或无法判断（应触发重建）
web_image_profile_matches() {
    ensure_deploy_profile
    local current_profile="${EASYAIOT_DEPLOY_PROFILE:-full}"
    local built_profile=""
    local profile_stamp="${EASYAIOT_ROOT}/.scripts/docker/.web_deploy_profile_built"
    if [ -f "$profile_stamp" ]; then
        built_profile=$(tr -d '\n' < "$profile_stamp")
    fi
    [ "$built_profile" = "$current_profile" ]
}

# 当前部署形态对应的 WEB 镜像本地标签（与 runtime_image.sh local_ref 一致）
web_profile_image_ref() {
    ensure_deploy_profile
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini|edge) echo "web-service:latest-mini" ;;
        standard) echo "web-service:latest-standard" ;;
        *)        echo "web-service:latest" ;;
    esac
}

# 将形态镜像打标为 docker-compose 使用的 web-service:latest
web_tag_compose_image() {
    local profile_ref compose_ref="web-service:latest"
    profile_ref=$(web_profile_image_ref)
    if [ "$profile_ref" = "$compose_ref" ]; then
        return 0
    fi
    if docker image inspect "$profile_ref" >/dev/null 2>&1; then
        docker tag "$profile_ref" "$compose_ref"
        print_info "已打标签: ${profile_ref} → ${compose_ref}（供 docker-compose 使用）"
        return 0
    fi
    return 1
}

# 解析远端拉取的 WEB 镜像（兼容旧版误标 web-service:latest-full）
web_resolve_pulled_image() {
    local profile_ref legacy_ref="web-service:latest-full"
    profile_ref=$(web_profile_image_ref)
    if docker image inspect "$profile_ref" >/dev/null 2>&1; then
        echo "$profile_ref"
        return 0
    fi
    ensure_deploy_profile
    if [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "full" ] && docker image inspect "$legacy_ref" >/dev/null 2>&1; then
        docker tag "$legacy_ref" "$profile_ref" 2>/dev/null || true
        echo "$profile_ref"
        return 0
    fi
    return 1
}

# 已选择拉取远端镜像且本地镜像就绪 → 跳过 vite/docker build
web_skip_build_from_pull() {
    [ "${EASYAIOT_SKIP_BUILD:-0}" != "1" ] && return 1
    local img
    img=$(web_resolve_pulled_image) || return 1
    web_tag_compose_image
    record_web_deploy_profile_built "${EASYAIOT_ROOT}"
    print_success "镜像已从远程拉取 (${img})，跳过 Docker 构建与 vite 编译"
    return 0
}

# docker-compose.yaml 将宿主机 dist 挂载到 nginx 静态目录。该挂载会覆盖镜像内
# Docker 构建产生的 dist，因此每次使用新镜像启动前都要把镜像产物同步到宿主机。
sync_web_dist_from_image() {
    local image_ref="${1:-web-service:latest}"
    local configured_dist="${WEB_DIST_DIR:-./dist}"
    local target_dist

    if ! docker image inspect "$image_ref" >/dev/null 2>&1; then
        print_error "WEB 镜像不存在，无法同步前端产物: ${image_ref}"
        return 1
    fi
    if [[ "$configured_dist" = /* ]]; then
        target_dist="$configured_dist"
    else
        target_dist="${SCRIPT_DIR}/${configured_dist#./}"
    fi
    case "$target_dist" in
        /|"$SCRIPT_DIR"|"$EASYAIOT_ROOT")
            print_error "拒绝将 WEB 静态产物同步到不安全目录: ${target_dist}"
            return 1
            ;;
    esac

    mkdir -p "$target_dist"
    # dist 通常由 root 身份的 nginx 容器写入；通过临时容器同步可避免宿主机
    # 普通部署用户在覆盖旧文件时遇到 permission denied。
    if ! docker run --rm --entrypoint sh -v "${target_dist}:/out" "$image_ref" \
        -lc 'cp -a /usr/share/nginx/html/. /out/'; then
        print_error "从 ${image_ref} 同步 WEB 静态产物失败"
        return 1
    fi
    if [ ! -s "${target_dist}/index.html" ]; then
        print_error "WEB 静态产物同步后缺少 index.html: ${target_dist}"
        return 1
    fi
    print_info "已同步镜像静态产物: ${image_ref} → ${target_dist}"
}

# 组合 git 提交与 clean 写入的戳，用于 Dockerfile ARG CACHE_BUST（使 COPY 之后层在代码/clean 后重建）
get_web_build_cache_bust() {
    local git_rev stamp
    git_rev=$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null || echo "nogit")
    stamp=""
    if [ -f "$(web_build_stamp_file "$EASYAIOT_ROOT")" ]; then
        stamp=$(tr -d '\n' < "$(web_build_stamp_file "$EASYAIOT_ROOT")")
    fi
    echo "${git_rev}-${stamp}"
}

# 执行 docker build（BuildKit + 宿主机 .build-cache/web/pnpm-store 本地 cache 后端）
docker_build_image() {
    init_easyaiot_build_cache_dirs "$EASYAIOT_ROOT"
    enable_docker_buildkit
    mkdir -p "${SCRIPT_DIR}/docker-build-logs"
    local ts log_new pnpm_log ec cache_bust
    ts=$(date +%Y%m%d-%H%M%S)
    log_new="${SCRIPT_DIR}/docker-build-logs/docker-build-${ts}.log"
    pnpm_log="${SCRIPT_DIR}/docker-build-logs/pnpm-build.log"
    cache_bust=$(get_web_build_cache_bust)
    ensure_deploy_profile
    local deploy_profile tenant_enable captcha_enable edge_standalone
    deploy_profile="$(frontend_deploy_profile)"
    if is_edge_deploy_profile; then
        tenant_enable=false
        captcha_enable=false
        edge_standalone=true
    else
        tenant_enable=true
        captcha_enable=true
        edge_standalone=false
    fi
    {
        echo ""
        echo "======== docker build 开始 ${ts} CACHE_BUST=${cache_bust} DEPLOY_PROFILE=${deploy_profile} TENANT=${tenant_enable} CAPTCHA=${captcha_enable} ========"
    } >> "$pnpm_log"
    print_info "本次构建独立日志: docker-build-logs/docker-build-${ts}.log；历史追加: docker-build-logs/pnpm-build.log"
    print_info "构建缓存标识 CACHE_BUST=${cache_bust}（clean 或代码变更后将重新 pnpm install/build）"
    print_info "部署形态 VITE_GLOB_DEPLOY_PROFILE=${deploy_profile}"
    if is_edge_deploy_profile; then
        print_info "edge 登录：关闭租户与滑块验证码（VITE_GLOB_APP_TENANT/CAPTCHA_ENABLE=false）"
    fi
    set -o pipefail
    local pnpm_store
    pnpm_store="$(pnpm_store_dir "$EASYAIOT_ROOT")"
    mkdir -p "${pnpm_store}"
    # 构建层缓存策略：
    # 默认依赖 Docker 守护进程自身的层缓存——稳定运行的服务器上，pnpm fetch/install 等重层会持续命中
    # （CACHED），无需每次再做 type=local 全量导出。实测 --cache-to mode=max 每次额外耗时数分钟
    # （日志 #27 exporting cache，仅 preparing 就 ~245s），且 CACHE_BUST 之后的层下次也用不上，纯浪费。
    # 易失/CI 环境（构建后守护进程缓存会被清理、或换机器）可设 WEB_PERSIST_BUILD_CACHE=1 重新启用持久化。
    local cache_from_to=()
    if [ "${WEB_PERSIST_BUILD_CACHE:-0}" = "1" ]; then
        if [ -d "${pnpm_store}" ] && [ "$(find "${pnpm_store}" -mindepth 1 -print -quit 2>/dev/null)" ]; then
            cache_from_to+=(--cache-from "type=local,src=${pnpm_store}")
        fi
        cache_from_to+=(--cache-to "type=local,dest=${pnpm_store},mode=max")
        print_info "持久化构建缓存到 ${pnpm_store}（WEB_PERSIST_BUILD_CACHE=1，会增加每次构建的导出耗时）"
    else
        print_info "使用 Docker 守护进程层缓存（默认）；如需跨守护进程清理/换机器持久化：WEB_PERSIST_BUILD_CACHE=1"
    fi
    local platform_opts=""
    if [ -n "${DOCKER_PLATFORM:-}" ]; then
        platform_opts="--platform $DOCKER_PLATFORM"
        print_info "构建目标平台: ${DOCKER_PLATFORM}"
    fi
    docker build \
        "${cache_from_to[@]}" \
        --build-arg "CACHE_BUST=${cache_bust}" \
        --build-arg "VITE_GLOB_DEPLOY_PROFILE=${deploy_profile}" \
        --build-arg "VITE_GLOB_APP_TENANT_ENABLE=${tenant_enable}" \
        --build-arg "VITE_GLOB_APP_CAPTCHA_ENABLE=${captcha_enable}" \
        --build-arg "VITE_GLOB_EDGE_STANDALONE=${edge_standalone}" \
        --build-arg "SKIP_VITE_BUILD=${SKIP_VITE_BUILD:-0}" \
        --build-arg NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmmirror.com/}" \
        --build-arg APK_MIRROR="${APK_MIRROR:-mirrors.tuna.tsinghua.edu.cn}" \
        $platform_opts \
        "$@" 2>&1 | tee "$log_new" | tee -a "$pnpm_log"
    ec=$?
    set +o pipefail
    {
        echo "======== docker build 结束 ${ts} 退出码: ${ec} ========"
        echo ""
    } >> "$pnpm_log"
    if [ $ec -ne 0 ]; then
        print_error "Docker 构建失败，请检查日志: ${log_new}"
    fi
    return $ec
}

# 获取占用端口的进程PID
get_port_pids() {
    local port=$1
    local pids=()
    
    if command -v lsof &> /dev/null; then
        # 使用lsof获取PID，排除标题行，提取唯一的PID
        while IFS= read -r line; do
            pid=$(echo "$line" | awk '{print $2}')
            # 跳过非数字的PID（如标题行）
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(lsof -i :"$port" 2>/dev/null | tail -n +2)
    elif command -v fuser &> /dev/null; then
        # 使用fuser获取PID
        pids=($(fuser "$port/tcp" 2>/dev/null | tr -d ' '))
    fi
    
    # 去重
    if [ ${#pids[@]} -gt 0 ]; then
        printf '%s\n' "${pids[@]}" | sort -u
    fi
}

# 处理端口占用
handle_port_conflict() {
    local port=$1
    local pids=()
    
    print_warning "端口 $port 已被占用"
    print_info "占用端口的进程信息:"
    
    # 显示进程信息并收集PID
    if command -v lsof &> /dev/null; then
        lsof -i :"$port" | head -10
        while IFS= read -r pid; do
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(lsof -i :"$port" 2>/dev/null | tail -n +2 | awk '{print $2}' | sort -u)
    elif command -v netstat &> /dev/null; then
        netstat -tulnp 2>/dev/null | grep ":$port " | head -5
        # netstat需要root权限才能显示PID，尝试提取
        while IFS= read -r line; do
            pid=$(echo "$line" | awk '{print $7}' | cut -d'/' -f1)
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(netstat -tulnp 2>/dev/null | grep ":$port ")
    elif command -v ss &> /dev/null; then
        ss -tulnp 2>/dev/null | grep ":$port " | head -5
        # ss需要root权限才能显示PID
        while IFS= read -r line; do
            pid=$(echo "$line" | grep -oP 'pid=\K[0-9]+' || echo "")
            if [[ "$pid" =~ ^[0-9]+$ ]]; then
                pids+=("$pid")
            fi
        done < <(ss -tulnp 2>/dev/null | grep ":$port ")
    fi
    
    # 去重PID数组
    if [ ${#pids[@]} -gt 0 ]; then
        local unique_pids=($(printf '%s\n' "${pids[@]}" | sort -u))
        pids=("${unique_pids[@]}")
    fi
    
    # 如果没有获取到PID，提示用户手动处理
    if [ ${#pids[@]} -eq 0 ]; then
        print_warning "无法自动获取占用端口的进程PID（可能需要root权限）"
        print_info "请手动停止占用端口的进程，或修改 .env 文件中的 WEB_PORT 配置"
        return 1
    fi
    
    echo ""
    print_info "检测到以下进程占用端口: ${pids[*]}"
    echo ""
    print_info "请选择处理方式:"
    echo "  1) 自动 - 自动kill占用端口的进程"
    echo "  2) 手动 - 手动处理（脚本退出）"
    echo "  3) 停止 - 停止脚本执行"
    echo ""
    print_info "请输入选项 (1/2/3，默认: 2): "
    read -r choice
    
    case "${choice:-2}" in
        1)
            print_info "正在kill占用端口的进程..."
            local killed_count=0
            local failed_count=0
            
            for pid in "${pids[@]}"; do
                # 检查进程是否存在
                if kill -0 "$pid" 2>/dev/null; then
                    # 先尝试优雅终止
                    if kill "$pid" 2>/dev/null; then
                        print_info "已发送终止信号到进程 $pid"
                        killed_count=$((killed_count + 1))
                        # 等待2秒
                        sleep 2
                        # 如果进程还在，强制kill
                        if kill -0 "$pid" 2>/dev/null; then
                            print_warning "进程 $pid 未响应，强制kill..."
                            if kill -9 "$pid" 2>/dev/null; then
                                print_success "已强制kill进程 $pid"
                            else
                                print_error "无法kill进程 $pid（可能需要root权限）"
                                failed_count=$((failed_count + 1))
                            fi
                        else
                            print_success "进程 $pid 已终止"
                        fi
                    else
                        print_error "无法kill进程 $pid（可能需要root权限）"
                        failed_count=$((failed_count + 1))
                    fi
                else
                    print_info "进程 $pid 已不存在"
                fi
            done
            
            # 等待一下，让端口释放
            sleep 1
            
            # 再次检查端口是否释放
            if command -v lsof &> /dev/null; then
                if ! lsof -i :"$port" &> /dev/null; then
                    print_success "端口 $port 已释放"
                    return 0
                fi
            elif command -v netstat &> /dev/null; then
                if ! netstat -tuln 2>/dev/null | grep -q ":$port "; then
                    print_success "端口 $port 已释放"
                    return 0
                fi
            elif command -v ss &> /dev/null; then
                if ! ss -tuln 2>/dev/null | grep -q ":$port "; then
                    print_success "端口 $port 已释放"
                    return 0
                fi
            fi
            
            if [ $failed_count -gt 0 ]; then
                print_error "部分进程kill失败，端口可能仍被占用"
                print_info "请手动处理或修改 .env 文件中的 WEB_PORT 配置"
                return 1
            else
                print_warning "端口可能仍被占用，请稍后重试或手动检查"
                return 1
            fi
            ;;
        2)
            print_info "请手动停止占用端口的进程，或修改 .env 文件中的 WEB_PORT 配置"
            print_info "占用端口的进程PID: ${pids[*]}"
            print_info "可以使用以下命令kill进程: kill -9 ${pids[*]}"
            return 1
            ;;
        3)
            print_info "已取消操作"
            exit 0
            ;;
        *)
            print_error "无效选项，已取消操作"
            return 1
            ;;
    esac
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if [ -z "$port" ]; then
        # 从.env文件读取端口，如果没有则使用默认值8888
        if [ -f .env ]; then
            port=$(grep "^WEB_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' | tr -d '"' | tr -d "'")
        fi
        port=${port:-8888}
    fi

    _web_port_in_use() {
        local p="$1"
        if command -v lsof &> /dev/null; then
            lsof -i :"$p" &> /dev/null && return 0
        elif command -v netstat &> /dev/null; then
            netstat -tuln 2>/dev/null | grep -q ":$p " && return 0
        elif command -v ss &> /dev/null; then
            ss -tuln 2>/dev/null | grep -q ":$p " && return 0
        fi
        return 1
    }

    if _web_port_in_use "$port"; then
        handle_port_conflict "$port"
        return $?
    fi

    return 0
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p conf
    mkdir -p logs
    mkdir -p conf/ssl
    mkdir -p dist
    print_success "目录创建完成"
}

# HTTPS + HTTP/2 自签证书（所有部署形态共用；对齐 IDEA pnpm dev:http2）
ensure_ssl_certs() {
    local crt="conf/ssl/server.crt"
    local key="conf/ssl/server.key"
    mkdir -p conf/ssl
    if [ -f "$crt" ] && [ -f "$key" ]; then
        print_info "SSL 证书已存在: $crt"
        return 0
    fi
    print_info "生成 nginx HTTPS 自签证书（大屏/分屏多路拉流需要 HTTP/2）..."
    if command -v node >/dev/null 2>&1 && [ -f scripts/gen-dev-certs.mjs ]; then
        if node scripts/gen-dev-certs.mjs; then
            print_success "已通过 scripts/gen-dev-certs.mjs 生成证书"
            return 0
        fi
    fi
    if ! command -v openssl >/dev/null 2>&1; then
        print_error "未找到 openssl，无法生成 SSL 证书"
        print_info "请安装 openssl 后重试，或手动放入 conf/ssl/server.crt 与 conf/ssl/server.key"
        return 1
    fi
    local tmpcnf
    tmpcnf="$(mktemp)"
    cat >"$tmpcnf" <<'EOF'
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
CN = localhost

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
    if openssl req -x509 -nodes -newkey rsa:2048 \
        -keyout "$key" -out "$crt" -days 825 \
        -config "$tmpcnf" -extensions v3_req >/dev/null 2>&1; then
        rm -f "$tmpcnf"
        chmod 644 "$crt"
        chmod 600 "$key"
        print_success "已生成自签证书: $crt / $key"
        return 0
    fi
    rm -f "$tmpcnf"
    print_error "openssl 生成证书失败"
    return 1
}

# 检查前端构建产物（已废弃，构建现在在容器内完成）
check_dist() {
    # 构建现在在Docker容器内完成，不再需要检查宿主机的dist目录
    return 0
}

# 按部署形态写入 WEB compose 使用的 nginx 配置路径
ensure_nginx_conf_for_profile() {
    ensure_deploy_profile
    local conf="./conf/nginx.conf"
    if is_edge_deploy_profile; then
        conf="./conf/nginx.edge.conf"
    elif is_mini_deploy_profile; then
        conf="./conf/nginx.mini.conf"
    fi
    export NGINX_CONF="$conf"
    if [ -f .env ]; then
        if grep -q '^NGINX_CONF=' .env 2>/dev/null; then
            sed -i "s|^NGINX_CONF=.*|NGINX_CONF=${conf}|" .env
        else
            echo "NGINX_CONF=${conf}" >> .env
        fi
    fi
    print_info "nginx 配置: ${conf} (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
}

# 创建 .env 文件
create_env_file() {
    if [ ! -f .env ]; then
        print_info ".env 文件不存在，正在创建..."
        if [ -f env.example ]; then
            cp env.example .env
            print_success ".env 文件已从 env.example 创建"
            print_warning "请编辑 .env 文件，配置端口等参数"
        else
            print_error "env.example 文件不存在，无法创建 .env 文件"
            exit 1
        fi
    else
        print_info ".env 文件已存在"
    fi
}

# 检查并切换 npm 源为国内源
check_and_switch_npm_registry() {
    if ! check_command npm; then
        return 0  # npm 不存在，跳过检查
    fi
    
    # 获取当前 npm 源
    CURRENT_REGISTRY=$(npm config get registry 2>/dev/null || echo "")
    
    # 国内源列表（支持新旧地址）
    DOMESTIC_REGISTRIES=(
        "https://registry.npmmirror.com"
        "https://registry.npm.taobao.org"
    )
    
    # 检查是否为国内源
    IS_DOMESTIC=false
    for registry in "${DOMESTIC_REGISTRIES[@]}"; do
        if [ "$CURRENT_REGISTRY" = "$registry" ] || [ "$CURRENT_REGISTRY" = "$registry/" ]; then
            IS_DOMESTIC=true
            break
        fi
    done
    
    # 如果不是国内源，切换为国内源
    if [ "$IS_DOMESTIC" = false ]; then
        print_warning "当前 npm 源: $CURRENT_REGISTRY"
        print_info "检测到非国内源，是否切换为国内源（淘宝镜像）？(Y/n)"
        read -r response
        if [[ ! "$response" =~ ^([nN][oO]|[nN])$ ]]; then
            print_info "正在切换 npm 源为国内源..."
            if npm config set registry https://registry.npmmirror.com; then
                print_success "npm 源已切换为: https://registry.npmmirror.com"
            else
                print_error "npm 源切换失败"
                return 1
            fi
        else
            print_info "保持当前 npm 源: $CURRENT_REGISTRY"
        fi
    else
        print_info "当前 npm 源已是国内源: $CURRENT_REGISTRY"
    fi
    
    return 0
}

# 安装 pnpm
install_pnpm() {
    print_info "正在安装 pnpm..."
    
    # 检查是否有 npm
    if ! check_command npm; then
        print_error "npm 未安装，无法安装 pnpm，请先安装 Node.js"
        exit 1
    fi
    
    # 使用 npm 全局安装 pnpm
    if npm install -g pnpm; then
        print_success "pnpm 安装成功: $(pnpm --version)"
        return 0
    else
        print_error "pnpm 安装失败"
        return 1
    fi
}

# 构建前端项目（在宿主机上，可选，主要用于测试）
build_frontend() {
    print_warning "注意：前端构建现在在Docker容器内自动完成"
    print_info "此命令仅用于在宿主机上测试构建，不影响Docker部署"
    print_info "开始构建前端项目..."
    
    # 检查 Node.js
    if ! check_command node; then
        print_error "Node.js 未安装，请先安装 Node.js"
        echo "安装指南: https://nodejs.org/"
        exit 1
    fi
    
    # 检查并切换 npm 源为国内源
    check_and_switch_npm_registry
    
    # 检查 pnpm
    if ! check_command pnpm; then
        print_warning "pnpm 未安装"
        print_info "是否自动安装 pnpm？(y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            if install_pnpm; then
                PACKAGE_MANAGER="pnpm"
            else
                print_warning "pnpm 安装失败，尝试使用 npm..."
                if ! check_command npm; then
                    print_error "npm 未安装，请先安装 Node.js"
                    exit 1
                fi
                PACKAGE_MANAGER="npm"
            fi
        else
            print_info "跳过 pnpm 安装，尝试使用 npm..."
            if ! check_command npm; then
                print_error "npm 未安装，请先安装 Node.js"
                exit 1
            fi
            PACKAGE_MANAGER="npm"
        fi
    else
        PACKAGE_MANAGER="pnpm"
    fi
    
    print_info "使用包管理器: $PACKAGE_MANAGER"
    
    # 安装依赖
    if [ ! -d "node_modules" ]; then
        print_info "安装依赖..."
        $PACKAGE_MANAGER install
    fi
    
    # 构建项目
    print_info "构建前端项目..."
    if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
        pnpm build
    else
        npm run build
    fi
    
    print_success "前端项目构建完成（此构建仅用于测试，Docker部署时会重新构建）"
}

# 验证上游后端服务是否可达（gateway/system-host）
verify_upstream_connectivity() {
    local container_name="web-service"
    # 等待容器完全启动
    local attempt=0
    while [ $attempt -lt 10 ]; do
        if docker exec "$container_name" wget -q --spider http://127.0.0.1/health 2>/dev/null; then
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    # 检查上游可达性（edge→VIDEO；mini→iot-system；其余→gateway）
    local upstream_host upstream_port upstream_label
    if is_edge_deploy_profile; then
        upstream_host="video-host"
        upstream_port="6000"
        upstream_label="VIDEO(6000)"
    elif is_mini_deploy_profile; then
        upstream_host="system-host"
        upstream_port="48099"
        upstream_label="iot-system(48099)"
    else
        upstream_host="gateway"
        upstream_port="48080"
        upstream_label="iot-gateway(48080)"
    fi

    print_info "验证后端服务连通性 (${upstream_label})..."
    if docker exec "$container_name" wget -q --timeout=3 --tries=1 --spider "http://${upstream_host}:${upstream_port}/" 2>/dev/null; then
        print_success "后端服务 ${upstream_label} 连通正常"
    elif docker exec "$container_name" wget -q --timeout=3 --tries=1 --spider "http://${upstream_host}:${upstream_port}/actuator/health" 2>/dev/null; then
        print_success "后端服务 ${upstream_label} 连通正常"
    else
        print_warning "后端服务 ${upstream_label} 不可达，API 请求将返回 502"
        if is_edge_deploy_profile; then
            print_warning "请确保 VIDEO 模块已成功安装并启动"
            print_info "检查 video-service: docker ps | grep video-service"
        elif is_mini_deploy_profile; then
            print_warning "请确保 DEVICE 模块已成功安装并启动"
            print_info "检查 iot-system 是否在运行: docker ps | grep iot-system"
            print_info "检查端口 48099 是否监听: ss -tlnp | grep 48099"
        else
            print_warning "请确保 DEVICE 模块已成功安装并启动"
            print_info "检查 iot-gateway 是否在运行: docker ps | grep iot-gateway"
            print_info "检查端口 48080 是否监听: ss -tlnp | grep 48080"
        fi
        print_info "待后端就绪后重启 web 服务: ./install_linux.sh restart"
    fi
}

# 安装服务
install_service() {
    print_info "开始安装 WEB 服务..."

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
    create_directories
    create_env_file
    ensure_nginx_conf_for_profile
    ensure_ssl_certs || exit 1
    
    # 先清理本服务的残留容器
    print_info "检查并清理残留容器..."
    docker rm -f web-service 2>/dev/null || true
    $COMPOSE_CMD down --remove-orphans 2>/dev/null || true

    # 检查端口占用
    if ! check_port; then
        print_error "端口检查失败，请解决端口占用问题后重试"
        exit 1
    fi

    if web_skip_build_from_pull; then
        :
    elif [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] && docker image inspect web-service:latest >/dev/null 2>&1 && web_image_profile_matches; then
        print_success "镜像已从远程拉取 (web-service:latest)，跳过 Docker 构建与 vite 编译"
    else
        print_info "前端构建将在 Docker 容器内自动完成"
        print_info "构建 Docker 镜像（根据代码重新构建）..."
        docker_build_image -t web-service:latest .
        record_web_deploy_profile_built "${EASYAIOT_ROOT}"
    fi
    
    sync_web_dist_from_image
    print_info "启动服务..."
    $COMPOSE_CMD up -d
    
    print_success "服务安装完成！"
    print_info "等待服务启动..."
    sleep 3
    
    # 检查服务状态
    check_status
    
    # 验证上游连通性
    verify_upstream_connectivity
    
    # 读取端口配置
    if [ -f .env ]; then
        WEB_PORT=$(grep "^WEB_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' | tr -d '"' | tr -d "'")
    fi
    WEB_PORT=${WEB_PORT:-8888}
    print_info "服务访问地址: https://localhost:${WEB_PORT}  （仅 HTTPS+HTTP/2，首次需信任自签证书）"
    print_info "健康检查: https://localhost:${WEB_PORT}/health"
    print_info "查看日志: ./install_linux.sh logs"
}

# 启动服务
start_service() {
    print_info "启动服务..."
    check_docker
    check_docker_compose
    
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在，正在创建..."
        create_env_file
    fi
    ensure_nginx_conf_for_profile
    ensure_ssl_certs || exit 1
    
    # 先清改名孤儿
    cleanup_renamed_containers

    # 检查端口占用
    if ! check_port; then
        print_error "端口检查失败，请解决端口占用问题后重试"
        exit 1
    fi

    sync_web_dist_from_image
    $COMPOSE_CMD up -d --remove-orphans
    print_success "服务已启动"
    check_status
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD down
    print_success "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    check_docker
    check_docker_compose
    ensure_nginx_conf_for_profile
    ensure_ssl_certs || exit 1
    
    sync_web_dist_from_image
    $COMPOSE_CMD up -d --force-recreate --remove-orphans
    print_success "服务已重启"
    check_status
}

# 查看服务状态
check_status() {
    print_info "服务状态:"
    check_docker
    check_docker_compose
    
    $COMPOSE_CMD ps
    
    echo ""
    print_info "容器健康状态:"
    if docker ps --filter "name=web-service" --format "table {{.Names}}\t{{.Status}}" | grep -q web-service; then
        docker ps --filter "name=web-service" --format "table {{.Names}}\t{{.Status}}"
        
        # 检查健康检查
        HEALTH=$(docker inspect --format='{{.State.Health.Status}}' web-service 2>/dev/null || echo "N/A")
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

    local profile_ref
    profile_ref=$(web_profile_image_ref)

    # runtime_image.sh 按形态推送 web-service:latest-{mini|standard}；须检查形态标签而非仅 latest
    if [ "${FORCE_REBUILD:-0}" != "1" ] \
        && docker image inspect "$profile_ref" >/dev/null 2>&1 \
        && web_image_profile_matches; then
        print_success "${profile_ref} 已存在，跳过 Docker 构建（强制重建请设置 FORCE_REBUILD=1）"
        web_tag_compose_image || true
        return 0
    fi

    print_info "重新构建 Docker 镜像..."
    # 注意：前端构建现在在Docker容器内完成，构建镜像时会自动完成
    print_info "前端构建将在Docker容器内自动完成"
    
    # 勿用 --no-cache：会强制重跑 pnpm fetch/install（数分钟）。
    # pnpm 11 偶发 Done 后不退出（#12297），Dockerfile 已监督收尾；仍应尽量命中层缓存。
    # 源码变更由 CACHE_BUST 触发 vite 重编；全量重建请先 clean。
    local build_rc=0
    docker_build_image -t "$profile_ref" . || build_rc=$?
    record_web_deploy_profile_built "${EASYAIOT_ROOT}"
    web_tag_compose_image || true
    if [ $build_rc -eq 0 ]; then
        print_success "镜像构建完成: ${profile_ref}"
    else
        print_error "镜像构建失败 (exit=${build_rc})"
    fi
    return $build_rc
}

# 清理服务
clean_service() {
    check_docker
    check_docker_compose
    
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

    print_info "停止并删除容器..."
        $COMPOSE_CMD down -v --remove-orphans
        
        # 强制删除容器（即使已停止）
        print_info "强制删除残留容器..."
        docker rm -f web-service 2>/dev/null || true
        
        print_info "删除镜像..."
        docker rmi web-service:latest 2>/dev/null || true
        
        # 清理 dist 文件夹
        print_info "清理 dist 文件夹..."
        local dist_path="${SCRIPT_DIR}/dist"
        if [ -d "$dist_path" ]; then
            rm -rf "$dist_path"
            print_success "已清理 dist 文件夹: $dist_path"
        else
            print_info "dist 文件夹不存在，跳过清理"
        fi

        # 使下次 install/build 失效 Docker 层缓存（否则 pnpm install/build 会全部 CACHED）
        init_easyaiot_build_cache_dirs "$EASYAIOT_ROOT"
        date +%s > "$(web_build_stamp_file "$EASYAIOT_ROOT")"
        print_info "已更新 .build-cache/web/.build-stamp，下次构建将重新编译前端（.build-cache/web/pnpm-store 依赖缓存保留）"
        
    print_success "清理完成"
}

# 更新服务
# 性能优化要点（命令接口/功能保持不变）：
#   1. 前端是编译型产物（容器内 pnpm build → 静态 dist 由 nginx 提供），代码变更必须
#      重新编译，无法像 AI/VIDEO 那样卷挂载源码免构建。
#   2. 但「代码无变更」时（git pull 显示 Already up to date 的常见场景）可整段跳过构建，
#      省掉 Vite 打包（Dockerfile 标注约 2–10 分钟）。可用 FORCE_REBUILD=1 强制重建。
#   3. 需要构建时仍复用 .build-cache/web/pnpm-store 依赖缓存（docker_build_image 已内置），
#      pnpm fetch/install 走缓存，仅 Vite 编译重跑；且构建期旧容器持续运行，停机最小化。
update_service() {
    print_info "更新服务..."
    check_docker
    check_docker_compose

    # 拉取预构建：跳过 git / 构建，仅 recreate（需部署形态匹配）
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ] \
        && docker image inspect web-service:latest >/dev/null 2>&1 \
        && web_image_profile_matches; then
        print_success "预构建镜像已就绪（EASYAIOT_SKIP_BUILD=1），跳过 git pull 与前端重建，仅 recreate"
        cleanup_renamed_containers
        sync_web_dist_from_image
        $COMPOSE_CMD up -d --remove-orphans
        check_status
        return 0
    fi
    # 安装包常见：无 git，有本地镜像 → 仅 recreate（不调用 git；不校验形态以免误阻塞）
    if ! easyaiot_have_git && docker image inspect web-service:latest >/dev/null 2>&1; then
        print_warning "未检测到 git 命令，跳过代码拉取，使用本地镜像 recreate"
        print_info "如需最新版本：一键 update 选「拉取预构建镜像」，或安装 git 后本地重建"
        cleanup_renamed_containers
        sync_web_dist_from_image
        $COMPOSE_CMD up -d --remove-orphans
        check_status
        return 0
    fi

    # 记录更新前代码版本，用于判断是否需要重建
    local rev_before=""
    rev_before="$(easyaiot_git_rev_parse_head)"

    print_info "拉取最新代码..."
    # --ff-only：快进失败立即返回，不产生意外合并提交，比默认 pull 更快更安全
    # 无 git 时 helper 会跳过 pull（随后基于当前目录构建）
    easyaiot_git_pull_ff_only

    local rev_after=""
    rev_after="$(easyaiot_git_rev_parse_head)"

    # 无变更快速路径：提交号未变 + 本地无未提交改动 + 镜像已存在 + 部署形态未变 → 跳过前端重建
    # 说明1：clean 会删除镜像并刷新构建戳，故 clean 后镜像不存在 → 此处不会误跳过
    # 说明2：git diff --quiet HEAD 捕获「已跟踪文件的本地未提交修改」，避免改了代码没 commit
    #        却被误判为无变更而跳过重建（git diff 不受未跟踪的构建日志干扰）。
    #        注意：全新的未跟踪文件 git diff 检测不到，这种情况请先 git add，或用 FORCE_REBUILD=1。
    # 说明3：部署形态（mini/standard/full）变更时，即使代码无变更也必须重建以写入正确的 VITE_GLOB_DEPLOY_PROFILE
    # 说明4：无 git 且无镜像时无法 recreate，会落到下方构建路径
    if [ "${FORCE_REBUILD:-0}" != "1" ] \
        && docker image inspect web-service:latest >/dev/null 2>&1 \
        && web_image_profile_matches \
        && [ -n "$rev_before" ] && [ "$rev_before" = "$rev_after" ] \
        && easyaiot_git_worktree_clean; then
        print_success "代码无变更且镜像已存在，跳过前端重建"
        print_info "（如需强制重建：FORCE_REBUILD=1 ./install_linux.sh update）"
        cleanup_renamed_containers
        sync_web_dist_from_image
        $COMPOSE_CMD up -d --remove-orphans
        check_status
        return 0
    fi

    # 注意：前端构建现在在Docker容器内完成，重新构建镜像时会自动完成
    print_info "重新构建镜像（前端构建将在容器内自动完成，复用 pnpm-store 依赖缓存）..."
    docker_build_image -t web-service:latest .
    record_web_deploy_profile_built "${EASYAIOT_ROOT}"

    # 构建完成后才 up -d（旧容器在 build 全程持续运行），停机仅数秒
    print_info "应用新镜像..."
    cleanup_renamed_containers
    sync_web_dist_from_image
    $COMPOSE_CMD up -d --remove-orphans

    print_success "服务更新完成"
    check_status
}

# 显示帮助信息
show_help() {
    echo "WEB服务 Docker Compose 管理脚本"
    echo ""
    echo "使用方法:"
    echo "  ./install_linux.sh [命令]"
    echo ""
    echo "可用命令:"
    echo "  install         - 安装并启动服务（首次运行）"
    echo "  start           - 启动服务"
    echo "  stop            - 停止服务"
    echo "  restart         - 重启服务"
    echo "  status          - 查看服务状态"
    echo "  logs            - 查看服务日志"
    echo "  logs -f         - 实时查看服务日志"
    echo "  build           - 重新构建镜像（前端构建在容器内自动完成）"
    echo "  build-frontend  - 在宿主机上构建前端项目（可选，用于测试）"
    echo "  clean           - 清理容器和镜像"
    echo "  update          - 更新并重启服务"
    echo ""
    echo "说明: install/build/update 执行 docker build 时完整输出写入 docker-build-logs/，pnpm-build.log 为追加，并带时间戳文件"
    echo "  help            - 显示此帮助信息"
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
        build-frontend)
            build_frontend
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
