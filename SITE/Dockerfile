# SITE 官方网站：node build → nginx 静态托管
# nginx 配置统一维护于 WEB/conf/nginx.site.conf
# 构建需附加上下文：--build-context webconf=../WEB/conf
# （SITE/install_linux.sh 已自动传入）
# 多架构由 .scripts/docker/runtime_image.sh 的 docker wrapper 注入 --platform
# syntax=docker/dockerfile:1.7

FROM node:22-alpine3.21 AS builder

ARG NPM_REGISTRY=https://registry.npmmirror.com/

ENV CI=true

RUN npm config set registry ${NPM_REGISTRY} && \
    npm install -g pnpm@9.15.0 && \
    pnpm config set registry ${NPM_REGISTRY} && \
    pnpm config set fetch-timeout 600000 && \
    pnpm config set fetch-retries 5

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./

RUN --mount=type=cache,target=/pnpm/store,id=site-pnpm-store \
    pnpm config set store-dir /pnpm/store && \
    if [ -f pnpm-lock.yaml ]; then \
      pnpm install --frozen-lockfile; \
    else \
      pnpm install; \
    fi

ARG CACHE_BUST=0
RUN echo "cache-bust=${CACHE_BUST}" > /tmp/.site-cache-bust

COPY . .

ARG SKIP_VITE_BUILD=0

RUN --mount=type=cache,target=/pnpm/store,id=site-pnpm-store \
    pnpm config set store-dir /pnpm/store && \
    set -e && \
    if [ "${SKIP_VITE_BUILD}" = "1" ]; then \
        echo "=== SKIP_VITE_BUILD=1：使用预构建 dist-prebuilt ==="; \
        test -d dist-prebuilt || (echo "=== dist-prebuilt/ 不存在 ===" && exit 1); \
        rm -rf dist && mv dist-prebuilt dist; \
    else \
        echo "=== vite build 开始 ===" && \
        NODE_ENV=production npx vite build; \
    fi

RUN test -d dist || (echo "=== dist missing after build ===" && exit 1)

FROM nginx:1.29.2-alpine

ARG APK_MIRROR=mirrors.tuna.tsinghua.edu.cn

RUN if [ -n "${APK_MIRROR}" ]; then \
        sed -i "s/dl-cdn.alpinelinux.org/${APK_MIRROR}/g" /etc/apk/repositories; \
    fi

LABEL org.opencontainers.image.authors="basiclab"
LABEL org.opencontainers.image.title="EasyAIoT SITE"

WORKDIR /usr/share/nginx/html

COPY --from=webconf nginx.site.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
