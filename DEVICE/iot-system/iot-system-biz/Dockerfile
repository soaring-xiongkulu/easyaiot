# ======================= 运行时阶段 =======================
# 此 Dockerfile 从宿主机挂载的 Jar 包构建运行时镜像
# Jar 包应该已经通过 base-builder 服务编译并挂载到 ./target/jars/ 目录

FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全设置：创建专用用户和组
RUN groupadd -r appuser -g 1001 && useradd -r -u 1001 -g appuser appuser

# 创建标准化的应用目录结构
RUN mkdir -p /app/{logs,config,data,temp} && chown -R appuser:appuser /app
WORKDIR /app

# 从宿主机挂载的 Jar 包目录复制构建产物
COPY target/jars/iot-system-biz.jar app.jar

# 如果 Jar 包不存在，给出提示
RUN if [ ! -f app.jar ]; then \
        echo "错误: iot-system-biz.jar 不存在！请先运行 base-builder 服务编译 Jar 包。" && \
        exit 1; \
    fi && \
    chown appuser:appuser app.jar

# 系统服务专用环境变量配置
# 系统服务需要稳定的内存配置，适合处理核心业务逻辑
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48099 \
    JAVA_OPTS="-Xms512m -Xmx1024m -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC -XX:MaxGCPauseMillis=150 -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai -Dfile.encoding=UTF-8"

# 创建运行时必要的目录结构
RUN mkdir -p /app/{logs,config,data,temp,backup} && chown -R appuser:appuser /app

# 暴露系统服务端口
EXPOSE 48099

# 系统服务健康检查（核心服务需要更严格监控）
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health > /dev/null 2>&1 || \
    wget --quiet --spider http://localhost:${SERVER_PORT}/actuator/health 2>/dev/null || exit 1

# 标签：元数据便于管理和监控
LABEL maintainer="devops@example.com" \
      version="1.0.0" \
      description="IoT System Business Service" \
      io.k8s.description="Core system service for IoT platform"

# 切换到非root用户运行
USER appuser

# 使用exec形式确保正确的信号传递
ENTRYPOINT ["sh", "-c", "exec java ${JAVA_OPTS} -jar app.jar"]
