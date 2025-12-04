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

# 复制所有子模块的 pom.xml（Maven 需要这些文件来解析模块结构）
RUN mkdir -p iot-common/iot-common-base iot-common/iot-common-env iot-common/iot-common-mybatis \
    iot-common/iot-common-redis iot-common/iot-common-web iot-common/iot-common-security \
    iot-common/iot-common-protection iot-common/iot-common-job iot-common/iot-common-mq \
    iot-common/iot-common-rpc iot-common/iot-common-excel iot-common/iot-common-test \
    iot-common/iot-common-tenant iot-common/iot-common-data-permission iot-common/iot-common-ip \
    iot-common/iot-common-swagger iot-common/iot-common-protocol \
    iot-system/iot-system-api iot-system/iot-system-biz \
    iot-infra/iot-infra-api iot-infra/iot-infra-biz \
    iot-file/iot-file-api iot-file/iot-file-biz
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
COPY iot-file/iot-file-api/pom.xml ./iot-file/iot-file-api/
COPY iot-file/iot-file-biz/pom.xml ./iot-file/iot-file-biz/

# 过滤不需要的模块以优化构建范围
RUN awk '/<modules>/,/<\/modules>/ { if (/<module>iot-(gateway|dataset|device|tdengine|sink|message)<\/module>/) next } 1' pom.xml > pom.xml.filtered && \
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
