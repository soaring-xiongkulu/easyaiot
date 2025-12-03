# ======================= 构建阶段 =======================
FROM maven:3.9.11-eclipse-temurin-21-alpine AS build

# 配置Maven阿里云镜像（简化配置）
RUN mkdir -p /root/.m2 && \
    cat > /root/.m2/settings.xml << 'EOF'
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

# 复制pom文件（利用Docker缓存层）
COPY pom.xml .
COPY lombok.config .

# 下载依赖（提前执行，利用缓存）
RUN mvn dependency:go-offline -B

# 复制源代码
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-infra ./iot-infra
COPY iot-device ./iot-device
COPY iot-tdengine ./iot-tdengine

# 过滤不需要的模块（优化pom.xml）
RUN awk '/<modules>/,/<\/modules>/ { if (/<module>iot-(gateway|file|dataset|sink|message)<\/module>/) next; print }' pom.xml > pom.xml.filtered && \
mv pom.xml.filtered pom.xml

# 编译目标模块
RUN mvn clean package -DskipTests -Dmaven.test.skip=true -pl iot-tdengine/iot-tdengine-biz -am

# ======================= 运行时阶段 =======================
FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds AS runtime

# 安全设置：创建非root用户（Rocky Linux 使用 groupadd/useradd）
RUN groupadd -r appgroup -g 1001 && useradd -r -u 1001 -g appgroup appuser

# 创建工作目录并设置权限
RUN mkdir -p /app && chown -R appuser:appgroup /app
WORKDIR /app

# 从构建阶段复制jar文件
COPY --from=build --chown=appuser:appgroup /app/iot-tdengine/iot-tdengine-biz/target/iot-tdengine-biz.jar app.jar

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
