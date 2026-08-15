FROM node:22-bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    curl git ca-certificates socat \
    python3 make g++ \
  && rm -rf /var/lib/apt/lists/* \
  && npm install -g pnpm@10

ARG DSH_VERSION=0.1.0-rc.6
ARG HARNESS_SIDEBAR_PACKAGE=dsh-better-sidebar@0.12.1
RUN npm install -g "@deepseek-ai/dsh@${DSH_VERSION}" tsx

WORKDIR /harness

COPY plugins/ /harness/plugins/
RUN mkdir -p /harness/plugins/node_modules/@deepseek-ai \
  && ln -sf /usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-tools \
    /harness/plugins/node_modules/@deepseek-ai/dsh-tools \
  && ln -sf /usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/cordis \
    /harness/plugins/node_modules/@deepseek-ai/cordis

COPY scripts/ /harness/scripts/
COPY image/ /harness/image/
COPY docker-entrypoint.sh /usr/local/bin/harness-entrypoint.sh
RUN chmod +x /usr/local/bin/harness-entrypoint.sh \
    /harness/image/apply-branding.sh \
    /harness/scripts/ensure-ux-plugins.sh \
    /harness/scripts/purge-harness-workspace.sh \
  && HARNESS_APP_NAME=EasyAIoT HARNESS_APP_SHORT=EasyAIoT /harness/image/apply-branding.sh

# 构建期预装侧边栏到 seed，首启可离线复制到 DSH_HOME volume
ENV DSH_HOME=/harness/dsh-seed
RUN mkdir -p /harness/dsh-seed \
  && HARNESS_ENABLE_SIDEBAR=1 \
     HARNESS_SIDEBAR_PACKAGE="${HARNESS_SIDEBAR_PACKAGE}" \
     HARNESS_UX_SEED=/harness/dsh-seed \
     /harness/scripts/ensure-ux-plugins.sh \
  || echo "[harness] WARN: sidebar seed install skipped (build continues)"

# 运行时工作目录必须是仓库根（资源管理器根 = 会话 cwd）
RUN mkdir -p /workspace/easyaiot
WORKDIR /workspace/easyaiot

ENV DSH_HOME=/data/dsh-home
ENV HARNESS_LISTEN_HOST=127.0.0.1
ENV HARNESS_LISTEN_PORT=3080
ENV HARNESS_WORKSPACE=/workspace/easyaiot
ENV HARNESS_ENABLE_SIDEBAR=1
ENV HARNESS_SIDEBAR_PACKAGE=${HARNESS_SIDEBAR_PACKAGE}
ENV HARNESS_UX_SEED=/harness/dsh-seed

EXPOSE 3080

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=120s \
  CMD curl -fsS "http://127.0.0.1:${HARNESS_LISTEN_PORT}/" >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/harness-entrypoint.sh"]
