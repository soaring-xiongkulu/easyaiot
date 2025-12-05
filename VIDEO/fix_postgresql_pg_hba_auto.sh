#!/bin/bash
#
# PostgreSQL pg_hba.conf 自动修复脚本（用于开机自启动）
# 等待 PostgreSQL 容器启动后自动执行修复
#
# @author 翱翔的雄库鲁
# @email andywebjava@163.com
# @wechat EasyAIoT2025

set -e

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志文件
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/fix_postgresql_pg_hba_auto_$(date +%Y%m%d).log"

# 日志函数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1" | tee -a "$LOG_FILE"
}

# 配置
POSTGRES_CONTAINER="postgres-server"
MAX_WAIT_TIME=300  # 最大等待时间（秒）
CHECK_INTERVAL=5   # 检查间隔（秒）

log_info "========================================="
log_info "PostgreSQL pg_hba.conf 自动修复脚本启动"
log_info "========================================="

# 等待 Docker 服务启动
log_info "等待 Docker 服务启动..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker ps &> /dev/null; then
        log_success "Docker 服务已启动"
        break
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 10)) -eq 0 ]; then
        log_warning "等待 Docker 服务启动... ($attempt/$max_attempts)"
    fi
    sleep 2
done

if [ $attempt -ge $max_attempts ]; then
    log_error "Docker 服务未启动，退出"
    exit 1
fi

# 等待 PostgreSQL 容器启动
log_info "等待 PostgreSQL 容器 '$POSTGRES_CONTAINER' 启动..."
start_time=$(date +%s)
attempt=0

while true; do
    # 检查容器是否存在
    if docker ps -a --filter "name=$POSTGRES_CONTAINER" --format "{{.Names}}" | grep -q "$POSTGRES_CONTAINER"; then
        # 检查容器是否在运行
        if docker ps --filter "name=$POSTGRES_CONTAINER" --format "{{.Names}}" | grep -q "$POSTGRES_CONTAINER"; then
            log_success "PostgreSQL 容器已启动"
            break
        else
            log_info "PostgreSQL 容器存在但未运行，尝试启动..."
            docker start "$POSTGRES_CONTAINER" > /dev/null 2>&1 || true
        fi
    fi
    
    # 检查是否超时
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    if [ $elapsed -ge $MAX_WAIT_TIME ]; then
        log_error "等待 PostgreSQL 容器启动超时（${MAX_WAIT_TIME}秒），退出"
        exit 1
    fi
    
    attempt=$((attempt + 1))
    if [ $((attempt % 6)) -eq 0 ]; then
        log_info "等待 PostgreSQL 容器启动... (已等待 ${elapsed}秒)"
    fi
    
    sleep $CHECK_INTERVAL
done

# 等待 PostgreSQL 服务就绪
log_info "等待 PostgreSQL 服务就绪..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec "$POSTGRES_CONTAINER" pg_isready -U postgres > /dev/null 2>&1; then
        log_success "PostgreSQL 服务已就绪"
        break
    fi
    attempt=$((attempt + 1))
    if [ $((attempt % 10)) -eq 0 ]; then
        log_info "等待 PostgreSQL 服务就绪... ($attempt/$max_attempts)"
    fi
    sleep 2
done

if [ $attempt -ge $max_attempts ]; then
    log_error "PostgreSQL 服务未就绪，但继续尝试修复..."
fi

# 执行修复脚本
log_info "执行 PostgreSQL pg_hba.conf 修复脚本..."
if [ -f "$SCRIPT_DIR/fix_postgresql_pg_hba.sh" ]; then
    # 执行修复脚本，捕获输出
    if bash "$SCRIPT_DIR/fix_postgresql_pg_hba.sh" >> "$LOG_FILE" 2>&1; then
        log_success "PostgreSQL pg_hba.conf 修复完成"
        exit 0
    else
        log_error "PostgreSQL pg_hba.conf 修复失败，查看日志: $LOG_FILE"
        exit 1
    fi
else
    log_error "修复脚本不存在: $SCRIPT_DIR/fix_postgresql_pg_hba.sh"
    exit 1
fi

