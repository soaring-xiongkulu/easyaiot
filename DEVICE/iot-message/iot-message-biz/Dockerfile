# 使用maven镜像进行底层编译
FROM maven:3.9.11-eclipse-temurin-21-alpine AS build

# 配置 Maven 使用阿里镜像源
RUN mkdir -p /root/.m2 && \
    echo '<?xml version="1.0" encoding="UTF-8"?>' > /root/.m2/settings.xml && \
    echo '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"' >> /root/.m2/settings.xml && \
    echo '          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' >> /root/.m2/settings.xml && \
    echo '          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">' >> /root/.m2/settings.xml && \
    echo '  <mirrors>' >> /root/.m2/settings.xml && \
    echo '    <mirror>' >> /root/.m2/settings.xml && \
    echo '      <id>aliyun</id>' >> /root/.m2/settings.xml && \
    echo '      <mirrorOf>central</mirrorOf>' >> /root/.m2/settings.xml && \
    echo '      <name>Aliyun Maven</name>' >> /root/.m2/settings.xml && \
    echo '      <url>https://maven.aliyun.com/nexus/content/groups/public/</url>' >> /root/.m2/settings.xml && \
    echo '    </mirror>' >> /root/.m2/settings.xml && \
    echo '  </mirrors>' >> /root/.m2/settings.xml && \
    echo '</settings>' >> /root/.m2/settings.xml

# 设置工作目录
WORKDIR /app

# 复制根目录的 pom.xml、lombok.config 和所有模块
COPY pom.xml .
COPY lombok.config .
COPY iot-parent ./iot-parent
COPY iot-common ./iot-common
COPY iot-system ./iot-system
COPY iot-infra ./iot-infra
COPY iot-message ./iot-message

# 修改 pom.xml，只保留需要的模块，避免 Maven 检查不存在的模块
RUN sed -i.bak \
    -e '/<module>iot-gateway<\/module>/d' \
    -e '/<module>iot-file<\/module>/d' \
    -e '/<module>iot-dataset<\/module>/d' \
    -e '/<module>iot-device<\/module>/d' \
    -e '/<module>iot-tdengine<\/module>/d' \
    -e '/<module>iot-sink<\/module>/d' \
    pom.xml && rm -f pom.xml.bak

# 编译项目（只编译 iot-message-biz 及其依赖）
RUN mvn clean package -DskipTests -pl iot-message/iot-message-biz -am

# 切换镜像 - 使用 Java 21
FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds

# 创建目录，并使用它作为工作目录
RUN mkdir -p /iot-message-biz
WORKDIR /iot-message-biz

# 从build阶段中拷贝产物
COPY --from=build /app/iot-message/iot-message-biz/target/iot-message-biz.jar app.jar

# 设置 TZ 时区
# 设置 JAVA_OPTS 环境变量，可通过 docker run -e "JAVA_OPTS=" 进行覆盖
ENV TZ=Asia/Shanghai JAVA_OPTS="-Xms512m -Xmx512m"

# 暴露后端项目的 48093 端口
EXPOSE 48093

# 启动后端项目
CMD java ${JAVA_OPTS} -Djava.security.egd=file:/dev/./urandom -jar app.jar

