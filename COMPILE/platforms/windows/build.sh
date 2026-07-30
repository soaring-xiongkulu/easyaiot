#!/usr/bin/env bash
# 在 Windows 主机本机构建 PANEL 可执行文件（.exe）+ 内置 runtime，可选生成 NSIS 安装包
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/windows}"
VENV_DIR="${COMPILE_ROOT}/.venv-build-windows"
MAKE_INSTALLER=0

# shellcheck source=../../lib/pack_desktop_runtime.sh
source "${COMPILE_ROOT}/lib/pack_desktop_runtime.sh"
# shellcheck source=../../lib/resolve_panel_version.sh
source "${COMPILE_ROOT}/lib/resolve_panel_version.sh"

log() { echo "[COMPILE/windows] $*"; }

for arg in "$@"; do
  case "$arg" in
    --installer|installer|--nsis)
      MAKE_INSTALLER=1
      ;;
    -h|--help)
      echo "用法: $0 [--installer]"
      echo "产物: easyaiot-panel.exe + runtime/（含 install_windows.sh）+ panel.env + run.bat"
      exit 0
      ;;
    *)
      echo "[COMPILE/windows] 未知参数: $arg" >&2
      exit 1
      ;;
  esac
done

if [[ "${OS:-}" != "Windows_NT" && "$(uname -s 2>/dev/null || true)" != MINGW* && "$(uname -s 2>/dev/null || true)" != CYGWIN* ]]; then
  echo "[COMPILE/windows] 请在 Windows 主机执行此脚本（PowerShell/Git Bash/CMD 均可）" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[COMPILE/windows] 需要 npm" >&2
  exit 1
fi
if ! command -v python >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
  echo "[COMPILE/windows] 需要 Python 3.11+" >&2
  exit 1
fi

PY_BIN="$(command -v python || command -v python3)"

mkdir -p "$OUT_DIR"

log "构建前端 ui/dist"
(cd "${REPO_ROOT}/PANEL/ui" && npm install --no-audit --no-fund && npm run build)
test -f "${REPO_ROOT}/PANEL/ui/dist/index.html"

if [ ! -d "$VENV_DIR" ]; then
  "$PY_BIN" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/Scripts/activate" 2>/dev/null || source "${VENV_DIR}/bin/activate"
pip install -U pip
pip install -r "${COMPILE_ROOT}/requirements-build.txt"

export PANEL_SRC="${REPO_ROOT}/PANEL"
WORK_DIR="${COMPILE_ROOT}/work/windows"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

log "PyInstaller 打包 .exe"
pyinstaller \
  --clean \
  --noconfirm \
  --distpath "$OUT_DIR" \
  --workpath "$WORK_DIR" \
  "${SCRIPT_DIR}/panel.spec"

if [ ! -f "${OUT_DIR}/easyaiot-panel.exe" ]; then
  echo "[COMPILE/windows] 未生成 easyaiot-panel.exe" >&2
  exit 1
fi

VERSION="$(resolve_panel_version)"
RUNTIME_DIR="${OUT_DIR}/runtime"
log "打包内置 runtime（install_windows 镜像部署）→ ${RUNTIME_DIR}"
rm -rf "$RUNTIME_DIR"
pack_source_free_runtime "$RUNTIME_DIR" "$VERSION" "amd64"

cp -f "${SCRIPT_DIR}/panel.env" "${OUT_DIR}/panel.env.example"
if [ ! -f "${OUT_DIR}/panel.env" ]; then
  cp -f "${SCRIPT_DIR}/panel.env" "${OUT_DIR}/panel.env"
fi

cat > "${OUT_DIR}/run.bat" <<'EOF'
@echo off
setlocal enabledelayedexpansion
set HERE=%~dp0
rem 去掉末尾反斜杠
if "%HERE:~-1%"=="\" set HERE=%HERE:~0,-1%

if "%EASYAIOT_ROOT%"=="" (
  if exist "%HERE%\runtime\.scripts\docker\install_windows.sh" (
    set EASYAIOT_ROOT=%HERE%\runtime
  ) else (
    rem 开发态：从 COMPILE\dist\windows 回推仓库根
    set EASYAIOT_ROOT=%HERE%\..\..\..
  )
)
if "%PANEL_ENV_FILE%"=="" set PANEL_ENV_FILE=%HERE%\panel.env
if not exist "%PANEL_ENV_FILE%" if exist "%HERE%\panel.env.example" copy "%HERE%\panel.env.example" "%PANEL_ENV_FILE%" >nul

set INSTALL_SCRIPT=.scripts\docker\install_windows.sh
set EASYAIOT_ENABLE_PANEL=0

start "" http://127.0.0.1:9200/
"%HERE%\easyaiot-panel.exe"
EOF

cat > "${OUT_DIR}/README.txt" <<EOF
EasyAIoT PANEL ${VERSION} (Windows)

1. 安装并启动 Docker Desktop
2. 安装 Git for Windows（提供 bash，PANEL 一键部署需要）
3. 双击 run.bat，或运行 easyaiot-panel.exe
4. 浏览器打开 http://127.0.0.1:9200/
5. 在「应用部署」中执行 install（仅拉取预构建镜像，不本地编译）

内置 runtime: %CD%\\runtime
部署脚本: runtime\\.scripts\\docker\\install_windows.sh
配置: panel.env（INSTALL_SCRIPT / EASYAIOT_ROOT）
EOF

log "完成: ${OUT_DIR}/easyaiot-panel.exe + runtime/"
ls -lh "${OUT_DIR}/easyaiot-panel.exe" 2>/dev/null || ls -lh "${OUT_DIR}/easyaiot-panel.exe"
du -sh "${RUNTIME_DIR}" 2>/dev/null || true

if [ "$MAKE_INSTALLER" -eq 1 ]; then
  if ! command -v makensis >/dev/null 2>&1; then
    echo "[COMPILE/windows] 需要 NSIS (makensis) 才能生成安装包" >&2
    echo "请安装 NSIS 后重试，或先仅生成 .exe + runtime" >&2
    exit 1
  fi

  INSTALLER="${OUT_DIR}/easyaiot-panel-${VERSION}-setup.exe"
  TMP_NSI="${OUT_DIR}/installer.generated.nsi"
  # NSIS 路径：Git Bash 下转为 Windows 反斜杠
  OUT_WIN="${OUT_DIR//\//\\}"
  INSTALLER_WIN="${INSTALLER//\//\\}"
  sed \
    -e "s|__VERSION__|${VERSION}|g" \
    -e "s|__OUTFILE__|${INSTALLER_WIN}|g" \
    -e "s|__DISTDIR__|${OUT_WIN}|g" \
    "${SCRIPT_DIR}/installer.nsi" > "${TMP_NSI}"

  log "生成 NSIS 安装包（含 runtime）"
  makensis "${TMP_NSI}"
  ls -lh "${INSTALLER}"
fi
