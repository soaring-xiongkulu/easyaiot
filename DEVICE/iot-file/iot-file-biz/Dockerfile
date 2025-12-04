# ======================= 运行时阶段 =======================
# 此 Dockerfile 从宿主机挂载的 Jar 包构建运行时镜像
# Jar 包应该已经通过 base-builder 服务编译并挂载到 ./target/jars/ 目录

FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全设置：使用非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建统一的应用目录结构
RUN mkdir -p /app/{data,logs,temp} && chown -R appuser:appuser /app
WORKDIR /app

# 从宿主机挂载的 Jar 包目录复制构建产物
COPY target/jars/iot-file-biz.jar app.jar

# 如果 Jar 包不存在，给出提示
RUN if [ ! -f app.jar ]; then \
        echo "错误: iot-file-biz.jar 不存在！请先运行 base-builder 服务编译 Jar 包。" && \
        exit 1; \
    fi && \
    chown appuser:appuser app.jar

# 环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    JAVA_OPTS="-Xms512m -Xmx512m -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai" \
    SERVER_PORT=48090 \
    FILE_STORAGE_PATH="/app/data"

# 创建必要的文件存储目录并设置权限
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# 暴露应用端口
EXPOSE 48090

# 健康检查（针对文件服务可能需要自定义健康端点）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health > /dev/null 2>&1 || wget --spider http://localhost:${SERVER_PORT}/actuator/health 2>/dev/null || exit 1

# 切换到非 root 用户
USER appuser

# 使用 exec 形式确保正确的信号处理
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
