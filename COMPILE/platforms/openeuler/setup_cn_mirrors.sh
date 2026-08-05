#!/usr/bin/env bash
# 将 openEuler 容器内 dnf 源切换为国内镜像（默认华为云）
# 保留镜像自带 repo 结构（含 LTS-SP3 等路径），仅替换官方域名，避免版本错配。
# 用法（容器内）: bash COMPILE/platforms/openeuler/setup_cn_mirrors.sh
set -euo pipefail

CN_MIRROR_VENDOR="${COMPILE_CN_MIRROR:-huawei}"

case "$CN_MIRROR_VENDOR" in
  huawei|hw)
    OE_HOST="${COMPILE_OPENEULER_MIRROR_HOST:-https://repo.huaweicloud.com/openeuler}"
    ;;
  aliyun|ali)
    OE_HOST="${COMPILE_OPENEULER_MIRROR_HOST:-https://mirrors.aliyun.com/openeuler}"
    ;;
  tuna|tsinghua)
    OE_HOST="${COMPILE_OPENEULER_MIRROR_HOST:-https://mirrors.tuna.tsinghua.edu.cn/openeuler}"
    ;;
  *)
    echo "[COMPILE/openeuler-cn] 未知 COMPILE_CN_MIRROR=${CN_MIRROR_VENDOR}" >&2
    exit 1
    ;;
esac

echo "[COMPILE/openeuler-cn] vendor=${CN_MIRROR_VENDOR} host=${OE_HOST}"

if ! ls /etc/yum.repos.d/*.repo >/dev/null 2>&1; then
  echo "[COMPILE/openeuler-cn] 未找到 /etc/yum.repos.d/*.repo" >&2
  exit 1
fi

# 替换官方 repo / metalink / gpgkey 域名为国内镜像，保留 openEuler-24.03-LTS-SP3 等路径
sed -i \
  -e "s|https\\?://repo\\.openeuler\\.org|${OE_HOST}|g" \
  -e 's|^metalink=|#metalink=|g' \
  /etc/yum.repos.d/*.repo

# 关闭 debuginfo / source 等非必需源，加快元数据下载
for f in /etc/yum.repos.d/*.repo; do
  awk '
    BEGIN {skip=0}
    /^\[/ {
      name=$0
      skip = (tolower(name) ~ /(debug|source|updateinfo)/)
    }
    skip && /^enabled=/ { print "enabled=0"; next }
    { print }
  ' "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
done

dnf clean all >/dev/null 2>&1 || true
