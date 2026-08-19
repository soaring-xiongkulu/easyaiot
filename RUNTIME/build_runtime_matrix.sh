#!/usr/bin/env bash
# ============================================
# RUNTIME 离线包矩阵构建入口（委托 scripts/export_runtime_all.sh）
#
# 用法:
#   bash RUNTIME/build_runtime_matrix.sh                    # 默认实验室优先包
#   bash RUNTIME/build_runtime_matrix.sh --all              # 全矩阵
#   bash RUNTIME/build_runtime_matrix.sh --compile-target openeuler
#   bash RUNTIME/build_runtime_matrix.sh openeuler22 el9
# ============================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/scripts/export_runtime_all.sh" "$@"
