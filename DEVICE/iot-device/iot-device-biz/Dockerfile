# ======================= 构建阶段 =======================
FROM maven:3.9.11-eclipse-temurin-21-alpine AS build

# 使用HERE文档简化Maven配置
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
  <interactiveMode>false</interactiveMode>
  <offline>false</offline>
</settings>
EOF

# 设置工作目录
WORKDIR /app

# 阶段1：复制配置文件并下载依赖（最大化利用缓存）
COPY pom.xml .
COPY lombok.config .

# 复制各模块的pom.xml以提前构建依赖层
COPY iot-parent/pom.xml ./iot-parent/
COPY iot-common/pom.xml ./iot-common/
COPY iot-system/pom.xml ./iot-system/
COPY iot-infra/pom.xml ./iot-infra/
COPY iot-file/pom.xml ./iot-file/
COPY iot-tdengine/pom.xml ./iot-tdengine/
COPY iot-sink/pom.xml ./iot-sink/
COPY iot-device/pom.xml ./iot-device/

# 过滤不需要的模块，优化构建目标
RUN awk '
/<modules>/,/<\/modules>/ {
    if (/<module>iot-(gateway|dataset|message)<\/module>/) next
    print
}' pom.xml > pom.xml.filtered && \
mv pom.xml.filtered pom.xml

# 并行下载依赖，提高效率
RUN mvn dependency:go-offline -T 1C -B

# 阶段2：复制所有源代码
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-infra ./iot-infra
COPY iot-file ./iot-file
COPY iot-tdengine ./iot-tdengine
COPY iot-sink ./iot-sink
COPY iot-device ./iot-device

# 编译目标模块
RUN mvn clean package -DskipTests -Dmaven.test.skip=true -T 1C -pl iot-device/iot-device-biz -am

# ======================= 运行时阶段 =======================
FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds

# 设置非root用户以增强安全性
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建工作目录并设置权限
RUN mkdir -p /app && chown -R appuser:appuser /app
WORKDIR /app

# 复制构建产物并保留正确权限
COPY --from=build --chown=appuser:appuser /app/iot-device/iot-device-biz/target/iot-device-biz.jar app.jar

# 环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48083 \
    JAVA_OPTS="-Xms512m -Xmx512m -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai"

# 暴露应用端口
EXPOSE 48083

# 动态健康检查（针对Spring Boot应用）
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health > /dev/null 2>&1 || exit 1

# 切换到非root用户
USER appuser

# 启动应用（使用exec形式确保正确信号处理）
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
