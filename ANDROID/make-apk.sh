#!/usr/bin/env bash
# ================================================================
# EasyAIoT APK 一键打包脚本（Linux / macOS）
#
# 用法:
#   ./make-apk.sh            # 生产模式（production）
#   ./make-apk.sh test       # 测试模式（test）
#   ./make-apk.sh dev        # 开发模式（development）
#
# 流程: 版本校验 -> APP 前端构建 -> 同步 www 资源 -> Gradle 打包
# 产物: ANDROID/easyaiot-<版本>-<模式>-android.apk
#
# 环境要求见 README.md；Android SDK 路径配置在 local.properties
# ================================================================
set -euo pipefail

MODE="${1:-prod}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$ROOT")"
FRONT="$WORKSPACE/APP"
ANDROID="$ROOT"
APPID="__UNI__8A5A71D"

case "$MODE" in
  prod) BUILD_CMD="pnpm build:app:prod" ;;
  test) BUILD_CMD="pnpm build:app:test" ;;
  dev)  BUILD_CMD="pnpm build:app" ;;
  *) echo "未知模式: $MODE（可选 prod|test|dev）"; exit 1 ;;
esac

if ! command -v pnpm >/dev/null 2>&1; then
  echo "[ERROR] 未找到 pnpm，请先安装 Node>=20 与 pnpm>=9"; exit 1
fi
if ! command -v java >/dev/null 2>&1; then
  echo "[ERROR] 未找到 java，请安装 JDK 17 及以上并配置 JAVA_HOME"; exit 1
fi

# ---- [1/5] 版本一致性校验：三处必须完全一致 -----------------------
GRADLE_VER=$(sed -nE 's/^[[:space:]]*versionName[[:space:]]+"([^"]+)".*/\1/p' "$ANDROID/app/build.gradle" | head -1)
GRADLE_CODE=$(sed -nE 's/^[[:space:]]*versionCode[[:space:]]+([0-9]+).*/\1/p' "$ANDROID/app/build.gradle" | head -1)
MANI_VER=$(grep -oE "'versionName':[[:space:]]*'[^']+'" "$FRONT/manifest.config.ts" | head -1 | sed "s/.*'\(.*\)'/\1/")
MANI_CODE=$(grep -oE "'versionCode':[[:space:]]*'[0-9]+'" "$FRONT/manifest.config.ts" | head -1 | grep -oE '[0-9]+')
CTRL_VER=$(sed -nE 's/.*appver="([^"]+)".*/\1/p' "$ANDROID/app/src/main/assets/data/dcloud_control.xml")

echo "[1/5] 版本一致性校验"
echo "      gradle=$GRADLE_VER/$GRADLE_CODE  manifest=$MANI_VER/$MANI_CODE  dcloud_control=$CTRL_VER"
if [ -z "$GRADLE_VER" ] || [ -z "$MANI_VER" ] || [ -z "$CTRL_VER" ] || [ -z "$GRADLE_CODE" ]; then
  echo "==== 版本信息解析失败，打包终止 ===="; exit 1
fi
if [ "$GRADLE_VER" != "$MANI_VER" ] || [ "$GRADLE_VER" != "$CTRL_VER" ] || [ "$GRADLE_CODE" != "$MANI_CODE" ]; then
  echo "==== 版本不一致，打包终止。以下四处保持一致后重试： ===="
  echo "  1. ANDROID/app/build.gradle                     versionName / versionCode"
  echo "  2. APP/manifest.config.ts                       'versionName' / 'versionCode'"
  echo "  3. ANDROID/app/src/main/assets/data/dcloud_control.xml   appver"
  exit 1
fi

# ---- [2/5] 构建前端 App 资源 -------------------------------------
echo "[2/5] 构建前端资源（mode=$MODE）: $BUILD_CMD"
(cd "$FRONT" && eval "$BUILD_CMD")

SRC="$FRONT/dist/build/app"
if [ ! -f "$SRC/manifest.json" ]; then
  echo "[ERROR] 未找到 $SRC/manifest.json，前端构建可能失败"; exit 1
fi
if ! grep -q "\"$GRADLE_VER\"" "$SRC/manifest.json" && ! grep -q "$GRADLE_VER" "$SRC/manifest.json"; then
  echo "[ERROR] 构建产物 manifest.json 中未找到版本号 $GRADLE_VER，疑似旧缓存"; exit 1
fi

# ---- [3/5] 同步 www 资源到壳工程 --------------------------------
echo "[3/5] 同步 www 资源到壳工程（$APPID）"
DST="$ANDROID/app/src/main/assets/apps/$APPID/www"
rm -rf "$DST"
mkdir -p "$DST"
cp -a "$SRC/." "$DST/"

# ---- [4/5] Gradle 打包 ------------------------------------------
echo "[4/5] Gradle assembleRelease"
cd "$ANDROID"
./gradlew assembleRelease --no-daemon "-Dorg.gradle.jvmargs=-Xmx3g"

APK="$ANDROID/app/build/outputs/apk/release/app-release.apk"
if [ ! -f "$APK" ]; then
  echo "[ERROR] 未找到 APK 产物: $APK"; exit 1
fi

# ---- [5/5] 输出成品 ----------------------------------------------
OUT="$ANDROID/easyaiot-$GRADLE_VER-$MODE-android.apk"
cp -f "$APK" "$OUT"

echo ""
echo "================================================================"
echo " SUCCESS: $OUT"
echo " 签名: app/iot.jks (alias=iot)   包名: com.basiclab.iot.app"
echo "================================================================"
