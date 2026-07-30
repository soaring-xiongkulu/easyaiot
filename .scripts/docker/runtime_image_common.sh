#!/bin/bash
# EasyAIoT 运行时镜像公共库
# 供 runtime_image.sh、install_linux.sh、install_business_linux.sh 等脚本 source 复用。
# 调用方需先设置 SCRIPT_DIR（.scripts/docker 目录）并已 source deploy_profile.sh。

# shellcheck disable=SC2034
[[ -n "${RUNTIME_IMAGE_COMMON_LOADED:-}" ]] && return 0
RUNTIME_IMAGE_COMMON_LOADED=1

: "${SCRIPT_DIR:?runtime_image_common.sh 需要 SCRIPT_DIR}"

RUNTIME_IMAGE_SCRIPT="${RUNTIME_IMAGE_SCRIPT:-${SCRIPT_DIR}/runtime_image.sh}"
RUNTIME_IMAGES_MARKER="${RUNTIME_IMAGES_MARKER:-${SCRIPT_DIR}/.runtime_images_pulled}"
RUNTIME_REGISTRY_CONFIG="${RUNTIME_REGISTRY_CONFIG:-${SCRIPT_DIR}/runtime_registry.conf}"

# 加载后由 runtime_load_registry() 填充（可被 EASYAIOT_RUNTIME_REGISTRY 环境变量覆盖）
RUNTIME_IMAGE_REGISTRY=""

# ============================================================================
# 镜像映射表（远程名 ↔ 本地名）
# ============================================================================
DEVICE_REMOTE_NAMES=(
    aiot-gateway aiot-system aiot-infra aiot-device aiot-dataset
    aiot-node aiot-visualize aiot-tdengine aiot-file aiot-message aiot-sink aiot-gb28181
)

DEVICE_LOCAL_NAMES=(
    iot-gateway iot-module-system-biz iot-module-infra-biz iot-module-device-biz
    iot-module-dataset-biz iot-module-node-biz iot-module-visualize-biz iot-module-tdengine-biz
    iot-module-file-biz iot-module-message-biz iot-sink-biz iot-gb28181-biz
)

# 与 DEVICE_REMOTE_NAMES / DEVICE_LOCAL_NAMES 下标一一对应（docker-compose 服务名）
DEVICE_COMPOSE_SERVICES=(
    iot-gateway iot-system iot-infra iot-device iot-dataset
    iot-node iot-visualize iot-tdengine iot-file iot-message iot-sink iot-gb28181
)

INDEPENDENT_MODULES=(
    "aiot-ai|ai-service|AI"
    "aiot-video|video-service|VIDEO"
    "aiot-web|web-service|WEB"
    "aiot-panel|easyaiot/panel|PANEL"
)

# 仅 full 全量形态部署（远程名 ↔ 本地名，与 INDEPENDENT_MODULES 格式相同）
# 注意：aiot-visualize 已用于 DEVICE 后端 iot-module-visualize-biz，前端用 aiot-visualize-web
FULL_ONLY_MODULES=(
    "aiot-app|app-service|APP"
    "aiot-visualize-web|visualize-service|VISUALIZE"
    "aiot-transform|transform-service|TRANSFORM"
)

PROFILE_DEPENDENT_REMOTES=(aiot-web)
FULL_ONLY_REMOTES=(aiot-app aiot-visualize-web aiot-transform)
ALL_DEPLOY_PROFILES=(mini standard full)
ALL_RUNTIME_ARCHS=(amd64 arm64)

# ============================================================================
# 架构检测
# ============================================================================
runtime_detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64)   echo "amd64" ;;
        aarch64|arm64)  echo "arm64" ;;
        armv7l|armv6l)  echo "arm32" ;;
        *)              echo "amd64" ;;
    esac
}

runtime_arch_to_platform() {
    case "$1" in
        amd64) echo "linux/amd64" ;;
        arm64) echo "linux/arm64" ;;
        arm32) echo "linux/arm/v7" ;;
        *)     echo "linux/amd64" ;;
    esac
}

runtime_is_native_arch() {
    [ "$1" = "$(runtime_detect_arch)" ]
}

# 规范化 build-runtime 目标架构（空/all=全部；无效返回 INVALID）
runtime_normalize_build_arch() {
    local raw="${1:-}"
    raw="${raw,,}"  # bash 4+ 小写
    case "$raw" in
        ""|all) echo "" ;;
        amd64|x86_64) echo "amd64" ;;
        arm64|aarch64) echo "arm64" ;;
        arm32|armv7|armv7l) echo "arm32" ;;
        *) echo "INVALID" ;;
    esac
}

# 是否仅构建单一架构（非 all/空）
runtime_is_single_arch_build() {
    local a="${EASYAIOT_RUNTIME_BUILD_ARCH:-}"
    [ -n "$a" ] && [ "$a" != "all" ]
}

# build-runtime 可选单模块（PANEL 全形态；APP/VISUALIZE/TRANSFORM 仅 full）
ALL_RUNTIME_BUILD_MODULES=(DEVICE AI VIDEO WEB APP VISUALIZE TRANSFORM PANEL)

# 规范化 build-runtime 目标模块（空/all=全部；无效返回 INVALID）
runtime_normalize_build_module() {
    local raw="${1:-}"
    raw="${raw,,}"
    case "$raw" in
        ""|all) echo "" ;;
        device) echo "DEVICE" ;;
        ai|aiot-ai) echo "AI" ;;
        video|aiot-video) echo "VIDEO" ;;
        web|aiot-web) echo "WEB" ;;
        app|aiot-app) echo "APP" ;;
        visualize|aiot-visualize-web|goview) echo "VISUALIZE" ;;
        transform|aiot-transform) echo "TRANSFORM" ;;
        panel|aiot-panel|easyaiot/panel) echo "PANEL" ;;
        *) echo "INVALID" ;;
    esac
}

# 是否仅构建单一模块（非 all/空）
runtime_is_single_module_build() {
    [ -n "${EASYAIOT_RUNTIME_BUILD_MODULE:-}" ]
}

# 当前构建计划是否包含指定运行时模块（未指定模块时视为全部）
runtime_build_includes_module() {
    local mod="$1"
    local sel="${EASYAIOT_RUNTIME_BUILD_MODULE:-}"
    [ -z "$sel" ] || [ "$sel" = "$mod" ]
}

# 解析 build-runtime 模块 CLI/环境变量（install_*.sh 第二参数）
runtime_apply_build_module_arg() {
    local arg="${1:-${EASYAIOT_RUNTIME_BUILD_MODULE:-}}"
    [ -z "$arg" ] && return 0
    local normalized
    normalized=$(runtime_normalize_build_module "$arg")
    if [ "$normalized" = "INVALID" ]; then
        runtime_img_msg error "无效的运行时模块: ${arg}，可选: all | DEVICE | AI | VIDEO | WEB | APP | VISUALIZE | TRANSFORM | PANEL"
        return 1
    fi
    if [ -n "$normalized" ]; then
        export EASYAIOT_RUNTIME_BUILD_MODULE="$normalized"
        runtime_img_msg info "已指定模块: ${EASYAIOT_RUNTIME_BUILD_MODULE}"
    else
        unset EASYAIOT_RUNTIME_BUILD_MODULE
    fi
    return 0
}

# 单模块 APP / VISUALIZE / TRANSFORM 与部署形态兼容性校验（均仅 full）
runtime_validate_build_module_profile() {
    case "${EASYAIOT_RUNTIME_BUILD_MODULE:-}" in
        APP|VISUALIZE|TRANSFORM) ;;
        *) return 0 ;;
    esac
    if [ "${EASYAIOT_RUNTIME_BUILD_ALL_PROFILES:-0}" = "1" ]; then
        return 0
    fi
    if [ "${EASYAIOT_DEPLOY_PROFILE:-full}" != "full" ]; then
        runtime_img_msg error "${EASYAIOT_RUNTIME_BUILD_MODULE} 模块仅 full 形态可用，当前形态: ${EASYAIOT_DEPLOY_PROFILE:-未设置}"
        return 1
    fi
    return 0
}

# 解析 build-runtime 目标架构列表 → RUNTIME_RESOLVED_BUILD_ARCHS
runtime_resolve_build_archs() {
    local target normalized current a supported=false
    target="${EASYAIOT_RUNTIME_BUILD_ARCH:-}"
    RUNTIME_RESOLVED_BUILD_ARCHS=()
    current=$(runtime_detect_arch)

    if [ -z "$target" ] || [ "$target" = "all" ]; then
        RUNTIME_RESOLVED_BUILD_ARCHS+=("$current")
        for a in "${ALL_RUNTIME_ARCHS[@]}"; do
            [ "$a" = "$current" ] || RUNTIME_RESOLVED_BUILD_ARCHS+=("$a")
        done
        return 0
    fi

    normalized=$(runtime_normalize_build_arch "$target")
    if [ "$normalized" = "INVALID" ]; then
        runtime_img_msg error "无效的目标架构: ${target}，可选: all | amd64 | arm64 | arm32"
        return 1
    fi

    for a in "${ALL_RUNTIME_ARCHS[@]}"; do
        if [ "$a" = "$normalized" ]; then
            supported=true
            break
        fi
    done
    if ! $supported; then
        runtime_img_msg error "不支持的目标架构: ${normalized}，当前支持: ${ALL_RUNTIME_ARCHS[*]}"
        return 1
    fi

    RUNTIME_RESOLVED_BUILD_ARCHS=("$normalized")
    return 0
}

# ============================================================================
# 远程仓库配置（CNB）
# ============================================================================
runtime_load_registry() {
    local from_file=""
    if [ -f "$RUNTIME_REGISTRY_CONFIG" ]; then
        from_file=$(sed -n 's/^[[:space:]]*REGISTRY=//p' "$RUNTIME_REGISTRY_CONFIG" 2>/dev/null | head -1)
        from_file="${from_file//\"/}"
        from_file="${from_file//\'/}"
        from_file="${from_file%%#*}"
        from_file="${from_file// /}"
    fi
    RUNTIME_IMAGE_REGISTRY=$(runtime_normalize_registry "${EASYAIOT_RUNTIME_REGISTRY:-${from_file:-docker.cnb.cool/holmesian/easyaiot/}}")
    export RUNTIME_IMAGE_REGISTRY
}

runtime_log_registry_info() {
    runtime_load_registry
    runtime_img_msg info "========================================"
    runtime_img_msg info "  运行时镜像远程仓库"
    runtime_img_msg info "========================================"
    runtime_img_msg info "  当前地址: ${RUNTIME_IMAGE_REGISTRY}"
    runtime_img_msg info "  配置文件: ${RUNTIME_REGISTRY_CONFIG}"
    runtime_img_msg info "  更换仓库:"
    runtime_img_msg info "    1) 编辑上述配置文件，修改 REGISTRY= 一行（须以 / 结尾）"
    runtime_img_msg info "    2) 或临时指定: export EASYAIOT_RUNTIME_REGISTRY=your.cool/namespace/project/"
    runtime_img_msg info "========================================"
}

# 从 REGISTRY 地址提取主机名（如 docker.cnb.cool/holmesian/easyaiot/ → docker.cnb.cool）
runtime_registry_host() {
    local r="${1:-${REGISTRY:-$RUNTIME_IMAGE_REGISTRY}}"
    r="${r%%/*}"
    echo "$r"
}

# 检查 ~/.docker/config.json 是否已保存指定 registry 的登录凭据
runtime_docker_has_registry_auth() {
    local host="$1"
    local config="${DOCKER_CONFIG:-$HOME/.docker}/config.json"
    [ -f "$config" ] || return 1
    if ! command -v python3 >/dev/null 2>&1; then
        # 无 python3 时做简单 grep 兜底
        grep -qE "\"${host}\"|\"https://${host}\"|\"http://${host}\"" "$config" 2>/dev/null
        return $?
    fi
    python3 - "$host" "$config" <<'PY'
import json, subprocess, sys

host = sys.argv[1]
config_path = sys.argv[2]

try:
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
except OSError:
    sys.exit(1)

def has_auth_entry(entry):
    return bool(entry.get("auth") or entry.get("identitytoken"))

auths = cfg.get("auths", {})
for key in (host, f"https://{host}", f"http://{host}"):
    if has_auth_entry(auths.get(key, {})):
        sys.exit(0)

def try_cred_helper(helper, server):
    if not helper:
        return False
    cmd = f"docker-credential-{helper}"
    try:
        p = subprocess.run(
            [cmd, "get"],
            input=server.encode(),
            capture_output=True,
            timeout=10,
        )
        return p.returncode == 0 and bool(p.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return False

cred_helpers = cfg.get("credHelpers", {})
if try_cred_helper(cred_helpers.get(host), host):
    sys.exit(0)

creds_store = cfg.get("credsStore")
if try_cred_helper(creds_store, host):
    sys.exit(0)

sys.exit(1)
PY
}

# 输出 CNB 登录/权限失败时的修复指引
runtime_print_registry_auth_help() {
    local host="$1" registry="$2" reason="${3:-not_logged_in}"
    registry=$(runtime_normalize_registry "$registry")
    runtime_img_msg error "========================================"
    case "$reason" in
        no_push_access)
            runtime_img_msg error "  无法推送到 CNB 镜像仓库（权限不足或仓库路径错误）"
            ;;
        *)
            runtime_img_msg error "  未登录 CNB 镜像仓库，无法执行 build-runtime 推送"
            ;;
    esac
    runtime_img_msg error "========================================"
    runtime_img_msg error "  目标仓库: ${registry}"
    runtime_img_msg error "  Registry: ${host}"
    runtime_img_msg error ""
    runtime_img_msg error "  请先登录 CNB Docker 制品库（需具有推送权限的访问令牌 CNB_TOKEN）："
    runtime_img_msg error "    docker login ${host} -u cnb -p \${CNB_TOKEN}"
    runtime_img_msg error ""
    runtime_img_msg error "  文档: https://docs.cnb.cool/zh/artifact/docker.html"
    runtime_img_msg error ""
    runtime_img_msg error "  若已登录仍失败，请检查："
    runtime_img_msg error "    1) CNB_TOKEN 是否有效且具有该仓库的 push 权限"
    runtime_img_msg error "    2) 仓库路径是否正确: ${RUNTIME_REGISTRY_CONFIG} 中 REGISTRY= 须以 / 结尾"
    runtime_img_msg error "       当前: ${registry}"
    runtime_img_msg error "    3) 或临时指定: export EASYAIOT_RUNTIME_REGISTRY=your.cool/namespace/project/"
    runtime_img_msg error "========================================"
}

# build-runtime 开始前校验 CNB 登录与推送权限（避免构建完成后才推送失败）
runtime_verify_registry_push_access() {
    if [ "${EASYAIOT_REGISTRY_AUTH_VERIFIED:-0}" = "1" ]; then
        return 0
    fi
    if [ "${EASYAIOT_SKIP_REGISTRY_AUTH_CHECK:-0}" = "1" ]; then
        runtime_img_msg warn "已跳过 CNB 仓库登录/推送权限检查 (EASYAIOT_SKIP_REGISTRY_AUTH_CHECK=1)"
        return 0
    fi

    local registry host probe_ref push_out rc=0
    runtime_load_registry
    registry=$(runtime_normalize_registry "${1:-${REGISTRY:-$RUNTIME_IMAGE_REGISTRY}}")
    host=$(runtime_registry_host "$registry")

    runtime_img_msg info "检查 CNB 镜像仓库登录与推送权限..."
    runtime_img_msg info "  Registry: ${host}"
    runtime_img_msg info "  仓库路径: ${registry}"

    if ! runtime_docker_has_registry_auth "$host"; then
        runtime_print_registry_auth_help "$host" "$registry" "not_logged_in"
        return 1
    fi

    runtime_img_msg info "已检测到 ${host} 登录凭据，正在探测推送权限..."

    probe_ref="${registry}easyaiot-push-auth-check:__probe__"
    if ! docker image inspect hello-world:latest >/dev/null 2>&1; then
        runtime_img_msg info "拉取 hello-world（用于推送权限探测）..."
        if ! docker pull hello-world:latest >/dev/null 2>&1; then
            runtime_img_msg warn "无法拉取 hello-world，仅验证登录凭据（未探测推送权限）"
            runtime_img_msg ok "CNB 登录凭据已就绪: ${host}"
            return 0
        fi
    fi

    docker tag hello-world:latest "$probe_ref" >/dev/null 2>&1 || {
        runtime_img_msg error "创建推送探测标签失败: ${probe_ref}"
        return 1
    }

    push_out=$(docker push "$probe_ref" 2>&1) || rc=$?
    docker rmi "$probe_ref" >/dev/null 2>&1 || true

    if [ "$rc" -ne 0 ]; then
        if echo "$push_out" | grep -qiE 'no basic auth credentials|unauthorized|authentication required|authorization failed'; then
            runtime_print_registry_auth_help "$host" "$registry" "not_logged_in"
            return 1
        fi
        if echo "$push_out" | grep -qiE 'push access denied|access denied|denied'; then
            runtime_print_registry_auth_help "$host" "$registry" "no_push_access"
            runtime_img_msg error "推送探测输出:"
            echo "$push_out" | while IFS= read -r line; do runtime_img_msg error "  $line"; done
            return 1
        fi
        runtime_img_msg error "推送权限探测失败（未知错误）:"
        echo "$push_out" | while IFS= read -r line; do runtime_img_msg error "  $line"; done
        return 1
    fi

    runtime_img_msg ok "CNB 仓库登录与推送权限验证通过"
    export EASYAIOT_REGISTRY_AUTH_VERIFIED=1
    return 0
}

# 交互选择部署形态（默认 full）；非交互 / 已指定形态 / 无源码 runtime 时不弹窗
runtime_interactive_select_profile() {
    local purpose="${1:-pull}"
    if [ "${EASYAIOT_SKIP_PROFILE_PROMPT:-}" = "1" ] || [ "${EASYAIOT_SKIP_IMAGE_PROMPT:-0}" = "1" ]; then
        ensure_deploy_profile 2>/dev/null || export EASYAIOT_DEPLOY_PROFILE="${EASYAIOT_DEPLOY_PROFILE:-full}"
        return 0
    fi
    case "${EASYAIOT_DEPLOY_PROFILE:-}" in
        mini|standard|full)
            if declare -F apply_deploy_profile >/dev/null 2>&1; then
                apply_deploy_profile
                save_deploy_profile 2>/dev/null || true
            fi
            runtime_img_msg info "部署形态: $(runtime_profile_label "${EASYAIOT_DEPLOY_PROFILE}") (${EASYAIOT_DEPLOY_PROFILE})（环境变量已指定）"
            return 0
            ;;
    esac
    if [ ! -t 0 ] || runtime_is_source_free_runtime; then
        export EASYAIOT_DEPLOY_PROFILE="${EASYAIOT_DEPLOY_PROFILE:-full}"
        if declare -F apply_deploy_profile >/dev/null 2>&1; then
            apply_deploy_profile
            save_deploy_profile 2>/dev/null || true
        fi
        return 0
    fi

    echo ""
    if [ "$purpose" = "build" ]; then
        echo "请选择要构建的部署形态："
        echo "  1) mini     — 边缘精简版"
        echo "  2) standard — 标准版"
        echo "  3) full     — 完整版（默认）"
        echo "  4) 全部     — mini + standard + full"
        echo ""
        local choice=""
        read -r -p "请输入选项 [1-4，默认 3]: " choice
        case "${choice:-3}" in
            1) export EASYAIOT_DEPLOY_PROFILE=mini; unset EASYAIOT_RUNTIME_BUILD_ALL_PROFILES ;;
            2) export EASYAIOT_DEPLOY_PROFILE=standard; unset EASYAIOT_RUNTIME_BUILD_ALL_PROFILES ;;
            4) export EASYAIOT_RUNTIME_BUILD_ALL_PROFILES=1; unset EASYAIOT_DEPLOY_PROFILE ;;
            *) export EASYAIOT_DEPLOY_PROFILE=full; unset EASYAIOT_RUNTIME_BUILD_ALL_PROFILES ;;
        esac
    else
        echo "请选择要拉取的部署形态："
        echo "  1) mini     — 边缘精简版"
        echo "  2) standard — 标准版"
        echo "  3) full     — 完整版（默认）"
        echo ""
        local choice=""
        read -r -p "请输入选项 [1-3，默认 3]: " choice
        case "${choice:-3}" in
            1) export EASYAIOT_DEPLOY_PROFILE=mini ;;
            2) export EASYAIOT_DEPLOY_PROFILE=standard ;;
            *) export EASYAIOT_DEPLOY_PROFILE=full ;;
        esac
    fi

    if declare -F apply_deploy_profile >/dev/null 2>&1; then
        apply_deploy_profile
        save_deploy_profile 2>/dev/null || true
        sync_deploy_profile_to_modules 2>/dev/null || true
    fi
    if [ "${EASYAIOT_RUNTIME_BUILD_ALL_PROFILES:-0}" = "1" ]; then
        runtime_img_msg info "已选择: 全部形态 (mini + standard + full)"
    else
        runtime_img_msg info "已选择: $(runtime_profile_label "${EASYAIOT_DEPLOY_PROFILE}") (${EASYAIOT_DEPLOY_PROFILE})"
    fi
    echo ""
}

# build-runtime 交互选择目标架构（默认全部）
runtime_interactive_select_build_arch() {
    local normalized current choice idx a
    if [ -n "${EASYAIOT_RUNTIME_BUILD_ARCH:-}" ]; then
        normalized=$(runtime_normalize_build_arch "$EASYAIOT_RUNTIME_BUILD_ARCH")
        if [ "$normalized" = "INVALID" ]; then
            runtime_img_msg error "无效的目标架构: ${EASYAIOT_RUNTIME_BUILD_ARCH}，可选: all | amd64 | arm64 | arm32"
            exit 1
        fi
        if [ -n "$normalized" ]; then
            export EASYAIOT_RUNTIME_BUILD_ARCH="$normalized"
            runtime_img_msg info "已选择: 仅 ${EASYAIOT_RUNTIME_BUILD_ARCH} 架构"
        else
            unset EASYAIOT_RUNTIME_BUILD_ARCH
        fi
        return 0
    fi
    if [ ! -t 0 ]; then
        return 0
    fi

    current=$(runtime_detect_arch)
    echo ""
    echo "请选择要构建的目标架构："
    echo "  1) 全部     — 本机 + 所有支持架构（默认）"
    idx=2
    declare -A _ARCH_CHOICES=()
    for a in "${ALL_RUNTIME_ARCHS[@]}"; do
        if [ "$a" = "$current" ]; then
            echo "  ${idx}) ${a}     — 仅本机架构"
        else
            echo "  ${idx}) ${a}     — 仅该架构（跨架构构建）"
        fi
        _ARCH_CHOICES[$idx]="$a"
        idx=$((idx + 1))
    done
    echo ""
    read -r -p "请输入选项 [1-$((idx - 1))，默认 1]: " choice
    case "${choice:-1}" in
        1)
            unset EASYAIOT_RUNTIME_BUILD_ARCH
            runtime_img_msg info "已选择: 全部架构 (${ALL_RUNTIME_ARCHS[*]})"
            ;;
        *)
            if [ -n "${_ARCH_CHOICES[$choice]:-}" ]; then
                export EASYAIOT_RUNTIME_BUILD_ARCH="${_ARCH_CHOICES[$choice]}"
                runtime_img_msg info "已选择: 仅 ${EASYAIOT_RUNTIME_BUILD_ARCH} 架构"
            else
                runtime_img_msg warning "无效选项，使用默认: 全部架构"
                unset EASYAIOT_RUNTIME_BUILD_ARCH
            fi
            ;;
    esac
    echo ""
}

# build-runtime 交互选择目标模块（默认全部）
runtime_interactive_select_build_module() {
    local normalized choice idx mod
    if [ -n "${EASYAIOT_RUNTIME_BUILD_MODULE:-}" ]; then
        normalized=$(runtime_normalize_build_module "$EASYAIOT_RUNTIME_BUILD_MODULE")
        if [ "$normalized" = "INVALID" ]; then
            runtime_img_msg error "无效的运行时模块: ${EASYAIOT_RUNTIME_BUILD_MODULE}，可选: all | DEVICE | AI | VIDEO | WEB | APP | VISUALIZE | TRANSFORM | PANEL"
            exit 1
        fi
        if [ -n "$normalized" ]; then
            export EASYAIOT_RUNTIME_BUILD_MODULE="$normalized"
            runtime_img_msg info "已选择模块: ${EASYAIOT_RUNTIME_BUILD_MODULE}"
        else
            unset EASYAIOT_RUNTIME_BUILD_MODULE
        fi
        return 0
    fi
    if [ ! -t 0 ]; then
        return 0
    fi

    echo ""
    echo "请选择要构建/推送的运行时模块："
    echo "  1) 全部     — DEVICE + AI + VIDEO + WEB + APP + VISUALIZE + TRANSFORM + PANEL（默认）"
    idx=2
    declare -A _MODULE_CHOICES=()
    for mod in "${ALL_RUNTIME_BUILD_MODULES[@]}"; do
        case "$mod" in
            DEVICE) echo "  ${idx}) DEVICE    — Device 微服务（含 aiot-visualize 后台）" ;;
            AI)     echo "  ${idx}) AI        — AI 服务" ;;
            VIDEO)  echo "  ${idx}) VIDEO     — Video 服务" ;;
            WEB)    echo "  ${idx}) WEB       — Web 前端（按上方所选部署形态）" ;;
            APP)    echo "  ${idx}) APP       — App 移动端 H5（仅 full 形态）" ;;
            VISUALIZE) echo "  ${idx}) VISUALIZE — 可视化编辑器（仅 full 形态）" ;;
            TRANSFORM) echo "  ${idx}) TRANSFORM — 系统对接 Runtime（仅 full 形态）" ;;
            PANEL)  echo "  ${idx}) PANEL     — 独立运维控制台（全形态）" ;;
        esac
        _MODULE_CHOICES[$idx]="$mod"
        idx=$((idx + 1))
    done
    echo ""
    read -r -p "请输入选项 [1-$((idx - 1))，默认 1]: " choice
    case "${choice:-1}" in
        1)
            unset EASYAIOT_RUNTIME_BUILD_MODULE
            runtime_img_msg info "已选择: 全部模块"
            ;;
        *)
            if [ -n "${_MODULE_CHOICES[$choice]:-}" ]; then
                export EASYAIOT_RUNTIME_BUILD_MODULE="${_MODULE_CHOICES[$choice]}"
                runtime_img_msg info "已选择模块: ${EASYAIOT_RUNTIME_BUILD_MODULE}"
            else
                runtime_img_msg warning "无效选项，使用默认: 全部模块"
                unset EASYAIOT_RUNTIME_BUILD_MODULE
            fi
            ;;
    esac
    echo ""
}

runtime_interactive_select_tag() {
    if [ -n "${EASYAIOT_RUNTIME_TAG:-}" ]; then
        return 0
    fi
    # PANEL 无源码 / 非交互 / 已跳过镜像菜单：默认 latest，不打断 install
    if [ ! -t 0 ] \
        || [ "${EASYAIOT_SKIP_IMAGE_PROMPT:-0}" = "1" ] \
        || [ "${EASYAIOT_SKIP_PROFILE_PROMPT:-}" = "1" ] \
        || runtime_is_source_free_runtime; then
        export EASYAIOT_RUNTIME_TAG="${TAG:-latest}"
        runtime_img_msg info "镜像标签: ${EASYAIOT_RUNTIME_TAG}（自动）"
        return 0
    fi
    local tag_input=""
    read -r -p "镜像版本标签 [默认 latest]: " tag_input
    export EASYAIOT_RUNTIME_TAG="${tag_input:-latest}"
    runtime_img_msg info "镜像标签: ${EASYAIOT_RUNTIME_TAG}"
}

runtime_interactive_confirm_push() {
    if [ -n "${EASYAIOT_RUNTIME_PUSH:-}" ]; then
        return 0
    fi
    if [ ! -t 0 ]; then
        export EASYAIOT_RUNTIME_PUSH="${EASYAIOT_RUNTIME_PUSH:-0}"
        return 0
    fi
    echo ""
    read -r -p "构建完成后推送到远程仓库？(Y/n) " push_resp
    case "${push_resp:-Y}" in
        n|N|no|NO) export EASYAIOT_RUNTIME_PUSH=0 ;;
        *) export EASYAIOT_RUNTIME_PUSH=1 ;;
    esac
}

runtime_interactive_confirm_force_rebuild() {
    if [ -n "${EASYAIOT_RUNTIME_FORCE_REBUILD:-}" ]; then
        return 0
    fi
    if [ "${FORCE_REBUILD:-}" = "true" ]; then
        export EASYAIOT_RUNTIME_FORCE_REBUILD=1
        return 0
    fi
    if [ ! -t 0 ]; then
        export EASYAIOT_RUNTIME_FORCE_REBUILD="${EASYAIOT_RUNTIME_FORCE_REBUILD:-0}"
        return 0
    fi
    echo ""
    local fr=""
    read -r -p "强制重新构建全部镜像（忽略本地缓存）？(y/N) " fr
    case "${fr:-N}" in
        y|Y|yes|YES) export EASYAIOT_RUNTIME_FORCE_REBUILD=1 ;;
        *) export EASYAIOT_RUNTIME_FORCE_REBUILD=0 ;;
    esac
    if [ "${EASYAIOT_RUNTIME_FORCE_REBUILD}" = "1" ]; then
        runtime_img_msg info "已选择: 强制重新构建（忽略本地镜像缓存）"
    fi
}

# pull 前配置：无源码 / 非交互 / 已跳过菜单时不询问 tag/profile
runtime_images_prepare_pull_interactive() {
    runtime_log_registry_info
    if [ ! -t 0 ] \
        || [ "${EASYAIOT_SKIP_IMAGE_PROMPT:-0}" = "1" ] \
        || [ "${EASYAIOT_SKIP_PROFILE_PROMPT:-}" = "1" ] \
        || runtime_is_source_free_runtime; then
        export EASYAIOT_DEPLOY_PROFILE="${EASYAIOT_DEPLOY_PROFILE:-full}"
        export EASYAIOT_RUNTIME_TAG="${EASYAIOT_RUNTIME_TAG:-${TAG:-latest}}"
        if declare -F apply_deploy_profile >/dev/null 2>&1; then
            apply_deploy_profile
            save_deploy_profile 2>/dev/null || true
        fi
        runtime_img_msg info "拉取参数: profile=${EASYAIOT_DEPLOY_PROFILE}, tag=${EASYAIOT_RUNTIME_TAG}"
    else
        runtime_interactive_select_profile pull
        runtime_interactive_select_tag
    fi
    runtime_load_registry
    export EASYAIOT_RUNTIME_REGISTRY="$RUNTIME_IMAGE_REGISTRY"
    export REGISTRY="$RUNTIME_IMAGE_REGISTRY"
}

# build-runtime 前交互配置
runtime_images_prepare_build_interactive() {
    runtime_log_registry_info
    runtime_load_registry
    export EASYAIOT_RUNTIME_REGISTRY="$RUNTIME_IMAGE_REGISTRY"
    export REGISTRY="$RUNTIME_IMAGE_REGISTRY"
    runtime_verify_registry_push_access "$RUNTIME_IMAGE_REGISTRY" || exit 1
    runtime_interactive_select_profile build
    runtime_interactive_select_build_module
    runtime_validate_build_module_profile || exit 1
    runtime_interactive_select_build_arch
    runtime_interactive_select_tag
    runtime_interactive_confirm_push
    runtime_interactive_confirm_force_rebuild
}

# 将交互/环境变量导出给 runtime_image.sh 子进程
runtime_images_export_for_invoke() {
    runtime_load_registry
    export EASYAIOT_RUNTIME_REGISTRY="${EASYAIOT_RUNTIME_REGISTRY:-$RUNTIME_IMAGE_REGISTRY}"
    export REGISTRY="${REGISTRY:-$EASYAIOT_RUNTIME_REGISTRY}"
    if [ -n "${EASYAIOT_RUNTIME_TAG:-}" ]; then
        export EASYAIOT_RUNTIME_TAG
        export TAG="$EASYAIOT_RUNTIME_TAG"
    fi
    if [ "${EASYAIOT_RUNTIME_PUSH:-0}" = "1" ] || [ "${EASYAIOT_RUNTIME_PUSH:-}" = "true" ]; then
        export EASYAIOT_RUNTIME_PUSH=1
    fi
    if [ "${EASYAIOT_RUNTIME_FORCE_REBUILD:-0}" = "1" ]; then
        export EASYAIOT_RUNTIME_FORCE_REBUILD=1
        export FORCE_REBUILD=true
    else
        export EASYAIOT_RUNTIME_FORCE_REBUILD=0
        export FORCE_REBUILD=false
    fi
    if [ "${EASYAIOT_RUNTIME_FORCE_PULL:-0}" = "1" ]; then
        export EASYAIOT_RUNTIME_FORCE_PULL=1
    fi
    if [ -n "${EASYAIOT_DEPLOY_PROFILE:-}" ] && [ "${EASYAIOT_RUNTIME_BUILD_ALL_PROFILES:-0}" != "1" ]; then
        export EASYAIOT_RUNTIME_EXPLICIT_PROFILE="$EASYAIOT_DEPLOY_PROFILE"
    fi
    if [ "${EASYAIOT_RUNTIME_BUILD_ALL_PROFILES:-0}" = "1" ]; then
        unset EASYAIOT_RUNTIME_EXPLICIT_PROFILE
    fi
    if [ -n "${EASYAIOT_RUNTIME_BUILD_ARCH:-}" ]; then
        local _ba; _ba=$(runtime_normalize_build_arch "$EASYAIOT_RUNTIME_BUILD_ARCH")
        if [ "$_ba" = "INVALID" ]; then
            runtime_img_msg error "无效的目标架构: ${EASYAIOT_RUNTIME_BUILD_ARCH}"
            exit 1
        fi
        if [ -n "$_ba" ]; then
            export EASYAIOT_RUNTIME_BUILD_ARCH="$_ba"
        else
            unset EASYAIOT_RUNTIME_BUILD_ARCH
        fi
    fi
    if [ -n "${EASYAIOT_RUNTIME_BUILD_MODULE:-}" ]; then
        local _bm; _bm=$(runtime_normalize_build_module "$EASYAIOT_RUNTIME_BUILD_MODULE")
        if [ "$_bm" = "INVALID" ]; then
            runtime_img_msg error "无效的运行时模块: ${EASYAIOT_RUNTIME_BUILD_MODULE}"
            exit 1
        fi
        if [ -n "$_bm" ]; then
            export EASYAIOT_RUNTIME_BUILD_MODULE="$_bm"
        else
            unset EASYAIOT_RUNTIME_BUILD_MODULE
        fi
    fi
}

# ============================================================================
# 镜像引用命名（v3：形态在镜像名，架构在标签）
# ============================================================================
runtime_normalize_registry() {
    local r="${1:-$RUNTIME_IMAGE_REGISTRY}"
    [[ "$r" != */ ]] && r="${r}/"
    echo "$r"
}

runtime_remote_ref() {
    local name="$1" profile="${2:-}" arch="${3:-$(runtime_detect_arch)}"
    local registry; registry=$(runtime_normalize_registry "${REGISTRY:-$RUNTIME_IMAGE_REGISTRY}")
    local image_name="${name}"
    [ -n "$profile" ] && [ "$profile" != "full" ] && image_name="${name}-${profile}"
    echo "${registry}${image_name}:${arch}"
}

runtime_manifest_ref() {
    local name="$1" profile="${2:-}"
    local registry; registry=$(runtime_normalize_registry "${REGISTRY:-$RUNTIME_IMAGE_REGISTRY}")
    local tag="${TAG:-latest}"
    local image_name="${name}"
    [ -n "$profile" ] && [ "$profile" != "full" ] && image_name="${name}-${profile}"
    echo "${registry}${image_name}:${tag}"
}

runtime_local_ref() {
    local name="$1" profile="${2:-}"
    local tag="${TAG:-latest}"
    local ref="${name}:${tag}"
    [ -n "$profile" ] && [ "$profile" != "full" ] && ref="${ref}-${profile}"
    echo "$ref"
}

runtime_is_profile_dependent() {
    local r="$1"
    for x in "${PROFILE_DEPENDENT_REMOTES[@]}"; do
        [ "$x" = "$r" ] && return 0
    done
    return 1
}

runtime_is_full_only() {
    local r="$1"
    for x in "${FULL_ONLY_REMOTES[@]}"; do
        [ "$x" = "$r" ] && return 0
    done
    return 1
}

runtime_profile_label() {
    case "$1" in
        mini) echo "边缘精简版" ;;
        standard) echo "标准版" ;;
        full) echo "完整版" ;;
        *) echo "$1" ;;
    esac
}

# pull / install 就绪检测：该 DEVICE 镜像是否属于当前部署形态实际会启动的服务
# 逻辑与 deploy_profile.sh 中 device_skipped_services / device_enabled_services 一致
runtime_device_image_needed_for_pull() {
    local idx="$1" profile="${2:-${EASYAIOT_DEPLOY_PROFILE:-full}}"
    local compose_svc="${DEVICE_COMPOSE_SERVICES[$idx]:-}"
    [ -z "$compose_svc" ] && return 1

    if ! declare -F device_skipped_services >/dev/null 2>&1 \
        || ! declare -F device_enabled_services >/dev/null 2>&1; then
        return 0
    fi

    local saved_profile="${EASYAIOT_DEPLOY_PROFILE:-full}"
    local enabled="" skips="" e s
    export EASYAIOT_DEPLOY_PROFILE="$profile"
    enabled=$(device_enabled_services)
    skips=$(device_skipped_services)
    export EASYAIOT_DEPLOY_PROFILE="$saved_profile"

    if [ -n "$enabled" ]; then
        for e in $enabled; do
            [ "$e" = "$compose_svc" ] && return 0
        done
        return 1
    fi
    for s in $skips; do
        [ "$s" = "$compose_svc" ] && return 1
    done
    return 0
}

runtime_device_pull_count_for_profile() {
    local profile="$1" count=0 i
    for i in "${!DEVICE_REMOTE_NAMES[@]}"; do
        runtime_device_image_needed_for_pull "$i" "$profile" && count=$((count + 1))
    done
    echo "$count"
}

# ============================================================================
# 本地镜像架构检测（预下载链路）
# ============================================================================
runtime_image_actual_arch() {
    docker image inspect "$1" --format '{{.Architecture}}' 2>/dev/null || echo ""
}

# 本地镜像存在且架构与期望一致
runtime_local_image_arch_ready() {
    local ref="$1" expected="${2:-$(runtime_detect_arch)}"
    if ! docker image inspect "$ref" >/dev/null 2>&1; then
        return 1
    fi
    local actual; actual=$(runtime_image_actual_arch "$ref")
    [ -n "$actual" ] && [ "$actual" = "$expected" ]
}

# 收集当前部署形态下需校验的本地运行时镜像引用
# 用法: runtime_images_collect_check_refs <数组名> [profile] [tag]
runtime_images_collect_check_refs() {
    local -n _out="$1"
    local profile="${2:-${EASYAIOT_DEPLOY_PROFILE:-full}}"
    local tag="${3:-latest}"
    _out=(
        "ai-service:${tag}"
        "video-service:${tag}"
    )
    local _di _dlname
    for _di in "${!DEVICE_LOCAL_NAMES[@]}"; do
        if runtime_device_image_needed_for_pull "$_di" "$profile"; then
            _dlname="${DEVICE_LOCAL_NAMES[$_di]}"
            _out+=("${_dlname}:${tag}")
        fi
    done
    case "$profile" in
        mini)     _out+=("web-service:${tag}-mini") ;;
        standard) _out+=("web-service:${tag}-standard") ;;
        *)        _out+=("web-service:${tag}") ;;
    esac
    if [ "$profile" = "full" ]; then
        _out+=("app-service:${tag}")
    fi
}

# 删除与当前系统架构不一致的本地预构建镜像；清除无效拉取标记
runtime_images_ensure_arch_consistency() {
    local expected_arch="${1:-$(runtime_detect_arch)}"
    local profile="${2:-${EASYAIOT_DEPLOY_PROFILE:-full}}"
    local tag="${3:-latest}"
    local marker="${RUNTIME_IMAGES_MARKER}"

    if [ -f "$marker" ]; then
        local pull_arch
        pull_arch=$(sed -n 's/^PULL_ARCH=//p' "$marker" 2>/dev/null || true)
        if [ -n "${pull_arch:-}" ] && [ "$pull_arch" != "$expected_arch" ]; then
            runtime_img_msg info "拉取标记架构 (${pull_arch}) 与当前系统 (${expected_arch}) 不一致，清除标记"
            rm -f "$marker"
        fi
    fi

    local -a refs=()
    runtime_images_collect_check_refs refs "$profile" "$tag"
    local ref actual cleaned=0
    for ref in "${refs[@]}"; do
        if ! docker image inspect "$ref" >/dev/null 2>&1; then
            continue
        fi
        actual=$(runtime_image_actual_arch "$ref")
        if [ -z "$actual" ] || [ "$actual" != "$expected_arch" ]; then
            runtime_img_msg info "镜像架构不匹配: ${ref} (现有=${actual:-?}, 期望=${expected_arch})，删除后重新拉取"
            docker rmi "$ref" 2>/dev/null || true
            cleaned=$((cleaned + 1))
            rm -f "$marker"
        fi
    done
    if [ "$cleaned" -gt 0 ]; then
        runtime_img_msg info "已清理 ${cleaned} 个架构不匹配的预构建镜像"
    fi
}

# pull 时：镜像已存在且架构正确则跳过；否则删除错误架构后返回需拉取
# update 流程设置 EASYAIOT_RUNTIME_FORCE_PULL=1 时强制拉取最新镜像（不跳过已有）
runtime_pull_should_skip_image() {
    local ref="$1" expected="${2:-$(runtime_detect_arch)}"
    if [ "${EASYAIOT_RUNTIME_FORCE_PULL:-0}" = "1" ]; then
        return 1
    fi
    if runtime_local_image_arch_ready "$ref" "$expected"; then
        return 0
    fi
    if docker image inspect "$ref" >/dev/null 2>&1; then
        local actual; actual=$(runtime_image_actual_arch "$ref")
        runtime_img_msg info "镜像架构不匹配: ${ref} (现有=${actual:-?}, 期望=${expected})，删除后重新拉取"
        docker rmi "$ref" 2>/dev/null || true
        rm -f "${RUNTIME_IMAGES_MARKER}"
    fi
    return 1
}

# ============================================================================
# 拉取标记与本地镜像就绪检测
# ============================================================================
# 规范化标记中的本地镜像 tag（历史包曾误写 embedded，等价于 latest）
runtime_normalize_pull_tag() {
    case "${1:-latest}" in
        ""|embedded|package|source-free|source_free) echo "latest" ;;
        *) echo "$1" ;;
    esac
}

# PANEL/deb 无源码 runtime：禁止回退到本地 docker build
runtime_is_source_free_runtime() {
    local root="${PROJECT_ROOT:-}"
    local marker="${RUNTIME_IMAGES_MARKER}"
    if [ -f "${SCRIPT_DIR}/.source_free_runtime" ]; then
        return 0
    fi
    if [ -f "$marker" ] && grep -qE '^(SOURCE_FREE=1|# Generated by COMPILE .*source-free)' "$marker" 2>/dev/null; then
        return 0
    fi
    # 启发式：DEVICE 仅有部署脚本、无 pom.xml
    if [ -n "$root" ] && [ -f "${root}/DEVICE/install_linux.sh" ] && [ ! -f "${root}/DEVICE/pom.xml" ]; then
        return 0
    fi
    return 1
}

# 写入/刷新拉取标记（供 pull 成功或部分成功后复用）
runtime_images_write_pulled_marker() {
    local arch="${1:-$(runtime_detect_arch)}"
    local profile="${2:-${EASYAIOT_DEPLOY_PROFILE:-full}}"
    local tag
    tag="$(runtime_normalize_pull_tag "${3:-latest}")"
    local marker="${RUNTIME_IMAGES_MARKER}"
    local source_free_line=""
    if runtime_is_source_free_runtime || [ -f "${SCRIPT_DIR}/.source_free_runtime" ]; then
        source_free_line="SOURCE_FREE=1"
    fi
    mkdir -p "$(dirname "$marker")"
    cat > "$marker" <<EOF
# EasyAIoT 运行时镜像拉取标记
# 此文件由 runtime_image.sh / install 自动生成或刷新
# 各平台 install 脚本检测到此文件后会跳过 docker build，直接启动服务
PULL_TIME=$(date '+%Y-%m-%d %H:%M:%S')
PULL_ARCH=${arch}
PULL_PROFILE=${profile}
PULL_TAG=${tag}
${source_free_line}
EOF
}

# 返回 0 = 已拉取且本地镜像齐全，可跳过构建
runtime_images_pulled_ready() {
    local marker="${RUNTIME_IMAGES_MARKER}"
    if [ ! -f "$marker" ]; then
        return 1
    fi

    local pull_arch="" pull_profile="" pull_tag=""
    pull_arch=$(sed -n 's/^PULL_ARCH=//p' "$marker" 2>/dev/null || true)
    pull_profile=$(sed -n 's/^PULL_PROFILE=//p' "$marker" 2>/dev/null || true)
    pull_tag=$(sed -n 's/^PULL_TAG=//p' "$marker" 2>/dev/null || true)
    pull_tag="$(runtime_normalize_pull_tag "$pull_tag")"

    local current_arch; current_arch=$(runtime_detect_arch)
    if [ "${pull_arch:-}" != "$current_arch" ]; then
        runtime_img_msg info "拉取标记架构 (${pull_arch:-?}) 与当前系统 (${current_arch}) 不一致，将重新拉取"
        rm -f "$marker"
        return 1
    fi

    if declare -F ensure_deploy_profile >/dev/null 2>&1; then
        ensure_deploy_profile
    fi
    local current_profile="${EASYAIOT_DEPLOY_PROFILE:-full}"
    if [ "${pull_profile:-full}" != "$current_profile" ]; then
        runtime_img_msg info "拉取标记形态 (${pull_profile:-full}) 与当前 (${current_profile}) 不匹配，将重新拉取"
        return 1
    fi

    local -a check_images=()
    runtime_images_collect_check_refs check_images "${pull_profile:-full}" "${pull_tag}"

    local img actual
    for img in "${check_images[@]}"; do
        if ! runtime_local_image_arch_ready "$img" "$current_arch"; then
            if docker image inspect "$img" >/dev/null 2>&1; then
                actual=$(runtime_image_actual_arch "$img")
                runtime_img_msg warn "本地镜像 ${img} 架构 (${actual:-?}) 与当前系统 (${current_arch}) 不一致，将重新拉取"
                rm -f "$marker"
            else
                runtime_img_msg warn "预构建镜像 ${img} 不在本地，将重新拉取"
            fi
            return 1
        fi
    done

    # 兼容旧包：标记里曾写 PULL_TAG=embedded，校验用 latest 通过后写回正确标记
    local raw_tag
    raw_tag=$(sed -n 's/^PULL_TAG=//p' "$marker" 2>/dev/null || true)
    if [ "${raw_tag}" != "${pull_tag}" ]; then
        runtime_images_write_pulled_marker "$current_arch" "${pull_profile:-full}" "$pull_tag"
    fi

    runtime_img_msg ok "检测到预构建镜像已就绪 (${pull_arch}, ${pull_profile:-full})，跳过构建"
    return 0
}

# 判断 docker push 输出是否为可重试的瞬时网络/服务端错误
runtime_docker_push_is_transient_error() {
    local output="$1"
    echo "$output" | grep -qiE \
        'use of closed network connection|connection reset by peer|broken pipe|unexpected EOF|EOF|i/o timeout|temporary failure|timeout|network is unreachable|TLS handshake timeout|read: connection|write tcp.*443:|failed to copy: failed to do request|502 Bad Gateway|503 Service Unavailable|504 Gateway Timeout|server closed idle connection|transport is closing'
}

# 带重试执行镜像上传命令（docker push / docker manifest push 等；已推送层会自动复用）
# 环境变量: EASYAIOT_DOCKER_PUSH_RETRIES（默认 8）, EASYAIOT_DOCKER_PUSH_RETRY_DELAY（默认 10，秒，指数退避）
runtime_docker_upload_with_retry() {
    local label="$1"
    shift
    local max_retries="${EASYAIOT_DOCKER_PUSH_RETRIES:-8}"
    local base_delay="${EASYAIOT_DOCKER_PUSH_RETRY_DELAY:-10}"
    local attempt=1 rc=0 delay=0 log_file push_out err_tail

    log_file=$(mktemp "${TMPDIR:-/tmp}/easyaiot_docker_push.XXXXXX") || return 1

    while [ "$attempt" -le "$max_retries" ]; do
        if [ "$attempt" -gt 1 ]; then
            case $((attempt - 1)) in
                1) delay=$base_delay ;;
                2) delay=$((base_delay * 2)) ;;
                3) delay=$((base_delay * 4)) ;;
                4) delay=$((base_delay * 8)) ;;
                *) delay=120 ;;
            esac
            [ "$delay" -gt 120 ] && delay=120
            runtime_img_msg warn "${label} 失败（第 ${attempt}/${max_retries} 次），${delay}s 后重试（已推送层会自动复用）..."
            sleep "$delay"
        fi

        : > "$log_file"
        "$@" 2>&1 | tee "$log_file"
        rc=${PIPESTATUS[0]}
        if [ "$rc" -eq 0 ]; then
            rm -f "$log_file"
            return 0
        fi

        push_out=$(cat "$log_file" 2>/dev/null || true)

        # 认证/权限错误不可重试
        if echo "$push_out" | grep -qiE 'no basic auth credentials|unauthorized|authentication required|authorization failed|push access denied|access denied|denied: requested access'; then
            runtime_docker_log_push_failure "$label" "$push_out"
            rm -f "$log_file"
            return "$rc"
        fi

        if [ "$attempt" -ge "$max_retries" ] || ! runtime_docker_push_is_transient_error "$push_out"; then
            runtime_docker_log_push_failure "$label" "$push_out"
            rm -f "$log_file"
            return "$rc"
        fi

        # 中间失败也记一行摘要，便于对照主日志
        err_tail=$(echo "$push_out" | grep -iE 'error|denied|timeout|EOF|reset|broken pipe|unauthorized|failed' | tail -n 3)
        if [ -n "$err_tail" ]; then
            while IFS= read -r line; do
                [ -n "$line" ] && runtime_img_msg warn "  → ${line}"
            done <<< "$err_tail"
        fi

        attempt=$((attempt + 1))
    done

    rm -f "$log_file"
    return 1
}

# 将 docker push 失败摘要写入主日志（tee 输出默认不进 LOG_FILE）
runtime_docker_log_push_failure() {
    local label="$1" push_out="$2" line
    runtime_img_msg error "${label} 失败，docker 输出摘要:"
    while IFS= read -r line; do
        [ -n "$line" ] && runtime_img_msg error "  ${line}"
    done <<< "$(echo "$push_out" | tail -n 40)"
}

# 带重试的 docker push
runtime_docker_push_with_retry() {
    runtime_docker_upload_with_retry "推送 $1" docker push "$1"
}

# 轻量消息输出（source 方有 print_* 时复用）
runtime_img_msg() {
    local level="$1" text="$2"
    case "$level" in
        info)
            if declare -F print_info >/dev/null 2>&1; then print_info "$text"; else echo "[INFO] $text"; fi ;;
        warn)
            if declare -F print_warning >/dev/null 2>&1; then print_warning "$text"; else echo "[WARN] $text"; fi ;;
        ok)
            if declare -F print_success >/dev/null 2>&1; then print_success "$text"; else echo "[OK] $text"; fi ;;
        error)
            if declare -F print_error >/dev/null 2>&1; then print_error "$text"; else echo "[ERROR] $text"; fi ;;
        *) echo "$text" ;;
    esac
}

# ============================================================================
# 本地构建指引（install 用户专用）
# ============================================================================
# 推断当前应使用的 install 入口（可由各 install 脚本 export EASYAIOT_INSTALL_SCRIPT 覆盖）
runtime_guess_install_script() {
    if [ -n "${EASYAIOT_INSTALL_SCRIPT:-}" ]; then
        echo "$EASYAIOT_INSTALL_SCRIPT"
        return 0
    fi
    local arch
    arch=$(runtime_detect_arch)
    case "$arch" in
        arm64|arm32)
            if [ -f /etc/.kyinfo ] || { [ -f /etc/os-release ] && grep -qiE 'kylin|neokylin' /etc/os-release; }; then
                echo ".scripts/docker/install_linux_kylin.sh"
            else
                echo ".scripts/docker/install_linux_arm.sh"
            fi
            ;;
        *)
            echo ".scripts/docker/install_linux.sh"
            ;;
    esac
}

# 预构建镜像拉取失败或用户选择本地构建时的手动构建指引
# context: install = install 流程内（将自动继续本地构建）; pull = 独立 pull 命令失败
runtime_print_install_local_build_help() {
    local context="${1:-pull}"
    local install_script profile
    install_script=$(runtime_guess_install_script)
    profile="${EASYAIOT_DEPLOY_PROFILE:-full}"

    echo ""
    runtime_img_msg warn "========================================"
    runtime_img_msg warn "  预构建镜像不可用 — 本地构建指引"
    runtime_img_msg warn "========================================"
    if [ "$context" = "install" ] || [ "$context" = "update" ]; then
        runtime_img_msg info "${context} 将自动在各模块执行 docker build，一般无需额外操作。"
        runtime_img_msg info "若 ${context} 已中断或需分步执行，可参考以下命令："
    else
        runtime_img_msg info "请在本机编译并制作 Docker 镜像，可使用以下命令："
    fi
    echo ""
    runtime_img_msg info "方案 1（推荐）：一键安装（含本地构建）"
    runtime_img_msg info "  bash ${install_script} install"
    runtime_img_msg info "  交互提示「是否从远程仓库下载预构建的镜像？」时输入 n 可主动选择本地构建。"
    echo ""
    runtime_img_msg info "方案 2：先构建镜像，再启动服务"
    runtime_img_msg info "  bash ${install_script} build     # 各模块 docker build（耗时较长）"
    runtime_img_msg info "  bash ${install_script} start     # 镜像就绪后启动"
    echo ""
    if [ "$install_script" = ".scripts/docker/install_business_linux.sh" ]; then
        runtime_img_msg info "（当前脚本仅含业务模块 DEVICE/AI/VIDEO/WEB/APP/VISUALIZE/TRANSFORM/PANEL，不含中间件）"
    else
        runtime_img_msg info "方案 3：仅构建/安装单个模块（示例 DEVICE）"
        runtime_img_msg info "  bash DEVICE/install_linux.sh build"
        runtime_img_msg info "  bash DEVICE/install_linux.sh install"
        echo ""
        runtime_img_msg info "若中间件（Nacos/PostgreSQL 等）已单独部署，仅需业务模块："
        runtime_img_msg info "  bash .scripts/docker/install_business_linux.sh install"
    fi
    echo ""
    runtime_img_msg info "非交互环境（无 TTY，默认尝试拉取预构建镜像）："
    runtime_img_msg info "  rm -f .scripts/docker/.runtime_images_pulled"
    runtime_img_msg info "  bash ${install_script} build && bash ${install_script} install"
    echo ""
    runtime_img_msg info "当前部署形态: ${profile}（EASYAIOT_DEPLOY_PROFILE=mini|standard|full）"
    runtime_img_msg info "预计耗时: 视机器配置约 30 分钟～数小时，请确保磁盘空间充足。"
    runtime_img_msg warn "========================================"
    echo ""
}

# ============================================================================
# 统一镜像获取（install / install_business 共用）
# ============================================================================
# 交互询问拉取或本地构建；成功拉取后设置 EASYAIOT_SKIP_BUILD 与 EASYAIOT_SKIP_IMAGE_PROMPT
runtime_images_acquire() {
    local skip_prompt="${1:-0}"
    local do_local_build=0
    local source_free=0
    if runtime_is_source_free_runtime; then
        source_free=1
    fi

    # 无源码 runtime（PANEL 包）只能拉预构建镜像，禁止弹「本地构建」菜单
    if [ "$source_free" -eq 1 ]; then
        skip_prompt=1
        export EASYAIOT_SKIP_IMAGE_PROMPT=1
        export EASYAIOT_RUNTIME_TAG="${EASYAIOT_RUNTIME_TAG:-latest}"
        if runtime_images_pulled_ready; then
            runtime_img_msg info "无源码 runtime：预构建镜像已就绪，跳过拉取与构建"
            export EASYAIOT_SKIP_BUILD=1
            return 0
        fi
        runtime_img_msg info "无源码 runtime（PANEL）：自动拉取预构建镜像（不支持本地 docker build）"
    fi

    if [ "$skip_prompt" != "1" ] && [ "${EASYAIOT_SKIP_IMAGE_PROMPT:-0}" != "1" ]; then
        if [ -t 0 ]; then
            runtime_img_msg info "========================================"
            runtime_img_msg info "  镜像获取方式"
            runtime_img_msg info "========================================"
            runtime_img_msg info "  1) 拉取预构建镜像：从远程仓库下载（快速，默认）"
            runtime_img_msg info "  2) 本地构建：编译并制作 Docker 镜像（耗时较长）"
            echo ""
            read -r -p "是否从远程仓库下载预构建的镜像？(Y/n) " _pull_response
            case "${_pull_response:-Y}" in
                n|N|no|NO)
                    do_local_build=1
                    runtime_img_msg info "已选择本地构建，install 将在各模块自动执行 docker build（耗时较长）"
                    ;;
                *) do_local_build=0 ;;
            esac
        else
            runtime_img_msg info "非交互模式，默认拉取预构建镜像"
        fi
    elif [ "$source_free" -eq 0 ] && runtime_images_pulled_ready; then
        export EASYAIOT_SKIP_BUILD=1
        export EASYAIOT_SKIP_IMAGE_PROMPT=1
        return 0
    fi

    if [ "$do_local_build" -eq 1 ] && [ "$source_free" -eq 1 ]; then
        runtime_img_msg warn "无源码 runtime 不支持本地构建，改为拉取预构建镜像"
        do_local_build=0
    fi

    if [ "$do_local_build" -eq 0 ]; then
        runtime_img_msg info "正在拉取预构建镜像..."
        runtime_images_prepare_pull_interactive
        runtime_images_export_for_invoke
        if runtime_images_invoke pull; then
            runtime_img_msg ok "预构建镜像拉取成功"
            export EASYAIOT_SKIP_BUILD=1
        elif runtime_images_pulled_ready; then
            # 个别镜像（如尚未发布的 aiot-transform）失败时，核心镜像仍可能已就绪
            runtime_img_msg warn "部分远程镜像拉取失败，但本地核心预构建镜像已就绪，将跳过构建并继续安装"
            export EASYAIOT_SKIP_BUILD=1
            do_local_build=0
        else
            if [ "$source_free" -eq 1 ]; then
                runtime_img_msg error "预构建镜像不完整，且当前为无源码 runtime（PANEL 安装包），无法本地 docker build"
                runtime_img_msg error "请检查仓库连通性，或确认远程已发布缺失镜像（如 aiot-transform）后重试 pull/install"
                runtime_print_install_local_build_help pull
                export EASYAIOT_SKIP_IMAGE_PROMPT=1
                return 1
            fi
            runtime_img_msg warn "预构建镜像拉取失败，install 将自动在各模块执行本地构建"
            runtime_print_install_local_build_help install
            do_local_build=1
        fi
    fi

    export EASYAIOT_SKIP_IMAGE_PROMPT=1
    # 本地构建是正常路径，始终 return 0（避免 install 脚本 set -e 误退出）
    return 0
}

# 统一镜像更新（update 流程共用）
# 交互询问拉取最新预构建镜像或本地重建；成功拉取后设置 EASYAIOT_SKIP_BUILD
runtime_images_acquire_for_update() {
    local do_local_build=0
    local source_free=0
    if runtime_is_source_free_runtime; then
        source_free=1
    fi

    if [ "${EASYAIOT_RUNTIME_FORCE_PULL:-0}" = "1" ]; then
        do_local_build=0
    elif [ "$source_free" -eq 1 ]; then
        runtime_img_msg info "无源码 runtime（PANEL）：自动拉取最新预构建镜像（不支持本地重建）"
        do_local_build=0
    elif [ "${EASYAIOT_SKIP_IMAGE_PROMPT:-0}" = "1" ]; then
        if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]; then
            return 0
        fi
        do_local_build=1
    elif [ -t 0 ]; then
        runtime_img_msg info "========================================"
        runtime_img_msg info "  镜像更新方式"
        runtime_img_msg info "========================================"
        runtime_img_msg info "  1) 拉取最新预构建镜像：从远程仓库下载（快速，默认）"
        runtime_img_msg info "  2) 本地重建：编译并制作 Docker 镜像（耗时较长）"
        echo ""
        read -r -p "是否从远程仓库拉取最新预构建镜像？(Y/n) " _pull_response
        case "${_pull_response:-Y}" in
            n|N|no|NO)
                do_local_build=1
                runtime_img_msg info "已选择本地重建，update 将在各模块执行 docker build（耗时较长）"
                ;;
            *) do_local_build=0 ;;
        esac
    else
        runtime_img_msg info "非交互模式，默认拉取最新预构建镜像"
    fi

    if [ "$do_local_build" -eq 1 ] && [ "$source_free" -eq 1 ]; then
        runtime_img_msg warn "无源码 runtime 不支持本地重建，改为拉取预构建镜像"
        do_local_build=0
    fi

    if [ "$do_local_build" -eq 0 ]; then
        runtime_img_msg info "正在拉取最新预构建镜像..."
        export EASYAIOT_RUNTIME_FORCE_PULL=1
        runtime_images_prepare_pull_interactive
        runtime_images_export_for_invoke
        if runtime_images_invoke pull; then
            runtime_img_msg ok "预构建镜像更新成功"
            export EASYAIOT_SKIP_BUILD=1
        elif runtime_images_pulled_ready; then
            runtime_img_msg warn "部分远程镜像拉取失败，但本地核心预构建镜像已就绪，将跳过重建并继续更新"
            export EASYAIOT_SKIP_BUILD=1
            do_local_build=0
            unset EASYAIOT_RUNTIME_FORCE_PULL
        else
            if runtime_is_source_free_runtime; then
                runtime_img_msg error "预构建镜像不完整，且当前为无源码 runtime（PANEL 安装包），无法本地重建"
                runtime_print_install_local_build_help pull
                unset EASYAIOT_RUNTIME_FORCE_PULL
                export EASYAIOT_SKIP_IMAGE_PROMPT=1
                return 1
            fi
            runtime_img_msg warn "预构建镜像拉取失败，update 将自动在各模块执行本地重建"
            runtime_print_install_local_build_help update
            do_local_build=1
            unset EASYAIOT_RUNTIME_FORCE_PULL
        fi
    fi

    export EASYAIOT_SKIP_IMAGE_PROMPT=1
    unset EASYAIOT_RUNTIME_FORCE_PULL
    return 0
}

# install 流程：拉取标记或本次拉取成功则跳过构建
runtime_images_should_skip_build() {
    if [ "${EASYAIOT_SKIP_BUILD:-0}" = "1" ]; then
        return 0
    fi
    if runtime_images_pulled_ready; then
        export EASYAIOT_SKIP_BUILD=1
        return 0
    fi
    return 1
}

# ============================================================================
# 跨架构构建：QEMU / binfmt 检测与安装
# x86 宿主机上 docker build --platform linux/arm64 执行 RUN 步骤需要 QEMU 用户态模拟
# ============================================================================
runtime_binfmt_handler_for_platform() {
    case "$1" in
        linux/arm64|linux/arm64/v8) echo "qemu-aarch64" ;;
        linux/arm/v7|linux/arm/v6)  echo "qemu-arm" ;;
        *)                          echo "" ;;
    esac
}

runtime_binfmt_supports_platform() {
    local handler
    handler=$(runtime_binfmt_handler_for_platform "$1")
    [ -z "$handler" ] && return 0
    [ -f "/proc/sys/fs/binfmt_misc/${handler}" ]
}

# 确保宿主机可执行目标平台的容器内指令（交叉构建前置条件）
runtime_ensure_qemu_binfmt() {
    local platform="${1:-linux/arm64}"
    local handler
    handler=$(runtime_binfmt_handler_for_platform "$platform")
    [ -z "$handler" ] && return 0

    if runtime_binfmt_supports_platform "$platform"; then
        return 0
    fi

    runtime_img_msg info "未检测到 ${platform} 的 QEMU/binfmt 支持，正在安装（首次约需 1 分钟）..."
    if ! command -v docker >/dev/null 2>&1; then
        runtime_img_msg error "Docker 未安装，无法配置 QEMU/binfmt"
        return 1
    fi
    if ! docker run --rm --privileged tonistiigi/binfmt --install all; then
        runtime_img_msg error "QEMU/binfmt 安装失败，无法在 x86 宿主机上交叉构建 ${platform} 镜像"
        runtime_img_msg info "可选方案: 在 ARM 机器上构建 arm64 镜像，或手动执行:"
        runtime_img_msg info "  docker run --rm --privileged tonistiigi/binfmt --install all"
        return 1
    fi
    if ! runtime_binfmt_supports_platform "$platform"; then
        runtime_img_msg error "QEMU/binfmt 安装后仍无法执行 ${platform} 容器（缺少 ${handler}）"
        return 1
    fi
    runtime_img_msg ok "QEMU/binfmt 已就绪，可交叉构建 ${platform}"
    return 0
}

# 委托 runtime_image.sh（参数原样透传，如 --profile mini --tag v1.0）
runtime_images_invoke() {
    if [ ! -f "$RUNTIME_IMAGE_SCRIPT" ]; then
        runtime_img_msg error "运行时镜像脚本不存在: ${RUNTIME_IMAGE_SCRIPT}"
        return 1
    fi
    bash "$RUNTIME_IMAGE_SCRIPT" "$@"
}

# 显示运行时镜像管理用法摘要
runtime_images_usage() {
    cat <<EOF
运行时镜像管理（业务模块 DEVICE/AI/VIDEO/WEB/APP/VISUALIZE/TRANSFORM/PANEL，不含中间件；APP/VISUALIZE/TRANSFORM 仅 full；PANEL 全形态）

pull 按部署形态过滤 DEVICE 镜像（与 compose 启停一致）：
  mini     — 仅拉 aiot-system（1/12）
  standard — 跳过 aiot-device、aiot-tdengine、aiot-visualize（9/12）
  full     — 拉全部 DEVICE（12/12，含 aiot-visualize）
  build-runtime 默认构建/推送全部模块；可指定单模块 DEVICE|AI|VIDEO|WEB|APP|VISUALIZE|TRANSFORM|PANEL
  全量 build-runtime 仍构建/推送全量 DEVICE，供各形态共用远程仓库

本地安装（含本地构建）:
  bash .scripts/docker/install_linux.sh install       # 交互可选拉取或本地构建
  bash .scripts/docker/install_linux.sh build         # 仅本地构建镜像
  bash .scripts/docker/install_linux_arm.sh install   # ARM 架构
  bash .scripts/docker/install_business_linux.sh install  # 仅业务模块

桌面端（仅镜像部署，禁止本地构建）:
  bash .scripts/docker/install_mac.sh install
  bash .scripts/docker/install_windows.sh install
  # Windows PowerShell: .scripts/docker/install_windows.ps1 install

远程镜像拉取/推送（交互式，默认部署形态 full）:
  bash .scripts/docker/install_linux.sh pull
  bash .scripts/docker/install_linux.sh build-runtime
  bash .scripts/docker/install_linux.sh build-runtime AI    # 仅构建/推送 AI 模块
  bash .scripts/docker/install_business_linux.sh pull
  bash .scripts/docker/install_business_linux.sh build-runtime

远程仓库配置:
  编辑 .scripts/docker/runtime_registry.conf 中的 REGISTRY=
  或 export EASYAIOT_RUNTIME_REGISTRY=your.cool/namespace/project/

非交互（CI）可用环境变量:
  EASYAIOT_RUNTIME_REGISTRY  远程仓库地址
  EASYAIOT_DEPLOY_PROFILE    部署形态 mini|standard|full
  EASYAIOT_RUNTIME_TAG         镜像标签（默认 latest）
  EASYAIOT_RUNTIME_PUSH=1      构建后推送（仅 build-runtime）
  EASYAIOT_RUNTIME_BUILD_ALL_PROFILES=1  构建全部形态（仅 build-runtime）
  EASYAIOT_RUNTIME_BUILD_ARCH=all|amd64|arm64  目标架构（默认 all=全部；单架构时跳过 manifest）
  EASYAIOT_RUNTIME_BUILD_MODULE=all|DEVICE|AI|VIDEO|WEB|APP|VISUALIZE|TRANSFORM|PANEL  目标模块（默认 all=全部）
  EASYAIOT_RUNTIME_FORCE_REBUILD=1       强制重建全部镜像（忽略本地缓存）
  EASYAIOT_RUNTIME_FORCE_REBUILD=0       复用本地镜像（已存在则跳过构建，直接推送）
  EASYAIOT_SKIP_REGISTRY_AUTH_CHECK=1     跳过 build-runtime 前的远程仓库登录/推送权限检查
  EASYAIOT_DOCKER_PUSH_RETRIES=8          推送失败时的最大重试次数（默认 8，大镜像/网络抖动时自动退避重试）
  EASYAIOT_DOCKER_PUSH_RETRY_DELAY=10     推送重试初始间隔秒数（默认 10，指数退避，上限 120s）

build-runtime 会在构建开始前校验远程仓库登录与推送权限；未登录请先 docker login。

也可直接调用 runtime_image.sh（支持命令行参数，适合 CI）:
  bash .scripts/docker/runtime_image.sh pull
  bash .scripts/docker/runtime_image.sh build --push
  bash .scripts/docker/runtime_image.sh build --push --module VIDEO
EOF
}

# 初始化默认仓库地址
runtime_load_registry
