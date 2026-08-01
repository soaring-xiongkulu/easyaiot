#!/bin/bash
# ============================================================================
# EasyAIoT 运行时镜像构建/推送与拉取脚本
#
# 构建流程：
#   1. 先在宿主机原生架构执行 install_linux.sh build，完成所有本机编译
#      （Maven、Vite、pip install 等耗时操作），产出 JAR / dist 等编译产物。
#   2. 针对不同目标架构（amd64 arm64），循环执行 docker build --platform，
#      仅 COPY 本机编译产物 + 拉取目标架构的 base image 完成镜像包装。
#      ★ 跨架构构建若 Dockerfile 含 RUN 步骤，宿主机需 QEMU/binfmt（脚本会自动安装）。
#      纯 Java JAR、纯前端 dist 等仅 COPY 的层不依赖 QEMU；含 yum/apt/pnpm 等 RUN 的层需要。
#   3. 打标签并推送到远程仓库；推送成功后立即删除本地镜像，避免磁盘占用。
#      WEB 本机镜像在删除前会先提取 dist，供跨架构构建复用。
#
# 推荐入口（交互式，无需参数，默认 full）:
#   bash .scripts/docker/install_linux.sh pull|build-runtime
#   bash .scripts/docker/install_business_linux.sh pull|build-runtime
#
# 远程仓库配置见 runtime_registry.conf（或 EASYAIOT_RUNTIME_REGISTRY 环境变量）
#
# 直接调用本脚本（支持命令行参数，适合 CI）:
#   bash .scripts/docker/runtime_image.sh build [--push] [--tag <tag>] [--profile <profile>] [--registry <url>] [--arch <arch>] [--module <module>] [--native-source] [--force-rebuild]
#   bash .scripts/docker/runtime_image.sh pull [--tag <tag>] [--profile <profile>] [--registry <url>]
#
# 选项:
#   --push           构建后推送到远程仓库（仅 build）
#   --tag <tag>      指定镜像标签（默认 latest）
#   --registry <url> 指定推送/拉取仓库地址（默认见 runtime_registry.conf）
#   --force-rebuild  强制重新构建，忽略已存在的镜像（默认跳过已有镜像）
#   --profile <name> 指定部署形态：mini | standard | full
#                    - build: 不指定则构建全部 3 种形态；指定则只构建该形态
#                    - pull:  不指定则交互选择（默认 full）；指定则直接拉取该形态
#   --arch <arch>    指定构建架构：all | amd64 | arm64（默认 all=全部架构）
#                    单架构模式仅构建/推送该架构镜像，跳过多架构 manifest 更新
#   --module <mod>   指定构建模块：all | DEVICE | AI | VIDEO | WEB | APP | VISUALIZE | TRANSFORM | PANEL（默认 all=全部）
#                    单模块模式仅构建/推送该模块镜像，跳过全量 install_linux.sh build
#   --native-source  使用原始源（非国内镜像源），默认使用腾讯云镜像源加速
#
# 架构自动检测（uname -m）:
#   x86_64 / amd64  → amd64
#   aarch64 / arm64 → arm64
#
# 远程镜像命名规则（v3）:
#   形态放在镜像名称中，架构作为标签：
#     <registry>/<name>-<profile>:<arch>
#     <registry>/<name>:<arch>                              (full 形态省略 -full)
#     例: docker.cnb.cool/holmesian/easyaiot/aiot-ai:amd64
#         docker.cnb.cool/holmesian/easyaiot/aiot-web-mini:arm64
#         docker.cnb.cool/holmesian/easyaiot/aiot-web-standard:amd64
#         docker.cnb.cool/holmesian/easyaiot/aiot-web:arm64              (full)
#   多架构 manifest（使用版本标签，docker pull 自动匹配架构）:
#     <registry>/<name>-<profile>:<tag>
#     <registry>/<name>:<tag>                              (full 形态)
#     例: docker.cnb.cool/holmesian/easyaiot/aiot-ai:latest
#         docker.cnb.cool/holmesian/easyaiot/aiot-web-mini:v1.0.0
#
# 镜像映射（远程 → 本地）:
#   共享镜像（全形态通用，pull 时按形态跳过不会启动的 DEVICE 服务）:
#     docker.cnb.cool/holmesian/easyaiot/aiot-ai:amd64       → ai-service:latest
#     docker.cnb.cool/holmesian/easyaiot/aiot-video:amd64    → video-service:latest
#     docker.cnb.cool/holmesian/easyaiot/aiot-panel:amd64    → easyaiot/panel:latest
#     mini 仅拉 aiot-system；standard 跳过 aiot-device/aiot-tdengine/aiot-visualize；full 拉全部 DEVICE
#   形态相关镜像（WEB，全量形态均构建/推送）:
#     docker.cnb.cool/holmesian/easyaiot/aiot-web:amd64          → web-service:latest          (full)
#     docker.cnb.cool/holmesian/easyaiot/aiot-web-mini:amd64     → web-service:latest-mini     (mini)
#     docker.cnb.cool/holmesian/easyaiot/aiot-web-standard:amd64 → web-service:latest-standard (standard)
#   仅 full 形态（APP 移动端 H5 / VISUALIZE 可视化编辑器 / TRANSFORM 系统对接）:
#     docker.cnb.cool/holmesian/easyaiot/aiot-app:amd64              → app-service:latest
#     docker.cnb.cool/holmesian/easyaiot/aiot-visualize-web:amd64    → visualize-service:latest
#     docker.cnb.cool/holmesian/easyaiot/aiot-transform:amd64        → transform-service:latest
#
# 示例:
#   bash .scripts/docker/runtime_image.sh build --push
#   bash .scripts/docker/runtime_image.sh build --profile standard
#   bash .scripts/docker/runtime_image.sh build --push --profile mini --registry my-registry.com/easyaiot/
#   bash .scripts/docker/runtime_image.sh build --push --arch arm64
#   bash .scripts/docker/runtime_image.sh build --push --module AI
#   bash .scripts/docker/runtime_image.sh pull
#   bash .scripts/docker/runtime_image.sh pull --profile mini --registry my-registry.com/easyaiot/
#   bash .scripts/docker/runtime_image.sh pull --tag v1.2.0 --profile full
# ============================================================================

set -o pipefail

# ============================================================================
# 颜色定义
# ============================================================================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

# ============================================================================
# 路径初始化
# ============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "$PROJECT_ROOT"

# ============================================================================
# 日志配置
# ============================================================================
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/runtime_image_$(date +%Y%m%d_%H%M%S).log"
: > "$LOG_FILE"

_log() {
    local label="$1" msg="$2"
    echo -e "${label}${msg}${NC}"
    # msg 来自 print_* 调用，均为纯文本（颜色仅在 label 中），无需 sed 剥离 ANSI
    # 运行中若 logs 目录被删（如误删 .scripts），自动重建，避免整段 pull 中止
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${msg}" >> "$LOG_FILE" 2>/dev/null || true
}
print_info()    { _log "$BLUE" "[INFO] $1"; }
print_success() { _log "$GREEN" "[OK] $1"; }
print_warning() { _log "$YELLOW" "[WARN] $1"; }
print_error()   { _log "$RED" "[ERROR] $1"; }
print_step()    { _log "$CYAN" "[STEP] $1"; }
print_header()  {
    echo ""
    echo "============================================================"
    echo -e "${GREEN} $1${NC}"
    echo "============================================================"
    mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE" 2>/dev/null || true
}

# ============================================================================
# 默认值与参数解析
# ============================================================================
TAG="latest"
DO_PUSH=false
REGISTRY=""
COMMAND=""
NATIVE_SOURCE="${NATIVE_SOURCE:-false}"
FORCE_REBUILD=false
_BUILD_ARCH=""
_BUILD_MODULE=""

# 内部布尔开关；子进程通过 subshell 导出数值型 FORCE_REBUILD=0|1，避免污染本变量
is_force_rebuild() { [ "$FORCE_REBUILD" = true ]; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        build|pull)
            COMMAND="$1"; shift ;;
        --push)
            DO_PUSH=true; shift ;;
        --tag)
            TAG="$2"; shift 2 ;;
        --arch)
            _BUILD_ARCH="$2"; shift 2 ;;
        --module)
            _BUILD_MODULE="$2"; shift 2 ;;
        --native-source)
            NATIVE_SOURCE=true; shift ;;
        --force-rebuild)
            FORCE_REBUILD=true; shift ;;
        --profile)
            _EXPLICIT_PROFILE="$2"; shift 2 ;;
        --registry)
            REGISTRY="$2"
            [[ "$REGISTRY" != */ ]] && REGISTRY="${REGISTRY}/"
            shift 2 ;;
        --help|-h)
            awk '/^# =+$/{if(f)exit;f=1;next}f' "$SCRIPT_PATH" | grep '^#' | sed 's/^# \?//'
            exit 0 ;;
        *)
            print_error "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1 ;;
    esac
done

if [ -z "$COMMAND" ]; then
    print_error "请指定命令: build 或 pull"
    echo "使用 --help 查看帮助"
    exit 1
fi

# ============================================================================
# 部署形态配置
# ============================================================================
source "${SCRIPT_DIR}/deploy_profile.sh"
# shellcheck source=init-build-cache-dirs.sh
source "${SCRIPT_DIR}/init-build-cache-dirs.sh"
# shellcheck source=runtime_image_common.sh
source "${SCRIPT_DIR}/runtime_image_common.sh"
# shellcheck source=docker_mirror_common.sh
source "${SCRIPT_DIR}/docker_mirror_common.sh"

runtime_load_registry
REGISTRY=$(runtime_normalize_registry "${REGISTRY:-$RUNTIME_IMAGE_REGISTRY}")

# 子进程/CI 通过环境变量传入的配置（install_linux.sh pull 等交互入口会设置）
if [ -n "${EASYAIOT_RUNTIME_REGISTRY:-}" ]; then
    REGISTRY=$(runtime_normalize_registry "$EASYAIOT_RUNTIME_REGISTRY")
fi
if [ -n "${EASYAIOT_RUNTIME_TAG:-}" ]; then
    TAG="$EASYAIOT_RUNTIME_TAG"
fi
if [ "${EASYAIOT_RUNTIME_PUSH:-}" = "1" ] || [ "${EASYAIOT_RUNTIME_PUSH:-}" = "true" ]; then
    DO_PUSH=true
fi
if [ "${EASYAIOT_RUNTIME_FORCE_REBUILD:-}" = "1" ] || [ "${FORCE_REBUILD:-}" = "true" ]; then
    FORCE_REBUILD=true
fi
if [ -n "${EASYAIOT_RUNTIME_EXPLICIT_PROFILE:-}" ] && [ -z "${_EXPLICIT_PROFILE:-}" ]; then
    _EXPLICIT_PROFILE="$EASYAIOT_RUNTIME_EXPLICIT_PROFILE"
fi
if [ "${EASYAIOT_RUNTIME_BUILD_ALL_PROFILES:-0}" = "1" ]; then
    unset _EXPLICIT_PROFILE
fi
if [ -n "$_BUILD_ARCH" ]; then
    export EASYAIOT_RUNTIME_BUILD_ARCH="$_BUILD_ARCH"
fi
if [ -n "$_BUILD_MODULE" ]; then
    export EASYAIOT_RUNTIME_BUILD_MODULE="$_BUILD_MODULE"
fi
if [ -n "${EASYAIOT_RUNTIME_BUILD_MODULE:-}" ]; then
    _bm_norm=$(runtime_normalize_build_module "$EASYAIOT_RUNTIME_BUILD_MODULE")
    if [ "$_bm_norm" = "INVALID" ]; then
        print_error "无效的目标模块: ${EASYAIOT_RUNTIME_BUILD_MODULE}，可选: all | DEVICE | AI | VIDEO | WEB | APP | VISUALIZE | TRANSFORM | PANEL"
        exit 1
    fi
    if [ -n "$_bm_norm" ]; then
        export EASYAIOT_RUNTIME_BUILD_MODULE="$_bm_norm"
    else
        unset EASYAIOT_RUNTIME_BUILD_MODULE
    fi
fi
if [ -n "${EASYAIOT_RUNTIME_BUILD_ARCH:-}" ]; then
    _ba_norm=$(runtime_normalize_build_arch "$EASYAIOT_RUNTIME_BUILD_ARCH")
    if [ "$_ba_norm" = "INVALID" ]; then
        print_error "无效的目标架构: ${EASYAIOT_RUNTIME_BUILD_ARCH}，可选: all | amd64 | arm64"
        exit 1
    fi
    if [ -n "$_ba_norm" ]; then
        export EASYAIOT_RUNTIME_BUILD_ARCH="$_ba_norm"
    else
        unset EASYAIOT_RUNTIME_BUILD_ARCH
    fi
fi

if [ -n "${_EXPLICIT_PROFILE:-}" ]; then
    case "$(_resolve_deploy_profile_raw)" in
        mini|standard|full) ;;
        *)
            print_error "无效的部署形态: ${_EXPLICIT_PROFILE}，可选: mini | standard | full"
            exit 1 ;;
    esac
    _EXPLICIT_PROFILE="$(_resolve_deploy_profile_raw)"
fi

# ============================================================================
# 国内镜像源配置（默认开启，清华源优先）
# ============================================================================
APT_MIRROR_URL="${APT_MIRROR_URL:-https://mirrors.tuna.tsinghua.edu.cn}"
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmmirror.com/}"
APK_MIRROR="${APK_MIRROR:-mirrors.tuna.tsinghua.edu.cn}"
# AlmaLinux 8 aarch64 在清华源已缺失，YUM 默认走华为云（Dockerfile.arm 还会探测回退）
YUM_MIRROR_URL="${YUM_MIRROR_URL:-https://mirrors.huaweicloud.com}"
# 阿里云：清华 maven-public 对 org.graalvm.* 常缺包（404），会导致 iot-sink-biz 编译失败
MAVEN_MIRROR_URL="${MAVEN_MIRROR_URL:-https://maven.aliyun.com/repository/public}"

if $NATIVE_SOURCE; then
    APT_MIRROR_URL=""
    PIP_INDEX_URL="https://pypi.org/simple"
    NPM_REGISTRY="https://registry.npmjs.org/"
    APK_MIRROR=""
    YUM_MIRROR_URL=""
    MAVEN_MIRROR_URL=""
    print_warning "使用默认原始源（非国内镜像源）"
else
    print_info "使用国内镜像源加速（APT=${APT_MIRROR_URL:-无}, PIP=${PIP_INDEX_URL}, NPM=${NPM_REGISTRY}）"
fi
export APT_MIRROR_URL PIP_INDEX_URL NPM_REGISTRY APK_MIRROR YUM_MIRROR_URL MAVEN_MIRROR_URL

# ============================================================================
# 多架构支持（定义见 runtime_image_common.sh）
# ============================================================================
ALL_ARCHS=("${ALL_RUNTIME_ARCHS[@]}")

detect_arch() { runtime_detect_arch; }
is_native_arch() { runtime_is_native_arch "$1"; }
arch_to_platform() { runtime_arch_to_platform "$1"; }

CURRENT_ARCH=$(detect_arch)

# 检测镜像实际架构
image_actual_arch() {
    docker image inspect "$1" --format '{{.Architecture}}' 2>/dev/null || echo ""
}

# ★ 验证镜像架构与目标架构一致，不一致则报错
verify_image_arch() {
    local ref="$1" expected="${2:-$CURRENT_ARCH}"
    local actual; actual=$(image_actual_arch "$ref")
    if [ -z "$actual" ]; then
        print_error "无法检测镜像架构: ${ref}"
        return 1
    fi
    if [ "$actual" != "$expected" ]; then
        print_error "镜像架构不匹配! ${ref} 实际=${actual} 期望=${expected}"
        return 1
    fi
    return 0
}

# ============================================================================
# 镜像映射与命名（数组与 runtime_* 定义见 runtime_image_common.sh）
# ============================================================================
remote_ref() { runtime_remote_ref "$@"; }
manifest_ref() { runtime_manifest_ref "$@"; }
local_ref() { runtime_local_ref "$@"; }
is_profile_dependent() { runtime_is_profile_dependent "$@"; }
_profile_label() { runtime_profile_label "$@"; }

# ============================================================================
# 跨架构构建支持（无 QEMU 依赖）
# ============================================================================
# 策略：
#   1. 先在宿主机原生架构执行 install_linux.sh build，完成所有编译
#      （Maven、Vite、pip install 等），产出 JAR / dist 等产物。
#   2. 针对目标架构，docker build --platform <target> 仅拉取目标架构的
#      base image，然后 COPY 本机编译产物完成镜像包装。
#   3. 跨架构 docker build --platform 拉取目标架构 base image 并 COPY 产物；
#      若 Dockerfile 含 RUN 步骤，x86 宿主机需 QEMU/binfmt（runtime_ensure_qemu_binfmt）。
# ============================================================================

# 执行宿主机原生架构的完整编译（install_linux.sh build）
# 这一步完成所有 Maven、Vite、pip install 等耗时操作
ensure_native_build() {
    if [ "${_NATIVE_BUILT:-0}" = "1" ]; then
        return 0
    fi
    print_header "阶段 0：宿主机本机编译（架构: ${CURRENT_ARCH}）"
    echo ""
    print_info "执行 install_linux.sh build 完成所有本机编译 ..."
    local install_script="${SCRIPT_DIR}/install_linux.sh"
    if [ ! -f "$install_script" ]; then
        print_error "install_linux.sh 不存在: ${install_script}"
        return 1
    fi
    local rc=0
    (
        cd "$PROJECT_ROOT"
        # 传递 FORCE_REBUILD，使各模块 install 脚本在复用模式下跳过已有镜像
        if is_force_rebuild; then
            export FORCE_REBUILD=1
        else
            export FORCE_REBUILD=0
        fi
        export EASYAIOT_RUNTIME_BUILD=1
        bash "$install_script" build 2>&1 | tee "${LOG_DIR}/native_build_${CURRENT_ARCH}.log"
    ) || rc=$?
    if [ $rc -ne 0 ]; then
        print_error "本机编译失败 (exit=${rc})，请检查日志"
        return 1
    fi
    print_success "本机编译完成 (${CURRENT_ARCH})"
    _NATIVE_BUILT=1
    return 0
}

# ============================================================================
# 多架构 Manifest 管理
# ============================================================================
create_and_push_manifest() {
    local manifest_ref="$1"; shift
    local -a arch_refs=("$@")
    if [ ${#arch_refs[@]} -eq 0 ]; then
        print_warning "没有架构引用，跳过 manifest: ${manifest_ref}"
        return 1
    fi
    print_info "创建多架构 manifest: ${manifest_ref}（$(printf '%s ' "${arch_refs[@]}")）"

    # ★ 校验所有 arch_ref 已存在于远程（tag_and_push 应已推送 :arch 镜像）
    local missing=0
    for aref in "${arch_refs[@]}"; do
        if ! docker manifest inspect "$aref" >/dev/null 2>&1; then
            print_error "远程不存在架构镜像: ${aref}（manifest create 将失败）"
            missing=$((missing + 1))
        fi
    done
    if [ $missing -gt 0 ]; then
        print_error "有 ${missing} 个架构镜像缺失，跳过 manifest: ${manifest_ref}"
        return 1
    fi

    # ★ 若远程已有旧 manifest list，先删除（方便下次干净重建）
    docker manifest rm "$manifest_ref" 2>/dev/null || true

    # ★ 确认 manifest 是否真正已删除（rm 可能因权限/网络问题静默失败）
    local manifest_exists=false
    if docker manifest inspect "$manifest_ref" >/dev/null 2>&1; then
        manifest_exists=true
    fi

    # ★ 解析 arch 引用：若远程 arch 标签是 manifest list（上次构建遗留），
    #   提取对应架构的单镜像 digest 并用 @sha256:... 引用。
    #   修复 grep 大小写：Docker JSON 使用 "mediaType"（小写 m），非 "MediaType"
    #   同时兼容两种大小写格式。
    local -a resolved_refs=()
    for aref in "${arch_refs[@]}"; do
        if ! docker manifest inspect "$aref" >/dev/null 2>&1; then
            print_error "远程不存在架构镜像: ${aref}"
            return 1
        fi

        local ml_json; ml_json=$(docker manifest inspect "$aref" 2>/dev/null)
        local is_ml=false
        # OCI 格式: application/vnd.oci.image.index.v1+json  → 含 "image.index"
        # Docker 格式: application/vnd.docker.distribution.manifest.list.v2+json → 含 "manifest.list"
        if echo "$ml_json" | grep -qiE '"mediaType".*(manifest\.list|image\.index)'; then
            is_ml=true
        fi

        if ! $is_ml; then
            # 正常单架构镜像，直接使用
            resolved_refs+=("$aref")
            continue
        fi

        # ★ arch_ref 是 manifest list → 提取目标架构的单镜像 digest
        print_info "远程 ${aref} 是 manifest list，提取单架构 manifest digest..."
        local arch_label="${aref##*:}"
        # arm32 → OCI architecture "arm"；其余保持原样
        local oci_arch="$arch_label"
        [ "$arch_label" = "arm32" ] && oci_arch="arm"

        local digest; digest=$(echo "$ml_json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('manifests', []):
    if m.get('platform', {}).get('architecture') == '${oci_arch}':
        print(m['digest'])
        break
" 2>/dev/null)

        if [ -z "$digest" ]; then
            print_warning "无法从 manifest list 提取 ${arch_label} 单架构 digest: ${aref}"
            print_info "提示：用 --force-rebuild 重新构建后可恢复"
            return 1
        fi

        # 构造 digest 引用：registry/repo@sha256:...
        local repo_part="${aref%:*}"
        resolved_refs+=("${repo_part}@${digest}")
        print_info "  → ${digest:0:19}..."
    done

    # ★ 创建 manifest list
    # --amend 用于修改已存在的 manifest list；若不存在则直接创建
    local all_refs="${resolved_refs[*]}"
    local create_cmd
    if $manifest_exists; then
        create_cmd="--amend ${manifest_ref} ${all_refs}"
    else
        create_cmd="${manifest_ref} ${all_refs}"
    fi

    if ! docker manifest create ${create_cmd} 2>&1; then
        print_warning "manifest create 失败: ${manifest_ref}"
        return 1
    fi
    # ★ 注解各架构的 OS/Arch（resolved_refs 与 arch_refs 索引一一对应）
    for idx in "${!resolved_refs[@]}"; do
        local arch_part="${arch_refs[$idx]##*:}"
        docker manifest annotate "$manifest_ref" "${resolved_refs[$idx]}" --os linux --arch "${arch_part}" 2>/dev/null || true
    done
    if $DO_PUSH; then
        print_info "推送 manifest: ${manifest_ref}"
        if runtime_docker_upload_with_retry "推送 manifest ${manifest_ref}" docker manifest push "$manifest_ref" --purge; then
            print_success "manifest 推送成功: ${manifest_ref}"
        else
            print_warning "manifest 推送失败: ${manifest_ref}"
            return 1
        fi
    else
        print_info "manifest 已创建（未推送）: ${manifest_ref}"
    fi
    return 0
}

# ============================================================================
# Docker 环境检查
# ============================================================================
check_docker() {
    print_info "检查 Docker 安装状态..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装"; exit 1
    fi
    print_success "Docker 已安装: $(docker --version 2>/dev/null || echo '未知版本')"
    if docker info &> /dev/null; then return 0; fi
    local err; err=$(docker info 2>&1)
    if echo "$err" | grep -qi "permission denied"; then
        print_error "没有权限访问 Docker daemon"
        echo "  解决方案: sudo usermod -aG docker \$USER 然后重新登录"
        exit 1
    elif echo "$err" | grep -qi "Is the docker daemon running"; then
        print_error "Docker daemon 未运行"
        echo "  解决方案: sudo systemctl start docker"
        exit 1
    else
        print_error "无法连接到 Docker daemon: $err"
        exit 1
    fi
}

# ★ 跨架构构建前检查磁盘空间并清理 Docker
# PyTorch devel 基础镜像约 10GB+，多架构拉取极易打满磁盘。
# 清理时故意不跑 docker system prune -af，以免删掉已缓存的 ARM 基础镜像。
ensure_docker_disk_space() {
    local target_arch="${1:-}"
    local df_path="${DOCKER_DATA_ROOT:-/var/lib/docker}"
    # 尝试从 docker info 推断 data root
    local inferred; inferred=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo "")
    [ -n "$inferred" ] && df_path="$inferred"

    local avail_kb; avail_kb=$(df -k "$df_path" 2>/dev/null | awk 'NR==2{print $4}' || echo "0")
    local avail_gb=$((avail_kb / 1024 / 1024))
    local min_gb=20  # 跨架构构建建议至少 20GB

    print_info "Docker 数据目录: ${df_path}, 可用空间: ${avail_gb} GB"

    if [ "$avail_gb" -lt "$min_gb" ]; then
        print_warning "可用磁盘空间不足 (${avail_gb} GB < ${min_gb} GB)，尝试清理容器/悬空镜像/构建缓存（保留跨架构基础镜像）..."
        docker container prune -f 2>/dev/null || true
        docker image prune -f 2>/dev/null || true
        docker builder prune -af 2>/dev/null || true
        avail_kb=$(df -k "$df_path" 2>/dev/null | awk 'NR==2{print $4}' || echo "0")
        avail_gb=$((avail_kb / 1024 / 1024))
        print_info "清理后可用空间: ${avail_gb} GB"
        if [ "$avail_gb" -lt "$min_gb" ]; then
            print_warning "清理后仍不足 ${min_gb} GB，[${target_arch}] 跨架构构建可能因磁盘满而失败"
            print_info "可手动清理未用运行时镜像；请勿删除 pytorch/manylinuxaarch64-builder 等 ARM 基础镜像"
        fi
    fi
}

# ============================================================================
# 镜像 tag & push 公共函数
# ============================================================================

# 推送成功后删除本地镜像（local + remote tag），避免 build-runtime 串行构建时磁盘被逐步占满
cleanup_local_after_push() {
    local local_ref="$1"
    local remote_ref="${2:-}"
    print_info "推送完成，删除本地镜像以释放磁盘..."
    if [ -n "$remote_ref" ] && [ "$remote_ref" != "$local_ref" ]; then
        docker rmi "$remote_ref" 2>/dev/null || true
    fi
    if docker rmi "$local_ref" 2>/dev/null; then
        print_success "已删除本地镜像: ${local_ref}"
    else
        # 可能仍有其他 tag 指向同一 image id，或镜像本就不存在
        print_warning "未能删除 ${local_ref}（可能仍有其他标签引用或不存在）"
    fi
}

# WEB 本机镜像在推送删除前提取 dist，供后续跨架构构建复用
extract_web_dist_before_cleanup() {
    local lref="$1" profile="$2"
    local dst="${PROJECT_ROOT}/WEB/dist-prebuilt-${profile}"
    if [ -d "$dst" ]; then
        print_info "WEB dist 已存在，跳过提取: ${dst}/"
        return 0
    fi
    if ! docker image inspect "$lref" >/dev/null 2>&1; then
        print_warning "WEB 镜像不存在，无法提取 dist: ${lref}"
        return 0
    fi
    print_info "提取 WEB dist 供跨架构复用: ${lref} → ${dst}/"
    rm -rf "$dst" 2>/dev/null || true
    local cid
    cid=$(docker create "$lref" 2>/dev/null) || true
    if [ -n "$cid" ]; then
        docker cp "${cid}:/usr/share/nginx/html/." "$dst/" 2>/dev/null || \
            print_warning "提取 dist 失败（非致命），跨架构 WEB 将回退到完整 vite build"
        docker rm "$cid" >/dev/null 2>&1
    fi
}

tag_and_push() {
    local local_ref="$1" remote_ref="$2"
    print_info "打标签: ${local_ref} → ${remote_ref}"
    docker tag "$local_ref" "$remote_ref" || { print_error "打标签失败"; return 1; }

    local arch_suffix="${remote_ref##*:}"
    local pushed=false

    # ★ 推送策略：
    #   - 带架构后缀（:amd64/:arm64/:arm32）：始终推送，manifest create 需从远程读取
    #   - manifest 标签（:latest/:tag）：由 DO_PUSH 控制（在 create_and_push_manifest 中处理）
    case "$arch_suffix" in
        amd64|arm64|arm32)
            # ★ 推送前校验镜像架构与标签一致
            if ! verify_image_arch "$remote_ref" "$arch_suffix"; then
                print_error "远程标签镜像架构校验失败，拒绝推送: ${remote_ref}"
                docker rmi "$remote_ref" 2>/dev/null || true
                return 1
            fi
            print_info "推送架构镜像: ${remote_ref}"
            if ! runtime_docker_push_with_retry "$remote_ref"; then
                print_error "推送失败: ${remote_ref}"
                return 1
            fi
            print_success "推送成功: ${remote_ref}"
            pushed=true
            ;;
        *)
            if $DO_PUSH; then
                print_info "推送: ${remote_ref}"
                runtime_docker_push_with_retry "$remote_ref" || { print_error "推送失败: ${remote_ref}"; return 1; }
                print_success "推送成功: ${remote_ref}"
                pushed=true
            fi
            ;;
    esac

    # ★ 推送成功即删本地镜像，避免多模块/多架构串行构建占满磁盘
    if $pushed; then
        cleanup_local_after_push "$local_ref" "$remote_ref"
    fi
    return 0
}

# ============================================================================
# 功能 1：构建与推送
# ============================================================================

# 使用模块 install 脚本构建单个模块的镜像
# 参数: module_dir local_name local_ref target_arch
# 本机架构：直接执行 install 脚本 build（复用 ensure_native_build 产物）
# 跨架构：docker build --platform <target> 仅 COPY 产物 + 拉取目标架构 base image
build_module_with_install_script() {
    local module_dir="$1" local_name="$2" local_ref="$3" target_arch="${4:-$CURRENT_ARCH}"
    local module_path="${PROJECT_ROOT}/${module_dir}"
    [ -d "$module_path" ] || { print_error "模块目录不存在: ${module_path}"; return 1; }

    local native_ref
    native_ref=$(local_ref "$local_name")

    # --force-rebuild：强制重建，跳过"已存在"检查；否则检查目标 local_ref 是否已就绪
    if ! is_force_rebuild; then
        if docker image inspect "$local_ref" >/dev/null 2>&1; then
            local existing; existing=$(image_actual_arch "$local_ref")
            if [ "$existing" = "$target_arch" ]; then
                print_info "${local_ref} 已存在（${existing}），跳过构建"
                return 0
            fi
            print_info "${local_ref} 架构不匹配 (现有=${existing}, 期望=${target_arch})，重新构建"
        fi
    else
        print_info "强制重建模式：忽略已存在的镜像缓存"
    fi

    # ★ 清除架构不匹配的镜像（本机/跨架构通用）
    # 各模块 install_linux.sh 的增量检测只按「镜像是否存在」跳过构建，不校验架构。
    # 若本地残留其他架构镜像（如 amd64），install 脚本会直接跳过，导致推送时架构校验失败。
    if ! is_force_rebuild; then
        local need_clean=false ref existing
        local -a refs_to_check=("$local_ref")
        [ "$native_ref" != "$local_ref" ] && refs_to_check+=("$native_ref")
        for ref in "${refs_to_check[@]}"; do
            if docker image inspect "$ref" >/dev/null 2>&1; then
                existing=$(image_actual_arch "$ref")
                if [ -n "$existing" ] && [ "$existing" != "$target_arch" ]; then
                    print_info "镜像架构不匹配: ${ref} (现有=${existing}, 期望=${target_arch})，将清理并重建"
                    need_clean=true
                fi
            fi
        done
        if $need_clean; then
            for ref in "${refs_to_check[@]}"; do
                docker rmi "$ref" 2>/dev/null || true
            done
        fi
    fi

    # 选择 install 脚本
    # ★ 优先使用架构专属脚本（如 install_linux_arm.sh），它内置正确的 Dockerfile 和基础镜像
    local install_script=""
    case "$target_arch" in
        arm64|arm32)
            install_script="install_linux_arm.sh"
            [ -f "${module_path}/${install_script}" ] || install_script="" ;;
    esac
    # 回退到通用脚本（WEB/DEVICE 等无 arm 脚本的模块，跨架构靠 --platform）
    if [ -z "$install_script" ]; then
        install_script="install_linux.sh"
    fi
    [ -f "${module_path}/${install_script}" ] || { print_error "安装脚本不存在: ${module_path}/${install_script}"; return 1; }

    # 修复换行符
    grep -q $'\r' "${module_path}/${install_script}" 2>/dev/null && sed -i 's/\r$//' "${module_path}/${install_script}" 2>/dev/null || true

    local arch_note=""; ! is_native_arch "$target_arch" && arch_note=" [跨架构: ${target_arch}]"
    print_info "执行 ${module_dir}/${install_script} build${arch_note} ..."

    # 本地镜像名可能含仓库前缀（如 easyaiot/panel），日志文件名需去掉路径分隔符
    local log_name="${local_name//\//-}"
    local build_log="${LOG_DIR}/build_${log_name}_${target_arch}_$(date +%Y%m%d_%H%M%S).log"
    local rc=0

    # subshell 内导出子进程环境，避免 FORCE_REBUILD=0|1 污染本脚本的布尔变量
    (
        if is_force_rebuild; then export FORCE_REBUILD=1; else export FORCE_REBUILD=0; fi
        # ★ 跨架构平台导出策略：
        #   - 架构专属脚本（install_linux_arm.sh）自带 DOCKER_PLATFORM 和基础镜像，不导出避免覆盖；
        #     但需设置 EASYAIOT_CROSS_BUILD=1 告诉脚本允许在 x86 宿主机上交叉构建 arm64 镜像。
        #   - 通用脚本（install_linux.sh）跨架构时需导出 DOCKER_PLATFORM 供 --platform 使用
        if ! is_native_arch "$target_arch"; then
            if [ "$install_script" = "install_linux.sh" ]; then
                export DOCKER_PLATFORM="$(arch_to_platform "$target_arch")"
            else
                export EASYAIOT_CROSS_BUILD=1
            fi
        fi
        cd "$module_path"
        bash "$install_script" build 2>&1 | tee "$build_log"
    ) || rc=$?

    if [ $rc -ne 0 ]; then
        print_error "构建失败 (exit=${rc})，日志: ${build_log}"
        if [ -f "$build_log" ]; then
            tail -40 "$build_log" | while IFS= read -r line; do echo "  $line"; done
        fi
        return 1
    fi

    # 跨架构：install 脚本产出 native_ref，需重打标签为目标架构标签
    if ! is_native_arch "$target_arch"; then
        if docker image inspect "$native_ref" >/dev/null 2>&1; then
            # ★ native_ref 与 local_ref 可能相同（无 profile 后缀时），避免 self-tag + self-rmi
            if [ "$native_ref" != "$local_ref" ]; then
                print_info "跨架构镜像已生成，重打标签: ${native_ref} → ${local_ref}"
                docker tag "$native_ref" "$local_ref" 2>/dev/null || {
                    print_error "重打标签失败: ${native_ref} → ${local_ref}"; return 1
                }
                # 清理 native 标签，防止污染
                docker rmi "$native_ref" 2>/dev/null || true
            fi
            # 校验跨架构构建产物的架构是否正确
            if ! verify_image_arch "$local_ref" "$target_arch"; then
                print_error "跨架构构建产物架构校验失败，镜像已删除"
                docker rmi "$local_ref" 2>/dev/null || true
                rm -f "$build_log"
                return 1
            fi
            rm -f "$build_log"
            return 0
        fi
    fi

    # 本机构建也校验架构一致性（优先校验目标 local_ref，兼容 install 脚本产出在 native_ref 的情况）
    if is_native_arch "$target_arch"; then
        local verify_ref="$local_ref"
        if ! docker image inspect "$verify_ref" >/dev/null 2>&1; then
            verify_ref="$native_ref"
        fi
        if ! verify_image_arch "$verify_ref" "$target_arch"; then
            print_error "本机构建产物架构校验失败，镜像已删除"
            docker rmi "$verify_ref" 2>/dev/null || true
            rm -f "$build_log"
            return 1
        fi
    fi
    rm -f "$build_log"
    return 0
}

# 检查单个本地镜像是否已就绪（存在且架构匹配）
local_image_ready() {
    local lname="$1" profile="$2" target_arch="$3"
    local lref; lref=$(local_ref "$lname" "$profile")
    if ! docker image inspect "$lref" >/dev/null 2>&1; then
        return 1
    fi
    local actual; actual=$(image_actual_arch "$lref")
    [ "$actual" = "$target_arch" ]
}

# 检查构建计划中指定架构的本地镜像是否已全部就绪（依赖外层 build_profiles；单模块时仅检查该模块）
all_build_plan_images_ready_for_arch() {
    local target_arch="$1" profile mapping tmp rname lname

    if runtime_build_includes_module AI || runtime_build_includes_module VIDEO || runtime_build_includes_module PANEL; then
        for mapping in "${INDEPENDENT_MODULES[@]}"; do
            rname="${mapping%%|*}"; tmp="${mapping#*|}"; lname="${tmp%%|*}"
            is_profile_dependent "$rname" && continue
            local _imod="${mapping##*|}"
            case "$_imod" in
                AI|VIDEO|PANEL) runtime_build_includes_module "$_imod" || continue ;;
                *) continue ;;
            esac
            local_image_ready "$lname" "" "$target_arch" || return 1
        done
    fi

    # 仅 full 形态模块（APP / VISUALIZE / TRANSFORM）
    for mapping in "${FULL_ONLY_MODULES[@]}"; do
        local rname="${mapping%%|*}"
        local tmp="${mapping#*|}"
        local lname="${tmp%%|*}"
        local mod="${mapping##*|}"
        runtime_build_includes_module "$mod" || continue
        for profile in "${build_profiles[@]}"; do
            if [ "$profile" = "full" ]; then
                local_image_ready "$lname" "" "$target_arch" || return 1
                break
            fi
        done
    done

    if runtime_build_includes_module DEVICE; then
        for lname in "${DEVICE_LOCAL_NAMES[@]}"; do
            local_image_ready "$lname" "" "$target_arch" || return 1
        done
    fi

    if runtime_build_includes_module WEB; then
        for profile in "${build_profiles[@]}"; do
            local_image_ready "web-service" "$profile" "$target_arch" || return 1
        done
    fi
    return 0
}

# 检查构建计划中所有架构的本地镜像是否已就绪（依赖外层 build_profiles / build_archs）
all_build_plan_images_ready() {
    local target_arch
    for target_arch in "${build_archs[@]}"; do
        all_build_plan_images_ready_for_arch "$target_arch" || return 1
    done
    return 0
}

# 打印各架构构建计划摘要
print_build_plan_summary() {
    local target_arch
    print_info "构建计划："
    for target_arch in "${build_archs[@]}"; do
        if is_force_rebuild; then
            print_info "  ${target_arch}: 强制重建后推送"
        elif all_build_plan_images_ready_for_arch "$target_arch"; then
            print_info "  ${target_arch}: 本地镜像已就绪，仅推送"
        else
            print_info "  ${target_arch}: 部分镜像缺失，构建后推送"
        fi
    done
}

# 构建 DEVICE 模块的所有镜像
# 参数: target_arch
# 跨架构时：Maven 编译产物（JAR）架构无关可复用，仅 Docker 镜像通过 --platform 重建
build_device_all() {
    local target_arch="${1:-$CURRENT_ARCH}"
    local device_path="${PROJECT_ROOT}/DEVICE"
    local install_script="${device_path}/install_linux.sh"

    [ -f "$install_script" ] || { print_error "DEVICE 安装脚本不存在: ${install_script}"; return 1; }
    grep -q $'\r' "$install_script" 2>/dev/null && sed -i 's/\r$//' "$install_script" 2>/dev/null || true

    if ! is_force_rebuild; then
        local all_device_ready=true
        for lname in "${DEVICE_LOCAL_NAMES[@]}"; do
            local_image_ready "$lname" "" "$target_arch" || { all_device_ready=false; break; }
        done
        if $all_device_ready; then
            print_info "DEVICE 模块本地镜像已全部就绪（${target_arch}），跳过构建"
            return 0
        fi
    fi

    local arch_note=""; ! is_native_arch "$target_arch" && arch_note=" [跨架构: ${target_arch}]"
    print_info "执行 DEVICE/install_linux.sh build${arch_note}（Maven 编译 + 镜像构建）..."

    local build_log="${LOG_DIR}/build_device_${target_arch}_$(date +%Y%m%d_%H%M%S).log"
    local rc=0

    # ★ 清除架构不匹配的 DEVICE 镜像（本机/跨架构通用）
    # DEVICE/install_linux.sh 的增量检测只按 content-hash 判断是否重编，不校验架构。
    # 若上一次跨架构构建残留了 arm64 镜像，本机 amd64 构建会直接跳过，导致推送时
    # 架构校验失败。必须先清除架构不匹配的镜像，再让脚本重新构建。
    local need_clean=false
    for i in "${!DEVICE_LOCAL_NAMES[@]}"; do
        local dlref; dlref=$(local_ref "${DEVICE_LOCAL_NAMES[$i]}")
        if docker image inspect "$dlref" >/dev/null 2>&1; then
            local actual; actual=$(image_actual_arch "$dlref")
            if [ -n "$actual" ] && [ "$actual" != "$target_arch" ]; then
                print_info "DEVICE 镜像架构不匹配: ${dlref} (现有=${actual}, 期望=${target_arch})，将清理并重建"
                need_clean=true
                break
            fi
        fi
    done
    if $need_clean; then
        print_info "删除架构不匹配的 DEVICE 镜像，强制为 ${target_arch} 重建..."
        for i in "${!DEVICE_LOCAL_NAMES[@]}"; do
            docker rmi "$(local_ref "${DEVICE_LOCAL_NAMES[$i]}")" 2>/dev/null || true
        done
    fi

    (
        if is_force_rebuild; then export FORCE_REBUILD=1; else export FORCE_REBUILD=0; fi
        if ! is_native_arch "$target_arch"; then
            export DOCKER_PLATFORM="$(arch_to_platform "$target_arch")"
        fi
        cd "$device_path"
        bash "$install_script" build 2>&1 | tee "$build_log"
    ) || rc=$?

    # 跨架构：重打 DEVICE 镜像标签并清理 native 标签
    if ! is_native_arch "$target_arch"; then
        for i in "${!DEVICE_REMOTE_NAMES[@]}"; do
            local lname="${DEVICE_LOCAL_NAMES[$i]}"
            local nref; nref=$(local_ref "$lname")
            local aref; aref=$(local_ref "$lname" "" "$target_arch")
            if docker image inspect "$nref" >/dev/null 2>&1; then
                # ★ nref 与 aref 相同时（无 profile 后缀），跳过 self-tag + self-rmi
                if [ "$nref" != "$aref" ]; then
                    docker tag "$nref" "$aref" 2>/dev/null || true
                    docker rmi "$nref" 2>/dev/null || true
                fi
            fi
        done
    fi

    if [ $rc -ne 0 ]; then
        # 检查是否至少部分镜像成功
        local any_exist=false
        for lname in "${DEVICE_LOCAL_NAMES[@]}"; do
            docker image inspect "$(local_ref "$lname")" >/dev/null 2>&1 && { any_exist=true; break; }
        done
        if ! $any_exist; then
            print_error "DEVICE 构建失败，日志: ${build_log}"
            tail -40 "$build_log" | while IFS= read -r line; do echo "  $line"; done
            return 1
        fi
        print_warning "DEVICE 部分镜像构建失败，继续处理已成功的镜像"
    fi
    rm -f "$build_log"
    return 0
}

# 构建单个模块（按 remote_name 分发到对应的安装脚本）
build_single_module() {
    local remote_name="$1" local_ref="$2" target_arch="${3:-$CURRENT_ARCH}"

    case "$remote_name" in
        aiot-ai)    build_module_with_install_script "AI" "ai-service" "$local_ref" "$target_arch" ;;
        aiot-video) build_module_with_install_script "VIDEO" "video-service" "$local_ref" "$target_arch" ;;
        aiot-web)   build_module_with_install_script "WEB" "web-service" "$local_ref" "$target_arch" ;;
        aiot-app)   build_module_with_install_script "APP" "app-service" "$local_ref" "$target_arch" ;;
        aiot-visualize-web) build_module_with_install_script "VISUALIZE" "visualize-service" "$local_ref" "$target_arch" ;;
        aiot-transform) build_module_with_install_script "TRANSFORM" "transform-service" "$local_ref" "$target_arch" ;;
        aiot-panel) build_module_with_install_script "PANEL" "easyaiot/panel" "$local_ref" "$target_arch" ;;
        *)
            # DEVICE 模块：统一由 build_device_all 处理
            build_device_all "$target_arch" || return 1
            ;;
    esac
}

# 构建单个模块、打标签推送并登记 manifest 引用（build_all_modules 内部复用，消除重复逻辑）
# 参数: rname lname profile target_arch  （profile 为空串表示共享镜像）
# 依赖外层动态作用域变量: success_all / failed_all / _MANIFEST_ARCH_REFS
_build_push_track() {
    local rname="$1" lname="$2" profile="$3" target_arch="$4"
    local lref rref mref step_label fail_label
    lref=$(local_ref "$lname" "$profile" "$target_arch")
    rref=$(remote_ref "$rname" "$profile" "$target_arch")
    mref=$(manifest_ref "$rname" "$profile")
    if [ -n "$profile" ]; then
        if ! is_force_rebuild && local_image_ready "$lname" "$profile" "$target_arch"; then
            step_label="推送: ${rname} (${profile}, ${target_arch})"
        else
            step_label="构建并推送: ${rname} (${profile}, ${target_arch})"
        fi
        fail_label="构建/推送失败: ${rname} (${profile}, ${target_arch})"
    else
        if ! is_force_rebuild && local_image_ready "$lname" "" "$target_arch"; then
            step_label="推送: ${rname} [${target_arch}]"
        else
            step_label="构建并推送: ${rname} [${target_arch}]"
        fi
        fail_label="构建/推送失败: ${rname} [${target_arch}]"
    fi
    print_step "$step_label"
    if ! build_single_module "$rname" "$lref" "$target_arch"; then
        print_error "$fail_label"
        failed_all=$((failed_all + 1))
        return 1
    fi
    # WEB 本机构建且还需跨架构：推送（会删本地镜像）前先提取 dist
    if [ "$lname" = "web-service" ] && [ -n "$profile" ] && is_native_arch "$target_arch"; then
        if declare -p cross_archs >/dev/null 2>&1 && [ ${#cross_archs[@]} -gt 0 ]; then
            extract_web_dist_before_cleanup "$lref" "$profile"
        fi
    fi
    if tag_and_push "$lref" "$rref"; then
        print_success "已推送并清理本地镜像: ${rref}"
        _MANIFEST_ARCH_REFS["$mref"]="${_MANIFEST_ARCH_REFS["$mref"]:+${_MANIFEST_ARCH_REFS["$mref"]} }${rref}"
        success_all=$((success_all + 1))
        return 0
    fi
    print_error "$fail_label"
    failed_all=$((failed_all + 1))
    return 1
}

# 统计当前构建计划下单架构应构建的镜像数量（用于跨架构前置失败时汇总；单模块时仅计该模块）
count_planned_images_for_arch() {
    local -a profiles=("$@")
    local count=0 mapping rname _bp

    if runtime_build_includes_module AI || runtime_build_includes_module VIDEO || runtime_build_includes_module PANEL; then
        for mapping in "${INDEPENDENT_MODULES[@]}"; do
            rname="${mapping%%|*}"
            is_profile_dependent "$rname" && continue
            local _imod="${mapping##*|}"
            case "$_imod" in
                AI|VIDEO|PANEL) runtime_build_includes_module "$_imod" || continue ;;
                *) continue ;;
            esac
            count=$((count + 1))
        done
    fi

    # full 专属：APP / VISUALIZE / TRANSFORM
    for mapping in "${FULL_ONLY_MODULES[@]}"; do
        local _fmod="${mapping##*|}"
        runtime_build_includes_module "$_fmod" || continue
        for _bp in "${profiles[@]}"; do
            if [ "$_bp" = "full" ]; then
                count=$((count + 1))
                break
            fi
        done
    done

    if runtime_build_includes_module DEVICE; then
        count=$((count + ${#DEVICE_REMOTE_NAMES[@]}))
    fi

    if runtime_build_includes_module WEB; then
        count=$((count + ${#profiles[@]}))
    fi
    echo "$count"
}

# 从本机 WEB 镜像提取 dist，供仅跨架构构建时复用
extract_web_dist_from_native_images() {
    local -a profiles=("$@")
    local profile img_ref dst cid
    print_info "从本机 WEB 镜像提取 dist 供跨架构复用 ..."
    for profile in "${profiles[@]}"; do
        dst="${PROJECT_ROOT}/WEB/dist-prebuilt-${profile}"
        if [ -d "$dst" ]; then
            print_info "  dist 已存在: ${dst}/"
            continue
        fi
        img_ref=$(local_ref "web-service" "$profile")
        if docker image inspect "$img_ref" >/dev/null 2>&1; then
            print_info "  → ${img_ref} → ${dst}/"
            rm -rf "$dst" 2>/dev/null || true
            cid=$(docker create "$img_ref" 2>/dev/null)
            if [ -n "$cid" ]; then
                docker cp "${cid}:/usr/share/nginx/html/." "$dst/" 2>/dev/null || \
                    print_warning "提取 dist 失败（非致命），跨架构 WEB 将回退到完整 vite build"
                docker rm "$cid" >/dev/null 2>&1
            fi
        else
            print_warning "本机 WEB 镜像不存在: ${img_ref}，跨架构 WEB 将回退到完整 vite build"
        fi
    done
}

# 单架构跨架构构建时，本机架构不在 build_archs 中，需提前提取 WEB dist
ensure_web_dist_for_cross_arch_build() {
    local -n archs=$1
    local -n profiles=$2
    local target_arch has_cross=false has_native=false
    for target_arch in "${archs[@]}"; do
        if is_native_arch "$target_arch"; then
            has_native=true
        else
            has_cross=true
        fi
    done
    if $has_cross && ! $has_native; then
        extract_web_dist_from_native_images "${profiles[@]}"
    fi
}

build_all_modules() {
    local -a build_profiles=()
    if [ -n "${_EXPLICIT_PROFILE:-}" ]; then
        build_profiles=("$_EXPLICIT_PROFILE")
    else
        build_profiles=("${ALL_DEPLOY_PROFILES[@]}")
    fi

    if ! runtime_validate_build_module_profile; then
        exit 1
    fi

    local -a build_archs=()
    if ! runtime_resolve_build_archs; then
        exit 1
    fi
    build_archs=("${RUNTIME_RESOLVED_BUILD_ARCHS[@]}")

    local total_archs=${#build_archs[@]}
    local total_profiles=${#build_profiles[@]}

    print_header "运行时镜像构建与推送"
    runtime_log_registry_info
    echo "  当前架构: ${CURRENT_ARCH}"; printf '  构建架构: %s\n' "${build_archs[*]}"
    if runtime_is_single_module_build; then
        echo "  构建模块: ${EASYAIOT_RUNTIME_BUILD_MODULE}（单模块）"
    else
        echo "  构建模块: 全部 (DEVICE + AI + VIDEO + WEB + APP + VISUALIZE + TRANSFORM + PANEL)"
    fi
    if runtime_is_single_arch_build; then
        echo "  架构模式: 单架构（跳过多架构 manifest 更新）"
    else
        echo "  架构模式: 全部架构"
    fi
    echo "  Registry: ${REGISTRY}"; echo "  Tag: ${TAG}"
    echo "  Push: ${DO_PUSH}"; echo "  强制重建: ${FORCE_REBUILD}"
    printf '  构建形态: %s\n' "${build_profiles[*]}"
    echo ""

    check_docker

    # ★ 构建前先校验 CNB 登录与推送权限，避免长时间编译后推送失败
    if ! runtime_verify_registry_push_access "$REGISTRY"; then
        exit 1
    fi
    echo ""

    # ========================================================================
    # 阶段 0：宿主机本机编译（install_linux.sh build）
    #   - 全部架构镜像已就绪 → 跳过
    #   - 仅跨架构缺失、本机架构已就绪 → 跳过
    #   - 本机架构有缺失或强制重建 → 执行本机编译
    # ========================================================================
    print_build_plan_summary
    echo ""

    if runtime_is_single_module_build; then
        print_info "单模块构建 (${EASYAIOT_RUNTIME_BUILD_MODULE})：跳过全量本机编译，由模块 install 脚本按需构建"
        _NATIVE_BUILT=1
    elif ! is_force_rebuild && all_build_plan_images_ready; then
        print_info "所有架构的运行时镜像均已就绪，跳过本机编译"
        _NATIVE_BUILT=1
    elif ! is_force_rebuild && all_build_plan_images_ready_for_arch "$CURRENT_ARCH"; then
        print_info "本机架构 (${CURRENT_ARCH}) 镜像已就绪，跳过本机编译"
        _NATIVE_BUILT=1
    elif ! ensure_native_build; then
        print_error "本机编译失败，无法继续构建镜像"
        exit 1
    fi
    echo ""

    if runtime_build_includes_module WEB; then
        ensure_web_dist_for_cross_arch_build build_archs build_profiles
    fi

    local success_all=0 failed_all=0
    declare -A _MANIFEST_ARCH_REFS

    local native_arch="${build_archs[0]}"
    local -a cross_archs=()
    for a in "${build_archs[@]:1}"; do
        cross_archs+=("$a")
    done

    echo ""

    # ========================================================================
    # 逐架构 × 逐形态串行构建
    # 本机架构：复用阶段 0 产物，直接执行 install 脚本 build
    # 跨架构：docker build --platform <target> 拉取目标架构 base image + COPY 产物
    # ========================================================================
    for target_arch in "${build_archs[@]}"; do
        local arch_label; is_native_arch "$target_arch" && arch_label="本机原生" || arch_label="跨架构 (QEMU)"
        print_header "${target_arch} (${arch_label})"
        echo ""

        # ★ 每次循环重置 DOCKER_PLATFORM，避免上一轮跨架构值泄漏到本机架构构建
        unset DOCKER_PLATFORM
        # 跨架构：检查磁盘空间、配置 QEMU/binfmt、导出目标平台
        if ! is_native_arch "$target_arch"; then
            local cross_platform; cross_platform="$(arch_to_platform "$target_arch")"
            if ! runtime_ensure_qemu_binfmt "$cross_platform"; then
                print_error "跨架构构建前置检查失败 (${target_arch})，跳过本架构"
                failed_all=$((failed_all + $(count_planned_images_for_arch "${build_profiles[@]}")))
                continue
            fi
            ensure_docker_disk_space "$target_arch"
            export DOCKER_PLATFORM="$cross_platform"

            # ★ 仅当本次构建包含 AI 时预拉取 pytorch 基础镜像（约 10GB+）
            # 单模块 WEB/DEVICE/APP 等不应误触发 AI 依赖拉取
            if runtime_build_includes_module AI; then
                local arm_base_images=(
                    "pytorch/manylinuxaarch64-builder:cuda12.9"
                )
                local base_img
                for base_img in "${arm_base_images[@]}"; do
                    if ! docker image inspect "$base_img" >/dev/null 2>&1; then
                        print_info "预拉取 AI ARM 基础镜像: ${base_img}（约 10GB+，请耐心等待）..."
                        if ! docker pull --platform "$DOCKER_PLATFORM" "$base_img"; then
                            print_warning "预拉取失败: ${base_img}，构建时将由 install 脚本自动拉取"
                        else
                            print_success "AI ARM 基础镜像已就绪: ${base_img}"
                        fi
                    else
                        print_info "AI ARM 基础镜像已存在: ${base_img}"
                    fi
                done
            fi
        fi

        # ★ ARM 构建前预下载 pip wheel / ffmpeg（仅 AI/VIDEO 需要，避免单模块 WEB 误跑）
        case "$target_arch" in
            arm64|arm32)
                local -a _arm_wheel_mods=()
                runtime_build_includes_module AI && _arm_wheel_mods+=(ai)
                runtime_build_includes_module VIDEO && _arm_wheel_mods+=(video)
                if [ ${#_arm_wheel_mods[@]} -gt 0 ]; then
                    print_info "检查 ARM 离线缓存（.build-cache/arm/ pip-wheels: ${_arm_wheel_mods[*]}）..."
                    ensure_arm_python_wheels_cached "$PROJECT_ROOT" "${_arm_wheel_mods[@]}"
                fi
                if runtime_build_includes_module VIDEO; then
                    print_info "检查 ARM ffmpeg 离线缓存..."
                    ensure_arm_ffmpeg_cached "$PROJECT_ROOT"
                    stage_arm_ffmpeg_into_build_context "$PROJECT_ROOT" "${PROJECT_ROOT}/VIDEO" || true
                fi
                ;;
        esac

        # ── 共享模块（AI + VIDEO + PANEL，全形态）──
        if runtime_build_includes_module AI || runtime_build_includes_module VIDEO || runtime_build_includes_module PANEL; then
            for mapping in "${INDEPENDENT_MODULES[@]}"; do
                local rname="${mapping%%|*}"; local tmp="${mapping#*|}"; local lname="${tmp%%|*}"
                local _imod="${mapping##*|}"
                is_profile_dependent "$rname" && continue
                case "$_imod" in
                    AI|VIDEO|PANEL) runtime_build_includes_module "$_imod" || continue ;;
                    *) continue ;;
                esac
                _build_push_track "$rname" "$lname" "" "$target_arch"
            done
        fi

        # ── full 专属模块（APP / VISUALIZE / TRANSFORM）──
        for mapping in "${FULL_ONLY_MODULES[@]}"; do
            local _frname="${mapping%%|*}"
            local _ftmp="${mapping#*|}"
            local _flname="${_ftmp%%|*}"
            local _fmod="${mapping##*|}"
            runtime_build_includes_module "$_fmod" || continue
            local _bp
            for _bp in "${build_profiles[@]}"; do
                if [ "$_bp" = "full" ]; then
                    _build_push_track "$_frname" "$_flname" "" "$target_arch"
                    break
                fi
            done
        done

        # ── DEVICE ──
        if runtime_build_includes_module DEVICE; then
            build_device_all "$target_arch"
            for i in "${!DEVICE_REMOTE_NAMES[@]}"; do
                local drname="${DEVICE_REMOTE_NAMES[$i]}"; local dlname="${DEVICE_LOCAL_NAMES[$i]}"
                local dlref; dlref=$(local_ref "$dlname" "" "$target_arch")
                local drref; drref=$(remote_ref "$drname" "" "$target_arch")
                local dmref; dmref=$(manifest_ref "$drname" "")
                if docker image inspect "$dlref" >/dev/null 2>&1; then
                    print_step "推送: ${drname} [${target_arch}]"
                    if tag_and_push "$dlref" "$drref"; then
                        _MANIFEST_ARCH_REFS["$dmref"]="${_MANIFEST_ARCH_REFS["$dmref"]:+${_MANIFEST_ARCH_REFS["$dmref"]} }${drref}"
                        success_all=$((success_all + 1))
                    else
                        failed_all=$((failed_all + 1))
                    fi
                else
                    print_warning "DEVICE 镜像未找到: ${dlref}"
                    failed_all=$((failed_all + 1))
                fi
            done
        fi

        # ── WEB 各形态 ──
        if runtime_build_includes_module WEB; then
            for profile in "${build_profiles[@]}"; do
                export EASYAIOT_DEPLOY_PROFILE="$profile"
                apply_deploy_profile
                save_deploy_profile
                sync_deploy_profile_to_modules

                # 跨架构 WEB：复用本机构建的 dist
                if ! is_native_arch "$target_arch"; then
                    local prebuilt_src="${PROJECT_ROOT}/WEB/dist-prebuilt-${profile}"
                    if [ -d "$prebuilt_src" ]; then
                        print_info "跨架构 WEB: 复用本机预构建 dist/ → ${prebuilt_src}"
                        rm -rf "${PROJECT_ROOT}/WEB/dist-prebuilt" 2>/dev/null || true
                        mkdir -p "${PROJECT_ROOT}/WEB/dist-prebuilt"
                        cp -a "${prebuilt_src}/." "${PROJECT_ROOT}/WEB/dist-prebuilt/"
                        export SKIP_VITE_BUILD=1
                    else
                        print_warning "跨架构 WEB: 预构建 dist 不存在 ${prebuilt_src}，将回退到容器内 vite build"
                        unset SKIP_VITE_BUILD
                    fi
                fi

                _build_push_track "aiot-web" "web-service" "$profile" "$target_arch"

                # 清理跨架构 WEB 临时 dist
                if ! is_native_arch "$target_arch"; then
                    rm -rf "${PROJECT_ROOT}/WEB/dist-prebuilt" 2>/dev/null || true
                    unset SKIP_VITE_BUILD
                fi
            done
        fi

        # WEB dist 已在各形态推送前按需提取（推送后本地镜像会删除），此处仅作兜底提示
        if runtime_build_includes_module WEB && is_native_arch "$target_arch" && [ ${#cross_archs[@]} -gt 0 ]; then
            local _missing_dist=0
            for profile in "${build_profiles[@]}"; do
                if [ ! -d "${PROJECT_ROOT}/WEB/dist-prebuilt-${profile}" ]; then
                    _missing_dist=$((_missing_dist + 1))
                fi
            done
            if [ "$_missing_dist" -gt 0 ]; then
                print_warning "有 ${_missing_dist} 个 WEB 形态缺少预构建 dist，跨架构 WEB 可能回退到完整 vite build"
            fi
        fi

        echo ""
    done

    # 清理 WEB 所有预构建 dist 临时目录
    rm -rf "${PROJECT_ROOT}/WEB/dist-prebuilt" "${PROJECT_ROOT}/WEB/dist-prebuilt-mini" \
           "${PROJECT_ROOT}/WEB/dist-prebuilt-standard" "${PROJECT_ROOT}/WEB/dist-prebuilt-full" 2>/dev/null || true

    # 恢复默认形态
    export EASYAIOT_DEPLOY_PROFILE=full
    apply_deploy_profile
    sync_deploy_profile_to_modules

    # ---- 创建多架构 Manifest ----
    if runtime_is_single_arch_build; then
        print_info "单架构构建模式：跳过多架构 manifest 创建（避免覆盖已有 manifest；需全架构构建时再更新 :${TAG} 标签）"
    elif [ ${#_MANIFEST_ARCH_REFS[@]} -gt 0 ]; then
        print_header "创建多架构 Manifest 列表"
        echo ""
        local manifest_ok=0 manifest_fail=0
        for mref in "${!_MANIFEST_ARCH_REFS[@]}"; do
            local -a arefs=()
            read -ra arefs <<< "${_MANIFEST_ARCH_REFS["$mref"]}"
            print_step "Manifest: ${mref}"
            for a in "${arefs[@]}"; do echo "  ← ${a}"; done
            if create_and_push_manifest "$mref" "${arefs[@]}"; then
                manifest_ok=$((manifest_ok + 1))
            else
                manifest_fail=$((manifest_fail + 1))
            fi
            echo ""
        done
        print_info "Manifest: 成功 ${manifest_ok}, 失败 ${manifest_fail}"
    fi

    # ---- 汇总 ----
    echo ""
    print_header "构建汇总"
    echo "  构建架构: ${total_archs} 个（${build_archs[*]}）"
    echo "  构建形态: ${total_profiles} 种"
    echo "  总计镜像: ${success_all} 个成功, ${failed_all} 个失败"
    echo ""
    if [ "$failed_all" -eq 0 ]; then
        print_success "所有运行时镜像构建成功！"
    else
        print_error "有 ${failed_all} 个镜像构建失败"
        return 1
    fi

    print_local_runtime_image_list build "${build_profiles[@]}"
    return 0
}

# ============================================================================
# 本地镜像列表（build / pull 共用）
# ============================================================================

_print_local_image_line() {
    local lref="$1"
    [ -z "$lref" ] && return 0
    if docker image inspect "$lref" >/dev/null 2>&1; then
        local size
        size=$(docker image inspect "$lref" --format '{{.Size}}' 2>/dev/null | awk '{printf "%.1f MB", $1/1024/1024}')
        echo "  ${lref}  (${size:-N/A})"
    fi
}

_append_unique_ref() {
    local ref="$1"
    local -n _refs=$2
    local existing
    [ -z "$ref" ] && return 0
    for existing in "${_refs[@]}"; do
        [ "$existing" = "$ref" ] && return 0
    done
    _refs+=("$ref")
}

print_local_runtime_image_list() {
    local mode="$1"
    shift

    echo ""
    print_info "本地运行时镜像列表 (${CURRENT_ARCH}):"

    for mapping in "${INDEPENDENT_MODULES[@]}"; do
        local rname="${mapping%%|*}"
        local tmp="${mapping#*|}"
        local lname="${tmp%%|*}"
        local -a lrefs=()
        _append_unique_ref "$(local_ref "$lname")" lrefs
        if is_profile_dependent "$rname"; then
            if [ "$mode" = build ]; then
                local p
                for p in "$@"; do
                    _append_unique_ref "$(local_ref "$lname" "$p")" lrefs
                done
            else
                _append_unique_ref "$(local_ref "$lname" "$1")" lrefs
            fi
        fi
        local lref
        for lref in "${lrefs[@]}"; do
            _print_local_image_line "$lref"
        done
    done

    if [ "$mode" = pull ]; then
        local pull_profile="$1" i tmp lname
        for i in "${!DEVICE_LOCAL_NAMES[@]}"; do
            runtime_device_image_needed_for_pull "$i" "$pull_profile" || continue
            _print_local_image_line "$(local_ref "${DEVICE_LOCAL_NAMES[$i]}")"
        done
        if [ "$pull_profile" = "full" ]; then
            for mapping in "${FULL_ONLY_MODULES[@]}"; do
                tmp="${mapping#*|}"; lname="${tmp%%|*}"
                _print_local_image_line "$(local_ref "$lname")"
            done
        fi
    else
        local lname tmp
        for lname in "${DEVICE_LOCAL_NAMES[@]}"; do
            _print_local_image_line "$(local_ref "$lname")"
        done
        for mapping in "${FULL_ONLY_MODULES[@]}"; do
            tmp="${mapping#*|}"; lname="${tmp%%|*}"
            _print_local_image_line "$(local_ref "$lname")"
        done
    fi
}

# ============================================================================
# 功能 2：拉取镜像
# ============================================================================

pull_and_tag_image() {
    local remote_ref="$1" local_ref="$2"
    print_info "docker pull ${remote_ref}"
    local pull_out pull_rc=0
    set +e
    pull_out=$(docker pull "$remote_ref" 2>&1)
    pull_rc=$?
    set -e
    printf '%s\n' "$pull_out"
    if [ "$pull_rc" -ne 0 ]; then
        print_warning "拉取失败: ${remote_ref}"
        if docker_error_is_dns_failure "$pull_out"; then
            _print_host_dns_fix_guide
            return 53
        fi
        return 1
    fi
    print_info "打本地标签: ${remote_ref} → ${local_ref}"
    docker tag "$remote_ref" "$local_ref" || { print_error "打标签失败"; return 1; }
    print_success "${local_ref} 已就绪"
    return 0
}

select_pull_profile() {
    if [ -n "${_EXPLICIT_PROFILE:-}" ]; then
        export EASYAIOT_DEPLOY_PROFILE="$(_resolve_deploy_profile_raw)"
        apply_deploy_profile
        save_deploy_profile
        sync_deploy_profile_to_modules
        print_info "部署形态: $(_deploy_profile_desc)（由 --profile 指定）"
        return 0
    fi
    if [ -n "${EASYAIOT_DEPLOY_PROFILE:-}" ]; then
        apply_deploy_profile
        sync_deploy_profile_to_modules
        print_info "部署形态: $(_deploy_profile_desc)（由环境变量指定）"
        return 0
    fi
    if [ ! -t 0 ]; then
        export EASYAIOT_DEPLOY_PROFILE=full
        apply_deploy_profile
        sync_deploy_profile_to_modules
        print_info "部署形态: $(_deploy_profile_desc)（默认）"
        return 0
    fi
    echo ""
    echo "请选择要拉取的部署形态镜像："
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
    apply_deploy_profile
    save_deploy_profile
    sync_deploy_profile_to_modules
    echo ""
    print_info "已选择: $(_deploy_profile_desc)"
    echo ""
}

pull_all_images() {
    print_header "从仓库拉取运行时镜像"
    runtime_log_registry_info
    echo "  当前架构: ${CURRENT_ARCH}"; echo "  Tag: ${TAG}"; echo ""
    check_docker

    # ★ 拉取前必须先修好宿主机 DNS（daemon.json dns 无法修复 dockerd 自身解析）
    # 典型故障: lookup docker.cnb.cool on [::1]:53: connection refused
    # Windows/Git Bash：不改 /etc/resolv.conf，走 Windows 本机 DNS / Docker Desktop 探测
    print_info "检查并修复宿主机 DNS（供 dockerd 解析镜像仓库）..."
    if ! ensure_host_dns_for_docker "docker.cnb.cool"; then
        if [ "${EASYAIOT_DESKTOP_OS:-}" = "windows" ] || [ "${EASYAIOT_FORCE_WINDOWS:-0}" = "1" ]; then
            print_error "DNS 不可用，已中止拉取。请按上方 Windows/Docker Desktop 指引排查后重试。"
        else
            print_error "宿主机 DNS 不可用，已中止拉取。请按上方指引修复 /etc/resolv.conf 后重试。"
        fi
        return 1
    fi

    select_pull_profile
    local pull_profile="${EASYAIOT_DEPLOY_PROFILE}"

    # ★ 拉取前校验本地镜像架构，删除与当前系统不一致的残留镜像（避免仅按「存在」跳过拉取）
    runtime_images_ensure_arch_consistency "$CURRENT_ARCH" "$pull_profile" "$TAG"

    local shared_ok=0 shared_fail=0 shared_skipped=0
    local device_pull_total
    device_pull_total=$(runtime_device_pull_count_for_profile "$pull_profile")
    # 非 local：供循环内检测到 DNS 故障后置位
    _EASYAIOT_DNS_ABORT=0

    # ---- 共享模块 ----
    print_header "阶段 1/2：拉取共享镜像（架构: ${CURRENT_ARCH}）"
    echo ""
    print_info "DEVICE 镜像：${pull_profile} 形态需拉取 ${device_pull_total}/${#DEVICE_REMOTE_NAMES[@]} 个（其余运行时不会启动，已跳过）"
    echo ""
    for mapping in "${INDEPENDENT_MODULES[@]}"; do
        [ "${_EASYAIOT_DNS_ABORT}" -eq 1 ] && break
        local rname="${mapping%%|*}"; local tmp="${mapping#*|}"; local lname="${tmp%%|*}"
        is_profile_dependent "$rname" && continue

        local rref; rref=$(remote_ref "$rname" "" "$CURRENT_ARCH")
        local lref; lref=$(local_ref "$lname")

        print_step "拉取: ${rref}"
        if runtime_pull_should_skip_image "$lref" "$CURRENT_ARCH"; then
            print_info "${lref} 已存在（${CURRENT_ARCH}），跳过"; shared_ok=$((shared_ok + 1)); continue
        fi
        local _prc=0
        pull_and_tag_image "$rref" "$lref" || _prc=$?
        if [ "$_prc" -eq 0 ]; then
            shared_ok=$((shared_ok + 1))
        elif [ "$_prc" -eq 53 ]; then
            _EASYAIOT_DNS_ABORT=1
            shared_fail=$((shared_fail + 1))
            break
        else
            shared_fail=$((shared_fail + 1))
        fi
    done
    # DEVICE 模块（按部署形态过滤，仅拉取 compose 会启动的服务）
    for i in "${!DEVICE_REMOTE_NAMES[@]}"; do
        [ "${_EASYAIOT_DNS_ABORT}" -eq 1 ] && break
        local rname="${DEVICE_REMOTE_NAMES[$i]}"; local lname="${DEVICE_LOCAL_NAMES[$i]}"
        if ! runtime_device_image_needed_for_pull "$i" "$pull_profile"; then
            print_info "跳过 ${rname} → ${lname}（${pull_profile} 形态不部署 ${DEVICE_COMPOSE_SERVICES[$i]}）"
            shared_skipped=$((shared_skipped + 1))
            continue
        fi
        local rref; rref=$(remote_ref "$rname" "" "$CURRENT_ARCH")
        local lref; lref=$(local_ref "$lname")

        print_step "拉取: ${rref}"
        if runtime_pull_should_skip_image "$lref" "$CURRENT_ARCH"; then
            print_info "${lref} 已存在（${CURRENT_ARCH}），跳过"; shared_ok=$((shared_ok + 1)); continue
        fi
        local _prc=0
        pull_and_tag_image "$rref" "$lref" || _prc=$?
        if [ "$_prc" -eq 0 ]; then
            shared_ok=$((shared_ok + 1))
        elif [ "$_prc" -eq 53 ]; then
            _EASYAIOT_DNS_ABORT=1
            shared_fail=$((shared_fail + 1))
            break
        else
            shared_fail=$((shared_fail + 1))
        fi
    done

    # APP 模块（仅 full 形态）
    if [ "$pull_profile" = "full" ] && [ "${_EASYAIOT_DNS_ABORT}" -eq 0 ]; then
        for mapping in "${FULL_ONLY_MODULES[@]}"; do
            [ "${_EASYAIOT_DNS_ABORT}" -eq 1 ] && break
            local rname="${mapping%%|*}"; local tmp="${mapping#*|}"; local lname="${tmp%%|*}"
            local rref; rref=$(remote_ref "$rname" "" "$CURRENT_ARCH")
            local lref; lref=$(local_ref "$lname")

            print_step "拉取: ${rref}"
            if runtime_pull_should_skip_image "$lref" "$CURRENT_ARCH"; then
                print_info "${lref} 已存在（${CURRENT_ARCH}），跳过"; shared_ok=$((shared_ok + 1)); continue
            fi
            local _prc=0
            pull_and_tag_image "$rref" "$lref" || _prc=$?
            if [ "$_prc" -eq 0 ]; then
                shared_ok=$((shared_ok + 1))
            elif [ "$_prc" -eq 53 ]; then
                _EASYAIOT_DNS_ABORT=1
                shared_fail=$((shared_fail + 1))
                break
            else
                shared_fail=$((shared_fail + 1))
            fi
        done
    fi

    if [ "${_EASYAIOT_DNS_ABORT}" -eq 1 ]; then
        if [ "${EASYAIOT_DESKTOP_OS:-}" = "windows" ] || [ "${EASYAIOT_FORCE_WINDOWS:-0}" = "1" ]; then
            print_error "因 DNS 故障已中止后续拉取。请检查 Windows 本机 DNS / Docker Desktop DNS 设置后重试。"
        else
            print_error "因宿主机 DNS 故障已中止后续拉取（避免无意义重试）。请先修复 /etc/resolv.conf。"
        fi
        return 1
    fi

    # 共享镜像总数 = 非形态相关的独立模块 + 当前形态需要的 DEVICE +（full 时）APP
    local shared_total=0
    for mapping in "${INDEPENDENT_MODULES[@]}"; do
        local rname="${mapping%%|*}"
        is_profile_dependent "$rname" || shared_total=$((shared_total + 1))
    done
    shared_total=$((shared_total + device_pull_total))
    if [ "$pull_profile" = "full" ]; then
        shared_total=$((shared_total + ${#FULL_ONLY_MODULES[@]}))
    fi
    echo ""
    print_info "共享镜像: 成功 ${shared_ok}/${shared_total}, 失败 ${shared_fail}/${shared_total}, 跳过 ${shared_skipped} 个 DEVICE"

    # ---- WEB 形态镜像 ----
    print_header "阶段 2/2：拉取 WEB 镜像（形态: $(_profile_label "$pull_profile"), 架构: ${CURRENT_ARCH}）"
    echo ""
    local web_ok=0 web_fail=0
    for mapping in "${INDEPENDENT_MODULES[@]}"; do
        local rname="${mapping%%|*}"; local tmp="${mapping#*|}"; local lname="${tmp%%|*}"
        is_profile_dependent "$rname" || continue

        local rref; rref=$(remote_ref "$rname" "$pull_profile" "$CURRENT_ARCH")
        local lref; lref=$(local_ref "$lname" "$pull_profile")

        print_step "拉取: ${rref}"
        if runtime_pull_should_skip_image "$lref" "$CURRENT_ARCH"; then
            print_info "${lref} 已存在（${CURRENT_ARCH}），跳过"
            web_ok=$((web_ok + 1))
            record_web_deploy_profile_built "${PROJECT_ROOT}"
            continue
        fi
        local _prc=0
        pull_and_tag_image "$rref" "$lref" || _prc=$?
        if [ "$_prc" -eq 0 ]; then
            web_ok=$((web_ok + 1))
            record_web_deploy_profile_built "${PROJECT_ROOT}"
        elif [ "$_prc" -eq 53 ]; then
            web_fail=$((web_fail + 1))
            print_error "因宿主机 DNS 故障已中止 WEB 镜像拉取。"
            return 1
        else
            web_fail=$((web_fail + 1))
        fi
    done

    # ---- 汇总 ----
    local total_all=$((shared_total + 1))
    local success_all=$((shared_ok + web_ok))
    local failed_all=$((shared_fail + web_fail))

    echo ""
    print_header "拉取汇总"
    echo "  当前架构: ${CURRENT_ARCH}"
    echo "  部署形态: $(_profile_label "$pull_profile") (${pull_profile})"
    echo "  共享镜像: ${shared_ok}/${shared_total}"
    echo "  WEB 镜像: ${web_ok}/1"
    echo "  总计:     ${success_all}/${total_all}"
    echo "  失败:     ${failed_all}"

    if [ "$failed_all" -eq 0 ]; then
        echo ""
        print_success "所有运行时镜像拉取成功！"
        echo ""

        # ★ 写入标记文件，让各平台 install 脚本自动跳过构建
        runtime_images_write_pulled_marker "$CURRENT_ARCH" "$pull_profile" "$TAG"
        print_info "已记录镜像拉取状态（install 将自动跳过构建）"

        print_info "现在可以直接使用对应平台的 install 脚本启动服务："
        echo "  bash .scripts/docker/install_linux.sh start"
        echo "  bash .scripts/docker/install_linux.sh install          (自动跳过构建)"
        if [ "$CURRENT_ARCH" = "arm64" ] || [ "$CURRENT_ARCH" = "arm32" ]; then
            echo "  bash .scripts/docker/install_linux_arm.sh start"
            echo "  bash .scripts/docker/install_linux_arm.sh install      (自动跳过构建)"
            echo "  bash .scripts/docker/install_linux_kylin.sh start      (麒麟系统)"
            echo "  bash .scripts/docker/install_linux_kylin.sh install    (自动跳过构建)"
        fi
        if [ "$(uname -s)" = "Darwin" ]; then
            echo "  bash .scripts/docker/install_mac.sh start"
            echo "  bash .scripts/docker/install_mac.sh install            (仅镜像部署)"
        fi
        case "$(uname -s)" in
            MINGW*|MSYS*|CYGWIN*)
                echo "  bash .scripts/docker/install_windows.sh start"
                echo "  bash .scripts/docker/install_windows.sh install        (仅镜像部署)"
                echo "  或 PowerShell: .scripts/docker/install_windows.ps1 install"
                ;;
        esac
    else
        echo ""
        print_warning "有 ${failed_all} 个镜像拉取失败"
        # 核心业务镜像已齐时视为软成功：避免因个别尚未发布镜像（如 aiot-transform）
        # 在 PANEL 无源码 runtime 上错误回退到本地 build
        local saved_profile="${EASYAIOT_DEPLOY_PROFILE:-}"
        export EASYAIOT_DEPLOY_PROFILE="$pull_profile"
        if runtime_images_pulled_ready 2>/dev/null || {
            # 标记可能仍是旧的 embedded：临时按 latest 校验核心镜像
            local -a _soft_refs=()
            runtime_images_collect_check_refs _soft_refs "$pull_profile" "latest"
            local _ok=1 _ref
            for _ref in "${_soft_refs[@]}"; do
                if ! runtime_local_image_arch_ready "$_ref" "$CURRENT_ARCH"; then
                    _ok=0
                    break
                fi
            done
            [ "$_ok" -eq 1 ]
        }; then
            runtime_images_write_pulled_marker "$CURRENT_ARCH" "$pull_profile" "latest"
            print_warning "核心预构建镜像已就绪，将跳过本地构建继续（缺失镜像需后续补拉）"
            [ -n "$saved_profile" ] && export EASYAIOT_DEPLOY_PROFILE="$saved_profile" || true
            print_local_runtime_image_list pull "$pull_profile"
            return 0
        fi
        [ -n "$saved_profile" ] && export EASYAIOT_DEPLOY_PROFILE="$saved_profile" || true
        runtime_print_install_local_build_help pull
        return 1
    fi

    print_local_runtime_image_list pull "$pull_profile"
    return 0
}

# ============================================================================
# 主入口
# ============================================================================
main() {
    case "$COMMAND" in
        build) build_all_modules ;;
        pull)  pull_all_images ;;
        *)     print_error "未知命令: $COMMAND"; exit 1 ;;
    esac
}

main "$@"
rc=$?

if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
    {
        echo ""
        echo "========================================="
        echo "脚本结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "退出码: $rc"
        echo "========================================="
    } >> "$LOG_FILE"
    print_info "日志文件已保存到: $LOG_FILE"
fi

exit $rc
