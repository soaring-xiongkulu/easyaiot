#!/usr/bin/env bash
# ================================================================
# EasyAIoT HAP 一键打包脚本（Linux / macOS / Windows-GitBash；
#   原生编译需 DevEco Studio 命令行工具或 HVIGOR_HOME；无工具链可 --skip-native）
#
# 用法:
#   ./make-hap.sh                    # 生产模式（production）
#   ./make-hap.sh test               # 测试模式（test）
#   ./make-hap.sh dev                # 开发模式（development）
#   ./make-hap.sh --skip-native      # 只做前端构建与资源同步
#
# 流程: 版本校验 -> APP 前端 H5 构建 -> 同步 rawfile 资源 -> hvigor assembleHap
# 产物: HARMONYOS/easyaiot-<版本>-<模式>-harmonyos.hap
#
# 环境要求见 README.md；版本号一致性由本脚本强制校验
# ================================================================
set -euo pipefail

MODE="prod"
SKIP_NATIVE=false

for arg in "$@"; do
  case "$arg" in
    --skip-native) SKIP_NATIVE=true ;;
    prod|test|dev) MODE="$arg" ;;
    *) echo "未知参数: $arg（支持 prod|test|dev、--skip-native）"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$ROOT")"
FRONT="$WORKSPACE/APP"
HARMONY="$ROOT"

case "$MODE" in
  prod) BUILD_CMD=(pnpm build:h5:prod) ;;
  test) BUILD_CMD=(pnpm build:h5:test) ;;
  dev)  BUILD_CMD=(pnpm build:h5) ;;
esac

if ! command -v pnpm >/dev/null 2>&1; then
  echo "[ERROR] 未找到 pnpm，请先安装 Node>=20 与 pnpm>=9"; exit 1
fi

# ---- [1/5] 版本一致性校验：两处必须完全一致 -----------------------
APP_VER=$(sed -nE 's/.*"versionName":[[:space:]]*"([^"]+)".*/\1/p' "$HARMONY/AppScope/app.json5" | head -1)
APP_CODE=$(sed -nE 's/.*"versionCode":[[:space:]]*([0-9]+).*/\1/p' "$HARMONY/AppScope/app.json5" | head -1)
MANI_VER=$(grep -oE "'versionName':[[:space:]]*'[^']+'" "$FRONT/manifest.config.ts" | head -1 | sed "s/.*'\(.*\)'/\1/")
MANI_CODE=$(grep -oE "'versionCode':[[:space:]]*'[0-9]+'" "$FRONT/manifest.config.ts" | head -1 | grep -oE '[0-9]+')

echo "[1/5] 版本一致性校验"
echo "      app.json5=$APP_VER/$APP_CODE  manifest=$MANI_VER/$MANI_CODE"
if [ -z "$APP_VER" ] || [ -z "$APP_CODE" ] || [ -z "$MANI_VER" ] || [ -z "$MANI_CODE" ]; then
  echo "==== 版本信息解析失败，打包终止 ===="; exit 1
fi
if [ "$APP_VER" != "$MANI_VER" ] || [ "$((10#$APP_CODE))" != "$((10#$MANI_CODE))" ]; then
  echo "==== 版本不一致，打包终止。以下两处保持一致后重试： ===="
  echo "  1. HARMONYOS/AppScope/app.json5             versionName / versionCode"
  echo "  2. APP/manifest.config.ts                   'versionName' / 'versionCode'"
  exit 1
fi

# ---- [2/5] 构建前端 H5 资源 ---------------------------------------
echo "[2/5] 构建前端资源（mode=$MODE）: ${BUILD_CMD[*]}"
(cd "$FRONT" && VITE_APP_PUBLIC_BASE=./ "${BUILD_CMD[@]}")

SRC="$FRONT/dist/build/h5"
if [ ! -f "$SRC/index.html" ]; then
  echo "[ERROR] 未找到 $SRC/index.html，前端构建可能失败"; exit 1
fi

# ---- [3/5] 同步 www 资源到壳工程 --------------------------------
echo "[3/5] 同步 www 资源到壳工程"
DST="$HARMONY/entry/src/main/resources/rawfile/www"
rm -rf "$DST"
mkdir -p "$DST"
cp -a "$SRC/." "$DST/"

# uni-app h5 构建只拷贝 src/static；根级 static/（jessibuca 播放器等公共脚本）需补充合并
if [ -d "$FRONT/static" ]; then
  mkdir -p "$DST/static"
  cp -a "$FRONT/static/." "$DST/static/"
fi

# 安全网：把残留的根绝对引用归一化为相对引用（构建已相对化时幂等无副作用）
perl -pi -e 's{(src|href)="/(assets|static)/}{$1="./$2/}g' "$DST/index.html"
ABS_LEFT=$(grep -cE '(src|href)="(/assets|/static)/' "$DST/index.html" || true)
if [ "${ABS_LEFT:-0}" != "0" ]; then
  echo "[ERROR] index.html 仍存在绝对路径引用 /assets、/static，请检查前端构建配置"; exit 1
fi

if [ "$SKIP_NATIVE" = true ]; then
  echo ""
  echo "================================================================"
  echo " SYNCED (--skip-native)：第 1~3 步完成，www 已就绪于 entry/src/main/resources/rawfile/www/"
  echo " 跳过原生编译：在装有 DevEco Studio 的机器上不带该参数重跑即可出包"
  echo "================================================================"
  exit 0
fi

# ---- [4/5] 原生打包 ----------------------------------------------
echo "[4/5] hvigor assembleHap"
cd "$HARMONY"

# SDK 缺失时给出提示（不强制：SDK 也可能由 DevEco 默认路径或 local.properties 提供）
if [ -z "${HOS_SDK_HOME:-}" ] && [ -z "${DEVECO_SDK_HOME:-}" ] \
  && [ ! -d "/Applications/DevEco-Studio.app/Contents/sdk" ]; then
  echo "[提示] 未在 HOS_SDK_HOME / DEVECO_SDK_HOME 检测到 HarmonyOS SDK。"
  echo "       若 hvigor 报 SDK 未找到，请安装 DevEco Studio 或设置上述环境变量。"
fi

./hvigorw assembleHap --mode module -p product=default -p buildMode=release

HAP=$(find entry/build -name '*.hap' 2>/dev/null | head -1 || true)
if [ -z "$HAP" ]; then
  echo "[ERROR] 构建目录未找到 hap 产物（entry/build/**/outputs）"; exit 1
fi

# ---- [5/5] 输出成品 ----------------------------------------------
OUT="$HARMONY/easyaiot-$APP_VER-$MODE-harmonyos.hap"
cp -f "$HAP" "$OUT"

echo ""
echo "================================================================"
echo " SUCCESS: $OUT"
echo " Bundle: com.basiclab.iot.app   真机安装需签名（见 README 第五节）"
echo "================================================================"
