#!/usr/bin/env bash
# 基于已编译 easyaiot-panel 生成 CentOS/RHEL ARM64 RPM（el7 / el8 / el9）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPILE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
# shellcheck source=../centos/el_common.sh
source "${COMPILE_ROOT}/platforms/centos/el_common.sh"
# shellcheck source=../../lib/resolve_panel_version.sh
source "${COMPILE_ROOT}/lib/resolve_panel_version.sh"

centos_resolve_el "${EL_RELEASE:-9}"

OUT_DIR="${COMPILE_OUT:-${COMPILE_ROOT}/dist/centos-arm-${EL_OUT_SUFFIX}}"
RPM_SRC="${SCRIPT_DIR}/rpm"
PANEL_LOGO="${COMPILE_PANEL_LOGO:-${COMPILE_ROOT}/assets/panel-logo.png}"
ARCH_RAW="${PANEL_ARCH:-$(uname -m)}"
case "$ARCH_RAW" in
  arm64|aarch64) ARCH="aarch64" ;;
  *)
    echo "[COMPILE/centos-arm-${EL_OUT_SUFFIX}] 期望 aarch64/arm64，当前 ARCH=${ARCH_RAW}" >&2
    exit 1
    ;;
esac
PKG_NAME="easyaiot-panel"
RELEASE="${PANEL_RELEASE:-1}"

RPMBUILD_ROOT="${COMPILE_ROOT}/work/centos-arm-${EL_OUT_SUFFIX}-rpmbuild"
BUILDROOT="${COMPILE_ROOT}/work/centos-arm-${EL_OUT_SUFFIX}-buildroot"
SPEC_PATH="${RPMBUILD_ROOT}/SPECS/${PKG_NAME}.spec"

log() { echo "[COMPILE/centos-arm-${EL_OUT_SUFFIX}-rpm] $*"; }

if ! command -v rpmbuild >/dev/null 2>&1; then
  echo "[COMPILE/centos-arm-${EL_OUT_SUFFIX}] 需要 rpmbuild" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "[COMPILE/centos-arm-${EL_OUT_SUFFIX}] 需要 python3" >&2
  exit 1
fi

BIN="${OUT_DIR}/easyaiot-panel"
if [ ! -x "$BIN" ]; then
  echo "[COMPILE/centos-arm-${EL_OUT_SUFFIX}] 缺少二进制: ${BIN}" >&2
  echo "请先执行: bash COMPILE/build.sh centos-arm-el${EL_RELEASE}" >&2
  exit 1
fi
if [ ! -f "$PANEL_LOGO" ]; then
  echo "[COMPILE/centos-arm-${EL_OUT_SUFFIX}] 缺少 logo: ${PANEL_LOGO}" >&2
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
EasyAIoT PANEL ${VERSION} (CentOS/RHEL ARM64 ${DIST_TAG})

1) 修改 /etc/easyaiot-panel/panel.env 中 EASYAIOT_ROOT 为本机仓库根
2) systemctl enable --now easyaiot-panel
3) 浏览器访问 http://127.0.0.1:9200/
4) 平台部署: .scripts/docker/install_linux_centos_arm.sh
EOF

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

DIST_TAG="${PANEL_DIST_TAG:-el${EL_RELEASE}}"
PUBLISH_OS="${PANEL_PUBLISH_OS:-${DIST_TAG}}"

cat > "$SPEC_PATH" <<EOF
Name:           ${PKG_NAME}
Version:        ${VERSION}
Release:        ${RELEASE}.${DIST_TAG}
Summary:        EasyAIoT platform ops console (PANEL) for CentOS/RHEL ARM64 ${DIST_TAG}
License:        Apache-2.0
URL:            https://github.com/soaring-xiongkulu/easyaiot
BuildArch:      ${ARCH}
Requires:       systemd

%description
Independent ops panel for EasyAIoT on CentOS/RHEL aarch64 (${DIST_TAG}).
Deploy with .scripts/docker/install_linux_centos_arm.sh after setting EASYAIOT_ROOT.

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

log "rpmbuild 生成 CentOS/RHEL ARM RPM（Release=${RELEASE}.${DIST_TAG} Arch=${ARCH}）"
rpmbuild --define "_topdir ${RPMBUILD_ROOT}" -bb "${SPEC_PATH}"
mkdir -p "${OUT_DIR}"

FINAL_RPM="${OUT_DIR}/${PKG_NAME}-${VERSION}-${RELEASE}.${PUBLISH_OS}.${ARCH}.rpm"
shopt -s nullglob
built=( "${RPMBUILD_ROOT}/RPMS/${ARCH}/${PKG_NAME}-${VERSION}-${RELEASE}."*.rpm )
shopt -u nullglob
if [ "${#built[@]}" -eq 0 ]; then
  echo "[COMPILE/centos-arm-${EL_OUT_SUFFIX}] rpmbuild 未产出 RPM" >&2
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
