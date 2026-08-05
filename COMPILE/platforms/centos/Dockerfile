# EasyAIoT COMPILE - CentOS/RHEL EL7/EL8/EL9 container build
# Build args: BASE_IMAGE, EL_RELEASE=7|8|9, BUILD_RPM, PANEL_VERSION
# 前端由宿主机构建后拷入上下文（避免容器内 npm / 交叉平台问题）

ARG BASE_IMAGE=quay.io/centos/centos:stream9
ARG EL_RELEASE=9

FROM ${BASE_IMAGE} AS builder

ARG BUILD_RPM=1
ARG PANEL_VERSION=
ARG EL_RELEASE=9
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COMPILE_OUT=/out \
    PANEL_VERSION=${PANEL_VERSION} \
    EL_RELEASE=${EL_RELEASE} \
    PANEL_DIST_TAG=el${EL_RELEASE} \
    PANEL_PUBLISH_OS=el${EL_RELEASE} \
    COMPILE_OUT_SKIP_LEGACY_LINK=1

WORKDIR /src

# EL7/EL8 EOL：官方 mirrorlist 已失效，改 vault；Rocky/Alma 不受影响
RUN set -eux; \
    if [ "${EL_RELEASE}" = "7" ]; then \
      sed -i \
        -e 's|^mirrorlist=|#mirrorlist=|g' \
        -e 's|^#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' \
        /etc/yum.repos.d/CentOS-*.repo; \
      yum -y install epel-release || true; \
      if ls /etc/yum.repos.d/epel*.repo >/dev/null 2>&1; then \
        sed -i \
          -e 's|^metalink=|#metalink=|g' \
          -e 's|^#baseurl=https://download.fedoraproject.org/pub/epel|baseurl=https://archives.fedoraproject.org/pub/archive/epel|g' \
          -e 's|^baseurl=https://download.fedoraproject.org/pub/epel|baseurl=https://archives.fedoraproject.org/pub/archive/epel|g' \
          /etc/yum.repos.d/epel*.repo; \
      fi; \
      yum -y install centos-release-scl || true; \
      if ls /etc/yum.repos.d/CentOS-SCLo*.repo >/dev/null 2>&1; then \
        sed -i \
          -e 's|^mirrorlist=|#mirrorlist=|g' \
          -e 's|^#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' \
          /etc/yum.repos.d/CentOS-SCLo*.repo; \
      fi; \
      if yum -y install python38 python38-devel python38-pip gcc gcc-c++ make rpm-build findutils which tar gzip; then \
        ln -sf /usr/bin/python3.8 /usr/local/bin/python3; \
        ln -sf /usr/bin/pip3.8 /usr/local/bin/pip3 || true; \
      else \
        yum -y install \
          rh-python38 rh-python38-python-devel rh-python38-python-pip \
          gcc gcc-c++ make rpm-build findutils which tar gzip; \
      fi; \
      yum clean all; \
    elif [ "${EL_RELEASE}" = "8" ]; then \
      if ls /etc/yum.repos.d/CentOS-*.repo >/dev/null 2>&1; then \
        sed -i \
          -e 's|^mirrorlist=|#mirrorlist=|g' \
          -e 's|^#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' \
          /etc/yum.repos.d/CentOS-*.repo; \
      fi; \
      dnf -y install \
        python39 python39-devel python39-pip \
        gcc gcc-c++ make rpm-build findutils which tar gzip \
        && dnf clean all; \
    else \
      dnf -y install \
        python3 python3-pip python3-devel \
        gcc gcc-c++ make rpm-build findutils which tar gzip \
        && dnf clean all; \
    fi

COPY . /src
RUN test -f /src/PANEL/ui/dist/index.html

# 启用 SCL / 保证 python3 指向可用解释器后执行本机构建
RUN set -eux; \
    if [ "${EL_RELEASE}" = "7" ]; then \
      if [ -f /opt/rh/rh-python38/enable ]; then \
        source /opt/rh/rh-python38/enable; \
        ln -sf "$(command -v python3)" /usr/local/bin/python3; \
        ln -sf "$(command -v pip3)" /usr/local/bin/pip3 || true; \
      fi; \
    elif [ "${EL_RELEASE}" = "8" ]; then \
      alternatives --set python3 /usr/bin/python3.9 2>/dev/null \
        || ln -sf /usr/bin/python3.9 /usr/local/bin/python3; \
    fi; \
    if [ "${BUILD_RPM}" = "1" ]; then \
      SKIP_UI_BUILD=1 EL_RELEASE="${EL_RELEASE}" \
        bash COMPILE/platforms/centos/build.sh --el"${EL_RELEASE}" --local --rpm ; \
    else \
      SKIP_UI_BUILD=1 EL_RELEASE="${EL_RELEASE}" \
        bash COMPILE/platforms/centos/build.sh --el"${EL_RELEASE}" --local --no-rpm ; \
    fi

FROM scratch AS export
COPY --from=builder /out/ /out/
