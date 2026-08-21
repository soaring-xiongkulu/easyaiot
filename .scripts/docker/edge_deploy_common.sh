#!/usr/bin/env bash
# EasyAIoT edge 双形态（install 规格选型内引导）
# 选项键为英文：standalone（纯边缘形态）/ integrated（云边一体形态）
#
# 导出：
#   EASYAIOT_EDGE_MORPHOLOGY=standalone|integrated
#   VIDEO_BASE_URL / GATEWAY_URL / MQTT_BROKER_URLS（integrated 交互填写时）

[[ -n "${EASYAIOT_EDGE_DEPLOY_COMMON_LOADED:-}" ]] && return 0
EASYAIOT_EDGE_DEPLOY_COMMON_LOADED=1

_edge_msg_info() {
    if declare -F print_info >/dev/null 2>&1; then
        print_info "$1"
    else
        echo "[INFO] $1"
    fi
}

_edge_msg_error() {
    if declare -F print_error >/dev/null 2>&1; then
        print_error "$1"
    else
        echo "[ERROR] $1" >&2
    fi
}

# 规范化边缘形态键：standalone|integrated（pure 为 standalone 别名）
normalize_edge_morphology() {
    case "${1:-}" in
        standalone|pure|pure-edge|site) echo "standalone" ;;
        integrated|cloud|cloud-edge|compute|compute-node) echo "integrated" ;;
        *) echo "" ;;
    esac
}

# integrated：交互收集中心汇聚面配置
prompt_cloud_edge_center_config() {
    local preset_url="${1:-}"
    local video_url gateway_url mqtt_urls

    if [ -n "$preset_url" ]; then
        export VIDEO_BASE_URL="$preset_url"
    fi
    video_url="${VIDEO_BASE_URL:-${EASYAIOT_VIDEO_BASE_URL:-}}"

    if [ -z "$video_url" ]; then
        if [ ! -t 0 ]; then
            _edge_msg_error "edge/integrated 需要中心汇聚面地址（请设置 VIDEO_BASE_URL）"
            return 1
        fi
        echo ""
        echo "edge / integrated — 请填写中心汇聚面地址"
        echo "  示例: http://192.168.1.10:6000"
        echo ""
        while true; do
            read -r -p "Center URL: " video_url
            video_url="$(echo "$video_url" | tr -d '[:space:]')"
            if [[ "$video_url" =~ ^https?://[^/[:space:]]+ ]]; then
                break
            fi
            echo "地址无效，请以 http:// 或 https:// 开头，例如 http://192.168.1.10:6000"
        done
        export VIDEO_BASE_URL="$video_url"
        export EASYAIOT_VIDEO_BASE_URL="$video_url"
    else
        export VIDEO_BASE_URL="$video_url"
        export EASYAIOT_VIDEO_BASE_URL="$video_url"
        _edge_msg_info "Center URL: ${video_url}"
    fi

    if [ -t 0 ]; then
        gateway_url="${GATEWAY_URL:-${EASYAIOT_GATEWAY_URL:-}}"
        if [ -z "$gateway_url" ]; then
            local host
            host="$(echo "$VIDEO_BASE_URL" | sed -E 's#^https?://([^:/]+).*#\1#')"
            echo ""
            read -r -p "Gateway URL [http://${host}:48080]: " gateway_url
            gateway_url="$(echo "$gateway_url" | tr -d '[:space:]')"
            if [ -z "$gateway_url" ]; then
                gateway_url="http://${host}:48080"
            fi
        fi
        export GATEWAY_URL="$gateway_url"
        export EASYAIOT_GATEWAY_URL="$gateway_url"

        mqtt_urls="${MQTT_BROKER_URLS:-}"
        if [ -z "$mqtt_urls" ]; then
            echo ""
            read -r -p "MQTT broker (optional, e.g. 192.168.1.10:1883): " mqtt_urls
            mqtt_urls="$(echo "$mqtt_urls" | tr -d '[:space:]')"
            if [ -n "$mqtt_urls" ]; then
                export MQTT_BROKER_URLS="$mqtt_urls"
            fi
        fi
        echo ""
        _edge_msg_info "Center:  ${VIDEO_BASE_URL}"
        _edge_msg_info "Gateway: ${GATEWAY_URL}"
        [ -n "${MQTT_BROKER_URLS:-}" ] && _edge_msg_info "MQTT:    ${MQTT_BROKER_URLS}"
        echo ""
    fi
    return 0
}

_print_edge_morphology_menu() {
    echo ""
    echo "Select edge mode:"
    echo "  1) standalone  — 纯边缘形态：汇聚面与算力同机，本地闭环（推荐 ≥ 2 GB）"
    echo "  2) integrated  — 云边一体形态：本机仅部署边缘算力，接入中心汇聚面"
    echo ""
}

# 已选 profile=edge 后，交互选择 standalone / integrated
select_edge_morphology_interactive() {
    local normalized
    normalized="$(normalize_edge_morphology "${EASYAIOT_EDGE_MORPHOLOGY:-}")"
    if [ -n "$normalized" ]; then
        export EASYAIOT_EDGE_MORPHOLOGY="$normalized"
        return 0
    fi

    if [ ! -t 0 ]; then
        export EASYAIOT_EDGE_MORPHOLOGY=standalone
        _edge_msg_info "非交互环境，默认 edge/standalone（纯边缘形态）"
        return 0
    fi

    _print_edge_morphology_menu
    local choice=""
    read -r -p "Enter choice [1-2, default 1]: " choice
    case "${choice:-1}" in
        2|integrated)
            export EASYAIOT_EDGE_MORPHOLOGY=integrated
            ;;
        1|standalone|pure|"")
            export EASYAIOT_EDGE_MORPHOLOGY=standalone
            ;;
        *)
            _edge_msg_error "无效选项: ${choice}"
            return 1
            ;;
    esac
    return 0
}

# install 流程内：确保 edge 已选定形态；integrated 时收集中心地址
ensure_edge_morphology_for_install() {
    case "${EASYAIOT_DEPLOY_PROFILE:-}" in
        edge) ;;
        *) return 0 ;;
    esac

    local normalized
    normalized="$(normalize_edge_morphology "${EASYAIOT_EDGE_MORPHOLOGY:-}")"
    if [ -n "$normalized" ]; then
        export EASYAIOT_EDGE_MORPHOLOGY="$normalized"
    else
        select_edge_morphology_interactive || return 1
    fi

    if [ "${EASYAIOT_EDGE_MORPHOLOGY}" = "integrated" ]; then
        prompt_cloud_edge_center_config || return 1
    fi
    return 0
}
