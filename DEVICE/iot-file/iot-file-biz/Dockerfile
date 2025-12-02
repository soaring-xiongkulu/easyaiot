# ======================= 构建阶段 =======================
FROM maven:3.9.11-eclipse-temurin-21-alpine AS build

# 使用更简洁的方式配置 Maven 镜像源
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

# 阶段1: 复制构建配置文件并下载依赖（最大化缓存利用）
COPY pom.xml .
COPY lombok.config .

# 复制各模块 pom.xml 以构建独立依赖层
COPY iot-parent/pom.xml ./iot-parent/
COPY iot-common/pom.xml ./iot-common/
COPY iot-system/pom.xml ./iot-system/
COPY iot-infra/pom.xml ./iot-infra/
COPY iot-file/pom.xml ./iot-file/

# 过滤不需要的模块以优化构建范围
RUN awk '
/<modules>/,/<\/modules>/ {
    if (/<module>iot-(gateway|dataset|device|tdengine|sink|message)<\/module>/) next
    print
    if (/<\/modules>/) exit
}' pom.xml > pom.xml.filtered && \
mv pom.xml.filtered pom.xml

# 应用依赖解析器，提前下载依赖（加速后续构建）
RUN mvn dependency:resolve-plugins dependency:go-offline -T 1C -B

# 阶段2: 复制所有源代码（仅在依赖之后）
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-infra ./iot-infra
COPY iot-file ./iot-file

# 编译目标模块（启用并行编译）
RUN mvn clean package -DskipTests -Dmaven.test.skip=true -T 1C -pl iot-file/iot-file-biz -am

# ======================= 运行时阶段 =======================
FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全设置：使用非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建统一的应用目录结构
RUN mkdir -p /app/{data,logs,temp} && chown -R appuser:appuser /app
WORKDIR /app

# 从构建阶段复制 jar 文件并设置所有权
COPY --from=build --chown=appuser:appuser /app/iot-file/iot-file-biz/target/iot-file-biz.jar app.jar

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
