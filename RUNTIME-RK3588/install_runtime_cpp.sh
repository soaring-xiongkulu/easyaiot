#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${1:-/opt/easyaiot/RUNTIME-RK3588}"
TARBALL="${2:-}"
[[ -f "$TARBALL" ]] || { echo "INSTALL_FAIL: tarball missing: $TARBALL" >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
tar -xzf "$TARBALL" -C "$WORK"
SOURCE="$(find "$WORK" -mindepth 1 -maxdepth 1 -type d -name 'easyaiot-runtime-rk3588-*' | head -1)"
[[ -x "$SOURCE/bin/RUNTIME" ]] || { echo "INSTALL_FAIL: invalid RK3588 package" >&2; exit 1; }
[[ -x "$SOURCE/bin/RUNTIME-RK3588-BENCH" ]] || { echo "INSTALL_FAIL: benchmark missing" >&2; exit 1; }
bash "$SOURCE/scripts/rk3588_preflight.sh"

RUN=""
if [[ ! -w "$(dirname "$INSTALL_DIR")" && ! -w "$INSTALL_DIR" ]]; then RUN="sudo"; fi
$RUN install -d "$INSTALL_DIR/bin" "$INSTALL_DIR/config" "$INSTALL_DIR/models" "$INSTALL_DIR/scripts"
$RUN install -m 0755 "$SOURCE/bin/RUNTIME" "$INSTALL_DIR/bin/RUNTIME"
$RUN install -m 0755 "$SOURCE/bin/RUNTIME-RK3588-BENCH" "$INSTALL_DIR/bin/RUNTIME-RK3588-BENCH"
$RUN install -m 0644 "$SOURCE/config/config.example.ini" "$INSTALL_DIR/config/config.example.ini"
$RUN install -m 0644 "$SOURCE/README.md" "$INSTALL_DIR/README.md"
$RUN install -m 0755 "$SOURCE/scripts/rk3588_preflight.sh" "$INSTALL_DIR/scripts/rk3588_preflight.sh"
$RUN install -m 0755 "$SOURCE/scripts/smoke_runtime.sh" "$INSTALL_DIR/scripts/smoke_runtime.sh"
$RUN install -m 0755 "$SOURCE/scripts/convert_rknn_model.py" "$INSTALL_DIR/scripts/convert_rknn_model.py"
$RUN install -m 0755 "$SOURCE/scripts/prepare_yolov8n_rk3588.sh" "$INSTALL_DIR/scripts/prepare_yolov8n_rk3588.sh"
if compgen -G "$SOURCE/models/*.rknn" >/dev/null; then
  $RUN install -m 0644 "$SOURCE"/models/*.rknn "$INSTALL_DIR/models/"
fi
[[ ! -f "$SOURCE/VERSION" ]] || $RUN install -m 0644 "$SOURCE/VERSION" "$INSTALL_DIR/VERSION"
bash "$INSTALL_DIR/scripts/smoke_runtime.sh" "$INSTALL_DIR/bin/RUNTIME"
echo "RUNTIME_RK3588_OK: $INSTALL_DIR/bin/RUNTIME"
echo "RUNTIME_RK3588_BENCH_OK: $INSTALL_DIR/bin/RUNTIME-RK3588-BENCH"
