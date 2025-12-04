# ======================= 运行时阶段 =======================
# 此 Dockerfile 从宿主机挂载的 Jar 包构建运行时镜像
# Jar 包应该已经通过 base-builder 服务编译并挂载到 ./target/jars/ 目录

FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全设置：创建专用运行用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建应用目录并设置权限
RUN mkdir -p /app && chown -R appuser:appuser /app
WORKDIR /app

# 从宿主机挂载的 Jar 包目录复制构建产物
COPY target/jars/iot-infra-biz.jar app.jar

# 如果 Jar 包不存在，给出提示
RUN if [ ! -f app.jar ]; then \
        echo "错误: iot-infra-biz.jar 不存在！请先运行 base-builder 服务编译 Jar 包。" && \
        exit 1; \
    fi && \
    chown appuser:appuser app.jar

# 基础设施服务环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48082 \
    # 基础设施服务可能需要更多内存支持缓存和连接池
    JAVA_OPTS="-Xms512m -Xmx1024m -XX:MaxRAMPercentage=75.0 -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai -Dspring.profiles.active=prod" \
    # 基础设施服务特定的配置
    INFRA_CACHE_SIZE="1000" \
    DB_CONNECTION_POOL_SIZE="20"

# 创建必要的运行时目录
RUN mkdir -p /app/{logs,config,cache} && chown -R appuser:appuser /app

# 暴露服务端口
EXPOSE 48082

# 基础设施服务健康检查（考虑其核心服务特性）
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health > /dev/null 2>&1 || \
    wget --spider http://localhost:${SERVER_PORT}/actuator/health 2>/dev/null || exit 1

# 切换到非root用户
USER appuser

# 确保正确的信号处理
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
