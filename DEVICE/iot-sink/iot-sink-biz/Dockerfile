# ======================= 运行时阶段 =======================
# 此 Dockerfile 从宿主机挂载的 Jar 包构建运行时镜像
# Jar 包应该已经通过 base-builder 服务编译并挂载到 ./target/jars/ 目录

FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds

# 创建目录，并使用它作为工作目录
RUN mkdir -p /iot-sink-biz
WORKDIR /iot-sink-biz

# 从宿主机挂载的 Jar 包目录复制构建产物
COPY target/jars/iot-sink-biz.jar app.jar

# 如果 Jar 包不存在，给出提示
RUN if [ ! -f app.jar ]; then \
        echo "错误: iot-sink-biz.jar 不存在！请先运行 base-builder 服务编译 Jar 包。" && \
        exit 1; \
    fi

# 设置 TZ 时区
# 设置 JAVA_OPTS 环境变量，可通过 docker run -e "JAVA_OPTS=" 进行覆盖
ENV TZ=Asia/Shanghai JAVA_OPTS="-Xms512m -Xmx512m"

# 暴露后端项目的 48092 端口
EXPOSE 48092

# 启动后端项目
CMD java ${JAVA_OPTS} -Djava.security.egd=file:/dev/./urandom -jar app.jar
