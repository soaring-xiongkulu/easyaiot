# EasyAIoT PANEL — 多阶段构建：独立前端 + Python Agent
# bash PANEL/install.sh build && bash PANEL/install.sh start

ARG NODE_IMAGE=node:20-bookworm-slim
ARG PYTHON_IMAGE=python:3.11-slim-bookworm

# ---------- 前端 ----------
FROM ${NODE_IMAGE} AS ui-builder
WORKDIR /ui
COPY ui/package.json ./
RUN npm install --no-audit --no-fund
COPY ui/ ./
RUN npm run build

# ---------- 运行时 ----------
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PANEL_LISTEN_HOST=0.0.0.0 \
    PANEL_LISTEN_PORT=9200 \
    EASYAIOT_ROOT=/easyaiot \
    PANEL_STATIC_DIR=/opt/panel/ui/dist

WORKDIR /opt/panel

# docker.io 提供 CLI；经挂载的 docker.sock 操控宿主机
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates docker.io docker-compose \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY docker_ops.py stack_ops.py topology.py panel_server.py run_panel.py ./
COPY --from=ui-builder /ui/dist ./ui/dist

EXPOSE 9200

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9200/health')" || exit 1

CMD ["python", "run_panel.py"]
