# syntax=docker/dockerfile:labs

# ---------------------------------------------------------------------------
# Stage 1: 从 vendor/go2rtc 编译 go2rtc 二进制
# ---------------------------------------------------------------------------
ARG GO_VERSION=1.25
FROM --platform=$BUILDPLATFORM golang:${GO_VERSION}-alpine AS go2rtc-build
ARG TARGETOS
ARG TARGETARCH
ARG GOPROXY=https://goproxy.cn,direct

ENV GOOS=${TARGETOS} GOARCH=${TARGETARCH} CGO_ENABLED=0 GOPROXY=${GOPROXY}

WORKDIR /build
RUN apk add --no-cache git

COPY vendor/go2rtc/go.mod vendor/go2rtc/go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    --mount=type=cache,target=/root/.cache/go-build,sharing=locked \
    go mod download

COPY vendor/go2rtc/ ./
RUN --mount=type=cache,target=/go/pkg/mod,sharing=locked \
    --mount=type=cache,target=/root/.cache/go-build,sharing=locked \
    go build -ldflags "-s -w" -trimpath -o /go2rtc .

# ---------------------------------------------------------------------------
# Stage 2: Python 管理服务 + go2rtc 运行时
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm

LABEL maintainer="EasyAIoT"
LABEL description="EasyAIoT RTC — go2rtc secondary development module"

RUN apt-get update && apt-get install -y --no-install-recommends \
    tini ffmpeg curl gettext-base \
    && rm -rf /var/lib/apt/lists/*

COPY --from=go2rtc-build /go2rtc /usr/local/bin/go2rtc

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/
COPY run.py docker-entrypoint.sh env.example ./

RUN chmod +x docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=6100 \
    GO2RTC_API_URL=http://127.0.0.1:1984 \
    GO2RTC_CONFIG=/config/go2rtc.yaml \
    GO2RTC_CONFIG_TEMPLATE=/app/config/go2rtc.yaml.template \
    TZ=Asia/Shanghai

EXPOSE 6100 1984 8554 8555 8555/udp

VOLUME ["/config"]

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash", "/app/docker-entrypoint.sh"]
