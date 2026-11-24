#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${1:-$ROOT/dist}"
bash "$ROOT/scripts/rk3588_preflight.sh"
bash "$ROOT/scripts/build_linux.sh"

VERSION="${RUNTIME_VERSION:-$(git -C "$ROOT" describe --always --dirty 2>/dev/null || echo dev)}"
ARCH="$(uname -m)"
NAME="easyaiot-runtime-rk3588-${VERSION}-${ARCH}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
STAGE="$WORK/$NAME"
install -d "$STAGE/bin" "$STAGE/config" "$STAGE/models" "$STAGE/scripts"
install -m 0755 "$ROOT/build/RUNTIME" "$STAGE/bin/RUNTIME"
install -m 0755 "$ROOT/build/RUNTIME-RK3588-BENCH" "$STAGE/bin/RUNTIME-RK3588-BENCH"
install -m 0644 "$ROOT/config/config.example.ini" "$STAGE/config/config.example.ini"
install -m 0644 "$ROOT/README.md" "$STAGE/README.md"
install -m 0755 "$ROOT/scripts/rk3588_preflight.sh" "$STAGE/scripts/rk3588_preflight.sh"
install -m 0755 "$ROOT/scripts/smoke_runtime.sh" "$STAGE/scripts/smoke_runtime.sh"
install -m 0755 "$ROOT/scripts/convert_rknn_model.py" "$STAGE/scripts/convert_rknn_model.py"
install -m 0755 "$ROOT/scripts/prepare_yolov8n_rk3588.sh" "$STAGE/scripts/prepare_yolov8n_rk3588.sh"
find "$ROOT/models" -maxdepth 1 -type f -name '*.rknn' -exec install -m 0644 {} "$STAGE/models/" \;
printf 'version=%s\narch=%s\nplatform=rk3588\n' "$VERSION" "$ARCH" > "$STAGE/VERSION"
mkdir -p "$OUT_DIR"
tar -C "$WORK" -czf "$OUT_DIR/$NAME.tar.gz" "$NAME"
echo "EXPORT_OK: $OUT_DIR/$NAME.tar.gz"
