#!/usr/bin/env bash
# ============================================================================
# EasyAIoT 桌面端（macOS / Windows）镜像部署 — 共用逻辑
# 由 install_mac.sh / install_windows.sh source 后调用 desktop_main "$@"
#
# 约定：
#   - 仅拉取预构建运行时镜像 + 中间件镜像，禁止本地 docker build / build-runtime
#   - 业务模块委托各模块 install_linux.sh，并强制 EASYAIOT_SKIP_BUILD=1
#   - 中间件委托 install_middleware_desktop.sh
#   - 调用方需先设置：EASYAIOT_DESKTOP_OS=macos|windows、EASYAIOT_INSTALL_LABEL
# ============================================================================

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

: "${SCRIPT_DIR:?SCRIPT_DIR must be set by caller}"
: "${PROJECT_ROOT:?PROJECT_ROOT must be set by caller}"
: "${EASYAIOT_DESKTOP_OS:?EASYAIOT_DESKTOP_OS must be set by caller}"

EASYAIOT_INSTALL_LABEL="${EASYAIOT_INSTALL_LABEL:-EasyAIoT 桌面端镜像部署}"
export EASYAIOT_DESKTOP_IMAGE_ONLY=1
export EASYAIOT_SKIP_BUILD=1
export EASYAIOT_SKIP_IMAGE_PROMPT="${EASYAIOT_SKIP_IMAGE_PROMPT:-0}"
export EASYAIOT_RUNTIME_FORCE_PULL="${EASYAIOT_RUNTIME_FORCE_PULL:-0}"

LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/install_${EASYAIOT_DESKTOP_OS}_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================" >> "$LOG_FILE"
echo "${EASYAIOT_INSTALL_LABEL}" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "命令: $*" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"
# shellcheck source=runtime_image_common.sh
source "${SCRIPT_DIR}/runtime_image_common.sh"
# shellcheck source=diagnose_tools.sh
source "${SCRIPT_DIR}/diagnose_tools.sh"
# shellcheck source=docker_compose_bundled.sh
source "${SCRIPT_DIR}/docker_compose_bundled.sh"

# 可选：平台 Agent 同步（失败不阻断）
if [ -f "${PROJECT_ROOT}/.scripts/node/ensure_platform_agent_invoke.sh" ]; then
  # shellcheck source=../node/ensure_platform_agent_invoke.sh
  source "${PROJECT_ROOT}/.scripts/node/ensure_platform_agent_invoke.sh"
fi

MODULES=(
  ".scripts/docker"
  "DEVICE"
  "AI"
  "VIDEO"
  "WEB"
  "APP"
  "VISUALIZE"
  "TRANSFORM"
  "PANEL"
)

# bash 3.2 兼容：用函数代替关联数组
module_name() {
  case "$1" in
    ".scripts/docker") echo "基础服务" ;;
    "DEVICE") echo "Device服务" ;;
    "AI") echo "AI服务" ;;
    "VIDEO") echo "Video服务" ;;
    "WEB") echo "Web前端服务" ;;
    "APP") echo "App移动端H5" ;;
    "VISUALIZE") echo "可视化编辑器" ;;
    "TRANSFORM") echo "系统对接" ;;
    "PANEL") echo "运维控制台" ;;
    *) echo "$1" ;;
  esac
}

module_port() {
  case "$1" in
    ".scripts/docker") echo "8848" ;;
    "DEVICE") echo "48080" ;;
    "AI") echo "5000" ;;
    "VIDEO") echo "6000" ;;
    "WEB") echo "8888" ;;
    "APP") echo "9010" ;;
    "VISUALIZE") echo "8002" ;;
    "TRANSFORM") echo "48096" ;;
    "PANEL") echo "9200" ;;
    *) echo "" ;;
  esac
}

module_health() {
  case "$1" in
    ".scripts/docker") echo "/nacos/actuator/health" ;;
    "DEVICE") echo "/actuator/health" ;;
    "AI") echo "/actuator/health" ;;
    "VIDEO") echo "/actuator/health" ;;
    "WEB") echo "/health" ;;
    "APP") echo "/health" ;;
    "VISUALIZE") echo "/health" ;;
    "TRANSFORM") echo "/actuator/health" ;;
    "PANEL") echo "/health" ;;
    *) echo "" ;;
  esac
}

log_to_file() {
  local message="$1"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local clean_message
  clean_message=$(printf '%s' "$message" | sed -E 's/\x1B\[[0-9;]*[mGK]//g')
  echo "[$timestamp] $clean_message" >> "$LOG_FILE"
}

print_info() {
  local message="${BLUE}[INFO]${NC} $1"
  echo -e "$message"
  log_to_file "[INFO] $1"
}
print_success() {
  local message="${GREEN}[SUCCESS]${NC} $1"
  echo -e "$message"
  log_to_file "[SUCCESS] $1"
}
print_warning() {
  local message="${YELLOW}[WARNING]${NC} $1"
  echo -e "$message"
  log_to_file "[WARNING] $1"
}
print_error() {
  local message="${RED}[ERROR]${NC} $1"
  echo -e "$message"
  log_to_file "[ERROR] $1"
}
print_section() {
  local section="$1"
  echo ""
  echo -e "${YELLOW}========================================${NC}"
  echo -e "${YELLOW}  $section${NC}"
  echo -e "${YELLOW}========================================${NC}"
  echo ""
  log_to_file ""
  log_to_file "========================================="
  log_to_file "  $section"
  log_to_file "========================================="
  log_to_file ""
}

check_command() {
  command -v "$1" >/dev/null 2>&1
}

reject_local_build() {
  local os_label="$EASYAIOT_DESKTOP_OS"
  case "$EASYAIOT_DESKTOP_OS" in
    mac) os_label="macOS" ;;
    windows) os_label="Windows" ;;
  esac
  print_error "${os_label} 桌面端仅支持「镜像部署」，不支持本地编译/构建"
  print_info "请使用: pull（拉预构建镜像）→ install / update（启动或更新）"
  print_info "Linux 服务器若需本地构建，请使用: .scripts/docker/install_linux.sh"
  return 1
}

# ---------- 前置依赖检测（缺什么提示装什么，不满足则中止） ----------
# 返回 0=全部通过；1=有缺失（已打印清单）。默认失败即 exit（由 require_desktop_prerequisites 调用）。
check_desktop_prerequisites() {
  local quiet_ok="${1:-0}"  # 1=全部通过时少打印
  local -a missing=()
  local -a howto=()
  local -a warnings=()
  local os_label="桌面端"
  case "$EASYAIOT_DESKTOP_OS" in
    mac) os_label="macOS" ;;
    windows) os_label="Windows" ;;
  esac

  print_section "前置环境检测（${os_label}）"

  # 1) bash 版本
  if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    missing+=("Bash 4+（当前: ${BASH_VERSION:-unknown}）")
    if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
      howto+=("安装 Homebrew bash: brew install bash")
      howto+=("然后重新打开终端，或确保 /opt/homebrew/bin/bash 在 PATH 中")
    else
      howto+=("安装/升级 Git for Windows: https://git-scm.com/download/win")
      howto+=("或在 WSL 中运行本脚本")
    fi
  else
    print_success "Bash: ${BASH_VERSION}"
  fi

  # 2) curl（健康检查 / 部分脚本）
  if check_command curl; then
    print_success "curl: 已安装"
  else
    missing+=("curl")
    if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
      howto+=("安装 curl: xcode-select --install  或  brew install curl")
    else
      howto+=("Git Bash 一般自带 curl；请重装 Git for Windows，或在 WSL 中: sudo apt install -y curl")
    fi
  fi

  # 3) Docker CLI（Windows：常见安装路径未进 PATH 时自动补齐当前会话）
  local docker_cli_ok=0
  if ! check_command docker && [ "$EASYAIOT_DESKTOP_OS" = "windows" ]; then
    local _ddir
    for _ddir in \
      "/c/Program Files/Docker/Docker/resources/bin" \
      "/c/Program Files (x86)/Docker/Docker/resources/bin" \
      "$HOME/AppData/Local/Docker/resources/bin"
    do
      if [ -x "${_ddir}/docker.exe" ] || [ -x "${_ddir}/docker" ]; then
        export PATH="${_ddir}:${PATH}"
        print_info "已将 Docker CLI 加入当前会话 PATH: ${_ddir}"
        break
      fi
    done
  fi
  if check_command docker; then
    print_success "Docker CLI: $(docker --version 2>/dev/null | head -n1 || echo 已安装)"
    docker_cli_ok=1
  else
    missing+=("Docker Desktop（未找到 docker 命令）")
    if [ "$EASYAIOT_DESKTOP_OS" = "windows" ]; then
      howto+=("推荐 PowerShell 一键引导:  .\\.scripts\\docker\\install_windows.ps1 bootstrap")
      howto+=("或管理员执行:  wsl --install")
      howto+=("然后:  winget install -e --id Docker.DockerDesktop")
      howto+=("手动下载: https://www.docker.com/products/docker-desktop （建议勾选 WSL2 后端）")
      howto+=("装完后重启终端（必要时重启电脑）再执行本脚本")
    else
      howto+=("下载安装 Docker Desktop: https://www.docker.com/products/docker-desktop")
    fi
  fi

  # 4) Docker daemon（可尝试拉起 Desktop；未安装则快速失败，不空等）
  local docker_daemon_ok=0
  if [ "$docker_cli_ok" -eq 1 ]; then
    if docker info >/dev/null 2>&1; then
      print_success "Docker Desktop: 引擎已运行"
      docker_daemon_ok=1
    else
      local desktop_launchable=0
      if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
        if [ -d "/Applications/Docker.app" ] || [ -d "${HOME}/Applications/Docker.app" ]; then
          desktop_launchable=1
          print_warning "Docker 引擎未就绪，尝试启动 Docker Desktop..."
          open -a Docker >/dev/null 2>&1 || true
        fi
      elif check_command powershell.exe; then
        if powershell.exe -NoProfile -Command "
          \$dd = @(
            \"\$env:ProgramFiles\Docker\Docker\Docker Desktop.exe\",
            \"\${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe\",
            \"\$env:LOCALAPPDATA\Docker\Docker Desktop.exe\"
          ) | Where-Object { Test-Path \$_ } | Select-Object -First 1
          if (-not \$dd) { exit 2 }
          Start-Process \$dd
          exit 0
        " >/dev/null 2>&1; then
          desktop_launchable=1
          print_warning "Docker 引擎未就绪，尝试启动 Docker Desktop..."
        fi
      fi

      if [ "$desktop_launchable" -eq 1 ]; then
        local i
        for i in $(seq 1 45); do
          sleep 2
          if docker info >/dev/null 2>&1; then
            print_success "Docker Desktop: 引擎已就绪"
            docker_daemon_ok=1
            break
          fi
          if [ $((i % 5)) -eq 0 ]; then
            print_info "等待 Docker Desktop 启动... (${i}/45)"
          fi
        done
      fi

      if [ "$docker_daemon_ok" -eq 0 ]; then
        if [ "$desktop_launchable" -eq 0 ]; then
          missing+=("Docker Desktop 未安装或引擎未运行（docker info 失败）")
          if [ "$EASYAIOT_DESKTOP_OS" = "windows" ]; then
            howto+=("推荐: .\\.scripts\\docker\\install_windows.ps1 bootstrap")
          fi
          howto+=("下载安装并启动 Docker Desktop: https://www.docker.com/products/docker-desktop")
        else
          missing+=("Docker Desktop 引擎未运行（docker info 失败）")
          howto+=("请手动打开 Docker Desktop，等待状态栏显示 Running 后重试")
          howto+=("安装地址: https://www.docker.com/products/docker-desktop")
        fi
        if [ "$EASYAIOT_DESKTOP_OS" = "windows" ] && ! { [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; }; then
          if ! command -v wsl.exe >/dev/null 2>&1 || ! wsl.exe --status >/dev/null 2>&1; then
            howto+=("本机 WSL2 未就绪，Docker Desktop 后端可能无法启动，请先: wsl --install（完成后重启）")
          fi
        fi
      fi
    fi
  fi

  # 5) Docker Compose
  if [ "$docker_daemon_ok" -eq 1 ] || [ "$docker_cli_ok" -eq 1 ]; then
    if docker compose version >/dev/null 2>&1; then
      print_success "Docker Compose: $(docker compose version --short 2>/dev/null || echo v2)"
      COMPOSE_CMD="docker compose"
    elif check_command docker-compose; then
      print_success "Docker Compose: $(docker-compose --version 2>/dev/null || echo v1)"
      COMPOSE_CMD="docker-compose"
    else
      missing+=("Docker Compose（docker compose / docker-compose）")
      howto+=("请升级 Docker Desktop 到较新版本（自带 Compose V2）")
    fi
  fi

  # 6) 平台特定：Windows 需要 Git Bash（本脚本已在 bash 中，但提示友好）
  if [ "$EASYAIOT_DESKTOP_OS" = "windows" ]; then
    case "$(uname -s 2>/dev/null)" in
      MINGW*|MSYS*|CYGWIN*)
        print_success "Shell: Git Bash / MSYS ($(uname -s))"
        ;;
      Linux)
        if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; then
          print_success "Shell: WSL (${WSL_DISTRO_NAME:-Linux})"
        fi
        ;;
    esac
  fi

  # 7) 软性告警：内存（不阻断）
  local mem_gb=""
  if [ "$EASYAIOT_DESKTOP_OS" = "mac" ] && check_command sysctl; then
    local mem_bytes
    mem_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
    if [ "${mem_bytes:-0}" -gt 0 ] 2>/dev/null; then
      mem_gb=$((mem_bytes / 1024 / 1024 / 1024))
    fi
  elif check_command free; then
    mem_gb=$(free -g 2>/dev/null | awk '/Mem:/{print $2}')
  fi
  if [ -n "$mem_gb" ] && [ "$mem_gb" -gt 0 ] 2>/dev/null; then
    if [ "$mem_gb" -lt 8 ]; then
      warnings+=("物理内存约 ${mem_gb}GB，建议 ≥16GB（mini 规格至少 ≥8GB）")
    else
      print_info "内存: 约 ${mem_gb}GB"
    fi
  fi

  # 汇总
  if [ ${#warnings[@]} -gt 0 ]; then
    echo ""
    print_warning "建议关注："
    local w
    for w in "${warnings[@]}"; do
      echo "  - $w"
    done
  fi

  if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    print_error "前置环境不满足，已中止安装/部署"
    echo ""
    echo "缺少以下组件："
    local m
    for m in "${missing[@]}"; do
      echo "  ✗ $m"
    done
    echo ""
    echo "请按下列说明安装后重试："
    local h n=1
    for h in "${howto[@]}"; do
      echo "  ${n}. $h"
      n=$((n + 1))
    done
    echo ""
    echo "装好后可先自检："
    echo "  bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh check"
    echo ""
    return 1
  fi

  if [ "$quiet_ok" != "1" ]; then
    print_success "前置环境检测通过"
  fi
  return 0
}

require_desktop_prerequisites() {
  if [ "${EASYAIOT_DESKTOP_PREREQ_OK:-0}" = "1" ]; then
    return 0
  fi
  if ! check_desktop_prerequisites 0; then
    exit 1
  fi
  export EASYAIOT_DESKTOP_PREREQ_OK=1
}

# ---------- Docker Desktop（兼容旧调用；内部走统一检测） ----------
ensure_docker_desktop() {
  require_desktop_prerequisites
}

ensure_compose_desktop() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    return 0
  fi
  if check_command docker-compose; then
    COMPOSE_CMD="docker-compose"
    return 0
  fi
  require_desktop_prerequisites
}

# ---------- 宿主机 IP（GB28181 / ZLM 等） ----------
detect_host_ip_desktop() {
  if [ -n "${HOST_IP:-}" ]; then
    print_info "使用已设置的宿主机 IP: $HOST_IP"
    return 0
  fi

  local host_ip=""

  if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
    host_ip=$(ipconfig getifaddr en0 2>/dev/null || true)
    [ -z "$host_ip" ] && host_ip=$(ipconfig getifaddr en1 2>/dev/null || true)
    if [ -z "$host_ip" ] && check_command route; then
      host_ip=$(route -n get default 2>/dev/null | awk '/interface:/{iface=$2} END{print iface}' | xargs -I{} ipconfig getifaddr {} 2>/dev/null || true)
    fi
  else
    # Windows Git Bash / MSYS
    if check_command ipconfig; then
      host_ip=$(ipconfig 2>/dev/null | tr -d '\r' | awk '/IPv4/{print $NF; exit}')
    fi
    if [ -z "$host_ip" ] && check_command powershell.exe; then
      host_ip=$(powershell.exe -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { \$_.IPAddress -notlike '127.*' -and \$_.IPAddress -notlike '169.254.*' } | Select-Object -First 1 -ExpandProperty IPAddress)" 2>/dev/null | tr -d '\r' | head -n1)
    fi
  fi

  if [ -z "$host_ip" ]; then
    print_warning "无法自动检测宿主机 IP；可手动: export HOST_IP=<局域网IP>"
    print_warning "部分媒体能力（GB28181 等）可能需要正确的 HOST_IP"
    return 0
  fi

  export HOST_IP="$host_ip"
  print_info "检测到宿主机 IP: $HOST_IP"
  return 0
}

create_network() {
  if ! docker network inspect easyaiot-network >/dev/null 2>&1; then
    print_info "创建 Docker 网络: easyaiot-network"
    docker network create easyaiot-network >/dev/null
    print_success "网络已创建"
  else
    print_info "Docker 网络 easyaiot-network 已存在"
  fi
}

prepare_desktop_environment() {
  # 统一前置检测：缺什么提示装什么，不满足则中止
  require_desktop_prerequisites
  detect_host_ip_desktop
  create_network
  # 桌面端跳过 Linux 专属：daemon.json 镜像源、RTP sysctl、/dev/null 深度诊断
  print_info "镜像加速请在 Docker Desktop → Settings → Docker Engine 中配置 registry-mirrors"
}

fix_line_endings() {
  local script_file="$1"
  [ -f "$script_file" ] || return 0
  if grep -q $'\r' "$script_file" 2>/dev/null; then
    if sed --version >/dev/null 2>&1; then
      sed -i 's/\r$//' "$script_file" 2>/dev/null || true
    else
      sed -i '' 's/\r$//' "$script_file" 2>/dev/null || true
    fi
  fi
  [ -x "$script_file" ] || chmod u+x "$script_file" 2>/dev/null || true
}

module_install_script() {
  case "$1" in
    ".scripts/docker") echo "install_middleware_desktop.sh" ;;
    "PANEL")
      if [ -f "${PROJECT_ROOT}/PANEL/install_linux.sh" ]; then
        echo "install_linux.sh"
      else
        echo "install.sh"
      fi
      ;;
    *) echo "install_linux.sh" ;;
  esac
}

execute_module_command() {
  local module=$1
  local command=$2
  local name
  name=$(module_name "$module")
  local install_file
  install_file=$(module_install_script "$module")

  if [ ! -d "$PROJECT_ROOT/$module" ]; then
    case "$module" in
      TRANSFORM|PANEL|APP|VISUALIZE)
        print_info "未检测到 ${module} 目录，跳过"
        return 0
        ;;
    esac
    print_warning "模块 $module 不存在，跳过"
    return 1
  fi

  cd "$PROJECT_ROOT/$module"

  if [ ! -f "$install_file" ]; then
    print_info "${name} 无安装脚本 ${install_file}，跳过"
    return 0
  fi

  fix_line_endings "$install_file"
  print_info "执行 ${name}: ${command}"

  ensure_deploy_profile
  export EASYAIOT_DEPLOY_PROFILE
  export EASYAIOT_SKIP_PROFILE_PROMPT
  export EASYAIOT_SKIP_IMAGE_PROMPT=1
  export EASYAIOT_SKIP_BUILD=1
  export HOST_IP

  local defer_agent_sync=0
  case "$module" in
    DEVICE|AI|VIDEO|WEB|APP|VISUALIZE|TRANSFORM) defer_agent_sync=1 ;;
  esac
  if [ "$defer_agent_sync" -eq 1 ]; then
    export EASYAIOT_DEFER_PLATFORM_AGENT_SYNC=1
  fi

  local rc
  bash "$install_file" "$command" 2>&1 | tee -a "$LOG_FILE"
  rc=${PIPESTATUS[0]}

  if [ "$defer_agent_sync" -eq 1 ]; then
    unset EASYAIOT_DEFER_PLATFORM_AGENT_SYNC
  fi

  if [ "$rc" -eq 0 ]; then
    print_success "${name}: ${command} 执行成功"
    return 0
  fi
  print_error "${name}: ${command} 执行失败 (exit $rc)"
  return 1
}

_count_installable_modules() {
  local count=0 module _inst
  for module in "${MODULES[@]}"; do
    module_enabled_for_deploy_profile "$module" || continue
    _inst="${PROJECT_ROOT}/${module}/$(module_install_script "$module")"
    [ -f "$_inst" ] || continue
    count=$((count + 1))
  done
  echo "$count"
}

wait_for_container_ready() {
  local name=$1 max_attempts=$2 interval=$3
  shift 3
  local attempt=0
  print_info "等待 ${name} 服务就绪..."
  while [ $attempt -lt $max_attempts ]; do
    if "$@" >/dev/null 2>&1; then
      print_success "${name} 服务已就绪"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep "$interval"
  done
  print_warning "${name} 未在预期时间内就绪，继续执行..."
  return 1
}

wait_for_base_services() {
  if docker ps --filter "name=postgres-server" --format "{{.Names}}" 2>/dev/null | grep -q "postgres-server"; then
    wait_for_container_ready "PostgreSQL" 60 2 \
      docker exec postgres-server pg_isready -U postgres
  fi
  if docker ps --filter "name=nacos-server" --format "{{.Names}}" 2>/dev/null | grep -q "nacos-server"; then
    wait_for_container_ready "Nacos" 60 2 \
      curl -s --connect-timeout 2 "http://localhost:8848/nacos/actuator/health"
  fi
  if docker ps --filter "name=redis-server" --format "{{.Names}}" 2>/dev/null | grep -q "redis-server"; then
    wait_for_container_ready "Redis" 30 1 \
      docker exec redis-server redis-cli ping
  fi
}

wait_for_device_gateway() {
  wait_for_container_ready "iot-gateway" 90 2 \
    curl -s --connect-timeout 2 "http://localhost:48080/actuator/health"
}

collect_biz_modules() {
  ensure_deploy_profile
  BIZ_MODULES=()
  local module
  for module in "${MODULES[@]}"; do
    [ "$module" = ".scripts/docker" ] && continue
    module_enabled_for_deploy_profile "$module" || continue
    BIZ_MODULES+=("$module")
  done
}

# ---------- 镜像拉取（强制，无本地构建回退） ----------
desktop_pull_runtime_images() {
  print_section "拉取预构建运行时镜像"
  prepare_desktop_environment
  ensure_deploy_profile
  export EASYAIOT_SKIP_IMAGE_PROMPT=1
  export EASYAIOT_RUNTIME_TAG="${EASYAIOT_RUNTIME_TAG:-latest}"
  runtime_images_prepare_pull_interactive
  runtime_images_export_for_invoke
  if runtime_images_invoke pull; then
    export EASYAIOT_SKIP_BUILD=1
    print_success "预构建镜像拉取成功"
    return 0
  fi
  if runtime_images_pulled_ready; then
    export EASYAIOT_SKIP_BUILD=1
    print_warning "部分镜像拉取失败，但核心预构建镜像已就绪，将继续"
    return 0
  fi
  print_error "预构建镜像拉取失败，且桌面端禁止本地构建"
  print_info "请检查网络 / Docker Desktop 镜像加速 / runtime_registry.conf 后重试: pull"
  return 1
}

desktop_acquire_images() {
  # 已就绪且非强制刷新
  if [ "${EASYAIOT_RUNTIME_FORCE_PULL:-0}" != "1" ] && runtime_images_pulled_ready; then
    print_info "本地预构建镜像已就绪，跳过拉取（需要刷新请: pull 或 EASYAIOT_RUNTIME_FORCE_PULL=1）"
    export EASYAIOT_SKIP_BUILD=1
    export EASYAIOT_SKIP_IMAGE_PROMPT=1
    return 0
  fi
  desktop_pull_runtime_images
}

# ---------- 安装 / 启停 ----------
desktop_install() {
  print_section "开始安装（仅镜像部署）"
  # 先做前置检测：缺什么提示装什么，不满足则中止（避免拉镜像中途才失败）
  prepare_desktop_environment
  select_deploy_profile_for_install
  export EASYAIOT_INSTALL_SCRIPT=".scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh"

  if ! desktop_acquire_images; then
    return 1
  fi

  local success_count=0
  local total_count
  total_count=$(_count_installable_modules)
  local -a failed_modules=()
  local -a succeeded_modules=()
  local module name

  for module in "${MODULES[@]}"; do
    if ! module_enabled_for_deploy_profile "$module"; then
      print_info "跳过 $(module_name "$module")（形态 ${EASYAIOT_DEPLOY_PROFILE} 不包含）"
      continue
    fi
    local _inst="${PROJECT_ROOT}/${module}/$(module_install_script "$module")"
    if [ ! -f "$_inst" ]; then
      print_info "$(module_name "$module") 无需安装（无安装脚本），跳过"
      continue
    fi

    print_section "安装 $(module_name "$module")"
    if [ "$module" != ".scripts/docker" ]; then
      print_info "使用预构建镜像启动（跳过 docker build）"
    fi

    if execute_module_command "$module" "install"; then
      success_count=$((success_count + 1))
      succeeded_modules+=("$(module_name "$module")")
      if [ "$module" = ".scripts/docker" ]; then
        wait_for_base_services
      fi
      if [ "$module" = "DEVICE" ]; then
        wait_for_device_gateway || print_warning "iot-gateway 未就绪，WEB /dev-api 可能暂时 503"
      fi
    else
      failed_modules+=("$(module_name "$module")")
    fi
    echo ""
  done

  print_section "安装完成"
  echo "成功安装: $success_count / $total_count 个模块"
  if [ ${#succeeded_modules[@]} -gt 0 ]; then
    echo "  已成功: ${succeeded_modules[*]}"
  fi
  if [ ${#failed_modules[@]} -gt 0 ]; then
    echo "  已失败: ${failed_modules[*]}"
    print_warning "部分模块安装失败，请检查日志: ${LOG_FILE}"
    return 1
  fi

  print_success "所有模块安装成功！"
  if declare -F ensure_platform_agent_if_needed >/dev/null 2>&1; then
    ENSURE_PLATFORM_AGENT_INFO=print_info \
    ENSURE_PLATFORM_AGENT_OK=print_success \
    ENSURE_PLATFORM_AGENT_WARN=print_warning \
    ensure_platform_agent_if_needed || true
  fi
  print_access_urls
  return 0
}

desktop_start() {
  print_section "启动所有服务"
  ensure_deploy_profile
  prepare_desktop_environment

  print_section "启动基础服务"
  if ! execute_module_command ".scripts/docker" "start"; then
    print_error "基础服务启动失败"
    return 1
  fi
  wait_for_base_services
  echo ""

  collect_biz_modules
  local module
  if [ "${PARALLEL_MODULES:-true}" = "true" ] && [ ${#BIZ_MODULES[@]} -gt 0 ]; then
    print_info "并行启动业务模块: ${BIZ_MODULES[*]}"
    local pids=() mods=() mlog rc fail=0 i
    for module in "${BIZ_MODULES[@]}"; do
      mlog="${LOG_DIR}/start_$(echo "$module" | tr '/' '_')_$$.log"
      : > "$mlog"
      ( LOG_FILE="$mlog"; execute_module_command "$module" "start" >/dev/null 2>&1 ) &
      pids+=($!)
      mods+=("$module")
    done
    for i in "${!pids[@]}"; do
      if wait "${pids[$i]}"; then
        print_success "$(module_name "${mods[$i]}"): start 完成"
      else
        fail=$((fail + 1))
        print_error "$(module_name "${mods[$i]}"): start 失败"
      fi
    done
    [ "$fail" -eq 0 ] || print_warning "有 ${fail} 个模块启动失败"
  else
    for module in "${BIZ_MODULES[@]}"; do
      execute_module_command "$module" "start" || print_warning "$(module_name "$module") 启动失败"
      echo ""
    done
  fi

  print_success "启动流程完成"
  print_access_urls
}

desktop_stop() {
  print_section "停止所有服务"
  collect_biz_modules
  local idx module
  for ((idx=${#BIZ_MODULES[@]}-1; idx>=0; idx--)); do
    module="${BIZ_MODULES[$idx]}"
    execute_module_command "$module" "stop" || true
  done
  execute_module_command ".scripts/docker" "stop" || true
  print_success "已停止"
}

desktop_restart() {
  desktop_stop
  desktop_start
}

desktop_status() {
  print_section "服务状态"
  ensure_deploy_profile
  local module
  for module in "${MODULES[@]}"; do
    module_enabled_for_deploy_profile "$module" || continue
    print_section "$(module_name "$module") 状态"
    execute_module_command "$module" "status" || true
  done
}

desktop_logs() {
  local target="${1:-}"
  if [ -n "$target" ]; then
    local module
    for module in "${MODULES[@]}"; do
      if [ "$module" = "$target" ] || [ "$(module_name "$module")" = "$target" ]; then
        execute_module_command "$module" "logs"
        return
      fi
    done
    print_error "未知模块: $target"
    return 1
  fi
  local module
  for module in "${MODULES[@]}"; do
    module_enabled_for_deploy_profile "$module" || continue
    print_section "$(module_name "$module") 日志"
    execute_module_command "$module" "logs" || true
  done
}

desktop_update() {
  print_section "更新（拉取最新预构建镜像并重启）"
  select_deploy_profile_for_install
  export EASYAIOT_RUNTIME_FORCE_PULL=1
  if ! desktop_pull_runtime_images; then
    return 1
  fi

  execute_module_command ".scripts/docker" "update" || print_warning "基础服务更新失败"
  wait_for_base_services

  collect_biz_modules
  local module
  for module in "${BIZ_MODULES[@]}"; do
    print_info "更新 $(module_name "$module")（跳过本地构建）"
    execute_module_command "$module" "update" || print_warning "$(module_name "$module") 更新失败"
  done
  print_success "更新完成"
  print_access_urls
}

desktop_clean() {
  print_section "清理容器与数据"
  print_warning "将停止并清理各模块容器（可能删除数据卷，取决于子脚本）"
  read -r -p "确认继续？(y/N) " resp
  case "${resp:-}" in
    y|Y|yes|YES) ;;
    *) print_info "已取消"; return 0 ;;
  esac
  collect_biz_modules
  local idx module
  for ((idx=${#BIZ_MODULES[@]}-1; idx>=0; idx--)); do
    module="${BIZ_MODULES[$idx]}"
    execute_module_command "$module" "clean" || true
  done
  execute_module_command ".scripts/docker" "clean" || true
  print_success "清理完成"
}

desktop_verify() {
  print_section "验证服务健康"
  ensure_deploy_profile
  local module port health ok_count=0 total=0 failed=""
  for module in "${MODULES[@]}"; do
    module_enabled_for_deploy_profile "$module" || continue
    total=$((total + 1))
    port=$(module_port "$module")
    health=$(module_health "$module")
    print_info "验证 $(module_name "$module") (端口: $port)..."
    if [ -n "$health" ] && curl -s --connect-timeout 2 "http://localhost:${port}${health}" >/dev/null 2>&1; then
      print_success "$(module_name "$module") 运行正常"
      ok_count=$((ok_count + 1))
    elif curl -s --connect-timeout 1 "http://localhost:${port}" >/dev/null 2>&1; then
      print_success "$(module_name "$module") 端口可达"
      ok_count=$((ok_count + 1))
    else
      print_error "$(module_name "$module") 未就绪"
      failed="${failed} $(module_name "$module")"
    fi
  done
  echo ""
  echo "通过: ${ok_count}/${total}"
  if [ "$ok_count" -eq "$total" ]; then
    print_success "全部验证通过"
    print_access_urls
    return 0
  fi
  print_warning "未通过:${failed}"
  return 1
}

print_access_urls() {
  ensure_deploy_profile
  echo ""
  echo -e "${GREEN}访问地址：${NC}"
  echo -e "  Web 控制台:              http://localhost:8888"
  echo -e "  API 网关:                http://localhost:48080"
  echo -e "  Nacos:                   http://localhost:8848/nacos"
  echo -e "  MinIO:                   http://localhost:9001"
  if module_enabled_for_deploy_profile APP; then
    echo -e "  App H5:                  http://localhost:9010"
  fi
  if module_enabled_for_deploy_profile VISUALIZE; then
    echo -e "  可视化编辑器:            http://localhost:8002"
  fi
  if module_enabled_for_deploy_profile TRANSFORM; then
    echo -e "  系统对接 (TRANSFORM):    http://localhost:48096"
  fi
  if module_enabled_for_deploy_profile PANEL; then
    echo -e "  运维控制台 (PANEL):      http://localhost:9200"
  fi
  echo ""
}

desktop_check() {
  # check 本身就是前置检测入口（失败已打印清单并 exit）
  require_desktop_prerequisites
  print_section "主机信息"
  print_info "操作系统: $(uname -s) $(uname -r)"
  print_info "架构: $(uname -m)"
  print_info "桌面平台: ${EASYAIOT_DESKTOP_OS}"
  print_info "用户: $(whoami)"
  print_info "Bash: ${BASH_VERSION}"
  print_info "Compose: ${COMPOSE_CMD:-未设置}"
  print_section "检查完成"
}

show_help() {
  cat <<EOF
${EASYAIOT_INSTALL_LABEL}

使用方法:
  ./install_${EASYAIOT_DESKTOP_OS}.sh                 - 打开交互式引导
  ./install_${EASYAIOT_DESKTOP_OS}.sh [命令]

本脚本仅支持「镜像部署」（拉取预构建镜像后启动），不支持本地编译。

可用命令:
  install     - 拉取镜像（若需要）并安装启动全部服务
  start       - 启动所有服务
  stop        - 停止所有服务
  restart     - 重启所有服务
  status      - 查看状态
  logs [模块] - 查看日志
  pull        - 从远程仓库拉取预构建运行时镜像
  update      - 拉取最新镜像并重启
  verify      - 健康检查
  clean       - 清理容器（慎用）
  check       - 前置环境自检（缺什么提示装什么；不满足则退出）
  profile     - 显示当前部署形态
  menu        - 交互引导
  help        - 显示帮助

说明:
  install / pull / update / start 等会在真正部署前自动做前置检测；
  缺少 Docker Desktop、Compose、Bash 4+、curl 等会打印安装指引并中止。

部署形态（EASYAIOT_DEPLOY_PROFILE）:
  mini(1) / standard(2) / full(3，默认)

不支持的命令（请改用 Linux 服务器脚本）:
  build / build-runtime / clean-build-runtime

示例:
  bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh check
  bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh install
  bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh pull
  EASYAIOT_DEPLOY_PROFILE=mini bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh install
EOF
}

# ---------- 交互菜单（桌面精简版，无 build-runtime） ----------
_print_desktop_deploy_header() {
  echo ""
  echo -e "${YELLOW}========================================${NC}"
  echo -e "${YELLOW}  【部署】镜像部署与运维（${EASYAIOT_DESKTOP_OS}）${NC}"
  echo -e "${YELLOW}========================================${NC}"
  echo ""
  echo "  1) 首次安装并启动（自动拉取预构建镜像）"
  echo "  2) 启动所有服务"
  echo "  3) 停止所有服务"
  echo "  4) 重启所有服务"
  echo "  5) 查看运行状态"
  echo "  6) 查看服务日志"
  echo "  7) 验证服务健康"
  echo "  8) 拉取最新镜像并更新"
  echo "  9) 仅拉取预构建镜像"
  echo "  10) 前置环境自检（缺什么提示装什么）"
  echo "  11) 查看部署形态"
  echo "  12) 完整命令行帮助"
  echo ""
  echo "  0) 返回上级菜单"
  echo ""
}

run_desktop_deploy_menu() {
  local choice=""
  while true; do
    _print_desktop_deploy_header
    read -r -p "请输入部署选项 [0-12]: " choice || choice=""
    [ -z "$choice" ] && continue
    case "$choice" in
      1) easyaiot_run_command install ;;
      2) easyaiot_run_command start ;;
      3) easyaiot_run_command stop ;;
      4) easyaiot_run_command restart ;;
      5) easyaiot_run_command status ;;
      6) easyaiot_run_command logs ;;
      7) easyaiot_run_command verify ;;
      8) easyaiot_run_command update ;;
      9) easyaiot_run_command pull ;;
      10) easyaiot_run_command check ;;
      11) easyaiot_run_command profile ;;
      12) show_help ;;
      0|q|Q) return 0 ;;
      *) print_error "无效选项: $choice"; sleep 1 ;;
    esac
  done
}

run_desktop_root_menu() {
  local choice=""
  while true; do
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  ${EASYAIOT_INSTALL_LABEL}${NC}"
    echo -e "${YELLOW}  仅镜像部署 · 交互引导${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo "  1) 部署 — 安装、启停、更新、状态、日志"
    echo "  2) 分析 — 日志、磁盘、健康检查"
    echo ""
    echo "  0) 退出"
    echo ""
    read -r -p "请选择 [0-2]: " choice || choice=""
    case "$choice" in
      1) run_desktop_deploy_menu ;;
      2) run_analyze_interactive_menu ;;
      0|q|Q) return 0 ;;
      *) print_error "无效选项"; sleep 1 ;;
    esac
  done
}

# diagnose_tools 回调
easyaiot_run_command() {
  EASYAIOT_FROM_MENU=1 main "$@"
}

main() {
  local cmd="${1:-}"

  if [ -z "$cmd" ] || [ "$cmd" = "menu" ] || [ "$cmd" = "interactive" ]; then
    if [ "${EASYAIOT_FROM_MENU:-}" != "1" ]; then
      run_desktop_root_menu
      return 0
    fi
    cmd="help"
  fi

  case "$cmd" in
    install) desktop_install ;;
    start) desktop_start ;;
    stop) desktop_stop ;;
    restart) desktop_restart ;;
    status) desktop_status ;;
    logs) desktop_logs "$2" ;;
    pull|images-pull) desktop_pull_runtime_images ;;
    update) desktop_update ;;
    verify) desktop_verify ;;
    clean) desktop_clean ;;
    check) desktop_check ;;
    profile)
      ensure_deploy_profile
      print_deploy_profile_summary
      ;;
    diagnose|diagnose-tools) run_analyze_interactive_menu ;;
    analyze-logs|analyze-log|merge-logs) invoke_analyze_merge_logs "${@:2}" ;;
    analyze-disk|analyze-disk-usage|disk-usage) invoke_analyze_disk_usage "${@:2}" ;;
    build|build-runtime|images-build|clean-build-runtime|clean-runtime)
      reject_local_build
      exit 1
      ;;
    help|--help|-h) show_help ;;
    *)
      print_error "未知命令: $cmd"
      show_help
      exit 1
      ;;
  esac
}

desktop_main() {
  main "$@"
  if [ -n "${LOG_FILE:-}" ] && [ -f "$LOG_FILE" ]; then
    echo "" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo "脚本结束时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo ""
    print_info "日志文件已保存到: $LOG_FILE"
  fi
}
