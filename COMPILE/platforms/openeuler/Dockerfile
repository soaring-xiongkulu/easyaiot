# EasyAIoT COMPILE - openEuler 24.x（国内 dnf 源；前端由宿主机构建）
ARG BASE_IMAGE=openeuler/openeuler:24.03

FROM ${BASE_IMAGE} AS builder

ARG BUILD_RPM=1
ARG PANEL_VERSION=
ARG COMPILE_CN_MIRROR=huawei
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COMPILE_OUT=/out \
    PANEL_VERSION=${PANEL_VERSION} \
    COMPILE_CN_MIRROR=${COMPILE_CN_MIRROR} \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /src

COPY COMPILE/platforms/openeuler/setup_cn_mirrors.sh /tmp/setup_cn_mirrors.sh

# 不用 dnf update（官方 everything 极慢）；装完构建依赖即可
RUN set -eux; \
    bash /tmp/setup_cn_mirrors.sh; \
    dnf -y install \
      python3 \
      python3-pip \
      python3-devel \
      gcc \
      gcc-c++ \
      make \
      rpm-build \
      findutils \
      which \
      tar \
      gzip \
      binutils \
    && dnf clean all

COPY . /src
RUN test -f /src/PANEL/ui/dist/index.html

RUN if [ "${BUILD_RPM}" = "1" ]; then \
      SKIP_UI_BUILD=1 bash COMPILE/platforms/openeuler/build.sh --local --rpm ; \
    else \
      SKIP_UI_BUILD=1 bash COMPILE/platforms/openeuler/build.sh --local --no-rpm ; \
    fi

FROM scratch AS export
COPY --from=builder /out/ /out/
