#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

entrypoints=(
  "${SCRIPT_DIR}/install_linux.sh"
  "${SCRIPT_DIR}/install_linux_arm.sh"
  "${SCRIPT_DIR}/install_linux_kylin.sh"
  "${SCRIPT_DIR}/runtime_image.sh"
  "${SCRIPT_DIR}/runtime_image_common.sh"
)

for entrypoint in "${entrypoints[@]}"; do
  bash -n "$entrypoint"
done

# 长任务入口必须以已预解析的 main 调用结束，不能在 main 返回后再读取日志代码。
for entrypoint in \
  "${SCRIPT_DIR}/install_linux.sh" \
  "${SCRIPT_DIR}/install_linux_arm.sh" \
  "${SCRIPT_DIR}/install_linux_kylin.sh" \
  "${SCRIPT_DIR}/runtime_image.sh"; do
  last_line="$(awk 'NF { line=$0 } END { print line }' "$entrypoint")"
  [[ "$last_line" == 'main "$@"' ]] || {
    echo "FAIL: $entrypoint 的 main 调用后仍有代码: $last_line" >&2
    exit 1
  }
done

# 验证 runtime_image 使用的快照目录覆盖：脚本位于临时路径时仍能从真实目录
# 加载公共文件并完成帮助命令，且不会启动任何构建。
snapshot_file="$(mktemp)"
cleanup() { unlink "$snapshot_file" 2>/dev/null || true; }
trap cleanup EXIT
cp "${SCRIPT_DIR}/install_linux.sh" "$snapshot_file"
EASYAIOT_INSTALL_SCRIPT_DIR_OVERRIDE="$SCRIPT_DIR" \
  bash "$snapshot_file" help >/dev/null

echo "OK: build-runtime 入口语法、尾部预解析与不可变快照检查通过 (${PROJECT_ROOT})"
