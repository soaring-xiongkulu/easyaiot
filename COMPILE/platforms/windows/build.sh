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
# Windows venv 上直接 `pip install -U pip` 会报错，需用 python -m pip
python -m pip install -U pip
python -m pip install -r "${COMPILE_ROOT}/requirements-build.txt"

export PANEL_SRC="${REPO_ROOT}/PANEL"
WORK_DIR="${COMPILE_ROOT}/work/windows"
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

PANEL_LOGO="${COMPILE_PANEL_LOGO:-${COMPILE_ROOT}/assets/panel-logo.png}"
PANEL_ICO="${OUT_DIR}/panel.ico"
if [ ! -f "$PANEL_LOGO" ]; then
  echo "[COMPILE/windows] 缺少图标: ${PANEL_LOGO}" >&2
  exit 1
fi
log "从 panel-logo.png 生成圆形白底 Windows 图标 → ${PANEL_ICO}"
python - "$PANEL_LOGO" "$PANEL_ICO" <<'PY'
from PIL import Image
from PIL import ImageDraw
import os
import sys

src, dst = sys.argv[1], sys.argv[2]
img = Image.open(src).convert("RGBA")

# 与 Ubuntu deb 一致：圆形白底，外圈透明
size = 512
canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)
margin = int(size * 0.015)
draw.ellipse((margin, margin, size - margin, size - margin), fill=(255, 255, 255, 255))

inner = int((size - margin * 2) * 0.98)
img.thumbnail((inner, inner), Image.Resampling.LANCZOS)
x = (size - img.width) // 2
y = (size - img.height) // 2
canvas.alpha_composite(img, (x, y))

# 多尺寸 ICO（Pillow 按 sizes 缩放；勿用 append_images）
canvas.save(
    dst,
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(f"wrote {dst} ({os.path.getsize(dst)} bytes)")
PY
# PyInstaller 在 Windows 上需要原生路径
if command -v cygpath >/dev/null 2>&1; then
  export PANEL_ICON="$(cygpath -w "${PANEL_ICO}")"
  export PANEL_SRC="$(cygpath -w "${REPO_ROOT}/PANEL")"
else
  export PANEL_ICON="${PANEL_ICO}"
  export PANEL_SRC="${REPO_ROOT}/PANEL"
fi

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

# 旁路静态资源：与 exe 同级，避免仅依赖 %TEMP%\_MEI*（重启后易被清理导致 / 404）
log "同步前端到产物目录 ui/dist"
rm -rf "${OUT_DIR}/ui"
mkdir -p "${OUT_DIR}/ui"
cp -a "${REPO_ROOT}/PANEL/ui/dist" "${OUT_DIR}/ui/dist"
test -f "${OUT_DIR}/ui/dist/index.html"

VERSION="$(resolve_panel_version)"
RUNTIME_DIR="${OUT_DIR}/runtime"
log "打包内置 runtime（install_windows 镜像部署）→ ${RUNTIME_DIR}"
rm -rf "$RUNTIME_DIR"
pack_source_free_runtime "$RUNTIME_DIR" "$VERSION" "amd64"

cp -f "${SCRIPT_DIR}/panel.env" "${OUT_DIR}/panel.env.example"
if [ ! -f "${OUT_DIR}/panel.env" ]; then
  cp -f "${SCRIPT_DIR}/panel.env" "${OUT_DIR}/panel.env"
fi

# Compatibility stub: prefer run.vbs (no cmd/powershell flash)
cat > "${OUT_DIR}/run.bat" <<'EOF'
@echo off
wscript "%~dp0run.vbs"
EOF

# Silent launcher: no cmd / powershell. Shortcuts must point here.
cat > "${OUT_DIR}/run.vbs" <<'EOF'
Option Explicit
Dim sh, fso, dir, env, exe, dd, i, already
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
exe = dir & "\easyaiot-panel.exe"

Set env = sh.Environment("PROCESS")
If env("EASYAIOT_ROOT") = "" Then
  If fso.FileExists(dir & "\runtime\.scripts\docker\install_windows.sh") Then
    env("EASYAIOT_ROOT") = dir & "\runtime"
  Else
    env("EASYAIOT_ROOT") = dir & "\..\..\.."
  End If
End If
If env("PANEL_ENV_FILE") = "" Then env("PANEL_ENV_FILE") = dir & "\panel.env"
If Not fso.FileExists(env("PANEL_ENV_FILE")) Then
  If fso.FileExists(dir & "\panel.env.example") Then
    fso.CopyFile dir & "\panel.env.example", env("PANEL_ENV_FILE"), True
  End If
End If
env("INSTALL_SCRIPT") = ".scripts\docker\install_windows.sh"
env("EASYAIOT_ENABLE_PANEL") = "0"

If Not ProcExists("Docker Desktop.exe") And Not ProcExists("com.docker.backend.exe") Then
  dd = ""
  If fso.FileExists(sh.ExpandEnvironmentStrings("%ProgramFiles%\Docker\Docker\Docker Desktop.exe")) Then
    dd = sh.ExpandEnvironmentStrings("%ProgramFiles%\Docker\Docker\Docker Desktop.exe")
  ElseIf fso.FileExists(sh.ExpandEnvironmentStrings("%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe")) Then
    dd = sh.ExpandEnvironmentStrings("%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe")
  ElseIf fso.FileExists(sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Docker\Docker Desktop.exe")) Then
    dd = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Docker\Docker Desktop.exe")
  End If
  If dd <> "" Then sh.Run """" & dd & """", 1, False
End If

already = ProcExists("easyaiot-panel.exe")
If Not already Then
  sh.Run """" & exe & """", 0, False
  For i = 1 To 40
    If HttpOk("http://127.0.0.1:9200/health") Then Exit For
    WScript.Sleep 400
  Next
End If

sh.Run "http://127.0.0.1:9200/", 1, False

Function ProcExists(name)
  Dim wmi, col
  On Error Resume Next
  Set wmi = GetObject("winmgmts:\\.\root\cimv2")
  Set col = wmi.ExecQuery("SELECT ProcessId FROM Win32_Process WHERE Name='" & name & "'")
  ProcExists = (Not col Is Nothing) And (col.Count > 0)
  On Error GoTo 0
End Function

Function HttpOk(url)
  Dim http
  HttpOk = False
  On Error Resume Next
  Set http = CreateObject("MSXML2.ServerXMLHTTP.6.0")
  If http Is Nothing Then Set http = CreateObject("MSXML2.XMLHTTP")
  If http Is Nothing Then Exit Function
  http.setTimeouts 1000, 1000, 1000, 1000
  http.Open "GET", url, False
  http.Send
  HttpOk = (Err.Number = 0 And http.Status = 200)
  On Error GoTo 0
End Function
EOF

cat > "${OUT_DIR}/README.txt" <<EOF
EasyAIoT PANEL ${VERSION} (Windows)

1. 安装 Docker Desktop（首次）；启动时会自动尝试拉起它
2. 安装 Git for Windows（提供 bash，PANEL 一键部署需要）
3. 双击桌面「EasyAIoT Panel」（无黑窗后台运行），或运行 run.vbs / easyaiot-panel.exe
4. 浏览器打开 http://127.0.0.1:9200/
5. 在「应用部署」中执行 install（仅拉取预构建镜像，不本地编译）

前端静态资源: %CD%\\ui\\dist（与 exe 同级，避免临时目录被清理）
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
  rm -f "${OUT_DIR}/easyaiot-panel-${VERSION}-amd64-setup.exe"
  TMP_NSI="${OUT_DIR}/installer.generated.nsi"
  # 用 Python 写 NSI；路径先转成 Windows 形式，避免 Git Bash /e/... 路径失效
  if command -v cygpath >/dev/null 2>&1; then
    NSI_TPL_WIN="$(cygpath -w "${SCRIPT_DIR}/installer.nsi")"
    OUT_WIN="$(cygpath -w "${OUT_DIR}")"
    INSTALLER_WIN="$(cygpath -w "${INSTALLER}")"
    TMP_NSI_WIN="$(cygpath -w "${TMP_NSI}")"
  else
    NSI_TPL_WIN="${SCRIPT_DIR}/installer.nsi"
    OUT_WIN="${OUT_DIR}"
    INSTALLER_WIN="${INSTALLER}"
    TMP_NSI_WIN="${TMP_NSI}"
  fi
  python - <<PY
from pathlib import Path
tpl = Path(r"""${NSI_TPL_WIN}""")
out = Path(r"""${OUT_WIN}""")
installer = Path(r"""${INSTALLER_WIN}""")
text = tpl.read_text(encoding="utf-8")
text = text.replace("__VERSION__", """${VERSION}""")
text = text.replace("__OUTFILE__", str(installer))
text = text.replace("__DISTDIR__", str(out))
Path(r"""${TMP_NSI_WIN}""").write_text(text, encoding="utf-8-sig")
print(f"NSI written: {Path(r'''${TMP_NSI_WIN}''')}")
print(f"OutFile: {installer}")
PY

  log "生成 NSIS 安装包（含 runtime）"
  makensis "${TMP_NSI}"
  ls -lh "${INSTALLER}"
fi
