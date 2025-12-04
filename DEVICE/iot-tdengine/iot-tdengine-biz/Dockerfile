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

# 复制各模块 pom.xml
COPY iot-parent/pom.xml ./iot-parent/
COPY iot-common/pom.xml ./iot-common/
COPY iot-system/pom.xml ./iot-system/
COPY iot-infra/pom.xml ./iot-infra/
COPY iot-device/pom.xml ./iot-device/
COPY iot-tdengine/pom.xml ./iot-tdengine/

# 复制所有子模块的 pom.xml（Maven 需要这些文件来解析模块结构）
RUN mkdir -p iot-common/iot-common-base iot-common/iot-common-env iot-common/iot-common-mybatis \
    iot-common/iot-common-redis iot-common/iot-common-web iot-common/iot-common-security \
    iot-common/iot-common-protection iot-common/iot-common-job iot-common/iot-common-mq \
    iot-common/iot-common-rpc iot-common/iot-common-excel iot-common/iot-common-test \
    iot-common/iot-common-tenant iot-common/iot-common-data-permission iot-common/iot-common-ip \
    iot-common/iot-common-swagger iot-common/iot-common-protocol \
    iot-system/iot-system-api iot-system/iot-system-biz \
    iot-infra/iot-infra-api iot-infra/iot-infra-biz \
    iot-device/iot-device-api iot-device/iot-device-biz \
    iot-tdengine/iot-tdengine-api iot-tdengine/iot-tdengine-biz
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
COPY iot-device/iot-device-api/pom.xml ./iot-device/iot-device-api/
COPY iot-device/iot-device-biz/pom.xml ./iot-device/iot-device-biz/
COPY iot-tdengine/iot-tdengine-api/pom.xml ./iot-tdengine/iot-tdengine-api/
COPY iot-tdengine/iot-tdengine-biz/pom.xml ./iot-tdengine/iot-tdengine-biz/

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
RUN awk '/<modules>/,/<\/modules>/ { if (/<module>iot-(gateway|file|dataset|sink|message)<\/module>/) next } 1' pom.xml > pom.xml.filtered && \
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
