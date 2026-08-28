FROM bellsoft/liberica-openjdk-rocky:21.0.8-cds

RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN mkdir -p /app && chown -R appuser:appuser /app
WORKDIR /app

COPY target/jars/iot-flow-biz.jar app.jar
RUN chown appuser:appuser app.jar

ENV TZ=Asia/Shanghai \
    LANG=C.UTF-8 \
    SERVER_PORT=48097 \
    JAVA_OPTS="-Xms256m -Xmx512m -Djava.security.egd=file:/dev/./urandom -Duser.timezone=Asia/Shanghai"

EXPOSE 48097

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${SERVER_PORT}/actuator/health || exit 1

USER appuser
ENTRYPOINT ["sh", "-c", "java ${JAVA_OPTS} -jar app.jar"]
