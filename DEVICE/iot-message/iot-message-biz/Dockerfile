# ======================= 构建阶段 =======================
FROM maven:3.9.11-eclipse-temurin-21-alpine AS build

# 使用高效的HERE文档配置Maven镜像源
RUN mkdir -p /root/.m2 && cat > /root/.m2/settings.xml <<'EOF'
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
  <interactiveMode>false</interactiveMode>
</settings>
EOF

# 设置工作目录
WORKDIR /app

# 阶段1: 复制构建配置文件构建依赖缓存层
COPY pom.xml .
COPY lombok.config .

# 复制各模块pom.xml构建分层缓存
COPY iot-parent/pom.xml ./iot-parent/
COPY iot-common/pom.xml ./iot-common/
COPY iot-system/pom.xml ./iot-system/
COPY iot-infra/pom.xml ./iot-infra/
COPY iot-message/pom.xml ./iot-message/

# 动态过滤不需要的模块引用
RUN awk '
/<modules>/,/<\/modules>/ {
    if (/<module>iot-(gateway|file|dataset|device|tdengine|sink)<\/module>/) next
    print
}' pom.xml > pom.xml.filtered && \
mv pom.xml.filtered pom.xml

# 并行预下载依赖（消息服务通常依赖较多中间件）
RUN mvn dependency:resolve-plugins dependency:go-offline -T 2C -B

# 阶段2: 复制源代码
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-infra ./iot-infra
COPY iot-message ./iot-message

# 编译消息服务模块（消息处理需要详细日志便于调试）
RUN mvn clean package -DskipTests -Dmaven.test.skip=true -T 2C -pl iot-message/iot-message-biz -am

# ======================= 运行时阶段 =======================
FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全设置：创建专用运行用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建标准化应用目录
RUN mkdir -p /app && chown -R appuser:appuser /app
WORKDIR /app

# 复制构建产物
COPY --from=build --chown=appuser:appuser /app/iot-message/iot-message-biz/target/iot-message-biz.jar app.jar

# 消息服务特有环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48093 \
    # 消息服务通常需要处理大量消息，优化内存和GC
    JAVA_OPTS="-Xms512m -Xmx1024m -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai"

# 创建消息服务专用目录
RUN mkdir -p /app/{logs,config,message-queue} && chown -R appuser:appuser /app

# 暴露消息服务端口
EXPOSE 48093

# 针对消息服务的健康检查（需要考虑消息处理延迟）
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health > /dev/null 2>&1 || \
    wget --spider http://localhost:${SERVER_PORT}/actuator/health 2>/dev/null || exit 1

# 切换到非root用户
USER appuser

# 确保消息服务的优雅关闭和信号处理
ENTRYPOINT ["sh", "-c", "exec java ${JAVA_OPTS} -jar app.jar"]
