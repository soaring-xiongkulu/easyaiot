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

# 复制项目配置文件以利用 Docker 缓存层
COPY pom.xml .
COPY lombok.config .

# 仅复制父模块和必要的通用模块，提前分离依赖下载层
COPY iot-parent/pom.xml ./iot-parent/
COPY iot-common/pom.xml ./iot-common/
COPY iot-system/pom.xml ./iot-system/
COPY iot-infra/pom.xml ./iot-infra/
COPY iot-file/pom.xml ./iot-file/
COPY iot-dataset/pom.xml ./iot-dataset/

# 过滤不需要的模块
RUN awk '
/<modules>/,/<\/modules>/ {
    if (/<module>iot-(gateway|device|tdengine|sink|message)<\/module>/) next
    print
}' pom.xml > pom.xml.filtered && \
mv pom.xml.filtered pom.xml

# 下载依赖（优化构建缓存）
# -B 表示非交互模式，-C 表示严格模式
RUN mvn dependency:go-offline -B -C

# 复制所有模块的源代码
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-infra ./iot-infra
COPY iot-file ./iot-file
COPY iot-dataset ./iot-dataset

# 编译项目并跳过测试
RUN mvn clean package -DskipTests -Dmaven.test.skip=true -pl iot-dataset/iot-dataset-biz -am

# ======================= 运行时阶段 =======================
FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds

# 创建非 root 用户以提升安全性
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建工作目录并设置权限
RUN mkdir -p /app && chown -R appuser:appuser /app
WORKDIR /app

# 从构建阶段复制 jar 文件，并保留正确的文件权限
COPY --from=build --chown=appuser:appuser /app/iot-dataset/iot-dataset-biz/target/iot-dataset-biz.jar app.jar

# 环境变量配置
ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48087 \
    JAVA_OPTS="-Xms512m -Xmx512m -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai"

# 暴露应用端口
EXPOSE 48087

# 健康检查端点
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1

# 切换到非 root 用户
USER appuser

# 启动应用（使用 exec 形式以确保信号正确处理）
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
