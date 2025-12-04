# 多阶段构建Dockerfile - SpringCloud微服务项目
# 基础构建阶段
FROM maven:3.9.11-eclipse-temurin-21-alpine AS builder

# 配置 Maven 使用阿里云镜像源
RUN mkdir -p /root/.m2 && \
    cat > /root/.m2/settings.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">
  <mirrors>
    <mirror>
      <id>aliyun</id>
      <mirrorOf>central</mirrorOf>
      <name>Aliyun Maven</name>
      <url>https://maven.aliyun.com/nexus/content/groups/public/</url>
    </mirror>
  </mirrors>
  <localRepository>/root/.m2/repository</localRepository>
</settings>
EOF

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 跳过测试并打包所有模块
RUN mvn clean package -DskipTests -Dmaven.test.skip=true -Drevision=1.0.0 -T 2C

# 运行时基础镜像
FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds AS runtime-base
# 安全设置：创建非root用户（Rocky Linux 使用 groupadd/useradd）
RUN groupadd -r appgroup -g 1001 && useradd -r -u 1001 -g appgroup appuser

# 创建工作目录并设置权限
RUN mkdir -p /app/{logs,config,data,cache,temp,backup,message-queue} && chown -R appuser:appgroup /app
WORKDIR /app

# 通用环境变量
ENV TZ=Asia/Shanghai
ENV LANG=C.UTF-8
ENV JAVA_OPTS="-Xms512m -Xmx512m -Djava.security.egd=file:/dev/./urandom"
ENV SPRING_PROFILES_ACTIVE="prod"

# ============ iot-gateway 服务镜像 ============
FROM runtime-base AS iot-gateway
COPY --from=builder /app/iot-gateway/target/iot-gateway.jar app.jar
# 服务端口
ENV SERVER_PORT=48080
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48080
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-infra 服务镜像 ============
FROM runtime-base AS iot-infra
COPY --from=builder /app/iot-infra/iot-infra-biz/target/iot-infra-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48082
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48082
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-device 服务镜像 ============
FROM runtime-base AS iot-device
COPY --from=builder /app/iot-device/iot-device-biz/target/iot-device-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48083
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48083
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-dataset 服务镜像 ============
FROM runtime-base AS iot-dataset
COPY --from=builder /app/iot-dataset/iot-dataset-biz/target/iot-dataset-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48087
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48087
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-file 服务镜像 ============
FROM runtime-base AS iot-file
COPY --from=builder /app/iot-file/iot-file-biz/target/iot-file-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48090
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48090
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-tdengine 服务镜像 ============
FROM runtime-base AS iot-tdengine
COPY --from=builder /app/iot-tdengine/iot-tdengine-biz/target/iot-tdengine-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48091
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48091
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-sink 服务镜像 ============
FROM runtime-base AS iot-sink
COPY --from=builder /app/iot-sink/iot-sink-biz/target/iot-sink-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48092
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48092
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-message 服务镜像 ============
FROM runtime-base AS iot-message
COPY --from=builder /app/iot-message/iot-message-biz/target/iot-message-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48093
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48093
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-system 服务镜像 ============
FROM runtime-base AS iot-system
COPY --from=builder /app/iot-system/iot-system-biz/target/iot-system-biz.jar app.jar
# 服务端口
ENV SERVER_PORT=48099
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1
# 切换到非root用户
USER appuser
# 暴露端口
EXPOSE 48099
# 启动应用（使用exec形式）
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

