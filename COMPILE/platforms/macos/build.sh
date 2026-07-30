#!/usr/bin/env bash
# 在 macOS 主机本机构建 PANEL 可执行文件 + 内置 runtime，可选生成 .app / .dmg
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/macos}"
VENV_DIR="${COMPILE_ROOT}/.venv-build-macos"
MAKE_APP=0
MAKE_DMG=0
APP_NAME="EasyAIoT Panel"
ICON_SRC="${COMPILE_ROOT}/assets/panel-logo.png"

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
    --dmg|dmg)
      MAKE_APP=1
      MAKE_DMG=1
      ;;
    -h|--help)
      echo "用法: $0 [--app] [--dmg]"
      echo "产物: easyaiot-panel + runtime/（含 install_mac.sh）+ panel.env + run.command"
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
  arm64|aarch64) ARCH=arm64 ;;
  *) ARCH=amd64 ;;
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
open "http://127.0.0.1:9200/" >/dev/null 2>&1 || true
exec "${HERE}/easyaiot-panel"
EOF
chmod +x "${OUT_DIR}/run.command"

cat > "${OUT_DIR}/README.txt" <<EOF
EasyAIoT PANEL ${VERSION} (macOS)

1. 安装并启动 Docker Desktop
2. 建议: brew install bash（bash 4+）
3. 双击 run.command，或执行 ./easyaiot-panel
4. 浏览器打开 http://127.0.0.1:9200/
5. 在「应用部署」中执行 install（仅拉取预构建镜像）

内置 runtime: ./runtime
部署脚本: runtime/.scripts/docker/install_mac.sh
配置: panel.env
EOF

log "完成: ${OUT_DIR}/easyaiot-panel + runtime/"
ls -lh "${OUT_DIR}/easyaiot-panel"
du -sh "${RUNTIME_DIR}" 2>/dev/null || true

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

  log "复制 runtime 到 .app Resources..."
  rm -rf "${RES_DIR}/runtime"
  cp -a "${RUNTIME_DIR}" "${RES_DIR}/runtime"

  ICONSET_DIR="${OUT_DIR}/icon.iconset"
  ICNS_PATH="${RES_DIR}/panel.icns"
  rm -rf "${ICONSET_DIR}"
  mkdir -p "${ICONSET_DIR}"

  sips -z 16 16 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_16x16.png" >/dev/null
  sips -z 32 32 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_32x32.png" >/dev/null
  sips -z 64 64 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_128x128.png" >/dev/null
  sips -z 256 256 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_256x256.png" >/dev/null
  sips -z 512 512 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_512x512.png" >/dev/null
  sips -z 1024 1024 "${ICON_SRC}" --out "${ICONSET_DIR}/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "${ICONSET_DIR}" -o "${ICNS_PATH}"

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
open "http://127.0.0.1:9200/" >/dev/null 2>&1 || true
exec "${HERE}/easyaiot-panel"
EOF
  chmod +x "${MACOS_DIR}/open-panel"

  log "已生成 .app: ${APP_DIR}"
fi

if [ "$MAKE_DMG" -eq 1 ]; then
  APP_DIR="${OUT_DIR}/${APP_NAME}.app"
  if [ ! -d "$APP_DIR" ]; then
    echo "[COMPILE/macos] 未找到 .app，无法生成 dmg" >&2
    exit 1
  fi
  DMG_PATH="${OUT_DIR}/easyaiot-panel-${VERSION}.dmg"
  rm -f "${DMG_PATH}"
  hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_DIR}" -ov -format UDZO "${DMG_PATH}" >/dev/null
  log "已生成 .dmg: ${DMG_PATH}"
  ls -lh "${DMG_PATH}"
fi
