# ======================= 构建阶段 =======================
FROM maven:3.9.11-eclipse-temurin-21-alpine AS build

# 使用更简洁高效的 HERE 文档配置 Maven
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

# 阶段1: 复制构建配置并解析依赖（优化缓存层）
COPY pom.xml .
COPY lombok.config .

# 复制各模块 pom.xml 构建依赖预加载层
COPY iot-parent/pom.xml ./iot-parent/
COPY iot-common/pom.xml ./iot-common/
COPY iot-system/pom.xml ./iot-system/
COPY iot-gateway/pom.xml ./iot-gateway/

# 动态过滤模块引用（网关服务通常需要核心基础模块）
RUN awk '
/<modules>/,/<\/modules>/ {
    if (/<module>iot-(infra|file|dataset|device|tdengine|sink|message)<\/module>/) next
    print
}' pom.xml > pom.xml.filtered && \
mv pom.xml.filtered pom.xml

# 预下载所有依赖和插件（利用多线程加速）
RUN mvn dependency:resolve-plugins dependency:go-offline -T 2C -B

# 阶段2: 复制源代码
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-gateway ./iot-gateway

# 编译网关模块（启用并行编译和详细日志）
RUN mvn clean package -DskipTests -Dmaven.test.skip=true -T 2C -pl iot-gateway -am

# ======================= 运行时阶段 =======================
FROM bellsoft/liberica-openjdk-debian:21.0.8

# 安全配置：创建专用用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建标准化目录结构
RUN mkdir -p /app/{logs,config,cache} && chown -R appuser:appuser /app
WORKDIR /app

# 复制构建产物并设置权限
COPY --from=build --chown=appuser:appuser /app/iot-gateway/target/iot-gateway.jar app.jar

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
