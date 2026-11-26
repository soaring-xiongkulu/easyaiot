#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---runtime}"
fail() { echo "[BM1688 预检失败] $*" >&2; exit 1; }
ok() { echo "[BM1688 预检] $*"; }

[[ "$(uname -s)" == "Linux" ]] || fail "仅支持 Linux"
case "$(uname -m)" in aarch64|arm64) ;; *) fail "仅支持 BM1688 aarch64 SoC" ;; esac

chip_text=""
for probe in \
  /proc/device-tree/compatible \
  /sys/firmware/devicetree/base/compatible \
  /proc/device-tree/model \
  /sys/firmware/devicetree/base/model; do
  [[ -r "$probe" ]] || continue
  chip_text+="$(tr '\0' ' ' < "$probe" 2>/dev/null || true) "
done
if command -v bm-smi >/dev/null 2>&1; then
  chip_text+="$(bm-smi 2>/dev/null || true)"
fi
printf '%s' "$chip_text" | grep -Eqi 'bm1688|cv186|sophon' \
  || fail "未识别到 BM1688/CV186X；本模块不会在普通 ARM 主机上运行"
ok "芯片识别通过"

for lib in bmlib bmrt bmcv; do
  ldconfig -p 2>/dev/null | grep -q "lib${lib}\.so" \
    || find /opt/sophon /usr/local /usr -name "lib${lib}.so*" -print -quit 2>/dev/null | grep -q . \
    || fail "缺少 lib${lib}，请安装 BM1688 SOPHONSDK"
done
ok "BMLib / BMRuntime / BMCV 已安装"

if [[ "$MODE" == "--build" ]]; then
  for command in cmake c++ make pkg-config; do
    command -v "$command" >/dev/null 2>&1 || fail "缺少编译工具: $command"
  done
  exit 0
fi

command -v ffmpeg >/dev/null 2>&1 || fail "缺少 SOPHON FFmpeg"
ffmpeg -hide_banner -decoders 2>/dev/null | grep -q 'h264_bm' || fail "缺少 h264_bm 硬件解码器"
ffmpeg -hide_banner -decoders 2>/dev/null | grep -q 'hevc_bm' || fail "缺少 hevc_bm 硬件解码器"
ok "SOPHON VPU 编解码能力通过"
