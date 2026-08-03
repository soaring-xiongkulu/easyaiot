#!/bin/bash
# EasyAIoT 部署形态配置
#
# EASYAIOT_DEPLOY_PROFILE 取值（默认 full）：
#   mini     | 1  — 边缘精简版，推荐宿主机内存 ≥ 4 GB
#   standard | 2  — 标准版，推荐宿主机内存 ≥ 16 GB
#   full     | 3  — 完整版，推荐宿主机内存 ≥ 20 GB（默认）
#
# 各形态服务范围详见 print_deploy_profile_summary；内存占用分析见 analyze_deploy_memory.sh。

_resolve_deploy_profile_raw() {
    local p="${EASYAIOT_DEPLOY_PROFILE:-full}"
    case "$p" in
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

apply_deploy_profile() {
    EASYAIOT_DEPLOY_PROFILE="$(_resolve_deploy_profile_raw)"
    export EASYAIOT_DEPLOY_PROFILE

    case "$EASYAIOT_DEPLOY_PROFILE" in
        mini)
            export EASYAIOT_ENABLE_TDENGINE=0
            export EASYAIOT_ENABLE_EMQX=0
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

    sync_deploy_profile_to_modules
}

# docker compose --profile 参数（standard/full 启用 EMQX；full 另启 TDengine）
compose_profile_flags() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        full) echo "--profile tdengine --profile emqx" ;;
        standard) echo "--profile emqx" ;;
        *) echo "" ;;
    esac
}

# 返回空格分隔的中间件 compose 服务名（跳过列表，传给 compose_up_middleware）
middleware_skipped_services() {
    local -a skips=()
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini)
            skips+=(Nacos MinIO Milvus ZLMediaKit NodeRED FUXA TDengine TDengine-init EMQX Kafka)
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
        mini)
            skips+=(iot-gateway iot-infra iot-device iot-dataset iot-node iot-visualize iot-file iot-message iot-gb28181 iot-tdengine iot-sink)
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
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini) echo "iot-system" ;;
        *) echo "" ;;
    esac
}

# mini 形态：不部署 Nacos / Gateway，前端经 nginx 直连 iot-system 宿主机端口
is_mini_deploy_profile() {
    [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "mini" ]
}

# full 形态：含 TDengine / iot-sink 工业协议演示等完整能力
is_full_deploy_profile() {
    [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "full" ]
}

# 按部署形态判断业务模块是否启用
#   APP / VISUALIZE / TRANSFORM — 仅 full 全量形态
#   PANEL — 源码/Docker 部署默认启用；安装包（deb/桌面端）本身即为 PANEL，
#           由 systemd/二进制托管，部署时不应再拉 Docker PANEL（EASYAIOT_ENABLE_PANEL=0）。
#           无源码 runtime 未显式开启时也默认跳过。
module_enabled_for_deploy_profile() {
    case "$1" in
        APP|VISUALIZE|TRANSFORM) [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "full" ] ;;
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
        mini|standard) return 0 ;;
        *) return 1 ;;
    esac
}

# mini / standard 形态均不部署可视化（iot-visualize / VISUALIZE 编辑器 / FUXA / 相关菜单）
is_visualize_disabled_deploy_profile() {
    case "${EASYAIOT_DEPLOY_PROFILE:-full}" in
        mini|standard) return 0 ;;
        *) return 1 ;;
    esac
}

# iot-sink Spring Profile（local + 形态专用 profile）
iot_sink_spring_profiles_active() {
    if is_mini_deploy_profile; then
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
        mini|1) echo "4096" ;;
        standard|2) echo "16384" ;;
        full|3|*) echo "20480" ;;
    esac
}

deploy_profile_budget_label() {
    case "${1:-${EASYAIOT_DEPLOY_PROFILE:-full}}" in
        mini|1) echo "4 GB" ;;
        standard|2) echo "16 GB" ;;
        full|3|*) echo "20 GB" ;;
    esac
}

_deploy_profile_desc() {
    case "${EASYAIOT_DEPLOY_PROFILE:-}" in
        mini) echo "边缘精简版（推荐 ≥ 4 GB）" ;;
        standard) echo "标准版（推荐 ≥ 16 GB）" ;;
        full) echo "完整版（推荐 ≥ 20 GB）" ;;
        *) echo "完整版（推荐 ≥ 20 GB）" ;;
    esac
}

_print_deploy_profile_menu() {
    echo ""
    echo "请选择部署规格（按目标宿主机内存选型）："
    echo "  1) mini     — 边缘精简版（推荐内存 ≥ 4 GB）"
    echo "  2) standard — 标准版（推荐内存 ≥ 16 GB）"
    echo "  3) full     — 完整版（推荐内存 ≥ 20 GB，默认）"
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

print_deploy_profile_summary() {
  apply_deploy_profile
  local desc
  desc="$(_deploy_profile_desc)"
  echo "当前部署形态: ${desc} (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
  warn_web_rebuild_if_profile_changed
  case "${EASYAIOT_DEPLOY_PROFILE}" in
    mini)
      echo "  业务: iot-system（48099）, VIDEO, AI, WEB（告警由 VIDEO 直连落库，无需 iot-sink/Kafka）"
      echo "  运维: PANEL 独立控制台（:9200，所有形态默认启用）"
      echo "  中间件: PostgreSQL, Redis, SRS"
      echo "  不启动: Kafka, iot-sink, Nacos, MinIO, iot-gateway, iot-infra, Milvus, ZLMediaKit, NodeRED, FUXA, TDengine, EMQX、iot-visualize/VISUALIZE、TRANSFORM 及多数 DEVICE 模块"
      echo "  API 路由: nginx 将 /admin-api、/dev-api 直连宿主机 iot-system:48099（登录鉴权由 system 自身处理）"
      ;;
    standard)
      echo "  不启动: TDengine, NodeRED, FUXA, iot-device, iot-tdengine, iot-visualize/VISUALIZE、TRANSFORM（相关菜单不启用）"
      echo "  运维: PANEL 独立控制台（:9200，所有形态默认启用）"
      echo "  其余模块与中间件全部启动（含 EMQX）"
      ;;
    full)
      echo "  启动全部业务模块与中间件（含 APP 移动端 H5、iot-visualize/VISUALIZE、TRANSFORM、FUXA，推荐宿主机内存 ≥ 20 GB）"
      echo "  运维: PANEL 独立控制台（:9200，所有形态默认启用）"
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
    lock_deploy_profile_for_child_installs
    return 0
  fi

  # 已通过环境变量显式指定形态时不弹菜单（含交互终端）
  # 例: EASYAIOT_DEPLOY_PROFILE=full bash .../install_linux.sh install
  case "${EASYAIOT_DEPLOY_PROFILE:-}" in
    mini|standard|full)
      apply_deploy_profile
      save_deploy_profile
      lock_deploy_profile_for_child_installs
      echo ""
      if declare -F print_info >/dev/null 2>&1; then
        print_info "使用环境变量指定的部署形态: $(_deploy_profile_desc) (EASYAIOT_DEPLOY_PROFILE=${EASYAIOT_DEPLOY_PROFILE})"
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
  read -r -p "请输入选项 [1-3，默认 3]: " choice
  case "${choice:-3}" in
    1) export EASYAIOT_DEPLOY_PROFILE=mini ;;
    2) export EASYAIOT_DEPLOY_PROFILE=standard ;;
    *) export EASYAIOT_DEPLOY_PROFILE=full ;;
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
    read -r -p "请输入选项 [1-3，默认 3]: " choice
    case "${choice:-3}" in
        1) export EASYAIOT_DEPLOY_PROFILE=mini ;;
        2) export EASYAIOT_DEPLOY_PROFILE=standard ;;
        *) export EASYAIOT_DEPLOY_PROFILE=full ;;
    esac
    apply_deploy_profile
    save_deploy_profile
    echo ""
    print_deploy_profile_summary
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

# WEB：按形态写入 nginx 配置路径（compose 读 WEB/.env 中的 NGINX_CONF）
sync_web_deploy_profile_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local web_env="${root}/WEB/.env"
    local conf="./conf/nginx.conf"
    if is_mini_deploy_profile; then
        conf="./conf/nginx.mini.conf"
    fi
    [ -f "$web_env" ] || return 0
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
    apply_python_service_deploy_env "$root"
    apply_device_deploy_env "$root"
    apply_transform_deploy_env "$root"
    sync_web_deploy_profile_env "$root"
}

# DEVICE：按形态写入 .env（docker compose 自动读取，供 IOT_SYSTEM_SPRING_PROFILES_ACTIVE 等变量替换）
apply_device_deploy_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    local env_file="${root}/DEVICE/.env"
    mkdir -p "$(dirname "$env_file")"
    touch "$env_file"
    if is_mini_deploy_profile; then
        _set_env_docker_kv "$env_file" IOT_SYSTEM_SPRING_PROFILES_ACTIVE "local,mini"
    else
        _set_env_docker_kv "$env_file" IOT_SYSTEM_SPRING_PROFILES_ACTIVE "local"
    fi
    _set_env_docker_kv "$env_file" IOT_SINK_SPRING_PROFILES_ACTIVE "$(iot_sink_spring_profiles_active)"
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

# 按部署形态同步 VIDEO/AI .env.docker（mini 直连 48099 + 本地存储；standard/full 走网关 + MinIO）
apply_python_service_deploy_env() {
    local root="${1:-$(_deploy_profile_repo_root)}"
    if [ -z "$root" ]; then
        root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    fi
    local module env_file
    for module in VIDEO AI; do
        env_file="${root}/${module}/.env.docker"
        [ -f "$env_file" ] || continue
        if is_mini_deploy_profile; then
            _set_env_docker_kv "$env_file" EASYAIOT_DEPLOY_PROFILE mini
            _set_env_docker_kv "$env_file" JAVA_BACKEND_URL "http://localhost:48099"
            _set_env_docker_kv "$env_file" GATEWAY_URL "http://localhost:48099"
            _set_env_docker_kv "$env_file" AUTH_CHECK_URL "http://localhost:48099/admin-api/system/auth/get-permission-info"
            _set_env_docker_kv "$env_file" NODE_REMOTE_DEPLOY false
            if [ "$module" = "VIDEO" ]; then
                _set_env_docker_kv "$env_file" ALERT_KEEP_LATEST true
                _set_env_docker_kv "$env_file" ALERT_USE_DIRECT_PERSIST true
            fi
            if [ "$module" = "AI" ]; then
                # compose 只读挂载 ../.scripts/minio -> /minio-seed-data（flat 种子数据）
                _set_env_docker_kv "$env_file" MINIO_SEED_DATA_ROOT "/minio-seed-data"
            fi
        else
            _set_env_docker_kv "$env_file" EASYAIOT_DEPLOY_PROFILE "${EASYAIOT_DEPLOY_PROFILE:-full}"
            _set_env_docker_kv "$env_file" JAVA_BACKEND_URL "http://localhost:48080"
            _set_env_docker_kv "$env_file" GATEWAY_URL "http://localhost:48080"
            _set_env_docker_kv "$env_file" AUTH_CHECK_URL "http://localhost:48080/admin-api/system/auth/get-permission-info"
            _set_env_docker_kv "$env_file" NODE_REMOTE_DEPLOY true
            if [ "$module" = "VIDEO" ]; then
                _set_env_docker_kv "$env_file" ALERT_KEEP_LATEST false
                _set_env_docker_kv "$env_file" ALERT_USE_DIRECT_PERSIST false
            fi
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

# 根据跳过列表判断中间件是否属于当前形态
middleware_service_enabled() {
    local svc="$1"
    local skip
    for skip in $(middleware_skipped_services); do
        [ "$svc" = "$skip" ] && return 1
    done
    return 0
}
