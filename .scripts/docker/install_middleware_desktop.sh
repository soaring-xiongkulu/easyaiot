#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# EasyAIoT 中间件一键脚本（macOS / Windows · Docker Desktop · 仅镜像部署）
# 不执行本地 docker build，只拉取官方/预置中间件镜像并 compose up。
# ---------------------------------------------------------------------------
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC}  $1" >&2; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
NETWORK_NAME="easyaiot-network"
ARCH_FILE="${SCRIPT_DIR}/.env.arch"
ENV_FILE="${SCRIPT_DIR}/.env.docker"
COMPOSE_CMD=()
COMPOSE_PROFILE_ARGS=()
DOCKER_PLATFORM=""
BASE_IMAGE=""

# shellcheck source=deploy_profile.sh
source "${SCRIPT_DIR}/deploy_profile.sh"
ensure_deploy_profile

ensure_env_var() {
  local key="$1" value="$2"
  grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null && return
  if [[ -s "${ENV_FILE}" ]]; then
    tail -c1 "${ENV_FILE}" 2>/dev/null | grep -q $'\n' || printf '\n' >> "${ENV_FILE}"
  fi
  echo "${key}=${value}" >> "${ENV_FILE}"
}

SERVICES=(Nacos PostgresSQL TDengine Redis Kafka MinIO SRS NodeRED FUXA EMQX)
MINIO_BUCKETS=(
  "dataset" "datasets" "export-bucket" "inference-inputs" "inference-results" "models" "snap-space" "alert-images"
  "plate-models" "plate-train-results" "plate-train-logs" "plate-inference-results"
)

service_port() {
  case "$1" in
    Nacos) echo 8848 ;;
    PostgresSQL) echo 5432 ;;
    TDengine) echo 6030 ;;
    Redis) echo 6379 ;;
    Kafka) echo 9092 ;;
    MinIO) echo 9000 ;;
    SRS) echo 1935 ;;
    NodeRED) echo 1880 ;;
    FUXA) echo 1881 ;;
    EMQX) echo 1883 ;;
    *) echo "" ;;
  esac
}

service_health() {
  case "$1" in
    Nacos) echo "/nacos/actuator/health" ;;
    MinIO) echo "/minio/health/live" ;;
    SRS) echo "/api/v1/versions" ;;
    NodeRED) echo "/" ;;
    FUXA) echo "/" ;;
    EMQX) echo "/api/v5/status" ;;
    *) echo "" ;;
  esac
}

ensure_docker() {
  command -v docker >/dev/null 2>&1 || {
    err "未检测到 Docker Desktop，请先安装 https://www.docker.com/products/docker-desktop"; exit 1; }
  docker info >/dev/null 2>&1 && return
  warn "Docker daemon 未运行"
  if [[ "${OSTYPE:-}" == darwin* ]]; then
    warn "尝试打开 Docker Desktop..."
    open -a Docker >/dev/null 2>&1 || true
    for _ in {1..30}; do
      sleep 2
      docker info >/dev/null 2>&1 && { ok "Docker Desktop 已就绪"; return; }
    done
  fi
  err "仍无法连接 Docker daemon，请手动启动 Docker Desktop 后重试"
  exit 1
}

ensure_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
  else
    err "未检测到 docker compose，请安装/升级 Docker Desktop"
    exit 1
  fi
}

compose() {
  local env_args=()
  [[ -f "${ENV_FILE}" ]] && env_args=(--env-file "${ENV_FILE}")
  (cd "${SCRIPT_DIR}" && \
    DOCKER_PLATFORM="${DOCKER_PLATFORM}" \
    BASE_IMAGE="${BASE_IMAGE}" \
    "${COMPOSE_CMD[@]}" ${COMPOSE_PROFILE_ARGS[@]+"${COMPOSE_PROFILE_ARGS[@]}"} "${env_args[@]}" -f "${COMPOSE_FILE}" "$@")
}

# 按部署形态启动中间件（mini/standard 跳过 FUXA/NodeRED 等）
compose_up_for_profile() {
  apply_deploy_profile
  COMPOSE_PROFILE_ARGS=()
  local flags
  flags=$(compose_profile_flags)
  if [ -n "$flags" ]; then
    # shellcheck disable=SC2206
    COMPOSE_PROFILE_ARGS=($flags)
  fi

  local -a skip_services=()
  local -a up_services=()
  local svc should_skip
  # shellcheck disable=SC2206
  skip_services=($(middleware_skipped_services))

  while IFS= read -r svc; do
    [ -z "$svc" ] && continue
    should_skip=0
    for s in "${skip_services[@]}"; do
      [ "$svc" = "$s" ] && should_skip=1 && break
    done
    [ "$should_skip" -eq 0 ] && up_services+=("$svc")
  done < <(compose config --services 2>/dev/null)

  if [ ${#skip_services[@]} -gt 0 ]; then
    warn "当前形态 (${EASYAIOT_DEPLOY_PROFILE}) 跳过中间件: ${skip_services[*]}"
    local -a lingering=()
    for svc in "${skip_services[@]}"; do
      if compose ps -q "$svc" 2>/dev/null | grep -q .; then
        lingering+=("$svc")
      fi
    done
    if [ ${#lingering[@]} -gt 0 ]; then
      info "停止并移除形态外中间件: ${lingering[*]}"
      compose stop "${lingering[@]}" >/dev/null 2>&1 || true
      compose rm -f "${lingering[@]}" >/dev/null 2>&1 || true
    fi
  fi

  if [ ${#up_services[@]} -eq 0 ]; then
    err "没有可启动的中间件服务"
    return 1
  fi
  info "启动中间件: ${up_services[*]}"
  compose up -d "${up_services[@]}"
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) DOCKER_PLATFORM="linux/amd64" ;;
    arm64|aarch64) DOCKER_PLATFORM="linux/arm64" ;;
    *) err "不支持的架构: $(uname -m)"; exit 1 ;;
  esac
  BASE_IMAGE="pytorch/pytorch:2.1.0-cpu"
  cat > "${ARCH_FILE}" <<EOF_ARCH
DOCKER_PLATFORM=${DOCKER_PLATFORM}
BASE_IMAGE=${BASE_IMAGE}
EOF_ARCH
  ok "架构配置: ${DOCKER_PLATFORM}"
}

ensure_dirs() {
  local dirs=(
    "data/uploads" "data/datasets" "data/models" "data/inference_results"
    "static/models" "temp_uploads" "model"
    "standalone-logs" "db_data" "redis_data" "taos_data" "mq_data"
    "minio_data" "srs_data" "nodered_data"
    "fuxa_data/appdata" "fuxa_data/db" "fuxa_data/logs" "fuxa_data/images"
  )
  for d in "${dirs[@]}"; do mkdir -p "${SCRIPT_DIR}/${d}"; done

  # macOS 根分区常只读；Windows/macOS 均可用用户目录作为 SRS 宿主机数据目录兜底
  local DESKTOP_DATA_DIR="${EASYAIOT_DESKTOP_DATA_DIR:-$HOME/easyaiot/data}"
  if mkdir -p "$DESKTOP_DATA_DIR/playbacks" 2>/dev/null; then
    chmod 777 "$DESKTOP_DATA_DIR" "$DESKTOP_DATA_DIR/playbacks" 2>/dev/null || true
  else
    warn "无法创建数据目录 $DESKTOP_DATA_DIR，请手动创建并赋予权限"
  fi
}

ensure_env() {
  local example="${SCRIPT_DIR}/env.example"
  [[ -f "$example" ]] || { err "缺少 env.example"; exit 1; }
  [[ -f "${ENV_FILE}" ]] || cp "$example" "${ENV_FILE}"
  ensure_env_var "POSTGRES_PASSWORD" "iot45722414822"
  ensure_env_var "DATABASE_URL" "postgresql://postgres:\${POSTGRES_PASSWORD}@PostgresSQL:5432/iot-ai20"
  ensure_env_var "NACOS_SERVER" "Nacos:8848"
  ensure_env_var "NACOS_NAMESPACE" ""
  ensure_env_var "NACOS_PASSWORD" "basiclab@iot78475418754"
  ensure_env_var "MINIO_ENDPOINT" "MinIO:9000"
  ensure_env_var "MINIO_SECRET_KEY" "basiclab@iot975248395"
  ensure_env_var "REDIS_PASSWORD" "basiclab@iot975248395"
  ensure_env_var "EMQX_DASHBOARD_PASSWORD" "basiclab@iot6874125784"
  ok ".env.docker 已准备"
}

ensure_network() {
  docker network inspect "${NETWORK_NAME}" >/dev/null 2>&1 && return
  info "创建网络 ${NETWORK_NAME}"
  docker network create "${NETWORK_NAME}" >/dev/null
}

get_docker_network_gateway() {
  local network_name="${1:-easyaiot-network}"
  local gateway_ip=""

  if docker network inspect "$network_name" >/dev/null 2>&1; then
    gateway_ip=$(docker network inspect "$network_name" --format='{{range .IPAM.Config}}{{.Gateway}}{{end}}' 2>/dev/null | head -n 1)
    if [[ -n "$gateway_ip" && "$gateway_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo "$gateway_ip"
      return 0
    fi
  fi

  if ! docker network inspect "$network_name" >/dev/null 2>&1; then
    if docker network create "$network_name" >/dev/null 2>&1; then
      gateway_ip=$(docker network inspect "$network_name" --format='{{range .IPAM.Config}}{{.Gateway}}{{end}}' 2>/dev/null | head -n 1)
      if [[ -n "$gateway_ip" && "$gateway_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "$gateway_ip"
        return 0
      fi
    fi
  fi

  # Docker Desktop：host.docker.internal
  if ping -c 1 host.docker.internal >/dev/null 2>&1 || ping -n 1 host.docker.internal >/dev/null 2>&1; then
    local resolved_ip=""
    resolved_ip=$(getent hosts host.docker.internal 2>/dev/null | awk '{print $1}' | head -n 1 || true)
    if [[ -z "$resolved_ip" ]] && command -v dscacheutil >/dev/null 2>&1; then
      resolved_ip=$(dscacheutil -q host -a name host.docker.internal 2>/dev/null | awk '/ip_address/{print $2; exit}')
    fi
    if [[ -n "$resolved_ip" && "$resolved_ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo "$resolved_ip"
      return 0
    fi
  fi

  echo "172.18.0.1"
  return 0
}

_sed_inplace() {
  # 兼容 GNU sed / BSD sed
  local expr="$1" file="$2"
  if sed --version >/dev/null 2>&1; then
    sed -i -E "$expr" "$file"
  else
    sed -i '' -E "$expr" "$file"
  fi
}

copy_srs_conf() {
  local src="${SCRIPT_DIR}/../srs/conf"
  local dst="${SCRIPT_DIR}/srs_data/conf"
  local target="${dst}/docker.conf"

  if [[ ! -f "${src}/docker.conf" ]]; then
    warn "未找到默认 SRS 配置 (${src}/docker.conf)"
    return
  fi

  mkdir -p "$dst"
  local gateway_ip
  gateway_ip=$(get_docker_network_gateway "${NETWORK_NAME}")
  if [[ -z "$gateway_ip" ]]; then
    warn "无法获取 Docker 网络网关 IP，将使用 172.18.0.1"
    gateway_ip="172.18.0.1"
  else
    info "检测到 Docker 网络网关 IP: $gateway_ip"
  fi

  cp -R "${src}/." "$dst/"

  if [[ -f "$target" ]]; then
    if _sed_inplace "s|http://([0-9]{1,3}\\.){3}[0-9]{1,3}:48080|http://${gateway_ip}:48080|g" "$target" 2>/dev/null; then
      info "已将 SRS 配置中的 Gateway 地址更新为: $gateway_ip:48080"
      ok "SRS 配置已复制并更新"
    else
      local temp_file
      temp_file=$(mktemp)
      if sed -E "s|http://([0-9]{1,3}\\.){3}[0-9]{1,3}:48080|http://${gateway_ip}:48080|g" "$target" > "$temp_file" 2>/dev/null; then
        mv "$temp_file" "$target"
        info "已将 SRS 配置中的 Gateway 地址更新为: $gateway_ip:48080"
        ok "SRS 配置已复制并更新"
      else
        rm -f "$temp_file"
        warn "无法更新 SRS 配置中的 IP 地址，使用原始配置"
        ok "SRS 配置已复制"
      fi
    fi
  else
    ok "SRS 配置已复制"
  fi
}

ensure_ready() {
  ensure_docker
  ensure_compose
  detect_arch
  ensure_dirs
  ensure_env
  ensure_network
  copy_srs_conf
}

pull_middleware_images() {
  info "拉取中间件镜像（按当前部署形态）..."
  apply_deploy_profile
  COMPOSE_PROFILE_ARGS=()
  local flags
  flags=$(compose_profile_flags)
  if [ -n "$flags" ]; then
    # shellcheck disable=SC2206
    COMPOSE_PROFILE_ARGS=($flags)
  fi

  local -a skip_services=()
  local -a pull_services=()
  local svc should_skip
  # shellcheck disable=SC2206
  skip_services=($(middleware_skipped_services))

  while IFS= read -r svc; do
    [ -z "$svc" ] && continue
    should_skip=0
    for s in "${skip_services[@]}"; do
      [ "$svc" = "$s" ] && should_skip=1 && break
    done
    [ "$should_skip" -eq 0 ] && pull_services+=("$svc")
  done < <(compose config --services 2>/dev/null)

  if [ ${#pull_services[@]} -eq 0 ]; then
    warn "没有需要拉取的中间件服务"
    return 0
  fi
  info "拉取: ${pull_services[*]}"
  compose pull "${pull_services[@]}" || warn "部分中间件镜像拉取失败，将尝试直接启动（本地已有镜像可继续）"
}

wait_for_health() {
  local port="$1" path="$2"
  local _
  for _ in $(seq 1 60); do
    if curl -fs "http://localhost:${port}${path}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

ensure_minio_buckets() {
  info "初始化 MinIO 存储桶..."
  if ! wait_for_health 9000 "/minio/health/live"; then
    warn "MinIO 未就绪，跳过存储桶初始化"
    return 1
  fi

  local access_key="${MINIO_ACCESS_KEY:-minioadmin}"
  local secret_key="${MINIO_SECRET_KEY:-basiclab@iot975248395}"
  local failed=0
  local bucket

  for bucket in "${MINIO_BUCKETS[@]}"; do
    if docker run --rm --network "${NETWORK_NAME}" \
      -e MINIO_ACCESS_KEY="${access_key}" \
      -e MINIO_SECRET_KEY="${secret_key}" \
      minio/mc sh -c 'mc alias set local http://MinIO:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" >/dev/null 2>&1 && mc mb --ignore-existing "local/'"${bucket}"'" >/dev/null 2>&1'; then
      ok "存储桶就绪: ${bucket}"
    else
      warn "存储桶初始化失败: ${bucket}"
      failed=$((failed + 1))
    fi
  done

  [[ $failed -eq 0 ]]
}

update_nacos_password() {
  local nacos_server="http://localhost:8848"
  local default_username="nacos"
  local default_password="nacos"
  local new_password="${NACOS_PASSWORD:-basiclab@iot78475418754}"

  info "检测 Nacos API 是否就绪..."
  if ! wait_for_health 8848 "/nacos/actuator/health"; then
    warn "Nacos 健康检查未通过，跳过密码修改"
    return 1
  fi

  local api_ready=0 _
  for _ in $(seq 1 30); do
    if curl -s --connect-timeout 2 "${nacos_server}/nacos/v1/auth/users?pageNo=1&pageSize=1" >/dev/null 2>&1; then
      api_ready=1
      break
    fi
    sleep 1
  done

  if [[ $api_ready -eq 0 ]]; then
    warn "Nacos API 未就绪，跳过密码修改"
    return 1
  fi

  info "尝试使用目标密码登录 Nacos..."
  local login_response
  login_response=$(curl -s -X POST "${nacos_server}/nacos/v1/auth/login" \
    -d "username=${default_username}&password=${new_password}" 2>/dev/null || true)
  if echo "$login_response" | grep -qiE '"accessToken"|\"token\"'; then
    ok "Nacos 已使用期望密码"
    return 0
  fi

  info "尝试使用 admin 初始化接口设置密码..."
  local admin_init_response
  admin_init_response=$(curl -s -X POST "${nacos_server}/nacos/v1/auth/users/admin" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "password=${new_password}" 2>/dev/null || true)
  if echo "$admin_init_response" | grep -qiE '"username":"nacos"|"code":200'; then
    ok "Nacos 管理员密码初始化成功"
    return 0
  fi

  info "尝试使用默认密码登录并修改..."
  login_response=$(curl -s -X POST "${nacos_server}/nacos/v1/auth/login" \
    -d "username=${default_username}&password=${default_password}" 2>/dev/null || true)

  local access_token=""
  if command -v jq >/dev/null 2>&1; then
    access_token=$(echo "$login_response" | jq -r '.accessToken // .token // empty' 2>/dev/null)
  else
    access_token=$(echo "$login_response" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
    [[ -z "$access_token" ]] && access_token=$(echo "$login_response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
  fi

  if [[ -n "$access_token" && "$access_token" != "null" ]]; then
    local change_response
    change_response=$(curl -s -X PUT "${nacos_server}/nacos/v1/auth/users" \
      -H "Authorization: Bearer ${access_token}" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=${default_username}&newPassword=${new_password}" 2>/dev/null || true)
    if echo "$change_response" | grep -qiE "\"code\":200|success|true"; then
      ok "Nacos 密码修改成功"
      return 0
    fi
  fi

  warn "自动修改 Nacos 密码失败，请手动登录 http://localhost:8848/nacos 设置为 ${new_password}"
  return 1
}

post_start_hooks() {
  ensure_minio_buckets || warn "部分 MinIO 存储桶初始化失败，请稍后重试"
  update_nacos_password || warn "自动修改 Nacos 密码失败，请稍后手动确认"
  sleep 3
  bash "${SCRIPT_DIR}/set_permanent_token.sh" >/dev/null 2>&1 || true
}

cmd_install() {
  ensure_ready
  pull_middleware_images
  info "启动中间件（镜像部署，不本地构建）..."
  compose_up_for_profile
  post_start_hooks
  ok "安装完成"
  cmd_status
}

cmd_start() {
  ensure_ready
  info "启动服务..."
  compose_up_for_profile
  post_start_hooks
  ok "已启动"
}

cmd_stop()   { ensure_ready; info "停止服务..."; compose down; ok "已停止"; }
cmd_restart(){ ensure_ready; info "重启服务..."; compose down; compose_up_for_profile; post_start_hooks; ok "已重启"; }
cmd_status() { ensure_ready; compose ps; }

cmd_logs() {
  ensure_ready
  if [[ "${1:-}" = "-f" || "${1:-}" = "--follow" ]]; then
    shift || true
    compose logs -f "$@"
  else
    compose logs --tail=100 "$@"
  fi
}

cmd_clean() {
  ensure_ready
  read -r -p "将删除中间件容器与数据卷，确认？(y/N) " resp
  [[ "$resp" =~ ^[Yy]([Ee][Ss])?$ ]] || { warn "已取消"; return; }
  compose down -v --remove-orphans
  ok "清理完成"
}

cmd_update() {
  ensure_ready
  info "拉取最新中间件镜像并重启（仅镜像部署）..."
  pull_middleware_images
  compose_up_for_profile
  post_start_hooks
  ok "更新完成"
  cmd_status
}

cmd_verify() {
  ensure_ready
  local ok_count=0
  local svc port path
  for svc in "${SERVICES[@]}"; do
    port=$(service_port "$svc")
    path=$(service_health "$svc")
    info "验证 ${svc} (:${port})"
    if [[ -n "$path" ]]; then
      if wait_for_health "$port" "$path"; then
        ok "${svc} 健康"
        ok_count=$((ok_count + 1))
      else
        warn "${svc} 未通过健康检查"
      fi
    else
      if (command -v nc >/dev/null 2>&1 && nc -z localhost "$port" >/dev/null 2>&1) \
        || curl -s --connect-timeout 1 "http://localhost:${port}" >/dev/null 2>&1; then
        ok "${svc} 端口就绪"
        ok_count=$((ok_count + 1))
      else
        warn "${svc} 端口未开启"
      fi
    fi
  done
  info "通过 ${ok_count}/${#SERVICES[@]}"
  [[ $ok_count -eq ${#SERVICES[@]} ]] || exit 1
}

usage() {
  cat <<'USAGE'
EasyAIoT 中间件脚本（macOS / Windows · 仅镜像部署）
  install   拉取镜像并启动全部中间件
  start     启动服务
  stop      停止服务
  restart   重启服务
  status    查看状态
  logs [-f] 查看日志
  clean     清理容器/卷
  update    拉取最新镜像并重启
  verify    健康检查各服务
  help      查看帮助

说明：本脚本不支持本地 docker build；业务运行时镜像请用上级 install_mac / install_windows 的 pull。
USAGE
}

case "${1:-help}" in
  install) cmd_install ;;
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_restart ;;
  status)  cmd_status ;;
  logs)    shift || true; cmd_logs "$@" ;;
  clean)   cmd_clean ;;
  update)  cmd_update ;;
  verify)  cmd_verify ;;
  build)
    err "桌面端仅支持镜像部署，不支持本地构建中间件"
    err "请使用: $0 install / update（自动 pull + up）"
    exit 1
    ;;
  help|-h|--help) usage ;;
  *) err "未知命令: ${1:-}"; usage; exit 1 ;;
esac
