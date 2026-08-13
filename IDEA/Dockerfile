# EasyAIoT IDEA Portal — 编排 code-server 贡献者工作区
ARG PYTHON_IMAGE=python:3.11-slim-bookworm

FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    IDEA_LISTEN_HOST=0.0.0.0 \
    IDEA_LISTEN_PORT=9300 \
    IDEA_DATA_DIR=/var/lib/easyaiot-idea/workspaces

WORKDIR /opt/idea

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY workspace_ops.py idle_reaper.py oauth_auth.py idea_server.py run_idea.py publish_ops.py ./
COPY webui/ ./webui/

EXPOSE 9300

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9300/health')" || exit 1

CMD ["python", "run_idea.py"]
