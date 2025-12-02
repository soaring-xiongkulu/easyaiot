#!/bin/bash

# DEVICE模块 Docker Compose 管理脚本
# 用于管理DEVICE目录下的所有Docker服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# 检查docker-compose是否存在
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: 未找到docker或docker-compose命令${NC}"
    exit 1
fi

# 使用docker compose（新版本）或docker-compose（旧版本）
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}错误: 未找到docker compose或docker-compose命令${NC}"
    exit 1
fi

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

# 检查并修复文件权限
fix_file_permissions() {
    local file_path="$1"
    local min_perms="$2"
    
    if [ ! -e "$file_path" ]; then
        return 1
    fi
    
    # 获取当前权限
    local current_perms=$(stat -c "%a" "$file_path" 2>/dev/null || echo "000")
    
    # 检查权限是否足够
    if [ "$current_perms" -lt "$min_perms" ] 2>/dev/null; then
        print_info "修复文件权限: $file_path (当前: $current_perms, 需要: $min_perms)"
        if [ "$EUID" -eq 0 ]; then
            chmod "$min_perms" "$file_path" 2>/dev/null || return 1
        elif command -v sudo &> /dev/null; then
            sudo chmod "$min_perms" "$file_path" 2>/dev/null || return 1
        else
            print_warning "无法修复权限，请手动执行: chmod $min_perms $file_path"
            return 1
        fi
    fi
    
    return 0
}

# 检查并修复目录权限
fix_directory_permissions() {
    local dir_path="$1"
    local min_perms="$2"
    
    if [ ! -d "$dir_path" ]; then
        return 1
    fi
    
    # 获取当前权限
    local current_perms=$(stat -c "%a" "$dir_path" 2>/dev/null || echo "000")
    
    # 检查权限是否足够
    if [ "$current_perms" -lt "$min_perms" ] 2>/dev/null; then
        print_info "修复目录权限: $dir_path (当前: $current_perms, 需要: $min_perms)"
        if [ "$EUID" -eq 0 ]; then
            chmod "$min_perms" "$dir_path" 2>/dev/null || return 1
        elif command -v sudo &> /dev/null; then
            sudo chmod "$min_perms" "$dir_path" 2>/dev/null || return 1
        else
            print_warning "无法修复权限，请手动执行: chmod $min_perms $dir_path"
            return 1
        fi
    fi
    
    return 0
}

# 诊断 Docker Compose 配置问题
diagnose_compose_issue() {
    local compose_file="$1"
    
    print_info "开始诊断 Docker Compose 配置问题..."
    echo
    
    # 1. 检查文件是否存在
    print_info "1. 检查文件存在性..."
    if [ ! -f "$compose_file" ]; then
        print_error "文件不存在: $compose_file"
        return 1
    fi
    print_success "文件存在"
    echo
    
    # 2. 检查文件权限
    print_info "2. 检查文件权限..."
    local file_perms=$(stat -c "%a" "$compose_file" 2>/dev/null || echo "未知")
    local file_owner=$(stat -c "%U:%G" "$compose_file" 2>/dev/null || echo "未知")
    print_info "   权限: $file_perms"
    print_info "   所有者: $file_owner"
    
    # 3. 检查文件系统挂载选项
    print_info "3. 检查文件系统挂载选项..."
    local mount_info=$(df -h "$compose_file" 2>/dev/null | tail -1)
    print_info "   挂载信息: $mount_info"
    local mount_point=$(echo "$mount_info" | awk '{print $NF}')
    local mount_opts=$(mount | grep -E "^[^ ]+ on $mount_point " | head -1 | grep -oE "\([^)]+\)" | tr -d '()' || echo "未知")
    print_info "   挂载选项: $mount_opts"
    
    # 检查是否有 noexec 或 nosuid
    if echo "$mount_opts" | grep -q "noexec"; then
        print_warning "   警告: 文件系统挂载了 noexec 选项，可能影响执行"
    fi
    if echo "$mount_opts" | grep -q "nosuid"; then
        print_warning "   警告: 文件系统挂载了 nosuid 选项"
    fi
    echo
    
    # 4. 检查 SELinux 状态（如果存在）
    print_info "4. 检查 SELinux 状态..."
    if command -v getenforce &> /dev/null; then
        local selinux_status=$(getenforce 2>/dev/null || echo "未知")
        print_info "   SELinux 状态: $selinux_status"
        if [ "$selinux_status" != "Disabled" ]; then
            local selinux_context=$(ls -Z "$compose_file" 2>/dev/null | awk '{print $NF}' || echo "未知")
            print_info "   SELinux 上下文: $selinux_context"
        fi
    else
        print_info "   SELinux 未安装或不可用"
    fi
    echo
    
    # 5. 检查 Docker 用户组
    print_info "5. 检查 Docker 用户组..."
    if getent group docker > /dev/null 2>&1; then
        local docker_gid=$(getent group docker | cut -d: -f3)
        print_info "   Docker 组 GID: $docker_gid"
        if [ "$EUID" -eq 0 ]; then
            print_info "   当前用户: root (UID 0)"
        else
            local current_groups=$(id -Gn)
            if echo "$current_groups" | grep -q "docker"; then
                print_success "   当前用户在 docker 组中"
            else
                print_warning "   当前用户不在 docker 组中"
            fi
        fi
    else
        print_warning "   Docker 组不存在"
    fi
    echo
    
    # 6. 尝试直接读取文件
    print_info "6. 测试文件可读性..."
    if [ -r "$compose_file" ]; then
        print_success "   文件可读"
    else
        print_error "   文件不可读"
    fi
    
    # 7. 尝试使用 Docker Compose 验证配置
    print_info "7. 测试 Docker Compose 配置验证..."
    local compose_error
    compose_error=$($DOCKER_COMPOSE -f "$compose_file" config 2>&1)
    local compose_exit_code=$?
    
    if [ $compose_exit_code -eq 0 ]; then
        print_success "   Docker Compose 配置验证成功"
        return 0
    else
        print_error "   Docker Compose 配置验证失败"
        print_error "   错误信息:"
        echo "$compose_error" | sed 's/^/   /'
        return 1
    fi
}

# 修复 Docker Compose 配置访问问题
fix_compose_access() {
    local compose_file="$1"
    local script_dir="$2"
    
    print_info "尝试修复 Docker Compose 配置访问问题..."
    
    # 1. 修复文件权限
    if [ "$EUID" -eq 0 ]; then
        chmod 644 "$compose_file" 2>/dev/null || true
        chmod 755 "$script_dir" 2>/dev/null || true
    elif command -v sudo &> /dev/null; then
        sudo chmod 644 "$compose_file" 2>/dev/null || true
        sudo chmod 755 "$script_dir" 2>/dev/null || true
    fi
    
    # 2. 修复 SELinux 上下文（如果启用）
    if command -v getenforce &> /dev/null && [ "$(getenforce 2>/dev/null)" != "Disabled" ]; then
        if command -v chcon &> /dev/null; then
            print_info "修复 SELinux 上下文..."
            if [ "$EUID" -eq 0 ]; then
                chcon -R -t container_file_t "$script_dir" 2>/dev/null || true
            elif command -v sudo &> /dev/null; then
                sudo chcon -R -t container_file_t "$script_dir" 2>/dev/null || true
            fi
        fi
    fi
    
    # 3. 如果文件在 /dev/shm 下，可能需要特殊处理
    if echo "$compose_file" | grep -q "^/dev/shm"; then
        print_warning "检测到文件在 /dev/shm (tmpfs) 中"
        print_info "tmpfs 文件系统可能有特殊限制"
        
        # 尝试将文件所有者改为当前用户（如果是 root，可能需要改为 docker 用户）
        if [ "$EUID" -eq 0 ]; then
            # root 用户，检查是否有 docker 用户
            if id docker > /dev/null 2>&1; then
                print_info "尝试将文件所有者改为 docker 用户..."
                chown docker:docker "$compose_file" 2>/dev/null || true
                chown -R docker:docker "$script_dir" 2>/dev/null || true
            fi
        fi
    fi
    
    # 4. 最后尝试使用更宽松的权限
    if [ "$EUID" -eq 0 ]; then
        chmod 755 "$compose_file" 2>/dev/null || true
        chmod 755 "$script_dir" 2>/dev/null || true
    elif command -v sudo &> /dev/null; then
        sudo chmod 755 "$compose_file" 2>/dev/null || true
        sudo chmod 755 "$script_dir" 2>/dev/null || true
    fi
}

# 检查docker-compose.yml是否存在并修复权限
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml文件不存在: $COMPOSE_FILE"
        exit 1
    fi
    
    # 检查并修复文件权限（至少需要 644，Docker 需要读取）
    if ! fix_file_permissions "$COMPOSE_FILE" "644"; then
        print_warning "无法自动修复 docker-compose.yml 权限，尝试手动修复..."
        # 尝试使用更宽松的权限
        if [ "$EUID" -eq 0 ]; then
            chmod 644 "$COMPOSE_FILE" 2>/dev/null || chmod 755 "$COMPOSE_FILE" 2>/dev/null || true
        elif command -v sudo &> /dev/null; then
            sudo chmod 644 "$COMPOSE_FILE" 2>/dev/null || sudo chmod 755 "$COMPOSE_FILE" 2>/dev/null || true
        fi
    fi
    
    # 检查并修复脚本目录权限（至少需要 755）
    if ! fix_directory_permissions "$SCRIPT_DIR" "755"; then
        print_warning "无法自动修复脚本目录权限，尝试手动修复..."
        if [ "$EUID" -eq 0 ]; then
            chmod 755 "$SCRIPT_DIR" 2>/dev/null || true
        elif command -v sudo &> /dev/null; then
            sudo chmod 755 "$SCRIPT_DIR" 2>/dev/null || true
        fi
    fi
    
    # 验证文件是否可读
    if [ ! -r "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml 文件不可读: $COMPOSE_FILE"
        print_error "当前权限: $(stat -c "%a %U:%G" "$COMPOSE_FILE" 2>/dev/null || echo "未知")"
        print_error "请手动修复权限: chmod 644 $COMPOSE_FILE"
        exit 1
    fi
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# WEB目录路径
WEB_DIR="${SCRIPT_DIR}/../WEB"

# 创建WEB必要的目录
create_web_directories() {
    print_info "创建WEB必要的目录..."
    mkdir -p "${WEB_DIR}/conf"
    mkdir -p "${WEB_DIR}/logs"
    mkdir -p "${WEB_DIR}/conf/ssl"
    mkdir -p "${WEB_DIR}/dist"
    print_success "WEB目录创建完成"
}

# 检查前端构建产物
check_web_dist() {
    if [ ! -d "${WEB_DIR}/dist" ] || [ -z "$(ls -A ${WEB_DIR}/dist 2>/dev/null)" ]; then
        print_warning "WEB/dist 目录不存在或为空，需要先构建前端项目"
        print_info "运行: $0 build-frontend"
        return 1
    fi
    return 0
}

# 构建前端项目
build_frontend() {
    print_info "开始构建前端项目..."
    
    if [ ! -d "$WEB_DIR" ]; then
        print_error "WEB目录不存在: $WEB_DIR"
        exit 1
    fi
    
    cd "$WEB_DIR"
    
    # 检查 Node.js 和 pnpm
    if ! check_command node; then
        print_error "Node.js 未安装，请先安装 Node.js"
        echo "安装指南: https://nodejs.org/"
        exit 1
    fi
    
    if ! check_command pnpm; then
        print_warning "pnpm 未安装，尝试使用 npm..."
        if ! check_command npm; then
            print_error "npm 未安装，请先安装 Node.js"
            exit 1
        fi
        PACKAGE_MANAGER="npm"
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
    
    print_success "前端项目构建完成"
    cd "$SCRIPT_DIR"
}

# 检查并构建Jar包（已废弃，现在在Docker容器中编译）
check_and_build_jars() {
    print_info "跳过宿主机Jar包检查（编译将在Docker容器中完成）..."
    # 不再需要在宿主机上编译，所有编译都在Docker容器中完成
}

# 构建所有镜像
build_images() {
    print_info "开始构建所有Docker镜像（在容器中编译，显示完整日志）..."
    
    # 确保权限正确
    check_compose_file
    
    cd "$SCRIPT_DIR"
    # 使用 --progress=plain 显示完整输出
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    # 直接执行命令并实时输出
    local exit_code
    
    # 执行构建命令（不使用 --progress，兼容所有版本）
    $DOCKER_COMPOSE build
    exit_code=$?
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "镜像构建失败（退出码: $exit_code）"
        exit 1
    fi
    
    print_success "镜像构建完成（所有编译在容器中完成）"
}

# 构建并启动所有服务
build_and_start() {
    print_info "开始构建并启动所有服务（在容器中编译，显示完整日志）..."
    
    # 确保权限正确
    print_info "检查 Docker Compose 配置文件..."
    check_compose_file
    print_success "配置文件检查完成"
    
    print_info "切换到脚本目录: $SCRIPT_DIR"
    if ! cd "$SCRIPT_DIR"; then
        print_error "无法切换到目录: $SCRIPT_DIR"
        exit 1
    fi
    print_success "当前工作目录: $(pwd)"
    
    # 验证 Docker 可以访问 docker-compose.yml
    # 使用 -f 明确指定配置文件路径，确保可靠性
    print_info "验证 Docker Compose 可以读取配置文件..."
    local compose_test_output
    set +e  # 暂时关闭错误退出，以便捕获退出码
    compose_test_output=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" config 2>&1)
    local compose_test_exit=$?
    set -e  # 重新开启错误退出
    
    if [ $compose_test_exit -ne 0 ]; then
        print_error "Docker Compose 无法读取配置文件"
        echo
        
        # 运行详细诊断
        if ! diagnose_compose_issue "$COMPOSE_FILE"; then
            echo
            print_info "尝试自动修复..."
            fix_compose_access "$COMPOSE_FILE" "$SCRIPT_DIR"
            echo
            
            # 再次验证（使用明确指定的文件路径）
            compose_test_output=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" config 2>&1)
            compose_test_exit=$?
            
            if [ $compose_test_exit -ne 0 ]; then
                print_error "自动修复失败，详细错误信息:"
                echo "$compose_test_output" | sed 's/^/  /'
                echo
                print_error "可能的解决方案:"
                
                # 如果文件在 /dev/shm 下，提供特殊建议
                if echo "$COMPOSE_FILE" | grep -q "^/dev/shm"; then
                    print_warning "检测到项目在 /dev/shm (tmpfs) 中，这可能导致权限问题"
                    print_error "建议解决方案:"
                    print_error "  方案1（推荐）: 将项目移动到其他位置"
                    print_error "    sudo mv /dev/shm/easyaiot /opt/easyaiot"
                    print_error "    cd /opt/easyaiot/DEVICE && ./install_linux.sh install"
                    print_error ""
                    print_error "  方案2: 检查 /dev/shm 挂载选项"
                    print_error "    mount | grep /dev/shm"
                    print_error "    如果看到 noexec 或 nosuid，可能需要重新挂载"
                    print_error ""
                fi
                
                print_error "  方案3: 检查 SELinux 上下文"
                print_error "    ls -Z $COMPOSE_FILE"
                print_error "    如果需要，修复上下文: sudo chcon -R -t container_file_t $SCRIPT_DIR"
                print_error ""
                print_error "  方案4: 检查 Docker daemon 日志"
                print_error "    journalctl -u docker.service -n 50"
                print_error ""
                print_error "  方案5: 检查文件系统是否可写"
                print_error "    touch $SCRIPT_DIR/.test_write && rm $SCRIPT_DIR/.test_write"
                exit 1
            else
                print_success "问题已修复，可以继续"
            fi
        fi
    else
        print_success "Docker Compose 配置文件验证通过"
    fi
    
    # 使用 --progress=plain 显示完整输出
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    # 显示调试信息
    print_info "当前工作目录: $(pwd)"
    print_info "Docker Compose 文件: $COMPOSE_FILE"
    print_info "使用的 Docker Compose 命令: $DOCKER_COMPOSE"
    
    # 检查 Docker daemon 是否运行
    print_info "检查 Docker daemon 状态..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon 未运行，请先启动 Docker 服务"
        print_info "尝试启动: sudo systemctl start docker"
        exit 1
    fi
    print_success "Docker daemon 运行正常"
    
    # 再次验证配置文件
    print_info "验证 Docker Compose 配置文件..."
    if ! $DOCKER_COMPOSE -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        print_error "Docker Compose 配置文件验证失败"
        print_info "尝试查看详细错误:"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" config
        exit 1
    fi
    print_success "配置文件验证通过"
    
    print_info "准备执行: $DOCKER_COMPOSE up -d --build"
    echo
    
    # 直接执行命令并实时输出
    local exit_code
    
    # 执行构建和启动命令（不使用 --progress，兼容所有版本）
    # 直接执行并显示输出，同时捕获退出码
    print_info "开始执行 Docker Compose 命令..."
    set +e  # 暂时关闭错误退出，以便捕获退出码
    $DOCKER_COMPOSE up -d --build
    exit_code=$?
    set -e  # 重新开启错误退出
    
    echo  # 添加空行分隔
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "服务构建或启动失败（退出码: $exit_code）"
        print_info "尝试诊断问题..."
        echo
        diagnose_compose_issue "$COMPOSE_FILE"
        exit 1
    fi
    
    # 如果命令成功但没有输出，给出提示
    if [ $exit_code -eq 0 ]; then
        print_info "Docker Compose 命令执行完成"
    fi
    
    # 验证容器是否真的创建了
    local container_count
    container_count=$($DOCKER_COMPOSE ps -q 2>/dev/null | wc -l)
    if [ "$container_count" -eq 0 ]; then
        print_error "警告：没有检测到运行的容器"
        print_info "请检查 docker-compose.yml 配置和依赖服务（如 Nacos、PostgreSQL、Redis 等）"
        print_info "尝试查看服务状态："
        $DOCKER_COMPOSE ps
        exit 1
    fi
    
    print_success "服务构建并启动完成（所有编译在容器中完成，共 $container_count 个容器）"
}

# 启动所有服务
start_services() {
    print_info "启动所有服务..."
    cd "$SCRIPT_DIR"
    # 使用 --quiet-pull 减少拉取镜像时的输出
    if echo "$DOCKER_COMPOSE" | grep -q "docker compose"; then
        $DOCKER_COMPOSE up -d --quiet-pull 2>&1 | grep -E "(Creating|Starting|Started|ERROR|WARNING)" || true
    else
        $DOCKER_COMPOSE up -d 2>&1 | grep -E "(Creating|Starting|Started|ERROR|WARNING)" || true
    fi
    print_success "服务启动完成"
}

# 停止所有服务
stop_services() {
    print_info "停止所有服务..."
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE down
    print_success "服务已停止"
}

# 重启所有服务
restart_services() {
    print_info "重启所有服务..."
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE restart
    print_success "服务重启完成"
}

# 查看服务状态
show_status() {
    print_info "服务状态:"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE ps
}

# 查看日志
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        print_info "查看所有服务日志（最近50行，按Ctrl+C退出）..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs -f --tail=50
    else
        print_info "查看服务 $service 的日志（最近50行，按Ctrl+C退出）..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs -f --tail=50 "$service"
    fi
}

# 查看特定服务的日志（最近50行）
show_logs_tail() {
    local service=$1
    if [ -z "$service" ]; then
        print_info "查看所有服务最近50行日志..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs --tail=50
    else
        print_info "查看服务 $service 最近50行日志..."
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE logs --tail=50 "$service"
    fi
}

# 重启特定服务
restart_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "请指定要重启的服务名称"
        echo "可用服务:"
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE config --services
        exit 1
    fi
    print_info "重启服务: $service"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE restart "$service"
    print_success "服务 $service 重启完成"
}

# 停止特定服务
stop_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "请指定要停止的服务名称"
        echo "可用服务:"
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE config --services
        exit 1
    fi
    print_info "停止服务: $service"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE stop "$service"
    print_success "服务 $service 已停止"
}

# 启动特定服务
start_service() {
    local service=$1
    if [ -z "$service" ]; then
        print_error "请指定要启动的服务名称"
        echo "可用服务:"
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE config --services
        exit 1
    fi
    print_info "启动服务: $service"
    cd "$SCRIPT_DIR"
    $DOCKER_COMPOSE up -d "$service"
    print_success "服务 $service 启动完成"
}

# 清理（停止并删除容器）
clean() {
    print_warning "这将停止并删除所有容器，但保留镜像"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE down
        print_success "清理完成"
    else
        print_info "操作已取消"
    fi
}

# 完全清理（包括镜像）
clean_all() {
    print_warning "这将停止并删除所有容器和镜像"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$SCRIPT_DIR"
        $DOCKER_COMPOSE down --rmi all
        print_success "完全清理完成"
    else
        print_info "操作已取消"
    fi
}

# 更新服务（重新构建并重启）
update_services() {
    print_info "更新所有服务（在容器中重新构建并重启，显示完整日志）..."
    
    # 确保权限正确
    check_compose_file
    
    cd "$SCRIPT_DIR"
    # 使用 --progress=plain 显示完整输出
    # 注意：编译将在Docker容器中完成，不需要宿主机Maven环境
    
    # 直接执行命令并实时输出
    local exit_code
    
    # 执行更新命令（不使用 --progress，兼容所有版本）
    $DOCKER_COMPOSE up -d --build --force-recreate
    exit_code=$?
    
    # 检查命令是否成功
    if [ $exit_code -ne 0 ]; then
        print_error "服务更新失败（退出码: $exit_code）"
        exit 1
    fi
    
    # 验证容器是否真的创建了
    local container_count
    container_count=$($DOCKER_COMPOSE ps -q 2>/dev/null | wc -l)
    if [ "$container_count" -eq 0 ]; then
        print_error "警告：没有检测到运行的容器"
        print_info "请检查 docker-compose.yml 配置和依赖服务（如 Nacos、PostgreSQL、Redis 等）"
        print_info "尝试查看服务状态："
        $DOCKER_COMPOSE ps
        exit 1
    fi
    
    print_success "服务更新完成（所有编译在容器中完成，共 $container_count 个容器）"
}

# 显示帮助信息
show_help() {
    cat << EOF
DEVICE模块 Docker Compose 管理脚本

用法: $0 [命令] [选项]

命令:
    build               构建所有Docker镜像（在容器中编译，无需宿主机Maven）
    start               启动所有服务
    stop                停止所有服务
    restart             重启所有服务
    status              查看服务状态
    logs [服务名]       查看日志（所有服务或指定服务，最近50行）
    logs-tail [服务名]  查看最近50行日志
    restart-service     重启指定服务
    stop-service        停止指定服务
    start-service       启动指定服务
    clean               清理（停止并删除容器，保留镜像）
    clean-all           完全清理（停止并删除容器和镜像）
    update              更新服务（在容器中重新构建并重启）
    install             安装（构建并启动所有服务，在容器中编译）
    help                显示此帮助信息

示例:
    $0 install                    # 构建并启动所有服务
    $0 start                      # 启动所有服务
    $0 logs iot-gateway           # 查看iot-gateway的日志
    $0 restart-service iot-system # 重启iot-system服务
    $0 status                     # 查看所有服务状态

可用服务:
    - iot-gateway
    - iot-system
    - iot-infra
    - iot-device
    - iot-dataset
    - iot-tdengine
    - iot-file
    - iot-message

EOF
}

# 主函数
main() {
    check_compose_file
    
    case "${1:-}" in
        build)
            build_images
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        logs-tail)
            show_logs_tail "$2"
            ;;
        restart-service)
            restart_service "$2"
            ;;
        stop-service)
            stop_service "$2"
            ;;
        start-service)
            start_service "$2"
            ;;
        clean)
            clean
            ;;
        clean-all)
            clean_all
            ;;
        update)
            update_services
            ;;
        install|build-and-start)
            build_and_start
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            # 如果没有参数，显示交互式菜单
            show_interactive_menu
            ;;
        *)
            print_error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 交互式菜单
show_interactive_menu() {
    while true; do
        echo
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}  DEVICE模块 Docker Compose 管理${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo "1) 安装/构建并启动所有服务"
        echo "2) 启动所有服务"
        echo "3) 停止所有服务"
        echo "4) 重启所有服务"
        echo "5) 查看服务状态"
        echo "6) 查看日志（所有服务）"
        echo "7) 查看日志（指定服务）"
        echo "8) 重启指定服务"
        echo "9) 停止指定服务"
        echo "10) 启动指定服务"
        echo "11) 更新服务（重新构建并重启）"
        echo "12) 清理（删除容器，保留镜像）"
        echo "13) 完全清理（删除容器和镜像）"
        echo "0) 退出"
        echo
        read -p "请选择操作 [0-13]: " choice
        
        case $choice in
            1)
                build_and_start
                ;;
            2)
                start_services
                ;;
            3)
                stop_services
                ;;
            4)
                restart_services
                ;;
            5)
                show_status
                ;;
            6)
                show_logs
                ;;
            7)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                show_logs "$service_name"
                ;;
            8)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                restart_service "$service_name"
                ;;
            9)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                stop_service "$service_name"
                ;;
            10)
                echo "可用服务:"
                cd "$SCRIPT_DIR"
                $DOCKER_COMPOSE config --services
                read -p "请输入服务名称: " service_name
                start_service "$service_name"
                ;;
            11)
                update_services
                ;;
            12)
                clean
                ;;
            13)
                clean_all
                ;;
            0)
                print_info "退出"
                exit 0
                ;;
            *)
                print_error "无效选择，请重新输入"
                ;;
        esac
    done
}

# 执行主函数
main "$@"

