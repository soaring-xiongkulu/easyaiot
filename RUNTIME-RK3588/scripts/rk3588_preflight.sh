#!/usr/bin/env bash
set -euo pipefail

fail() { echo "RK3588_PREFLIGHT_FAIL: $*" >&2; exit 1; }
[[ "$(uname -m)" == "aarch64" || "$(uname -m)" == "arm64" ]] || fail "仅支持 aarch64 RK3588"

compatible=""
for path in /proc/device-tree/compatible /sys/firmware/devicetree/base/compatible; do
  if [[ -r "$path" ]]; then compatible="$(tr '\0' ',' < "$path")"; break; fi
done
[[ "$compatible" == *rockchip,rk3588* ]] || fail "设备树不是 rockchip,rk3588/rk3588s: $compatible"

[[ -e /dev/rknpu || -e /dev/rknpu0 ]] || fail "缺少 /dev/rknpu"
[[ -e /dev/rga || -e /dev/rga2 ]] || fail "缺少 /dev/rga"
[[ -e /dev/mpp_service || -e /dev/vpu_service || -e /dev/hevc_service ]] || fail "缺少 MPP/VPU 驱动节点"
[[ -e /dev/dri/renderD128 || -e /dev/dri/card0 ]] || fail "缺少 DRM 节点"

if command -v ldconfig >/dev/null 2>&1; then
  cache="$(ldconfig -p 2>/dev/null || true)"
  [[ "$cache" == *librknnrt.so* ]] || fail "动态链接器找不到 librknnrt.so"
  [[ "$cache" == *librga.so* ]] || fail "动态链接器找不到 librga.so"
  [[ "$cache" == *librockchip_mpp.so* || "$cache" == *libmpp.so* ]] || fail "动态链接器找不到 Rockchip MPP"
fi

if [[ "${1:-}" != "--build" ]] && command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -hide_banner -encoders 2>/dev/null | awk '{print $2}' | grep -qx h264_rkmpp \
    || fail "FFmpeg 未编入 h264_rkmpp 编码器"
fi
echo "RK3588_PREFLIGHT_OK: $compatible"
