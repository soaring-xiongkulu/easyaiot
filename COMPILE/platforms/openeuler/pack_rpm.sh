#!/usr/bin/env bash
# 基于已编译 easyaiot-panel 生成 openEuler RPM 包
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
REPO_ROOT="$(cd "${COMPILE_ROOT}/.." && pwd)"
# shellcheck source=../../lib/resolve_panel_version.sh
source "${COMPILE_ROOT}/lib/resolve_panel_version.sh"
OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/openeuler}"
RPM_SRC="${SCRIPT_DIR}/rpm"
PANEL_LOGO="${COMPILE_PANEL_LOGO:-${COMPILE_ROOT}/assets/panel-logo.png}"
ARCH="$(uname -m)"
PKG_NAME="easyaiot-panel"
RELEASE="${PANEL_RELEASE:-1}"

RPMBUILD_ROOT="${COMPILE_ROOT}/work/openeuler-rpmbuild"
BUILDROOT="${COMPILE_ROOT}/work/openeuler-buildroot"
SPEC_PATH="${RPMBUILD_ROOT}/SPECS/${PKG_NAME}.spec"

log() { echo "[COMPILE/openeuler-rpm] $*"; }

if ! command -v rpmbuild >/dev/null 2>&1; then
  echo "[COMPILE/openeuler] 需要 rpmbuild（请安装 rpm-build）" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "[COMPILE/openeuler] 需要 python3（图标处理）" >&2
  exit 1
fi

BIN="${OUT_DIR}/easyaiot-panel"
if [ ! -x "$BIN" ]; then
  echo "[COMPILE/openeuler] 缺少二进制: ${BIN}" >&2
  echo "请先执行: bash COMPILE/build.sh openeuler" >&2
  exit 1
fi
if [ ! -f "$PANEL_LOGO" ]; then
  echo "[COMPILE/openeuler] 缺少 logo: ${PANEL_LOGO}" >&2
  exit 1
fi

VERSION="$(resolve_panel_version)"

rm -rf "$RPMBUILD_ROOT" "$BUILDROOT"
mkdir -p \
  "${RPMBUILD_ROOT}/"{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS} \
  "${BUILDROOT}/opt/easyaiot-panel/bin" \
  "${BUILDROOT}/etc/easyaiot-panel" \
  "${BUILDROOT}/usr/share/applications" \
  "${BUILDROOT}/usr/share/pixmaps" \
  "${BUILDROOT}/usr/lib/systemd/system" \
  "${BUILDROOT}/usr/share/doc/${PKG_NAME}"

install -m 0755 "$BIN" "${BUILDROOT}/opt/easyaiot-panel/bin/easyaiot-panel"
install -m 0755 "${RPM_SRC}/open-panel.sh" "${BUILDROOT}/opt/easyaiot-panel/bin/open-panel.sh"
install -m 0644 "${RPM_SRC}/panel.env" "${BUILDROOT}/etc/easyaiot-panel/panel.env"
install -m 0644 "${RPM_SRC}/easyaiot-panel.desktop" "${BUILDROOT}/usr/share/applications/easyaiot-panel.desktop"
install -m 0644 "${RPM_SRC}/easyaiot-panel.service" "${BUILDROOT}/usr/lib/systemd/system/easyaiot-panel.service"

cat > "${BUILDROOT}/usr/share/doc/${PKG_NAME}/README" <<EOF
EasyAIoT PANEL ${VERSION} (openEuler)

1) 修改 /etc/easyaiot-panel/panel.env 中 EASYAIOT_ROOT 为本机仓库根
2) systemctl enable --now easyaiot-panel
3) 浏览器访问 http://127.0.0.1:9200/
4) 平台部署请使用仓库内: .scripts/docker/install_linux_openeuler.sh
EOF

# 生成圆形白底图标（和 Ubuntu / CentOS 保持一致）
python3 - "$PANEL_LOGO" "${BUILDROOT}/usr/share/pixmaps/easyaiot-panel.png" <<'PY'
from PIL import Image, ImageDraw
import sys
src, dst = sys.argv[1], sys.argv[2]
img = Image.open(src).convert("RGBA")
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
canvas.save(dst, format="PNG", optimize=True)
PY

# RPM 元数据与发布文件名统一用标准 dist tag（oe2403 = openEuler 24.03）
DIST_TAG="${PANEL_DIST_TAG:-oe2403}"
PUBLISH_OS="${PANEL_PUBLISH_OS:-${DIST_TAG}}"

cat > "$SPEC_PATH" <<EOF
Name:           ${PKG_NAME}
Version:        ${VERSION}
Release:        ${RELEASE}.${DIST_TAG}
Summary:        EasyAIoT platform ops console (PANEL) for openEuler
License:        Apache-2.0
URL:            https://github.com/soaring-xiongkulu/easyaiot
BuildArch:      ${ARCH}
Requires:       systemd

%description
Independent ops panel for EasyAIoT on openEuler: container management,
install script UI, topology and host overview.
Deploy platform with .scripts/docker/install_linux_openeuler.sh after
setting EASYAIOT_ROOT to the EasyAIoT repository root.

%prep

%build

%install
mkdir -p %{buildroot}
cp -a ${BUILDROOT}/* %{buildroot}/

%post
if command -v systemctl >/dev/null 2>&1; then
  systemctl daemon-reload || true
  systemctl enable easyaiot-panel.service >/dev/null 2>&1 || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

%preun
if [ \$1 -eq 0 ]; then
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop easyaiot-panel.service >/dev/null 2>&1 || true
    systemctl disable easyaiot-panel.service >/dev/null 2>&1 || true
  fi
fi

%postun
if command -v systemctl >/dev/null 2>&1; then
  systemctl daemon-reload || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

%files
%defattr(-,root,root,-)
/opt/easyaiot-panel/bin/easyaiot-panel
/opt/easyaiot-panel/bin/open-panel.sh
%config(noreplace) /etc/easyaiot-panel/panel.env
/usr/share/applications/easyaiot-panel.desktop
/usr/share/pixmaps/easyaiot-panel.png
/usr/lib/systemd/system/easyaiot-panel.service
/usr/share/doc/${PKG_NAME}/README
EOF

log "rpmbuild 生成 openEuler RPM（Release=${RELEASE}.${DIST_TAG}）"
rpmbuild --define "_topdir ${RPMBUILD_ROOT}" -bb "${SPEC_PATH}"
mkdir -p "${OUT_DIR}"

# 专业写法：与包内 NEVRA 一致，例 easyaiot-panel-180-1.oe2403.x86_64.rpm
FINAL_RPM="${OUT_DIR}/${PKG_NAME}-${VERSION}-${RELEASE}.${PUBLISH_OS}.${ARCH}.rpm"
shopt -s nullglob
built=( "${RPMBUILD_ROOT}/RPMS/${ARCH}/${PKG_NAME}-${VERSION}-${RELEASE}."*.rpm )
shopt -u nullglob
if [ "${#built[@]}" -eq 0 ]; then
  echo "[COMPILE/openeuler] rpmbuild 未产出 RPM" >&2
  exit 1
fi
cp -f "${built[0]}" "${FINAL_RPM}"
shopt -s nullglob
for f in "${OUT_DIR}/${PKG_NAME}-${VERSION}"*.rpm; do
  [ "$f" = "$FINAL_RPM" ] && continue
  rm -f "$f"
done
shopt -u nullglob
ls -lh "${FINAL_RPM}"
log "产物: ${FINAL_RPM}"
