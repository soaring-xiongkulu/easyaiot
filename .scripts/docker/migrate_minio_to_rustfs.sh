#!/usr/bin/env bash

# Copy object data from a running MinIO endpoint to RustFS through the S3 API.
# The script never modifies the source. Credentials are read from environment.

set -euo pipefail

SOURCE_ENDPOINT="${MINIO_SOURCE_ENDPOINT:-http://127.0.0.1:19000}"
SOURCE_ACCESS_KEY="${MINIO_SOURCE_ACCESS_KEY:-minioadmin}"
SOURCE_SECRET_KEY="${MINIO_SOURCE_SECRET_KEY:-}"
DEST_ENDPOINT="${RUSTFS_DEST_ENDPOINT:-http://127.0.0.1:9000}"
DEST_ACCESS_KEY="${RUSTFS_ACCESS_KEY:-minioadmin}"
DEST_SECRET_KEY="${RUSTFS_SECRET_KEY:-}"
MC_IMAGE="${MC_IMAGE:-minio/mc:latest}"
MODE="sync"

usage() {
    cat <<'EOF'
Usage: migrate_minio_to_rustfs.sh [--dry-run|--watch|--verify]

Required environment variables:
  MINIO_SOURCE_SECRET_KEY   Source MinIO secret key
  RUSTFS_SECRET_KEY        Destination RustFS secret key

Optional environment variables:
  MINIO_SOURCE_ENDPOINT    Default: http://127.0.0.1:19000
  MINIO_SOURCE_ACCESS_KEY  Default: minioadmin
  RUSTFS_DEST_ENDPOINT     Default: http://127.0.0.1:9000
  RUSTFS_ACCESS_KEY        Default: minioadmin
  MC_IMAGE                 Default: minio/mc:latest

Modes:
  --dry-run  Show the objects that would be copied
  --watch    Initial copy followed by continuous incremental synchronization
  --verify   Compare source and destination without copying
EOF
}

case "${1:-}" in
    "") ;;
    --dry-run) MODE="dry-run" ;;
    --watch) MODE="watch" ;;
    --verify) MODE="verify" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
esac

if [[ -z "$SOURCE_SECRET_KEY" || -z "$DEST_SECRET_KEY" ]]; then
    echo "MINIO_SOURCE_SECRET_KEY and RUSTFS_SECRET_KEY must be set." >&2
    exit 2
fi

config_dir="$(mktemp -d "${TMPDIR:-/tmp}/easyaiot-rustfs-migration.XXXXXX")"
cleanup() {
    # minio/mc runs as root and may create mode-0700 directories. Clean them
    # through a short-lived container, then remove the now-empty host folder.
    docker run --rm -v "${config_dir}:/cleanup" alpine:3.22 \
        find /cleanup -mindepth 1 -depth -delete >/dev/null 2>&1 || true
    find "$config_dir" -depth -delete 2>/dev/null || true
}
trap cleanup EXIT

mc() {
    docker run --rm --network host \
        -v "${config_dir}:/root/.mc" \
        "$MC_IMAGE" "$@"
}

echo "Configuring source and destination aliases..."
mc alias set minio-source "$SOURCE_ENDPOINT" "$SOURCE_ACCESS_KEY" "$SOURCE_SECRET_KEY" >/dev/null
mc alias set rustfs-dest "$DEST_ENDPOINT" "$DEST_ACCESS_KEY" "$DEST_SECRET_KEY" >/dev/null
mc ls minio-source >/dev/null
mc ls rustfs-dest >/dev/null

case "$MODE" in
    dry-run)
        mc mirror --dry-run minio-source/ rustfs-dest/
        ;;
    watch)
        echo "Starting continuous mirror. Stop it only after writes are paused and the final changes are synchronized."
        mc mirror --watch --overwrite minio-source/ rustfs-dest/
        ;;
    verify)
        mc diff minio-source/ rustfs-dest/
        ;;
    sync)
        mc mirror --overwrite minio-source/ rustfs-dest/
        echo "Copy finished. Run this script with --verify before cutover."
        ;;
esac
