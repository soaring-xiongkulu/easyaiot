# ======================= 运行时阶段 =======================
# 此 Dockerfile 从宿主机挂载的 Jar 包构建运行时镜像
# Jar 包应该已经通过 base-builder 服务编译并挂载到 ./target/jars/ 目录

FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds AS runtime

# 安全设置：创建非root用户（Rocky Linux 使用 groupadd/useradd）
RUN groupadd -r appgroup -g 1001 && useradd -r -u 1001 -g appgroup appuser

# 创建工作目录并设置权限
RUN mkdir -p /app && chown -R appuser:appgroup /app
WORKDIR /app

# 从宿主机挂载的 Jar 包目录复制构建产物
COPY target/jars/iot-tdengine-biz.jar app.jar

# 如果 Jar 包不存在，给出提示
RUN if [ ! -f app.jar ]; then \
        echo "错误: iot-tdengine-biz.jar 不存在！请先运行 base-builder 服务编译 Jar 包。" && \
        exit 1; \
    fi && \
    chown appuser:appgroup app.jar

# 环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48091 \
    JAVA_OPTS="-Xms512m -Xmx512m -Djava.security.egd=file:/dev/./urandom"

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 48091

# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
