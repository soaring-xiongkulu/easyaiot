# 使用Nginx官方镜像
FROM nginx:alpine

# 作者信息
MAINTAINER basiclab

# 设置工作目录
WORKDIR /usr/share/nginx/html

# 创建必要的目录
RUN mkdir -p /usr/share/nginx/html

# 复制nginx配置文件
COPY ./conf/nginx.conf /etc/nginx/nginx.conf

# 复制前端构建产物
COPY ./dist /usr/share/nginx/html

# 复制启动脚本
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 安装必要的工具（用于解析服务 IP）
RUN apk add --no-cache getent bind-tools iputils

# 暴露端口（默认80，可通过环境变量修改）
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# 使用启动脚本启动
ENTRYPOINT ["/entrypoint.sh"]

