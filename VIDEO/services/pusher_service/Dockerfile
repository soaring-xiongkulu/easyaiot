# 使用Python官方镜像
FROM python:3.10-slim

# 设置非交互式环境
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 配置 Debian 镜像源（使用华为云镜像加速）
RUN sed -i 's/deb.debian.org/mirrors.huaweicloud.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.huaweicloud.com|g' /etc/apt/sources.list 2>/dev/null || \
    (echo "deb https://mirrors.huaweicloud.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
     echo "deb https://mirrors.huaweicloud.com/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
     echo "deb https://mirrors.huaweicloud.com/debian-security/ bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list) || true

# 安装基本工具和FFmpeg（用于视频流推送）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc git zip unzip wget curl vim htop \
    libavcodec-dev libavformat-dev libswscale-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装pip并配置使用阿里源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set install.trusted-host mirrors.aliyun.com \
    && pip install --upgrade pip --timeout 30 --retries 3 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制requirements文件
COPY requirements.txt requirements.txt

# 安装Python依赖
RUN pip install -r requirements.txt --timeout 30 --retries 3 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs

# 设置权限
RUN chmod +x run_deploy.py

# 暴露端口
EXPOSE 8003

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# 启动命令
CMD ["python", "run_deploy.py"]

