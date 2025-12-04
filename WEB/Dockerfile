# 构建阶段
FROM node:22-alpine3.21 AS builder

# 配置npm国内镜像源（淘宝镜像 - npmmirror.com是淘宝镜像的新地址）
RUN npm config set registry https://registry.npmmirror.com/

# 安装pnpm
RUN npm install -g pnpm@9.0.4

# 配置pnpm国内镜像源（淘宝镜像）
RUN pnpm config set registry https://registry.npmmirror.com/ && \
    pnpm config set network-timeout 600000 && \
    pnpm config set fetch-retries 5 && \
    pnpm config set fetch-retry-mintimeout 20000 && \
    pnpm config set fetch-retry-maxtimeout 120000

# 设置工作目录
WORKDIR /app

# 复制package文件和锁定文件（如果存在，提高安装可靠性）
COPY package.json ./
COPY pnpm-lock.yaml* ./

# 安装依赖（如果存在锁定文件则使用，否则重新生成）
RUN if [ -f pnpm-lock.yaml ]; then \
        pnpm install --frozen-lockfile; \
    else \
        pnpm install; \
    fi

# 复制源代码
COPY . .

# 构建项目
RUN pnpm build

# 生产阶段
FROM nginx:1.29.2-alpine

# 配置国内镜像源（如果需要安装额外软件）
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 作者信息
MAINTAINER basiclab

# 设置工作目录
WORKDIR /usr/share/nginx/html

# 创建必要的目录
RUN mkdir -p /usr/share/nginx/html

# 复制nginx配置文件
COPY ./conf/nginx.conf /etc/nginx/nginx.conf

# 从构建阶段复制构建产物到nginx的html目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口（默认80，可通过环境变量修改）
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# 启动nginx（使用非daemon模式以便在容器中运行）
CMD ["nginx", "-g", "daemon off;"]

