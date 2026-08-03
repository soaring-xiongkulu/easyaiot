# shellcheck shell=bash
# 共享 Docker registry-mirrors + DNS 配置（供 install_linux_kylin / business 等脚本 source）
# 调用方需提供: check_command, print_info, print_success, print_warning, print_error
# （若未提供 check_command / print_*，本文件提供简易回退）
#
# 环境变量:
#   DOCKER_MIRROR   镜像源，默认 DaoCloud 公共镜像（国内较稳）；可用华为云 SWR 加速器覆盖:
#                   https://<id>.mirror.swr.myhuaweicloud.com
#   DOCKER_DNS      逗号分隔 DNS，默认 223.5.5.5,119.29.29.29（阿里/腾讯）
#   EASYAIOT_FORCE_DOCKER_DNS=1  强制写入 daemon.json DNS（即使 resolv.conf 非 loopback）
#   EASYAIOT_FORCE_HOST_DNS=1    强制重写宿主机 /etc/resolv.conf

if ! declare -f check_command >/dev/null 2>&1; then
    check_command() { command -v "$1" >/dev/null 2>&1; }
fi
if ! declare -f print_info >/dev/null 2>&1; then
    print_info() { echo "[INFO] $1"; }
fi
if ! declare -f print_success >/dev/null 2>&1; then
    print_success() { echo "[OK] $1"; }
fi
if ! declare -f print_warning >/dev/null 2>&1; then
    print_warning() { echo "[WARN] $1"; }
fi
if ! declare -f print_error >/dev/null 2>&1; then
    print_error() { echo "[ERR] $1" >&2; }
fi

# 默认公共代理：DaoCloud 优先（1panel 对部分仓库 HEAD/pull 常 403）
# 华为云专属加速器用 DOCKER_MIRROR 覆盖
DOCKER_MIRROR="${DOCKER_MIRROR:-https://docker.m.daocloud.io}"
# 拉取回退链（逗号分隔主机名，不含协议）；可通过 DOCKER_MIRROR_FALLBACKS 覆盖
DOCKER_MIRROR_FALLBACKS="${DOCKER_MIRROR_FALLBACKS:-docker.m.daocloud.io,docker.1ms.run,docker.1panel.live}"
# 国内公网 DNS；麒麟等系统 /etc/resolv.conf 常指向 ::1/127.0.0.53，Docker 内无法使用
DOCKER_DNS="${DOCKER_DNS:-223.5.5.5,119.29.29.29}"

restart_docker_if_active() {
    if ! check_command systemctl; then
        print_warning "未找到 systemctl，跳过重启 Docker（容器或非 systemd 环境）"
        return 0
    fi
    if systemctl is-active --quiet docker 2>/dev/null; then
        print_info "正在重启 Docker 服务以使配置生效..."
        systemctl daemon-reload 2>/dev/null || true
        if systemctl restart docker 2>/dev/null; then
            print_success "Docker 服务已重启"
        else
            print_warning "Docker 重启失败，请稍后手动执行: sudo systemctl restart docker"
        fi
    fi
}

# 宿主机 resolv.conf 是否指向 loopback（Docker 守护进程无法用此类 DNS）
_host_resolv_uses_loopback_dns() {
    [ -f /etc/resolv.conf ] || return 1
    grep -Eiq '^\s*nameserver\s+(127\.|::1)' /etc/resolv.conf 2>/dev/null
}

# 是否应在 daemon.json 写入公网 DNS
_should_configure_docker_dns() {
    [ "${EASYAIOT_FORCE_DOCKER_DNS:-0}" = "1" ] && return 0
    _host_resolv_uses_loopback_dns && return 0
    # 麒麟/统信等国产系统常见 DNS 异常，默认补齐
    if [ -f /etc/os-release ] && grep -Eiq 'kylin|uos|openEuler|UnionTech' /etc/os-release 2>/dev/null; then
        return 0
    fi
    return 1
}

# 配置 Docker 镜像源 +（按需）DNS
# 优先 python3 合并 JSON；无 python3 时用 jq；皆无则仅在文件不存在时写最小配置
configure_docker_mirror() {
    print_info "配置 Docker 镜像源..."

    local config_file="/etc/docker/daemon.json"
    local want_dns=0
    local dns_csv="$DOCKER_DNS"

    # PANEL 容器内写 /etc/docker 不影响宿主机 dockerd
    if [ -f /.dockerenv ] || { [ -r /proc/1/cgroup ] && grep -Eq '(docker|containerd|kubepods|/libpod)' /proc/1/cgroup 2>/dev/null; }; then
        print_info "容器环境跳过写入宿主机 Docker 镜像源（请在宿主机配置 /etc/docker/daemon.json）"
        return 0
    fi

    if _should_configure_docker_dns; then
        want_dns=1
        print_info "将配置 Docker DNS: ${dns_csv}（避免守护进程使用 ::1/127.0.0.53 导致拉取失败）"
    fi

    if [ "${EUID:-$(id -u)}" -ne 0 ]; then
        print_warning "配置 Docker 镜像源需要 root 权限，跳过此步骤"
        return 0
    fi
    mkdir -p /etc/docker

    if [ ! -f "$config_file" ]; then
        local wrote=0
        if [ "$want_dns" -eq 1 ] && check_command python3; then
            if python3 - "$config_file" "$DOCKER_MIRROR" "$dns_csv" <<'PYEOF'
import json, sys
path, mirror, dns_csv = sys.argv[1], sys.argv[2], sys.argv[3]
dns = [x.strip() for x in dns_csv.split(",") if x.strip()]
json.dump({"registry-mirrors": [mirror], "dns": dns}, open(path, "w"), indent=2, ensure_ascii=False)
PYEOF
            then
                wrote=1
            fi
        fi
        if [ "$wrote" -eq 0 ]; then
            if [ "$want_dns" -eq 1 ]; then
                local dns_json
                dns_json=$(echo "$dns_csv" | awk -F',' '{
                  printf "["
                  for (i=1;i<=NF;i++) { gsub(/^[ \t]+|[ \t]+$/,"",$i); if($i!=""){ if(n++)printf ", "; printf "\"%s\"", $i } }
                  printf "]"
                }')
                printf '{\n  "registry-mirrors": ["%s"],\n  "dns": %s\n}\n' "$DOCKER_MIRROR" "$dns_json" > "$config_file"
            else
                printf '{\n  "registry-mirrors": ["%s"]\n}\n' "$DOCKER_MIRROR" > "$config_file"
            fi
        fi
        print_success "已写入 Docker 镜像源配置: $DOCKER_MIRROR"
        [ "$want_dns" -eq 1 ] && print_success "已写入 Docker DNS: $dns_csv"
        restart_docker_if_active
        return 0
    fi

    if check_command python3; then
        local rc=0
        python3 - "$config_file" "$DOCKER_MIRROR" "$want_dns" "$dns_csv" <<'PYEOF' || rc=$?
import json, sys
path, mirror, want_dns, dns_csv = sys.argv[1], sys.argv[2], sys.argv[3] == "1", sys.argv[4]
cfg = json.load(open(path))
changed = False

# mirrors: 规整为唯一目标源
cur = [m.rstrip("/") for m in cfg.get("registry-mirrors", []) if isinstance(m, str)]
if cur != [mirror.rstrip("/")]:
    cfg["registry-mirrors"] = [mirror]
    changed = True

# dns: 仅在需要且尚未配置（或仍是 loopback）时写入
if want_dns:
    dns = [x.strip() for x in dns_csv.split(",") if x.strip()]
    existing = cfg.get("dns") if isinstance(cfg.get("dns"), list) else []
    existing_norm = [str(x).strip() for x in existing]
    loopback = any(x.startswith("127.") or x in ("::1",) for x in existing_norm)
    if not existing_norm or loopback or existing_norm != dns:
        if existing_norm != dns:
            cfg["dns"] = dns
            changed = True

if not changed:
    sys.exit(0)
json.dump(cfg, open(path, "w"), indent=2, ensure_ascii=False)
sys.exit(3)
PYEOF
        case $rc in
            0)
                print_success "Docker 镜像源配置已就绪（$DOCKER_MIRROR）"
                [ "$want_dns" -eq 1 ] && print_success "Docker DNS 配置已就绪（$dns_csv）"
                ;;
            3)
                print_success "Docker 镜像源已更新为 $DOCKER_MIRROR"
                [ "$want_dns" -eq 1 ] && print_success "Docker DNS 已更新为 $dns_csv"
                restart_docker_if_active
                ;;
            *)
                print_error "解析 $config_file 失败（非法 JSON？），请手动检查"
                return 1
                ;;
        esac
        return 0
    fi

    if check_command jq; then
        local tmp_json
        tmp_json=$(mktemp)
        if [ "$want_dns" -eq 1 ]; then
            # shellcheck disable=SC2016
            if ! jq --arg m "$DOCKER_MIRROR" --arg csv "$dns_csv" '
                .["registry-mirrors"] = [$m]
                | .dns = ($csv | split(",") | map(gsub("^\\s+|\\s+$";"")) | map(select(length>0)))
              ' "$config_file" > "$tmp_json" 2>/dev/null; then
                rm -f "$tmp_json"
                print_error "解析 $config_file 失败（非法 JSON？），请手动检查"
                return 1
            fi
        else
            if ! jq --arg m "$DOCKER_MIRROR" '.["registry-mirrors"] = [$m]' "$config_file" > "$tmp_json" 2>/dev/null; then
                rm -f "$tmp_json"
                print_error "解析 $config_file 失败（非法 JSON？），请手动检查"
                return 1
            fi
        fi
        if cmp -s "$config_file" "$tmp_json" 2>/dev/null; then
            rm -f "$tmp_json"
            print_success "Docker 镜像源配置已就绪（$DOCKER_MIRROR）"
            return 0
        fi
        mv "$tmp_json" "$config_file"
        print_success "Docker 镜像源已更新为 $DOCKER_MIRROR"
        [ "$want_dns" -eq 1 ] && print_success "Docker DNS 已更新为 $dns_csv"
        restart_docker_if_active
        return 0
    fi

    print_warning "未安装 jq/python3 且 $config_file 已存在，跳过自动配置（请手动确认 registry-mirrors 含 $DOCKER_MIRROR，并建议添加 dns: [\"223.5.5.5\",\"119.29.29.29\"]）"
}

# ---------------------------------------------------------------------------
# Docker Desktop（macOS / Windows）：写入用户级 ~/.docker/daemon.json
# 与 Linux configure_docker_mirror 同源（DOCKER_MIRROR / DOCKER_MIRROR_FALLBACKS）
#
# 说明：
#   - registry-mirrors 主要加速 docker.io（中间件官方镜像）
#   - FUXA 不走 DaoCloud 优先：compose 固定 docker.1panel.live/...，拉取见 pull_fuxa.sh（1ms 优先）
#   - 业务预构建镜像在 docker.cnb.cool，不受 registry-mirrors 影响
#   - 跳过：EASYAIOT_DOCKER_SKIP_MIRROR=1
# ---------------------------------------------------------------------------
_desktop_daemon_json_path() {
    if [ -n "${DOCKER_CONFIG:-}" ]; then
        echo "${DOCKER_CONFIG}/daemon.json"
        return
    fi
    # Windows Git Bash：优先 USERPROFILE；WSL 内尽量落到 Windows 用户目录
    if _is_windows_docker_desktop_env 2>/dev/null || [ "${EASYAIOT_DESKTOP_OS:-}" = "windows" ]; then
        local win_home="${USERPROFILE:-}"
        if [ -z "$win_home" ] && command -v cmd.exe >/dev/null 2>&1; then
            win_home=$(cmd.exe /c "echo %USERPROFILE%" 2>/dev/null | tr -d '\r')
        fi
        if [ -n "$win_home" ]; then
            # C:\Users\x → /c/Users/x（Git Bash）或 /mnt/c/Users/x（WSL）
            if command -v cygpath >/dev/null 2>&1; then
                echo "$(cygpath -u "$win_home")/.docker/daemon.json"
                return
            fi
            if command -v wslpath >/dev/null 2>&1 && [[ "$win_home" == [A-Za-z]:* ]]; then
                echo "$(wslpath -u "$win_home")/.docker/daemon.json"
                return
            fi
            if [[ "$win_home" == [A-Za-z]:* ]]; then
                local drive="${win_home:0:1}"
                local rest="${win_home:2}"
                rest="${rest//\\//}"
                if [ -d "/mnt/${drive,,}" ]; then
                    echo "/mnt/${drive,,}${rest}/.docker/daemon.json"
                else
                    echo "/${drive,,}${rest}/.docker/daemon.json"
                fi
                return
            fi
        fi
    fi
    echo "${HOME}/.docker/daemon.json"
}

# 合并写入 Desktop daemon.json；若有变更返回 0 且 stdout 打印 changed；已就绪返回 0 打印 ok；失败返回 1
_merge_desktop_daemon_mirrors() {
    local config_file="$1"
    local primary="${DOCKER_MIRROR:-https://docker.m.daocloud.io}"
    primary="${primary%/}"
    if [[ "$primary" != http://* && "$primary" != https://* ]]; then
        primary="https://${primary}"
    fi

    # Desktop 写入主源 + 回退链（与 Linux 拉取出处一致；引擎按序尝试）
    local hosts=("$primary")
    local h
    IFS=',' read -r -a _fb <<< "${DOCKER_MIRROR_FALLBACKS:-docker.m.daocloud.io,docker.1ms.run,docker.1panel.live}"
    for h in "${_fb[@]}"; do
        h="${h#https://}"
        h="${h#http://}"
        h="${h%/}"
        h="${h// /}"
        [ -z "$h" ] && continue
        local url="https://${h}"
        local dup=0 x
        for x in "${hosts[@]}"; do
            [ "${x%/}" = "${url%/}" ] && dup=1 && break
        done
        [ "$dup" -eq 0 ] && hosts+=("$url")
    done

    mkdir -p "$(dirname "$config_file")"
    if ! check_command python3; then
        print_warning "未找到 python3，无法自动写入 Desktop daemon.json"
        print_info "请在 Docker Desktop → Settings → Docker Engine 手动添加 registry-mirrors: ${hosts[*]}"
        return 1
    fi

    local mirrors_arg
    mirrors_arg=$(IFS=','; echo "${hosts[*]}")
    python3 - "$config_file" "$mirrors_arg" <<'PY'
import json, sys, os, shutil
path, mirrors_csv = sys.argv[1], sys.argv[2]
want = []
for m in mirrors_csv.split(","):
    m = m.strip().rstrip("/")
    if not m:
        continue
    if not m.startswith("http://") and not m.startswith("https://"):
        m = "https://" + m
    want.append(m)

if os.path.exists(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except Exception:
        bak = path + ".easyaiot.broken.bak"
        shutil.copy2(path, bak)
        cfg = {}
else:
    cfg = {}

cur = cfg.get("registry-mirrors") if isinstance(cfg.get("registry-mirrors"), list) else []
cur_norm = [str(x).rstrip("/") for x in cur]
want_norm = [str(x).rstrip("/") for x in want]
if cur_norm == want_norm:
    print("ok")
    sys.exit(0)

bak = path + ".easyaiot.bak"
if os.path.exists(path) and not os.path.exists(bak):
    shutil.copy2(path, bak)
cfg["registry-mirrors"] = want
with open(path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("changed")
PY
}

_restart_docker_desktop_for_mirror() {
    print_info "重启 Docker Desktop 以使 registry-mirrors 生效..."
    if [ "$(uname -s 2>/dev/null)" = "Darwin" ] || [ "${EASYAIOT_DESKTOP_OS:-}" = "mac" ]; then
        osascript -e 'quit app "Docker"' >/dev/null 2>&1 || true
        sleep 3
        pkill -f 'Docker Desktop' >/dev/null 2>&1 || true
        pkill -f com.docker.backend >/dev/null 2>&1 || true
        sleep 2
        open -a Docker >/dev/null 2>&1 || true
    elif command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -ExecutionPolicy Bypass -Command @'
$ErrorActionPreference = "SilentlyContinue"
Get-Process "Docker Desktop","com.docker.backend" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
if (Get-Command wsl.exe -ErrorAction SilentlyContinue) { wsl.exe --shutdown 2>$null }
$exes = @(
  "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
  "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
  "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
)
foreach ($e in $exes) { if (Test-Path $e) { Start-Process $e; break } }
'@ >/dev/null 2>&1 || true
    else
        print_warning "请手动重启 Docker Desktop 后执行: docker info | grep -A5 Mirrors"
        return 1
    fi
    local i
    for i in $(seq 1 90); do
        if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
            print_success "Docker 引擎已重新就绪"
            return 0
        fi
        [ $((i % 10)) -eq 0 ] && print_info "等待 Docker 重启... (${i}/90)"
        sleep 2
    done
    print_warning "Docker 重启后尚未就绪，请手动打开 Docker Desktop"
    return 1
}

# 配置 Docker Desktop 国内镜像加速（对齐 Linux；FUXA 仍走 pull_fuxa.sh）
configure_docker_mirror_desktop() {
    if [ "${EASYAIOT_DOCKER_SKIP_MIRROR:-0}" = "1" ]; then
        print_info "已设置 EASYAIOT_DOCKER_SKIP_MIRROR=1，跳过 Desktop 镜像源配置"
        return 0
    fi

    print_info "配置 Docker Desktop 国内镜像源（与 Linux 一致）..."
    print_info "  主源: ${DOCKER_MIRROR:-https://docker.m.daocloud.io}"
    print_info "  回退: ${DOCKER_MIRROR_FALLBACKS:-docker.m.daocloud.io,docker.1ms.run,docker.1panel.live}"
    print_info "  FUXA: 专用 pull_fuxa.sh（1ms 优先；DaoCloud 对 frangoteam 常 403）"

    local config_file status
    config_file=$(_desktop_daemon_json_path)
    status=$(_merge_desktop_daemon_mirrors "$config_file") || {
        print_warning "Desktop daemon.json 写入失败: $config_file"
        return 1
    }

    case "$status" in
        ok)
            print_success "Docker Desktop 镜像源已就绪: $config_file"
            ;;
        changed)
            print_success "已写入 registry-mirrors → $config_file"
            if [ "${EASYAIOT_DOCKER_SKIP_MIRROR_RESTART:-0}" = "1" ]; then
                print_warning "已跳过自动重启（EASYAIOT_DOCKER_SKIP_MIRROR_RESTART=1）；请手动重启 Docker Desktop"
            else
                _restart_docker_desktop_for_mirror || true
            fi
            ;;
        *)
            print_warning "未知合并结果: $status"
            return 1
            ;;
    esac

    # 展示生效情况
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        local mirrors_line
        mirrors_line=$(docker info 2>/dev/null | grep -A8 -i 'Registry Mirrors' || true)
        if [ -n "$mirrors_line" ]; then
            print_info "当前 Registry Mirrors:"
            echo "$mirrors_line" | sed 's/^/  /'
        else
            print_warning "docker info 尚未显示 Registry Mirrors；若刚写入请确认 Desktop 已完全重启"
        fi
    fi
    return 0
}

# 从国内镜像前缀直连拉取并 tag 回原名（registry-mirrors 失效时的回退）
# 用法: docker_pull_with_mirror_fallback [--platform linux/arm64] image:tag
#
# 支持目标已是「镜像站/官方路径」形式（如 docker.1panel.live/frangoteam/fuxa:1.3.3）：
# 主源 403 时会剥离已知镜像站前缀，再按回退链拉取官方路径并 tag 回原名。
docker_pull_with_mirror_fallback() {
    local platform_args=()
    while [ $# -gt 0 ]; do
        case "$1" in
            --platform)
                platform_args=(--platform "$2")
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    local img="${1:-}"
    [ -n "$img" ] || return 1

    export DOCKER_CONTENT_TRUST=0

    if docker image inspect "$img" &>/dev/null; then
        return 0
    fi

    if docker pull "${platform_args[@]}" "$img"; then
        return 0
    fi

    local primary="${DOCKER_MIRROR_HOST:-}"
    if [ -z "$primary" ]; then
        primary="${DOCKER_MIRROR:-https://docker.m.daocloud.io}"
    fi
    primary="${primary#https://}"
    primary="${primary#http://}"
    primary="${primary%/}"

    local hosts=()
    local h
    # 主源优先
    [ -n "$primary" ] && hosts+=("$primary")
    # 回退链
    IFS=',' read -r -a _fb <<< "${DOCKER_MIRROR_FALLBACKS:-docker.m.daocloud.io,docker.1ms.run,docker.1panel.live}"
    for h in "${_fb[@]}"; do
        h="${h#https://}"
        h="${h#http://}"
        h="${h%/}"
        h="${h// /}"
        [ -z "$h" ] && continue
        local dup=0
        local x
        for x in "${hosts[@]}"; do
            [ "$x" = "$h" ] && dup=1 && break
        done
        [ "$dup" -eq 0 ] && hosts+=("$h")
    done
    # 本机常见可用代理也纳入尝试（不写入 daemon，仅拉取回退）
    for h in proxy.vvvv.ee dockerproxy.com; do
        dup=0
        for x in "${hosts[@]}"; do
            [ "$x" = "$h" ] && dup=1 && break
        done
        [ "$dup" -eq 0 ] && hosts+=("$h")
    done

    # 剥离已知镜像站前缀，得到官方路径（frangoteam/fuxa:1.3.3 / library/redis:7 等）
    local canonical="$img"
    local known_mirrors=(
        docker.m.daocloud.io docker.1ms.run docker.1panel.live
        proxy.vvvv.ee dockerproxy.com docker.mirrors.ustc.edu.cn
        hub-mirror.c.163.com mirror.ccs.tencentyun.com
    )
    for h in "${hosts[@]}" "${known_mirrors[@]}"; do
        [ -z "$h" ] && continue
        if [[ "$canonical" == "$h"/* ]]; then
            canonical="${canonical#${h}/}"
            # DaoCloud/部分源对官方库使用 library/ 前缀
            break
        fi
    done
    # library/xxx → 再尝试无 library 的官方短名本地标签
    local canonical_nolib="$canonical"
    if [[ "$canonical_nolib" == library/* ]]; then
        canonical_nolib="${canonical_nolib#library/}"
    fi

    # 本地已有其它镜像站同内容时，直接 tag，避免再拉
    local alt
    for h in "${hosts[@]}" "${known_mirrors[@]}"; do
        [ -z "$h" ] && continue
        for alt in "${h}/${canonical}" "${h}/${canonical_nolib}" "$canonical" "$canonical_nolib"; do
            [ -z "$alt" ] && continue
            [ "$alt" = "$img" ] && continue
            if docker image inspect "$alt" &>/dev/null; then
                docker tag "$alt" "$img" 2>/dev/null || true
                if docker image inspect "$img" &>/dev/null; then
                    print_success "已用本地镜像 $alt 标记为 $img"
                    return 0
                fi
            fi
        done
    done

    local mirror_host c
    for mirror_host in "${hosts[@]}"; do
        for c in "${mirror_host}/${canonical}" "${mirror_host}/${canonical_nolib}"; do
            [ -z "$c" ] && continue
            [ "$c" = "$img" ] && continue
            # 已是该镜像站完整路径且刚才 pull 失败过则跳过重复
            if [[ "$img" == "$mirror_host"/* ]] && [ "$c" = "$img" ]; then
                continue
            fi
            print_info "镜像源直连回退拉取: $c"
            if docker pull "${platform_args[@]}" "$c"; then
                docker tag "$c" "$img" 2>/dev/null || true
                print_success "已拉取并标记为 $img"
                return 0
            fi
        done
    done
    return 1
}

# ---------------------------------------------------------------------------
# 宿主机 DNS 修复（关键）
# daemon.json 的 "dns" 只影响容器内解析，不影响 dockerd 自己拉镜像时的域名解析。
# 错误形态: lookup xxx on [::1]:53: connection refused
# 原因: /etc/resolv.conf 指向 ::1 / 127.0.0.53，但本机 53 端口无服务或不可用。
#
# Windows / Git Bash / Docker Desktop：
#   Git Bash 的 /etc/resolv.conf 与 Docker Desktop（WSL2 VM）无关，不能按 Linux
#   方式改 resolv.conf；应检测 Windows 本机 DNS，或直接探测 docker 引擎解析能力。
# ---------------------------------------------------------------------------

_dns_print_info() { if declare -f print_info >/dev/null 2>&1; then print_info "$1"; else echo "[INFO] $1"; fi; }
_dns_print_ok() { if declare -f print_success >/dev/null 2>&1; then print_success "$1"; else echo "[OK] $1"; fi; }
_dns_print_warn() { if declare -f print_warning >/dev/null 2>&1; then print_warning "$1"; else echo "[WARN] $1"; fi; }
_dns_print_err() { if declare -f print_error >/dev/null 2>&1; then print_error "$1"; else echo "[ERROR] $1"; fi; }

# 是否为 Windows 桌面部署环境（Git Bash / MSYS / Cygwin / 强制标记 / WSL 跑 install_windows）
_is_windows_docker_desktop_env() {
    [ "${EASYAIOT_FORCE_WINDOWS:-0}" = "1" ] && return 0
    [ "${EASYAIOT_DESKTOP_OS:-}" = "windows" ] && return 0
    case "$(uname -s 2>/dev/null)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
    esac
    return 1
}

# 返回当前 resolv.conf 中的 nameserver 列表（空格分隔）
_host_nameservers() {
    [ -f /etc/resolv.conf ] || return 0
    awk 'BEGIN{IGNORECASE=1} /^[[:space:]]*nameserver[[:space:]]+/ {print $2}' /etc/resolv.conf 2>/dev/null | tr '\n' ' '
}

# Windows 本机能否解析域名（优先 nslookup.exe / PowerShell，不依赖 Git Bash resolv.conf）
_windows_host_dns_can_resolve() {
    local host="${1:-docker.cnb.cool}"
    local out=""

    if command -v nslookup.exe >/dev/null 2>&1; then
        out="$(nslookup.exe "$host" 2>&1 || true)"
        echo "$out" | grep -Eqi 'Name:|Addresses?:|Address:' && \
            ! echo "$out" | grep -Eqi "can't find|Non-existent|NXDOMAIN|找不到" && return 0
    elif command -v nslookup >/dev/null 2>&1; then
        out="$(nslookup "$host" 2>&1 || true)"
        echo "$out" | grep -Eqi 'Name:|Addresses?:|Address:' && \
            ! echo "$out" | grep -Eqi "can't find|Non-existent|NXDOMAIN|找不到" && return 0
    fi

    if command -v powershell.exe >/dev/null 2>&1; then
        powershell.exe -NoProfile -Command \
            "try { [void][System.Net.Dns]::GetHostAddresses('${host}'); exit 0 } catch { exit 1 }" \
            >/dev/null 2>&1 && return 0
    fi

    # Windows ping：无 -c/-W；成功时输出含 TTL=
    if command -v ping.exe >/dev/null 2>&1; then
        ping.exe -n 1 -w 2000 "$host" 2>&1 | grep -Eqi 'TTL=|Reply from|来自' && return 0
    fi
    return 1
}

# Docker 引擎侧能否解析（比 Git Bash getent 更贴近真实 pull）
_docker_engine_dns_can_resolve() {
    local host="${1:-docker.cnb.cool}"
    command -v docker >/dev/null 2>&1 || return 1
    # 用业务仓库路径做轻量 inspect（触发 dockerd 域名解析，不真正落盘大镜像）
    local probe_ref="${host}/soaring-xiongkulu/easyaiot/aiot-web:latest"
    local err=""
    err="$(docker manifest inspect "$probe_ref" 2>&1 || true)"
    # DNS/连接拒绝算失败
    if echo "$err" | grep -Eqi 'lookup .*(:53|connection refused)|no such host|Temporary failure in name resolution|Could not resolve host|Dial .*no such host'; then
        return 1
    fi
    # 能连上仓库（成功/401/404/TLS 等）说明 DNS 已通
    if [ -z "$err" ]; then
        return 0
    fi
    if echo "$err" | grep -Eqi 'unauthorized|denied|not found|no such manifest|manifest unknown|TOOMANYREQUESTS|timeout|TLS|x509|mediaType|schemaVersion|digest|sha256|http:|401|403|404'; then
        return 0
    fi
    # 其它错误偏保守：交由上层（本机 DNS 已通则可继续）
    return 1
}

# 宿主机能否解析外部域名（Linux 用 resolv.conf；Windows 用本机解析器）
_host_dns_can_resolve() {
    local host="${1:-docker.cnb.cool}"
    if _is_windows_docker_desktop_env; then
        _windows_host_dns_can_resolve "$host" && return 0
        return 1
    fi
    if command -v getent >/dev/null 2>&1; then
        getent hosts "$host" >/dev/null 2>&1 && return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$host" <<'PY' 2>/dev/null && return 0
import socket, sys
socket.getaddrinfo(sys.argv[1], 443, proto=socket.IPPROTO_TCP)
PY
    fi
    if command -v ping >/dev/null 2>&1; then
        ping -c 1 -W 2 "$host" >/dev/null 2>&1 && return 0
    fi
    return 1
}

_print_windows_dns_fix_guide() {
    _dns_print_err "Docker Desktop 无法解析镜像仓库域名"
    _dns_print_info "Git Bash 的 /etc/resolv.conf 与 Docker Desktop 无关，请勿按 Linux 方式修改。"
    echo ""
    echo "请按下列步骤排查后重试："
    echo "----------------------------------------"
    cat <<'EOF'
1) 在 PowerShell 验证本机 DNS:
   Resolve-DnsName docker.cnb.cool
   nslookup docker.cnb.cool

2) 验证 Docker 能否拉取:
   docker pull docker.cnb.cool/soaring-xiongkulu/easyaiot/aiot-web:latest

3) 若本机可解析但 docker pull 报 lookup ... :53:
   - 打开 Docker Desktop → Settings → Docker Engine
   - 增加（可与现有项合并）:
     {
       "dns": ["223.5.5.5", "119.29.29.29", "114.114.114.114"]
     }
   - Apply & Restart 后重试

4) 检查 Windows「以太网/WLAN → 属性 → IPv4 → DNS」是否可用，
   或临时设为 223.5.5.5 / 119.29.29.29
EOF
    echo "----------------------------------------"
}

_print_host_dns_fix_guide() {
    if _is_windows_docker_desktop_env; then
        _print_windows_dns_fix_guide
        return 0
    fi
    _dns_print_err "Docker 无法解析域名（典型: lookup ... on [::1]:53 connection refused）"
    _dns_print_info "这是宿主机 DNS 故障，不是镜像仓库或 registry-mirrors 问题。"
    _dns_print_info "daemon.json 里的 dns 只影响容器，不能修复 docker pull。"
    echo ""
    echo "请用 root 执行以下命令后重试："
    echo "----------------------------------------"
    cat <<'EOF'
# 备份并重写宿主机 DNS（麒麟/ARM 常用）
sudo cp -a /etc/resolv.conf /etc/resolv.conf.bak.$(date +%Y%m%d%H%M%S)
# 若是符号链接，先拆掉再写实体文件
if [ -L /etc/resolv.conf ]; then
  sudo rm -f /etc/resolv.conf
fi
sudo tee /etc/resolv.conf >/dev/null <<'DNS'
nameserver 223.5.5.5
nameserver 119.29.29.29
nameserver 114.114.114.114
DNS

# 验证
getent hosts docker.cnb.cool || ping -c 1 docker.cnb.cool

# 可选：同步写 daemon.json（仅影响容器内 DNS）
sudo tee /etc/docker/daemon.json >/dev/null <<'JSON'
{
  "registry-mirrors": ["https://docker.m.daocloud.io/"],
  "dns": ["223.5.5.5", "119.29.29.29"]
}
JSON
sudo systemctl restart docker

# 再拉一次验证
docker pull docker.cnb.cool/soaring-xiongkulu/easyaiot/aiot-web:arm64
EOF
    echo "----------------------------------------"
}

# Windows / Docker Desktop：不改 /etc/resolv.conf，只验证本机 DNS + 引擎解析
_ensure_windows_docker_desktop_dns() {
    local test_host="${1:-docker.cnb.cool}"

    if _windows_host_dns_can_resolve "$test_host"; then
        _dns_print_ok "Windows 本机 DNS 正常（可解析 ${test_host}）"
        # 再轻量确认引擎侧；失败仅警告，不因 Git Bash 误判中止
        if command -v docker >/dev/null 2>&1; then
            if _docker_engine_dns_can_resolve "$test_host"; then
                _dns_print_ok "Docker Desktop 引擎 DNS 可用"
            else
                _dns_print_warn "本机可解析 ${test_host}，继续拉取；若 pull 失败请检查 Docker Desktop DNS 设置"
            fi
        fi
        return 0
    fi

    _dns_print_warn "Windows 本机暂时无法解析 ${test_host}，改用 Docker 引擎探测..."
    if _docker_engine_dns_can_resolve "$test_host"; then
        _dns_print_ok "Docker Desktop 引擎可解析 ${test_host}，继续拉取"
        return 0
    fi

    _print_windows_dns_fix_guide
    return 1
}

# 修复宿主机 /etc/resolv.conf（及 systemd-resolved），使 dockerd 能解析外网域名
# 返回 0=可用；1=仍不可用（已打印修复指引）
ensure_host_dns_for_docker() {
    local test_host="${1:-docker.cnb.cool}"
    local dns_list="${DOCKER_DNS:-223.5.5.5,119.29.29.29,114.114.114.114}"
    local ns
    ns="$(_host_nameservers)"

    # Windows Desktop：Git Bash resolv.conf 无效，走专用路径
    if _is_windows_docker_desktop_env; then
        _ensure_windows_docker_desktop_dns "$test_host"
        return $?
    fi

    if _host_dns_can_resolve "$test_host"; then
        if [ "${EASYAIOT_FORCE_HOST_DNS:-0}" != "1" ]; then
            _dns_print_ok "宿主机 DNS 正常（可解析 ${test_host}），nameserver: ${ns:-未知}"
            return 0
        fi
    else
        _dns_print_warn "宿主机无法解析 ${test_host}（当前 nameserver: ${ns:-无}）"
    fi

    if echo " $ns " | grep -Eq ' (::1|127\.)'; then
        _dns_print_warn "检测到 loopback DNS（::1/127.x），dockerd 拉镜像会失败，正在修复..."
    fi

    if [ "${EUID:-$(id -u)}" -ne 0 ]; then
        _dns_print_warn "修复宿主机 DNS 需要 root，当前非 root，跳过自动修复"
        _print_host_dns_fix_guide
        return 1
    fi

    # 优先配置 systemd-resolved（若在跑）
    if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
        local resolved_conf="/etc/systemd/resolved.conf"
        mkdir -p /etc/systemd
        if [ -f "$resolved_conf" ]; then
            cp -a "$resolved_conf" "${resolved_conf}.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
        fi
        local dns_space
        dns_space=$(echo "$dns_list" | tr ',' ' ')
        if [ ! -f "$resolved_conf" ]; then
            printf '[Resolve]\nDNS=%s\nFallbackDNS=114.114.114.114\n' "$dns_space" > "$resolved_conf"
        elif grep -qE '^\s*DNS=' "$resolved_conf" 2>/dev/null; then
            sed -i -E "s|^\s*DNS=.*|DNS=${dns_space}|" "$resolved_conf"
        elif grep -qE '^\s*\[Resolve\]' "$resolved_conf" 2>/dev/null; then
            sed -i -E "/^\s*\[Resolve\]/a DNS=${dns_space}" "$resolved_conf"
        else
            printf '\n[Resolve]\nDNS=%s\nFallbackDNS=114.114.114.114\n' "$dns_space" >> "$resolved_conf"
        fi
        systemctl restart systemd-resolved 2>/dev/null || true
        _dns_print_info "已更新 systemd-resolved DNS: ${dns_space}"
    fi

    # 写实体 /etc/resolv.conf（若是指向 stub 的坏链接则替换）
    local backup="/etc/resolv.conf.bak.easyaiot.$(date +%Y%m%d%H%M%S)"
    if [ -e /etc/resolv.conf ] || [ -L /etc/resolv.conf ]; then
        cp -a /etc/resolv.conf "$backup" 2>/dev/null || true
        _dns_print_info "已备份 /etc/resolv.conf → $backup"
    fi
    if [ -L /etc/resolv.conf ]; then
        rm -f /etc/resolv.conf
    fi

    {
        echo "# Generated by EasyAIoT ensure_host_dns_for_docker ($(date '+%F %T'))"
        echo "# Previous backup: ${backup}"
        local d
        local _dns_arr
        IFS=',' read -ra _dns_arr <<< "$dns_list"
        for d in "${_dns_arr[@]}"; do
            d=$(echo "$d" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            [ -n "$d" ] && echo "nameserver $d"
        done
        echo "options timeout:2 attempts:3"
    } > /etc/resolv.conf
    chmod 644 /etc/resolv.conf
    _dns_print_ok "已写入宿主机 DNS: $dns_list"

    sleep 1

    if _host_dns_can_resolve "$test_host"; then
        _dns_print_ok "宿主机 DNS 修复成功（已解析 ${test_host}）"
        return 0
    fi

    _dns_print_warn "写入公网 DNS 后仍无法解析 ${test_host}（可能是出网/防火墙限制）"
    _print_host_dns_fix_guide
    return 1
}

# 判断 docker 错误是否为 DNS 故障（应立即中止连续 pull）
docker_error_is_dns_failure() {
    local msg="${1:-}"
    echo "$msg" | grep -Eqi 'lookup .*(on \[::1\]:53|on 127\.|connection refused)|no such host|Temporary failure in name resolution|Could not resolve host'
}

# 先修宿主机 DNS，再写 daemon.json（容器侧）
ensure_docker_network_ready() {
    ensure_host_dns_for_docker "$@" || return 1
    if declare -f configure_docker_mirror >/dev/null 2>&1; then
        EASYAIOT_FORCE_DOCKER_DNS=1 configure_docker_mirror || true
    fi
    return 0
}
