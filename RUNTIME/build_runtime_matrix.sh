#!/usr/bin/env bash
# ============================================
# RUNTIME 离线包矩阵构建入口（委托 scripts/export_runtime_all.sh）
#
# 用法:
#   bash RUNTIME/build_runtime_matrix.sh                    # COMPILE pack_all_linux 全覆盖
#   bash RUNTIME/build_runtime_matrix.sh --all              # 含 openeuler22 等扩展项
#   bash RUNTIME/build_runtime_matrix.sh --compile-target openeuler
#   bash RUNTIME/build_runtime_matrix.sh openeuler24 el9
#   bash RUNTIME/scripts/verify_runtime_compile_matrix.sh   # 仅验证映射，不构建
# ============================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$ROOT/scripts/export_runtime_all.sh" "$@"
