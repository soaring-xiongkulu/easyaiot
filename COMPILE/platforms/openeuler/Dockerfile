# EasyAIoT COMPILE - openEuler 24.x standard container build
# Output: easyaiot-panel binary and optional rpm package

ARG BASE_IMAGE=openeuler/openeuler:24.03

FROM node:20-bookworm-slim AS ui-builder
WORKDIR /ui
COPY PANEL/ui/package.json ./
RUN npm install --no-audit --no-fund
COPY PANEL/ui/ ./
RUN npm run build && test -f /ui/dist/index.html

FROM ${BASE_IMAGE} AS builder

ARG BUILD_RPM=1
ARG PANEL_VERSION=
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COMPILE_OUT=/out \
    PANEL_VERSION=${PANEL_VERSION}

WORKDIR /src

# openEuler 使用 dnf；部分镜像需先刷新缓存
RUN dnf -y update && dnf -y install \
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
COPY --from=ui-builder /ui/dist /src/PANEL/ui/dist

# 使用本地模式，确保容器内不再嵌套 docker
RUN if [ "${BUILD_RPM}" = "1" ]; then \
      SKIP_UI_BUILD=1 bash COMPILE/platforms/openeuler/build.sh --local --rpm ; \
    else \
      SKIP_UI_BUILD=1 bash COMPILE/platforms/openeuler/build.sh --local --no-rpm ; \
    fi

FROM scratch AS export
COPY --from=builder /out/ /out/
