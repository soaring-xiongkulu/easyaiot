# BuildKit 内置前端，支持 RUN --mount
# 构建阶段：pnpm store 使用 BuildKit cache mount（id=visualize-pnpm-store），
# 由 install_linux.sh 通过 --cache-from/--cache-to type=local 持久化到 .build-cache/visualize/pnpm-store
#
# 多架构支持：由 .scripts/docker/runtime_image.sh 的 docker wrapper 注入 --platform 实现
FROM node:22-alpine3.21 AS builder

ARG NPM_REGISTRY=https://registry.npmmirror.com/

ENV CI=true
ENV HUSKY=0

RUN npm config set registry ${NPM_REGISTRY}

RUN npm install -g pnpm@11.3.0 && \
    pnpm config set registry ${NPM_REGISTRY} && \
    pnpm config set fetch-timeout 600000 && \
    pnpm config set fetch-retries 5 && \
    pnpm config set fetch-retry-mintimeout 20000 && \
    pnpm config set fetch-retry-maxtimeout 120000

WORKDIR /app
RUN mkdir -p /tmp/visualize-build-logs /pnpm

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN --mount=type=cache,target=/pnpm/store,id=visualize-pnpm-store \
    pnpm config set store-dir /pnpm/store && \
    pnpm fetch --frozen-lockfile 2>&1 | tee /tmp/visualize-build-logs/pnpm-fetch.log || true

# pnpm 11.x 偶发打印 "Done in Xs" 后永不退出（https://github.com/pnpm/pnpm/issues/12297），监督并强制收尾
RUN --mount=type=cache,target=/pnpm/store,id=visualize-pnpm-store \
    pnpm config set store-dir /pnpm/store && \
    sh -ec '\
      log=/tmp/visualize-build-logs/pnpm-install.log; \
      rcfile=/tmp/pnpm-install.rc; \
      : > "$log"; rm -f "$rcfile"; \
      setsid sh -c "set -o pipefail; pnpm install --frozen-lockfile 2>&1 | tee \"$log\"; echo \$? > \"$rcfile\"" & \
      pid=$!; \
      hung=0; \
      for i in $(seq 1 1800); do \
        if [ -f "$rcfile" ]; then wait "$pid" || true; break; fi; \
        if grep -q "Done in " "$log" 2>/dev/null; then \
          for j in $(seq 1 20); do \
            [ -f "$rcfile" ] && break; \
            sleep 1; \
          done; \
          if [ ! -f "$rcfile" ]; then \
            echo "=== pnpm 打印 Done 后 20s 未退出，强制结束（pnpm#12297）==="; \
            kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true; \
            sleep 5; \
            kill -KILL -"$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true; \
            wait "$pid" 2>/dev/null || true; \
            hung=1; \
          else \
            wait "$pid" || true; \
          fi; \
          break; \
        fi; \
        if [ $((i % 60)) -eq 0 ]; then echo "=== pnpm install 仍在运行 (${i}s) ==="; fi; \
        sleep 1; \
      done; \
      if [ ! -f "$rcfile" ] && [ "$hung" -eq 0 ]; then \
        echo "=== pnpm install 超过 1800s 未完成，终止 ==="; \
        kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true; \
        sleep 5; \
        kill -KILL -"$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true; \
        wait "$pid" 2>/dev/null || true; \
      fi; \
      if [ -f "$rcfile" ]; then \
        rc=$(cat "$rcfile"); \
        if [ "$rc" != "0" ]; then echo "=== pnpm install 失败 rc=$rc ==="; cat "$log"; exit "$rc"; fi; \
      elif [ "$hung" -eq 1 ]; then \
        test -d node_modules/vite || { echo "=== 强制结束后依赖不完整 ==="; cat "$log"; exit 1; }; \
        echo "=== 依赖完整，忽略 pnpm 挂起继续 ==="; \
      else \
        echo "=== pnpm install 状态未知 ==="; cat "$log"; exit 1; \
      fi; \
      echo "=== pnpm install 完成，校验 vite ==="; \
      test -d node_modules/vite || { echo "=== pnpm install 未生成 node_modules/vite ==="; exit 1; }; \
    '

ARG CACHE_BUST=0
RUN echo "cache-bust=${CACHE_BUST}" > /tmp/.visualize-cache-bust

COPY . .

ARG SKIP_VITE_BUILD=0

RUN --mount=type=cache,target=/pnpm/store,id=visualize-pnpm-store \
    pnpm config set store-dir /pnpm/store && \
    set -e && \
    if [ "${SKIP_VITE_BUILD}" = "1" ]; then \
        echo "=== SKIP_VITE_BUILD=1：使用预构建 dist-prebuilt（规避 QEMU 模拟 vite build）==="; \
        test -d dist-prebuilt || (echo "=== SKIP_VITE_BUILD=1 但 dist-prebuilt/ 不存在！ ===" && exit 1); \
        rm -rf dist && mv dist-prebuilt dist; \
    else \
        echo "=== vite build 开始（约 1–5 分钟）===" && \
        # 与 WEB 一致：直接调 vite，避免 pnpm run 触发隐式 install 再拉各平台 esbuild 可选依赖（易超时）
        NODE_ENV=production npx vite build 2>&1 | tee /tmp/visualize-build-logs/pnpm-build.log || \
        (echo "=== vite build failed, log: ===" && cat /tmp/visualize-build-logs/pnpm-build.log && exit 1); \
    fi

RUN test -d dist || (echo "=== dist missing after build ===" && cat /tmp/visualize-build-logs/pnpm-build.log && exit 1)

FROM nginx:1.31.4-alpine

ARG APK_MIRROR=mirrors.tuna.tsinghua.edu.cn

RUN if [ -n "${APK_MIRROR}" ]; then \
        sed -i "s/dl-cdn.alpinelinux.org/${APK_MIRROR}/g" /etc/apk/repositories; \
    fi

LABEL org.opencontainers.image.authors="basiclab"

WORKDIR /usr/share/nginx/html

RUN mkdir -p /usr/share/nginx/html /app/logs /opt/visualize-build-logs

COPY ./conf/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html
COPY --from=builder /tmp/visualize-build-logs /opt/visualize-build-logs

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["sh", "-c", "mkdir -p /app/logs && cp -af /opt/visualize-build-logs/. /app/logs/ && echo \"[$(date '+%Y-%m-%d %H:%M:%S')] visualize-service container started\" >> /app/logs/runtime.log && nginx -g 'daemon off;'"]
