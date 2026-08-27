#!/usr/bin/env bash
# ================================================================
# EasyAIoT iOS 一键打包脚本（macOS；Linux/CI 可加 --skip-native 验证到同步为止）
#
# 用法:
#   ./make-ipa.sh                    # 默认：模拟器 .app（免签名，开箱即跑）
#   ./make-ipa.sh --device           # 真机/分发：archive + 导出 ipa（需签名配置）
#   ./make-ipa.sh [--device] [--skip-native] [prod|test|dev]
#
# 流程: 版本校验 -> APP 前端 H5 构建 -> 同步 www 资源 -> xcodebuild
# 产物: IOS/easyaiot-<版本>-<模式>-ios-sim.app 或 easyaiot-<版本>-<模式>-ios.ipa
#
# 环境要求见 README.md；版本号一致性由本脚本强制校验
# ================================================================
set -euo pipefail

MODE="prod"
SKIP_NATIVE=false
BUILD_DEVICE=false

for arg in "$@"; do
  case "$arg" in
    --skip-native) SKIP_NATIVE=true ;;
    --device)      BUILD_DEVICE=true ;;
    prod|test|dev) MODE="$arg" ;;
    *) echo "未知参数: $arg（支持 prod|test|dev、--device、--skip-native）"; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$ROOT")"
FRONT="$WORKSPACE/APP"
IOS="$ROOT"

case "$MODE" in
  prod) BUILD_CMD=(pnpm build:h5:prod) ;;
  test) BUILD_CMD=(pnpm build:h5:test) ;;
  dev)  BUILD_CMD=(pnpm build:h5) ;;
esac

if ! command -v pnpm >/dev/null 2>&1; then
  echo "[ERROR] 未找到 pnpm，请先安装 Node>=20 与 pnpm>=9"; exit 1
fi

# ---- [1/5] 版本一致性校验：两处必须完全一致 -----------------------
PBX_VER=$(sed -nE 's/^[[:space:]]*MARKETING_VERSION[[:space:]]*=[[:space:]]*"?([^";]+)"?;.*/\1/p' "$IOS/EasyAIoT.xcodeproj/project.pbxproj" | head -1)
PBX_CODE=$(sed -nE 's/^[[:space:]]*CURRENT_PROJECT_VERSION[[:space:]]*=[[:space:]]*([0-9]+);.*/\1/p' "$IOS/EasyAIoT.xcodeproj/project.pbxproj" | head -1)
MANI_VER=$(grep -oE "'versionName':[[:space:]]*'[^']+'" "$FRONT/manifest.config.ts" | head -1 | sed "s/.*'\(.*\)'/\1/")
MANI_CODE=$(grep -oE "'versionCode':[[:space:]]*'[0-9]+'" "$FRONT/manifest.config.ts" | head -1 | grep -oE '[0-9]+')

echo "[1/5] 版本一致性校验"
echo "      pbxproj=$PBX_VER/$PBX_CODE  manifest=$MANI_VER/$MANI_CODE"
if [ -z "$PBX_VER" ] || [ -z "$PBX_CODE" ] || [ -z "$MANI_VER" ] || [ -z "$MANI_CODE" ]; then
  echo "==== 版本信息解析失败，打包终止 ===="; exit 1
fi
if [ "$PBX_VER" != "$MANI_VER" ] || [ "$((10#$PBX_CODE))" != "$((10#$MANI_CODE))" ]; then
  echo "==== 版本不一致，打包终止。以下两处保持一致后重试： ===="
  echo "  1. IOS/EasyAIoT.xcodeproj/project.pbxproj   MARKETING_VERSION / CURRENT_PROJECT_VERSION"
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
DST="$IOS/EasyAIoT/www"
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
  echo " SYNCED (--skip-native)：第 1~3 步完成，www 已就绪于 EasyAIoT/www/"
  echo " 跳过原生编译：在装有 Xcode 的机器上不带该参数重跑即可出包"
  echo "================================================================"
  exit 0
fi

# ---- [4/5] 原生打包 ----------------------------------------------
echo "[4/5] xcodebuild（--device=$BUILD_DEVICE）"
if ! command -v xcodebuild >/dev/null 2>&1; then
  echo "[ERROR] 未找到 xcodebuild。iOS 编译需要 macOS + Xcode 16+；"
  echo "        Linux/CI 请使用 --skip-native 只完成前端构建与资源同步。"; exit 1
fi

cd "$IOS"
mkdir -p build
IPA=""
if [ "$BUILD_DEVICE" = true ]; then
  # 真机/分发：校验 ExportOptions.plist 是否仍是占位 Team ID
  FLAT=$(tr '\n\t' '  ' < "$IOS/ExportOptions.plist")
  TEAM=$(printf '%s' "$FLAT" | sed -nE 's#.*<key>teamID</key> *<string>([^<]*)</string>.*#\1#p')
  if [ -z "$TEAM" ] || [ "$TEAM" = "YOUR_TEAM_ID" ]; then
    echo "[ERROR] ExportOptions.plist 的 teamID 还是占位值 YOUR_TEAM_ID，无法导出 ipa。"
    echo "        在 Xcode → Settings → Accounts 查看 Team ID 后替换，或先用默认模拟器流程验证。"
    exit 1
  fi
  xcodebuild -quiet archive -project EasyAIoT.xcodeproj -scheme EasyAIoT \
    -configuration Release -sdk iphoneos -archivePath build/EasyAIoT.xcarchive
  rm -rf build/export
  xcodebuild -quiet -exportArchive -archivePath build/EasyAIoT.xcarchive \
    -exportOptionsPlist ExportOptions.plist -exportPath build/export
  IPA=$(find build/export -name '*.ipa' | head -1 || true)
  if [ -z "$IPA" ]; then
    echo "[ERROR] 导出目录未找到 ipa：build/export"; exit 1
  fi
else
  xcodebuild -quiet build -project EasyAIoT.xcodeproj -scheme EasyAIoT \
    -configuration Release -sdk iphonesimulator -derivedDataPath build \
    CODE_SIGNING_ALLOWED=NO
fi

# ---- [5/5] 输出成品 ----------------------------------------------
if [ "$BUILD_DEVICE" = true ]; then
  OUT="$IOS/easyaiot-$PBX_VER-$MODE-ios.ipa"
  cp -f "$IPA" "$OUT"
  KIND="release.ipa（真机/分发）"
else
  OUT="$IOS/easyaiot-$PBX_VER-$MODE-ios-sim.app"
  rm -rf "$OUT"
  cp -R "build/Build/Products/Release-iphonesimulator/EasyAIoT.app" "$OUT"
  KIND="sim.app（模拟器，免签名）"
fi

echo ""
echo "================================================================"
echo " SUCCESS: $OUT ($KIND)"
echo " Bundle ID: com.basiclab.iot.app   后端地址见 APP/env/.env 的 VITE_SERVER_BASEURL"
echo "================================================================"
