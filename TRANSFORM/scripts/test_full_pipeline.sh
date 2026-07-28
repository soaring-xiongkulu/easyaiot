#!/usr/bin/env bash
# 便捷入口：本地没有 TRANSFORM 也会自动拉起并跑通业务流程
set -euo pipefail
exec bash "$(cd "$(dirname "$0")" && pwd)/test-pipeline/run_all.sh" "$@"
