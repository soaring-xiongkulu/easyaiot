# ======================= 构建阶段 =======================
FROM maven:3.9.11-eclipse-temurin-21-alpine AS build

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

# 阶段1: 复制配置文件和模块POM构建依赖缓存
COPY pom.xml .
COPY lombok.config .

# 复制各模块pom.xml实现分层缓存
COPY iot-parent/pom.xml ./iot-parent/
COPY iot-common/pom.xml ./iot-common/
COPY iot-system/pom.xml ./iot-system/
COPY iot-infra/pom.xml ./iot-infra/

# 动态过滤不需要的模块引用
RUN awk '
/<modules>/,/<\/modules>/ {
    if (/<module>iot-(gateway|file|dataset|device|tdengine|sink|message)<\/module>/) next
    print
}' pom.xml > pom.xml.filtered && \
mv pom.xml.filtered pom.xml

# 并行预下载依赖（系统服务需要稳定可靠的依赖解析）
RUN mvn dependency:resolve-plugins dependency:go-offline -T 2C -B -q

# 阶段2: 复制源代码
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-infra ./iot-infra

# 编译系统核心模块（系统服务通常需要严格测试）
RUN mvn clean package -DskipTests -T 2C -pl iot-system/iot-system-biz -am

# ======================= 运行时阶段 =======================
FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全设置：创建专用用户和组
RUN groupadd -r appuser -g 1001 && useradd -r -u 1001 -g appuser appuser

# 创建标准化的应用目录结构
RUN mkdir -p /app/{logs,config,data,temp} && chown -R appuser:appuser /app
WORKDIR /app

# 复制构建产物并设置正确的权限
COPY --from=build --chown=appuser:appuser /app/iot-system/iot-system-biz/target/iot-system-biz.jar app.jar

# 系统服务专用环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48099 \
    # 系统服务需要稳定的内存配置，适合处理核心业务逻辑
    JAVA_OPTS="-Xms512m -Xmx1024m -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC -XX:MaxGCPauseMillis=150 -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai -Dfile.encoding=UTF-8" \


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
