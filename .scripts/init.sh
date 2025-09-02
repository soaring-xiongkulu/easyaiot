#!/bin/bash

# ==========================================
# 目录初始化脚本
# 功能：创建数据库及中间件的数据和日志目录
# 版本: 1.0
# 日期: 2025-09-02
# ==========================================

# 设置脚本执行选项
set -e  # 遇到任何错误立即退出脚本
set -u  # 遇到未定义的变量报错

# 颜色输出设置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 恢复默认颜色

# 打印彩色信息
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

# 创建目录的函数
create_directories() {
    local base_dirs=("db_data" "taos_data" "mq_data" "redis_data" "nacos_data")
    local sub_dirs=("data" "log")

    print_info "开始创建目录结构..."
    echo "当前工作目录: $(pwd)"
    echo ""

    for base_dir in "${base_dirs[@]}"; do
        for sub_dir in "${sub_dirs[@]}"; do
            local full_path="${base_dir}/${sub_dir}"
            if [ -d "$full_path" ]; then
                print_warning "目录已存在: ${full_path} (跳过创建)"
            else
                mkdir -p "$full_path"
                if [ $? -eq 0 ]; then
                    print_success "已创建目录: ${full_path}"
                else
                    print_error "创建目录失败: ${full_path}"
                    exit 1
                fi
            fi
        done
    done
}

# 显示创建摘要
show_summary() {
    echo ""
    print_info "========== 目录创建摘要 =========="
    echo "创建时间: $(date)"
    echo "当前工作目录: $(pwd)"
    echo "创建的目录结构:"

    local base_dirs=("db_data" "taos_data" "mq_data" "redis_data" "nacos_data")
    local sub_dirs=("data" "log")

    for base_dir in "${base_dirs[@]}"; do
        echo "  📁 ${base_dir}"
        for sub_dir in "${sub_dirs[@]}"; do
            local full_path="${base_dir}/${sub_dir}"
            if [ -d "$full_path" ]; then
                echo "      ├── 📂 ${sub_dir} ${GREEN}(存在)${NC}"
            else
                echo "      ├── 📂 ${sub_dir} ${RED}(缺失)${NC}"
            fi
        done
    done

    print_info "=================================="
}

# 主执行函数
main() {
    echo "=========================================="
    echo "        目录结构初始化脚本"
    echo "=========================================="

    # 创建目录
    create_directories

    # 显示创建结果摘要
    show_summary

    print_success "目录初始化完成！"
}

# 执行主函数
main "$@"