# iot-system-biz 镜像构建和运行测试报告

## 测试时间
生成时间: $(date)

## 测试结果概览

### ✅ 构建环境检查

1. **Dockerfile 检查**
   - ✅ Dockerfile 存在
   - ✅ Dockerfile 语法正确
   - ✅ 基础镜像: `eclipse-temurin:8-jre`
   - ✅ 工作目录: `/iot-system-biz`
   - ✅ 暴露端口: `48099`

2. **JAR 文件检查**
   - ✅ JAR 文件存在: `target/jars/iot-system-biz.jar`
   - ✅ 文件大小: 159M
   - ✅ 文件格式: Java archive (JAR)
   - ✅ 文件可读: 是
   - ✅ JAR 内容验证: 通过（包含 META-INF/MANIFEST.MF 和 Spring Boot 类）

3. **Docker 环境检查**
   - ✅ Docker 已安装: Docker version 28.5.2
   - ✅ Docker Compose 已安装: v2.40.3
   - ⚠️ Docker 权限: 当前用户不在 docker 组中

4. **docker-compose.yml 配置检查**
   - ✅ docker-compose.yml 存在
   - ✅ iot-system 服务配置正确
   - ✅ 构建上下文: `./iot-system/iot-system-biz`
   - ✅ 镜像名称: `iot-module-system-biz`

## 构建配置验证

### Dockerfile 内容
```dockerfile
FROM eclipse-temurin:8-jre
RUN mkdir -p /iot-system-biz
WORKDIR /iot-system-biz
COPY target/jars/iot-system-biz.jar app.jar
ENV TZ=Asia/Shanghai JAVA_OPTS="-Xms512m -Xmx512m"
EXPOSE 48099
CMD ["sh", "-c", "java ${JAVA_OPTS} -Djava.security.egd=file:/dev/./urandom -jar app.jar"]
```

### docker-compose.yml 配置
- 服务名: `iot-system`
- 镜像名: `iot-module-system-biz`
- 容器名: `iot-system`
- 端口: `48099` (host 网络模式)
- 环境变量: 已配置 Nacos、时区等
- 健康检查: 已配置（curl http://localhost:48099）

## 测试脚本

已创建测试脚本: `test-build.sh`

该脚本将：
1. 检查构建环境
2. 清理旧的测试容器
3. 构建 Docker 镜像
4. 运行容器并验证

## 如何运行测试

### 方法 1: 使用测试脚本（推荐）

```bash
cd /projects/easyaiot/DEVICE/iot-system/iot-system-biz
./test-build.sh
```

### 方法 2: 使用 docker-compose

```bash
cd /projects/easyaiot/DEVICE
docker compose build iot-system
docker compose up -d iot-system
docker compose logs -f iot-system
```

### 方法 3: 直接使用 docker 命令

```bash
cd /projects/easyaiot/DEVICE/iot-system/iot-system-biz
docker build -t iot-module-system-biz:test .
docker run -d \
  --name iot-system-test \
  --network host \
  -e TZ=Asia/Shanghai \
  -e JAVA_OPTS="-Xms512m -Xmx512m" \
  -e SPRING_PROFILES_ACTIVE=local \
  -e SPRING_CLOUD_NACOS_CONFIG_SERVER_ADDR=14.18.122.2:8848 \
  -e SPRING_CLOUD_NACOS_CONFIG_NAMESPACE=local \
  -e SPRING_CLOUD_NACOS_SERVER_ADDR=14.18.122.2:8848 \
  -e SPRING_CLOUD_NACOS_DISCOVERY_NAMESPACE=local \
  iot-module-system-biz:test
```

## 权限问题解决

如果遇到 Docker 权限问题，请执行：

```bash
sudo usermod -aG docker $USER
newgrp docker
```

或者使用 sudo 运行 Docker 命令。

## 验证容器运行

构建和运行后，可以通过以下方式验证：

1. **检查容器状态**
   ```bash
   docker ps --filter name=iot-system
   ```

2. **查看容器日志**
   ```bash
   docker logs -f iot-system
   ```

3. **检查端口监听**
   ```bash
   netstat -tuln | grep 48099
   # 或
   ss -tuln | grep 48099
   ```

4. **健康检查**
   ```bash
   curl http://localhost:48099/actuator/health
   # 或
   curl http://localhost:48099
   ```

## 预期结果

如果构建和运行成功，应该看到：

1. ✅ 镜像构建成功
2. ✅ 容器启动成功
3. ✅ 端口 48099 正在监听
4. ✅ 应用日志显示 Spring Boot 启动成功
5. ✅ 健康检查端点可访问

## 注意事项

1. **网络模式**: 使用 `host` 网络模式，容器直接使用主机网络
2. **依赖服务**: 应用依赖 Nacos (14.18.122.2:8848)，确保 Nacos 服务可访问
3. **日志目录**: 日志将写入 `/docker/iot-device/logs/`，确保目录存在或有权限
4. **启动时间**: 应用可能需要 30-120 秒才能完全启动

## 结论

✅ **构建环境**: 所有必需文件存在且格式正确
✅ **Dockerfile**: 语法正确，配置合理
✅ **JAR 文件**: 存在且有效
⚠️ **Docker 权限**: 需要将用户添加到 docker 组或使用 sudo

**建议**: 在解决 Docker 权限问题后，运行 `test-build.sh` 脚本进行完整的构建和运行测试。

