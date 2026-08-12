#!/usr/bin/env bash
# EasyAIoT EDGE 离线打包（self-contained）
# 用法:
#   bash EDGE/pack_linux.sh
#   EDGE_ARCH=arm64 bash EDGE/pack_linux.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

arch_key() {
  local m="${EDGE_ARCH:-$(uname -m)}"
  m="$(echo "$m" | tr '[:upper:]' '[:lower:]')"
  case "$m" in
    aarch64|arm64) echo "arm64" ;;
    *) echo "x64" ;;
  esac
}

ARCH="$(arch_key)"
RID="linux-$ARCH"
OUT_DIR="$ROOT/.bundle-edge/$ARCH"
STAGE="$OUT_DIR/stage"
TARBALL="$OUT_DIR/easyaiot-edge-$ARCH.tar.gz"
HOST_PROJECT="$ROOT/src/EasyAIoT.Edge.Host/EasyAIoT.Edge.Host.csproj"
PUBLISH_DIR="$STAGE/opt/easyaiot-edge"

echo "[EDGE] arch=$ARCH rid=$RID"

if ! command -v dotnet >/dev/null 2>&1; then
  echo "[EDGE] dotnet SDK not found"
  exit 1
fi

rm -rf "$STAGE"
mkdir -p "$PUBLISH_DIR"

dotnet publish "$HOST_PROJECT" \
  -c Release \
  -r "$RID" \
  --self-contained true \
  -p:PublishSingleFile=true \
  -p:IncludeNativeLibrariesForSelfExtract=true \
  -o "$PUBLISH_DIR"

mkdir -p "$PUBLISH_DIR/data"
if [[ -f "$ROOT/src/EasyAIoT.Edge.Host/data/device-jobs.json" ]]; then
  cp "$ROOT/src/EasyAIoT.Edge.Host/data/device-jobs.json" "$PUBLISH_DIR/data/"
fi

cat > "$STAGE/opt/easyaiot-edge/run.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
exec ./EasyAIoT.Edge.Host
EOF
chmod +x "$STAGE/opt/easyaiot-edge/run.sh"

mkdir -p "$STAGE/lib/systemd/system"
cat > "$STAGE/lib/systemd/system/easyaiot-edge.service" <<EOF
[Unit]
Description=EasyAIoT EDGE Collector
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/easyaiot-edge
ExecStart=/opt/easyaiot-edge/run.sh
Restart=always
RestartSec=5
Environment=DOTNET_ENVIRONMENT=Production

[Install]
WantedBy=multi-user.target
EOF

mkdir -p "$OUT_DIR"
tar -czf "$TARBALL" -C "$STAGE" opt lib
echo "[EDGE] bundle: $TARBALL"
ls -lh "$TARBALL"
