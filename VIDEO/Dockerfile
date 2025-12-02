# 使用Python官方镜像（Python 3.10）
FROM python:3.10-slim

# 设置非交互式环境，避免构建时卡住
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 设置时区，避免时区配置交互式提示
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 配置 Debian 镜像源（使用华为云镜像加速）
RUN sed -i 's/deb.debian.org/mirrors.huaweicloud.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.huaweicloud.com|g' /etc/apt/sources.list 2>/dev/null || \
    (echo "deb https://mirrors.huaweicloud.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
     echo "deb https://mirrors.huaweicloud.com/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
     echo "deb https://mirrors.huaweicloud.com/debian-security/ bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list) || true

# 安装基本工具（根据不同的宿主机架构修改）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc git zip unzip wget curl vim htop libgl1 libglib2.0-0 libpython3-dev gnupg g++ libusb-1.0-0 libsm6 \
    libgomp1 libgthread-2.0-0 libgtk-3-0 libavcodec-dev libavformat-dev libswscale-dev \
    libmagic1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装 X11 依赖（可视化，如果需要）
# 注意：镜像源已在上面配置，这里直接使用
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    x11-apps \
    libxcb-xinerama0 \
    && rm -rf /var/lib/apt/lists/*

# 设置环境变量（可视化）
ENV QT_QPA_PLATFORM=xcb
ENV QT_X11_NO_MITSHM=1

# 安装 pip 并更新到最新版本，同时配置使用阿里源
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
RUN mkdir -p data/uploads data/datasets data/models data/inference_results temp_uploads static/models

# 设置权限
RUN chmod +x run.py

# 创建非root用户（-m 参数自动创建主目录）
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

# 创建必要的用户目录并设置权限
RUN mkdir -p /home/appuser/.paddlex/temp /home/appuser/.config/Ultralytics && \
    chown -R appuser:appuser /home/appuser

# 设置目录权限
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口（默认6000，可通过环境变量FLASK_RUN_PORT修改）
EXPOSE 6000

# 健康检查
# 注意：start-period设置为90秒，因为应用启动时会等待Nacos服务（最多30秒）
# 加上应用初始化时间，总共可能需要60-90秒
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:6000/actuator/health || exit 1

# 启动命令
CMD ["python", "run.py"]

