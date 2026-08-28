#!/bin/bash
# EasyAIoT 部署形态配置
#
# EASYAIOT_DEPLOY_PROFILE 取值（默认 full）：
#   edge     | 0  — 边缘部署（交互选型后再选 standalone / integrated；
#                   环境变量指定 edge 时默认 standalone，便于快速开始）
#   mini     | 1  — 边缘精简版，推荐宿主机内存 ≥ 4 GB
#   standard | 2  — 标准版，推荐宿主机内存 ≥ 16 GB
#   full     | 3  — 完整版，推荐宿主机内存 ≥ 20 GB（默认）
#
# edge 子形态（EASYAIOT_EDGE_MORPHOLOGY）：
#   standalone  — 纯边缘形态（汇聚面与算力同机）【快速开始默认】
#   integrated  — 云边一体形态（本机仅算力，接入中心）
#
# 各形态能力说明见 print_deploy_profile_summary；内存占用分析见 analyze_deploy_memory.sh。

# shellcheck source=edge_deploy_common.sh
_EDGE_COMMON="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/edge_deploy_common.sh"
# shellcheck disable=SC1090
[ -f "$_EDGE_COMMON" ] && source "$_EDGE_COMMON"
unset _EDGE_COMMON

_resolve_deploy_profile_raw() {
    local p="${EASYAIOT_DEPLOY_PROFILE:-full}"
    case "$p" in
        0|edge|pure-edge|standalone-edge) echo "edge" ;;
        1|mini|minimal|4g|4G) echo "mini" ;;
        2|standard|std|16g|16G) echo "standard" ;;
        3|full|complete|*) echo "full" ;;
    esac
}

_deploy_profile_repo_root() {
    local root="${1:-}"
    if [ -n "$root" ]; then
        echo "$root"
        return
    fi
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
}

_deploy_profile_load_media_root_helpers() {
    local helper
    helper="$(_deploy_profile_repo_root)/.scripts/media-cluster/nfs/resolve_media_root.sh"
    [ -f "$helper" ] || return 0
    # shellcheck source=../media-cluster/nfs/resolve_media_root.sh
    source "$helper"
}

apply_deploy_profile() {
    _deploy_profile_load_media_root_helpers
    EASYAIOT_DEPLOY_PROFILE="$(_resolve_deploy_profile_raw)"
    export EASYAIOT_DEPLOY_PROFILE

    case "$EASYAIOT_DEPLOY_PROFILE" in
        edge)
            export EASYAIOT_ENABLE_TDENGINE=0
            # RUNTIME 告警走 HTTP → VIDEO，不依赖 MQTT/EMQX
            export EASYAIOT_ENABLE_EMQX=0
            export EASYAIOT_ENABLE_HARNESS=0
            export EASYAIOT_ENABLE_IDEA=0
            export EASYAIOT_ENABLE_PANEL=0
            export EASYAIOT_ENABLE_MQTT_DEMO=0
            ;;
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

    # 确保宿主机 bind 源是真实目录（误建成文件会导致 daemon: mkdir ... file exists）
    if command -v ensure_easyaiot_media_bind_source >/dev/null 2>&1 || type ensure_easyaiot_media_bind_source >/dev/null 2>&1; then
        EASYAIOT_MEDIA_ROOT="$(ensure_easyaiot_media_bind_source)"
    else
        EASYAIOT_MEDIA_ROOT="$(resolve_easyaiot_media_root 2>/dev/null || echo "${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}")"
    fi
    export EASYAIOT_MEDIA_ROOT
    if [ -z "${NFS_SERVER:-}" ]; then
        NFS_SERVER="$(resolve_nfs_server_from_mount)"
        [ -n "$NFS_SERVER" ] && export NFS_SERVER
    fi

    sync_deploy_profile_to_modules
}

# docker compose --profile 参数（mini/standard/full 启用 EMQX；full 另启 TDengine；edge 无 profile）
compose_profile_flags() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        full) echo "--profile tdengine --profile emqx" ;;
        mini|standard) echo "--profile emqx" ;;
        edge) echo "" ;;
        *) echo "" ;;
    esac
}

# 返回空格分隔的中间件 compose 服务名（跳过列表，传给 compose_up_middleware）
middleware_skipped_services() {
    local -a skips=()
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        edge)
            # 仅保留 PostgreSQL / Redis / SRS；无 DEVICE → 无 Nacos/MinIO/EMQX/Kafka
            skips+=(Milvus ZLMediaKit NodeRED FUXA TDengine TDengine-init Kafka MinIO Nacos)
            ;;
        mini)
            skips+=(Milvus ZLMediaKit NodeRED FUXA TDengine TDengine-init)
            ;;
        standard)
            skips+=(NodeRED FUXA TDengine TDengine-init)
            ;;
        full)
            ;;
    esac
    echo "${skips[*]}"
}

# DEVICE compose 服务：跳过列表
device_skipped_services() {
    local -a skips=()
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        edge)
            # 零 DEVICE：全部跳过（模块级也会跳过；此处兜底）
            skips+=(iot-gateway iot-system iot-infra iot-sink iot-device iot-dataset iot-node iot-visualize iot-file iot-message iot-gb28181 iot-tdengine)
            ;;
        mini)
            # 不部署 iot-flow（告警工单）：mini 无工作流引擎，前端隐藏工单 Tab/菜单
            skips+=(iot-device iot-dataset iot-node iot-visualize iot-flow iot-file iot-message iot-gb28181 iot-tdengine)
            ;;
        standard)
            skips+=(iot-device iot-tdengine iot-visualize)
            ;;
        full)
            ;;
    esac
    echo "${skips[*]}"
}

# DEVICE compose 服务：仅启动白名单（空表示除跳过列表外全部启动）
device_enabled_services() {
    echo ""
}

# mini：精简 DEVICE/中间件，事件面仍为 Gateway→iot-sink；不部署 iot-flow（告警工单）
# edge：与 mini 共享部分本地存储行为（见 is_local_storage_deploy_profile），但零 DEVICE
is_mini_deploy_profile() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini) return 0 ;;
        *) return 1 ;;
    esac
}

is_edge_deploy_profile() {
    [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "edge" ]
}

# 本地存储热路径（告警图/录像不经 MinIO）：mini 与 edge
is_local_storage_deploy_profile() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini|edge) return 0 ;;
        *) return 1 ;;
    esac
}

# WEB 前端构建/镜像标签：edge 与 mini 共用裁剪菜单（VITE 仅识别 mini/standard/full）
frontend_deploy_profile() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        edge) echo "mini" ;;
        *) echo "${EASYAIOT_DEPLOY_PROFILE:-full}" ;;
    esac
}

# full 形态：含 TDengine / iot-sink 工业协议演示等完整能力
is_full_deploy_profile() {
    [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "full" ]
}

# 按部署形态判断业务模块是否启用
#   APP / VISUALIZE / TRANSFORM — 仅 full 全量形态
#   POST — 仅 standard / full（mini / edge 不部署定制后处理）
#   PANEL — 源码/Docker 部署默认启用；安装包（deb/桌面端）本身即为 PANEL，
#           由 systemd/二进制托管，部署时不应再拉 Docker PANEL（EASYAIOT_ENABLE_PANEL=0）。
#           无源码 runtime 未显式开启时也默认跳过。
#   IDEA — 社区贡献在线 IDE，mini/standard/full 均启用（EASYAIOT_ENABLE_IDEA=0 关闭）
#   HARNESS — DeepSeek Harness AI Agent，mini/standard/full 均启用（EASYAIOT_ENABLE_HARNESS=0 关闭）
module_enabled_for_deploy_profile() {
    case "$1" in
        APP|VISUALIZE|TRANSFORM) [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "full" ] ;;
        POST)
            case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
                standard|full) return 0 ;;
                *) return 1 ;;
            esac
            ;;
        DEVICE)
            # edge：零 DEVICE（无 gateway/system/sink）；告警/DVR 由 VIDEO 本地消化
            is_edge_deploy_profile && return 1
            return 0
            ;;
        AI|RTC)
            is_edge_deploy_profile && return 1
            return 0
            ;;
        HARNESS)
            case "${EASYAIOT_ENABLE_HARNESS:-}" in
                0|false|FALSE|no|NO|off|OFF) return 1 ;;
                *) return 0 ;;
            esac
            ;;
        PANEL)
            case "${EASYAIOT_ENABLE_PANEL:-}" in
                0|false|FALSE|no|NO|off|OFF) return 1 ;;
                1|true|TRUE|yes|YES|on|ON) return 0 ;;
            esac
            # 未显式设置：PANEL 安装包 / 无源码 runtime 默认不二次部署
            if type runtime_is_source_free_runtime >/dev/null 2>&1 && runtime_is_source_free_runtime; then
                return 1
            fi
            [ "${EASYAIOT_ENABLE_PANEL:-1}" != "0" ]
            ;;
        IDEA)
            case "${EASYAIOT_ENABLE_IDEA:-}" in
                0|false|FALSE|no|NO|off|OFF) return 1 ;;
                *) return 0 ;;
            esac
            ;;
        *) return 0 ;;
    esac
}

# 跳过 PANEL 部署时的说明（安装包场景避免误判为“形态少装了模块”）
panel_skip_deploy_reason() {
    if [ "${EASYAIOT_ENABLE_PANEL:-}" = "0" ] || [ "${EASYAIOT_ENABLE_PANEL:-}" = "false" ]; then
        echo "安装包/本机 PANEL 已在运行，部署无需再装运维控制台"
        return
    fi
    if type runtime_is_source_free_runtime >/dev/null 2>&1 && runtime_is_source_free_runtime; then
        echo "无源码 runtime（PANEL 安装包）已提供运维入口，跳过 Docker PANEL"
        return
    fi
    echo "已禁用 PANEL 模块部署（EASYAIOT_ENABLE_PANEL=0）"
}

# mini / standard 形态均不部署 TDengine 中间件
is_tdengine_disabled_deploy_profile() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini|standard|edge) return 0 ;;
        *) return 1 ;;
    esac
}

# mini / standard 形态均不部署可视化（iot-visualize / VISUALIZE 编辑器 / FUXA / 相关菜单）
is_visualize_disabled_deploy_profile() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini|standard|edge) return 0 ;;
        *) return 1 ;;
    esac
}

# iot-sink Spring Profile（local + 形态专用 profile）；edge 不部署 sink
iot_sink_spring_profiles_active() {
    if is_edge_deploy_profile; then
        echo "local"
    elif is_mini_deploy_profile || is_local_storage_deploy_profile; then
        echo "local,mini"
    elif is_tdengine_disabled_deploy_profile; then
        echo "local,standard"
    else
        echo "local"
    fi
}

# DEVICE 是否需要 tdengine compose profile
device_compose_profile_flags() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        full) echo "--profile tdengine" ;;
        *) echo "" ;;
    esac
}

# 各形态推荐内存上限（MiB，供 analyze_deploy_memory.sh 等脚本引用）
deploy_profile_budget_mib() {
    case "${1:-${EASYAIOT_DEPLOY_PROFILE:-full}}" in
        edge) echo "2048" ;;
        mini|1) echo "4096" ;;
        standard|2) echo "16384" ;;
        full|3|*) echo "20480" ;;
    esac
}

deploy_profile_budget_label() {
    case "${1:-${EASYAIOT_DEPLOY_PROFILE:-full}}" in
        edge) echo "2 GB" ;;
        mini|1) echo "4 GB" ;;
        standard|2) echo "16 GB" ;;
        full|3|*) echo "20 GB" ;;
    esac
}

_deploy_profile_desc() {
    case "${EASYAIOT_DEPLOY_PROFILE:-}" in
        edge)
            case "${EASYAIOT_EDGE_MORPHOLOGY:-standalone}" in
                integrated) echo "edge / integrated（云边一体形态）" ;;
                *) echo "edge / standalone（纯边缘形态，推荐 ≥ 2 GB）" ;;
            esac
            ;;
        mini) echo "mini（边缘精简版，推荐 ≥ 4 GB）" ;;
        standard) echo "standard（标准版，推荐 ≥ 16 GB）" ;;
        full) echo "full（完整版，推荐 ≥ 20 GB）" ;;
        *) echo "full（完整版，推荐 ≥ 20 GB）" ;;
    esac
}

_print_deploy_profile_menu() {
    echo ""
    echo "请选择部署形态："
    echo "  0) edge      — 边缘部署（随后选择 standalone / integrated）"
    echo "  1) mini      — 边缘精简版（推荐内存 ≥ 4 GB）"
    echo "  2) standard  — 标准版（推荐内存 ≥ 16 GB）"
    echo "  3) full      — 完整版（推荐内存 ≥ 20 GB，默认）"
    echo ""
}

# 持久化上次选择的部署形态（install 交互选择后写入，start 等命令自动读取）
_deploy_profile_file() {
    local base="${DEPLOY_PROFILE_FILE:-}"
    if [ -n "$base" ]; then
        echo "$base"
        return
    fi
    # BASH_SOURCE[1] 为 source 方脚本目录；直接执行 deploy_profile.sh 时回退到自身目录
    local src="${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}"
    echo "$(cd "$(dirname "$src")" && pwd)/.deploy_profile"
}

load_saved_deploy_profile() {
    if [ -n "${EASYAIOT_DEPLOY_PROFILE:-}" ]; then
        return 0
    fi
    local f
    f="$(_deploy_profile_file)"
    if [ -f "$f" ]; then
        local saved
        saved=$(tr -d '[:space:]' < "$f")
        if [ -n "$saved" ]; then
            export EASYAIOT_DEPLOY_PROFILE="$saved"
        fi
    fi
}

save_deploy_profile() {
    local f
    f="$(_deploy_profile_file)"
    echo "$EASYAIOT_DEPLOY_PROFILE" > "$f"
}

# 非 install 命令：读取已保存形态或默认 full，不弹交互
ensure_deploy_profile() {
    load_saved_deploy_profile
    apply_deploy_profile
}

# compose 报「creating mount source path ... file exists」时调用：修复/回退媒体根并同步模块 env
# 返回 0=已修复可重试；1=非该类错误
repair_media_bind_after_compose_error() {
    local log_text="${1:-}"
    _deploy_profile_load_media_root_helpers
    if ! type is_media_bind_source_mkdir_error >/dev/null 2>&1; then
        return 1
    fi
    is_media_bind_source_mkdir_error "$log_text" || return 1

    local prev="${EASYAIOT_MEDIA_ROOT:-/mnt/easyaiot-media}"
    echo "[media] 检测到 Docker bind 源异常（mkdir file exists），正在修复媒体根: ${prev}"

    # 1) 原地修复（误建成文件 / 坏 symlink → 目录）
    if type ensure_easyaiot_media_bind_source >/dev/null 2>&1; then
        ensure_easyaiot_media_bind_source >/dev/null || true
    fi

    # 2) /mnt 路径在 Snap Docker / 异常挂载上常仍失败 → 强制家目录本地 bind
    case "$prev" in
        /mnt/*)
            echo "[media] /mnt 媒体根对 Docker 不可用，回退到 $(easyaiot_home_media_root 2>/dev/null || echo "${HOME}/easyaiot/media")"
            ensure_easyaiot_media_bind_source --force-home >/dev/null || true
            ;;
    esac

    export EASYAIOT_MEDIA_ROOT
    sync_deploy_profile_to_modules "$(_deploy_profile_repo_root)"
    echo "[media] 已修复并同步 EASYAIOT_MEDIA_ROOT=${EASYAIOT_MEDIA_ROOT}"
    return 0
}

print_deploy_profile_summary() {
  apply_deploy_profile
  local desc
  desc="$(_deploy_profile_desc)"
  echo "当前部署形态: ${desc} (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
  warn_web_rebuild_if_profile_changed
  case "${EASYAIOT_DEPLOY_PROFILE}" in
    edge)
      if [ "${EASYAIOT_EDGE_MORPHOLOGY:-standalone}" = "integrated" ]; then
        echo "  定位: edge / integrated — 云边一体形态（本机仅部署边缘算力）"
        echo "  能力: 接入中心汇聚面，执行边缘推理任务"
      else
        echo "  定位: edge / standalone — 纯边缘形态（汇聚面与算力同机，本地闭环）"
        echo "  推荐内存: ≥ 2 GB（含边缘推理与峰值缓冲）"
        echo "  能力: 视频接入、实时推理、告警与录像本地闭环"
        echo "  存储: 本地媒体目录"
        echo "  中间件: 精简为数据库、缓存与流媒体必要组件"
        echo "  访问: 控制台本机直连（默认端口见部署说明）"
      fi
      ;;
    mini)
      echo "  定位: 边缘精简版 — 轻量平台能力，适于点位智能化"
      echo "  推荐内存: ≥ 4 GB"
      echo "  能力: 设备接入、视频智能、实时通信与管理控制台"
      echo "  事件面: 经平台网关统一汇聚"
      echo "  精简: 不含时序库、工业可视化与部分扩展组件"
      ;;
    standard)
      echo "  定位: 标准版 — 完整业务主干，适于楼层/园区级覆盖"
      echo "  推荐内存: ≥ 16 GB"
      echo "  能力: 在精简版基础上启用更完整的中间件与业务能力"
      echo "  精简: 不含时序库、部分工业组态与可视化扩展"
      ;;
    full)
      echo "  定位: 完整版 — 全栈能力，适于一体机/机房级交付"
      echo "  推荐内存: ≥ 20 GB"
      echo "  能力: 全量业务与中间件（含移动端、可视化、工业协议演示等）"
      ;;
  esac
}

# 上级 orchestrator（install_linux / install_business 等）选定形态后调用，子模块 install 不再弹窗
lock_deploy_profile_for_child_installs() {
    export EASYAIOT_DEPLOY_PROFILE
    export EASYAIOT_SKIP_PROFILE_PROMPT=1
}

# install 专用：交互终端下弹窗选择；环境变量已指定 / 上级已 lock / 非交互则直接沿用
select_deploy_profile_for_install() {
  if [ "${EASYAIOT_SKIP_PROFILE_PROMPT:-}" = "1" ]; then
    ensure_deploy_profile
    if declare -F ensure_edge_morphology_for_install >/dev/null 2>&1; then
      ensure_edge_morphology_for_install || return 1
    fi
    lock_deploy_profile_for_child_installs
    return 0
  fi

  # 已通过环境变量显式指定形态时不弹菜单（含交互终端）
  # 例: EASYAIOT_DEPLOY_PROFILE=full bash .../install_linux.sh install
  # 快速开始: EASYAIOT_DEPLOY_PROFILE=edge → 默认 standalone，不再二次弹窗
  # 云边一体: EASYAIOT_DEPLOY_PROFILE=edge EASYAIOT_EDGE_MORPHOLOGY=integrated VIDEO_BASE_URL=...
  case "${EASYAIOT_DEPLOY_PROFILE:-}" in
    mini|standard|full|edge)
      apply_deploy_profile
      if [ "${EASYAIOT_DEPLOY_PROFILE}" = "edge" ]; then
        # 显式指定 edge 且未给子形态时，默认纯边缘（快速开始一键路径）
        local _edge_morph=""
        if declare -F normalize_edge_morphology >/dev/null 2>&1; then
          _edge_morph="$(normalize_edge_morphology "${EASYAIOT_EDGE_MORPHOLOGY:-}")"
        fi
        if [ -z "${_edge_morph}" ]; then
          export EASYAIOT_EDGE_MORPHOLOGY=standalone
        else
          export EASYAIOT_EDGE_MORPHOLOGY="${_edge_morph}"
        fi
        if declare -F ensure_edge_morphology_for_install >/dev/null 2>&1; then
          ensure_edge_morphology_for_install || return 1
        fi
      fi
      save_deploy_profile
      lock_deploy_profile_for_child_installs
      echo ""
      if declare -F print_info >/dev/null 2>&1; then
        if [ "${EASYAIOT_EDGE_MORPHOLOGY:-}" = "integrated" ]; then
          print_info "已选定: edge / integrated（云边一体形态）"
        elif [ "${EASYAIOT_DEPLOY_PROFILE}" = "edge" ]; then
          print_info "已选定: edge / standalone（纯边缘形态）"
        else
          print_info "使用环境变量指定的部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
        fi
      else
        echo "[INFO] 使用环境变量指定的部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
      fi
      echo ""
      return 0
      ;;
  esac

  if [ ! -t 0 ]; then
    load_saved_deploy_profile
    [ -z "${EASYAIOT_DEPLOY_PROFILE:-}" ] && export EASYAIOT_DEPLOY_PROFILE=full
    apply_deploy_profile
    save_deploy_profile
    lock_deploy_profile_for_child_installs
    return 0
  fi

  _print_deploy_profile_menu
  local choice=""
  read -r -p "请输入选项 [0-3，默认 3]: " choice
  case "${choice:-3}" in
    0|edge)
      export EASYAIOT_DEPLOY_PROFILE=edge
      unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true
      if declare -F ensure_edge_morphology_for_install >/dev/null 2>&1; then
        ensure_edge_morphology_for_install || return 1
      else
        export EASYAIOT_EDGE_MORPHOLOGY=standalone
      fi
      if [ "${EASYAIOT_EDGE_MORPHOLOGY}" = "integrated" ]; then
        apply_deploy_profile
        lock_deploy_profile_for_child_installs
        echo ""
        if declare -F print_info >/dev/null 2>&1; then
          print_info "已选定: edge / integrated（云边一体形态）"
        else
          echo "[INFO] 已选定: edge / integrated（云边一体形态）"
        fi
        echo ""
        return 0
      fi
      export EASYAIOT_EDGE_MORPHOLOGY=standalone
      ;;
    1|mini) export EASYAIOT_DEPLOY_PROFILE=mini; unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true ;;
    2|standard) export EASYAIOT_DEPLOY_PROFILE=standard; unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true ;;
    *) export EASYAIOT_DEPLOY_PROFILE=full; unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true ;;
  esac
  apply_deploy_profile
  save_deploy_profile
  lock_deploy_profile_for_child_installs
  echo ""
  print_deploy_profile_summary
  echo ""
}

# 交互式选择（通用；环境中已设置 EASYAIOT_DEPLOY_PROFILE 时不弹窗）
select_deploy_profile_interactive() {
    if [ -n "${EASYAIOT_DEPLOY_PROFILE:-}" ]; then
        apply_deploy_profile
        return 0
    fi
    if [ ! -t 0 ]; then
        load_saved_deploy_profile
        [ -z "${EASYAIOT_DEPLOY_PROFILE:-}" ] && export EASYAIOT_DEPLOY_PROFILE=full
        apply_deploy_profile
        return 0
    fi

    _print_deploy_profile_menu
    local choice=""
    read -r -p "请输入选项 [0-3，默认 3]: " choice
    case "${choice:-3}" in
        0|edge)
            export EASYAIOT_DEPLOY_PROFILE=edge
            unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true
            if declare -F ensure_edge_morphology_for_install >/dev/null 2>&1; then
                ensure_edge_morphology_for_install || return 1
            else
                export EASYAIOT_EDGE_MORPHOLOGY=standalone
            fi
            if [ "${EASYAIOT_EDGE_MORPHOLOGY}" = "integrated" ]; then
                apply_deploy_profile
                echo ""
                echo "[INFO] 已选定: edge / integrated（云边一体形态）"
                echo ""
                return 0
            fi
            export EASYAIOT_EDGE_MORPHOLOGY=standalone
            ;;
        1|mini) export EASYAIOT_DEPLOY_PROFILE=mini; unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true ;;
        2|standard) export EASYAIOT_DEPLOY_PROFILE=standard; unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true ;;
        *) export EASYAIOT_DEPLOY_PROFILE=full; unset EASYAIOT_EDGE_MORPHOLOGY 2>/dev/null || true ;;
    esac
    apply_deploy_profile
    save_deploy_profile
    echo ""
    print_deploy_profile_summary
    echo ""
}

# 从现有 mount 推断 NFS 服务端（未显式设置 NFS_SERVER 时）
resolve_nfs_server_from_mount() {
    if [ -n "${NFS_SERVER:-}" ]; then
        echo "${NFS_SERVER}"
        return
    fi
    local root
    root="$(resolve_easyaiot_media_root)"
    # 用 findmnt/timeout，避免僵死 NFS 上 mountpoint 卡死整个 update
    if type _is_media_mountpoint_safe >/dev/null 2>&1; then
        if _is_media_mountpoint_safe "$root"; then
            findmnt -n -o SOURCE "$root" 2>/dev/null | cut -d: -f1 || true
            return
        fi
    elif command -v timeout >/dev/null 2>&1; then
        if timeout 3 mountpoint -q "$root" 2>/dev/null; then
            findmnt -n -o SOURCE "$root" 2>/dev/null | cut -d: -f1 || true
            return
        fi
    elif mountpoint -q "$root" 2>/dev/null; then
        findmnt -n -o SOURCE "$root" 2>/dev/null | cut -d: -f1 || true
        return
    fi
    echo ""
}

# 写入或更新 .env.docker 中的键值
# 使用临时文件方式（而非 sed -i），兼容 GNU sed 与 BSD sed（macOS）
_set_env_docker_kv() {
    local file="$1" key="$2" value="$3"
    [ -f "$file" ] || return 0
    if grep -q "^${key}=" "$file" 2>/dev/null; then
        local tmp="${file}.tmp.$$"
        sed "s|^${key}=.*|${key}=${value}|" "$file" > "$tmp" && mv "$tmp" "$file"
    else
        # 确保追加前文件以换行结尾，避免与最后一行粘连
        [ -n "$(tail -c1 "$file" 2>/dev/null || true)" ] && echo "" >> "$file"
        echo "${key}=${value}" >> "$file"
    fi
}

# WEB .env：KEY = value（Vite 格式，允许等号两侧空格）
_set_web_env_kv() {
    local file="$1" key="$2" value="$3"
    [ -f "$file" ] || return 0
    if grep -qE "^${key}[[:space:]]*=" "$file" 2>/dev/null; then
        local tmp="${file}.tmp.$$"
        sed -E "s|^${key}[[:space:]]*=.*|${key} = ${value}|" "$file" > "$tmp" && mv "$tmp" "$file"
    else
        [ -n "$(tail -c1 "$file" 2>/dev/null || true)" ] && echo "" >> "$file"
        echo "${key} = ${value}" >> "$file"
    fi
}

# WEB：按形态写入 nginx 配置（统一经 Gateway 48080；edge/mini 用专用 conf）
sync_web_deploy_profile_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local web_env="${root}/WEB/.env"
    local conf="./conf/nginx.conf"
    local vite_profile tenant_flag captcha_flag edge_flag
    vite_profile="$(frontend_deploy_profile)"
    if is_edge_deploy_profile; then
        conf="./conf/nginx.edge.conf"
        tenant_flag="false"
        captcha_flag="false"
        edge_flag="true"
    elif is_mini_deploy_profile; then
        conf="./conf/nginx.mini.conf"
        tenant_flag="true"
        captcha_flag="true"
        edge_flag="false"
    else
        tenant_flag="true"
        captcha_flag="true"
        edge_flag="false"
    fi
    [ -f "$web_env" ] || return 0
    _set_web_env_kv "$web_env" "VITE_GLOB_DEPLOY_PROFILE" "$vite_profile"
    _set_web_env_kv "$web_env" "VITE_GLOB_APP_TENANT_ENABLE" "$tenant_flag"
    _set_web_env_kv "$web_env" "VITE_GLOB_APP_CAPTCHA_ENABLE" "$captcha_flag"
    _set_web_env_kv "$web_env" "VITE_GLOB_EDGE_STANDALONE" "$edge_flag"
    if grep -q '^NGINX_CONF=' "$web_env" 2>/dev/null; then
        local tmp="${web_env}.tmp.$$"
        sed "s|^NGINX_CONF=.*|NGINX_CONF=${conf}|" "$web_env" > "$tmp" && mv "$tmp" "$web_env"
    else
        [ -n "$(tail -c1 "$web_env" 2>/dev/null || true)" ] && echo "" >> "$web_env"
        echo "NGINX_CONF=${conf}" >> "$web_env"
    fi
}

# 将 .deploy_profile 同步到各业务模块持久化配置（install/start/restart 均应一致）
sync_deploy_profile_to_modules() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    apply_middleware_deploy_env "$root"
    apply_python_service_deploy_env "$root"
    apply_device_deploy_env "$root"
    apply_transform_deploy_env "$root"
    sync_web_deploy_profile_env "$root"
}

# 中间件 compose：写入 .env 供 SRS 等 volume 变量替换
apply_middleware_deploy_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local env_file="${root}/.scripts/docker/.env"
    local mount_root
    mount_root="$(ensure_easyaiot_media_bind_source 2>/dev/null || resolve_easyaiot_media_root)"
    local nfs_export="${NFS_EXPORT:-$mount_root}"
    mkdir -p "$(dirname "$env_file")"
    touch "$env_file"
    _set_env_docker_kv "$env_file" EASYAIOT_MEDIA_ROOT "$mount_root"
    _set_env_docker_kv "$env_file" NFS_SERVER "${NFS_SERVER:-}"
    _set_env_docker_kv "$env_file" NFS_EXPORT "$nfs_export"
}

# DEVICE：按形态写入 .env（docker compose 自动读取，供 IOT_SYSTEM_SPRING_PROFILES_ACTIVE 等变量替换）
apply_device_deploy_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local env_file="${root}/DEVICE/.env"
    # edge 不部署 DEVICE，跳过写入以免误导
    if is_edge_deploy_profile; then
        return 0
    fi
    mkdir -p "$(dirname "$env_file")"
    touch "$env_file"
    if is_mini_deploy_profile; then
        _set_env_docker_kv "$env_file" IOT_SYSTEM_SPRING_PROFILES_ACTIVE "local,mini"
    else
        _set_env_docker_kv "$env_file" IOT_SYSTEM_SPRING_PROFILES_ACTIVE "local"
    fi
    _set_env_docker_kv "$env_file" IOT_SINK_SPRING_PROFILES_ACTIVE "$(iot_sink_spring_profiles_active)"
    _set_env_docker_kv "$env_file" EASYAIOT_MEDIA_ROOT "$(ensure_easyaiot_media_bind_source 2>/dev/null || resolve_easyaiot_media_root)"
}

# TRANSFORM：按形态写入 .env.docker（供运行脚本统一读取）
apply_transform_deploy_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local env_file="${root}/TRANSFORM/.env.docker"
    [ -d "${root}/TRANSFORM" ] || return 0
    mkdir -p "$(dirname "$env_file")"
    touch "$env_file"

    _set_env_docker_kv "$env_file" EASYAIOT_DEPLOY_PROFILE "${EASYAIOT_DEPLOY_PROFILE:-full}"
    _set_env_docker_kv "$env_file" SPRING_PROFILES_ACTIVE "local"
    _set_env_docker_kv "$env_file" TRANSFORM_ROLE "full"
    _set_env_docker_kv "$env_file" TRANSFORM_BACKUP_DIR "/opt/easyaiot/TRANSFORM/data/transform-backup"
    _set_env_docker_kv "$env_file" NACOS_ADDR "Nacos:8848"
    _set_env_docker_kv "$env_file" NACOS_USERNAME "nacos"
    _set_env_docker_kv "$env_file" NACOS_PASSWORD "basiclab@iot78475418754"
    _set_env_docker_kv "$env_file" KAFKA_BOOTSTRAP "Kafka:9092"
    _set_env_docker_kv "$env_file" POSTGRES_URL "jdbc:postgresql://PostgresSQL:5432/iot-transform20"
    _set_env_docker_kv "$env_file" POSTGRES_USERNAME "postgres"
    _set_env_docker_kv "$env_file" POSTGRES_PASSWORD "iot45722414822"
    _set_env_docker_kv "$env_file" SERVER_PORT "48096"
}

# 若 WEB 镜像构建时的形态与当前不一致，提示需 rebuild（前端 VITE_GLOB_DEPLOY_PROFILE 编译进镜像）
warn_web_rebuild_if_profile_changed() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local stamp="${root}/.scripts/docker/.web_deploy_profile_built"
    local current="${EASYAIOT_DEPLOY_PROFILE:-full}"
    if [ -f "$stamp" ] && [ "$(tr -d '[:space:]' < "$stamp")" != "$current" ]; then
        echo "⚠️  WEB 部署形态已从 $(tr -d '[:space:]' < "$stamp") 变为 ${current}，请执行 WEB/install_linux.sh build 或 install 重新构建前端镜像"
    fi
}

record_web_deploy_profile_built() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local stamp="${root}/.scripts/docker/.web_deploy_profile_built"
    echo "${EASYAIOT_DEPLOY_PROFILE:-full}" > "$stamp"
}

# 按部署形态同步 VIDEO/AI .env.docker
# mini/standard/full：告警/DVR 经 Gateway→iot-sink（可含 MinIO）
# edge：零 DEVICE；本地落库 + 本地 DVR；不写 sink/MinIO
_apply_python_sink_media_env() {
    local env_file="$1"
    local compose_env="${2:-}"
    local with_sink_hooks="${3:-1}"
    local mount_root
    _deploy_profile_load_media_root_helpers
    # 宿主机绑定源（供 docker-compose ${EASYAIOT_MEDIA_ROOT} 替换）
    mount_root="$(ensure_easyaiot_media_bind_source 2>/dev/null || resolve_easyaiot_media_root 2>/dev/null || true)"
    if [ -z "$mount_root" ]; then
        local repo_root
        repo_root="$(_deploy_profile_repo_root)"
        if [ -d "${repo_root}/.runtime-media" ]; then
            mount_root="${repo_root}/.runtime-media"
        else
            mount_root="/mnt/easyaiot-media"
        fi
    fi
    # 容器内固定挂载点（与 VIDEO/AI docker-compose.yaml 一致；勿把宿主机路径写进 .env.docker）
    local container_media_root="/mnt/easyaiot-media"
    if [ "$with_sink_hooks" = "1" ]; then
        _set_env_docker_kv "$env_file" MINIO_ENABLED true
        _set_env_docker_kv "$env_file" IOT_SINK_USE_GATEWAY 1
        _set_env_docker_kv "$env_file" SINK_DVR_HOOK_URL "http://localhost:48080/admin-api/sink/media/hook/srs/on_dvr"
        _set_env_docker_kv "$env_file" IOT_SINK_MEDIA_HOOK_URL "http://localhost:48080/admin-api/sink/media/hook/srs/on_dvr"
    fi
    _set_env_docker_kv "$env_file" ALERT_IMAGES_DIR "${container_media_root}/alert_images"
    _set_env_docker_kv "$env_file" SRS_HOST_DATA_ROOT "$container_media_root"
    _set_env_docker_kv "$env_file" SRS_RECORD_DIR "${container_media_root}/playbacks"
    _set_env_docker_kv "$env_file" EASYAIOT_MEDIA_ROOT "$container_media_root"
    # 全形态：录像守护默认策略（live+ai 双写易撑盘）
    _set_env_docker_kv "$env_file" PLAYBACK_CLEANUP_ENABLED true
    _set_env_docker_kv "$env_file" PLAYBACK_GUARD_INTERVAL_MINUTES 5
    _set_env_docker_kv "$env_file" PLAYBACK_MAX_AGE_HOURS "${PLAYBACK_MAX_AGE_HOURS:-24}"
    _set_env_docker_kv "$env_file" PLAYBACK_GLOBAL_MAX_FILES "${PLAYBACK_GLOBAL_MAX_FILES:-1500}"
    _set_env_docker_kv "$env_file" PLAYBACK_GLOBAL_MAX_GB "${PLAYBACK_GLOBAL_MAX_GB:-50}"
    _set_env_docker_kv "$env_file" PLAYBACK_DEVICE_MAX_FILES "${PLAYBACK_DEVICE_MAX_FILES:-60}"
    _set_env_docker_kv "$env_file" PLAYBACK_DISK_WARN_PERCENT 80
    _set_env_docker_kv "$env_file" PLAYBACK_DISK_CRITICAL_PERCENT 85
    _set_env_docker_kv "$env_file" PLAYBACK_DISK_TARGET_PERCENT 70
    _set_env_docker_kv "$env_file" PLAYBACK_LEGACY_DIRS "${HOME:-/home/ubuntu}/easyaiot/data/playbacks"
    # compose 文件变量替换读项目目录 .env（不是 .env.docker），同步写入宿主机路径
    if [ -n "$compose_env" ]; then
        touch "$compose_env" 2>/dev/null || true
        if [ -w "$compose_env" ] || [ -w "$(dirname "$compose_env")" ]; then
            _set_env_docker_kv "$compose_env" EASYAIOT_MEDIA_ROOT "$mount_root"
        else
            echo "[media] 警告: 无法写入 ${compose_env}（权限不足），请手动设置 EASYAIOT_MEDIA_ROOT=${mount_root}" >&2
        fi
    fi
}

apply_python_service_deploy_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    if [ -z "$root" ]; then
        root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    fi
    local module env_file
    for module in VIDEO AI; do
        env_file="${root}/${module}/.env.docker"
        [ -f "$env_file" ] || continue
        _set_env_docker_kv "$env_file" EASYAIOT_DEPLOY_PROFILE "${EASYAIOT_DEPLOY_PROFILE:-full}"

        if is_edge_deploy_profile; then
            # 零 DEVICE：业务回调指向本机 VIDEO
            _set_env_docker_kv "$env_file" JAVA_BACKEND_URL "http://127.0.0.1:6000"
            _set_env_docker_kv "$env_file" GATEWAY_URL "http://127.0.0.1:6000"
            _set_env_docker_kv "$env_file" NODE_REMOTE_DEPLOY false
            if [ "$module" = "VIDEO" ]; then
                _set_env_docker_kv "$env_file" ALERT_KEEP_LATEST true
                _set_env_docker_kv "$env_file" ALERT_USE_DIRECT_PERSIST true
                _set_env_docker_kv "$env_file" MINIO_ENABLED false
                # edge 不部署 POST：Infer 走直发 / 本地落盘路径
                _set_env_docker_kv "$env_file" POST_ENABLED false
                # 模型管理走本机 VIDEO（无 AI / 无 MinIO）
                _set_env_docker_kv "$env_file" AI_SERVICE_URL "http://127.0.0.1:6000/video"
                # 容器内媒体卷路径；权重落盘到 local-storage，种子只读挂载 /model-seed-data
                _set_env_docker_kv "$env_file" LOCAL_STORAGE_ROOT "/mnt/easyaiot-media/local-storage"
                _set_env_docker_kv "$env_file" MODEL_SEED_DATA_ROOT "/model-seed-data"
                # edge 无 EMQX：RUNTIME HTTP → VIDEO /video/alert/hook 直连落库
                _set_env_docker_kv "$env_file" ALGO_BUS_TRANSPORT http
                _set_env_docker_kv "$env_file" ALERT_HOOK_URL "http://127.0.0.1:6000/video/alert/hook"
                # 本地 DVR：勿在「上传后删本地」（edge 无 MinIO）；录像守护扫容器内目录
                _set_env_docker_kv "$env_file" PLAYBACK_DELETE_AFTER_UPLOAD false
                _set_env_docker_kv "$env_file" PLAYBACK_MAX_AGE_HOURS 24
                _set_env_docker_kv "$env_file" IOT_SINK_USE_GATEWAY 0
                _set_env_docker_kv "$env_file" SINK_DVR_HOOK_URL ""
                _set_env_docker_kv "$env_file" IOT_SINK_MEDIA_HOOK_URL ""
                _set_env_docker_kv "$env_file" DVR_LOCAL_PERSIST 1
                _set_env_docker_kv "$env_file" MEDIA_UPLOAD_MODE sync
                _set_env_docker_kv "$env_file" VIDEO_AUTH_ENABLED 1
                _set_env_docker_kv "$env_file" AUTH_CHECK_URL "http://127.0.0.1:6000/video/system/auth/get-permission-info"
                # edge 默认不部署 RTC；仍写入占位，避免 VIDEO 读到 127.0.0.1:1984 误导前端
                _set_env_docker_kv "$env_file" RTC_SERVICE_URL "http://127.0.0.1:6100"
                _set_env_docker_kv "$env_file" RTC_GO2RTC_WEB_URL "/dev-api/go2rtc/"
                _set_env_docker_kv "$env_file" RTC_RTSP_HOST "127.0.0.1"
                _set_env_docker_kv "$env_file" RTC_RTSP_PORT "8554"
                _apply_python_sink_media_env "$env_file" "${root}/${module}/.env" 0
            else
                _apply_python_sink_media_env "$env_file" "${root}/${module}/.env" 0
            fi
            continue
        fi

        _set_env_docker_kv "$env_file" JAVA_BACKEND_URL "http://localhost:48080"
        _set_env_docker_kv "$env_file" GATEWAY_URL "http://localhost:48080"
        _set_env_docker_kv "$env_file" AUTH_CHECK_URL "http://localhost:48080/admin-api/system/auth/get-permission-info"
        if is_mini_deploy_profile || is_local_storage_deploy_profile; then
            _set_env_docker_kv "$env_file" NODE_REMOTE_DEPLOY false
        else
            _set_env_docker_kv "$env_file" NODE_REMOTE_DEPLOY true
        fi
        if [ "$module" = "VIDEO" ]; then
            # RTC / go2rtc：存量 .env.docker 可能缺项，安装/切形态时补齐
            _set_env_docker_kv "$env_file" RTC_SERVICE_URL "http://127.0.0.1:6100"
            _set_env_docker_kv "$env_file" RTC_GO2RTC_WEB_URL "/dev-api/go2rtc/"
            _set_env_docker_kv "$env_file" RTC_RTSP_HOST "127.0.0.1"
            _set_env_docker_kv "$env_file" RTC_RTSP_PORT "8554"
            # POST 仅 standard/full；mini 关闭定制后处理切流
            if is_mini_deploy_profile; then
                _set_env_docker_kv "$env_file" POST_ENABLED false
            else
                _set_env_docker_kv "$env_file" POST_ENABLED true
            fi
            if is_mini_deploy_profile || is_local_storage_deploy_profile; then
                _set_env_docker_kv "$env_file" ALERT_KEEP_LATEST true
            else
                _set_env_docker_kv "$env_file" ALERT_KEEP_LATEST false
            fi
            _set_env_docker_kv "$env_file" ALERT_USE_DIRECT_PERSIST false
            _apply_python_sink_media_env "$env_file" "${root}/${module}/.env" 1
        else
            # AI：仅同步媒体根，供 compose ${EASYAIOT_MEDIA_ROOT} 替换
            _apply_python_sink_media_env "$env_file" "${root}/${module}/.env" 0
        fi
    done
}

# 兼容旧调用名
apply_mini_python_service_env() {
    apply_python_service_deploy_env "$@"
}

# mini 形态：安装阶段将 MinIO 磁盘历史对象同步到宿主机 /data/local-storage
migrate_mini_minio_data_to_local_storage() {
    is_mini_deploy_profile || return 0
    is_edge_deploy_profile && return 0
    local root="${1:-}"
    if [ -z "$root" ]; then
        root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    fi
    local minio_seed="${root}/.scripts/minio"
    if [ ! -d "$minio_seed" ]; then
        return 0
    fi
    local ai_dir="${root}/AI"
    if [ ! -d "$ai_dir" ]; then
        return 0
    fi
    echo "mini 形态：同步 MinIO 种子数据到 /data/local-storage ..."
    if (
        cd "$ai_dir" && \
        EASYAIOT_DEPLOY_PROFILE=mini \
        MINIO_SEED_DATA_ROOT="$minio_seed" \
        LOCAL_STORAGE_ROOT="/data/local-storage" \
        python3 -c "
from app.services.local_storage_service import migrate_seed_data_to_local_storage
copied, skipped = migrate_seed_data_to_local_storage(buckets=['models'], skip_existing=True)
print(f'copied={copied} skipped={skipped}')
"
    ); then
        echo "mini 形态：MinIO 历史数据同步完成"
    else
        echo "警告: mini MinIO 历史数据同步失败，AI 启动时会再次尝试"
    fi
}

_profile_print_info() {
    if type print_info >/dev/null 2>&1; then
        print_info "$@"
    else
        echo "[INFO] $*"
    fi
}

_container_exists_by_name() {
    local name="$1"
    docker ps -a --filter "name=^${name}$" --format '{{.Names}}' 2>/dev/null | grep -qx "$name"
}

# 停止并移除当前部署形态不应运行的容器（含从 full/standard 切换后残留）
cleanup_profile_excluded_containers() {
    ensure_deploy_profile 2>/dev/null || apply_deploy_profile

    local -a to_stop=()
    local name skip found

    if is_tdengine_disabled_deploy_profile; then
        for name in tdengine-server tdengine-init; do
            _container_exists_by_name "$name" && to_stop+=("$name")
        done
    fi

    # edge 零 DEVICE，不会执行 DEVICE/install_linux.sh 的 stop_device_disabled_services
    if is_edge_deploy_profile || ! module_enabled_for_deploy_profile DEVICE; then
        for skip in $(device_skipped_services); do
            [ -z "$skip" ] && continue
            _container_exists_by_name "$skip" || continue
            found=0
            for name in "${to_stop[@]}"; do
                if [ "$name" = "$skip" ]; then
                    found=1
                    break
                fi
            done
            [ "$found" -eq 0 ] && to_stop+=("$skip")
        done
    fi

    [ ${#to_stop[@]} -eq 0 ] && return 0

    _profile_print_info "当前形态 (${EASYAIOT_DEPLOY_PROFILE}) 不部署以下容器，停止并移除: ${to_stop[*]}"
    for name in "${to_stop[@]}"; do
        docker stop "$name" >/dev/null 2>&1 || true
        docker rm -f "$name" >/dev/null 2>&1 || true
    done
}

# 根据跳过列表判断中间件是否属于当前形态
middleware_service_enabled() {
    local svc="$1"
    local skip
    for skip in $(middleware_skipped_services); do
        [ "$svc" = "$skip" ] && return 1
    done
    return 0
}
