# TRANSFORM Runtime 镜像（无状态，可同节点多副本）
# build:
#   docker build -t easyaiot/transform-runtime:1.0.0 -f TRANSFORM/Dockerfile TRANSFORM
# run (单实例示例):
#   docker run -d --name transform-demo -p 48096:48096 \
#     -e KAFKA_BOOTSTRAP=host.docker.internal:9092 \
#     -e POSTGRES_URL=jdbc:postgresql://host.docker.internal:5432/iot-transform20 \
#     -e TRANSFORM_INSTANCE_ID=demo-1 \
#     easyaiot/transform-runtime:1.0.0

# 默认用仓库已缓存的 Temurin 21；若环境可拉官方镜像可改为 eclipse-temurin:21-jre-jammy
ARG BASE_IMAGE=maven:3.9.11-eclipse-temurin-21-alpine
FROM ${BASE_IMAGE}

WORKDIR /opt/easyaiot/TRANSFORM

ARG JAR_FILE=transform-runtime/target/transform-runtime-1.0.0.jar
COPY ${JAR_FILE} /opt/easyaiot/TRANSFORM/transform-runtime.jar
COPY scripts/run-runtime-container.sh /opt/easyaiot/TRANSFORM/run-runtime-container.sh

RUN chmod +x /opt/easyaiot/TRANSFORM/run-runtime-container.sh \
    && mkdir -p /opt/easyaiot/TRANSFORM/data/transform-backup

ENV SPRING_PROFILES_ACTIVE=local \
    SERVER_PORT=48096 \
    TRANSFORM_ROLE=full \
    TRANSFORM_BACKUP_DIR=/opt/easyaiot/TRANSFORM/data/transform-backup \
    JAVA_OPTS="-Xms256m -Xmx1024m"

EXPOSE 48096

ENTRYPOINT ["/opt/easyaiot/TRANSFORM/run-runtime-container.sh"]
