FROM node:22-bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    curl git ca-certificates socat \
    python3 make g++ \
  && rm -rf /var/lib/apt/lists/*

ARG DSH_VERSION=0.1.0-rc.6
RUN npm install -g "@deepseek-ai/dsh@${DSH_VERSION}" tsx

WORKDIR /harness

COPY plugins/ /harness/plugins/
RUN mkdir -p /harness/plugins/node_modules/@deepseek-ai \
  && ln -sf /usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-tools \
    /harness/plugins/node_modules/@deepseek-ai/dsh-tools \
  && ln -sf /usr/local/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/cordis \
    /harness/plugins/node_modules/@deepseek-ai/cordis

COPY docker-entrypoint.sh /usr/local/bin/harness-entrypoint.sh
RUN chmod +x /usr/local/bin/harness-entrypoint.sh

ENV DSH_HOME=/data/dsh-home
ENV HARNESS_LISTEN_HOST=127.0.0.1
ENV HARNESS_LISTEN_PORT=3080
ENV HARNESS_WORKSPACE=/workspace/easyaiot

EXPOSE 3080

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=90s \
  CMD curl -fsS "http://127.0.0.1:${HARNESS_LISTEN_PORT}/" >/dev/null || exit 1

ENTRYPOINT ["/usr/local/bin/harness-entrypoint.sh"]
