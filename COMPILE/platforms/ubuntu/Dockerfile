# EasyAIoT COMPILE — Ubuntu (glibc / bookworm) 单文件 PANEL
# 产出: /out/easyaiot-panel
#
# 由 build.sh 准备精简上下文：已包含宿主机构建好的 PANEL/ui/dist。
# 容器内只做 pip + PyInstaller，不再跑 npm（避免 registry 慢导致卡死）。

ARG PYTHON_IMAGE=python:3.11-slim-bookworm

FROM ${PYTHON_IMAGE} AS packager

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PANEL_SRC=/src/PANEL \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        build-essential \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY COMPILE/requirements-build.txt /src/COMPILE/requirements-build.txt
RUN pip install --no-cache-dir -r /src/COMPILE/requirements-build.txt

COPY PANEL/docker_ops.py PANEL/stack_ops.py PANEL/topology.py \
     PANEL/panel_server.py PANEL/run_panel.py \
     /src/PANEL/
COPY PANEL/ui/dist /src/PANEL/ui/dist
COPY COMPILE/platforms/ubuntu/panel.spec /src/COMPILE/platforms/ubuntu/panel.spec

RUN test -f /src/PANEL/ui/dist/index.html

WORKDIR /build
RUN pyinstaller \
      --clean \
      --noconfirm \
      --distpath /out \
      --workpath /build/work \
      /src/COMPILE/platforms/ubuntu/panel.spec \
    && test -x /out/easyaiot-panel \
    && ls -lh /out/easyaiot-panel

FROM scratch AS export
COPY --from=packager /out/easyaiot-panel /easyaiot-panel
