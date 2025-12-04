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
WORKDIR /app

# 通用环境变量
ENV JAVA_OPTS="-Xmx512m -Xms256m"
ENV SPRING_PROFILES_ACTIVE="prod"

# ============ iot-gateway 服务镜像 ============
FROM runtime-base AS iot-gateway
COPY --from=builder /app/iot-gateway/target/iot-gateway.jar app.jar
EXPOSE 48080
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-infra 服务镜像 ============
FROM runtime-base AS iot-infra
COPY --from=builder /app/iot-infra/iot-infra-biz/target/iot-infra-biz.jar app.jar
EXPOSE 48082
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-device 服务镜像 ============
FROM runtime-base AS iot-device
COPY --from=builder /app/iot-device/iot-device-biz/target/iot-device-biz.jar app.jar
EXPOSE 48083
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-dataset 服务镜像 ============
FROM runtime-base AS iot-dataset
COPY --from=builder /app/iot-dataset/iot-dataset-biz/target/iot-dataset-biz.jar app.jar
EXPOSE 48087
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-file 服务镜像 ============
FROM runtime-base AS iot-file
COPY --from=builder /app/iot-file/iot-file-biz/target/iot-file-biz.jar app.jar
EXPOSE 48090
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-tdengine 服务镜像 ============
FROM runtime-base AS iot-tdengine
COPY --from=builder /app/iot-tdengine/iot-tdengine-biz/target/iot-tdengine-biz.jar app.jar
EXPOSE 48091
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-sink 服务镜像 ============
FROM runtime-base AS iot-sink
COPY --from=builder /app/iot-sink/iot-sink-biz/target/iot-sink-biz.jar app.jar
EXPOSE 48092
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-message 服务镜像 ============
FROM runtime-base AS iot-message
COPY --from=builder /app/iot-message/iot-message-biz/target/iot-message-biz.jar app.jar
EXPOSE 48093
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

# ============ iot-system 服务镜像 ============
FROM runtime-base AS iot-system
COPY --from=builder /app/iot-system/iot-system-biz/target/iot-system-biz.jar app.jar
EXPOSE 48099
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]

