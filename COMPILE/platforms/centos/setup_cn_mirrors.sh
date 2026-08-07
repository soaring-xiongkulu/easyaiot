#!/usr/bin/env bash
# 将 CentOS/RHEL/Rocky 容器内 yum/dnf 源切换为国内镜像（默认华为云）
# 用法（容器内）:
#   EL_RELEASE=7|8|9 bash COMPILE/platforms/centos/setup_cn_mirrors.sh
set -euo pipefail

EL_RELEASE="${EL_RELEASE:-9}"
# 可用: huawei | aliyun | tuna
CN_MIRROR_VENDOR="${COMPILE_CN_MIRROR:-huawei}"

case "$CN_MIRROR_VENDOR" in
  huawei|hw)
    EL7_VAULT="${COMPILE_EL7_MIRROR:-https://mirrors.huaweicloud.com/centos-vault/7.9.2009}"
    # 注意：华为云路径是 rockylinux，不是 rocky（rocky 会返回门户 HTML）
    ROCKY_MIRROR="${COMPILE_ROCKY_MIRROR:-https://mirrors.huaweicloud.com/rockylinux}"
    CENTOS_STREAM_MIRROR="${COMPILE_CENTOS_STREAM_MIRROR:-https://mirrors.huaweicloud.com/centos-stream}"
    ;;
  aliyun|ali)
    EL7_VAULT="${COMPILE_EL7_MIRROR:-https://mirrors.aliyun.com/centos-vault/7.9.2009}"
    ROCKY_MIRROR="${COMPILE_ROCKY_MIRROR:-https://mirrors.aliyun.com/rockylinux}"
    CENTOS_STREAM_MIRROR="${COMPILE_CENTOS_STREAM_MIRROR:-https://mirrors.aliyun.com/centos-stream}"
    ;;
  tuna|tsinghua)
    EL7_VAULT="${COMPILE_EL7_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/centos-vault/7.9.2009}"
    # 清华 rockylinux 路径偶发 404，回退阿里云
    ROCKY_MIRROR="${COMPILE_ROCKY_MIRROR:-https://mirrors.aliyun.com/rockylinux}"
    CENTOS_STREAM_MIRROR="${COMPILE_CENTOS_STREAM_MIRROR:-https://mirrors.tuna.tsinghua.edu.cn/centos-stream}"
    ;;
  *)
    echo "[COMPILE/cn-mirrors] 未知 COMPILE_CN_MIRROR=${CN_MIRROR_VENDOR}（huawei|aliyun|tuna）" >&2
    exit 1
    ;;
esac

echo "[COMPILE/cn-mirrors] EL=${EL_RELEASE} vendor=${CN_MIRROR_VENDOR}"

setup_el7() {
  local arch root
  arch="$(uname -m)"
  root="${EL7_VAULT}"
  if [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then
    if [ -n "${COMPILE_EL7_MIRROR:-}" ]; then
      root="$COMPILE_EL7_MIRROR"
    else
      case "$CN_MIRROR_VENDOR" in
        huawei|hw) root="https://mirrors.huaweicloud.com/centos-vault/altarch/7.9.2009" ;;
        aliyun|ali) root="https://mirrors.aliyun.com/centos-vault/altarch/7.9.2009" ;;
        tuna|tsinghua) root="https://mirrors.tuna.tsinghua.edu.cn/centos-vault/altarch/7.9.2009" ;;
      esac
    fi
  fi
  echo "[COMPILE/cn-mirrors] el7 root=${root} arch=${arch}"
  rm -f /etc/yum.repos.d/*.repo
  cat > /etc/yum.repos.d/CentOS-el7-cn.repo <<EOF
[base]
name=CentOS-7 - Base
baseurl=${root}/os/\$basearch/
gpgcheck=0
enabled=1

[updates]
name=CentOS-7 - Updates
baseurl=${root}/updates/\$basearch/
gpgcheck=0
enabled=1

[extras]
name=CentOS-7 - Extras
baseurl=${root}/extras/\$basearch/
gpgcheck=0
enabled=1

[centos-sclo-rh]
name=CentOS-7 - SCLo rh
baseurl=${root}/sclo/\$basearch/rh/
gpgcheck=0
enabled=1

[centos-sclo-sclo]
name=CentOS-7 - SCLo sclo
baseurl=${root}/sclo/\$basearch/sclo/
gpgcheck=0
enabled=1
EOF
}

setup_rocky() {
  # 镜像内文件名可能是 rocky*.repo 或 Rocky*.repo（大小写敏感）
  shopt -s nullglob
  local repos=(/etc/yum.repos.d/rocky*.repo /etc/yum.repos.d/Rocky*.repo)
  shopt -u nullglob
  if [ "${#repos[@]}" -eq 0 ]; then
    return 0
  fi
  echo "[COMPILE/cn-mirrors] rocky mirror=${ROCKY_MIRROR}"
  sed -i \
    -e 's|^mirrorlist=|#mirrorlist=|g' \
    -e 's|^#baseurl=http://dl.rockylinux.org/\$contentdir|baseurl='"${ROCKY_MIRROR}"'|g' \
    -e 's|^#baseurl=https://dl.rockylinux.org/\$contentdir|baseurl='"${ROCKY_MIRROR}"'|g' \
    -e 's|^baseurl=http://dl.rockylinux.org/\$contentdir|baseurl='"${ROCKY_MIRROR}"'|g' \
    -e 's|^baseurl=https://dl.rockylinux.org/\$contentdir|baseurl='"${ROCKY_MIRROR}"'|g' \
    "${repos[@]}"
}

setup_centos_stream() {
  if ls /etc/yum.repos.d/CentOS-Stream-*.repo >/dev/null 2>&1 \
     || ls /etc/yum.repos.d/centos*.repo >/dev/null 2>&1; then
    for f in /etc/yum.repos.d/CentOS-Stream-*.repo /etc/yum.repos.d/centos*.repo; do
      [ -f "$f" ] || continue
      sed -i \
        -e 's|^metalink=|#metalink=|g' \
        -e 's|^mirrorlist=|#mirrorlist=|g' \
        -e 's|^#baseurl=http://mirror.centos.org/\$contentdir/\$stream|baseurl='"${CENTOS_STREAM_MIRROR}"'/\$stream|g' \
        -e 's|^#baseurl=https://mirror.stream.centos.org|baseurl='"${CENTOS_STREAM_MIRROR}"'|g' \
        -e 's|^baseurl=https://mirror.stream.centos.org|baseurl='"${CENTOS_STREAM_MIRROR}"'|g' \
        "$f"
    done
  fi
}

case "$EL_RELEASE" in
  7) setup_el7 ;;
  8|9)
    setup_rocky
    setup_centos_stream
    ;;
  *)
    echo "[COMPILE/cn-mirrors] 不支持 EL=${EL_RELEASE}" >&2
    exit 1
    ;;
esac

if command -v dnf >/dev/null 2>&1; then
  dnf clean all >/dev/null 2>&1 || true
elif command -v yum >/dev/null 2>&1; then
  yum clean all >/dev/null 2>&1 || true
fi
