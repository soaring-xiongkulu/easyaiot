#!/usr/bin/env bash

# Non-destructive RustFS S3 compatibility check. A temporary bucket is created
# and removed. Existing buckets and objects are never touched.

set -euo pipefail

endpoint="${S3_ENDPOINT:-${RUSTFS_ENDPOINT:-127.0.0.1:9000}}"
access_key="${S3_ACCESS_KEY:-${RUSTFS_ACCESS_KEY:-minioadmin}}"
secret_key="${S3_SECRET_KEY:-${RUSTFS_SECRET_KEY:-basiclab@iot975248395}}"
secure="${S3_SECURE:-${RUSTFS_SECURE:-false}}"
mc_image="${MC_IMAGE:-minio/mc:latest}"
scheme="http"
[[ "$secure" == "true" ]] && scheme="https"
[[ "$endpoint" == http://* || "$endpoint" == https://* ]] || endpoint="${scheme}://${endpoint}"

suffix="$(date +%s)-$$"
bucket="easyaiot-rustfs-smoke-${suffix}"
object="checks/hello.txt"
expected="RustFS EasyAIoT S3 smoke ${suffix}"
config_volume="easyaiot-rustfs-smoke-mc-${suffix}"
created_bucket=false

mc() {
    docker run --rm --network host \
        -v "${config_volume}:/root/.mc" \
        "$mc_image" "$@"
}

cleanup() {
    if [[ "$created_bucket" == "true" ]]; then
        mc rm --force "rustfs/${bucket}/${object}" >/dev/null 2>&1 || true
        mc rb "rustfs/${bucket}" >/dev/null 2>&1 || true
    fi
    docker volume rm "$config_volume" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker volume create "$config_volume" >/dev/null
mc alias set rustfs "$endpoint" "$access_key" "$secret_key" >/dev/null
mc mb "rustfs/${bucket}" >/dev/null
created_bucket=true

printf '%s\n' "$expected" | docker run -i --rm --network host \
    -v "${config_volume}:/root/.mc" \
    "$mc_image" pipe "rustfs/${bucket}/${object}" >/dev/null

actual="$(mc cat "rustfs/${bucket}/${object}")"
[[ "$actual" == "$expected" ]] || {
    echo "RustFS download verification failed" >&2
    exit 1
}
mc stat "rustfs/${bucket}/${object}" >/dev/null

echo "RustFS S3 create/upload/download/stat verification: PASS"
