#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-install}"
PREFIX="${EASYAIOT_RK3588_INSTALL_DIR:-/opt/easyaiot/RUNTIME-RK3588}"

case "$ACTION" in
  preflight)
    exec bash "$ROOT/scripts/rk3588_preflight.sh"
    ;;
  build)
    exec bash "$ROOT/scripts/build_linux.sh"
    ;;
  install)
    bash "$ROOT/scripts/rk3588_preflight.sh"
    bash "$ROOT/scripts/build_linux.sh"
    cmake --install "$ROOT/build" --prefix "$PREFIX"
    install -d "$PREFIX/config" "$PREFIX/models" "$PREFIX/scripts"
    install -m 0644 "$ROOT/config/config.example.ini" "$PREFIX/config/config.example.ini"
    install -m 0755 "$ROOT/scripts/rk3588_preflight.sh" "$PREFIX/scripts/rk3588_preflight.sh"
    install -m 0755 "$ROOT/scripts/convert_rknn_model.py" "$PREFIX/scripts/convert_rknn_model.py"
    install -m 0755 "$ROOT/scripts/prepare_yolov8n_rk3588.sh" "$PREFIX/scripts/prepare_yolov8n_rk3588.sh"
    echo "RUNTIME-RK3588 installed: $PREFIX/bin/RUNTIME"
    echo "RK3588 benchmark installed: $PREFIX/bin/RUNTIME-RK3588-BENCH"
    ;;
  *)
    echo "用法: $0 {preflight|build|install}" >&2
    exit 2
    ;;
esac
