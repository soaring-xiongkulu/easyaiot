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

# 复制所有子模块的 pom.xml（Maven 需要这些文件来解析模块结构）
RUN mkdir -p iot-common/iot-common-base iot-common/iot-common-env iot-common/iot-common-mybatis \
    iot-common/iot-common-redis iot-common/iot-common-web iot-common/iot-common-security \
    iot-common/iot-common-protection iot-common/iot-common-job iot-common/iot-common-mq \
    iot-common/iot-common-rpc iot-common/iot-common-excel iot-common/iot-common-test \
    iot-common/iot-common-tenant iot-common/iot-common-data-permission iot-common/iot-common-ip \
    iot-common/iot-common-swagger iot-common/iot-common-protocol \
    iot-system/iot-system-api iot-system/iot-system-biz \
    iot-infra/iot-infra-api iot-infra/iot-infra-biz \
    iot-message/iot-message-api iot-message/iot-message-biz
COPY iot-common/iot-common-base/pom.xml ./iot-common/iot-common-base/
COPY iot-common/iot-common-env/pom.xml ./iot-common/iot-common-env/
COPY iot-common/iot-common-mybatis/pom.xml ./iot-common/iot-common-mybatis/
COPY iot-common/iot-common-redis/pom.xml ./iot-common/iot-common-redis/
COPY iot-common/iot-common-web/pom.xml ./iot-common/iot-common-web/
COPY iot-common/iot-common-security/pom.xml ./iot-common/iot-common-security/
COPY iot-common/iot-common-protection/pom.xml ./iot-common/iot-common-protection/
COPY iot-common/iot-common-job/pom.xml ./iot-common/iot-common-job/
COPY iot-common/iot-common-mq/pom.xml ./iot-common/iot-common-mq/
COPY iot-common/iot-common-rpc/pom.xml ./iot-common/iot-common-rpc/
COPY iot-common/iot-common-excel/pom.xml ./iot-common/iot-common-excel/
COPY iot-common/iot-common-test/pom.xml ./iot-common/iot-common-test/
COPY iot-common/iot-common-tenant/pom.xml ./iot-common/iot-common-tenant/
COPY iot-common/iot-common-data-permission/pom.xml ./iot-common/iot-common-data-permission/
COPY iot-common/iot-common-ip/pom.xml ./iot-common/iot-common-ip/
COPY iot-common/iot-common-swagger/pom.xml ./iot-common/iot-common-swagger/
COPY iot-common/iot-common-protocol/pom.xml ./iot-common/iot-common-protocol/
COPY iot-system/iot-system-api/pom.xml ./iot-system/iot-system-api/
COPY iot-system/iot-system-biz/pom.xml ./iot-system/iot-system-biz/
COPY iot-infra/iot-infra-api/pom.xml ./iot-infra/iot-infra-api/
COPY iot-infra/iot-infra-biz/pom.xml ./iot-infra/iot-infra-biz/
COPY iot-message/iot-message-api/pom.xml ./iot-message/iot-message-api/
COPY iot-message/iot-message-biz/pom.xml ./iot-message/iot-message-biz/

# 动态过滤不需要的模块引用
RUN awk '/<modules>/,/<\/modules>/ { if (/<module>iot-(gateway|file|dataset|device|tdengine|sink)<\/module>/) next } 1' pom.xml > pom.xml.filtered && \
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
