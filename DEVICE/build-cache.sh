#!/bin/bash

# 构建缓存脚本 - 用于构建和保存build阶段的镜像，以加速后续构建

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}开始构建build阶段镜像缓存...${NC}"

# 定义服务和对应的Dockerfile路径
declare -A SERVICES=(
    ["iot-gateway"]="iot-gateway/Dockerfile"
    ["iot-module-system-biz"]="iot-system/iot-system-biz/Dockerfile"
    ["iot-module-infra-biz"]="iot-infra/iot-infra-biz/Dockerfile"
    ["iot-module-device-biz"]="iot-device/iot-device-biz/Dockerfile"
    ["iot-module-dataset-biz"]="iot-dataset/iot-dataset-biz/Dockerfile"
    ["iot-module-tdengine-biz"]="iot-tdengine/iot-tdengine-biz/Dockerfile"
    ["iot-module-file-biz"]="iot-file/iot-file-biz/Dockerfile"
)

# 构建每个服务的build阶段镜像
for SERVICE_NAME in "${!SERVICES[@]}"; do
    DOCKERFILE="${SERVICES[$SERVICE_NAME]}"
    CACHE_TAG="${SERVICE_NAME}:build"
    
    echo -e "${YELLOW}正在构建 ${SERVICE_NAME} 的build阶段镜像...${NC}"
    
    # 构建build阶段的镜像并打标签
    docker build \
        --target build \
        --tag "${CACHE_TAG}" \
        --file "${DOCKERFILE}" \
        . || {
        echo -e "${RED}构建 ${SERVICE_NAME} 的build阶段镜像失败${NC}"
        exit 1
    }
    
    echo -e "${GREEN}✓ ${SERVICE_NAME} 的build阶段镜像已保存为 ${CACHE_TAG}${NC}"
done

echo -e "${GREEN}所有build阶段镜像缓存构建完成！${NC}"
echo -e "${YELLOW}提示：现在可以使用 docker-compose build 或 docker-compose up --build 来利用这些缓存加速构建${NC}"

