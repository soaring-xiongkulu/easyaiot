#!/bin/bash
# ============================================
# EasyAIoT 容器内存占用分析
# ============================================
# 统计当前运行中的中间件与业务容器实际内存占用，
# 并与 mini / standard / full 三种部署规格的推荐上限对比。
#
# 用法:
#   ./analyze_deploy_memory.sh              # 使用已保存的部署规格作为基准
#   ./analyze_deploy_memory.sh --profile mini
#   ./analyze_deploy_memory.sh --all-profiles
#   ./analyze_deploy_memory.sh --json
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"

JSON_OUTPUT=false
SHOW_ALL_PROFILES=false
TARGET_PROFILE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON_OUTPUT=true ;;
        --all-profiles) SHOW_ALL_PROFILES=true ;;
        --profile)
            shift
            TARGET_PROFILE="${1:-}"
            ;;
        -h|--help)
            cat <<'EOF'
用法: ./analyze_deploy_memory.sh [选项]

选项:
  --profile <mini|standard|full>  指定对比基准规格（默认读取 .deploy_profile）
  --all-profiles                  同时展示三种规格的符合性判定
  --json                          以 JSON 输出（便于自动化采集）
  -h, --help                      显示帮助

说明:
  容器内存取自 docker stats 的 RSS 用量（运行中容器）。
  规格上限取自 deploy_profile.sh 中的推荐值：mini 4 GB / standard 16 GB / full 20 GB。
EOF
            exit 0
            ;;
        *)
            echo "未知参数: $1" >&2
            exit 2
            ;;
    esac
    shift
done

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

MIDDLEWARE_CONTAINERS=(
    nacos-server postgres-server postgres-init redis-server kafka-server
    minio-server milvus-server srs-server nodered-server fuxa-server emqx-server
    zlmediakit-server tdengine-server tdengine-init
)
DEVICE_CONTAINERS=(
    iot-gateway iot-system iot-infra iot-device iot-dataset iot-node
    iot-visualize iot-tdengine iot-file iot-message iot-sink iot-gb28181
)
APP_CONTAINERS=(
    ai-service rtc-service video-service web-service app-service
    pusher-service sorter-service frame-extractor-service
)

mem_usage_to_mib() {
    local raw="${1%%/*}"
    raw="${raw// /}"
    local num unit
    # docker stats 常见格式如 155.7MiB、8.004MiB；勿用 %[*] 剥单位，会把 MiB 误拆成 Mi+B
    if [[ "$raw" =~ ^([0-9]+\.?[0-9]*)(TiB|GiB|MiB|KiB|TB|GB|MB|kB|B)$ ]]; then
        num="${BASH_REMATCH[1]}"
        unit="${BASH_REMATCH[2]}"
    else
        echo "0"
        return
    fi
    case "$unit" in
        B)       awk -v n="$num" 'BEGIN { printf "%.2f", n/1024/1024 }' ;;
        KiB|kB)  awk -v n="$num" 'BEGIN { printf "%.2f", n/1024 }' ;;
        MiB|MB)  echo "$num" ;;
        GiB|GB)  awk -v n="$num" 'BEGIN { printf "%.2f", n*1024 }' ;;
        TiB|TB)  awk -v n="$num" 'BEGIN { printf "%.2f", n*1024*1024 }' ;;
        *)       echo "0" ;;
    esac
}

mib_to_gb() {
    awk -v m="$1" 'BEGIN { printf "%.2f", m/1024 }'
}

format_mib() {
    local mib="$1"
    if awk -v m="$mib" 'BEGIN { exit (m >= 1024) ? 0 : 1 }'; then
        printf "%.2f GB" "$(mib_to_gb "$mib")"
    else
        printf "%.0f MiB" "$mib"
    fi
}

array_contains() {
    local needle="$1"
    shift
    local item
    for item in "$@"; do
        [ "$item" = "$needle" ] && return 0
    done
    return 1
}

classify_container() {
    local name="$1"
    if array_contains "$name" "${MIDDLEWARE_CONTAINERS[@]}"; then
        echo "middleware"
    elif array_contains "$name" "${DEVICE_CONTAINERS[@]}"; then
        echo "device"
    elif array_contains "$name" "${APP_CONTAINERS[@]}"; then
        echo "app"
    else
        echo "other"
    fi
}

read_host_memory_mib() {
    if [ ! -f /proc/meminfo ]; then
        echo "0 0 0"
        return
    fi
    local total_kb avail_kb
    total_kb=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
    avail_kb=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
    local used_kb=$((total_kb - avail_kb))
    awk -v t="$total_kb" -v u="$used_kb" -v a="$avail_kb" \
        'BEGIN { printf "%.2f %.2f %.2f", t/1024, u/1024, a/1024 }'
}

collect_running_easyaiot_containers() {
    local -a found=()
    local name

    if docker network inspect easyaiot-network >/dev/null 2>&1; then
        while IFS= read -r name; do
            [ -n "$name" ] && found+=("$name")
        done < <(docker ps --filter network=easyaiot-network --format '{{.Names}}' 2>/dev/null | sort -u)
    fi

    local all_known=("${MIDDLEWARE_CONTAINERS[@]}" "${DEVICE_CONTAINERS[@]}" "${APP_CONTAINERS[@]}")
    for name in "${all_known[@]}"; do
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$name"; then
            if ! array_contains "$name" "${found[@]+"${found[@]}"}"; then
                found+=("$name")
            fi
        fi
    done

    if [ "${#found[@]}" -eq 0 ]; then
        return 1
    fi
    printf '%s\n' "${found[@]}" | sort -u
}

infer_profile_from_containers() {
    local -a running=("$@")
    local name

    for name in "${running[@]}"; do
        case "$name" in
            tdengine-server|nodered-server|iot-visualize|fuxa-server)
                echo "full"
                return 0
                ;;
        esac
    done

    for name in "${running[@]}"; do
        case "$name" in
            iot-device|iot-tdengine|iot-dataset|iot-node|iot-file|iot-message|iot-sink|iot-gb28181)
                echo "standard"
                return 0
                ;;
        esac
    done

    local has_core_device=false
    for name in "${running[@]}"; do
        case "$name" in
            iot-system) has_core_device=true ;;
        esac
    done
    if $has_core_device; then
        echo "mini"
        return 0
    fi

    echo "unknown"
}

profile_budget_check() {
    local total_mib="$1"
    local profile="$2"
    local budget
    budget=$(deploy_profile_budget_mib "$profile")
    awk -v t="$total_mib" -v b="$budget" 'BEGIN { exit (t <= b) ? 0 : 1 }'
}

resolve_target_profile() {
    if [ -n "$TARGET_PROFILE" ]; then
        case "$TARGET_PROFILE" in
            1|mini) echo "mini" ;;
            2|standard) echo "standard" ;;
            3|full) echo "full" ;;
            *) print_err "无效规格: $TARGET_PROFILE"; exit 2 ;;
        esac
        return
    fi
    load_saved_deploy_profile
    apply_deploy_profile
    echo "${EASYAIOT_DEPLOY_PROFILE:-full}"
}

json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

bool_within_budget() {
    profile_budget_check "$1" "$2" && echo "true" || echo "false"
}

emit_json_report() {
    local target_profile="$1"
    local inferred_profile="$2"
    local total_mib="$3"
    local mw_mib="$4"
    local dev_mib="$5"
    local app_mib="$6"
    local other_mib="$7"
    local host_total_mib="$8"
    local host_used_mib="$9"
    local host_avail_mib="${10}"
    shift 10
    local -a containers=("$@")

    local lines="["
    local first=true
    local name mib raw class
    for name in "${containers[@]}"; do
        mib="${MEM_MIB[$name]:-0}"
        raw="${MEM_RAW[$name]:-}"
        class=$(classify_container "$name")
        $first || lines+=","
        first=false
        lines+=$(printf '{"name":"%s","mib":%s,"usage":"%s","category":"%s"}' \
            "$(json_escape "$name")" "$mib" "$(json_escape "$raw")" "$(json_escape "$class")")
    done
    lines+="]"

    local profiles_json
    profiles_json=$(cat <<EOF
{
  "mini": {"budget_mib": 4096, "within_budget": $(bool_within_budget "$total_mib" mini), "headroom_mib": $(awk -v b=4096 -v t="$total_mib" 'BEGIN { printf "%.2f", b-t }')},
  "standard": {"budget_mib": 16384, "within_budget": $(bool_within_budget "$total_mib" standard), "headroom_mib": $(awk -v b=16384 -v t="$total_mib" 'BEGIN { printf "%.2f", b-t }')},
  "full": {"budget_mib": 20480, "within_budget": $(bool_within_budget "$total_mib" full), "headroom_mib": $(awk -v b=20480 -v t="$total_mib" 'BEGIN { printf "%.2f", b-t }')}
}
EOF
)

    cat <<EOF
{
  "target_profile": "$target_profile",
  "inferred_profile": "$inferred_profile",
  "host": {
    "total_mib": $host_total_mib,
    "used_mib": $host_used_mib,
    "available_mib": $host_avail_mib
  },
  "totals_mib": {
    "all": $total_mib,
    "middleware": $mw_mib,
    "device": $dev_mib,
    "app": $app_mib,
    "other": $other_mib
  },
  "profiles": $profiles_json,
  "containers": $lines
}
EOF
}

declare -A MEM_MIB=()
declare -A MEM_RAW=()

main() {
    if ! command -v docker >/dev/null 2>&1; then
        print_err "未找到 docker 命令"
        exit 1
    fi
    if ! docker info >/dev/null 2>&1; then
        print_err "无法连接 Docker daemon"
        exit 1
    fi

    local -a containers=()
    while IFS= read -r line; do
        [ -n "$line" ] && containers+=("$line")
    done < <(collect_running_easyaiot_containers || true)

    if [ "${#containers[@]}" -eq 0 ]; then
        if $JSON_OUTPUT; then
            echo '{"error":"no_running_containers"}'
        else
            print_warn "未发现运行中的 EasyAIoT 容器（easyaiot-network 或已知容器名）"
        fi
        exit 1
    fi

    local host_mem
    host_mem=$(read_host_memory_mib)
    local host_total_mib host_used_mib host_avail_mib
    read -r host_total_mib host_used_mib host_avail_mib <<< "$host_mem"

    local name stats_line mib class
    local total_mib=0
    local mw_mib=0 dev_mib=0 app_mib=0 other_mib=0

    for name in "${containers[@]}"; do
        stats_line=$(docker stats --no-stream --format '{{.MemUsage}}' "$name" 2>/dev/null || echo "")
        [ -z "$stats_line" ] && continue
        mib=$(mem_usage_to_mib "$stats_line")
        MEM_MIB["$name"]="$mib"
        MEM_RAW["$name"]="${stats_line%%/*}"
        total_mib=$(awk -v a="$total_mib" -v b="$mib" 'BEGIN { printf "%.2f", a+b }')
        class=$(classify_container "$name")
        case "$class" in
            middleware) mw_mib=$(awk -v a="$mw_mib" -v b="$mib" 'BEGIN { printf "%.2f", a+b }') ;;
            device)     dev_mib=$(awk -v a="$dev_mib" -v b="$mib" 'BEGIN { printf "%.2f", a+b }') ;;
            app)        app_mib=$(awk -v a="$app_mib" -v b="$mib" 'BEGIN { printf "%.2f", a+b }') ;;
            *)          other_mib=$(awk -v a="$other_mib" -v b="$mib" 'BEGIN { printf "%.2f", a+b }') ;;
        esac
    done

    local target_profile inferred_profile
    target_profile=$(resolve_target_profile)
    inferred_profile=$(infer_profile_from_containers "${containers[@]}")

    if $JSON_OUTPUT; then
        emit_json_report "$target_profile" "$inferred_profile" \
            "$total_mib" "$mw_mib" "$dev_mib" "$app_mib" "$other_mib" \
            "$host_total_mib" "$host_used_mib" "$host_avail_mib" \
            "${containers[@]}"
        profile_budget_check "$total_mib" "$target_profile"
        exit $?
    fi

    print_section "宿主机内存"
    print_info "总内存:     $(format_mib "$host_total_mib")"
    print_info "已用内存:   $(format_mib "$host_used_mib")（含系统及其他进程）"
    print_info "可用内存:   $(format_mib "$host_avail_mib")"

    print_section "运行容器内存明细（${#containers[@]} 个）"
    printf "  %-28s %-12s %-10s\n" "容器" "占用" "分类"
    printf "  %-28s %-12s %-10s\n" "----------------------------" "------------" "----------"

    local sorted line _mib _name
    sorted=$(for name in "${containers[@]}"; do
        printf '%s %s\n' "${MEM_MIB[$name]:-0}" "$name"
    done | sort -rn)

    while read -r line; do
        [ -z "$line" ] && continue
        _mib="${line%% *}"
        _name="${line#* }"
        class=$(classify_container "$_name")
        case "$class" in
            middleware) class="中间件" ;;
            device)     class="DEVICE" ;;
            app)        class="业务应用" ;;
            *)          class="其他" ;;
        esac
        printf "  %-28s %-12s %-10s\n" "$_name" "${MEM_RAW[$_name]}" "$class"
    done <<< "$sorted"

    print_section "分类汇总"
    print_info "中间件合计:   $(format_mib "$mw_mib")"
    print_info "DEVICE 合计:  $(format_mib "$dev_mib")"
    print_info "业务应用合计: $(format_mib "$app_mib")"
    if awk -v o="$other_mib" 'BEGIN { exit (o > 0.01) ? 0 : 1 }'; then
        print_info "其他容器合计: $(format_mib "$other_mib")"
    fi
    echo ""
    print_info "EasyAIoT 容器总占用: $(format_mib "$total_mib")"

    print_section "部署规格符合性"
    load_saved_deploy_profile
    apply_deploy_profile
    print_info "已保存规格:   $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE:-未设置})"
    print_info "运行态推断:   ${inferred_profile}"
    print_info "本次对比基准: ${target_profile}（上限 $(deploy_profile_budget_label "$target_profile")）"
    echo ""

    local profile p_label headroom status
    local -a profiles_to_show=(mini standard full)
    if ! $SHOW_ALL_PROFILES; then
        profiles_to_show=("$target_profile")
    fi

    local overall_ok=true
    for profile in "${profiles_to_show[@]}"; do
        p_label=$(deploy_profile_budget_label "$profile")
        headroom=$(awk -v b="$(deploy_profile_budget_mib "$profile")" -v t="$total_mib" \
            'BEGIN { printf "%.2f", b-t }')
        if profile_budget_check "$total_mib" "$profile"; then
            status="${GREEN}符合${NC}"
        else
            status="${RED}超出${NC}"
            [ "$profile" = "$target_profile" ] && overall_ok=false
        fi
        printf "  %-10s 上限 %-6s  容器占用 %-10s  余量 %-10s  %b\n" \
            "$profile" "$p_label" "$(format_mib "$total_mib")" "$(format_mib "$headroom")" "$status"
    done

    echo ""
    if profile_budget_check "$total_mib" "$target_profile"; then
        print_ok "当前容器总占用在 ${target_profile} 规格（$(deploy_profile_budget_label "$target_profile")）范围内"
    else
        local over
        over=$(awk -v t="$total_mib" -v b="$(deploy_profile_budget_mib "$target_profile")" \
            'BEGIN { printf "%.2f", t-b }')
        print_warn "当前容器总占用超出 ${target_profile} 规格上限 $(format_mib "$over")"
        print_info "建议: 升级至更高规格，或停止非必要服务后重试"
    fi

    if [ "$inferred_profile" != "unknown" ] && [ "$inferred_profile" != "$target_profile" ]; then
        print_warn "运行中的服务组合更接近 ${inferred_profile} 规格，与已保存/指定规格 ${target_profile} 不一致"
        print_info "可执行 ./install_middleware_linux.sh profile 查看规格详情"
    fi

    if awk -v a="$host_avail_mib" -v t="$total_mib" 'BEGIN { exit (a < t * 0.15) ? 0 : 1 }'; then
        print_warn "宿主机可用内存偏低，容器扩容或业务高峰时存在 OOM 风险"
    fi

    if $overall_ok; then
        exit 0
    fi
    exit 1
}

main "$@"
