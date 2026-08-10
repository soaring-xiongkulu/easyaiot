# 使用Python官方镜像
FROM python:3.10-slim

# 设置非交互式环境
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# 镜像源配置（通过 --build-arg 传入，默认腾讯云）
ARG APT_MIRROR_URL=https://mirrors.tuna.tsinghua.edu.cn
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 配置镜像源（支持Ubuntu和Debian）
RUN if [ -n "${APT_MIRROR_URL}" ]; then \
        OS_ID=$(cat /etc/os-release 2>/dev/null | grep "^ID=" | cut -d'=' -f2 | tr -d '"' || echo "ubuntu") && \
        OS_VERSION=$(cat /etc/os-release 2>/dev/null | grep "^VERSION_CODENAME=" | cut -d'=' -f2 | tr -d '"' || cat /etc/os-release 2>/dev/null | grep "^VERSION_ID=" | cut -d'=' -f2 | tr -d '"' | cut -d'.' -f1 || echo "jammy") && \
        if [ "$OS_ID" = "ubuntu" ]; then \
            sed -i "s|http://.*archive.ubuntu.com|${APT_MIRROR_URL}|g" /etc/apt/sources.list 2>/dev/null || true; \
            sed -i "s|http://.*security.ubuntu.com|${APT_MIRROR_URL}|g" /etc/apt/sources.list 2>/dev/null || true; \
            if [ ! -f /etc/apt/sources.list ] || ! grep -q "${APT_MIRROR_URL}" /etc/apt/sources.list 2>/dev/null; then \
                echo "deb ${APT_MIRROR_URL}/ubuntu/ ${OS_VERSION} main restricted universe multiverse" > /etc/apt/sources.list && \
                echo "deb ${APT_MIRROR_URL}/ubuntu/ ${OS_VERSION}-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
                echo "deb ${APT_MIRROR_URL}/ubuntu/ ${OS_VERSION}-security main restricted universe multiverse" >> /etc/apt/sources.list && \
                echo "deb ${APT_MIRROR_URL}/ubuntu/ ${OS_VERSION}-backports main restricted universe multiverse" >> /etc/apt/sources.list; \
            fi; \
        elif [ "$OS_ID" = "debian" ]; then \
            sed -i "s|deb.debian.org|${APT_MIRROR_URL##https://}|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null || true; \
            sed -i "s|deb.debian.org|${APT_MIRROR_URL##https://}|g" /etc/apt/sources.list 2>/dev/null || true; \
            if [ ! -f /etc/apt/sources.list ] || ! grep -q "${APT_MIRROR_URL}" /etc/apt/sources.list 2>/dev/null; then \
                echo "deb ${APT_MIRROR_URL}/debian/ ${OS_VERSION} main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
                echo "deb ${APT_MIRROR_URL}/debian/ ${OS_VERSION}-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
                echo "deb ${APT_MIRROR_URL}/debian-security/ ${OS_VERSION}-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
            fi; \
        fi; \
    fi || true

# 安装基本工具和FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc git zip unzip wget curl vim htop \
    libgl1 libglib2.0-0 libpython3-dev \
    libavcodec-dev libavformat-dev libswscale-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装pip并更新到最新版本
RUN pip config set global.index-url ${PIP_INDEX_URL} \
    && pip install --upgrade pip --timeout 30 --retries 3 -i ${PIP_INDEX_URL}

# 复制requirements文件
COPY requirements.txt requirements.txt

# 安装Python依赖
RUN pip install -r requirements.txt --timeout 30 --retries 3 -i ${PIP_INDEX_URL}

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs

# 设置权限
RUN chmod +x run_deploy.py

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 启动命令
CMD ["python", "run_deploy.py"]

