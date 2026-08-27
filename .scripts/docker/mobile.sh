#!/usr/bin/env bash
# ================================================================
# EasyAIoT 移动端（Android / iOS / HarmonyOS）三端打包统一管理入口
#
# 用法:
#   .scripts/docker/mobile.sh status
#       三端版本一致性 / 工具链就绪度 / 已有成品 概览
#
#   .scripts/docker/mobile.sh build <android|ios|harmonyos|all> [prod|test|dev] [--skip-native]
#       单端或三端打包；--skip-native 只做前端构建与资源同步（无原生工具链时用）
#
#   .scripts/docker/mobile.sh bump <x.y.z> <versionCode>
#       发版：APP manifest 与三端壳共 5 处版本号一次改齐并回读校验
#
#   .scripts/docker/mobile.sh artifacts
#       列出所有已产出安装包
#
#   .scripts/docker/mobile.sh clean <android|ios|harmonyos|all>
#       清理指定端的打包成品
#
# 也可通过统一安装脚本调用: bash .scripts/docker/install_linux.sh mobile <同上子命令>
# 环境要求见各模块 README；总览与命名规范见 MOBILE.md
# ================================================================
set -eo pipefail

# 本脚本位于 .scripts/docker/ 下，项目根目录需向上回退两级
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONT="$ROOT/APP"

# ---- 版本号读取（返回 "<ver>|<code>"，解析失败位为空串） ----------------------
read_manifest() {
  local ver code
  ver=$(grep -oE "'versionName':[[:space:]]*'[^']+'" "$FRONT/manifest.config.ts" | head -1 | sed "s/.*'\(.*\)'/\1/")
  code=$(grep -oE "'versionCode':[[:space:]]*'[0-9]+'" "$FRONT/manifest.config.ts" | head -1 | grep -oE '[0-9]+')
  printf '%s|%s' "$ver" "$code"
}

read_android() {
  local ver code
  ver=$(sed -nE 's/^[[:space:]]*versionName[[:space:]]+"([^"]+)".*/\1/p' "$ROOT/ANDROID/app/build.gradle" | head -1)
  code=$(sed -nE 's/^[[:space:]]*versionCode[[:space:]]+([0-9]+).*/\1/p' "$ROOT/ANDROID/app/build.gradle" | head -1)
  printf '%s|%s' "$ver" "$code"
}

read_ios() {
  local pbx="$ROOT/IOS/EasyAIoT.xcodeproj/project.pbxproj" ver code
  ver=$(sed -nE 's/^[[:space:]]*MARKETING_VERSION[[:space:]]*=[[:space:]]*"?([^";]+)"?;.*/\1/p' "$pbx" | head -1)
  code=$(sed -nE 's/^[[:space:]]*CURRENT_PROJECT_VERSION[[:space:]]*=[[:space:]]*([0-9]+);.*/\1/p' "$pbx" | head -1)
  printf '%s|%s' "$ver" "$code"
}

read_harmony() {
  local ver code
  ver=$(sed -nE 's/.*"versionName":[[:space:]]*"([^"]+)".*/\1/p' "$ROOT/HARMONYOS/AppScope/app.json5" | head -1)
  code=$(sed -nE 's/.*"versionCode":[[:space:]]*([0-9]+).*/\1/p' "$ROOT/HARMONYOS/AppScope/app.json5" | head -1)
  printf '%s|%s' "$ver" "$code"
}

pair() { # -> "ver/code"
  local v="${1%%|*}" c="${1##*|}"
  if [ -z "$v" ] || [ -z "$c" ]; then echo "未找到配置"; else echo "$v/$c"; fi
}

agree() { # 端版本 vs 基准版本 -> 一致|不一致|?
  if [ -z "${1%%|*}" ] || [ -z "${1##*|}" ] || [ -z "${2%%|*}" ] || [ -z "${2##*|}" ]; then
    echo "?"; return
  fi
  local mv="${1%%|*}" mc="${1##*|}" iv="${2%%|*}" ic="${2##*|}"
  if [ "$mv" = "$iv" ] && [ "$((10#$mc))" = "$((10#$ic))" ]; then
    echo "一致"
  else
    echo "不一致"
  fi
}

toolchain() {
  case "$1" in
    android) if command -v java >/dev/null 2>&1 && [ -x "$ROOT/ANDROID/gradlew" ]; then
               echo "gradlew+java 就绪(SDK 见 local.properties)"
             else
               echo "需 JDK17+(gradlew 已入库)"
             fi ;;
    ios)     if command -v xcodebuild >/dev/null 2>&1; then
               echo "xcodebuild 就绪"
             else
               echo "需 macOS+Xcode16(--skip-native 可用)"
             fi ;;
    harmony) if command -v node >/dev/null 2>&1; then
               echo "hvigorw 启动器就绪(SDK 见 DEVECO_SDK_HOME)"
             else
               echo "需 Node + DevEco Studio 工具链"
             fi ;;
  esac
}

count_artifacts() {
  find "$1" -maxdepth 1 \( -name 'easyaiot-*' -o -name 'EasyAIoT-*' \) -type f 2>/dev/null | wc -l | tr -d ' '
}

# 打印文件头两行 "# ====" 分隔线之间的用法说明
_print_usage() {
  sed -n '/^# ====.*$/,/^# ====.*$/p' "${BASH_SOURCE[0]}" | sed '1d;$d' \
    | sed 's/^#\{1,\} \{0,1\}//; /^$/d'
}

# 调用某端的打包脚本（参数已校验过取值范围，可安全分词）
run_module() {
  local target="$1"; shift
  local args="$*"   # 形如 "prod --skip-native" 或 "prod"
  case "$target" in
    android)
      (cd "$ROOT/ANDROID" && ./make-apk.sh $args) ;;
    ios)
      (cd "$ROOT/IOS" && ./make-ipa.sh $args) ;;
    harmonyos)
      (cd "$ROOT/HARMONYOS" && ./make-hap.sh $args) ;;
  esac
}

cmd_status() {
  local mani base
  mani=$(read_manifest)
  base="${mani%%|*}/${mani##*|}"

  echo "============================================================"
  echo " EasyAIoT 移动端三端状态巡检"
  echo " 基准: APP/manifest.config.ts → $base"
  echo "============================================================"
  printf "\n%-11s %-16s %-7s %s\n" "平台" "壳工程版本" "一致性" "工具链"
  if [ -f "$ROOT/ANDROID/app/build.gradle" ]; then
    printf "%-11s %-16s %-7s %s\n" "android" "$(pair "$(read_android)")" \
      "$(agree "$(read_android)" "$mani")" "$(toolchain android)"
  fi
  if [ -f "$ROOT/IOS/EasyAIoT.xcodeproj/project.pbxproj" ]; then
    printf "%-11s %-16s %-7s %s\n" "ios" "$(pair "$(read_ios)")" \
      "$(agree "$(read_ios)" "$mani")" "$(toolchain ios)"
  fi
  if [ -f "$ROOT/HARMONYOS/AppScope/app.json5" ]; then
    printf "%-11s %-16s %-7s %s\n" "harmonyos" "$(pair "$(read_harmony)")" \
      "$(agree "$(read_harmony)" "$mani")" "$(toolchain harmony)"
  fi

  echo ""
  local d total=0
  for d in ANDROID IOS HARMONYOS; do
    [ -d "$ROOT/$d" ] || continue
    echo "成品[$d]: $(count_artifacts "$ROOT/$d") 个"
    total=$((total + $(count_artifacts "$ROOT/$d")))
  done
  echo "成品合计: $total 个（.scripts/docker/mobile.sh artifacts 查看 / ... clean <端> 清理）"
}

cmd_build() {
  local target="${1:-}"
  shift || true
  local mode="prod"
  local extra=""
  while [ $# -gt 0 ]; do
    case "$1" in
      prod|test|dev) mode="$1" ;;
      --skip-native) extra="--skip-native" ;;
      *) echo "[ERROR] build 参数不识别: $1"; exit 1 ;;
    esac
    shift
  done
  if ! printf '%s' "$target" | grep -qE '^(android|ios|harmonyos|all)$'; then
    echo "[ERROR] 用法: .scripts/docker/mobile.sh build <android|ios|harmonyos|all> [prod|test|dev] [--skip-native]"
    exit 1
  fi

  # Android 的 make-apk.sh 没有 --skip-native 概念（无独立的可交接中间态），显式说明避免静默失效
  if [ "$extra" = "--skip-native" ] && [ "$target" = "android" ]; then
    echo "[提示] Android 端无 --skip-native：改为全流程打包（或对 ios/harmonyos 使用）"
    extra=""
  fi

  local rc=0 failed="" t dir script
  if [ "$target" != "all" ]; then
    echo ">>>>>> 构建 $target（$mode $extra）"
    run_module "$target" "$mode $extra" || rc=1
  else
    for t in android ios harmonyos; do
      echo ""
      echo ">>>>>> 构建 $t（$mode $extra）"
      run_module "$t" "$mode $extra" || { rc=1; failed="$failed $t"; }
    done
  fi

  echo ""
  if [ "$rc" = 0 ]; then
    echo "构建完成。产物命名规范: easyaiot-<版本>-<模式>-<android|ios|harmonyos>.<apk|ipa|hap>"
  else
    echo "以下端构建失败:$failed（以上方日志定位原因）"
  fi
  return $rc
}

cmd_bump() {
  local ver="${1:-}" code="${2:-}"
  if ! printf '%s' "$ver" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$' \
     || ! printf '%s' "$code" | grep -qE '^[0-9]+$'; then
    echo "[ERROR] 用法: .scripts/docker/mobile.sh bump <x.y.z> <整数versionCode>，例: .scripts/docker/mobile.sh bump 1.0.1 101"
    exit 1
  fi

  # 改之前先确认五个目标都能解析，避免改一半留下不一致
  local mani a i h bad=0 p
  mani=$(read_manifest); a=$(read_android); i=$(read_ios); h=$(read_harmony)
  for p in "$mani" "$a" "$i" "$h"; do
    if [ -z "${p%%|*}" ] || [ -z "${p##*|}" ]; then
      bad=1
    fi
  done
  if [ "$bad" = 1 ]; then
    echo "[ERROR] 存在解析失败的版本文件，请先人工检查后再执行 bump"; exit 1
  fi

  echo "版本号升级: versionName=$ver  versionCode=$code（共 5 处）"

  VER="$ver" CODE="$code" perl -pi -e "s/'versionName':\s*'[^']*'/'versionName': '\$ENV{VER}'/" "$FRONT/manifest.config.ts"
  VER="$ver" CODE="$code" perl -pi -e "s/'versionCode':\s*'[^']*'/'versionCode': '\$ENV{CODE}'/" "$FRONT/manifest.config.ts"
  VER="$ver" CODE="$code" perl -pi -e 's/versionName\s+"[^"]+"/versionName "$ENV{VER}"/; s/versionCode\s+[0-9]+/versionCode $ENV{CODE}/' "$ROOT/ANDROID/app/build.gradle"
  VER="$ver" perl -pi -e 's/appver="[^"]+"/appver="$ENV{VER}"/' "$ROOT/ANDROID/app/src/main/assets/data/dcloud_control.xml"
  VER="$ver" CODE="$code" perl -pi -e 's/MARKETING_VERSION = [^;]+;/MARKETING_VERSION = $ENV{VER};/g; s/CURRENT_PROJECT_VERSION = [0-9]+;/CURRENT_PROJECT_VERSION = $ENV{CODE};/g' "$ROOT/IOS/EasyAIoT.xcodeproj/project.pbxproj"
  VER="$ver" CODE="$code" perl -pi -e 's/"versionCode":\s*[0-9]+/"versionCode": $ENV{CODE}/; s/"versionName":\s*"[^"]+"/"versionName": "$ENV{VER}"/' "$ROOT/HARMONYOS/AppScope/app.json5"

  # 回读校验：全部一致才算成功
  mani=$(read_manifest); a=$(read_android); i=$(read_ios); h=$(read_harmony)
  if [ "$(agree "$a" "$mani")" != "一致" ] \
     || [ "$(agree "$i" "$mani")" != "一致" ] \
     || [ "$(agree "$h" "$mani")" != "一致" ]; then
    echo "[FAIL] 回读发现未对齐项: android=$(pair "$a") ios=$(pair "$i") harmonyos=$(pair "$h")"
    echo "       请人工核对上述文件后重试"; exit 1
  fi

  echo ""
  echo "SUCCESS: 五处版本号已统一为 $ver/$code"
  echo "  1. APP/manifest.config.ts                 ('versionName'/'versionCode')"
  echo "  2. ANDROID/app/build.gradle               (versionName/versionCode)"
  echo "  3. ANDROID/.../assets/data/dcloud_control.xml (appver)"
  echo "  4. IOS/EasyAIoT.xcodeproj/project.pbxproj (Debug+Release 两处)"
  echo "  5. HARMONYOS/AppScope/app.json5           (versionName/versionCode)"
}

cmd_artifacts() {
  local found=0 f
  for f in "$ROOT"/ANDROID/easyaiot-* "$ROOT"/IOS/easyaiot-* "$ROOT"/HARMONYOS/easyaiot-* \
           "$ROOT"/ANDROID/EasyAIoT-* "$ROOT"/IOS/EasyAIoT-* "$ROOT"/HARMONYOS/EasyAIoT-*; do
    [ -e "$f" ] || continue
    ls -lh "$f" | awk '{print $NF "  " $5}'
    found=1
  done
  [ "$found" = 1 ] || echo "（暂无安装包成品，先执行 .scripts/docker/mobile.sh build ...）"
}

cmd_clean() {
  local target="${1:-}"
  if ! printf '%s' "$target" | grep -qE '^(android|ios|harmonyos|all)$'; then
    echo "[ERROR] 用法: .scripts/docker/mobile.sh clean <android|ios|harmonyos|all>"; exit 1
  fi
  clean_dir() {
    rm -f "$1"/easyaiot-* "$1"/EasyAIoT-* 2>/dev/null || true
    echo "已清理 $1 下打包成品"
  }
  case "$target" in
    android)   clean_dir "$ROOT/ANDROID" ;;
    ios)       clean_dir "$ROOT/IOS" ;;
    harmonyos) clean_dir "$ROOT/HARMONYOS" ;;
    all)       clean_dir "$ROOT/ANDROID"; clean_dir "$ROOT/IOS"; clean_dir "$ROOT/HARMONYOS" ;;
  esac
}

case "${1:-help}" in
  status)    shift; cmd_status "$@" ;;
  build)     shift; cmd_build "$@" ;;
  bump)      shift; cmd_bump "$@" ;;
  artifacts) cmd_artifacts ;;
  clean)     shift; cmd_clean "$@" ;;
  help|-h|--help|"") _print_usage ;;
  *) echo "未知命令: $1"; echo ""; _print_usage; exit 1 ;;
esac
