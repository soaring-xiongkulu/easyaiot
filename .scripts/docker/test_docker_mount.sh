#!/bin/bash

# ============================================
# Docker 容器创建和文件挂载测试脚本
# ============================================
# 用于测试当前服务器是否能够创建 Docker 容器并挂载文件进去
# 使用方法：
#   ./test_docker_mount.sh
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 测试目录和文件
TEST_DIR="${SCRIPT_DIR}/.docker_mount_test"
TEST_FILE="${TEST_DIR}/test_file.txt"
TEST_DIR_IN_CONTAINER="/test_mount"
CONTAINER_NAME="docker-mount-test-$$"

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

print_section() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
}

# 清理函数
cleanup() {
    print_info "清理测试资源..."
    
    # 停止并删除测试容器
    if docker ps -a --filter "name=${CONTAINER_NAME}" --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        print_info "删除测试容器: ${CONTAINER_NAME}"
        docker rm -f "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    fi
    
    # 删除测试目录
    if [ -d "$TEST_DIR" ]; then
        print_info "删除测试目录: $TEST_DIR"
        rm -rf "$TEST_DIR" || true
    fi
    
    print_success "清理完成"
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 检查 Docker 是否安装
check_docker_installed() {
    print_section "检查 Docker 安装"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"
        print_info "安装 Docker:"
        print_info "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install docker.io"
        print_info "  CentOS/RHEL: sudo yum install docker"
        print_info "  或参考: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    local docker_version=$(docker --version)
    print_success "Docker 已安装: $docker_version"
}

# 检查 Docker 服务状态
check_docker_service() {
    print_section "检查 Docker 服务状态"
    
    # 检查 Docker 服务是否运行
    if systemctl is-active --quiet docker 2>/dev/null || pgrep -x dockerd > /dev/null 2>&1; then
        print_success "Docker 服务正在运行"
    else
        print_error "Docker 服务未运行"
        print_info "启动命令: sudo systemctl start docker"
        exit 1
    fi
    
    # 检查 Docker 权限
    if docker ps &> /dev/null; then
        print_success "Docker 权限正常"
    else
        print_error "Docker 权限不足"
        print_info "解决方案: sudo usermod -aG docker $USER"
        print_info "然后重新登录或运行: newgrp docker"
        exit 1
    fi
    
    # 测试 Docker 基本功能
    print_info "测试 Docker 基本功能..."
    if docker run --rm hello-world > /dev/null 2>&1; then
        print_success "Docker 基本功能正常"
    else
        print_error "Docker 基本功能测试失败"
        exit 1
    fi
}

# 准备测试文件
prepare_test_files() {
    print_section "准备测试文件"
    
    # 创建测试目录
    print_info "创建测试目录: $TEST_DIR"
    if mkdir -p "$TEST_DIR" 2>/dev/null; then
        print_success "测试目录创建成功"
    else
        print_error "测试目录创建失败"
        exit 1
    fi
    
    # 创建测试文件
    print_info "创建测试文件: $TEST_FILE"
    local test_content="Docker Mount Test File
创建时间: $(date '+%Y-%m-%d %H:%M:%S')
测试内容: 这是一个用于测试 Docker 文件挂载的测试文件
随机字符串: $(openssl rand -hex 16 2>/dev/null || echo $(date +%s))"
    
    if echo "$test_content" > "$TEST_FILE" 2>/dev/null; then
        print_success "测试文件创建成功"
        print_info "文件内容:"
        echo "$test_content" | sed 's/^/  /'
    else
        print_error "测试文件创建失败"
        exit 1
    fi
    
    # 检查文件系统是否可写
    print_info "检查文件系统是否可写..."
    if [ -w "$TEST_DIR" ]; then
        print_success "文件系统可写"
    else
        print_error "文件系统不可写"
        print_info "检查挂载状态: mount | grep $(df "$TEST_DIR" 2>/dev/null | tail -1 | awk '{print $1}')"
        exit 1
    fi
}

# 测试文件挂载（只读）
test_readonly_mount() {
    print_section "测试只读文件挂载"
    
    print_info "创建测试容器（只读挂载）..."
    print_info "容器名称: ${CONTAINER_NAME}"
    print_info "挂载路径: ${TEST_FILE} -> ${TEST_DIR_IN_CONTAINER}/test_file.txt:ro"
    
    # 创建容器并挂载文件（只读）
    if docker run -d --name "${CONTAINER_NAME}" \
        -v "${TEST_FILE}:${TEST_DIR_IN_CONTAINER}/test_file.txt:ro" \
        alpine:latest sleep 300 > /dev/null 2>&1; then
        print_success "容器创建成功"
    else
        print_error "容器创建失败"
        return 1
    fi
    
    # 等待容器启动
    sleep 2
    
    # 检查容器是否运行
    if docker ps --filter "name=${CONTAINER_NAME}" --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        print_success "容器正在运行"
    else
        print_error "容器未运行"
        print_info "容器日志:"
        docker logs "${CONTAINER_NAME}" 2>&1 | head -20 | sed 's/^/  /'
        return 1
    fi
    
    # 在容器内读取文件
    print_info "在容器内读取文件..."
    if docker exec "${CONTAINER_NAME}" cat "${TEST_DIR_IN_CONTAINER}/test_file.txt" > /dev/null 2>&1; then
        print_success "容器内文件读取成功"
        print_info "文件内容:"
        docker exec "${CONTAINER_NAME}" cat "${TEST_DIR_IN_CONTAINER}/test_file.txt" | sed 's/^/  /'
    else
        print_error "容器内文件读取失败"
        return 1
    fi
    
    # 测试只读权限（尝试写入应该失败）
    print_info "测试只读权限（尝试写入应该失败）..."
    if docker exec "${CONTAINER_NAME}" sh -c "echo 'test' >> ${TEST_DIR_IN_CONTAINER}/test_file.txt" 2>/dev/null; then
        print_warning "只读挂载测试失败：文件可以被写入（这不应该发生）"
        return 1
    else
        print_success "只读挂载测试通过：文件无法被写入（符合预期）"
    fi
    
    # 停止并删除容器
    print_info "停止测试容器..."
    docker rm -f "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    
    return 0
}

# 测试目录挂载（读写）
test_readwrite_mount() {
    print_section "测试读写目录挂载"
    
    print_info "创建测试容器（读写挂载）..."
    print_info "容器名称: ${CONTAINER_NAME}"
    print_info "挂载路径: ${TEST_DIR} -> ${TEST_DIR_IN_CONTAINER}:rw"
    
    # 创建容器并挂载目录（读写）
    if docker run -d --name "${CONTAINER_NAME}" \
        -v "${TEST_DIR}:${TEST_DIR_IN_CONTAINER}:rw" \
        alpine:latest sleep 300 > /dev/null 2>&1; then
        print_success "容器创建成功"
    else
        print_error "容器创建失败"
        return 1
    fi
    
    # 等待容器启动
    sleep 2
    
    # 检查容器是否运行
    if docker ps --filter "name=${CONTAINER_NAME}" --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        print_success "容器正在运行"
    else
        print_error "容器未运行"
        print_info "容器日志:"
        docker logs "${CONTAINER_NAME}" 2>&1 | head -20 | sed 's/^/  /'
        return 1
    fi
    
    # 在容器内读取文件
    print_info "在容器内读取文件..."
    if docker exec "${CONTAINER_NAME}" cat "${TEST_DIR_IN_CONTAINER}/test_file.txt" > /dev/null 2>&1; then
        print_success "容器内文件读取成功"
    else
        print_error "容器内文件读取失败"
        return 1
    fi
    
    # 在容器内创建新文件
    print_info "在容器内创建新文件..."
    local new_file="${TEST_DIR_IN_CONTAINER}/container_created_file.txt"
    local new_content="这是容器内创建的文件
创建时间: $(date '+%Y-%m-%d %H:%M:%S')"
    
    if docker exec "${CONTAINER_NAME}" sh -c "echo '$new_content' > ${new_file}" 2>/dev/null; then
        print_success "容器内文件创建成功"
        
        # 检查宿主机上是否能看到新文件
        local host_file="${TEST_DIR}/container_created_file.txt"
        if [ -f "$host_file" ]; then
            print_success "宿主机上可以看到容器创建的文件"
            print_info "文件内容:"
            cat "$host_file" | sed 's/^/  /'
        else
            print_error "宿主机上无法看到容器创建的文件"
            return 1
        fi
    else
        print_error "容器内文件创建失败"
        return 1
    fi
    
    # 在容器内修改文件
    print_info "在容器内修改文件..."
    if docker exec "${CONTAINER_NAME}" sh -c "echo '容器内添加的内容' >> ${TEST_DIR_IN_CONTAINER}/test_file.txt" 2>/dev/null; then
        print_success "容器内文件修改成功"
        
        # 检查宿主机上文件是否被修改
        if grep -q "容器内添加的内容" "${TEST_FILE}" 2>/dev/null; then
            print_success "宿主机上文件已被修改"
        else
            print_error "宿主机上文件未被修改"
            return 1
        fi
    else
        print_error "容器内文件修改失败"
        return 1
    fi
    
    # 停止并删除容器
    print_info "停止测试容器..."
    docker rm -f "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    
    return 0
}

# 测试文件系统权限
test_filesystem_permissions() {
    print_section "测试文件系统权限"
    
    # 检查挂载点信息
    print_info "检查挂载点信息..."
    local mount_point=$(df "$TEST_DIR" 2>/dev/null | tail -1 | awk '{print $6}')
    local filesystem=$(df "$TEST_DIR" 2>/dev/null | tail -1 | awk '{print $1}')
    print_info "  挂载点: $mount_point"
    print_info "  文件系统: $filesystem"
    
    # 检查挂载选项
    if [ -f /proc/mounts ]; then
        local mount_options=$(grep -E "^${filesystem}[[:space:]]" /proc/mounts 2>/dev/null | awk '{print $4}' | head -1 || echo "")
        if [ -n "$mount_options" ]; then
            print_info "  挂载选项: $mount_options"
            
            # 检查是否包含 ro (read-only)
            if echo "$mount_options" | grep -qE "(^|,)ro(,|$)"; then
                print_warning "  文件系统挂载为只读模式 (ro)"
                print_warning "  这可能会影响 Docker 容器的文件挂载功能"
            else
                print_success "  文件系统挂载为可写模式 (rw)"
            fi
        fi
    fi
    
    # 检查磁盘空间
    print_info "检查磁盘空间..."
    local df_output=$(df -h "$TEST_DIR" 2>/dev/null | tail -1)
    if [ -n "$df_output" ]; then
        local total=$(echo "$df_output" | awk '{print $2}')
        local used=$(echo "$df_output" | awk '{print $3}')
        local available=$(echo "$df_output" | awk '{print $4}')
        local use_percent=$(echo "$df_output" | awk '{print $5}' | sed 's/%//')
        
        print_info "  总空间: $total"
        print_info "  已用: $used"
        print_info "  可用: $available"
        print_info "  使用率: ${use_percent}%"
        
        if [ "$use_percent" -ge 95 ]; then
            print_error "  磁盘空间严重不足（使用率 >= 95%）"
            return 1
        elif [ "$use_percent" -ge 90 ]; then
            print_warning "  磁盘空间不足（使用率 >= 90%）"
        else
            print_success "  磁盘空间充足"
        fi
    fi
}

# 生成测试报告
generate_report() {
    print_section "测试报告"
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # 统计测试结果
    if [ -f "${TEST_DIR}/.test_results" ]; then
        while IFS= read -r line; do
            total_tests=$((total_tests + 1))
            if echo "$line" | grep -q "PASS"; then
                passed_tests=$((passed_tests + 1))
            else
                failed_tests=$((failed_tests + 1))
            fi
        done < "${TEST_DIR}/.test_results"
    fi
    
    print_info "测试总结:"
    print_info "  总测试数: $total_tests"
    print_success "  通过: $passed_tests"
    if [ $failed_tests -gt 0 ]; then
        print_error "  失败: $failed_tests"
    else
        print_success "  失败: $failed_tests"
    fi
    
    echo ""
    if [ $failed_tests -eq 0 ] && [ $total_tests -gt 0 ]; then
        print_success "所有测试通过！服务器可以正常创建 Docker 容器并挂载文件。"
    elif [ $failed_tests -gt 0 ]; then
        print_error "部分测试失败，请检查上述错误信息。"
    fi
}

# 主函数
main() {
    print_section "Docker 容器创建和文件挂载测试工具"
    
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    local test_results_file="${TEST_DIR}/.test_results"
    rm -f "$test_results_file"
    
    # 检查 Docker 安装
    check_docker_installed
    echo ""
    
    # 检查 Docker 服务
    check_docker_service
    echo ""
    
    # 测试文件系统权限
    test_filesystem_permissions
    echo ""
    
    # 准备测试文件
    prepare_test_files
    echo ""
    
    # 测试只读挂载
    if test_readonly_mount; then
        echo "PASS: 只读文件挂载测试" >> "$test_results_file"
    else
        echo "FAIL: 只读文件挂载测试" >> "$test_results_file"
    fi
    echo ""
    
    # 测试读写挂载
    if test_readwrite_mount; then
        echo "PASS: 读写目录挂载测试" >> "$test_results_file"
    else
        echo "FAIL: 读写目录挂载测试" >> "$test_results_file"
    fi
    echo ""
    
    # 生成测试报告
    generate_report
    echo ""
    
    print_section "测试完成"
    echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    print_info "测试资源将在脚本退出时自动清理"
}

# 运行主函数
main "$@"

