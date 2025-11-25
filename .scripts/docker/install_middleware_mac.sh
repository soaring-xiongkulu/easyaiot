#!/bin/bash
# ---------------------------------------------------------------------------
# EasyAIoT 中间件一键脚本 (macOS)
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
DOCKER_PLATFORM=""
BASE_IMAGE=""

ensure_env_var() {
  local key="$1" value="$2"
  grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null && return
  if [[ -s "${ENV_FILE}" ]]; then
    tail -c1 "${ENV_FILE}" 2>/dev/null | grep -q $'\n' || printf '\n' >> "${ENV_FILE}"
  fi
  echo "${key}=${value}" >> "${ENV_FILE}"
}

SERVICES=(Nacos PostgresSQL TDengine Redis Kafka MinIO SRS NodeRED EMQX)

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
    EMQX) echo "/api/v5/status" ;;
    *) echo "" ;;
  esac
}

require_macos() {
  [[ "${OSTYPE}" == darwin* ]] || { err "仅支持 macOS"; exit 1; }
}

ensure_docker() {
  command -v docker >/dev/null 2>&1 || {
    err "未检测到 Docker Desktop，请先安装 https://www.docker.com/products/docker-desktop"; exit 1; }
  docker info >/dev/null 2>&1 && return
  warn "Docker daemon 未运行，尝试打开 Docker Desktop..."
  open -a Docker >/dev/null 2>&1 || true
  for _ in {1..30}; do
    sleep 2
    docker info >/dev/null 2>&1 && { ok "Docker Desktop 已就绪"; return; }
  done
  err "仍无法连接 Docker daemon，请手动启动 Docker Desktop 后重试"
  exit 1
}

ensure_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
  else
    err "未检测到 docker compose，请安装 Docker Desktop 或运行 brew install docker-compose"
    exit 1
  fi
}

compose() {
  local env_args=()
  [[ -f "${ENV_FILE}" ]] && env_args=(--env-file "${ENV_FILE}")
  (cd "${SCRIPT_DIR}" && \
    DOCKER_PLATFORM="${DOCKER_PLATFORM}" \
    BASE_IMAGE="${BASE_IMAGE}" \
    "${COMPOSE_CMD[@]}" "${env_args[@]}" -f "${COMPOSE_FILE}" "$@")
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) DOCKER_PLATFORM="linux/amd64" ;;
    arm64|aarch64) DOCKER_PLATFORM="linux/arm64" ;;
    *) err "不支持的架构"; exit 1 ;;
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
  )
  for d in "${dirs[@]}"; do mkdir -p "${SCRIPT_DIR}/${d}"; done
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

copy_srs_conf() {
  local src="${SCRIPT_DIR}/../srs/conf"
  local dst="${SCRIPT_DIR}/srs_data/conf"
  local target="${dst}/docker.conf"
  [[ -f "$target" ]] && return
  if [[ -f "${src}/docker.conf" ]]; then
    mkdir -p "$dst"
    cp -R "${src}/." "$dst/"
    ok "SRS 配置已复制"
  else
    warn "未找到默认 SRS 配置 (${src}/docker.conf)"
  fi
}

ensure_ready() {
  require_macos
  ensure_docker
  ensure_compose
  detect_arch
  ensure_dirs
  ensure_env
  ensure_network
  copy_srs_conf
}

cmd_install() {
  ensure_ready
  info "构建镜像..."
  compose build --build-arg BASE_IMAGE="${BASE_IMAGE}" --build-arg DOCKER_PLATFORM="${DOCKER_PLATFORM}"
  info "启动服务..."
  compose up -d
  update_nacos_password || warn "自动修改 Nacos 密码失败，请稍后手动确认"
  ok "安装完成"
  cmd_status
}

cmd_start()  { ensure_ready; info "启动服务..."; compose up -d; update_nacos_password || warn "自动修改 Nacos 密码失败，请稍后手动确认"; ok "已启动"; }
cmd_stop()   { ensure_ready; info "停止服务..."; compose down; ok "已停止"; }
cmd_restart(){ ensure_ready; info "重启服务..."; compose down; compose up -d; update_nacos_password || warn "自动修改 Nacos 密码失败，请稍后手动确认"; ok "已重启"; }
cmd_status() { ensure_ready; compose ps; echo ""; docker ps --filter "name=ai-service" --format "table {{.Names}}\t{{.Status}}"; }

cmd_logs() {
  ensure_ready
  if [[ "${1:-}" = "-f" || "${1:-}" = "--follow" ]]; then
    shift || true
    compose logs -f "$@"
  else
    compose logs --tail=100 "$@"
  fi
}

cmd_build()  { ensure_ready; compose build --no-cache --build-arg BASE_IMAGE="${BASE_IMAGE}" --build-arg DOCKER_PLATFORM="${DOCKER_PLATFORM}"; ok "构建完成"; }
cmd_clean()  {
  ensure_ready
  read -r -p "将删除容器/卷/ai-service 镜像，确认？(y/N) " resp
  [[ "$resp" =~ ^[Yy]([Ee][Ss])?$ ]] || { warn "已取消"; return; }
  compose down -v --remove-orphans
  docker rmi ai-service:latest >/dev/null 2>&1 || true
  ok "清理完成"
}
cmd_update() {
  ensure_ready
  info "拉取最新代码..."
  (cd "${SCRIPT_DIR}" && git pull || warn "git pull 失败，继续使用现有代码")
  info "重新构建并启动..."
  compose build --build-arg BASE_IMAGE="${BASE_IMAGE}" --build-arg DOCKER_PLATFORM="${DOCKER_PLATFORM}"
  compose up -d
  update_nacos_password || warn "自动修改 Nacos 密码失败，请稍后手动确认"
  ok "更新完成"
  cmd_status
}

wait_for_health() {
  local port="$1" path="$2"
  for _ in {1..60}; do
    if curl -fs "http://localhost:${port}${path}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
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

  local api_ready=0
  for _ in {1..30}; do
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
  elif echo "$admin_init_response" | grep -qi '"code":409'; then
    info "管理员密码已初始化，继续执行后续检查..."
  elif [[ -n "$admin_init_response" ]]; then
    warn "admin 初始化接口返回: $admin_init_response"
  fi

  info "尝试使用默认密码登录 Nacos..."
  login_response=$(curl -s -X POST "${nacos_server}/nacos/v1/auth/login" \
    -d "username=${default_username}&password=${default_password}" 2>/dev/null || true)

  if [[ -z "$login_response" ]]; then
    warn "默认密码登录无响应，可能是 Nacos 尚未启用鉴权"
  elif echo "$login_response" | grep -qE "user not found|403|401"; then
    info "默认密码不可用，继续尝试其他方式..."
  fi

  local access_token=""
  if command -v jq >/dev/null 2>&1; then
    access_token=$(echo "$login_response" | jq -r '.accessToken // .token // empty' 2>/dev/null)
  else
    access_token=$(echo "$login_response" | grep -o '"accessToken":"[^"]*"' | cut -d'"' -f4)
    [[ -z "$access_token" ]] && access_token=$(echo "$login_response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
  fi

  if [[ -n "$access_token" && "$access_token" != "null" ]]; then
    info "获取 accessToken 成功，使用受保护接口修改密码..."
    local change_response
    change_response=$(curl -s -X PUT "${nacos_server}/nacos/v1/auth/users" \
      -H "Authorization: Bearer ${access_token}" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=${default_username}&newPassword=${new_password}" 2>/dev/null || true)
    if echo "$change_response" | grep -qiE "\"code\":200|success|true"; then
      ok "Nacos 密码修改成功"
      return 0
    else
      warn "Token 修改接口返回: $change_response"
    fi
  fi

  info "尝试使用未认证 PUT 接口修改密码..."
  local direct_response
  direct_response=$(curl -s -X PUT "${nacos_server}/nacos/v1/auth/users" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${default_username}&newPassword=${new_password}" 2>/dev/null || true)
  if echo "$direct_response" | grep -qiE "\"code\":200|success|true"; then
    ok "Nacos 密码修改成功（直接方式）"
    return 0
  fi

  info "尝试使用 POST 接口设置密码..."
  local post_response
  post_response=$(curl -s -X POST "${nacos_server}/nacos/v1/auth/users" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${default_username}&password=${new_password}" 2>/dev/null || true)
  if echo "$post_response" | grep -qiE "\"code\":200|success|true"; then
    ok "Nacos 密码修改成功（POST 方式）"
    return 0
  fi

  warn "自动修改 Nacos 密码失败，请手动登录 http://localhost:8848/nacos 设置为 ${new_password}"
  return 1
}

cmd_verify() {
  ensure_ready
  local ok_count=0
  for svc in "${SERVICES[@]}"; do
    local port path
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
      if nc -z localhost "$port" >/dev/null 2>&1; then
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
EasyAIoT 中间件脚本 (macOS)
  install   构建并启动全部服务
  start     启动服务
  stop      停止服务
  restart   重启服务
  status    查看状态
  logs [-f] 查看日志
  build     重新构建镜像
  clean     清理容器/卷
  update    git pull + rebuild + restart
  verify    健康检查各服务
  help      查看帮助
USAGE
}

case "${1:-help}" in
  install) cmd_install ;;
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_restart ;;
  status)  cmd_status ;;
  logs)    shift || true; cmd_logs "$@" ;;
  build)   cmd_build ;;
  clean)   cmd_clean ;;
  update)  cmd_update ;;
  verify)  cmd_verify ;;
  help|-h|--help) usage ;;
  *) err "未知命令: $1"; usage; exit 1 ;;
esac
