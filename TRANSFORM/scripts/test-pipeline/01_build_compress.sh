#!/usr/bin/env bash
# 步骤 01：无镜像则构建，并确保 gzip 压缩制品存在
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/_common.sh"

SKIP_BUILD="${1:-${SKIP_BUILD:-0}}"

log "=== [01] 打包 / 压缩 ==="
mkdir -p "$ROOT/dist"

if [[ "$SKIP_BUILD" == "1" || "$SKIP_BUILD" == "--skip-build" ]]; then
  log "跳过构建（--skip-build）"
else
  if docker_ok; then
    if docker image inspect "$TRANSFORM_IMAGE" >/dev/null 2>&1 && [[ -f "$GZ" || -f "$TAR" ]]; then
      ok "已有镜像与制品，跳过 docker build"
    else
      log "执行 build-image.sh …"
      bash "$SCRIPTS_DIR/build-image.sh"
    fi
  else
    log "Docker 不可用：跳过镜像构建（jar 模式仍可测后续步骤）"
    if [[ ! -f "$JAR" ]]; then
      log "打包 jar …"
      (cd "$ROOT" && mvn -pl transform-runtime -am package -DskipTests -q)
    fi
    [[ -f "$JAR" ]] || fail "缺少 jar: $JAR"
    ok "jar 就绪: $JAR"
    exit 0
  fi
fi

# 保证 gz
if [[ -f "$TAR" && ! -f "$GZ" ]]; then
  log "gzip 压缩 tar → tar.gz"
  gzip -c "$TAR" > "$GZ"
fi
if [[ -f "$GZ" && ! -f "$TAR" ]]; then
  log "从 tar.gz 解出 tar（兼容旧 load 路径）"
  gunzip -c "$GZ" > "$TAR"
fi

if [[ -f "$GZ" ]]; then
  ok "压缩制品: $GZ ($(du -h "$GZ" | awk '{print $1}'))"
elif [[ -f "$TAR" ]]; then
  ok "制品: $TAR ($(du -h "$TAR" | awk '{print $1}'))"
else
  fail "缺少 dist 制品；请先 build-image.sh 或去掉 --skip-build"
fi

# 本机 load（为后续 docker 部署准备）
if docker_ok; then
  if docker image inspect "$TRANSFORM_IMAGE" >/dev/null 2>&1; then
    ok "本机已有镜像 $TRANSFORM_IMAGE"
  elif [[ -f "$GZ" ]]; then
    log "gunzip | docker load …"
    gunzip -c "$GZ" | docker load
    ok "docker load 完成"
  else
    docker load -i "$TAR"
    ok "docker load 完成"
  fi
fi
