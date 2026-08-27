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
    echo "  4) 移动端 — APP 三端打包管理（Android/iOS/HarmonyOS）"
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
    echo "  10) 查看当前部署形态（edge/mini/standard/full）"
    echo "  11) 显示完整命令行帮助"
    echo "  12) 清理 build-runtime 构建产物"
    echo "     说明：先停止业务服务，再删打包镜像/构建缓存；中间件不停"
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
    echo "  5) 告警事件面验收（控制面共享盘 + MQTT 入库）"
    echo "     说明：探针校验 ALERT_IMAGES 共享挂载，再跑 MQTT→iot-sink→alert 表"
    echo "  6) 节点 Ceph/共享媒体（列表·探针·业务打通）"
    echo "     说明：按 compute_node 列出 ceph_mount_ready，验 alert_images + playbacks"
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
        read -r -p "请输入分析选项 [0-6]: " choice || choice=""
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
            5)
                print_info "即将执行：告警事件面验收 (verify-alert)"
                easyaiot_run_command verify-alert
                ;;
            6)
                print_info "即将执行：节点 Ceph 列表 + 业务验收 (ceph verify)"
                easyaiot_run_command ceph verify
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
        read -r -p "请输入选项 [0-4，默认 0 退出]: " choice || choice=""
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
            4)
                run_mobile_interactive_menu
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

# ---- 移动端 APP 三端打包管理（Android/iOS/HarmonyOS）----
# 直接调用同目录 mobile.sh，不依赖各安装脚本实现 mobile 命令

_print_mobile_header() {
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  【移动端】APP 三端打包管理${NC}"
    echo -e "${YELLOW}  Android / iOS / HarmonyOS${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "  1) 三端状态巡检（版本一致性 / 工具链 / 成品数）"
    echo "     说明：打包前先巡检五处版本号是否一致"
    echo "  2) 打包（单端或三端）"
    echo "     说明：无原生工具链的平台可用「仅前端构建」产出可交接中间态"
    echo "  3) 发版：版本号一次改齐 5 处（bump）"
    echo "     说明：APP manifest + Android/iOS/鸿蒙壳工程全部对齐并回读校验"
    echo "  4) 列出已产出安装包"
    echo "  5) 清理打包成品"
    echo ""
    echo "总览与命名规范见 MOBILE.md"
    echo ""
    echo "  0) 返回上级菜单"
    echo ""
}

run_mobile_interactive_menu() {
    local choice="" target mode ver code mobile_sh=""
    while true; do
        _print_mobile_header
        read -r -p "请输入移动端选项 [0-5]: " choice || choice=""
        if [ -z "$choice" ]; then
            continue
        fi
        case "$choice" in
            1)
                print_info "即将执行：三端状态巡检 (mobile status)"
                bash "${SCRIPT_DIR}/mobile.sh" status || true
                ;;
            2)
                read -r -p "打包目标 android|ios|harmonyos|all [all]: " target || target=""
                target="${target:-all}"
                read -r -p "环境 prod|test|dev [prod]: " mode || mode=""
                mode="${mode:-prod}"
                print_info "即将执行：打包 ${target}（${mode}）(mobile build)"
                bash "${SCRIPT_DIR}/mobile.sh" build "$target" "$mode" || true
                ;;
            3)
                read -r -p "新版本号 x.y.z（如 1.0.1）: " ver || ver=""
                read -r -p "versionCode 整数（如 101）: " code || code=""
                if [ -z "$ver" ] || [ -z "$code" ]; then
                    print_error "版本号与 versionCode 均不能为空"
                    sleep 1
                    continue
                fi
                print_info "即将执行：发版 $ver/$code (mobile bump)"
                bash "${SCRIPT_DIR}/mobile.sh" bump "$ver" "$code" || true
                ;;
            4)
                print_info "即将执行：列出已产出安装包 (mobile artifacts)"
                bash "${SCRIPT_DIR}/mobile.sh" artifacts || true
                ;;
            5)
                read -r -p "清理目标 android|ios|harmonyos|all [all]: " target || target=""
                target="${target:-all}"
                print_info "即将执行：清理 ${target} 打包成品 (mobile clean)"
                bash "${SCRIPT_DIR}/mobile.sh" clean "$target" || true
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
