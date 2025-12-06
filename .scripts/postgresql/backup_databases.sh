#!/bin/bash

# PostgreSQL 数据库备份脚本
# 使用 Docker 容器内的 pg_dump（版本匹配）
# 备份目录：.scripts/postgresql/backup/备份时间戳/

# 注意：不使用 set -e，因为我们需要继续处理所有数据库，即使某个失败

# 配置信息
POSTGRES_CONTAINER="postgres-server"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="iot45722414822"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"

# 需要备份的数据库列表
DATABASES=(
    "iot-ai20"
    "iot-device20"
    "iot-video20"
    "iot-message20"
    "ruoyi-vue-pro20"
)

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 备份目录（在脚本所在目录下的 backup 子目录）
BACKUP_BASE_DIR="${SCRIPT_DIR}/backup"

# 创建时间戳格式的备份目录
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${BACKUP_BASE_DIR}/${TIMESTAMP}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 容器是否运行
check_container() {
    if ! docker ps | grep -q "${POSTGRES_CONTAINER}"; then
        log_error "PostgreSQL 容器 ${POSTGRES_CONTAINER} 未运行！"
        log_info "请先启动容器：docker start ${POSTGRES_CONTAINER}"
        exit 1
    fi
    log_info "PostgreSQL 容器 ${POSTGRES_CONTAINER} 运行正常"
}

# 检查数据库是否存在
check_database() {
    local db_name=$1
    local result=$(docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${POSTGRES_CONTAINER}" \
        psql -U "${POSTGRES_USER}" -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -d postgres -tAc \
        "SELECT 1 FROM pg_database WHERE datname='${db_name}'" 2>/dev/null || echo "0")
    
    if [ "$result" = "1" ]; then
        return 0
    else
        return 1
    fi
}

# 备份单个数据库
backup_database() {
    local db_name=$1
    local backup_file="${BACKUP_DIR}/${db_name}.sql"
    local exit_code=0
    
    log_info "开始备份数据库: ${db_name}"
    
    # 检查数据库是否存在
    if ! check_database "${db_name}"; then
        log_warn "数据库 ${db_name} 不存在，跳过备份"
        return 1
    fi
    
    # 使用 Docker exec 在容器内执行 pg_dump
    # 注意：容器内的 pg_dump 版本是 18，与服务器版本匹配
    # 将 stderr 重定向到临时文件，以便检查是否有错误
    local error_file="${BACKUP_DIR}/${db_name}.error.log"
    if docker exec -e PGPASSWORD="${POSTGRES_PASSWORD}" "${POSTGRES_CONTAINER}" \
        pg_dump -U "${POSTGRES_USER}" \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -d "${db_name}" \
        --clean \
        --if-exists \
        --create \
        --format=plain \
        --no-owner \
        --no-privileges \
        > "${backup_file}" 2> "${error_file}"; then
        exit_code=$?
    else
        exit_code=$?
    fi
    
    # 检查备份文件是否成功创建且不为空
    if [ -f "${backup_file}" ] && [ -s "${backup_file}" ]; then
        # 检查错误日志文件，看是否有 pg_dump 的错误
        if [ -f "${error_file}" ] && [ -s "${error_file}" ]; then
            # 检查错误日志中是否有真正的错误（不是警告）
            if grep -qiE "pg_dump.*error|fatal|could not" "${error_file}" 2>/dev/null; then
                log_error "数据库 ${db_name} 备份失败，错误信息:"
                cat "${error_file}" | sed 's/^/  /'
                rm -f "${backup_file}" "${error_file}"
                return 1
            fi
        fi
        
        # 检查备份文件开头是否包含 PostgreSQL 备份标识
        if head -5 "${backup_file}" | grep -q "PostgreSQL database dump"; then
            local file_size=$(du -h "${backup_file}" | cut -f1)
            log_info "✓ 数据库 ${db_name} 备份成功: ${backup_file} (大小: ${file_size})"
            rm -f "${error_file}"
            return 0
        else
            log_error "数据库 ${db_name} 备份文件格式不正确，可能备份失败"
            rm -f "${backup_file}" "${error_file}"
            return 1
        fi
    else
        # 如果有错误日志，显示它
        if [ -f "${error_file}" ] && [ -s "${error_file}" ]; then
            log_error "数据库 ${db_name} 备份失败，错误信息:"
            cat "${error_file}" | sed 's/^/  /'
        else
            log_error "数据库 ${db_name} 备份文件为空或创建失败"
        fi
        rm -f "${backup_file}" "${error_file}"
        return 1
    fi
}

# 主函数
main() {
    log_info "=========================================="
    log_info "PostgreSQL 数据库备份脚本"
    log_info "=========================================="
    
    # 检查容器
    check_container
    
    # 创建备份目录
    mkdir -p "${BACKUP_DIR}"
    log_info "备份目录: ${BACKUP_DIR}"
    
    # 统计信息
    local success_count=0
    local fail_count=0
    local skip_count=0
    
    # 备份每个数据库
    for db in "${DATABASES[@]}"; do
        if backup_database "${db}"; then
            success_count=$((success_count + 1))
        else
            if check_database "${db}"; then
                fail_count=$((fail_count + 1))
            else
                skip_count=$((skip_count + 1))
            fi
        fi
        echo ""
    done
    
    # 输出统计信息
    log_info "=========================================="
    log_info "备份完成统计:"
    log_info "  成功: ${success_count} 个数据库"
    if [ ${fail_count} -gt 0 ]; then
        log_warn "  失败: ${fail_count} 个数据库"
    fi
    if [ ${skip_count} -gt 0 ]; then
        log_warn "  跳过: ${skip_count} 个数据库（不存在）"
    fi
    log_info "备份目录: ${BACKUP_DIR}"
    log_info "=========================================="
    
    # 如果有失败的备份，返回非零退出码
    if [ ${fail_count} -gt 0 ]; then
        exit 1
    fi
}

# 执行主函数
main

