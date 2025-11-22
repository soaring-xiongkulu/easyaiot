# 使用PyTorch官方镜像（包含CUDA支持，Python 3.10）
# 注意：本镜像仅支持 x86_64 架构，ARM架构不支持容器化部署
# 升级到PyTorch 2.1.0以支持OpenVINO 2025.3.0（需要torch.float8_e4m3fn）
ARG BASE_IMAGE=pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
FROM ${BASE_IMAGE}

# 设置非交互式环境，避免构建时卡住
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0
ENV TZ=Asia/Shanghai

# 设置时区，避免时区配置交互式提示
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 安装基本工具（根据不同的宿主机架构修改）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc git zip unzip wget curl vim htop libgl1 libglib2.0-0 libpython3-dev gnupg g++ libusb-1.0-0 libsm6 \
    libgomp1 libgtk-3-0 libavcodec-dev libavformat-dev libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 X11 依赖（可视化，如果需要）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    x11-apps \
    libgl1-mesa-glx \
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

# 安装Python依赖（PyTorch已预装，无需重复安装）
RUN pip install -r requirements.txt --timeout 30 --retries 3 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 卸载 rknn-toolkit2（如果存在），避免与 torch 2.8.0 的依赖冲突
RUN pip uninstall -y rknn-toolkit2 rknn-toolkit 2>/dev/null || true

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

# 暴露端口（默认5000，可通过环境变量FLASK_RUN_PORT修改）
EXPOSE 5000

# 健康检查
# 注意：start-period设置为90秒，因为应用启动时会等待Nacos服务（最多30秒）
# 加上应用初始化时间，总共可能需要60-90秒
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:5000/actuator/health || exit 1

# 启动命令
CMD ["python", "run.py"]
