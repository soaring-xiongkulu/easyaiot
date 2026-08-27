#!/usr/bin/env bash
# EasyAIoT 媒体节点 — SRS + ZLMediaKit 一键部署
# 参考 docker-compose.media-node.yml；若服务已在运行且健康检查通过则自动跳过。
#
# 用法（在目标媒体节点上）:
#   export MEDIA_NODE_HOST=10.0.0.11 MEDIA_HOOK_HOST=10.0.0.1 MEDIA_HOOK_PORT=48080
#   bash install_media_stack.sh
#
# 或一行执行（控制台「添加节点」会生成带变量的完整脚本）:
#   curl -fsSL ... | bash
set -euo pipefail

MEDIA_CLUSTER_ROOT="${MEDIA_CLUSTER_ROOT:-/opt/easyaiot/media-cluster}"
VIDEO_RUNTIME_ROOT="${VIDEO_RUNTIME_ROOT:-/opt/easyaiot/VIDEO}"
MEDIA_NODE_NAME="${MEDIA_NODE_NAME:-media-node}"
MEDIA_NODE_HOST="${MEDIA_NODE_HOST:-$(hostname -I 2>/dev/null | awk '{print $1}')}"
MEDIA_HOOK_HOST="${MEDIA_HOOK_HOST:-127.0.0.1}"
MEDIA_HOOK_PORT="${MEDIA_HOOK_PORT:-48080}"
# 经 Gateway(48080) 回调需 /admin-api 前缀；直连 VIDEO(6000) 时设为空
MEDIA_HOOK_PATH_PREFIX="${MEDIA_HOOK_PATH_PREFIX:-/admin-api}"
MEDIA_CONTROL_HOOK_HOST="${MEDIA_CONTROL_HOOK_HOST:-${MEDIA_HOOK_HOST}}"
MEDIA_CONTROL_HOOK_PORT="${MEDIA_CONTROL_HOOK_PORT:-${MEDIA_HOOK_PORT}}"
MEDIA_CONTROL_HOOK_PATH_PREFIX="${MEDIA_CONTROL_HOOK_PATH_PREFIX:-${MEDIA_HOOK_PATH_PREFIX}}"
MEDIA_DVR_HOOK_HOST="${MEDIA_DVR_HOOK_HOST:-${MEDIA_HOOK_HOST}}"
MEDIA_DVR_HOOK_PORT="${MEDIA_DVR_HOOK_PORT:-${MEDIA_HOOK_PORT}}"
# edge_local 需要显式空前缀直连边缘代理；使用 `-` 而不是 `:-`，保留空字符串。
MEDIA_DVR_HOOK_PATH_PREFIX="${MEDIA_DVR_HOOK_PATH_PREFIX-${MEDIA_HOOK_PATH_PREFIX}}"
MEDIA_DVR_HOOK_PATH="${MEDIA_DVR_HOOK_PATH:-/sink/media/hook/srs/on_dvr}"
RECORDING_STORAGE_MODE="${RECORDING_STORAGE_MODE:-central_shared}"
RECORDING_STORAGE_GENERATION="${RECORDING_STORAGE_GENERATION:-1}"
MEDIA_RECORDING_ROOT="${MEDIA_RECORDING_ROOT:-/mnt/easyaiot-media}"
EDGE_MEDIA_PORT="${EDGE_MEDIA_PORT:-6000}"
export MEDIA_RECORDING_ROOT
SRS_CANDIDATE_IP="${SRS_CANDIDATE_IP:-${MEDIA_NODE_HOST}}"
SRS_RTMP_PORT="${SRS_RTMP_PORT:-1935}"
SRS_HTTP_PORT="${SRS_HTTP_PORT:-8080}"
SRS_API_PORT="${SRS_API_PORT:-1985}"
SRS_RTC_PORT="${SRS_RTC_PORT:-8000}"
SRS_FORWARD_ENABLED="${SRS_FORWARD_ENABLED:-off}"
SRS_FORWARD_DESTINATION="${SRS_FORWARD_DESTINATION:-127.0.0.1:19350}"
ZLM_HTTP_PORT="${ZLM_HTTP_PORT:-6080}"
ZLM_RTMP_PORT="${ZLM_RTMP_PORT:-10935}"
ZLM_RTSP_PORT="${ZLM_RTSP_PORT:-8554}"
ZLM_RTP_PORT_MIN="${ZLM_RTP_PORT_MIN:-30000}"
ZLM_RTP_PORT_MAX="${ZLM_RTP_PORT_MAX:-30500}"
ZLM_RTC_PORT="${ZLM_RTC_PORT:-8800}"
ZLM_RTC_EXTERN_IP="${ZLM_RTC_EXTERN_IP:-${SRS_CANDIDATE_IP:-${MEDIA_NODE_HOST}}}"
ZLM_SECRET="${ZLM_SECRET:-EasyAIoT_Media_Secret}"
SRS_IMAGE="${SRS_IMAGE:-ossrs/srs:5}"
ZLM_IMAGE="${ZLM_IMAGE:-zlmediakit/zlmediakit:master}"
SRS_IMAGE_TAR="${SRS_IMAGE_TAR:-ossrs-srs-5.tar}"
ZLM_IMAGE_TAR="${ZLM_IMAGE_TAR:-zlmediakit-master.tar}"

print_step() { echo ">>> $*"; }
print_ok() { echo "[OK] $*"; }
print_skip() { echo "[SKIP] $*"; }
print_err() { echo "[ERROR] $*" >&2; }

run_privileged() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi
  if sudo -n true >/dev/null 2>&1; then
    sudo -n "$@"
    return
  fi
  if [[ "${EASYAIOT_SUDO_STDIN:-0}" == "1" ]]; then
    sudo -S -p '' "$@"
    return
  fi
  print_err "目录 ${MEDIA_RECORDING_ROOT} 需要管理员权限；请配置免密 sudo，或将边缘录像目录改为 SSH 用户可写路径"
  return 1
}

load_offline_image() {
  local canonical="$1"
  local tar_path="$2"

  if docker image inspect "${canonical}" >/dev/null 2>&1; then
    print_ok "镜像已存在: ${canonical}"
    return 0
  fi
  if [[ ! -f "${tar_path}" ]]; then
    print_err "未找到离线镜像包: ${tar_path}"
    echo "请确认：① 本机已执行 export_media_images.sh 导出 ② iot-node 已更新并重新部署 ③ 同步步骤已上传 images/*.tar"
    return 1
  fi

  print_step "从离线包导入: ${tar_path}"
  local load_out load_rc
  set +e
  load_out=$(docker load -i "${tar_path}" 2>&1)
  load_rc=$?
  set -e
  if [[ "${load_rc}" -ne 0 ]]; then
    print_err "离线导入失败: ${tar_path}"
    [[ -n "${load_out}" ]] && echo "${load_out}"
    return 1
  fi
  [[ -n "${load_out}" ]] && echo "${load_out}"

  if docker image inspect "${canonical}" >/dev/null 2>&1; then
    print_ok "离线镜像就绪: ${canonical}"
    return 0
  fi

  local loaded=""
  loaded=$(echo "${load_out}" | sed -n 's/^Loaded image: //p' | tail -1)
  if [[ -n "${loaded}" ]]; then
    docker tag "${loaded}" "${canonical}" 2>/dev/null || true
    if docker image inspect "${canonical}" >/dev/null 2>&1; then
      print_ok "离线镜像已导入并标记为: ${canonical}"
      return 0
    fi
  fi

  print_err "离线包已加载但未找到目标镜像 ${canonical}"
  return 1
}

ensure_media_images() {
  local images_dir="${MEDIA_CLUSTER_ROOT}/images"
  local srs_tar="${images_dir}/${SRS_IMAGE_TAR}"
  local zlm_tar="${images_dir}/${ZLM_IMAGE_TAR}"

  print_step "导入离线 Docker 镜像（目标机不联网拉取，须已同步 images/*.tar）"
  load_offline_image "${SRS_IMAGE}" "${srs_tar}" || exit 1
  load_offline_image "${ZLM_IMAGE}" "${zlm_tar}" || exit 1
  print_ok "SRS / ZLM 镜像均已就绪（离线导入）"
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    print_err "未安装 Docker，请先安装 Docker Engine 并加入 docker 组"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    print_err "Docker 未运行或当前用户无权限（可尝试 sudo 或 usermod -aG docker \$USER）"
    exit 1
  fi
}

ensure_ceph_mount() {
  local mount_root="${MOUNT_ROOT:-${MEDIA_RECORDING_ROOT}}"
  if [[ "${SKIP_CEPH_CHECK:-0}" == "1" ]]; then
    print_skip "跳过共享存储检查（SKIP_CEPH_CHECK=1）"
    return 0
  fi
  if [[ "${REQUIRE_SHARED_STORAGE_MOUNT:-1}" == "0" ]]; then
    print_ok "控制面节点使用中心本地存储: ${mount_root}"
    return 0
  fi
  local fs_type mount_source
  fs_type=$(findmnt -T "${mount_root}" -n -o FSTYPE 2>/dev/null | head -1 | tr '[:upper:]' '[:lower:]' || true)
  mount_source=$(findmnt -T "${mount_root}" -n -o SOURCE 2>/dev/null | head -1 || true)
  case "${fs_type}" in
    nfs|nfs4|ceph|fuse.ceph|cifs|smb3|glusterfs|fuse.glusterfs|lustre|gpfs)
      if [[ ! -d "${mount_root}" ]] || [[ ! -w "${mount_root}" ]]; then
        print_err "共享存储已识别但目录不可写: ${mount_root}（${fs_type} ${mount_source}）"
        exit 1
      fi
      print_ok "共享存储已挂载: ${mount_root}（${fs_type} ${mount_source}）"
      return 0
      ;;
    "")
      print_err "未找到 ${mount_root} 的挂载信息；central_shared 要求边缘节点挂载与中心相同的 NFS/CephFS"
      ;;
    *)
      print_err "${mount_root} 当前是本地文件系统 ${fs_type}（${mount_source}），不是中心共享存储"
      ;;
  esac
  if [[ -d "${mount_root}" ]] && [[ -w "${mount_root}" ]]; then
    echo "目录可写不代表已挂载共享存储；请先挂载 NFS/CephFS，或改用 edge_local。" >&2
  fi
  exit 1
}

resolve_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  elif [[ -x /usr/local/bin/docker-compose ]]; then
    COMPOSE_CMD="/usr/local/bin/docker-compose"
  else
    print_err "未找到 docker compose 或 docker-compose"
    echo "请安装 Docker Compose 插件或独立包，例如:"
    echo "  yum install -y docker-compose-plugin   # 或 docker-compose"
    echo "  apt install -y docker-compose-plugin"
    exit 1
  fi
}

assert_not_running() {
  local service="$1"
  local healthy_fn="$2"
  if [[ -z "${MEDIA_FAIL_IF_RUNNING:-}" ]]; then
    return 0
  fi
  if "${healthy_fn}"; then
    print_err "目标机 ${service} 已在运行，自动部署已中止（请先手动停止现有服务）"
    exit 1
  fi
}

compose_up() {
  local service="$1"
  (
    cd "${MEDIA_CLUSTER_ROOT}"
    # shellcheck disable=SC2086
    ${COMPOSE_CMD} -f docker-compose.media-node.yml up -d "${service}"
  )
}

ensure_dirs() {
  print_step "创建媒体数据目录 ${MEDIA_RECORDING_ROOT}"
  local media_dirs=(
    "${MEDIA_RECORDING_ROOT}/playbacks"
    "${MEDIA_RECORDING_ROOT}/alert_images"
    "${MEDIA_RECORDING_ROOT}/events"
    "${MEDIA_RECORDING_ROOT}/logs"
    "${MEDIA_RECORDING_ROOT}/.state"
  )
  if ! mkdir -p "${media_dirs[@]}" 2>/dev/null; then
    run_privileged mkdir -p "${media_dirs[@]}"
  fi
  if ! chmod -R 755 "${MEDIA_RECORDING_ROOT}" 2>/dev/null; then
    run_privileged chmod -R 755 "${MEDIA_RECORDING_ROOT}"
  fi
  umask 077
  cat > "${MEDIA_CLUSTER_ROOT}/recording-storage.env" <<EOF
RECORDING_STORAGE_MODE=${RECORDING_STORAGE_MODE}
RECORDING_STORAGE_GENERATION=${RECORDING_STORAGE_GENERATION}
COMPUTE_NODE_ID=${COMPUTE_NODE_ID:-}
EDGE_RECORDING_ROOT=${MEDIA_RECORDING_ROOT}
MEDIA_HOST_DATA_ROOT=${MEDIA_RECORDING_ROOT}
SRS_HOST_DATA_ROOT=${MEDIA_RECORDING_ROOT}
ALERT_IMAGES_DIR=${MEDIA_RECORDING_ROOT}/alert_images
EOF
  if [[ -n "${MEDIA_INTERNAL_TOKEN:-}" ]]; then
    printf 'MEDIA_INTERNAL_TOKEN=%s\n' "${MEDIA_INTERNAL_TOKEN}" >> "${MEDIA_CLUSTER_ROOT}/recording-storage.env"
  fi
  if [[ -n "${MEDIA_ASSET_REPORT_URL:-}" ]]; then
    printf 'MEDIA_ASSET_REPORT_URL=%s\n' "${MEDIA_ASSET_REPORT_URL}" >> "${MEDIA_CLUSTER_ROOT}/recording-storage.env"
  fi
  chmod 600 "${MEDIA_CLUSTER_ROOT}/recording-storage.env"
  # VIDEO 通常以源码目录挂载运行；同步一份到该目录，使容器和宿主机进程使用同一代存储配置。
  if [[ -d "${VIDEO_RUNTIME_ROOT}" ]]; then
    cp "${MEDIA_CLUSTER_ROOT}/recording-storage.env" "${VIDEO_RUNTIME_ROOT}/.recording-storage.env"
    chmod 600 "${VIDEO_RUNTIME_ROOT}/.recording-storage.env"
  fi
}

ensure_media_cluster() {
  if [[ ! -f "${MEDIA_CLUSTER_ROOT}/docker-compose.media-node.yml" ]]; then
    print_err "未找到 ${MEDIA_CLUSTER_ROOT}/docker-compose.media-node.yml"
    echo "请先将仓库 .scripts/media-cluster 同步到目标机，例如:"
    echo "  rsync -avz .scripts/media-cluster/ root@${MEDIA_NODE_HOST:-<目标IP>}:/opt/easyaiot/media-cluster/"
    exit 1
  fi
  if ! command -v envsubst >/dev/null 2>&1; then
    print_err "未找到 envsubst，请安装 gettext 包（如 apt install gettext-base）"
    exit 1
  fi
}

srs_healthy() {
  local body
  body=$(curl -sf --connect-timeout 5 --max-time 10 "http://127.0.0.1:${SRS_API_PORT}/api/v1/versions" 2>/dev/null || true)
  [[ -n "${body}" ]] && echo "${body}" | grep -qE '"code"[[:space:]]*:[[:space:]]*0' \
    && echo "${body}" | grep -q '"version"'
}

zlm_healthy() {
  local url="http://127.0.0.1:${ZLM_HTTP_PORT}/index/api/getServerConfig"
  local body
  if [[ -n "${ZLM_SECRET}" ]]; then
    url="${url}?secret=${ZLM_SECRET}"
  fi
  body=$(curl -sf --connect-timeout 5 --max-time 10 "${url}" 2>/dev/null || true)
  [[ -n "${body}" ]] && echo "${body}" | grep -qE '"code"[[:space:]]*:[[:space:]]*0'
}

render_srs_config() {
  local out="${MEDIA_CLUSTER_ROOT}/srs/docker.conf"
  local rendered="${out}.rendered.$$"
  SRS_CONFIG_CHANGED=0
  export MEDIA_NODE_ID="${MEDIA_NODE_NAME}-srs"
  export MEDIA_CONTROL_HOOK_HOST MEDIA_CONTROL_HOOK_PORT MEDIA_CONTROL_HOOK_PATH_PREFIX
  export MEDIA_DVR_HOOK_HOST MEDIA_DVR_HOOK_PORT MEDIA_DVR_HOOK_PATH_PREFIX MEDIA_DVR_HOOK_PATH
  export SRS_CANDIDATE_IP SRS_RTC_PORT SRS_FORWARD_ENABLED SRS_FORWARD_DESTINATION
  print_step "渲染 SRS 配置 -> ${out}"
  envsubst '${MEDIA_NODE_ID} ${MEDIA_CONTROL_HOOK_HOST} ${MEDIA_CONTROL_HOOK_PORT} ${MEDIA_CONTROL_HOOK_PATH_PREFIX} ${MEDIA_DVR_HOOK_HOST} ${MEDIA_DVR_HOOK_PORT} ${MEDIA_DVR_HOOK_PATH_PREFIX} ${MEDIA_DVR_HOOK_PATH} ${SRS_CANDIDATE_IP} ${SRS_RTC_PORT} ${SRS_FORWARD_ENABLED} ${SRS_FORWARD_DESTINATION}' \
    < "${MEDIA_CLUSTER_ROOT}/srs/cluster.conf.template" \
    | sed -E \
      -e "s/^listen[[:space:]]+[0-9]+;/listen              ${SRS_RTMP_PORT};/" \
      -e "/http_server/,/}/ s/listen[[:space:]]+[0-9]+;/listen          ${SRS_HTTP_PORT};/" \
      -e "/http_api/,/}/ s/listen[[:space:]]+[0-9]+;/listen          ${SRS_API_PORT};/" \
    > "${rendered}"
  if [[ ! -f "${out}" ]] || ! cmp -s "${rendered}" "${out}"; then
    mv "${rendered}" "${out}"
    SRS_CONFIG_CHANGED=1
    print_ok "SRS 配置已更新"
  else
    rm -f "${rendered}"
    print_ok "SRS 配置无变化"
  fi
}

render_zlm_config() {
  local out="${MEDIA_CLUSTER_ROOT}/zlm/config.ini"
  local rendered="${out}.rendered.$$"
  ZLM_CONFIG_CHANGED=0
  export MEDIA_NODE_ID="${MEDIA_NODE_NAME}-zlm"
  export MEDIA_HOOK_HOST MEDIA_HOOK_PORT MEDIA_HOOK_PATH_PREFIX ZLM_SECRET
  export ZLM_HTTP_PORT ZLM_RTMP_PORT ZLM_RTSP_PORT ZLM_RTP_PORT_MIN ZLM_RTP_PORT_MAX
  export ZLM_RTC_PORT ZLM_RTC_EXTERN_IP
  print_step "渲染 ZLM 配置 -> ${out}"
  envsubst '${MEDIA_NODE_ID} ${MEDIA_HOOK_HOST} ${MEDIA_HOOK_PORT} ${MEDIA_HOOK_PATH_PREFIX} ${ZLM_SECRET} ${ZLM_HTTP_PORT} ${ZLM_RTMP_PORT} ${ZLM_RTSP_PORT} ${ZLM_RTP_PORT_MIN} ${ZLM_RTP_PORT_MAX} ${ZLM_RTC_PORT} ${ZLM_RTC_EXTERN_IP}' \
    < "${MEDIA_CLUSTER_ROOT}/zlm/config.ini.template" \
    > "${rendered}"
  if [[ ! -f "${out}" ]] || ! cmp -s "${rendered}" "${out}"; then
    mv "${rendered}" "${out}"
    ZLM_CONFIG_CHANGED=1
    print_ok "ZLM 配置已更新"
  else
    rm -f "${rendered}"
    print_ok "ZLM 配置无变化"
  fi
}

restart_media_service() {
  local service="$1"
  local config_changed="${2:-0}"
  local cname="${MEDIA_NODE_NAME}-${service}"
  local before_id=""
  local after_id=""
  before_id=$(docker inspect -f '{{.Id}}' "${cname}" 2>/dev/null || true)
  if ! (
    cd "${MEDIA_CLUSTER_ROOT}"
    # up 会在 bind mount、端口等 Compose 配置变化时自动重建容器；
    # 配置完全一致时保持容器不动，避免打断现有 RTMP 发布连接。
    ${COMPOSE_CMD} -f docker-compose.media-node.yml up -d "${service}" 2>/dev/null
  ); then
    docker restart "${cname}" >/dev/null 2>&1 || true
    return
  fi
  after_id=$(docker inspect -f '{{.Id}}' "${cname}" 2>/dev/null || true)
  if [[ "${config_changed}" == "1" && -n "${before_id}" && "${before_id}" == "${after_id}" ]]; then
    print_step "${service} 配置内容已变化，重启容器加载新配置"
    docker restart "${cname}" >/dev/null
  elif [[ -n "${before_id}" && "${before_id}" == "${after_id}" ]]; then
    print_skip "${service} 配置与挂载无变化，保持现有流连接"
  else
    print_ok "${service} Compose 配置已应用"
  fi
}

wait_srs_healthy() {
  local i=0
  while [[ $i -lt 30 ]]; do
    if srs_healthy; then
      print_ok "SRS 已就绪 (RTMP ${SRS_RTMP_PORT}, HTTP ${SRS_HTTP_PORT}, API ${SRS_API_PORT})"
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  print_err "SRS 启动超时，请检查: docker logs ${MEDIA_NODE_NAME}-srs"
  exit 1
}

wait_zlm_healthy() {
  local i=0
  while [[ $i -lt 30 ]]; do
    if zlm_healthy; then
      print_ok "ZLMediaKit 已就绪 (HTTP ${ZLM_HTTP_PORT}, RTMP ${ZLM_RTMP_PORT}, RTSP ${ZLM_RTSP_PORT})"
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  print_err "ZLMediaKit 启动超时，请检查: docker logs ${MEDIA_NODE_NAME}-zlm"
  exit 1
}

deploy_srs() {
  render_srs_config
  assert_not_running "SRS" srs_healthy
  if srs_healthy; then
    print_step "SRS 已在运行，检查配置与挂载变化"
    restart_media_service srs "${SRS_CONFIG_CHANGED}"
    wait_srs_healthy
    return 0
  fi
  print_step "启动 SRS 容器"
  export MEDIA_NODE_ID="${MEDIA_NODE_NAME}-srs"
  export ZLM_HTTP_PORT
  compose_up srs
  wait_srs_healthy
}

deploy_zlm() {
  render_zlm_config
  assert_not_running "ZLMediaKit" zlm_healthy
  if zlm_healthy; then
    print_step "ZLMediaKit 已在运行，检查配置与挂载变化"
    restart_media_service zlm "${ZLM_CONFIG_CHANGED}"
    wait_zlm_healthy
    return 0
  fi
  print_step "启动 ZLMediaKit 容器"
  export MEDIA_NODE_ID="${MEDIA_NODE_NAME}-zlm"
  export ZLM_HTTP_PORT
  compose_up zlm
  wait_zlm_healthy
}

restart_video_runtime_if_present() {
  if docker inspect video-service >/dev/null 2>&1; then
    print_step "重启 VIDEO 服务以加载第 ${RECORDING_STORAGE_GENERATION} 代录像存储配置"
    docker restart video-service >/dev/null
    local i=0
    while [[ $i -lt 30 ]]; do
      if curl -sf --connect-timeout 2 --max-time 3 "http://127.0.0.1:${VIDEO_SERVICE_PORT:-6000}/actuator/health" >/dev/null 2>&1; then
        print_ok "VIDEO 服务已加载新存储配置"
        return 0
      fi
      sleep 2
      i=$((i + 1))
    done
    print_err "VIDEO 服务重启后未在 60 秒内就绪，请检查 docker logs video-service"
    return 1
  fi
  print_skip "未发现 video-service 容器，运行时存储配置已写入，VIDEO 部署后自动加载"
}

ensure_edge_media_agent() {
  local unit_name="easyaiot-edge-media.service"
  local agent_script="${MEDIA_CLUSTER_ROOT}/edge_media_agent.py"
  local runner_script="${MEDIA_CLUSTER_ROOT}/start_edge_media_agent.sh"
  local pid_file="${MEDIA_RECORDING_ROOT}/.state/edge-media-agent.pid"
  local cron_marker="# EasyAIoT edge media agent"
  if [[ "${RECORDING_STORAGE_MODE}" != "edge_local" ]]; then
    if sudo -n systemctl is-enabled "${unit_name}" >/dev/null 2>&1; then
      print_step "停止边缘本地录像代理（已切换为中心共享存储）"
      sudo -n systemctl disable --now "${unit_name}" >/dev/null 2>&1 || true
    fi
    if [[ -f "${pid_file}" ]]; then
      local old_pid
      old_pid=$(cat "${pid_file}" 2>/dev/null || true)
      if [[ "${old_pid}" =~ ^[0-9]+$ ]] && [[ -r "/proc/${old_pid}/cmdline" ]] \
          && tr '\0' ' ' < "/proc/${old_pid}/cmdline" | grep -Fq "${agent_script}"; then
        kill "${old_pid}" 2>/dev/null || true
      fi
      rm -f "${pid_file}"
    fi
    if command -v crontab >/dev/null 2>&1; then
      (crontab -l 2>/dev/null || true) | grep -Fv "${cron_marker}" | crontab -
    fi
    return 0
  fi
  if [[ ! -f "${agent_script}" ]]; then
    print_err "未找到轻量级边缘媒体代理: ${agent_script}"
    return 1
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    print_err "edge_local 需要目标节点安装 Python 3"
    return 1
  fi
  chmod 755 "${agent_script}"
  if sudo -n true >/dev/null 2>&1; then
    print_step "安装轻量级边缘录像代理系统服务（端口 ${EDGE_MEDIA_PORT}）"
    sudo -n tee "/etc/systemd/system/${unit_name}" >/dev/null <<EOF
[Unit]
Description=EasyAIoT Edge Media Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=${MEDIA_CLUSTER_ROOT}/recording-storage.env
Environment=EDGE_MEDIA_PORT=${EDGE_MEDIA_PORT}
ExecStart=/usr/bin/python3 ${agent_script}
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    sudo -n systemctl daemon-reload
    sudo -n systemctl enable --now "${unit_name}" >/dev/null
  else
    print_step "当前账户无免密 sudo，使用用户进程 + crontab 部署边缘录像代理"
    cat > "${runner_script}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
MEDIA_CLUSTER_ROOT="${MEDIA_CLUSTER_ROOT}"
MEDIA_RECORDING_ROOT="${MEDIA_RECORDING_ROOT}"
EDGE_MEDIA_PORT="${EDGE_MEDIA_PORT}"
PID_FILE="${pid_file}"
AGENT_SCRIPT="${agent_script}"
if [[ -f "\${PID_FILE}" ]]; then
  old_pid=\$(cat "\${PID_FILE}" 2>/dev/null || true)
  if [[ "\${old_pid}" =~ ^[0-9]+$ ]] && kill -0 "\${old_pid}" 2>/dev/null \
      && [[ -r "/proc/\${old_pid}/cmdline" ]] \
      && tr '\0' ' ' < "/proc/\${old_pid}/cmdline" | grep -Fq "\${AGENT_SCRIPT}"; then
    exit 0
  fi
fi
set -a
# shellcheck disable=SC1091
source "\${MEDIA_CLUSTER_ROOT}/recording-storage.env"
set +a
export EDGE_MEDIA_PORT
mkdir -p "\${MEDIA_RECORDING_ROOT}/logs" "\${MEDIA_RECORDING_ROOT}/.state"
nohup python3 "\${AGENT_SCRIPT}" >> "\${MEDIA_RECORDING_ROOT}/logs/edge-media-agent.log" 2>&1 </dev/null &
echo \$! > "\${PID_FILE}"
EOF
    chmod 700 "${runner_script}"
    if [[ -f "${pid_file}" ]]; then
      local old_pid
      old_pid=$(cat "${pid_file}" 2>/dev/null || true)
      if [[ "${old_pid}" =~ ^[0-9]+$ ]] && [[ -r "/proc/${old_pid}/cmdline" ]] \
          && tr '\0' ' ' < "/proc/${old_pid}/cmdline" | grep -Fq "${agent_script}"; then
        kill "${old_pid}" 2>/dev/null || true
      fi
      rm -f "${pid_file}"
    fi
    "${runner_script}"
    if command -v crontab >/dev/null 2>&1; then
      { (crontab -l 2>/dev/null || true) | grep -Fv "${cron_marker}"; \
        echo "@reboot ${runner_script} ${cron_marker}"; } | crontab -
    else
      print_err "未找到 crontab；代理本次已启动，但节点重启后需重新下发媒体栈"
    fi
  fi
  local i=0
  while [[ $i -lt 20 ]]; do
    if curl -sf --connect-timeout 2 --max-time 3 \
      -H "X-Media-Internal-Token: ${MEDIA_INTERNAL_TOKEN}" \
      "http://127.0.0.1:${EDGE_MEDIA_PORT}/video/internal/edge-media/health" >/dev/null 2>&1; then
      print_ok "边缘录像代理已就绪 (HTTP ${EDGE_MEDIA_PORT})"
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  print_err "边缘录像代理未在 20 秒内就绪，请检查: journalctl -u ${unit_name}"
  return 1
}

ensure_edge_media_firewall() {
  if [[ "${RECORDING_STORAGE_MODE}" != "edge_local" ]]; then
    return 0
  fi
  local control_host="${MEDIA_CONTROL_HOOK_HOST:-}"
  if [[ -z "${control_host}" || "${control_host}" == "127.0.0.1" || "${control_host}" == "localhost" ]]; then
    return 0
  fi
  local ufw_bin=""
  ufw_bin=$(command -v ufw 2>/dev/null || true)
  if [[ -z "${ufw_bin}" && -x /usr/sbin/ufw ]]; then
    ufw_bin=/usr/sbin/ufw
  fi
  if [[ -n "${ufw_bin}" ]]; then
    local ufw_active=0
    # /etc/ufw/ufw.conf is readable without sudo on Ubuntu. Prefer it here so
    # remote non-interactive deployments do not lose the sudo password inside
    # command substitution while merely probing whether UFW is enabled.
    if [[ -r /etc/ufw/ufw.conf ]] && grep -Eq '^[[:space:]]*ENABLED=yes([[:space:]]|$)' /etc/ufw/ufw.conf; then
      ufw_active=1
    else
      local ufw_status
      ufw_status=$(run_privileged "${ufw_bin}" status 2>/dev/null || true)
      if echo "${ufw_status}" | grep -q '^Status: active'; then
        ufw_active=1
      fi
    fi
    if [[ "${ufw_active}" == "1" ]]; then
      print_step "允许控制面 ${control_host} 访问边缘录像代理端口 ${EDGE_MEDIA_PORT}"
      run_privileged "${ufw_bin}" allow proto tcp from "${control_host}" to any port "${EDGE_MEDIA_PORT}" \
        comment 'EasyAIoT control to edge media' >/dev/null
      print_ok "边缘录像代理防火墙规则已就绪"
    fi
  fi
}

main() {
  echo "========================================"
  echo " EasyAIoT 媒体栈部署 — ${MEDIA_NODE_NAME} @ ${MEDIA_NODE_HOST}"
  echo "========================================"
  if [[ -n "${MEDIA_RENDER_CONFIGS_ONLY:-}" ]]; then
    render_srs_config
    render_zlm_config
    print_ok "媒体栈配置已渲染（MEDIA_RENDER_CONFIGS_ONLY）"
    exit 0
  fi
  require_docker
  if [[ "${RECORDING_STORAGE_MODE}" == "edge_local" ]]; then
    SKIP_CEPH_CHECK=1
  fi
  ensure_ceph_mount
  resolve_compose_cmd
  print_ok "Compose 命令: ${COMPOSE_CMD}"
  ensure_dirs
  ensure_media_cluster
  if [[ -z "${MEDIA_DEPLOY_SERVICES_ONLY:-}" ]]; then
    ensure_media_images
  fi
  if [[ -n "${MEDIA_PREPARE_IMAGES_ONLY:-}" ]]; then
    exit 0
  fi
  deploy_srs
  deploy_zlm
  ensure_edge_media_agent
  ensure_edge_media_firewall
  restart_video_runtime_if_present
  echo ""
  print_ok "媒体栈部署完成。请在本平台完成 Agent 纳管后，可在节点列表「更多」中管理 SRS/ZLM。"
  echo "  SRS API:  http://${MEDIA_NODE_HOST}:${SRS_API_PORT}/api/v1/versions"
  echo "  ZLM API:  http://${MEDIA_NODE_HOST}:${ZLM_HTTP_PORT}/index/api/getServerConfig"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
