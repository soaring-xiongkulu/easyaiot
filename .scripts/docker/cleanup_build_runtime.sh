#!/bin/bash
# ============================================
# EasyAIoT build-runtime 构建产物清理工具
# ============================================
# 清理 build-runtime / runtime_image.sh 构建过程中产生的：
#   - 本地运行时镜像（ai-service / rtc-service / post-service / video-service / web-service / app-service / visualize-service / iot-* 等）
#   - 远程仓库标签镜像（<registry>/aiot-*:amd64|arm64|latest 等）
#   - Docker 悬空镜像与 BuildKit 构建缓存
#   - 项目 .build-cache 与 WEB/dist-prebuilt-* 中间产物（可选）
#   - runtime_image 构建日志（可选）
#
# 注意: 跨架构基础镜像（pytorch/manylinuxaarch64-builder 等，约 10GB+）故意保留，
#       避免每次 ARM 跨架构 build-runtime 都重新下载。
#
# 用法:
#   bash .scripts/docker/cleanup_build_runtime.sh           # 交互菜单
#   bash .scripts/docker/cleanup_build_runtime.sh --yes     # 一键清理（镜像+构建缓存，保留 .build-cache）
#   bash .scripts/docker/cleanup_build_runtime.sh --all -y  # 全部清理（含 .build-cache）
#   bash .scripts/docker/cleanup_build_runtime.sh --dry-run # 仅预览
#   bash .scripts/docker/cleanup_build_runtime.sh --module AI -y
#     # 仅清理指定模块（如 AI）：该模块镜像 + .build-cache/ai（含 arm 交叉缓存）
#     # 可选模块同 build-runtime: HARNESS|IDEA|DEVICE|AI|RTC|POST|VIDEO|WEB|APP|VISUALIZE|TRANSFORM|PANEL
#     # 指定模块时默认清理 镜像+该模块构建缓存；全局 BuildKit 缓存无法按模块过滤，自动跳过
#
# 注意: 若当前环境正在使用这些镜像运行服务，请先 stop 再清理。
# ============================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"
# shellcheck source=runtime_image_common.sh
source "${SCRIPT_DIR}/runtime_image_common.sh"
# shellcheck source=init-build-cache-dirs.sh
source "${SCRIPT_DIR}/init-build-cache-dirs.sh"

TAG="${EASYAIOT_RUNTIME_TAG:-latest}"
REGISTRY=""
BUILD_CACHE_DIR="$(easyaiot_build_cache_base "$PROJECT_ROOT")"
LOG_DIR="${SCRIPT_DIR}/logs"
RUNTIME_MARKER="${RUNTIME_IMAGES_MARKER}"

DO_IMAGES=false
DO_BUILDER=false
DO_CACHE=false
DO_DIST=false
DO_LOGS=false
DO_MARKER=false
DRY_RUN=false
ASSUME_YES=false
SHOW_HELP=false
# 指定模块时仅清理该模块（空=全部）；模块名同 build-runtime（HARNESS|IDEA|DEVICE|AI|RTC|POST|VIDEO|WEB|APP|VISUALIZE|TRANSFORM|PANEL）
CLEAN_MODULE=""

# 跨架构构建常拉取的大体积基础镜像（清理时故意保留，避免每次 ARM 重建都重新下载）
PRESERVE_CROSS_BUILD_BASE_IMAGES=(
    "pytorch/manylinuxaarch64-builder:cuda12.9"
    "pytorch/pytorch:2.9.0-cuda12.8-cudnn9-devel"
    "pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime"
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

show_help() {
    cat <<'EOF'
用法: cleanup_build_runtime.sh [选项]

默认（无选项）进入交互菜单。

选项:
  --images         清理 build-runtime 相关 Docker 镜像（本地 + 远程标签；保留跨架构基础镜像）
  --builder        清理 Docker BuildKit 构建缓存 (docker builder prune -af)
  --cache          清理项目 .build-cache（pip/maven/pnpm 离线缓存，下次构建会重新下载）
  --dist           清理 WEB/dist-prebuilt-* 跨架构中间产物
  --logs           清理 .scripts/docker/logs 下 runtime_image / build_ 日志
  --marker         删除 .runtime_images_pulled 拉取标记
  --module <模块>  仅清理指定模块（HARNESS|IDEA|DEVICE|AI|RTC|POST|VIDEO|WEB|APP|VISUALIZE|TRANSFORM|PANEL）
                   与 --images/--cache 联用时只清理该模块镜像与 .build-cache/<模块> 子目录；
                   与 --all 联用同理（BuildKit 缓存为全局共享，指定模块时自动跳过）；
                   --dist 仅在模块为 WEB 时生效
  --all            执行以上全部清理
  --yes, -y        跳过确认
  --dry-run, -n    仅预览，不实际删除
  -h, --help       显示帮助

示例:
  bash .scripts/docker/cleanup_build_runtime.sh --yes
  bash .scripts/docker/cleanup_build_runtime.sh --images --builder -y
  bash .scripts/docker/cleanup_build_runtime.sh --all --dry-run
  bash .scripts/docker/cleanup_build_runtime.sh --module AI -y
  bash .scripts/docker/cleanup_build_runtime.sh --module VIDEO --images --cache -n
EOF
}

human_du() {
    local path="$1"
    if [ ! -e "$path" ]; then
        echo "0"
        return 0
    fi
    du -sh "$path" 2>/dev/null | awk '{print $1}'
}

parse_args() {
    local any_target=false
    while [ $# -gt 0 ]; do
        case "$1" in
            --images)  DO_IMAGES=true;  any_target=true ;;
            --builder) DO_BUILDER=true; any_target=true ;;
            --cache)   DO_CACHE=true;   any_target=true ;;
            --dist)    DO_DIST=true;    any_target=true ;;
            --logs)    DO_LOGS=true;    any_target=true ;;
            --marker)  DO_MARKER=true;  any_target=true ;;
            --all)
                DO_IMAGES=true
                DO_BUILDER=true
                DO_CACHE=true
                DO_DIST=true
                DO_LOGS=true
                DO_MARKER=true
                any_target=true
                ;;
            --yes|-y)  ASSUME_YES=true ;;
            --dry-run|-n) DRY_RUN=true ;;
            -h|--help) SHOW_HELP=true ;;
            --module|-m)
                if [ $# -lt 2 ]; then
                    print_err "参数 $1 缺少模块名"
                    exit 2
                fi
                CLEAN_MODULE=$(runtime_normalize_build_module "$2")
                if [ "$CLEAN_MODULE" = "INVALID" ]; then
                    print_err "无效的运行时模块: $2，可选: $(runtime_build_module_help)"
                    exit 2
                fi
                shift 2
                continue
                ;;
            *)
                print_err "未知参数: $1"
                show_help
                exit 2
                ;;
        esac
        shift
    done
    if ! $any_target && ! $ASSUME_YES && ! $DRY_RUN; then
        INTERACTIVE=true
    else
        INTERACTIVE=false
    fi
}

confirm() {
    local prompt="$1"
    if $ASSUME_YES; then
        return 0
    fi
    while true; do
        echo -ne "${YELLOW}[提示]${NC} ${prompt} (y/N): "
        read -r response
        case "${response:-N}" in
            y|Y|yes|YES) return 0 ;;
            n|N|no|NO|"") return 1 ;;
            *) print_warn "请输入 y 或 N" ;;
        esac
    done
}

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        print_warn "Docker 未安装，跳过镜像相关清理"
        return 1
    fi
    if ! docker info >/dev/null 2>&1; then
        print_warn "无法连接 Docker daemon，跳过镜像相关清理"
        return 1
    fi
    return 0
}

# build-runtime 模块 → .build-cache 子目录名（无独立构建缓存的模块返回空）
build_cache_subdir_for() {
    case "${1:-}" in
        AI)        echo "ai" ;;
        VIDEO)     echo "video" ;;
        DEVICE)    echo "device" ;;
        WEB)       echo "web" ;;
        APP)       echo "app" ;;
        VISUALIZE) echo "visualize" ;;
        *)         echo "" ;;
    esac
}

# build-runtime 模块 → docker ps 容器名匹配模式（用于"模块运行中"告警；无映射返回空）
runtime_container_pattern_for() {
    case "${1:-}" in
        DEVICE)   echo "^(iot-)" ;;
        HARNESS)  echo "^(easyaiot-harness|harness)" ;;
        IDEA)     echo "^(easyaiot-idea-portal|easyaiot-idea-workspace|idea-portal|idea-workspace)" ;;
        PANEL)    echo "^(easyaiot-panel|panel)" ;;
        AI|RTC|POST|VIDEO|WEB|APP|VISUALIZE|TRANSFORM)
            echo "^(${1,,}-service)" ;;
        *)        echo "" ;;
    esac
}

# 收集指定模块（CLEAN_MODULE）的 .build-cache 目标目录；ai/video 另含 arm 交叉缓存
collect_module_cache_targets() {
    local -n _out="$1"
    local sub
    sub=$(build_cache_subdir_for "$CLEAN_MODULE")
    [ -n "$sub" ] || return 0
    _out+=("${BUILD_CACHE_DIR}/${sub}")
    case "$sub" in
        ai|video) _out+=("${BUILD_CACHE_DIR}/arm/${sub}") ;;
    esac
}

# 收集 build-runtime 相关的本地/远程镜像引用
# 用法: collect_runtime_image_refs <数组名> [模块]（不传或空=全部模块）
collect_runtime_image_refs() {
    local -n _out="$1"
    local module_filter="${2:-}"
    local profile arch rname tmp lname pname

    runtime_load_registry
    REGISTRY=$(runtime_normalize_registry "${EASYAIOT_RUNTIME_REGISTRY:-$RUNTIME_IMAGE_REGISTRY}")

    for mapping in "${INDEPENDENT_MODULES[@]}"; do
        rname="${mapping%%|*}"
        tmp="${mapping#*|}"
        lname="${tmp%%|*}"
        pname="${tmp#*|}"
        [ -n "$module_filter" ] && [ "$pname" != "$module_filter" ] && continue
        if runtime_is_profile_dependent "$rname"; then
            for profile in "${ALL_DEPLOY_PROFILES[@]}"; do
                _out+=("$(runtime_local_ref "$lname" "$profile")")
                for arch in "${ALL_RUNTIME_ARCHS[@]}"; do
                    _out+=("$(runtime_remote_ref "$rname" "$profile" "$arch")")
                done
                _out+=("$(runtime_manifest_ref "$rname" "$profile")")
            done
        else
            _out+=("$(runtime_local_ref "$lname")")
            for arch in "${ALL_RUNTIME_ARCHS[@]}"; do
                _out+=("$(runtime_remote_ref "$rname" "" "$arch")")
            done
            _out+=("$(runtime_manifest_ref "$rname")")
        fi
    done

    if [ -z "$module_filter" ] || [ "$module_filter" = "DEVICE" ]; then
        for lname in "${DEVICE_LOCAL_NAMES[@]}"; do
            _out+=("$(runtime_local_ref "$lname")")
        done
        for rname in "${DEVICE_REMOTE_NAMES[@]}"; do
            for arch in "${ALL_RUNTIME_ARCHS[@]}"; do
                _out+=("$(runtime_remote_ref "$rname" "" "$arch")")
            done
            _out+=("$(runtime_manifest_ref "$rname")")
        done
    fi

    for mapping in "${FULL_ONLY_MODULES[@]}"; do
        tmp="${mapping#*|}"
        lname="${tmp%%|*}"
        rname="${mapping%%|*}"
        pname="${tmp#*|}"
        [ -n "$module_filter" ] && [ "$pname" != "$module_filter" ] && continue
        _out+=("$(runtime_local_ref "$lname")")
        for arch in "${ALL_RUNTIME_ARCHS[@]}"; do
            _out+=("$(runtime_remote_ref "$rname" "" "$arch")")
        done
        _out+=("$(runtime_manifest_ref "$rname")")
    done

    # 不加入 PRESERVE_CROSS_BUILD_BASE_IMAGES：ARM 基础镜像体积大，保留供下次复用
}

append_unique_ref() {
    local ref="$1"
    local -n _arr="$2"
    local existing
    [ -z "$ref" ] && return 0
    for existing in "${_arr[@]}"; do
        [ "$existing" = "$ref" ] && return 0
    done
    _arr+=("$ref")
}

# 补充 grep 到的同仓库前缀镜像（防止命名规则变更后遗漏）
collect_extra_registry_images() {
    local -n _out="$1"
    local line repo_tag
    [ -n "$REGISTRY" ] || return 0
    local registry_prefix="${REGISTRY%/}"
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        repo_tag="${line%% *}"
        case "$repo_tag" in
            "${registry_prefix}"/*) append_unique_ref "$repo_tag" _out ;;
        esac
    done < <(docker images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null || true)
}

image_size_of() {
    docker image inspect "$1" --format '{{.Size}}' 2>/dev/null || echo "0"
}

format_bytes() {
    local bytes="$1"
    if command -v numfmt >/dev/null 2>&1; then
        numfmt --to=iec-i --suffix=B "$bytes" 2>/dev/null || echo "${bytes}B"
    else
        echo "${bytes}B"
    fi
}

show_cleanup_preview() {
    print_section "清理预览"

    if $DO_IMAGES && check_docker; then
        local -a refs=()
        collect_runtime_image_refs refs "$CLEAN_MODULE"
        if [ -z "$CLEAN_MODULE" ]; then
            collect_extra_registry_images refs
        fi

        local ref size_bytes total_bytes=0 found=0
        if [ -n "$CLEAN_MODULE" ]; then
            print_info "build-runtime 相关镜像（仅模块 ${CLEAN_MODULE}）:"
        else
            print_info "build-runtime 相关镜像:"
        fi
        for ref in "${refs[@]}"; do
            if docker image inspect "$ref" >/dev/null 2>&1; then
                size_bytes=$(image_size_of "$ref")
                total_bytes=$((total_bytes + size_bytes))
                found=$((found + 1))
                printf "  %-70s %s\n" "$ref" "$(format_bytes "$size_bytes")"
            fi
        done
        if [ "$found" -eq 0 ]; then
            print_info "  （无匹配镜像）"
        else
            print_info "  合计约 $(format_bytes "$total_bytes")（${found} 个镜像，层共享时实际释放可能更少）"
        fi

        local dangling
        dangling=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l | tr -d ' ')
        print_info "悬空镜像 (<none>): ${dangling} 个"

        # 提示将保留的跨架构基础镜像（不删除）
        local preserved=0 pref psize
        for pref in "${PRESERVE_CROSS_BUILD_BASE_IMAGES[@]}"; do
            if docker image inspect "$pref" >/dev/null 2>&1; then
                if [ "$preserved" -eq 0 ]; then
                    print_info "保留跨架构基础镜像（不删除，供 ARM 构建复用）:"
                fi
                psize=$(image_size_of "$pref")
                printf "  %-70s %s\n" "$pref" "$(format_bytes "$psize")"
                preserved=$((preserved + 1))
            fi
        done
        if [ "$preserved" -eq 0 ]; then
            print_info "跨架构基础镜像: （本地暂无，下次 build-runtime 会拉取并保留）"
        fi
    fi

    if $DO_BUILDER && check_docker; then
        if [ -n "$CLEAN_MODULE" ]; then
            print_info "BuildKit 构建缓存为全局共享，无法按模块过滤（本次跳过；如需清理请不带 --module 执行）"
        else
            print_info "Docker 构建缓存:"
            docker builder du 2>/dev/null || docker system df 2>/dev/null | grep -i build || print_info "  （无法统计）"
        fi
    fi

    if $DO_CACHE; then
        if [ -n "$CLEAN_MODULE" ]; then
            local -a cache_targets=()
            collect_module_cache_targets cache_targets
            if [ ${#cache_targets[@]} -eq 0 ]; then
                print_info "${CLEAN_MODULE} 无独立构建缓存目录（仅 AI/VIDEO/DEVICE/WEB/APP/VISUALIZE 有），跳过"
            else
                local ct
                for ct in "${cache_targets[@]}"; do
                    print_info ".build-cache 模块目录: $(human_du "$ct")  →  $ct"
                done
            fi
        else
            print_info ".build-cache: $(human_du "$BUILD_CACHE_DIR")  →  $BUILD_CACHE_DIR"
        fi
    fi

    if $DO_DIST; then
        local d
        for d in "${PROJECT_ROOT}"/WEB/dist-prebuilt-*; do
            [ -e "$d" ] || continue
            print_info "WEB 中间产物: $(human_du "$d")  →  $d"
        done
    fi

    if $DO_LOGS; then
        local log_count log_size
        log_count=$(find "$LOG_DIR" -maxdepth 1 \( -name 'runtime_image_*.log' -o -name 'build_*.log' \) 2>/dev/null | wc -l | tr -d ' ')
        log_size=$(human_du "$LOG_DIR")
        print_info "构建日志: ${log_count} 个文件，目录合计 ${log_size}"
    fi

    if $DO_MARKER && [ -f "$RUNTIME_MARKER" ]; then
        print_info "拉取标记: $RUNTIME_MARKER"
    fi
}

remove_image_ref() {
    local ref="$1"
    if ! docker image inspect "$ref" >/dev/null 2>&1; then
        return 0
    fi
    if $DRY_RUN; then
        print_info "[dry-run] docker rmi $ref"
        return 0
    fi
    if docker rmi "$ref" >/dev/null 2>&1; then
        print_ok "已删除镜像: $ref"
        return 0
    fi
    # 可能被其他标签引用，尝试强制删除
    if docker rmi -f "$ref" >/dev/null 2>&1; then
        print_ok "已强制删除镜像: $ref"
        return 0
    fi
    print_warn "无法删除镜像（可能正被容器使用）: $ref"
    return 1
}

cleanup_images() {
    if ! check_docker; then
        return 0
    fi

    if [ -n "$CLEAN_MODULE" ]; then
        print_section "清理 build-runtime 相关镜像（仅模块 ${CLEAN_MODULE}）"
    else
        print_section "清理 build-runtime 相关镜像"
    fi

    local -a refs=()
    collect_runtime_image_refs refs "$CLEAN_MODULE"
    if [ -z "$CLEAN_MODULE" ]; then
        collect_extra_registry_images refs
    fi

    local ref removed=0 skipped=0
    for ref in "${refs[@]}"; do
        if docker image inspect "$ref" >/dev/null 2>&1; then
            if remove_image_ref "$ref"; then
                removed=$((removed + 1))
            else
                skipped=$((skipped + 1))
            fi
        fi
    done

    local dangling
    dangling=$(docker images -f "dangling=true" -q 2>/dev/null || true)
    if [ -n "$dangling" ]; then
        if $DRY_RUN; then
            print_info "[dry-run] docker image prune -f"
        elif docker image prune -f >/dev/null 2>&1; then
            print_ok "已清理悬空镜像"
        else
            print_warn "悬空镜像清理失败"
        fi
    fi

    print_info "镜像清理完成: 删除 ${removed} 个，跳过 ${skipped} 个"
}

cleanup_builder_cache() {
    if ! check_docker; then
        return 0
    fi
    if [ -n "$CLEAN_MODULE" ]; then
        print_warn "BuildKit 构建缓存为全局共享，无法按模块过滤，已跳过"
        print_warn "如需清理全局构建缓存，请不带 --module 重新执行: bash ${0##*/} --builder"
        return 0
    fi
    print_section "清理 Docker 构建缓存"
    if $DRY_RUN; then
        print_info "[dry-run] docker builder prune -af"
        return 0
    fi
    if docker builder prune -af; then
        print_ok "构建缓存已清理"
    else
        print_warn "构建缓存清理失败"
    fi
}

cleanup_build_cache_dir() {
    print_section "清理 .build-cache"
    if [ -n "$CLEAN_MODULE" ]; then
        local -a targets=()
        collect_module_cache_targets targets
        if [ ${#targets[@]} -eq 0 ]; then
            print_info "${CLEAN_MODULE} 无独立构建缓存目录（仅 AI/VIDEO/DEVICE/WEB/APP/VISUALIZE 有），跳过"
            return 0
        fi
        local t size
        for t in "${targets[@]}"; do
            if [ ! -d "$t" ]; then
                print_info "目录不存在，跳过: $t"
                continue
            fi
            size=$(human_du "$t")
            if $DRY_RUN; then
                print_info "[dry-run] rm -rf ${t}/*"
            else
                rm -rf "${t:?}"/*
                print_ok "已清理 ${t}（释放约 ${size}）"
            fi
        done
        return 0
    fi
    if [ ! -d "$BUILD_CACHE_DIR" ]; then
        print_info "目录不存在，跳过: $BUILD_CACHE_DIR"
        return 0
    fi
    local size; size=$(human_du "$BUILD_CACHE_DIR")
    if $DRY_RUN; then
        print_info "[dry-run] rm -rf $BUILD_CACHE_DIR/*"
        return 0
    fi
    rm -rf "${BUILD_CACHE_DIR:?}"/*
    print_ok "已清理 .build-cache（释放约 ${size}）"
}

cleanup_dist_prebuilt() {
    if [ -n "$CLEAN_MODULE" ] && [ "$CLEAN_MODULE" != "WEB" ]; then
        print_info "跳过 WEB/dist-prebuilt-*（当前仅清理 ${CLEAN_MODULE} 模块）"
        return 0
    fi
    print_section "清理 WEB/dist-prebuilt-*"
    local found=false d size
    for d in "${PROJECT_ROOT}"/WEB/dist-prebuilt-*; do
        [ -e "$d" ] || continue
        found=true
        size=$(human_du "$d")
        if $DRY_RUN; then
            print_info "[dry-run] rm -rf $d"
        else
            rm -rf "$d"
            print_ok "已删除 ${d}（约 ${size}）"
        fi
    done
    if ! $found; then
        print_info "无 dist-prebuilt 目录"
    fi
}

cleanup_logs() {
    print_section "清理构建日志"
    local count=0 f
    while IFS= read -r f; do
        [ -z "$f" ] && continue
        count=$((count + 1))
        if $DRY_RUN; then
            print_info "[dry-run] rm -f $f"
        else
            rm -f "$f"
        fi
    done < <(find "$LOG_DIR" -maxdepth 1 \( -name 'runtime_image_*.log' -o -name 'build_*.log' \) 2>/dev/null || true)
    if [ "$count" -eq 0 ]; then
        print_info "无匹配日志"
    elif ! $DRY_RUN; then
        print_ok "已删除 ${count} 个日志文件"
    fi
}

cleanup_marker() {
    if [ ! -f "$RUNTIME_MARKER" ]; then
        return 0
    fi
    print_section "删除拉取标记"
    if $DRY_RUN; then
        print_info "[dry-run] rm -f $RUNTIME_MARKER"
        return 0
    fi
    rm -f "$RUNTIME_MARKER"
    print_ok "已删除 $RUNTIME_MARKER"
}

warn_running_services() {
    if ! check_docker; then
        return 0
    fi
    local pat running
    if [ -n "$CLEAN_MODULE" ]; then
        pat=$(runtime_container_pattern_for "$CLEAN_MODULE")
        [ -n "$pat" ] || return 0
        running=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "$pat" || true)
        if [ -z "$running" ]; then
            return 0
        fi
        print_warn "检测到以下容器可能正在使用 ${CLEAN_MODULE} 模块镜像:"
    else
        pat='^(ai-service|rtc-service|post-service|video-service|web-service|app-service|visualize-service|iot-)'
        running=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -E "$pat" || true)
        if [ -z "$running" ]; then
            return 0
        fi
        print_warn "检测到以下容器可能正在使用运行时镜像:"
    fi
    echo "$running" | sed 's/^/  /'
    print_warn "建议先执行: bash .scripts/docker/install_linux.sh clean-build-runtime${CLEAN_MODULE:+ ${CLEAN_MODULE}}"
    print_warn "（仅停业务服务并清理镜像；或手动 stop 对应业务模块，勿停中间件）"
}

run_selected_cleanup() {
    if [ -n "$CLEAN_MODULE" ]; then
        print_info "清理范围: 仅模块 ${CLEAN_MODULE}（镜像 + 该模块 .build-cache；全局 BuildKit 缓存与其余模块镜像不受影响）"
        echo ""
    fi
    warn_running_services
    show_cleanup_preview

    if ! $ASSUME_YES && ! $DRY_RUN; then
        echo ""
        if ! confirm "确认执行以上清理"; then
            print_info "已取消"
            return 0
        fi
    fi

    $DO_IMAGES  && cleanup_images
    $DO_BUILDER && cleanup_builder_cache
    $DO_CACHE   && cleanup_build_cache_dir
    $DO_DIST    && cleanup_dist_prebuilt
    $DO_LOGS    && cleanup_logs
    $DO_MARKER  && cleanup_marker

    print_section "清理后磁盘概况"
    print_info ".build-cache: $(human_du "$BUILD_CACHE_DIR")"
    if check_docker; then
        print_info "Docker 磁盘使用:"
        docker system df 2>/dev/null || true
    fi
}

interactive_menu() {
    print_section "build-runtime 构建产物清理"
    print_info "项目路径: ${PROJECT_ROOT}"
    print_info "远程仓库: $(runtime_normalize_registry "${EASYAIOT_RUNTIME_REGISTRY:-$(sed -n 's/^[[:space:]]*REGISTRY=//p' "${SCRIPT_DIR}/runtime_registry.conf" 2>/dev/null | head -1)}")"
    echo ""
    echo "请选择清理项（可多选，逗号分隔）:"
    echo "  1) 运行时镜像 + 悬空镜像（推荐；保留 pytorch/manylinux 等跨架构基础镜像）"
    echo "  2) Docker BuildKit 构建缓存"
    echo "  3) .build-cache 离线缓存（pip/maven/pnpm，下次构建会重新下载）"
    echo "  4) WEB/dist-prebuilt-* 跨架构中间产物"
    echo "  5) runtime_image / build_ 构建日志"
    echo "  6) .runtime_images_pulled 拉取标记"
    echo "  7) 全部清理（1-6）"
    echo "  8) 仅清理指定模块（该模块镜像 + .build-cache，全局 BuildKit 缓存不清理）"
    echo "  9) 退出"
    echo ""

    local choice
    echo -ne "${YELLOW}[提示]${NC} 请输入选项 [默认 1]: "
    read -r choice
    choice="${choice:-1}"

    case "$choice" in
        1) DO_IMAGES=true ;;
        2) DO_BUILDER=true ;;
        3) DO_CACHE=true ;;
        4) DO_DIST=true ;;
        5) DO_LOGS=true ;;
        6) DO_MARKER=true ;;
        7)
            DO_IMAGES=true
            DO_BUILDER=true
            DO_CACHE=true
            DO_DIST=true
            DO_LOGS=true
            DO_MARKER=true
            ;;
        8)
            runtime_interactive_pick_module
            CLEAN_MODULE="${RUNTIME_PICKED_MODULE}"
            if [ -n "$CLEAN_MODULE" ]; then
                DO_IMAGES=true
                DO_CACHE=true
                print_info "将仅清理模块: ${CLEAN_MODULE}"
            else
                interactive_menu
                return 0
            fi
            ;;
        9|q|Q)
            print_info "已退出"
            exit 0
            ;;
        *)
            # 支持 1,2,3 多选
            local item
            IFS=',' read -ra _items <<< "$choice"
            for item in "${_items[@]}"; do
                item="${item//[[:space:]]/}"
                case "$item" in
                    1) DO_IMAGES=true ;;
                    2) DO_BUILDER=true ;;
                    3) DO_CACHE=true ;;
                    4) DO_DIST=true ;;
                    5) DO_LOGS=true ;;
                    6) DO_MARKER=true ;;
                    7)
                        DO_IMAGES=true
                        DO_BUILDER=true
                        DO_CACHE=true
                        DO_DIST=true
                        DO_LOGS=true
                        DO_MARKER=true
                        ;;
                    8)
                        runtime_interactive_pick_module
                        CLEAN_MODULE="${RUNTIME_PICKED_MODULE}"
                        if [ -n "$CLEAN_MODULE" ]; then
                            DO_IMAGES=true
                            DO_CACHE=true
                            print_info "将仅清理模块: ${CLEAN_MODULE}"
                        fi
                        ;;
                    *)
                        print_err "无效选项: $item"
                        exit 2
                        ;;
                esac
            done
            ;;
    esac

    run_selected_cleanup
}

main() {
    parse_args "$@"

    if $SHOW_HELP; then
        show_help
        exit 0
    fi

    # 指定模块后不再进交互菜单（意图已由命令行明确），直接按模块范围清理
    if [ "${INTERACTIVE:-false}" = true ] && [ -z "$CLEAN_MODULE" ]; then
        interactive_menu
    else
        # 仅传 -y / --dry-run 时默认清理镜像 + 构建缓存
        if ! $DO_IMAGES && ! $DO_BUILDER && ! $DO_CACHE && ! $DO_DIST && ! $DO_LOGS && ! $DO_MARKER; then
            if [ -n "$CLEAN_MODULE" ]; then
                # 模块级默认: 该模块镜像 + 该模块 .build-cache（全局 BuildKit 缓存不碰）
                DO_IMAGES=true
                DO_CACHE=true
            else
                DO_IMAGES=true
                DO_BUILDER=true
            fi
        fi
        run_selected_cleanup
    fi
}

main "$@"
