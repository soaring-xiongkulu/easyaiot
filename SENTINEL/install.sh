#!/bin/bash
# EasyAIoT Sentinel Agent 安装与管理（集群节点观察者：探测 + 执行 + 上报）
#
# 用法:
#   ./install.sh [命令]
#
# 命令:
#   install    安装/更新 Agent 并启动服务（默认）
#   update     仅同步源码并重启（不重装依赖）
#   start      启动 Agent 服务
#   stop       停止 Agent 服务
#   restart    重启 Agent 服务（不更新代码）
#   status     查看服务状态
#   logs       查看最近日志（logs -f 实时跟踪）
#   clean      停止服务并清理 Agent
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-/opt/easyaiot/sentinel-agent}"
SERVICE_NAME="${SERVICE_NAME:-easyaiot-sentinel-agent}"
PYTHON="${PYTHON:-python3}"
if command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON="$(command -v "$PYTHON")"
fi

usage() {
  cat <<EOF
用法: $0 [命令]

命令:
  install    安装/更新 Agent 并启动服务（默认）
  update     仅同步源码并重启（不重装依赖）
  start      启动 Agent 服务
  stop       停止 Agent 服务
  restart    重启 Agent 服务（不更新代码）
  status     查看服务状态
  logs       查看最近日志（logs -f 实时跟踪）
  clean      停止服务并清理 Agent

环境变量:
  INSTALL_DIR  安装目录，默认 /opt/easyaiot/sentinel-agent
  PYTHON       Python 解释器，默认 python3
EOF
}

service_unit_file() {
  echo "/etc/systemd/system/${SERVICE_NAME}.service"
}

service_installed() {
  [ -f "$(service_unit_file)" ]
}

require_service() {
  if ! service_installed; then
    echo "SERVICE_FAIL: Agent 未安装，请先执行: sudo $0 install" >&2
    exit 1
  fi
}

cmd_start() {
  require_service
  echo "==> 启动 ${SERVICE_NAME}"
  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}" >/dev/null 2>&1 || true
  sudo systemctl start "${SERVICE_NAME}"
  if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "SERVICE_OK: ${SERVICE_NAME} 已启动"
  else
    echo "SERVICE_FAIL: ${SERVICE_NAME} 启动失败" >&2
    sudo systemctl status "${SERVICE_NAME}" --no-pager -l 2>&1 | head -20 >&2 || true
    exit 1
  fi
}

cmd_stop() {
  if ! service_installed; then
    echo "SERVICE_SKIP: 服务未安装"
    exit 0
  fi
  echo "==> 停止 ${SERVICE_NAME}"
  sudo systemctl stop "${SERVICE_NAME}" 2>&1 || true
  echo "SERVICE_OK: ${SERVICE_NAME} 已停止"
}

cmd_restart() {
  require_service
  echo "==> 重启 ${SERVICE_NAME}"
  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}" >/dev/null 2>&1 || true
  sudo systemctl restart "${SERVICE_NAME}"
  if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "SERVICE_OK: ${SERVICE_NAME} 已重启"
  else
    echo "SERVICE_FAIL: ${SERVICE_NAME} 重启失败" >&2
    sudo systemctl status "${SERVICE_NAME}" --no-pager -l 2>&1 | head -20 >&2 || true
    exit 1
  fi
}

cmd_status() {
  if ! service_installed; then
    echo "SERVICE_INACTIVE: 未安装"
    exit 1
  fi
  sudo systemctl status "${SERVICE_NAME}" --no-pager -l || true
  echo ""
  if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
    echo "SERVICE_OK: active"
  else
    echo "SERVICE_INACTIVE"
  fi
}

cmd_logs() {
  require_service
  local follow="${1:-}"
  if [ "$follow" = "-f" ] || [ "$follow" = "--follow" ]; then
    sudo journalctl -u "${SERVICE_NAME}" -f --no-pager
  else
    sudo journalctl -u "${SERVICE_NAME}" -n 200 --no-pager
  fi
}

sync_agent_sources() {
  local resolved_install_dir resolved_script_dir
  sudo mkdir -p "$INSTALL_DIR"
  resolved_install_dir="$(readlink -f "$INSTALL_DIR")"
  resolved_script_dir="$(readlink -f "$SCRIPT_DIR")"
  if [ "$resolved_script_dir" = "$resolved_install_dir" ]; then
    echo "==> Agent 源码已在安装目录: ${resolved_install_dir}（跳过同步）"
    return 0
  fi
  echo "==> 同步 Sentinel 源码: ${resolved_script_dir} -> ${resolved_install_dir}"
  sudo cp "$resolved_script_dir/run_sentinel.py" "$resolved_script_dir/run_agent.py" \
    "$resolved_script_dir/agent_server.py" \
    "$resolved_script_dir/camera_access.py" \
    "$resolved_script_dir/media_manager.py" "$resolved_script_dir/mqtt_manager.py" \
    "$resolved_script_dir/workload_manager.py" \
    "$resolved_script_dir/requirements.txt" "$resolved_script_dir/agent.env.example" \
    "$resolved_script_dir/install.sh" "$resolved_install_dir/"
  if [ -d "$SCRIPT_DIR/sentinel" ]; then
    sudo rm -rf "$resolved_install_dir/sentinel"
    sudo cp -a "$SCRIPT_DIR/sentinel" "$resolved_install_dir/"
  fi
  if [ -d "$SCRIPT_DIR/registry" ]; then
    sudo rm -rf "$resolved_install_dir/registry"
    sudo cp -a "$SCRIPT_DIR/registry" "$resolved_install_dir/"
  fi
  sudo chmod +x "$resolved_install_dir/install.sh"
  if [ -d "$SCRIPT_DIR/pip-wheels" ]; then
    sudo rm -rf "$resolved_install_dir/pip-wheels"
    sudo mkdir -p "$resolved_install_dir/pip-wheels"
    sudo cp -a "$SCRIPT_DIR/pip-wheels/." "$resolved_install_dir/pip-wheels/"
  fi
  if [ -f "$SCRIPT_DIR/get-pip.py" ]; then
    sudo cp "$SCRIPT_DIR/get-pip.py" "$resolved_install_dir/"
  fi
  if [ -f "$SCRIPT_DIR/agent.env" ] && [ ! -f "$resolved_install_dir/agent.env" ]; then
    sudo cp "$SCRIPT_DIR/agent.env" "$resolved_install_dir/"
  fi
}

cmd_update() {
  sync_agent_sources
  cmd_restart
}

cmd_clean() {
  echo "==> 清理 ${SERVICE_NAME}"
  if service_installed; then
    sudo systemctl stop "${SERVICE_NAME}" 2>&1 || true
    sudo systemctl disable "${SERVICE_NAME}" 2>&1 || true
    sudo rm -f "$(service_unit_file)"
    sudo systemctl daemon-reload
    echo "==> systemd 单元已移除"
  else
    echo "==> systemd 单元不存在，跳过"
  fi
  if [ -d "$INSTALL_DIR" ]; then
    sudo rm -rf "$INSTALL_DIR"
    echo "==> 已删除安装目录: $INSTALL_DIR"
  fi
  echo "CLEAN_OK"
}

do_install() {
  echo "==> 安装目录: $INSTALL_DIR"
  echo "==> Python: $PYTHON ($($PYTHON --version 2>&1))"
  sync_agent_sources
  local resolved_install_dir
  resolved_install_dir="$(readlink -f "$INSTALL_DIR")"
  cd "$resolved_install_dir"
  local WHEELS_DIR="$resolved_install_dir/pip-wheels"
  local ONLINE_PIP=0
  if [ ! -d "$WHEELS_DIR" ] || ! compgen -G "$WHEELS_DIR"/*.{whl,tar.gz,zip} >/dev/null 2>&1; then
    if $PYTHON -c 'import urllib.request; urllib.request.urlopen("https://pypi.org", timeout=8)' >/dev/null 2>&1; then
      echo "==> 未找到离线 pip-wheels，目标机可访问 PyPI，改用在线安装依赖"
      ONLINE_PIP=1
    else
      echo "INSTALL_FAIL: 缺少离线 pip 包目录 pip-wheels/，且目标机无法访问 PyPI 拉取资源" >&2
      exit 1
    fi
  fi

  python_minor_version() {
    $PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3.12"
  }

  check_wheels_python_match() {
    local marker="$WHEELS_DIR/.target-python" target="" actual=""
    actual="$(python_minor_version)"
    if [ ! -f "$marker" ]; then
      return 0
    fi
    target="$(tr -d '[:space:]' < "$marker")"
    if [ -n "$target" ] && [ "$target" != "$actual" ]; then
      echo "INSTALL_FAIL: pip-wheels 目标 Python ${target} 与当前 ${PYTHON} (${actual}) 不一致" >&2
      echo "INSTALL_FAIL: 请执行 AGENT_TARGET_PYTHON=${actual} ./export_pip_wheels.sh 后重新 ./install.sh" >&2
      exit 1
    fi
  }
  check_wheels_python_match

  local RUN_PYTHON="" EXEC_PYTHON=""
  local SITE_PKG="$resolved_install_dir/site-packages"
  local VENV_DIR="$resolved_install_dir/venv"

  has_bootstrap_wheel() {
    compgen -G "$WHEELS_DIR/$1"*.whl >/dev/null 2>&1 \
      || compgen -G "$WHEELS_DIR/${1,,}"*.whl >/dev/null 2>&1
  }

  describe_bootstrap_gaps() {
    local gaps=""
    if ! has_bootstrap_wheel pip; then
      gaps="${gaps} pip-*.whl"
    fi
    if ! has_bootstrap_wheel setuptools; then
      gaps="${gaps} setuptools-*.whl"
    fi
    if ! has_bootstrap_wheel wheel; then
      gaps="${gaps} wheel-*.whl"
    fi
    if [ -n "$gaps" ]; then
      echo "INSTALL_FAIL: 离线 bootstrap 包不完整，缺少:${gaps}" >&2
      echo "INSTALL_FAIL: 请在平台服务器重新执行 export_pip_wheels.sh 后再次部署" >&2
    fi
  }

  write_agent_launcher() {
    local launcher
    launcher="$resolved_install_dir/agent-python.sh"
    cat <<WRAP | sudo tee "$launcher" > /dev/null
#!/bin/bash
export PYTHONPATH="${SITE_PKG}\${PYTHONPATH:+:\$PYTHONPATH}"
if [ "\$#" -gt 0 ]; then
  exec ${PYTHON} "\$@"
fi
if [ -f "${resolved_install_dir}/run_sentinel.py" ]; then
  exec ${PYTHON} "${resolved_install_dir}/run_sentinel.py" "\$@"
fi
exec ${PYTHON} "${resolved_install_dir}/run_agent.py" "\$@"
WRAP
    sudo chmod +x "$launcher"
    EXEC_PYTHON="$launcher"
  }

  verify_agent_imports() {
    if [ -d "$SITE_PKG" ]; then
      sudo env PYTHONPATH="$SITE_PKG" $PYTHON -c \
        "import flask, psutil, requests, minio, yaml, httpx, wsdiscovery, onvif, mqtt_manager" 2>/dev/null \
        && return 0
    fi
    if [ -n "$RUN_PYTHON" ] && [ -x "$RUN_PYTHON" ]; then
      sudo "$RUN_PYTHON" -c "import flask, psutil, requests, minio, yaml, httpx, wsdiscovery, onvif, mqtt_manager" 2>/dev/null \
        && return 0
    fi
    return 1
  }

  setup_agent_site_packages() {
    if ! has_bootstrap_wheel pip || ! has_bootstrap_wheel setuptools || ! has_bootstrap_wheel wheel; then
      describe_bootstrap_gaps
      return 1
    fi

    echo "==> 离线 site-packages 安装（仅需同步 pip-wheels，无需 python-venv）..."
    sudo rm -rf "$SITE_PKG"
    sudo mkdir -p "$SITE_PKG"

    if ! sudo $PYTHON - "$SITE_PKG" "$WHEELS_DIR" <<'PY'
import glob, os, sys, zipfile
site, wheels_dir = sys.argv[1], sys.argv[2]
os.makedirs(site, exist_ok=True)
for pkg in ("pip", "setuptools", "wheel"):
    matches = glob.glob(os.path.join(wheels_dir, f"{pkg}-*.whl"))
    if not matches:
        print(f"INSTALL_FAIL: missing wheel for {pkg}", file=sys.stderr)
        sys.exit(1)
    with zipfile.ZipFile(matches[0]) as zf:
        zf.extractall(site)
PY
    then
      echo "INSTALL_FAIL: 解压 pip/setuptools/wheel 失败" >&2
      return 1
    fi

    if ! sudo env PYTHONPATH="$SITE_PKG" $PYTHON -m pip --version >/dev/null 2>&1; then
      echo "WARN: site-packages bootstrap pip 不可用，尝试其他路径..." >&2
      return 1
    fi

    if ! sudo env PYTHONPATH="$SITE_PKG" $PYTHON -m pip install \
        --target="$SITE_PKG" --no-index --find-links "$WHEELS_DIR" \
        -r requirements.txt -q; then
      echo "INSTALL_FAIL: site-packages 离线依赖安装失败" >&2
      return 1
    fi

    RUN_PYTHON="$PYTHON"
    write_agent_launcher
    echo "==> site-packages 已就绪: $SITE_PKG"
    return 0
  }

  try_install_python_venv() {
    if ! command -v apt-get >/dev/null 2>&1; then
      return 1
    fi
    local py_ver
    py_ver="$(python_minor_version)"
    echo "==> 尝试在线安装 python${py_ver}-venv（离线环境将跳过）..."
    if sudo apt-get update -qq >/dev/null 2>&1 \
      && { sudo apt-get install -y -qq "python${py_ver}-venv" 2>/dev/null \
        || sudo apt-get install -y -qq python3-venv 2>/dev/null; }; then
      return 0
    fi
    return 1
  }

  setup_agent_venv() {
    local get_pip="$resolved_install_dir/get-pip.py"
    if [ ! -f "$get_pip" ] || ! has_bootstrap_wheel pip; then
      return 1
    fi

    echo "==> 尝试 venv 备选路径..."
    sudo rm -rf "$VENV_DIR"
    if ! sudo $PYTHON -m venv --without-pip "$VENV_DIR" 2>/dev/null; then
      try_install_python_venv || true
      if ! sudo $PYTHON -m venv --without-pip "$VENV_DIR" 2>/dev/null; then
        return 1
      fi
    fi

    if ! sudo "$VENV_DIR/bin/python" "$get_pip" --no-index --find-links "$WHEELS_DIR" --no-warn-script-location -q; then
      return 1
    fi
    if [ ! -x "$VENV_DIR/bin/pip" ]; then
      return 1
    fi
    if ! sudo "$VENV_DIR/bin/pip" install --no-index --find-links "$WHEELS_DIR" -r requirements.txt -q; then
      echo "INSTALL_FAIL: venv 离线依赖安装失败" >&2
      return 1
    fi

    RUN_PYTHON="$VENV_DIR/bin/python"
    EXEC_PYTHON="$(readlink -f "$RUN_PYTHON" 2>/dev/null || echo "$RUN_PYTHON")"
    echo "==> venv 已就绪: $RUN_PYTHON"
    return 0
  }

  setup_agent_online_site_packages() {
    echo "==> 在线 site-packages 安装（目标机已通过 PyPI 预检）..."
    sudo rm -rf "$SITE_PKG"
    sudo mkdir -p "$SITE_PKG"
    if ! $PYTHON -m pip --version >/dev/null 2>&1; then
      echo "==> 引导 pip（ensurepip）"
      sudo $PYTHON -m ensurepip --upgrade >/dev/null 2>&1 || true
    fi
    if ! sudo $PYTHON -m pip install --target="$SITE_PKG" -r requirements.txt -q; then
      echo "INSTALL_FAIL: 在线 pip 安装依赖失败" >&2
      return 1
    fi
    RUN_PYTHON="$PYTHON"
    write_agent_launcher
    echo "==> 在线 site-packages 已就绪: $SITE_PKG"
    return 0
  }

  if [ "$ONLINE_PIP" = "1" ]; then
    if ! setup_agent_online_site_packages; then
      echo "INSTALL_FAIL: 在线依赖安装失败" >&2
      exit 1
    fi
  elif setup_agent_site_packages; then
    :
  elif setup_agent_venv; then
    :
  else
    local py_ver
    py_ver="$(python_minor_version)"
    echo "INSTALL_FAIL: 离线安装失败" >&2
    echo "INSTALL_FAIL: 请确认平台已同步完整 pip-wheels（含 pip/setuptools/wheel 及 Python ${py_ver} 依赖）" >&2
    exit 1
  fi

  echo "==> 验证关键依赖"
  if ! verify_agent_imports; then
    echo "INSTALL_FAIL: 依赖安装后 import 验证失败" >&2
    exit 1
  fi

  if [ ! -f "$INSTALL_DIR/agent.env" ]; then
    sudo cp agent.env.example agent.env
    echo "请编辑 $INSTALL_DIR/agent.env 填入 NODE_ID 和 AGENT_TOKEN"
  fi

  cat <<UNIT | sudo tee "$(service_unit_file)" > /dev/null
[Unit]
Description=EasyAIoT Sentinel Agent
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
EnvironmentFile=${resolved_install_dir}/agent.env
ExecStart=${EXEC_PYTHON}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

  sudo systemctl daemon-reload
  echo "==> systemd 单元已写入: $(service_unit_file)"

  cmd_start

  echo "==> 安装完成"
  echo "    管理命令: sudo $INSTALL_DIR/install.sh {start|stop|restart|status|logs}"
  echo "INSTALL_OK"
}

main() {
  local action="${1:-install}"
  case "$action" in
    install)
      do_install
      ;;
    update)
      cmd_update
      ;;
    start)
      cmd_start
      ;;
    stop)
      cmd_stop
      ;;
    restart)
      cmd_restart
      ;;
    status)
      cmd_status
      ;;
    logs)
      cmd_logs "${2:-}"
      ;;
    clean)
      cmd_clean
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "未知命令: $action" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
