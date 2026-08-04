#!/usr/bin/env bash
# 在 macOS 主机本机构建 PANEL 可执行文件 + 内置 runtime，可选生成 .app / .dmg
# 图标：COMPILE/assets/panel-logo.png → 圆形白底（与 Ubuntu/Windows 一致）→ .icns
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/macos}"
VENV_DIR="${COMPILE_ROOT}/.venv-build-macos"
MAKE_APP=0
MAKE_DMG=0
APP_NAME="EasyAIoT Panel"
PANEL_LOGO="${COMPILE_PANEL_LOGO:-${COMPILE_ROOT}/assets/panel-logo.png}"
CIRCLE_ICON_PNG=""
MAKE_CIRCLE_ICON_PY="${COMPILE_ROOT}/lib/make_circle_icon.py"

# shellcheck source=../../lib/pack_desktop_runtime.sh
source "${COMPILE_ROOT}/lib/pack_desktop_runtime.sh"
# shellcheck source=../../lib/resolve_panel_version.sh
source "${COMPILE_ROOT}/lib/resolve_panel_version.sh"

log() { echo "[COMPILE/macos] $*"; }

for arg in "$@"; do
  case "$arg" in
    --app|app)
      MAKE_APP=1
      ;;
    --dmg|dmg|--pkg|pkg|installer)
      MAKE_APP=1
      MAKE_DMG=1
      ;;
    -h|--help)
      echo "用法: $0 [--app] [--dmg]"
      echo "产物: easyaiot-panel + runtime/（含 install_mac.sh）+ panel.env + run.command"
      echo "  --app  生成 EasyAIoT Panel.app（圆形白底图标，与 Linux 一致）"
      echo "  --dmg  生成 .app + .dmg（文件名含架构：-arm64=Apple Silicon，-amd64=Intel）"
      exit 0
      ;;
    *)
      echo "[COMPILE/macos] 未知参数: $arg" >&2
      exit 1
      ;;
  esac
done

if [ "$(uname -s 2>/dev/null || true)" != "Darwin" ]; then
  echo "[COMPILE/macos] 请在 macOS 主机执行此脚本" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[COMPILE/macos] 需要 npm" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "[COMPILE/macos] 需要 Python 3.11+" >&2
  exit 1
fi
if [ ! -f "$PANEL_LOGO" ]; then
  echo "[COMPILE/macos] 缺少 PANEL logo: ${PANEL_LOGO}" >&2
  exit 1
fi
if [ ! -f "$MAKE_CIRCLE_ICON_PY" ]; then
  echo "[COMPILE/macos] 缺少 ${MAKE_CIRCLE_ICON_PY}" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

log "构建前端 ui/dist"
(cd "${REPO_ROOT}/PANEL/ui" && npm install --no-audit --no-fund && npm run build)
test -f "${REPO_ROOT}/PANEL/ui/dist/index.html"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
pip install -U pip
pip install -r "${COMPILE_ROOT}/requirements-build.txt"

export PANEL_SRC="${REPO_ROOT}/PANEL"
WORK_DIR="${COMPILE_ROOT}/work/macos"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# 圆形白底 PNG（与 Ubuntu deb / Windows ico 同源算法）
CIRCLE_ICON_PNG="${OUT_DIR}/panel-icon-circle.png"
log "从 panel-logo.png 生成圆形白底图标 → ${CIRCLE_ICON_PNG}"
python3 "$MAKE_CIRCLE_ICON_PY" "$PANEL_LOGO" "$CIRCLE_ICON_PNG" --size 1024

log "PyInstaller 打包 macOS 可执行文件"
pyinstaller \
  --clean \
  --noconfirm \
  --distpath "$OUT_DIR" \
  --workpath "$WORK_DIR" \
  "${SCRIPT_DIR}/panel.spec"

if [ ! -f "${OUT_DIR}/easyaiot-panel" ]; then
  echo "[COMPILE/macos] 未生成 easyaiot-panel" >&2
  exit 1
fi

chmod +x "${OUT_DIR}/easyaiot-panel"

VERSION="$(resolve_panel_version)"
case "$(uname -m)" in
  arm64|aarch64)
    ARCH=arm64
    ARCH_LABEL="Apple Silicon"
    ;;
  *)
    ARCH=amd64
    ARCH_LABEL="Intel"
    ;;
esac

RUNTIME_DIR="${OUT_DIR}/runtime"
log "打包内置 runtime（install_mac 镜像部署）→ ${RUNTIME_DIR}"
rm -rf "$RUNTIME_DIR"
pack_source_free_runtime "$RUNTIME_DIR" "$VERSION" "$ARCH"

cp -f "${SCRIPT_DIR}/panel.env" "${OUT_DIR}/panel.env.example"
if [ ! -f "${OUT_DIR}/panel.env" ]; then
  cp -f "${SCRIPT_DIR}/panel.env" "${OUT_DIR}/panel.env"
fi

cat > "${OUT_DIR}/run.command" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${EASYAIOT_ROOT:-}" ]; then
  if [ -f "${HERE}/runtime/.scripts/docker/install_mac.sh" ]; then
    export EASYAIOT_ROOT="${HERE}/runtime"
  else
    export EASYAIOT_ROOT="$(cd "${HERE}/../../.." && pwd)"
  fi
fi
export PANEL_ENV_FILE="${PANEL_ENV_FILE:-${HERE}/panel.env}"
export INSTALL_SCRIPT="${INSTALL_SCRIPT:-.scripts/docker/install_mac.sh}"
export EASYAIOT_ENABLE_PANEL="${EASYAIOT_ENABLE_PANEL:-0}"
if [ ! -f "$PANEL_ENV_FILE" ] && [ -f "${HERE}/panel.env.example" ]; then
  cp "${HERE}/panel.env.example" "$PANEL_ENV_FILE"
fi

URL="${EASYAIOT_PANEL_URL:-http://127.0.0.1:9200/}"
HEALTH_URL="${EASYAIOT_PANEL_HEALTH_URL:-http://127.0.0.1:9200/health}"

panel_ready() {
  curl -sf "$HEALTH_URL" >/dev/null 2>&1 || curl -sf "$URL" >/dev/null 2>&1
}

# 启动 PANEL 前尝试拉起 Docker Desktop（后台，不阻塞等待引擎；未安装则跳过）
if ! pgrep -f '/Docker\.app/' >/dev/null 2>&1; then
  if [ -d "/Applications/Docker.app" ] || [ -d "${HOME}/Applications/Docker.app" ]; then
    echo "[EasyAIoT] 正在启动 Docker Desktop..."
    open -a Docker >/dev/null 2>&1 || true
  else
    echo "[EasyAIoT] 未找到 Docker Desktop，部署前请先安装: https://www.docker.com/products/docker-desktop"
  fi
fi

# 与 Windows 启动器一致：先等服务就绪再打开浏览器，避免空白/无法连接页
if panel_ready; then
  open "$URL" >/dev/null 2>&1 || true
  exit 0
fi

"${HERE}/easyaiot-panel" &
PANEL_PID=$!
for _ in $(seq 1 60); do
  if panel_ready; then
    open "$URL" >/dev/null 2>&1 || true
    wait "$PANEL_PID"
    exit $?
  fi
  if ! kill -0 "$PANEL_PID" 2>/dev/null; then
    echo "[EasyAIoT] PANEL 启动失败，请查看终端输出" >&2
    wait "$PANEL_PID" || true
    exit 1
  fi
  sleep 0.4
done
echo "[EasyAIoT] 等待 PANEL 就绪超时，仍尝试打开 ${URL}" >&2
open "$URL" >/dev/null 2>&1 || true
wait "$PANEL_PID"
EOF
chmod +x "${OUT_DIR}/run.command"

cat > "${OUT_DIR}/README.txt" <<EOF
EasyAIoT PANEL ${VERSION} (macOS ${ARCH} / ${ARCH_LABEL})

1. 安装 Docker Desktop（首次）；双击 run.command / .app 时会自动尝试启动它
2. 建议: brew install bash（bash 4+）
3. 安装包：打开 easyaiot-panel-${VERSION}-${ARCH}.dmg，拖到 Applications
   （本包仅适用于 ${ARCH_LABEL} Mac，勿混用其他架构包）
   或双击 run.command / 执行 ./easyaiot-panel
4. 浏览器打开 http://127.0.0.1:9200/
5. 在「应用部署」中执行 install（仅拉取预构建镜像）

内置 runtime: ./runtime（.app 内为 Contents/Resources/runtime）
部署脚本: runtime/.scripts/docker/install_mac.sh
配置: panel.env
图标: COMPILE/assets/panel-logo.png（圆形白底，与 Linux 一致）
架构: ${ARCH}（${ARCH_LABEL}）
EOF

log "完成: ${OUT_DIR}/easyaiot-panel + runtime/"
ls -lh "${OUT_DIR}/easyaiot-panel"
du -sh "${RUNTIME_DIR}" 2>/dev/null || true

build_macos_icns() {
  local src_png="$1"
  local icns_path="$2"
  local iconset_dir="${OUT_DIR}/icon.iconset"
  rm -rf "${iconset_dir}"
  mkdir -p "${iconset_dir}"

  # 使用圆形白底 PNG 生成各尺寸（勿直接用原始 logo，避免方块白边）
  sips -z 16 16 "${src_png}" --out "${iconset_dir}/icon_16x16.png" >/dev/null
  sips -z 32 32 "${src_png}" --out "${iconset_dir}/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "${src_png}" --out "${iconset_dir}/icon_32x32.png" >/dev/null
  sips -z 64 64 "${src_png}" --out "${iconset_dir}/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "${src_png}" --out "${iconset_dir}/icon_128x128.png" >/dev/null
  sips -z 256 256 "${src_png}" --out "${iconset_dir}/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "${src_png}" --out "${iconset_dir}/icon_256x256.png" >/dev/null
  sips -z 512 512 "${src_png}" --out "${iconset_dir}/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "${src_png}" --out "${iconset_dir}/icon_512x512.png" >/dev/null
  sips -z 1024 1024 "${src_png}" --out "${iconset_dir}/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "${iconset_dir}" -o "${icns_path}"
  rm -rf "${iconset_dir}"
  log "已生成 icns: ${icns_path}"
}

if [ "$MAKE_APP" -eq 1 ]; then
  APP_DIR="${OUT_DIR}/${APP_NAME}.app"
  CONTENTS_DIR="${APP_DIR}/Contents"
  MACOS_DIR="${CONTENTS_DIR}/MacOS"
  RES_DIR="${CONTENTS_DIR}/Resources"
  rm -rf "${APP_DIR}"
  mkdir -p "${MACOS_DIR}" "${RES_DIR}"

  cp -f "${OUT_DIR}/easyaiot-panel" "${MACOS_DIR}/easyaiot-panel"
  chmod +x "${MACOS_DIR}/easyaiot-panel"
  cp -f "${OUT_DIR}/panel.env.example" "${RES_DIR}/panel.env.example"
  cp -f "${OUT_DIR}/panel.env" "${RES_DIR}/panel.env" 2>/dev/null || \
    cp -f "${OUT_DIR}/panel.env.example" "${RES_DIR}/panel.env"
  cp -f "${CIRCLE_ICON_PNG}" "${RES_DIR}/panel-icon-circle.png"

  log "复制 runtime 到 .app Resources..."
  rm -rf "${RES_DIR}/runtime"
  cp -a "${RUNTIME_DIR}" "${RES_DIR}/runtime"

  ICNS_PATH="${RES_DIR}/panel.icns"
  build_macos_icns "${CIRCLE_ICON_PNG}" "${ICNS_PATH}"

  cat > "${CONTENTS_DIR}/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>${APP_NAME}</string>
  <key>CFBundleDisplayName</key><string>${APP_NAME}</string>
  <key>CFBundleExecutable</key><string>open-panel</string>
  <key>CFBundleIdentifier</key><string>com.basiclab.easyaiot.panel</string>
  <key>CFBundleVersion</key><string>${VERSION}</string>
  <key>CFBundleShortVersionString</key><string>${VERSION}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleIconFile</key><string>panel</string>
  <key>CFBundleIconName</key><string>panel</string>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSPrincipalClass</key><string>NSApplication</string>
</dict>
</plist>
EOF

  # 启动包装：指向 Resources/runtime
  cat > "${MACOS_DIR}/open-panel" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RES="$(cd "${HERE}/../Resources" && pwd)"
export EASYAIOT_ROOT="${EASYAIOT_ROOT:-${RES}/runtime}"
export PANEL_ENV_FILE="${PANEL_ENV_FILE:-${RES}/panel.env}"
export INSTALL_SCRIPT="${INSTALL_SCRIPT:-.scripts/docker/install_mac.sh}"
export EASYAIOT_ENABLE_PANEL="${EASYAIOT_ENABLE_PANEL:-0}"
if [ ! -f "$PANEL_ENV_FILE" ] && [ -f "${RES}/panel.env.example" ]; then
  cp "${RES}/panel.env.example" "$PANEL_ENV_FILE"
fi

URL="${EASYAIOT_PANEL_URL:-http://127.0.0.1:9200/}"
HEALTH_URL="${EASYAIOT_PANEL_HEALTH_URL:-http://127.0.0.1:9200/health}"
LOG_FILE="${TMPDIR:-/tmp}/easyaiot-panel-open.log"

panel_ready() {
  curl -sf "$HEALTH_URL" >/dev/null 2>&1 || curl -sf "$URL" >/dev/null 2>&1
}

# 启动 PANEL 前尝试拉起 Docker Desktop（后台，不阻塞等待引擎；未安装则跳过）
if ! pgrep -f '/Docker\.app/' >/dev/null 2>&1; then
  if [ -d "/Applications/Docker.app" ] || [ -d "${HOME}/Applications/Docker.app" ]; then
    echo "[EasyAIoT] 正在启动 Docker Desktop..."
    open -a Docker >/dev/null 2>&1 || true
  else
    echo "[EasyAIoT] 未找到 Docker Desktop，部署前请先安装: https://www.docker.com/products/docker-desktop"
  fi
fi

# 与 Windows 启动器一致：先等服务就绪再打开浏览器，避免空白/无法连接页
if panel_ready; then
  open "$URL" >/dev/null 2>&1 || true
  exit 0
fi

"${HERE}/easyaiot-panel" >>"$LOG_FILE" 2>&1 &
PANEL_PID=$!
for _ in $(seq 1 60); do
  if panel_ready; then
    open "$URL" >/dev/null 2>&1 || true
    wait "$PANEL_PID"
    exit $?
  fi
  if ! kill -0 "$PANEL_PID" 2>/dev/null; then
    echo "[EasyAIoT] PANEL 启动失败，日志: ${LOG_FILE}" >&2
    wait "$PANEL_PID" || true
    exit 1
  fi
  sleep 0.4
done
echo "[EasyAIoT] 等待 PANEL 就绪超时，仍尝试打开 ${URL}（日志: ${LOG_FILE}）" >&2
open "$URL" >/dev/null 2>&1 || true
wait "$PANEL_PID"
EOF
  chmod +x "${MACOS_DIR}/open-panel"

  # 附带 README 到 Resources
  cp -f "${OUT_DIR}/README.txt" "${RES_DIR}/README.txt"

  log "已生成 .app: ${APP_DIR}"
fi

if [ "$MAKE_DMG" -eq 1 ]; then
  APP_DIR="${OUT_DIR}/${APP_NAME}.app"
  if [ ! -d "$APP_DIR" ]; then
    echo "[COMPILE/macos] 未找到 .app，无法生成 dmg" >&2
    exit 1
  fi
  # 文件名带架构，便于区分芯片：arm64=Apple Silicon，amd64=Intel
  DMG_PATH="${OUT_DIR}/easyaiot-panel-${VERSION}-${ARCH}.dmg"
  DMG_STAGE="${OUT_DIR}/dmg-stage"
  rm -f "${DMG_PATH}"
  # 清理同版本无架构后缀的旧命名，避免混淆
  rm -f "${OUT_DIR}/easyaiot-panel-${VERSION}.dmg"
  rm -rf "${DMG_STAGE}"
  mkdir -p "${DMG_STAGE}"
  cp -a "${APP_DIR}" "${DMG_STAGE}/"
  ln -sf /Applications "${DMG_STAGE}/Applications"
  # 便于用户阅读
  cp -f "${OUT_DIR}/README.txt" "${DMG_STAGE}/README.txt"
  cp -f "${CIRCLE_ICON_PNG}" "${DMG_STAGE}/.VolumeIcon.png" 2>/dev/null || true

  log "生成 .dmg（${ARCH} / ${ARCH_LABEL}，含 Applications 快捷方式）→ ${DMG_PATH}"
  hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "${DMG_STAGE}" \
    -ov \
    -format UDZO \
    -fs HFS+ \
    "${DMG_PATH}" >/dev/null
  rm -rf "${DMG_STAGE}"
  log "已生成 .dmg: ${DMG_PATH}（${ARCH} / ${ARCH_LABEL}）"
  ls -lh "${DMG_PATH}"
fi
