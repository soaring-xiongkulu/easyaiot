# EasyAIoT COMPILE - CentOS/RHEL ARM64 EL7/EL8/EL9 cross build
# 需本机已注册 qemu-aarch64；yum/dnf 默认国内源
ARG BASE_IMAGE=rockylinux:9
ARG EL_RELEASE=9

FROM ${BASE_IMAGE} AS builder

ARG BUILD_RPM=1
ARG PANEL_VERSION=
ARG EL_RELEASE=9
ARG COMPILE_CN_MIRROR=huawei
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COMPILE_OUT=/out \
    PANEL_VERSION=${PANEL_VERSION} \
    EL_RELEASE=${EL_RELEASE} \
    PANEL_DIST_TAG=el${EL_RELEASE} \
    PANEL_PUBLISH_OS=el${EL_RELEASE} \
    PANEL_ARCH=aarch64 \
    COMPILE_CN_MIRROR=${COMPILE_CN_MIRROR} \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /src

COPY COMPILE/platforms/centos/setup_cn_mirrors.sh /tmp/setup_cn_mirrors.sh

RUN set -eux; \
    bash /tmp/setup_cn_mirrors.sh; \
    if [ "${EL_RELEASE}" = "7" ]; then \
      yum -y install \
        rh-python38 rh-python38-python-devel rh-python38-python-pip \
        gcc gcc-c++ make rpm-build findutils which tar gzip; \
      yum clean all; \
    elif [ "${EL_RELEASE}" = "8" ]; then \
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

RUN set -eux; \
    if [ "${EL_RELEASE}" = "7" ]; then \
      if [ -f /opt/rh/rh-python38/enable ]; then \
        set +u; \
        # shellcheck disable=SC1091
        source /opt/rh/rh-python38/enable; \
        set -u; \
        ln -sf "$(command -v python3)" /usr/local/bin/python3; \
        ln -sf "$(command -v pip3)" /usr/local/bin/pip3 || true; \
      fi; \
    elif [ "${EL_RELEASE}" = "8" ]; then \
      alternatives --set python3 /usr/bin/python3.9 2>/dev/null \
        || ln -sf /usr/bin/python3.9 /usr/local/bin/python3; \
    fi; \
    if [ "${BUILD_RPM}" = "1" ]; then \
      SKIP_UI_BUILD=1 PANEL_ARCH=aarch64 EL_RELEASE="${EL_RELEASE}" \
        bash COMPILE/platforms/centos-arm/build.sh --el"${EL_RELEASE}" --local --rpm ; \
    else \
      SKIP_UI_BUILD=1 PANEL_ARCH=aarch64 EL_RELEASE="${EL_RELEASE}" \
        bash COMPILE/platforms/centos-arm/build.sh --el"${EL_RELEASE}" --local --no-rpm ; \
    fi

FROM scratch AS export
COPY --from=builder /out/ /out/
