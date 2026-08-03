#!/bin/bash
# EasyAIoT 统一交互入口 — 两层引导菜单（供 install_linux*.sh 引用）
# 第一层：部署 | 分析
# 第二层：各类可编号选择的具体操作

easyaiot_run_command() {
    # 从菜单回调主脚本命令，避免再次进入交互菜单
    EASYAIOT_FROM_MENU=1 main "$@"
}

_print_root_header() {
    local label="${EASYAIOT_INSTALL_LABEL:-EasyAIoT 统一安装脚本}"
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  ${label}${NC}"
    echo -e "${YELLOW}  交互式引导（推荐新手使用）${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "请选择您要做的事（输入数字后回车）："
    echo ""
    echo "  1) 部署 — 安装、启动、停止、更新等服务操作"
    echo "  2) 分析 — 日志、磁盘、状态等问题定位"
    echo "  3) 官网 — SITE 官方网站独立部署"
    echo ""
    echo "  0) 退出"
    echo ""
}

_print_site_header() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  【官网】SITE 独立部署${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "默认端口：http://localhost:8090"
    echo ""
    echo "  1) 安装并启动官网"
    echo "  2) 启动官网"
    echo "  3) 停止官网"
    echo "  4) 重启官网"
    echo "  5) 查看官网状态"
    echo "  6) 查看官网日志"
    echo "  7) 重新构建官网镜像"
    echo "  8) 更新官网（重建并启动）"
    echo "  9) 清理官网容器与镜像"
    echo ""
    echo "  0) 返回上级菜单"
    echo ""
}

_print_deploy_header() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  【部署】服务安装与运维${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "常用操作（多数场景选 1～4 即可）："
    echo "  1) 首次安装并启动全部服务"
    echo "     说明：第一次在服务器部署 EasyAIoT 时选此项"
    echo "  2) 启动所有服务"
    echo "     说明：服务器重启后，或 stop 之后重新拉起"
    echo "  3) 停止所有服务"
    echo "     说明：维护前暂停全部容器（不删数据）"
    echo "  4) 重启所有服务"
    echo "     说明：配置变更后希望全部服务重新加载"
    echo ""
    echo "查看与维护："
    echo "  5) 查看各模块运行状态"
    echo "  6) 查看服务日志"
    echo "  7) 验证服务是否健康"
    echo "  8) 更新镜像并重启"
    echo ""
    echo "其他："
    echo "  9) 检查 Docker 环境是否就绪"
    echo "  10) 查看当前部署形态（mini/standard/full）"
    echo "  11) 显示完整命令行帮助"
    echo "  12) 清理 build-runtime 构建产物"
    echo "     说明：先停止业务服务（DEVICE/AI/VIDEO/WEB/APP），再删打包镜像/构建缓存；中间件不停"
    echo ""
    echo "  0) 返回上级菜单"
    echo ""
}

_print_analyze_header() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  【分析】问题定位与信息采集${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "请选择分析工具（输出可直接发给技术支持）："
    echo "  1) 多模块日志合并分析"
    echo "     说明：基础服务/DEVICE 按 docker-compose 拆分为独立容器，各约 500 行"
    echo "  2) 项目磁盘占用分析"
    echo "     说明：MinIO 录像、告警图、本地 playbacks 等关键目录占用"
    echo "  3) 服务状态与健康验证"
    echo "     说明：先看运行状态，再自动做健康检查"
    echo "  4) Docker 与环境检查"
    echo "     说明：确认 Docker / Compose 是否安装可用"
    echo ""
    echo "  0) 返回上级菜单"
    echo ""
}

run_deploy_interactive_menu() {
    local choice=""
    while true; do
        _print_deploy_header
        read -r -p "请输入部署选项 [0-12]: " choice || choice=""
        if [ -z "$choice" ]; then
            continue
        fi
        case "$choice" in
            1)
                print_info "即将执行：首次安装并启动全部服务 (install)"
                easyaiot_run_command install
                ;;
            2)
                print_info "即将执行：启动所有服务 (start)"
                easyaiot_run_command start
                ;;
            3)
                print_info "即将执行：停止所有服务 (stop)"
                easyaiot_run_command stop
                ;;
            4)
                print_info "即将执行：重启所有服务 (restart)"
                easyaiot_run_command restart
                ;;
            5)
                print_info "即将执行：查看各模块运行状态 (status)"
                easyaiot_run_command status
                ;;
            6)
                print_info "即将执行：查看服务日志 (logs)"
                easyaiot_run_command logs
                ;;
            7)
                print_info "即将执行：验证服务是否健康 (verify)"
                easyaiot_run_command verify
                ;;
            8)
                print_info "即将执行：更新镜像并重启 (update)"
                easyaiot_run_command update
                ;;
            9)
                print_info "即将执行：检查 Docker 环境 (check)"
                easyaiot_run_command check
                ;;
            10)
                print_info "即将执行：查看部署形态 (profile)"
                easyaiot_run_command profile
                ;;
            11)
                show_help
                ;;
            12)
                print_info "即将执行：清理 build-runtime 构建产物（先停业务服务，保留中间件）"
                easyaiot_run_command clean-build-runtime
                ;;
            0|q|Q|exit|b|B)
                return 0
                ;;
            *)
                print_error "无效选项: $choice"
                sleep 1
                ;;
        esac
    done
}

run_analyze_interactive_menu() {
    local choice=""
    while true; do
        _print_analyze_header
        read -r -p "请输入分析选项 [0-4]: " choice || choice=""
        if [ -z "$choice" ]; then
            continue
        fi
        case "$choice" in
            1)
                print_info "即将执行：多模块日志合并分析"
                run_analyze_merge_logs
                ;;
            2)
                print_info "即将执行：项目磁盘占用分析"
                run_analyze_disk_usage
                ;;
            3)
                print_info "即将执行：服务状态 (status)"
                easyaiot_run_command status
                echo ""
                print_info "即将执行：健康验证 (verify)"
                easyaiot_run_command verify
                ;;
            4)
                print_info "即将执行：Docker 与环境检查 (check)"
                easyaiot_run_command check
                ;;
            0|q|Q|exit|b|B)
                return 0
                ;;
            *)
                print_error "无效选项: $choice"
                sleep 1
                ;;
        esac
    done
}

run_install_root_menu() {
    local choice=""
    while true; do
        _print_root_header
        read -r -p "请输入选项 [0-3，默认 0 退出]: " choice || choice=""
        choice="${choice:-0}"
        case "$choice" in
            1)
                run_deploy_interactive_menu
                ;;
            2)
                run_analyze_interactive_menu
                ;;
            3)
                run_site_interactive_menu
                ;;
            0|q|Q|exit)
                print_info "已退出交互式引导"
                return 0
                ;;
            *)
                print_error "无效选项: $choice"
                sleep 1
                ;;
        esac
    done
}

run_site_interactive_menu() {
    local choice=""
    while true; do
        _print_site_header
        read -r -p "请输入官网选项 [0-9]: " choice || choice=""
        if [ -z "$choice" ]; then
            continue
        fi
        case "$choice" in
            1)
                print_info "即将执行：安装并启动官网 (site install)"
                easyaiot_run_command site install
                ;;
            2)
                print_info "即将执行：启动官网 (site start)"
                easyaiot_run_command site start
                ;;
            3)
                print_info "即将执行：停止官网 (site stop)"
                easyaiot_run_command site stop
                ;;
            4)
                print_info "即将执行：重启官网 (site restart)"
                easyaiot_run_command site restart
                ;;
            5)
                print_info "即将执行：查看官网状态 (site status)"
                easyaiot_run_command site status
                ;;
            6)
                print_info "即将执行：查看官网日志 (site logs)"
                easyaiot_run_command site logs
                ;;
            7)
                print_info "即将执行：构建官网镜像 (site build)"
                easyaiot_run_command site build
                ;;
            8)
                print_info "即将执行：更新官网 (site update)"
                easyaiot_run_command site update
                ;;
            9)
                print_info "即将执行：清理官网 (site clean)"
                easyaiot_run_command site clean
                ;;
            0|q|Q|exit|b|B)
                return 0
                ;;
            *)
                print_error "无效选项: $choice"
                sleep 1
                ;;
        esac
    done
}

# 兼容旧命令 diagnose
run_diagnose_interactive_menu() {
    run_analyze_interactive_menu "$@"
}

invoke_analyze_merge_logs() {
    exec bash "${SCRIPT_DIR}/analyze_merge_logs.sh" "$@"
}

invoke_analyze_disk_usage() {
    exec bash "${SCRIPT_DIR}/analyze_disk_usage.sh" "$@"
}

run_analyze_merge_logs() {
    EASYAIOT_LOG_FROM_MENU=1 bash "${SCRIPT_DIR}/analyze_merge_logs.sh" "$@"
}

run_analyze_disk_usage() {
    bash "${SCRIPT_DIR}/analyze_disk_usage.sh" "$@"
}
