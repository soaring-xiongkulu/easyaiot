# ======================= 运行时阶段 =======================
# 此 Dockerfile 从宿主机挂载的 Jar 包构建运行时镜像
# Jar 包应该已经通过 base-builder 服务编译并挂载到 ./target/jars/ 目录

FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds

# 创建目录，并使用它作为工作目录
RUN mkdir -p /iot-sink-biz
WORKDIR /iot-sink-biz

# 从宿主机挂载的 Jar 包目录复制构建产物
COPY target/jars/iot-sink-biz.jar app.jar

# 设置 TZ 时区
# 设置 JAVA_OPTS 环境变量，可通过 docker run -e "JAVA_OPTS=" 进行覆盖
ENV TZ=Asia/Shanghai JAVA_OPTS="-Xms512m -Xmx512m"

# 暴露后端项目的 48092 端口
EXPOSE 48092

# Desktop 在容器快速 remove/recreate 后偶发仍无法立即重新绑定应用端口，短暂退避后再启动。
# 使用 exec 保证 Java 成为 PID 1，启动失败退出时 restart: always 可以正确接管。
CMD ["sh", "-c", "sleep \"${IOT_SINK_START_DELAY_SEC:-2}\"; exec java ${JAVA_OPTS} -Djava.security.egd=file:/dev/./urandom -jar app.jar"]
