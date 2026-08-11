#!/bin/bash
# ============================================
# EasyAIoT 多模块日志合并分析工具
# ============================================
# 交互式选择多个模块/子服务，合并输出各源最近约 500 行日志，
# 基础服务与 DEVICE 按 docker-compose 拆分为独立容器维度，模块间有明显分割线。
#
# 用法:
#   ./analyze_merge_logs.sh
#   ./analyze_merge_logs.sh --modules AI,dev-iot-gateway,mw-nacos
#   ./analyze_merge_logs.sh --modules DEVICE,.scripts/docker  # 展开为全部子服务
#   ./analyze_merge_logs.sh --lines 300 --save
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"

LOG_TAIL_LINES="${LOG_TAIL_LINES:-500}"
INTERACTIVE=true
SAVE_OUTPUT=false
SELECTED_UNITS=()
LOG_MENU_BACK=0

DEVICE_LOG_DIR="${PROJECT_ROOT}/.build-cache/device/logs"
DEVICE_NODE_LOG_DIR="${PROJECT_ROOT}/.build-cache/device/node-logs"
MW_COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
DEVICE_COMPOSE_FILE="${PROJECT_ROOT}/DEVICE/docker-compose.yml"
WEB_COMPOSE_FILE="${PROJECT_ROOT}/WEB/docker-compose.yaml"
AI_COMPOSE_FILE="${PROJECT_ROOT}/AI/docker-compose.yaml"
VIDEO_COMPOSE_FILE="${PROJECT_ROOT}/VIDEO/docker-compose.yaml"
EASYAIOT_DATA_DIR="${EASYAIOT_DATA_DIR:-${HOME}/easyaiot/data}"

# 日志采集单元顺序（menu 与输出均按此顺序）
ALL_LOG_UNITS=(
    mw-nacos mw-postgres-init mw-postgres mw-redis mw-kafka mw-minio mw-milvus
    mw-srs mw-nodered mw-fuxa mw-tdengine mw-tdengine-init mw-emqx mw-zlmediakit
    dev-iot-gateway dev-iot-system dev-iot-infra dev-iot-device dev-iot-dataset
    dev-iot-node dev-iot-visualize dev-iot-tdengine dev-iot-file dev-iot-message dev-iot-sink dev-iot-gb28181
    biz-ai biz-rtc biz-video biz-web biz-app biz-visualize
    mw-install-logs
)

declare -A UNIT_DISPLAY=(
    [mw-nacos]="基础/Nacos 注册配置 (nacos-server)"
    [mw-postgres-init]="基础/PostgreSQL 初始化 (postgres-init)"
    [mw-postgres]="基础/PostgreSQL 数据库 (postgres-server)"
    [mw-redis]="基础/Redis (redis-server)"
    [mw-kafka]="基础/Kafka (kafka-server)"
    [mw-minio]="基础/MinIO 对象存储 (minio-server)"
    [mw-milvus]="基础/Milvus 向量库 (milvus-server)"
    [mw-srs]="基础/SRS 流媒体 (srs-server)"
    [mw-nodered]="基础/NodeRED (nodered-server)"
    [mw-fuxa]="基础/FUXA 组态 (fuxa-server)"
    [mw-tdengine]="基础/TDengine (tdengine-server)"
    [mw-tdengine-init]="基础/TDengine 初始化 (tdengine-init)"
    [mw-emqx]="基础/EMQX MQTT (emqx-server)"
    [mw-zlmediakit]="基础/ZLMediaKit (zlmediakit-server)"
    [dev-iot-gateway]="DEVICE/网关 (iot-gateway)"
    [dev-iot-system]="DEVICE/系统模块 (iot-system)"
    [dev-iot-infra]="DEVICE/基础设施 (iot-infra)"
    [dev-iot-device]="DEVICE/设备服务 (iot-device)"
    [dev-iot-dataset]="DEVICE/数据集 (iot-dataset)"
    [dev-iot-node]="DEVICE/Node (iot-node)"
    [dev-iot-visualize]="DEVICE/可视化后台 (iot-visualize)"
    [dev-iot-tdengine]="DEVICE/TDengine 对接 (iot-tdengine)"
    [dev-iot-file]="DEVICE/文件服务 (iot-file)"
    [dev-iot-message]="DEVICE/消息服务 (iot-message)"
    [dev-iot-sink]="DEVICE/数据 Sink (iot-sink)"
    [dev-iot-gb28181]="DEVICE/GB28181 (iot-gb28181)"
    [biz-ai]="AI 服务 (ai-service)"
    [biz-rtc]="RTC 服务 (rtc-service)"
    [biz-video]="Video 服务 (video-service 等)"
    [biz-web]="Web 前端 (web-service)"
    [biz-app]="App 移动端 H5 (app-service)"
    [biz-visualize]="可视化编辑器 (visualize-service)"
    [mw-install-logs]="基础/安装脚本日志 (.scripts/docker/logs)"
)

# compose 服务名（用于 deploy_profile 跳过判断）
declare -A UNIT_COMPOSE_SERVICE=(
    [mw-nacos]=Nacos
    [mw-postgres-init]=PostgresSQL-init
    [mw-postgres]=PostgresSQL
    [mw-redis]=Redis
    [mw-kafka]=Kafka
    [mw-minio]=MinIO
    [mw-milvus]=Milvus
    [mw-srs]=SRS
    [mw-nodered]=NodeRED
    [mw-fuxa]=FUXA
    [mw-tdengine]=TDengine
    [mw-tdengine-init]=TDengine-init
    [mw-emqx]=EMQX
    [mw-zlmediakit]=ZLMediaKit
    [dev-iot-gateway]=iot-gateway
    [dev-iot-system]=iot-system
    [dev-iot-infra]=iot-infra
    [dev-iot-device]=iot-device
    [dev-iot-dataset]=iot-dataset
    [dev-iot-node]=iot-node
    [dev-iot-visualize]=iot-visualize
    [dev-iot-tdengine]=iot-tdengine
    [dev-iot-file]=iot-file
    [dev-iot-message]=iot-message
    [dev-iot-sink]=iot-sink
    [dev-iot-gb28181]=iot-gb28181
    [biz-ai]=ai-service
    [biz-rtc]=rtc-service
    [biz-video]=video-service
    [biz-web]=web-service
    [biz-app]=app-service
    [biz-visualize]=visualize-service
)

declare -A UNIT_CONTAINERS=(
    [mw-nacos]=nacos-server
    [mw-postgres-init]=postgres-init
    [mw-postgres]=postgres-server
    [mw-redis]=redis-server
    [mw-kafka]=kafka-server
    [mw-minio]=minio-server
    [mw-milvus]=milvus-server
    [mw-srs]=srs-server
    [mw-nodered]=nodered-server
    [mw-fuxa]=fuxa-server
    [mw-tdengine]=tdengine-server
    [mw-tdengine-init]=tdengine-init
    [mw-emqx]=emqx-server
    [mw-zlmediakit]=zlmediakit-server
    [dev-iot-gateway]=iot-gateway
    [dev-iot-system]=iot-system
    [dev-iot-infra]=iot-infra
    [dev-iot-device]=iot-device
    [dev-iot-dataset]=iot-dataset
    [dev-iot-node]=iot-node
    [dev-iot-visualize]=iot-visualize
    [dev-iot-tdengine]=iot-tdengine
    [dev-iot-file]=iot-file
    [dev-iot-message]=iot-message
    [dev-iot-sink]=iot-sink
    [dev-iot-gb28181]=iot-gb28181
    [biz-ai]="ai-service"
    [biz-rtc]="rtc-service"
    [biz-video]="video-service pusher-service sorter-service frame-extractor-service"
    [biz-web]=web-service
    [biz-app]=app-service
    [biz-visualize]=visualize-service
)

declare -A UNIT_FILE_LOG_DIRS=(
    [mw-nacos]="${SCRIPT_DIR}/standalone-logs"
    [mw-install-logs]="${SCRIPT_DIR}/logs"
)

# 宿主机日志目录与文件名模式（dir|glob）；按日期滚动时取最新文件的最近 N 行
declare -A UNIT_LOG_FILE_SPEC=(
    [mw-postgres]="${SCRIPT_DIR}/db_data/log|*.log"
    [mw-redis]="${SCRIPT_DIR}/redis_data/logs|*.log"
    [mw-tdengine]="${SCRIPT_DIR}/taos_data/log|*.log"
    [mw-srs]="${EASYAIOT_DATA_DIR}|srs.log*"
    [mw-zlmediakit]="${SCRIPT_DIR}/../zlmediakit/log|*.log"
    [dev-iot-gateway]="${DEVICE_LOG_DIR}|gateway-server.log*"
    [dev-iot-system]="${DEVICE_LOG_DIR}|system-server.log*"
    [dev-iot-infra]="${DEVICE_LOG_DIR}|infra-server.log*"
    [dev-iot-device]="${DEVICE_LOG_DIR}|device-server.log*"
    [dev-iot-dataset]="${DEVICE_LOG_DIR}|dataset-server.log*"
    [dev-iot-node]="${DEVICE_NODE_LOG_DIR}|node-server.log*"
    [dev-iot-tdengine]="${DEVICE_LOG_DIR}|tdengine-server.log*"
    [dev-iot-file]="${DEVICE_LOG_DIR}|file-server.log*"
    [dev-iot-message]="${DEVICE_LOG_DIR}|message-server.log*"
    [dev-iot-sink]="${DEVICE_LOG_DIR}|sink-server.log*"
    [dev-iot-gb28181]="${DEVICE_LOG_DIR}|iot-gb28181.log*"
    [biz-web]="${PROJECT_ROOT}/WEB/logs|runtime.log*"
    [biz-app]="${PROJECT_ROOT}/APP/logs|runtime.log*"
    [biz-visualize]="${PROJECT_ROOT}/VISUALIZE/logs|runtime.log*"
)

declare -A UNIT_COMPOSE_FILE=(
    [mw-nacos]="${MW_COMPOSE_FILE}"
    [mw-postgres-init]="${MW_COMPOSE_FILE}"
    [mw-postgres]="${MW_COMPOSE_FILE}"
    [mw-redis]="${MW_COMPOSE_FILE}"
    [mw-kafka]="${MW_COMPOSE_FILE}"
    [mw-minio]="${MW_COMPOSE_FILE}"
    [mw-milvus]="${MW_COMPOSE_FILE}"
    [mw-srs]="${MW_COMPOSE_FILE}"
    [mw-nodered]="${MW_COMPOSE_FILE}"
    [mw-fuxa]="${MW_COMPOSE_FILE}"
    [mw-tdengine]="${MW_COMPOSE_FILE}"
    [mw-tdengine-init]="${MW_COMPOSE_FILE}"
    [mw-emqx]="${MW_COMPOSE_FILE}"
    [mw-zlmediakit]="${MW_COMPOSE_FILE}"
    [dev-iot-gateway]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-system]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-infra]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-device]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-dataset]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-node]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-tdengine]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-file]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-message]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-sink]="${DEVICE_COMPOSE_FILE}"
    [dev-iot-gb28181]="${DEVICE_COMPOSE_FILE}"
    [biz-ai]="${AI_COMPOSE_FILE}"
    [biz-rtc]="${PROJECT_ROOT}/RTC/docker-compose.yaml"
    [biz-video]="${VIDEO_COMPOSE_FILE}"
    [biz-web]="${WEB_COMPOSE_FILE}"
    [biz-app]="${PROJECT_ROOT}/APP/docker-compose.yaml"
    [biz-visualize]="${PROJECT_ROOT}/VISUALIZE/docker-compose.yaml"
)

# 旧版模块 ID → 展开为子单元
LEGACY_MODULE_EXPAND=(
    ".scripts/docker:mw-nacos,mw-postgres-init,mw-postgres,mw-redis,mw-kafka,mw-minio,mw-milvus,mw-srs,mw-nodered,mw-fuxa,mw-tdengine,mw-tdengine-init,mw-emqx,mw-zlmediakit,mw-install-logs"
    "middleware:mw-nacos,mw-postgres-init,mw-postgres,mw-redis,mw-kafka,mw-minio,mw-milvus,mw-srs,mw-nodered,mw-fuxa,mw-tdengine,mw-tdengine-init,mw-emqx,mw-zlmediakit,mw-install-logs"
    "DEVICE:dev-iot-gateway,dev-iot-system,dev-iot-infra,dev-iot-device,dev-iot-dataset,dev-iot-node,dev-iot-tdengine,dev-iot-file,dev-iot-message,dev-iot-sink,dev-iot-gb28181"
    "AI:biz-ai"
    "RTC:biz-rtc"
    "VIDEO:biz-video"
    "WEB:biz-web"
    "APP:biz-app"
    "VISUALIZE:biz-visualize"
)

print_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
print_ok()      { echo -e "${GREEN}[OK]${NC} $1"; }
print_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_err()     { echo -e "${RED}[ERROR]${NC} $1"; }
print_section() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_unit_separator() {
    echo ""
    echo -e "${MAGENTA}################################################################################${NC}"
    echo -e "${MAGENTA}#                         >>>  服务分割线  <<<                                 #${NC}"
    echo -e "${MAGENTA}################################################################################${NC}"
    echo ""
}

show_help() {
    cat <<'EOF'
用法: ./analyze_merge_logs.sh [选项]

选项:
  --modules <list>     指定采集单元，逗号分隔；all=当前形态下全部
                       支持旧 ID：.scripts/docker / DEVICE / AI / VIDEO / WEB / APP（自动展开子服务）
                       支持新 ID：mw-nacos / dev-iot-gateway / biz-ai 等
  --lines <n>          每个容器/日志源采集行数（默认 500）
  --save               保存到 .scripts/docker/logs/merged_logs_*.log
  --non-interactive    配合 --modules 使用
  -h, --help           显示帮助

示例:
  ./analyze_merge_logs.sh
  ./analyze_merge_logs.sh --modules dev-iot-gateway,mw-postgres,biz-ai
  ./analyze_merge_logs.sh --modules DEVICE --lines 300
  ./analyze_merge_logs.sh --non-interactive --modules all --save
EOF
}

init_deploy_profile_for_logs() {
    # 仅读取部署形态与跳过列表，不写各模块 .env（避免 analyze 工具副作用）
    load_saved_deploy_profile
    EASYAIOT_DEPLOY_PROFILE="$(_resolve_deploy_profile_raw)"
    export EASYAIOT_DEPLOY_PROFILE
    case "$EASYAIOT_DEPLOY_PROFILE" in
        mini)
            export EASYAIOT_ENABLE_TDENGINE=0
            export EASYAIOT_ENABLE_EMQX=1
            ;;
        standard)
            export EASYAIOT_ENABLE_TDENGINE=0
            export EASYAIOT_ENABLE_EMQX=1
            ;;
        full)
            export EASYAIOT_ENABLE_TDENGINE=1
            export EASYAIOT_ENABLE_EMQX=1
            ;;
    esac
}

device_service_enabled() {
    local svc="$1"
    local skip enabled e
    for skip in $(device_skipped_services); do
        [ "$svc" = "$skip" ] && return 1
    done
    enabled="$(device_enabled_services)"
    if [ -n "$enabled" ]; then
        for e in $enabled; do
            [ "$svc" = "$e" ] && return 0
        done
        return 1
    fi
    return 0
}

log_unit_enabled() {
    local unit="$1"
    local svc
    case "$unit" in
        mw-*)
            [ "$unit" = "mw-install-logs" ] && return 0
            svc="${UNIT_COMPOSE_SERVICE[$unit]:-}"
            [ -n "$svc" ] || return 1
            middleware_service_enabled "$svc"
            ;;
        dev-*)
            svc="${UNIT_COMPOSE_SERVICE[$unit]:-}"
            [ -n "$svc" ] || return 1
            device_service_enabled "$svc"
            ;;
        biz-ai) module_enabled_for_deploy_profile AI ;;
        biz-rtc) module_enabled_for_deploy_profile RTC ;;
        biz-video) module_enabled_for_deploy_profile VIDEO ;;
        biz-web) module_enabled_for_deploy_profile WEB ;;
        biz-app) module_enabled_for_deploy_profile APP ;;
        biz-visualize) module_enabled_for_deploy_profile VISUALIZE ;;
        *) return 1 ;;
    esac
}

enabled_units_list() {
    # 必须与 print_unit_menu 的编号顺序一致：中间件 → DEVICE → 业务
    local u
    for u in "${ALL_LOG_UNITS[@]}"; do
        [[ "$u" == mw-* ]] || continue
        log_unit_enabled "$u" && echo "$u"
    done
    for u in "${ALL_LOG_UNITS[@]}"; do
        [[ "$u" == dev-* ]] || continue
        log_unit_enabled "$u" && echo "$u"
    done
    for u in "${ALL_LOG_UNITS[@]}"; do
        [[ "$u" == biz-* ]] || continue
        log_unit_enabled "$u" && echo "$u"
    done
}

_expand_legacy_module() {
    local token="$1"
    local pair key val
    for pair in "${LEGACY_MODULE_EXPAND[@]}"; do
        key="${pair%%:*}"
        val="${pair#*:}"
        if [ "$token" = "$key" ]; then
            echo "$val"
            return 0
        fi
    done
    return 1
}

_unit_is_known() {
    local u="$1"
    [ -n "${UNIT_DISPLAY[$u]:-}" ]
}

_append_unit_if_enabled() {
    local u="$1"
    _unit_is_known "$u" || return 1
    log_unit_enabled "$u" || return 1
    local existing
    for existing in "${SELECTED_UNITS[@]}"; do
        [ "$existing" = "$u" ] && return 0
    done
    SELECTED_UNITS+=("$u")
}

_add_modules_token() {
    local token="$1"
    local expanded sub
    token="$(echo "$token" | xargs)"
    [ -z "$token" ] && return 0

    if expanded="$(_expand_legacy_module "$token" 2>/dev/null)"; then
        IFS=',' read -ra subs <<< "$expanded"
        for sub in "${subs[@]}"; do
            _append_unit_if_enabled "$sub" || print_warn "跳过未启用/未知子服务: $sub"
        done
        return 0
    fi

    if _unit_is_known "$token"; then
        _append_unit_if_enabled "$token" || print_warn "单元 $token 在当前部署形态下未启用，已跳过"
        return 0
    fi

    print_err "未知模块/单元: $token"
    exit 2
}

print_unit_menu() {
    local idx=1 u section=""
    init_deploy_profile_for_logs
    echo "当前部署形态: $(_deploy_profile_desc) (${EASYAIOT_DEPLOY_PROFILE})"
    echo ""
    echo "可选日志源（基础服务与 DEVICE 已按 docker-compose 拆分；多选用逗号，0=全部）:"
    echo ""

    for u in $(enabled_units_list); do
        case "$u" in
            mw-*)
                if [ "$section" != "mw" ]; then
                    echo "--- 基础服务（中间件，按 compose 服务）---"
                    section="mw"
                fi
                ;;
            dev-*)
                if [ "$section" != "dev" ]; then
                    echo ""
                    echo "--- DEVICE 微服务（按 compose 服务）---"
                    section="dev"
                fi
                ;;
            biz-*)
                if [ "$section" != "biz" ]; then
                    echo ""
                    echo "--- 业务模块 ---"
                    section="biz"
                fi
                ;;
        esac
        printf "  %d) %s\n" "$idx" "${UNIT_DISPLAY[$u]}"
        idx=$((idx + 1))
    done
    echo ""
    echo "  0) 全部已启用日志源"
    if [ "${EASYAIOT_LOG_FROM_MENU:-0}" = "1" ]; then
        echo "  b) 返回【分析】菜单"
    else
        echo "  b) 退出"
    fi
    echo ""
}

resolve_unit_by_index() {
    local choice="$1"
    local idx=1
    local u
    for u in $(enabled_units_list); do
        if [ "$idx" -eq "$choice" ]; then
            echo "$u"
            return 0
        fi
        idx=$((idx + 1))
    done
    return 1
}

interactive_select_units() {
    LOG_MENU_BACK=0
    init_deploy_profile_for_logs
    print_unit_menu
    local input=""
    read -r -p "请输入选项 [例如 1,3,5 或 0，b=返回]: " input || input=""
    input="$(echo "$input" | tr -d '[:space:]')"
    if [ -z "$input" ]; then
        return 1
    fi
    if [ "$input" = "b" ] || [ "$input" = "B" ]; then
        LOG_MENU_BACK=1
        return 0
    fi

    SELECTED_UNITS=()
    if [ "$input" = "0" ] || [ "$input" = "all" ] || [ "$input" = "ALL" ]; then
        local u
        for u in $(enabled_units_list); do
            SELECTED_UNITS+=("$u")
        done
        return 0
    fi

    local part u had_error=0
    IFS=',' read -ra parts <<< "$input"
    for part in "${parts[@]}"; do
        [ -z "$part" ] && continue
        if [[ "$part" =~ ^[0-9]+$ ]]; then
            u="$(resolve_unit_by_index "$part" || true)"
            if [ -z "$u" ]; then
                print_err "无效序号: $part"
                had_error=1
                continue
            fi
            _append_unit_if_enabled "$u"
        else
            _add_modules_token "$part" || had_error=1
        fi
    done
    if [ "$had_error" -eq 1 ] && [ ${#SELECTED_UNITS[@]} -eq 0 ]; then
        return 1
    fi
    return 0
}

parse_modules_arg() {
    local arg="$1"
    SELECTED_UNITS=()
    if [ "$arg" = "all" ] || [ "$arg" = "ALL" ]; then
        local u
        for u in $(enabled_units_list); do
            SELECTED_UNITS+=("$u")
        done
        return 0
    fi
    local part
    IFS=',' read -ra parts <<< "$arg"
    for part in "${parts[@]}"; do
        _add_modules_token "$part"
    done
}

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --modules)
                shift
                parse_modules_arg "${1:-}"
                INTERACTIVE=false
                ;;
            --lines)
                shift
                LOG_TAIL_LINES="${1:-500}"
                ;;
            --save)
                SAVE_OUTPUT=true
                ;;
            --non-interactive)
                INTERACTIVE=false
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_err "未知参数: $1"
                show_help
                exit 2
                ;;
        esac
        shift
    done
}

container_exists() {
    docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$1"
}

docker_usable() {
    command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

tail_log_file() {
    local file="$1"
    local lines="$2"

    if [[ "$file" == *.gz ]]; then
        if command -v zcat >/dev/null 2>&1; then
            zcat "$file" 2>/dev/null | tail -n "$lines"
        elif command -v gzip >/dev/null 2>&1; then
            gzip -dc "$file" 2>/dev/null | tail -n "$lines"
        else
            print_warn "无法解压 gzip 日志: $file（缺少 zcat/gzip）"
            return 1
        fi
    else
        tail -n "$lines" "$file" 2>/dev/null
    fi
}

find_newest_log_file() {
    local dir="$1"
    local pattern="$2"
    local maxdepth="${3:-4}"
    local newest=""
    local active_base=""

    [ -d "$dir" ] || return 1

    # 如 sink-server.log* → 优先未滚动的 sink-server.log（Spring 当前写入文件）
    # 通配符开头的 *.log 等递归模式不适用此规则
    if [[ "$pattern" == *.log* ]] && [[ "$pattern" != \** ]]; then
        active_base="${pattern%.log*}.log"
        if [ -f "${dir}/${active_base}" ] && [ -s "${dir}/${active_base}" ]; then
            printf '%s\n' "${dir}/${active_base}"
            return 0
        fi
    fi

    if command -v find >/dev/null 2>&1; then
        newest="$(
            find "$dir" -maxdepth "$maxdepth" -type f -name "$pattern" -printf '%T@ %p\n' 2>/dev/null \
                | sort -rn \
                | head -1 \
                | awk '{ $1=""; sub(/^ /,""); print }'
        )"
    fi

    if [ -z "$newest" ]; then
        local f ts best_ts=0
        for f in "$dir"/$pattern; do
            [ -f "$f" ] || continue
            ts="$(stat -c %Y "$f" 2>/dev/null || echo 0)"
            if [ "$ts" -ge "$best_ts" ]; then
                best_ts="$ts"
                newest="$f"
            fi
        done
    fi

    [ -n "$newest" ] && [ -f "$newest" ] || return 1
    printf '%s\n' "$newest"
}

collect_latest_file_logs() {
    local dir="$1"
    local lines="$2"
    local pattern="${3:-*.log}"
    local maxdepth="${4:-4}"
    local newest

    newest="$(find_newest_log_file "$dir" "$pattern" "$maxdepth" || true)"
    [ -n "$newest" ] || return 1

    echo "--- 文件: ${newest} (最新日志文件，最近 ${lines} 行，含 INFO/WARN/ERROR 等全部级别) ---"
    tail_log_file "$newest" "$lines" || true
    echo ""
    return 0
}

collect_container_logs() {
    local container="$1"
    local lines="$2"
    local tmp

    docker_usable || return 1

    tmp="$(mktemp)"
    if docker logs --tail="$lines" --timestamps "$container" >"$tmp" 2>&1; then
        if [ -s "$tmp" ]; then
            echo "--- 容器: ${container} (docker logs 最近 ${lines} 行，含全部级别) ---"
            cat "$tmp"
            echo ""
            rm -f "$tmp"
            return 0
        fi
    fi
    rm -f "$tmp"
    return 1
}

collect_compose_service_logs() {
    local compose_file="$1"
    local service="$2"
    local lines="$3"
    local compose_dir compose_base tmp

    docker_usable || return 1
    [ -f "$compose_file" ] || return 1

    compose_dir="$(cd "$(dirname "$compose_file")" && pwd)"
    compose_base="$(basename "$compose_file")"
    tmp="$(mktemp)"

    if (
        cd "$compose_dir" || exit 1
        docker compose -f "$compose_base" logs --no-color --tail="$lines" "$service" 2>/dev/null
    ) >"$tmp"; then
        if [ -s "$tmp" ]; then
            echo "--- compose 服务: ${service} (${compose_base} 最近 ${lines} 行，含全部级别) ---"
            cat "$tmp"
            echo ""
            rm -f "$tmp"
            return 0
        fi
    fi
    rm -f "$tmp"
    return 1
}

collect_biz_video_compose_logs() {
    local lines="$1"
    local found=0
    local svc compose_file

    local -a video_sub_services=(
        "pusher-service|${PROJECT_ROOT}/VIDEO/services/pusher_service/docker-compose.yaml"
        "sorter-service|${PROJECT_ROOT}/VIDEO/services/sorter_service/docker-compose.yaml"
        "frame-extractor-service|${PROJECT_ROOT}/VIDEO/services/frame_extractor_service/docker-compose.yaml"
    )

    for svc in "${video_sub_services[@]}"; do
        compose_file="${svc#*|}"
        svc="${svc%%|*}"
        if collect_compose_service_logs "$compose_file" "$svc" "$lines"; then
            found=1
        fi
    done
    [ "$found" -eq 1 ]
}

collect_biz_video_subservice_file_logs() {
    local lines="$1"
    local found=0 rel_dir dir

    local sub_services=(
        "pusher_service"
        "sorter_service"
        "frame_extractor_service"
    )

    for rel_dir in "${sub_services[@]}"; do
        dir="${PROJECT_ROOT}/VIDEO/services/${rel_dir}/logs"
        [ -d "$dir" ] || continue
        if collect_latest_file_logs "$dir" "$lines" "*.log" 6; then
            found=1
        fi
    done
    [ "$found" -eq 1 ]
}

collect_biz_video_file_logs() {
    local lines="$1"
    local found=0

    # 算法任务 / 推流任务等按 task 分目录的日期日志（如 logs/task_1/2026-07-07.log）
    if collect_latest_file_logs "${PROJECT_ROOT}/VIDEO/logs" "$lines" "*.log" 12; then
        found=1
    fi

    if collect_biz_video_subservice_file_logs "$lines"; then
        found=1
    fi

    [ "$found" -eq 1 ]
}

collect_biz_ai_file_logs() {
    local lines="$1"
    local found=0

    # LLM 子服务等：AI/logs/llm/<id>/llm-service.log
    if collect_latest_file_logs "${PROJECT_ROOT}/AI/logs" "$lines" "*.log" 12; then
        found=1
    fi

    [ "$found" -eq 1 ]
}

collect_unit_file_logs() {
    local unit="$1"
    local lines="$2"
    local spec dir pattern found=0

    spec="${UNIT_LOG_FILE_SPEC[$unit]:-}"
    if [ -n "$spec" ]; then
        dir="${spec%%|*}"
        pattern="${spec#*|}"
        local search_depth=4
        if [[ "$unit" == biz-video ]] || [[ "$unit" == biz-ai ]]; then
            search_depth=12
        fi
        if collect_latest_file_logs "$dir" "$lines" "$pattern" "$search_depth"; then
            found=1
        elif [ "$unit" = "dev-iot-gb28181" ]; then
            collect_latest_file_logs "$dir" "$lines" "iot-gb28181-*.log.gz" 6 && found=1
        fi
    fi

    local file_dir="${UNIT_FILE_LOG_DIRS[$unit]:-}"
    if [ -n "$file_dir" ]; then
        if [ "$unit" = "mw-nacos" ]; then
            collect_latest_file_logs "$file_dir" "$lines" "nacos.log*" && found=1
        elif [ "$unit" = "mw-install-logs" ]; then
            collect_latest_file_logs "$file_dir" "$lines" "install_linux*.log" && found=1
            if [ "$found" -eq 0 ]; then
                collect_latest_file_logs "$file_dir" "$lines" "*.log" && found=1
            fi
        else
            collect_latest_file_logs "$file_dir" "$lines" "*.log" && found=1
        fi
    fi

    if [ "$unit" = "biz-video" ]; then
        if collect_biz_video_file_logs "$lines"; then
            found=1
        fi
    fi

    if [ "$unit" = "biz-ai" ]; then
        if collect_biz_ai_file_logs "$lines"; then
            found=1
        fi
    fi

    [ "$found" -eq 1 ]
}

collect_unit_logs() {
    local unit="$1"
    local lines="$2"
    local found=0
    local c container compose_file service
    local docker_had_content=0

    for c in ${UNIT_CONTAINERS[$unit]:-}; do
        if collect_container_logs "$c" "$lines"; then
            found=1
            docker_had_content=1
        fi
    done

    if [ "$docker_had_content" -eq 0 ]; then
        compose_file="${UNIT_COMPOSE_FILE[$unit]:-}"
        service="${UNIT_COMPOSE_SERVICE[$unit]:-}"
        if [ -n "$compose_file" ] && [ -n "$service" ]; then
            if collect_compose_service_logs "$compose_file" "$service" "$lines"; then
                found=1
            fi
        fi
        if [ "$unit" = "biz-video" ]; then
            if collect_biz_video_compose_logs "$lines"; then
                found=1
            fi
        fi
    fi

    if [ "$docker_had_content" -eq 0 ] || [[ "$unit" == dev-* ]] || [[ "$unit" == biz-* ]]; then
        if collect_unit_file_logs "$unit" "$lines"; then
            found=1
        fi
    fi

    if [ "$found" -eq 0 ]; then
        print_warn "单元 ${unit} (${UNIT_DISPLAY[$unit]:-$unit}) 未发现容器或本地日志。"
        print_info "  容器名: ${UNIT_CONTAINERS[$unit]:-无}  |  可先执行 ./install_linux.sh status 确认服务状态"
        local spec_hint="${UNIT_LOG_FILE_SPEC[$unit]:-}"
        if [ -n "$spec_hint" ]; then
            print_info "  本地日志: ${spec_hint%%|*} （${spec_hint#*|}）"
        fi
        case "$unit" in
            biz-video)
                print_info "  本地日志: ${PROJECT_ROOT}/VIDEO/logs （*.log，含 task_*/日期.log）"
                print_info "  说明: video-service 主进程日志在 docker；算法/推流任务日志在 VIDEO/logs/<task_id>/ 下按日期分文件"
                ;;
            biz-ai)
                print_info "  本地日志: ${PROJECT_ROOT}/AI/logs （*.log，含 llm/<id>/llm-service.log）"
                print_info "  说明: ai-service 主进程日志在 docker；LLM 等子服务可能在 AI/logs/ 下"
                ;;
        esac
    fi
}

scan_error_summary() {
    local content="$1"
    local label="$2"
    echo "$content" | grep -Ei 'error|exception|fatal|panic|failed|失败|异常|crash|segfault|oom|killed|timeout|refused|denied' \
        | sed 's/^[[:space:]]*//' \
        | tail -n 20 \
        | while IFS= read -r line; do
            [ -n "$line" ] && echo "  [${label}] ${line}"
        done || true
}

run_analysis_once() {
    if [ ${#SELECTED_UNITS[@]} -eq 0 ]; then
        print_err "未选择任何日志源"
        return 1
    fi

    if ! command -v docker >/dev/null 2>&1; then
        print_warn "未检测到 docker 命令，将优先尝试读取本地日志文件"
    elif ! docker info >/dev/null 2>&1; then
        print_warn "无法连接 Docker daemon，将优先尝试读取本地日志文件"
    fi

    local output_file=""
    if [ "$SAVE_OUTPUT" = true ]; then
        mkdir -p "${SCRIPT_DIR}/logs"
        output_file="${SCRIPT_DIR}/logs/merged_logs_$(date +%Y%m%d_%H%M%S).log"
        print_info "合并结果将保存到: $output_file"
    fi

    local merged="" summary=""
    local blocks=() headers=()
    local total="${#SELECTED_UNITS[@]}"
    local i=0 unit block header_buf label

    print_section "开始采集日志（每源最近 ${LOG_TAIL_LINES} 行完整日志，含 INFO/WARN/ERROR 等全部级别，共 ${total} 个服务/单元）"

    for unit in "${SELECTED_UNITS[@]}"; do
        i=$((i + 1))
        label="${UNIT_DISPLAY[$unit]:-$unit}"
        block="$(mktemp)"
        {
            collect_unit_logs "$unit" "$LOG_TAIL_LINES"
        } > "$block" 2>&1
        blocks+=("$block")
        header_buf="================================================================================
【${i}/${total}】${label}
单元 ID: ${unit}
采集时间: $(date '+%Y-%m-%d %H:%M:%S')
================================================================================"
        headers+=("$header_buf")
        merged+="${header_buf}"$'\n\n'"$(cat "$block")"$'\n\n'
        summary+=$(scan_error_summary "$(cat "$block")" "$label")
        summary+=$'\n'
    done

    print_section "错误/异常摘要（自动扫描，供快速定位）"
    if [ -n "$(echo "$summary" | sed '/^[[:space:]]*$/d')" ]; then
        echo "$summary" | sed '/^[[:space:]]*$/d' | tail -n 50
        print_warn "以上摘要由关键字自动匹配，请结合下方完整日志确认根因。"
    else
        print_ok "未在采集范围内发现明显的 ERROR/Exception/failed 等关键字（不代表绝对无问题）。"
    fi

    print_section "合并日志正文（服务间有明显分割线）"
    i=0
    for unit in "${SELECTED_UNITS[@]}"; do
        i=$((i + 1))
        [ "$i" -gt 1 ] && print_unit_separator
        echo "${headers[$((i - 1))]}"
        echo ""
        cat "${blocks[$((i - 1))]}"
    done

    for block in "${blocks[@]}"; do
        rm -f "$block"
    done

    if [ -n "$output_file" ]; then
        {
            echo "EasyAIoT 多模块日志合并报告"
            echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "部署形态: ${EASYAIOT_DEPLOY_PROFILE:-unknown}"
            echo "采集单元: ${SELECTED_UNITS[*]}"
            echo "每源行数: ${LOG_TAIL_LINES}"
            echo ""
            echo "========== 错误/异常摘要 =========="
            echo "$summary"
            echo ""
            echo "========== 完整合并日志 =========="
            echo "$merged"
        } > "$output_file"
        print_ok "已保存合并日志: $output_file"
        print_info "可将该文件直接提供给技术支持人员分析。"
    fi

    print_section "日志合并分析完成"
}

run_interactive_loop() {
    while true; do
        SELECTED_UNITS=()
        if ! interactive_select_units; then
            continue
        fi
        if [ "${LOG_MENU_BACK:-0}" = "1" ]; then
            break
        fi
        if [ ${#SELECTED_UNITS[@]} -eq 0 ]; then
            continue
        fi
        run_analysis_once
        echo ""
    done
}

main() {
    init_deploy_profile_for_logs
    parse_args "$@"
    if [ "$INTERACTIVE" = true ] && [ ${#SELECTED_UNITS[@]} -eq 0 ]; then
        run_interactive_loop
    elif [ ${#SELECTED_UNITS[@]} -eq 0 ]; then
        print_err "未选择任何日志源，请使用 --modules 或在交互模式下选择"
        exit 2
    else
        run_analysis_once
    fi
}

main "$@"
