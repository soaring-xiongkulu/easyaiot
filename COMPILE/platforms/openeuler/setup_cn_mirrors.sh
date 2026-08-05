#!/usr/bin/env bash
# 将 openEuler 容器内 dnf 源切换为国内镜像（默认华为云），并禁用慢速官方源
# 用法（容器内）: bash COMPILE/platforms/openeuler/setup_cn_mirrors.sh
set -euo pipefail

CN_MIRROR_VENDOR="${COMPILE_CN_MIRROR:-huawei}"
# openEuler 版本目录名（与基础镜像 24.03 对应）
OE_RELEASE_DIR="${COMPILE_OPENEULER_RELEASE_DIR:-openEuler-24.03-LTS}"

case "$CN_MIRROR_VENDOR" in
  huawei|hw)
    OE_MIRROR="${COMPILE_OPENEULER_MIRROR:-https://repo.huaweicloud.com/openeuler/${OE_RELEASE_DIR}}"
    ;;
  aliyun|ali)
    OE_MIRROR="${COMPILE_OPENEULER_MIRROR:-https://mirrors.aliyun.com/openeuler/${OE_RELEASE_DIR}}"
    ;;
  tuna|tsinghua)
    OE_MIRROR="${COMPILE_OPENEULER_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/openeuler/${OE_RELEASE_DIR}}"
    ;;
  *)
    echo "[COMPILE/openeuler-cn] 未知 COMPILE_CN_MIRROR=${CN_MIRROR_VENDOR}" >&2
    exit 1
    ;;
esac

echo "[COMPILE/openeuler-cn] vendor=${CN_MIRROR_VENDOR} mirror=${OE_MIRROR}"

# 覆盖为精简国内源（避免 dnf update 拉全量官方 everything）
rm -f /etc/yum.repos.d/*.repo
cat > /etc/yum.repos.d/openEuler-cn.repo <<EOF
[OS]
name=openEuler-\$releasever - OS
baseurl=${OE_MIRROR}/OS/\$basearch/
enabled=1
gpgcheck=0

[everything]
name=openEuler-\$releasever - everything
baseurl=${OE_MIRROR}/everything/\$basearch/
enabled=1
gpgcheck=0

[EPOL]
name=openEuler-\$releasever - EPOL
baseurl=${OE_MIRROR}/EPOL/main/\$basearch/
enabled=1
gpgcheck=0

[update]
name=openEuler-\$releasever - update
baseurl=${OE_MIRROR}/update/\$basearch/
enabled=1
gpgcheck=0
EOF

dnf clean all >/dev/null 2>&1 || true
