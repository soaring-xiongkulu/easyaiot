# ======================= 运行时阶段 =======================
# 此 Dockerfile 从宿主机挂载的 Jar 包构建运行时镜像
# Jar 包应该已经通过 base-builder 服务编译并挂载到 ./target/jars/ 目录

FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全配置：创建专用用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建标准化目录结构
RUN mkdir -p /app/{logs,config,cache} && chown -R appuser:appuser /app
WORKDIR /app

# 从宿主机挂载的 Jar 包目录复制构建产物
# 注意：构建上下文是 DEVICE 根目录，所以路径是相对于根目录的
COPY target/jars/iot-gateway.jar app.jar

# 如果 Jar 包不存在，给出提示
RUN if [ ! -f app.jar ]; then \
        echo "错误: iot-gateway.jar 不存在！请先运行 base-builder 服务编译 Jar 包。" && \
        exit 1; \
    fi && \
    chown appuser:appuser app.jar

# 网关专用环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48080 \
    # 网关通常需要更多内存处理网络请求和路由
    JAVA_OPTS="-Xms512m -Xmx1024m -XX:MaxRAMPercentage=75.0 -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai -Dspring.profiles.active=prod"

# 暴露网关端口（通常需要外部访问）
EXPOSE 48080

# 网关专用健康检查（通常有独立的管理端口或路径）
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health > /dev/null 2>&1 || \
    (test -f /proc/1/cmdline && grep -q gateway /proc/1/cmdline) || exit 1

# 创建必要的运行时目录
RUN mkdir -p /app/{logs,config,cache} && chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 使用exec形式确保网关能正确处理优雅关闭
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
