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
# shellcheck source=docker_mirror_common.sh
source "${SCRIPT_DIR}/docker_mirror_common.sh"

# 可选：平台 Agent 同步（失败不阻断）
if [ -f "${PROJECT_ROOT}/.scripts/node/ensure_platform_agent_invoke.sh" ]; then
  # shellcheck source=../node/ensure_platform_agent_invoke.sh
  source "${PROJECT_ROOT}/.scripts/node/ensure_platform_agent_invoke.sh"
fi

# 模块列表（按依赖顺序：HARNESS 先于 IDEA；任一模块失败则跳过并继续后续模块）
MODULES=(
  "HARNESS"
  "IDEA"
  ".scripts/docker"
  "DEVICE"
  "AI"
  "RTC"
  "VIDEO"
  "WEB"
  "APP"
  "VISUALIZE"
  "TRANSFORM"
  "PANEL"
)

# 编排前置模块（install/start/restart/update 失败时终止后续步骤）
is_bootstrap_module() {
  case "$1" in
    HARNESS|IDEA) return 0 ;;
    *) return 1 ;;
  esac
}

# 面板分拆部署：EASYAIOT_DEPLOY_SCOPE=all|middleware|business
apply_deploy_scope() {
  local scope="${EASYAIOT_DEPLOY_SCOPE:-all}"
  case "$scope" in
    middleware)
      MODULES=(".scripts/docker")
      ;;
    business)
      local _filtered=()
      local _m
      for _m in "${MODULES[@]}"; do
        [ "$_m" = ".scripts/docker" ] && continue
        _filtered+=("$_m")
      done
      MODULES=("${_filtered[@]}")
      ;;
    all|"")
      ;;
    *)
      echo -e "${YELLOW}[WARN]${NC} 未知 EASYAIOT_DEPLOY_SCOPE=${scope}，按 all 处理" >&2
      ;;
  esac
}
apply_deploy_scope

# bash 3.2 兼容：用函数代替关联数组
module_name() {
  case "$1" in
    "HARNESS") echo "HARNESS AI助手" ;;
    "IDEA") echo "IDEA在线IDE" ;;
    ".scripts/docker") echo "基础服务" ;;
    "DEVICE") echo "Device服务" ;;
    "AI") echo "AI服务" ;;
    "RTC") echo "RTC服务" ;;
    "VIDEO") echo "Video服务" ;;
    "WEB") echo "Web前端服务" ;;
    "APP") echo "App移动端H5" ;;
    "VISUALIZE") echo "可视化编辑器" ;;
    "TRANSFORM") echo "数据转发" ;;
    "PANEL") echo "运维控制台" ;;
    *) echo "$1" ;;
  esac
}

module_port() {
  case "$1" in
    "HARNESS") echo "3080" ;;
    "IDEA") echo "9300" ;;
    ".scripts/docker") echo "8848" ;;
    "DEVICE") echo "48080" ;;
    "AI") echo "5000" ;;
    "RTC") echo "6100" ;;
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
    "HARNESS") echo "/" ;;
    "IDEA") echo "/health" ;;
    ".scripts/docker") echo "/nacos/actuator/health" ;;
    "DEVICE") echo "/actuator/health" ;;
    "AI") echo "/actuator/health" ;;
    "RTC") echo "/actuator/health" ;;
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
  # 运行中若 logs 被删，自动重建，避免 set -e 下写日志失败拖垮部署
  mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
  echo "[$timestamp] $clean_message" >> "$LOG_FILE" 2>/dev/null || true
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
# macOS：常见安装路径未进 PATH 时自动补齐当前会话
_ensure_mac_tool_paths() {
  [ "$EASYAIOT_DESKTOP_OS" = "mac" ] || return 0
  local _dir
  for _dir in \
    "/opt/homebrew/bin" \
    "/usr/local/bin" \
    "/Applications/Docker.app/Contents/Resources/bin" \
    "${HOME}/Applications/Docker.app/Contents/Resources/bin" \
    "${HOME}/.docker/bin"
  do
    if [ -d "$_dir" ]; then
      case ":${PATH}:" in
        *":${_dir}:"*) ;;
        *) export PATH="${_dir}:${PATH}" ;;
      esac
    fi
  done
}

# ---------- Docker Desktop / Colima 资源（CPU / 内存 / 磁盘）----------
# 环境变量可覆盖目标：EASYAIOT_DOCKER_MEMORY_GB / EASYAIOT_DOCKER_CPUS / EASYAIOT_DOCKER_DISK_GB
# 跳过：EASYAIOT_DOCKER_SKIP_RESOURCES=1

_desktop_host_mem_gb() {
  local mem_gb=""
  if [ "$(uname -s 2>/dev/null)" = "Darwin" ] && check_command sysctl; then
    local mem_bytes
    mem_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
    [ "${mem_bytes:-0}" -gt 0 ] 2>/dev/null && mem_gb=$((mem_bytes / 1024 / 1024 / 1024))
  elif check_command free; then
    mem_gb=$(free -g 2>/dev/null | awk '/Mem:/{print $2}')
  elif [ -n "${EASYAIOT_HOST_MEM_GB:-}" ]; then
    mem_gb="$EASYAIOT_HOST_MEM_GB"
  fi
  echo "${mem_gb:-0}"
}

_desktop_host_cpus() {
  local n=""
  if [ "$(uname -s 2>/dev/null)" = "Darwin" ] && check_command sysctl; then
    n=$(sysctl -n hw.ncpu 2>/dev/null || echo 0)
  elif check_command nproc; then
    n=$(nproc 2>/dev/null || echo 0)
  elif [ -r /proc/cpuinfo ]; then
    n=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || echo 0)
  fi
  echo "${n:-0}"
}

# 输出: memory_gb cpus disk_gb（按部署形态 + 主机能力）
_desktop_resource_targets() {
  local profile="${EASYAIOT_DEPLOY_PROFILE:-full}"
  local host_mem host_cpu
  host_mem=$(_desktop_host_mem_gb)
  host_cpu=$(_desktop_host_cpus)
  [ "${host_mem:-0}" -gt 0 ] 2>/dev/null || host_mem=16
  [ "${host_cpu:-0}" -gt 0 ] 2>/dev/null || host_cpu=8

  local want_mem want_cpu want_disk
  case "$profile" in
    # Docker 引擎目标内存（不够时由 resources / bootstrap / install 自动调高）
    mini)     want_mem=4;  want_cpu=4; want_disk=60 ;;
    standard) want_mem=16; want_cpu=6; want_disk=80 ;;
    *)        want_mem=24; want_cpu=8; want_disk=100 ;;  # full
  esac

  # 环境变量覆盖
  [ -n "${EASYAIOT_DOCKER_MEMORY_GB:-}" ] && want_mem="$EASYAIOT_DOCKER_MEMORY_GB"
  [ -n "${EASYAIOT_DOCKER_CPUS:-}" ] && want_cpu="$EASYAIOT_DOCKER_CPUS"
  [ -n "${EASYAIOT_DOCKER_DISK_GB:-}" ] && want_disk="$EASYAIOT_DOCKER_DISK_GB"

  # 不超过主机：内存留 ≥4GB / 或主机的 25%（取较大）给宿主机；CPU 最多 host-1
  local mem_cap cpu_cap reserve
  reserve=4
  if [ "$host_mem" -ge 32 ]; then
    reserve=8
  fi
  mem_cap=$((host_mem - reserve))
  [ "$mem_cap" -lt 4 ] && mem_cap=4
  # 也不超过主机约 75%
  local pct_cap=$((host_mem * 75 / 100))
  [ "$mem_cap" -gt "$pct_cap" ] && mem_cap=$pct_cap
  [ "$want_mem" -gt "$mem_cap" ] && want_mem=$mem_cap

  cpu_cap=$((host_cpu - 1))
  [ "$cpu_cap" -lt 2 ] && cpu_cap=2
  [ "$want_cpu" -gt "$cpu_cap" ] && want_cpu=$cpu_cap
  [ "$want_cpu" -gt "$host_cpu" ] && want_cpu=$host_cpu

  echo "$want_mem $want_cpu $want_disk"
}

_desktop_docker_mem_gb() {
  if ! check_command docker || ! docker info >/dev/null 2>&1; then
    echo "0"
    return
  fi
  # MemTotal 单位字节；四舍五入到 GB，避免 19.x 被地板成 19 误报未达标
  local bytes
  bytes=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
  if [ "${bytes:-0}" -gt 0 ] 2>/dev/null; then
    echo $(( (bytes + 536870912) / 1024 / 1024 / 1024 ))
  else
    echo "0"
  fi
}

_desktop_docker_cpus() {
  if ! check_command docker || ! docker info >/dev/null 2>&1; then
    echo "0"
    return
  fi
  docker info --format '{{.NCPU}}' 2>/dev/null || echo 0
}

# 解析 Windows 用户目录下的 Docker settings / .wslconfig（Git Bash 或 WSL）
_desktop_windows_userprofile() {
  local p=""
  if [ -n "${USERPROFILE:-}" ]; then
    p="$USERPROFILE"
  elif [ -n "${HOME:-}" ] && [ -d "${HOME}/AppData/Roaming" ]; then
    p="$HOME"
  elif check_command cmd.exe; then
    p=$(cmd.exe /c "echo %USERPROFILE%" 2>/dev/null | tr -d '\r')
  elif check_command powershell.exe; then
    p=$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("UserProfile")' 2>/dev/null | tr -d '\r')
  fi
  # WSL: C:\Users\x → /mnt/c/Users/x
  if [ -n "$p" ] && [[ "$p" == [A-Za-z]:* ]] && check_command wslpath; then
    wslpath -u "$p" 2>/dev/null || echo "$p"
  elif [ -n "$p" ] && [[ "$p" == [A-Za-z]:* ]]; then
    # Git Bash 常已是 /c/Users/...
    local drive="${p:0:1}"
    local rest="${p:2}"
    rest="${rest//\\//}"
    echo "/${drive,,}${rest}"
  else
    echo "$p"
  fi
}

_desktop_settings_json_candidates() {
  if [ "$EASYAIOT_DESKTOP_OS" = "mac" ] || [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
    echo "${HOME}/Library/Group Containers/group.com.docker/settings-store.json"
    echo "${HOME}/Library/Group Containers/group.com.docker/settings.json"
    return
  fi
  local win_home appdata
  win_home=$(_desktop_windows_userprofile)
  if [ -n "${APPDATA:-}" ]; then
    echo "${APPDATA}/Docker/settings-store.json"
    echo "${APPDATA}/Docker/settings.json"
  fi
  if [ -n "$win_home" ]; then
    echo "${win_home}/AppData/Roaming/Docker/settings-store.json"
    echo "${win_home}/AppData/Roaming/Docker/settings.json"
  fi
}

_desktop_patch_settings_json() {
  local path="$1"
  local mem_mib="$2"
  local cpus="$3"
  local disk_mib="$4"
  local swap_mib="${5:-4096}"
  [ -f "$path" ] || return 1
  python3 - "$path" "$mem_mib" "$cpus" "$disk_mib" "$swap_mib" <<'PY'
import json, sys, shutil, os
path, mem, cpus, disk, swap = sys.argv[1:6]
mem, cpus, disk, swap = int(mem), int(cpus), int(disk), int(swap)
backup = path + ".easyaiot.bak"
if not os.path.exists(backup):
    shutil.copy2(path, backup)
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
# 新旧 Desktop 字段名并存写入（读取端通常认其一）
for k, v in (
    ("memoryMiB", mem), ("MemoryMiB", mem),
    ("cpus", cpus), ("Cpus", cpus),
    ("diskSizeMiB", disk), ("DiskSizeMiB", disk),
    ("swapMiB", swap), ("SwapMiB", swap),
):
    data[k] = v
# 关闭空闲休眠，避免部署期间引擎被挂起
data["useResourceSaver"] = False
data["UseResourceSaver"] = False
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
print(path)
PY
}

_desktop_patch_wslconfig() {
  # Windows WSL2 后端：资源以 %USERPROFILE%\.wslconfig 为准
  local win_home mem_gb cpus
  win_home=$(_desktop_windows_userprofile)
  mem_gb="$1"
  cpus="$2"
  [ -n "$win_home" ] || return 1
  local cfg="${win_home}/.wslconfig"
  python3 - "$cfg" "$mem_gb" "$cpus" <<'PY'
import sys, os, re
path, mem, cpus = sys.argv[1], sys.argv[2], sys.argv[3]
block = f"""[wsl2]
memory={mem}GB
processors={cpus}
swap=4GB
localhostForwarding=true
"""
if os.path.exists(path):
    text = open(path, encoding="utf-8", errors="ignore").read()
    if re.search(r"(?im)^\[wsl2\]", text):
        # 更新已有 [wsl2] 段中的 memory/processors/swap
        def repl_section(m):
            sec = m.group(0)
            for key, val in (("memory", f"{mem}GB"), ("processors", str(cpus)), ("swap", "4GB")):
                if re.search(rf"(?im)^\s*{key}\s*=", sec):
                    sec = re.sub(rf"(?im)^\s*{key}\s*=.*$", f"{key}={val}", sec, count=1)
                else:
                    sec = sec.rstrip() + f"\n{key}={val}\n"
            return sec
        text2, n = re.subn(r"(?ims)^\[wsl2\].*?(?=^\[|\Z)", repl_section, text, count=1)
        if n:
            open(path, "w", encoding="utf-8").write(text2)
            print(path)
            sys.exit(0)
    open(path, "a", encoding="utf-8").write("\n" + block)
else:
    open(path, "w", encoding="utf-8").write(block)
print(path)
PY
}

_desktop_restart_engine() {
  local mode="$1"  # desktop | colima
  if [ "$mode" = "colima" ]; then
    return 0  # colima 由 start 参数生效，无需此处重启
  fi
  print_info "重启 Docker Desktop 以使资源设置生效..."
  if [ "$EASYAIOT_DESKTOP_OS" = "mac" ] || [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
    osascript -e 'quit app "Docker"' >/dev/null 2>&1 || true
    sleep 3
    # 残留进程时再强杀
    pkill -f 'Docker Desktop' >/dev/null 2>&1 || true
    pkill -f com.docker.backend >/dev/null 2>&1 || true
    sleep 2
    open -a Docker >/dev/null 2>&1 || true
  else
    # Windows：优先 PowerShell
    if check_command powershell.exe; then
      powershell.exe -NoProfile -ExecutionPolicy Bypass -Command @'
$ErrorActionPreference = "SilentlyContinue"
Get-Process "Docker Desktop","com.docker.backend","com.docker.service" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
$exes = @(
  "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
  "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
  "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
)
foreach ($e in $exes) { if (Test-Path $e) { Start-Process $e; break } }
if (Get-Command wsl.exe -ErrorAction SilentlyContinue) { wsl.exe --shutdown 2>$null }
'@ >/dev/null 2>&1 || true
    fi
  fi
  local i
  for i in $(seq 1 90); do
    _ensure_mac_tool_paths
    if check_command docker && docker info >/dev/null 2>&1; then
      print_success "Docker 引擎已重新就绪"
      return 0
    fi
    if [ $((i % 10)) -eq 0 ]; then
      print_info "等待 Docker 重启... (${i}/90)"
    fi
    sleep 2
  done
  print_warning "Docker 重启后尚未就绪，请手动打开 Docker Desktop 后再 check"
  return 1
}

# 检测当前引擎类型：desktop | colima | unknown
_desktop_engine_kind() {
  if ! check_command docker || ! docker info >/dev/null 2>&1; then
    echo "unknown"
    return
  fi
  local ctx osname
  ctx=$(docker context show 2>/dev/null || echo "")
  osname=$(docker info --format '{{.OperatingSystem}}' 2>/dev/null || echo "")
  if [ "$ctx" = "colima" ] || echo "$osname" | grep -qi colima; then
    echo "colima"
  elif echo "$osname" | grep -qi 'Docker Desktop'; then
    echo "desktop"
  elif [ -d "/Applications/Docker.app" ] || [ -d "${HOME}/Applications/Docker.app" ]; then
    echo "desktop"
  else
    echo "desktop"
  fi
}

# 调配 Docker Desktop / Colima 资源。返回 0=已达目标或已成功写入；1=失败
desktop_configure_resources() {
  local force="${1:-0}"  # 1=即使已足够也重写并重启
  if [ "${EASYAIOT_DOCKER_SKIP_RESOURCES:-0}" = "1" ]; then
    print_info "已设置 EASYAIOT_DOCKER_SKIP_RESOURCES=1，跳过资源调配"
    return 0
  fi
  if ! check_command python3; then
    print_warning "未找到 python3，无法自动改写 Docker Desktop 配置；请在 GUI Settings → Resources 手动调内存"
    return 1
  fi

  print_section "调配 Docker 引擎资源（CPU / 内存 / 磁盘）"
  ensure_deploy_profile 2>/dev/null || true
  local want_mem want_cpu want_disk
  read -r want_mem want_cpu want_disk <<< "$(_desktop_resource_targets)"
  local cur_mem cur_cpu kind
  cur_mem=$(_desktop_docker_mem_gb)
  cur_cpu=$(_desktop_docker_cpus)
  kind=$(_desktop_engine_kind)

  print_info "部署形态: ${EASYAIOT_DEPLOY_PROFILE:-full}"
  print_info "目标: ${want_cpu} CPU / ${want_mem}GB 内存 / ${want_disk}GB 磁盘"
  print_info "当前引擎: ${kind} · ${cur_cpu} CPU / ${cur_mem}GB 内存"

  # 允许差 1GB（docker info 常显示 23.4GiB → 约 23/24）
  local mem_ok=0
  if [ "${cur_mem:-0}" -ge "$want_mem" ] 2>/dev/null \
    || [ "${cur_mem:-0}" -ge $((want_mem - 1)) ] 2>/dev/null; then
    mem_ok=1
  fi
  if [ "$force" != "1" ] && [ "$mem_ok" -eq 1 ] \
    && [ "${cur_cpu:-0}" -ge "$want_cpu" ] 2>/dev/null; then
    print_success "引擎资源已满足目标（约 ${cur_mem}GB / 目标 ${want_mem}GB），无需调整"
    return 0
  fi

  local mem_mib=$((want_mem * 1024))
  local disk_mib=$((want_disk * 1024))
  local swapped=0

  if [ "$kind" = "colima" ]; then
    print_info "正在按目标重启 Colima..."
    colima stop >/dev/null 2>&1 || true
    local arch_flag=""
    case "$(uname -m)" in
      arm64|aarch64) arch_flag="--arch aarch64" ;;
    esac
    # shellcheck disable=SC2086
    if colima start --cpu "$want_cpu" --memory "$want_mem" --disk "$want_disk" $arch_flag --downloader curl; then
      docker context use colima >/dev/null 2>&1 || true
      swapped=1
    else
      print_error "Colima 以新规格启动失败"
      return 1
    fi
  else
    local f patched=0
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      if [ -f "$f" ]; then
        if _desktop_patch_settings_json "$f" "$mem_mib" "$want_cpu" "$disk_mib"; then
          print_success "已写入: $f"
          patched=1
        fi
      fi
    done < <(_desktop_settings_json_candidates)

    if [ "$EASYAIOT_DESKTOP_OS" = "windows" ] || [ -n "${WINDIR:-}" ] || uname -s 2>/dev/null | grep -qiE 'MINGW|MSYS|CYGWIN'; then
      if _desktop_patch_wslconfig "$want_mem" "$want_cpu"; then
        print_success "已更新 WSL2 资源限制（.wslconfig）"
        patched=1
      fi
    fi
    # WSL 内跑脚本时也尝试写 .wslconfig
    if [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; then
      _desktop_patch_wslconfig "$want_mem" "$want_cpu" >/dev/null 2>&1 && patched=1 || true
    fi

    if [ "$patched" -eq 0 ]; then
      print_warning "未找到 Docker Desktop settings-store.json"
      if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
        print_info "请打开 Docker Desktop → Settings → Resources，将 Memory 调到 ≥${want_mem}GB 后 Apply & Restart"
      else
        print_info "请打开 Docker Desktop → Settings → Resources，或编辑 %USERPROFILE%\\.wslconfig 后执行 wsl --shutdown"
      fi
      return 1
    fi
    _desktop_restart_engine desktop || true
    swapped=1
  fi

  # 复核
  sleep 2
  cur_mem=$(_desktop_docker_mem_gb)
  cur_cpu=$(_desktop_docker_cpus)
  print_info "调整后: ${cur_cpu} CPU / ${cur_mem}GB 内存"
  if [ "${cur_mem:-0}" -ge "$want_mem" ] 2>/dev/null \
    || [ "${cur_mem:-0}" -ge $((want_mem - 1)) ] 2>/dev/null; then
    print_success "Docker 引擎内存已达标（约 ${cur_mem}GB，目标 ${want_mem}GB）"
    return 0
  fi
  if [ "$swapped" -eq 1 ]; then
    print_warning "配置已写入，但引擎汇报内存仍为 ${cur_mem}GB（目标 ${want_mem}GB）"
    print_info "若刚重启，请稍等引擎完全启动后再执行: bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh resources"
    print_info "或在 Docker Desktop → Settings → Resources 中确认并 Apply & Restart"
  fi
  return 0
}

# 打印 macOS 部署前置操作清单（部署前始终展示，便于人工确认）
print_mac_prereq_guide() {
  [ "$EASYAIOT_DESKTOP_OS" = "mac" ] || return 0
  echo ""
  echo -e "${YELLOW}========================================${NC}"
  echo -e "${YELLOW}  macOS 部署前置操作清单${NC}"
  echo -e "${YELLOW}========================================${NC}"
  echo ""
  echo "  ① Homebrew（包管理器）"
  echo "     /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
  echo ""
  echo "  ② Bash 4+（系统 /bin/bash 为 3.2，无法跑部署脚本）"
  echo "     brew install bash"
  echo ""
  echo "  ③ Docker 引擎（二选一，必须 docker info 可用）"
  echo "     A. Docker Desktop（推荐有 GUI 时）"
  echo "        brew install --cask docker"
  echo "        或官网: https://www.docker.com/products/docker-desktop"
  echo "        安装后打开 Docker Desktop，等待菜单栏鲸鱼图标稳定"
  echo "     B. Colima（无 Desktop / 官网下载失败时的轻量方案）"
  echo "        brew install docker docker-compose colima"
  echo "        colima start --cpu 6 --memory 16 --disk 100"
  echo ""
  echo "  ④ 国内镜像加速（与 Linux 一致，bootstrap/install 自动写入 ~/.docker/daemon.json）："
  echo "     主源 DaoCloud → 回退 1ms / 1panel（DOCKER_MIRROR / DOCKER_MIRROR_FALLBACKS 可覆盖）"
  echo "     FUXA 例外：pull_fuxa.sh 优先 1ms（DaoCloud 对 frangoteam 常 403）"
  echo "     手动: bash .scripts/docker/install_mac.sh mirrors"
  echo ""
  echo "  ⑤ 硬件建议（full 全量）：主机内存 ≥ 32GB，磁盘可用 ≥ 100GB"
  echo "     Docker 引擎建议：mini 4GB / standard 16GB / full 24GB（默认常仅 ~8GB）"
  echo "     一键调配: bash .scripts/docker/install_mac.sh resources"
  echo ""
  echo "  一键安装以上依赖（含尝试调高 Docker 内存）："
  echo "     bash .scripts/docker/install_mac.sh bootstrap"
  echo ""
  echo "  装好后自检："
  echo "     bash .scripts/docker/install_mac.sh check"
  echo ""
}

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
  _ensure_mac_tool_paths

  # macOS：先打印前置操作清单，再逐项检测
  if [ "$EASYAIOT_DESKTOP_OS" = "mac" ] && [ "$quiet_ok" != "1" ]; then
    print_mac_prereq_guide
    print_section "正在逐项检测"
  fi

  # 0) macOS：Homebrew（软性：仅提示，不阻断；bootstrap 需要）
  if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
    if check_command brew; then
      print_success "Homebrew: $(brew --version 2>/dev/null | head -n1 || echo 已安装)"
    else
      warnings+=("未检测到 Homebrew；一键安装依赖请先安装: https://brew.sh")
      howto+=("安装 Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
    fi
  fi

  # 1) bash 版本
  if [ "${BASH_VERSINFO[0]}" -lt 4 ]; then
    missing+=("Bash 4+（当前: ${BASH_VERSION:-unknown}）")
    if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
      howto+=("一键安装: bash .scripts/docker/install_mac.sh bootstrap")
      howto+=("或手动: brew install bash ，然后用 /opt/homebrew/bin/bash 重新执行本脚本")
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

  # 3) Docker CLI（Windows / macOS：常见安装路径未进 PATH 时自动补齐当前会话）
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
    missing+=("Docker CLI / 引擎（未找到 docker 命令）")
    if [ "$EASYAIOT_DESKTOP_OS" = "windows" ]; then
      howto+=("推荐 PowerShell 一键引导:  .\\.scripts\\docker\\install_windows.ps1 bootstrap")
      howto+=("或管理员执行:  wsl --install")
      howto+=("然后:  winget install -e --id Docker.DockerDesktop")
      howto+=("手动下载: https://www.docker.com/products/docker-desktop （建议勾选 WSL2 后端）")
      howto+=("装完后重启终端（必要时重启电脑）再执行本脚本")
    else
      howto+=("一键安装: bash .scripts/docker/install_mac.sh bootstrap")
      howto+=("方案 A: brew install --cask docker && open -a Docker")
      howto+=("方案 B: brew install docker docker-compose colima && colima start")
    fi
  fi

  # 4) Docker daemon（可尝试拉起 Desktop；未安装则快速失败，不空等）
  # Windows：优先轻量 docker version；引擎挂死时限时探测，避免无限阻塞
  _docker_info_ok() {
    if [ "$EASYAIOT_DESKTOP_OS" = "windows" ]; then
      local _probe_cmd=(docker version --format '{{.Server.Version}}')
      if command -v timeout >/dev/null 2>&1; then
        local _ver
        _ver="$(timeout 20 "${_probe_cmd[@]}" 2>/dev/null | head -n1 | tr -d '\r')"
        [ -n "$_ver" ]
        return $?
      fi
      # Git Bash 常无 GNU timeout：后台跑 + 轮询
      "${_probe_cmd[@]}" >/tmp/easyaiot_docker_probe.$$ 2>/dev/null &
      local _dipid=$!
      local _di=0
      while [ $_di -lt 20 ]; do
        if ! kill -0 $_dipid 2>/dev/null; then
          wait $_dipid
          local _rc=$?
          local _ver
          _ver="$(tr -d '\r' </tmp/easyaiot_docker_probe.$$ 2>/dev/null | head -n1)"
          rm -f /tmp/easyaiot_docker_probe.$$ 2>/dev/null || true
          [ $_rc -eq 0 ] && [ -n "$_ver" ]
          return $?
        fi
        sleep 1
        _di=$((_di + 1))
      done
      kill $_dipid 2>/dev/null || true
      wait $_dipid 2>/dev/null || true
      rm -f /tmp/easyaiot_docker_probe.$$ 2>/dev/null || true
      return 1
    fi
    docker info >/dev/null 2>&1
  }

  local docker_daemon_ok=0
  if [ "$docker_cli_ok" -eq 1 ]; then
    if _docker_info_ok; then
      local _ctx
      _ctx=$(docker context show 2>/dev/null || echo default)
      if [ "$EASYAIOT_DESKTOP_OS" = "mac" ] && { [ "$_ctx" = "colima" ] || check_command colima; } \
        && colima status 2>/dev/null | grep -qi running; then
        print_success "Docker 引擎已运行（Colima，context=${_ctx}）"
      else
        print_success "Docker 引擎已运行（context=${_ctx}）"
      fi
      docker_daemon_ok=1
    else
      local desktop_launchable=0
      local colima_launchable=0
      if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
        if [ -d "/Applications/Docker.app" ] || [ -d "${HOME}/Applications/Docker.app" ]; then
          desktop_launchable=1
          print_warning "Docker 引擎未就绪，尝试启动 Docker Desktop..."
          open -a Docker >/dev/null 2>&1 || true
        elif check_command colima; then
          colima_launchable=1
          print_warning "Docker 引擎未就绪，尝试启动 Colima..."
          colima start >/dev/null 2>&1 || true
          docker context use colima >/dev/null 2>&1 || true
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

      if [ "$desktop_launchable" -eq 1 ] || [ "$colima_launchable" -eq 1 ]; then
        local i
        for i in $(seq 1 45); do
          sleep 2
          if _docker_info_ok; then
            print_success "Docker 引擎已就绪"
            docker_daemon_ok=1
            break
          fi
          if [ $((i % 5)) -eq 0 ]; then
            if [ "$colima_launchable" -eq 1 ]; then
              print_info "等待 Colima 启动... (${i}/45)"
            else
              print_info "等待 Docker Desktop 启动... (${i}/45)"
            fi
          fi
        done
      fi

      if [ "$docker_daemon_ok" -eq 0 ]; then
        if [ "$desktop_launchable" -eq 0 ] && [ "$colima_launchable" -eq 0 ]; then
          missing+=("Docker 引擎未安装或未运行（docker info 失败）")
          if [ "$EASYAIOT_DESKTOP_OS" = "windows" ]; then
            howto+=("推荐: .\\.scripts\\docker\\install_windows.ps1 bootstrap")
            howto+=("下载安装并启动 Docker Desktop: https://www.docker.com/products/docker-desktop")
          else
            howto+=("一键安装: bash .scripts/docker/install_mac.sh bootstrap")
            howto+=("方案 A: brew install --cask docker && open -a Docker")
            howto+=("方案 B: brew install docker docker-compose colima && colima start")
          fi
        elif [ "$colima_launchable" -eq 1 ]; then
          missing+=("Colima / Docker 引擎未运行（docker info 失败）")
          howto+=("请执行: colima start   然后: docker context use colima")
        else
          missing+=("Docker Desktop 引擎未运行（docker info 失败）")
          howto+=("请手动打开 Docker Desktop，等待菜单栏鲸鱼图标显示 Running 后重试")
          if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
            howto+=("也可执行: open -a Docker")
          fi
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

  # 7) 软性告警：主机内存 + Docker 引擎已分配内存（不阻断）
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
  local profile_hint="${EASYAIOT_DEPLOY_PROFILE:-full}"
  if [ -n "$mem_gb" ] && [ "$mem_gb" -gt 0 ] 2>/dev/null; then
    if [ "$mem_gb" -lt 8 ]; then
      warnings+=("物理内存约 ${mem_gb}GB，建议 ≥16GB（mini 规格至少 ≥8GB）")
    elif [ "$profile_hint" = "full" ] && [ "$mem_gb" -lt 32 ]; then
      warnings+=("物理内存约 ${mem_gb}GB；full 全量建议主机 ≥32GB（引擎目标 24GB）")
      print_info "主机内存: 约 ${mem_gb}GB"
    elif [ "$profile_hint" = "standard" ] && [ "$mem_gb" -lt 24 ]; then
      warnings+=("物理内存约 ${mem_gb}GB；standard 建议主机 ≥24GB（引擎目标 16GB）")
      print_info "主机内存: 约 ${mem_gb}GB"
    else
      print_info "主机内存: 约 ${mem_gb}GB"
    fi
  fi
  # Docker VM / Colima 已分配内存（full 常需远高于 Desktop 默认 8GB）
  if check_command docker && docker info >/dev/null 2>&1; then
    local docker_mem_gb want_mem
    docker_mem_gb=$(_desktop_docker_mem_gb 2>/dev/null || echo "")
    want_mem=$(_desktop_resource_targets | awk '{print $1}')
    if [ -n "$docker_mem_gb" ] && [ "$docker_mem_gb" -gt 0 ] 2>/dev/null; then
      print_info "Docker 引擎内存: 约 ${docker_mem_gb}GB（形态 ${profile_hint} 建议 ≥${want_mem}GB）"
      # 允许差 1GB（docker info 常显示 23.4GiB）
      if [ "$docker_mem_gb" -lt $((want_mem - 1)) ] 2>/dev/null; then
        warnings+=("Docker 引擎仅约 ${docker_mem_gb}GB，${profile_hint} 建议 ≥${want_mem}GB；请执行: bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh resources")
      fi
    fi
  fi

  # 8) 磁盘可用空间（软性）
  if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
    local avail_gb=""
    avail_gb=$(df -g "$PROJECT_ROOT" 2>/dev/null | awk 'NR==2{print $4}')
    if [ -n "$avail_gb" ] && [ "$avail_gb" -gt 0 ] 2>/dev/null; then
      if [ "$avail_gb" -lt 50 ]; then
        warnings+=("项目所在磁盘可用约 ${avail_gb}GB，建议预留 ≥100GB（镜像与数据卷）")
      else
        print_info "磁盘可用: 约 ${avail_gb}GB"
      fi
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
    echo "请按下列说明完成前置操作后重试："
    local h n=1
    for h in "${howto[@]}"; do
      echo "  ${n}. $h"
      n=$((n + 1))
    done
    echo ""
    if [ "$EASYAIOT_DESKTOP_OS" = "mac" ]; then
      echo "推荐一键安装前置依赖："
      echo "  bash .scripts/docker/install_mac.sh bootstrap"
      echo ""
    fi
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

# 导出本机容器平台，避免 AI install_linux 在 Apple Silicon 上误判为不支持 ARM，
# 并保证中间件 compose 的 NACOS_PLATFORM 与宿主机一致。
export_desktop_arch_env() {
  case "$(uname -m)" in
    x86_64|amd64)
      export DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"
      ;;
    arm64|aarch64)
      export DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/arm64}"
      ;;
    *)
      export DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"
      ;;
  esac
  export NACOS_PLATFORM="${NACOS_PLATFORM:-${DOCKER_PLATFORM}}"
}

prepare_desktop_environment() {
  # 统一前置检测：缺什么提示装什么，不满足则中止
  require_desktop_prerequisites
  export_desktop_arch_env
  detect_host_ip_desktop
  create_network
  # 与 Linux 对齐：自动写入 Desktop ~/.docker/daemon.json 国内 registry-mirrors
  # FUXA 仍走 pull_fuxa.sh（1ms 优先），不依赖 DaoCloud
  configure_docker_mirror_desktop || print_warning "Desktop 镜像源自动配置未完成，中间件仍会走多源直连回退"
  print_info "中间件拉取回退链: ${DOCKER_MIRROR_FALLBACKS:-docker.m.daocloud.io,docker.1ms.run,docker.1panel.live}"
  print_info "FUXA: 专用多源（1ms → 1panel → DaoCloud）"
  print_info "容器平台: ${DOCKER_PLATFORM}（Nacos: ${NACOS_PLATFORM}）"
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
      HARNESS)
        print_error "未检测到 HARNESS 目录，无法部署 AI 助手"
        return 1
        ;;
      IDEA)
        print_error "未检测到 IDEA 目录，无法部署在线 IDE"
        return 1
        ;;
    esac
    print_warning "模块 $module 不存在，跳过"
    return 1
  fi

  cd "$PROJECT_ROOT/$module"

  if [ ! -f "$install_file" ]; then
    case "$module" in
      HARNESS)
        print_error "未检测到 HARNESS/install_linux.sh，无法部署 AI 助手"
        return 1
        ;;
      IDEA)
        print_error "未检测到 IDEA/install_linux.sh，无法部署在线 IDE"
        return 1
        ;;
    esac
    print_info "${name} 无安装脚本 ${install_file}，跳过"
    return 0
  fi

  fix_line_endings "$install_file"
  print_info "执行 ${name}: ${command}"

  ensure_deploy_profile
  export_desktop_arch_env
  export EASYAIOT_DEPLOY_PROFILE
  export EASYAIOT_SKIP_PROFILE_PROMPT
  export EASYAIOT_SKIP_IMAGE_PROMPT=1
  export EASYAIOT_SKIP_BUILD=1
  export HOST_IP
  export DOCKER_PLATFORM
  export NACOS_PLATFORM

  # Docker Desktop：host 网络无法把端口暴露到宿主机，启用 bridge override
  unset COMPOSE_FILE 2>/dev/null || true
  case "$module" in
    VIDEO|AI|RTC|DEVICE)
      export EASYAIOT_COMPOSE_DESKTOP=1
      if [ -f docker-compose.desktop.yaml ]; then
        local base_compose="docker-compose.yaml"
        [ -f docker-compose.yml ] && base_compose="docker-compose.yml"
        local compose_files="${base_compose}:docker-compose.desktop.yaml"
        if [ -f .docker-compose.gpu.override.yaml ]; then
          compose_files="${compose_files}:.docker-compose.gpu.override.yaml"
        fi
        export COMPOSE_FILE="$compose_files"
        print_info "已启用桌面端网络 override（bridge + 端口映射）: ${COMPOSE_FILE}"
      fi
      # DEVICE 桌面 override 将 yolo 数据集挂到项目缓存目录
      if [ "$module" = "DEVICE" ]; then
        mkdir -p "${PROJECT_ROOT}/.build-cache/device/yolo_dataset" \
          "${PROJECT_ROOT}/.build-cache/device/logs" \
          "${PROJECT_ROOT}/.build-cache/device/node-logs" \
          "${PROJECT_ROOT}/.build-cache/device/visualize-logs" 2>/dev/null || true
      fi
      ;;
  esac

  local defer_agent_sync=0
  case "$module" in
    DEVICE|AI|RTC|VIDEO|WEB|APP|VISUALIZE|TRANSFORM) defer_agent_sync=1 ;;
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
    # Docker Desktop（尤其 Apple Silicon）上 Nacos 冷启动可达数分钟，与 compose healthcheck start_period 对齐
    wait_for_container_ready "Nacos" 150 2 bash -c 'curl -sf --connect-timeout 2 --max-time 5 http://127.0.0.1:8848/nacos/actuator/health >/dev/null 2>&1 || docker exec nacos-server curl -sf --connect-timeout 2 --max-time 5 http://127.0.0.1:8848/nacos/actuator/health >/dev/null 2>&1 || [ "$(docker inspect -f "{{.State.Health.Status}}" nacos-server 2>/dev/null)" = "healthy" ]'
  fi
  if docker ps --filter "name=redis-server" --format "{{.Names}}" 2>/dev/null | grep -q "redis-server"; then
    wait_for_container_ready "Redis" 30 1 \
      docker exec redis-server redis-cli ping
  fi
  # full 形态：TDengine 就绪后再启 DEVICE（iot-tdengine 依赖）
  if [ "${EASYAIOT_DEPLOY_PROFILE:-full}" = "full" ] \
    && docker ps --filter "name=tdengine-server" --format "{{.Names}}" 2>/dev/null | grep -q "tdengine-server"; then
    wait_for_container_ready "TDengine" 60 2 \
      docker exec tdengine-server taos -h localhost -s "select 1;"
  fi
}

wait_for_device_gateway() {
  wait_for_container_ready "iot-gateway" 180 2 bash -c 'curl -sf --connect-timeout 2 --max-time 5 http://127.0.0.1:48080/actuator/health >/dev/null 2>&1 || docker exec iot-gateway curl -sf --connect-timeout 2 --max-time 5 http://127.0.0.1:48080/actuator/health >/dev/null 2>&1 || [ "$(docker inspect -f "{{.State.Health.Status}}" iot-gateway 2>/dev/null)" = "healthy" ]'
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
    if declare -F runtime_images_last_log_path >/dev/null 2>&1; then
      _desk_log=$(runtime_images_last_log_path 2>/dev/null || true)
      [ -n "${_desk_log:-}" ] && print_warning "拉取详情日志: ${_desk_log}"
    fi
    if declare -F runtime_images_report_missing_refs >/dev/null 2>&1; then
      runtime_images_report_missing_refs \
        "${EASYAIOT_DEPLOY_PROFILE:-full}" \
        "${EASYAIOT_RUNTIME_TAG:-latest}"
    fi
    return 0
  fi
  print_error "预构建镜像拉取失败，且桌面端禁止本地构建"
  print_info "请检查网络 / Docker Desktop 镜像加速 / runtime_registry.conf 后重试: pull"
  if declare -F runtime_images_dump_pull_failure >/dev/null 2>&1; then
    runtime_images_dump_pull_failure desktop
  fi
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
  # 全量部署前自动把 Docker 引擎内存调到建议值（不足时改 settings / 重启）
  desktop_configure_resources 0 || true

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
      if [ "$module" = "PANEL" ]; then
        print_info "跳过运维控制台（PANEL）：$(panel_skip_deploy_reason)"
      else
        print_info "跳过 $(module_name "$module")（形态 ${EASYAIOT_DEPLOY_PROFILE} 不包含）"
      fi
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
      print_error "$(module_name "$module") 安装失败，已跳过并继续后续模块"
      if [ -n "${LOG_FILE:-}" ] && [ -f "$LOG_FILE" ]; then
        print_error "日志末尾 (${LOG_FILE}):"
        tail -n 40 "$LOG_FILE" 2>/dev/null | while IFS= read -r _line; do print_error "  ${_line}"; done || true
      fi
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
  # 预先同步部署形态到各模块 .env，避免并行子 shell 同时写同一文件产生竞态
  sync_deploy_profile_to_modules
  prepare_desktop_environment

  # HARNESS 先于 IDEA（失败跳过并继续后续模块）
  local module
  for module in HARNESS IDEA; do
    if module_enabled_for_deploy_profile "$module"; then
      print_section "启动 $(module_name "$module")"
      if ! execute_module_command "$module" "start"; then
        print_error "$(module_name "$module") 启动失败，已跳过并继续后续模块"
        if [ -n "${LOG_FILE:-}" ] && [ -f "$LOG_FILE" ]; then
          print_error "日志末尾 (${LOG_FILE}):"
          tail -n 40 "$LOG_FILE" 2>/dev/null | while IFS= read -r _line; do print_error "  ${_line}"; done || true
        fi
      fi
      echo ""
    fi
  done

  print_section "启动基础服务"
  if ! execute_module_command ".scripts/docker" "start"; then
    print_error "基础服务启动失败，已跳过并继续后续模块"
    if [ -n "${LOG_FILE:-}" ] && [ -f "$LOG_FILE" ]; then
      print_error "日志末尾 (${LOG_FILE}):"
      tail -n 40 "$LOG_FILE" 2>/dev/null | while IFS= read -r _line; do print_error "  ${_line}"; done || true
    fi
  fi
  wait_for_base_services
  echo ""

  collect_biz_modules
  local -a start_modules=()
  local module
  for module in "${BIZ_MODULES[@]}"; do
    is_bootstrap_module "$module" && continue
    start_modules+=("$module")
  done
  if [ "${PARALLEL_MODULES:-true}" = "true" ] && [ ${#start_modules[@]} -gt 0 ]; then
    print_info "并行启动业务模块: ${start_modules[*]}"
    local pids=() mods=() mlog rc fail=0 i
    for module in "${start_modules[@]}"; do
      mlog="${LOG_DIR}/start_$(echo "$module" | tr '/' '_')_$$.log"
      : > "$mlog"
      (
        LOG_FILE="$mlog"
        export_desktop_arch_env
        execute_module_command "$module" "start" >/dev/null 2>&1
      ) &
      pids+=($!)
      mods+=("$module")
    done
    for i in "${!pids[@]}"; do
      if wait "${pids[$i]}"; then
        print_success "$(module_name "${mods[$i]}"): start 完成"
      else
        fail=$((fail + 1))
        print_error "$(module_name "${mods[$i]}"): start 失败"
        # 便于排障：把子模块失败日志摘要打到主日志
        mlog="${LOG_DIR}/start_$(echo "${mods[$i]}" | tr '/' '_')_$$.log"
        if [ -f "$mlog" ]; then
          print_info "---- $(module_name "${mods[$i]}") 失败日志尾部 (${mlog}) ----"
          tail -n 40 "$mlog" 2>/dev/null | tee -a "$LOG_FILE" || true
        fi
      fi
    done
    [ "$fail" -eq 0 ] || print_warning "有 ${fail} 个模块启动失败"
  else
    for module in "${start_modules[@]}"; do
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

  # HARNESS 先于 IDEA（失败跳过并继续后续模块）
  local module
  for module in HARNESS IDEA; do
    if module_enabled_for_deploy_profile "$module"; then
      print_section "更新 $(module_name "$module")"
      if ! execute_module_command "$module" "update"; then
        print_error "$(module_name "$module") 更新失败，已跳过并继续后续模块"
        if [ -n "${LOG_FILE:-}" ] && [ -f "$LOG_FILE" ]; then
          print_error "日志末尾 (${LOG_FILE}):"
          tail -n 40 "$LOG_FILE" 2>/dev/null | while IFS= read -r _line; do print_error "  ${_line}"; done || true
        fi
      fi
    fi
  done

  execute_module_command ".scripts/docker" "update" || print_warning "基础服务更新失败"
  wait_for_base_services

  collect_biz_modules
  local module
  for module in "${BIZ_MODULES[@]}"; do
    is_bootstrap_module "$module" && continue
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
  echo -e "  IDEA 在线 IDE:          http://localhost:9300"
  if module_enabled_for_deploy_profile HARNESS; then
    echo -e "  AI 助手 (HARNESS):       http://localhost:3080"
  fi
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

# ---------- 一键安装前置依赖（macOS；对齐 Windows bootstrap） ----------
desktop_bootstrap() {
  if [ "$EASYAIOT_DESKTOP_OS" != "mac" ]; then
    print_error "bootstrap 当前仅实现于 macOS（Windows 请用 install_windows.ps1 bootstrap）"
    return 1
  fi

  print_section "macOS 前置依赖安装（bootstrap）"
  print_mac_prereq_guide
  _ensure_mac_tool_paths

  local fail=0

  # 1) Homebrew
  if check_command brew; then
    print_success "Homebrew 已安装: $(brew --version 2>/dev/null | head -n1)"
  else
    print_info "正在安装 Homebrew（可能需要输入本机密码）..."
    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
      _ensure_mac_tool_paths
      # Apple Silicon 默认 brew 路径
      if [ -x /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true
        export PATH="/opt/homebrew/bin:${PATH}"
      fi
      if check_command brew; then
        print_success "Homebrew 安装成功"
      else
        print_error "Homebrew 安装后仍未找到 brew 命令，请新开终端后重试 bootstrap"
        return 1
      fi
    else
      print_error "Homebrew 安装失败"
      print_info "请手动安装: https://brew.sh"
      return 1
    fi
  fi

  # 2) Bash 4+
  local brew_bash=""
  for brew_bash in /opt/homebrew/bin/bash /usr/local/bin/bash; do
    if [ -x "$brew_bash" ] && "$brew_bash" -c '[[ ${BASH_VERSINFO[0]} -ge 4 ]]' 2>/dev/null; then
      print_success "Bash 4+: $($brew_bash --version | head -n1)"
      brew_bash="ok"
      break
    fi
  done
  if [ "$brew_bash" != "ok" ]; then
    print_info "正在安装 Bash 4+（brew install bash）..."
    if HOMEBREW_NO_AUTO_UPDATE=1 brew install bash; then
      _ensure_mac_tool_paths
      if [ -x /opt/homebrew/bin/bash ]; then
        print_success "Bash 已安装: $(/opt/homebrew/bin/bash --version | head -n1)"
      else
        print_success "brew install bash 完成"
      fi
    else
      print_error "brew install bash 失败"
      fail=1
    fi
  fi

  # 3) Docker 引擎：优先 Docker Desktop；失败则回退 Colima
  _ensure_mac_tool_paths
  local docker_app=""
  local engine_mode=""
  if [ -d "/Applications/Docker.app" ]; then
    docker_app="/Applications/Docker.app"
  elif [ -d "${HOME}/Applications/Docker.app" ]; then
    docker_app="${HOME}/Applications/Docker.app"
  fi

  if check_command docker && docker info >/dev/null 2>&1; then
    print_success "Docker 引擎已可用: $(docker --version 2>/dev/null | head -n1)"
    engine_mode="ready"
  elif [ -n "$docker_app" ]; then
    print_success "Docker Desktop 已安装: $docker_app"
    engine_mode="desktop"
    _ensure_mac_tool_paths
  else
    print_info "尝试安装 Docker Desktop（brew cask）..."
    if HOMEBREW_NO_AUTO_UPDATE=1 brew install --cask docker; then
      print_success "Docker Desktop cask 安装完成"
      engine_mode="desktop"
      _ensure_mac_tool_paths
    else
      print_warning "Docker Desktop 安装失败（常见于无法访问 desktop.docker.com）"
      print_info "回退安装 Colima + Docker CLI（轻量 Docker 引擎）..."
      if HOMEBREW_NO_AUTO_UPDATE=1 brew install docker docker-compose colima; then
        # 确保 compose 插件可被 docker 发现
        mkdir -p "${HOME}/.docker"
        if [ ! -f "${HOME}/.docker/config.json" ]; then
          cat > "${HOME}/.docker/config.json" <<'EOF'
{
  "cliPluginsExtraDirs": [
    "/opt/homebrew/lib/docker/cli-plugins"
  ]
}
EOF
        fi
        engine_mode="colima"
        print_success "已安装 docker / docker-compose / colima"
      else
        print_error "Docker Desktop 与 Colima 均安装失败"
        print_info "请手动安装其一后重试 bootstrap"
        fail=1
      fi
    fi
  fi

  # 4) 启动引擎并等待就绪
  if [ "$engine_mode" = "ready" ]; then
    :
  elif [ "$engine_mode" = "desktop" ] || [ -d "/Applications/Docker.app" ] || [ -d "${HOME}/Applications/Docker.app" ]; then
    print_info "正在启动 Docker Desktop..."
    open -a Docker >/dev/null 2>&1 || true
    local i
    for i in $(seq 1 60); do
      _ensure_mac_tool_paths
      if check_command docker && docker info >/dev/null 2>&1; then
        print_success "Docker Desktop: 引擎已就绪"
        engine_mode="ready"
        break
      fi
      if [ $((i % 5)) -eq 0 ]; then
        print_info "等待 Docker Desktop 启动... (${i}/60)"
        print_info "若弹出权限/许可协议窗口，请在 GUI 中点击允许/接受"
      fi
      sleep 2
    done
    if [ "$engine_mode" != "ready" ]; then
      print_warning "Docker Desktop 引擎尚未就绪，尝试 Colima 回退..."
      engine_mode="colima"
      HOMEBREW_NO_AUTO_UPDATE=1 brew install docker docker-compose colima >/dev/null 2>&1 || true
    fi
  fi

  if [ "$engine_mode" = "colima" ] || { [ "$engine_mode" != "ready" ] && check_command colima; }; then
    print_info "正在启动 Colima（建议 full: 6 CPU / 16GB 内存 / 100GB 磁盘）..."
    if ! colima status 2>/dev/null | grep -qi running; then
      # 若本机无法直连 GitHub，可预先放到 ~/.colima/_images/ 并用 --disk-image
      local local_img="${HOME}/.colima/_images/ubuntu-24.04-minimal-cloudimg-arm64-docker.raw.gz"
      if [ -f "$local_img" ]; then
        print_info "使用本地 Colima 镜像: $local_img"
        colima start --cpu 6 --memory 16 --disk 100 --arch aarch64 --disk-image "$local_img" --downloader curl || fail=1
      else
        print_info "首次启动需下载 VM 镜像；若 GitHub 不可达，可先用镜像站下载到 ~/.colima/_images/"
        colima start --cpu 6 --memory 16 --disk 100 --arch aarch64 --downloader curl || fail=1
      fi
    else
      print_success "Colima 已在运行"
    fi
    docker context use colima >/dev/null 2>&1 || true
    _ensure_mac_tool_paths
    local i
    for i in $(seq 1 30); do
      if check_command docker && docker info >/dev/null 2>&1; then
        print_success "Colima Docker 引擎已就绪"
        engine_mode="ready"
        break
      fi
      sleep 2
    done
    [ "$engine_mode" = "ready" ] || fail=1
  fi

  echo ""
  if [ "$fail" -eq 0 ] && check_command docker && docker info >/dev/null 2>&1; then
    print_success "前置依赖已就绪"
    print_info "当前 Docker: $(docker --version 2>/dev/null | head -n1)  context=$(docker context show 2>/dev/null || echo default)"
    # 与 Linux 对齐：国内 registry-mirrors（FUXA 仍用 pull_fuxa.sh）
    configure_docker_mirror_desktop || true
    # 按部署形态尝试调高 Docker Desktop / Colima 内存（full 默认常仅 ~8GB）
    desktop_configure_resources 0 || true
    print_info "建议下一步："
    print_info "  /opt/homebrew/bin/bash .scripts/docker/install_mac.sh check"
    print_info "  EASYAIOT_DEPLOY_PROFILE=full /opt/homebrew/bin/bash .scripts/docker/install_mac.sh install"
    if [ "${BASH_VERSINFO[0]}" -lt 4 ] && [ -x /opt/homebrew/bin/bash ]; then
      print_warning "当前 shell 仍是 Bash ${BASH_VERSION}；后续请用 /opt/homebrew/bin/bash 执行脚本"
    fi
    return 0
  fi

  print_warning "前置依赖未完全就绪，请按上方提示处理后重试 bootstrap / check"
  return 1
}

show_help() {
  cat <<EOF
${EASYAIOT_INSTALL_LABEL}

使用方法:
  ./install_${EASYAIOT_DESKTOP_OS}.sh                 - 打开交互式引导
  ./install_${EASYAIOT_DESKTOP_OS}.sh [命令]

本脚本仅支持「镜像部署」（拉取预构建镜像后启动），不支持本地编译。

可用命令:
  bootstrap   - 一键安装前置依赖（macOS: Homebrew bash + Docker Desktop；并尝试调资源/镜像源）
  check       - 前置环境自检（打印前置操作清单；缺什么提示装什么）
  mirrors     - 配置 Docker Desktop 国内镜像加速（与 Linux 一致；FUXA 仍走专用脚本）
  resources   - 按部署形态调配 Docker Desktop / Colima 的 CPU/内存/磁盘
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
  profile     - 显示当前部署形态
  menu        - 交互引导
  help        - 显示帮助

说明:
  首次部署请先: bootstrap → check → install
  install / pull / update / start 等会在真正部署前自动做前置检测；
  缺少 Docker Desktop、Compose、Bash 4+、curl 等会打印安装指引并中止。
  resources / bootstrap / install 会按形态尝试调高引擎内存（可用环境变量覆盖）：
    EASYAIOT_DOCKER_MEMORY_GB / EASYAIOT_DOCKER_CPUS / EASYAIOT_DOCKER_DISK_GB
    EASYAIOT_DOCKER_SKIP_RESOURCES=1 可跳过自动调配
  mirrors / bootstrap / install 会写入 ~/.docker/daemon.json 国内 registry-mirrors：
    DOCKER_MIRROR（默认 https://docker.m.daocloud.io）
    DOCKER_MIRROR_FALLBACKS（默认 docker.m.daocloud.io,docker.1ms.run,docker.1panel.live）
    EASYAIOT_DOCKER_SKIP_MIRROR=1 可跳过；FUXA 始终优先 pull_fuxa.sh（1ms）

部署形态（EASYAIOT_DEPLOY_PROFILE）:
  mini(1) / standard(2) / full(3，默认)

不支持的命令（请改用 Linux 服务器脚本）:
  build / build-runtime / clean-build-runtime

示例:
  bash .scripts/docker/install_${EASYAIOT_DESKTOP_OS}.sh bootstrap
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
  echo "  1) 安装前置依赖（bootstrap：bash4 + Docker Desktop）"
  echo "  2) 前置环境自检（打印清单并检测）"
  echo "  3) 配置国内镜像加速（registry-mirrors，对齐 Linux）"
  echo "  4) 调配 Docker 引擎资源（CPU / 内存 / 磁盘）"
  echo "  5) 首次安装并启动（自动拉取预构建镜像）"
  echo "  6) 启动所有服务"
  echo "  7) 停止所有服务"
  echo "  8) 重启所有服务"
  echo "  9) 查看运行状态"
  echo "  10) 查看服务日志"
  echo "  11) 验证服务健康"
  echo "  12) 拉取最新镜像并更新"
  echo "  13) 仅拉取预构建镜像"
  echo "  14) 查看部署形态"
  echo "  15) 完整命令行帮助"
  echo ""
  echo "  0) 返回上级菜单"
  echo ""
}

run_desktop_deploy_menu() {
  local choice=""
  while true; do
    _print_desktop_deploy_header
    read -r -p "请输入部署选项 [0-15]: " choice || choice=""
    [ -z "$choice" ] && continue
    case "$choice" in
      1) easyaiot_run_command bootstrap ;;
      2) easyaiot_run_command check ;;
      3) easyaiot_run_command mirrors ;;
      4) easyaiot_run_command resources ;;
      5) easyaiot_run_command install ;;
      6) easyaiot_run_command start ;;
      7) easyaiot_run_command stop ;;
      8) easyaiot_run_command restart ;;
      9) easyaiot_run_command status ;;
      10) easyaiot_run_command logs ;;
      11) easyaiot_run_command verify ;;
      12) easyaiot_run_command update ;;
      13) easyaiot_run_command pull ;;
      14) easyaiot_run_command profile ;;
      15) show_help ;;
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
    bootstrap|deps) desktop_bootstrap ;;
    resources|tune|tune-resources|docker-resources)
      require_desktop_prerequisites
      # force：传 force/1/-f 时即使已达标也重写配置并重启
      if [ "${2:-}" = "force" ] || [ "${2:-}" = "1" ] || [ "${2:-}" = "-f" ] || [ "${2:-}" = "--force" ]; then
        desktop_configure_resources 1
      else
        desktop_configure_resources 0
      fi
      ;;
    mirrors|mirror|registry-mirrors|docker-mirrors)
      require_desktop_prerequisites
      configure_docker_mirror_desktop
      ;;
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
