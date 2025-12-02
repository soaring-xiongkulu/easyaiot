# Nexus3 Docker 镜像仓库使用指南

本文档介绍如何在 Nexus3 中创建 Docker 镜像仓库，以及如何上传和下载镜像。

## 前置条件

1. Nexus3 已安装并运行（参考 `install.sh`）
2. 已获取管理员账号和密码（默认账号：`admin`，密码在 `nexus_data/admin.password` 文件中）
3. 已安装 Docker 客户端

## 一、创建 Docker 镜像仓库

### 1.1 登录 Nexus3 管理界面

1. 打开浏览器，访问：`http://localhost:18081`
2. 点击右上角 **Sign In** 登录
3. 使用管理员账号登录（首次登录需要修改默认密码）

### 1.2 创建 Docker 仓库

#### 步骤 1：进入仓库管理

1. 点击左侧菜单 **Administration**（齿轮图标）
2. 选择 **Repository** → **Repositories**

#### 步骤 2：创建仓库

1. 点击右上角 **Create repository** 按钮
2. 选择仓库类型：**docker (hosted)**
   - **hosted**: 用于存储您自己构建的镜像
   - **proxy**: 用于代理远程仓库（如 Docker Hub）
   - **group**: 用于组合多个仓库

#### 步骤 3：配置仓库信息

填写以下信息：

- **Name**: 仓库名称（例如：`docker-hosted`）
- **HTTP**: 勾选 **HTTP**，端口填写 `8082`（或自定义端口，需在 docker-compose.yml 中配置）
- **Allow anonymous docker pull**: 根据需要选择是否允许匿名拉取
- **Enable Docker V1 API**: 建议取消勾选（使用 V2 API）
- **Storage**: 选择 Blob Store（默认使用 `default`）

#### 步骤 4：保存配置

点击 **Create repository** 完成创建

### 1.3 配置 Docker 仓库端口（如需要）

如果使用自定义端口（非 8082），需要在 `docker-compose.yml` 中添加端口映射：

```yaml
services:
  nexus:
    ports:
      - "18081:8081"  # Web 界面端口
      - "18082:8082"  # Docker 仓库端口（根据实际配置）
```

然后重启服务：

```bash
./install.sh restart
```

## 二、配置 Docker 客户端

### 2.1 获取仓库地址

在 Nexus3 中创建的 Docker 仓库地址格式为：
```
http://<nexus-host>:<port>/repository/<repository-name>
```

例如：
```
http://localhost:18082/repository/docker-hosted
```

### 2.2 配置 Docker 登录认证

#### 方法 1：使用 Nexus3 用户账号

1. 在 Nexus3 中创建用户（**Administration** → **Users** → **Create user**）
2. 为用户分配 **nx-docker** 权限（**Administration** → **Roles** → 创建角色并分配权限）
3. 使用该用户账号登录 Docker：

```bash
docker login http://localhost:18082/repository/docker-hosted
# 输入用户名和密码
```

#### 方法 2：使用管理员账号（不推荐用于生产环境）

```bash
docker login http://localhost:18082/repository/docker-hosted
# 用户名: admin
# 密码: <管理员密码>
```

### 2.3 配置 Docker 允许不安全仓库（HTTP）

如果使用 HTTP 协议，需要配置 Docker 允许不安全的仓库：

#### Linux 系统

编辑或创建 `/etc/docker/daemon.json`：

```json
{
  "insecure-registries": ["localhost:18082", "127.0.0.1:18082"]
}
```

重启 Docker 服务：

```bash
sudo systemctl restart docker
```

#### macOS/Windows

在 Docker Desktop 设置中：
1. 打开 **Settings** → **Docker Engine**
2. 添加以下配置：

```json
{
  "insecure-registries": ["localhost:18082", "127.0.0.1:18082"]
}
```

3. 点击 **Apply & Restart**

## 三、上传镜像到 Nexus3

### 3.1 标记镜像

首先需要将本地镜像标记为 Nexus3 仓库地址格式：

```bash
docker tag <本地镜像名>:<标签> <nexus地址>/<镜像名>:<标签>
```

**示例**：

```bash
# 假设本地有一个镜像 nginx:latest
docker tag nginx:latest localhost:18082/repository/docker-hosted/nginx:latest

# 或者使用完整路径
docker tag nginx:latest localhost:18082/repository/docker-hosted/my-nginx:v1.0
```

### 3.2 推送镜像

使用 `docker push` 命令推送镜像：

```bash
docker push localhost:18082/repository/docker-hosted/nginx:latest
```

**完整示例流程**：

```bash
# 1. 登录 Nexus3 Docker 仓库
docker login http://localhost:18082/repository/docker-hosted

# 2. 标记镜像
docker tag nginx:latest localhost:18082/repository/docker-hosted/nginx:latest

# 3. 推送镜像
docker push localhost:18082/repository/docker-hosted/nginx:latest
```

### 3.3 验证上传

1. 登录 Nexus3 Web 界面
2. 进入 **Browse** → **Browse** → 选择创建的 Docker 仓库
3. 查看上传的镜像

## 四、从 Nexus3 下载镜像

### 4.1 拉取镜像

使用 `docker pull` 命令从 Nexus3 拉取镜像：

```bash
docker pull localhost:18082/repository/docker-hosted/nginx:latest
```

### 4.2 完整示例

```bash
# 1. 登录（如果需要认证）
docker login http://localhost:18082/repository/docker-hosted

# 2. 拉取镜像
docker pull localhost:18082/repository/docker-hosted/nginx:latest

# 3. 验证镜像
docker images | grep nginx
```

## 五、常用操作示例

### 5.1 完整工作流程

```bash
# 1. 构建镜像
docker build -t my-app:1.0.0 .

# 2. 登录 Nexus3
docker login http://localhost:18082/repository/docker-hosted

# 3. 标记镜像
docker tag my-app:1.0.0 localhost:18082/repository/docker-hosted/my-app:1.0.0

# 4. 推送镜像
docker push localhost:18082/repository/docker-hosted/my-app:1.0.0

# 5. 在其他机器上拉取
docker pull localhost:18082/repository/docker-hosted/my-app:1.0.0
```

### 5.2 批量操作

```bash
# 批量推送多个标签
docker tag my-app:1.0.0 localhost:18082/repository/docker-hosted/my-app:1.0.0
docker tag my-app:1.0.0 localhost:18082/repository/docker-hosted/my-app:latest
docker push localhost:18082/repository/docker-hosted/my-app:1.0.0
docker push localhost:18082/repository/docker-hosted/my-app:latest
```

### 5.3 删除镜像

在 Nexus3 Web 界面中：
1. 进入 **Browse** → 选择仓库
2. 找到要删除的镜像
3. 点击删除按钮

## 六、创建代理仓库（可选）

如果需要代理 Docker Hub 或其他公共仓库：

1. 创建仓库时选择 **docker (proxy)**
2. 配置：
   - **Name**: `docker-proxy`
   - **Remote storage**: `https://registry-1.docker.io`（Docker Hub）
   - **HTTP**: 端口 `8083`（或其他端口）
3. 拉取时使用代理仓库地址：

```bash
docker pull localhost:18083/repository/docker-proxy/nginx:latest
```

## 七、创建组合仓库（可选）

组合仓库可以将多个仓库合并为一个访问点：

1. 创建仓库时选择 **docker (group)**
2. 配置：
   - **Name**: `docker-group`
   - **Member repositories**: 选择要组合的仓库（如 `docker-hosted` 和 `docker-proxy`）
   - **HTTP**: 端口 `8084`
3. 使用组合仓库地址访问：

```bash
# 可以从组合仓库中拉取所有成员仓库的镜像
docker pull localhost:18084/repository/docker-group/nginx:latest
```

## 八、常见问题

### 8.1 推送镜像时提示 "unauthorized"

**原因**：未登录或认证失败

**解决方案**：
1. 确认已执行 `docker login`
2. 检查用户名和密码是否正确
3. 确认用户有推送权限

### 8.2 推送镜像时提示 "dial tcp: lookup localhost"

**原因**：Docker 客户端无法解析 localhost

**解决方案**：
- 使用 IP 地址替代 localhost：`127.0.0.1:18082`
- 或配置 `/etc/hosts` 文件

### 8.3 推送镜像时提示 "http: server gave HTTP response to HTTPS client"

**原因**：Docker 尝试使用 HTTPS 连接 HTTP 仓库

**解决方案**：
1. 确认已配置 `insecure-registries`（见 2.3 节）
2. 重启 Docker 服务
3. 确认仓库地址使用 `http://` 前缀

### 8.4 端口冲突

**原因**：配置的端口已被占用

**解决方案**：
1. 检查端口占用：`netstat -tuln | grep 18082`
2. 修改 `docker-compose.yml` 中的端口映射
3. 在 Nexus3 中修改仓库的 HTTP 端口配置

### 8.5 镜像上传后无法在 Web 界面看到

**原因**：可能需要等待索引更新

**解决方案**：
1. 等待几分钟让 Nexus3 完成索引
2. 刷新浏览器页面
3. 检查 **Browse** → **Browse** 中是否正确选择仓库

## 九、安全建议

1. **使用 HTTPS**：生产环境建议配置 HTTPS 和 SSL 证书
2. **创建专用用户**：不要使用管理员账号进行日常操作
3. **设置访问权限**：为不同用户分配适当的权限
4. **定期清理**：删除不再使用的镜像以节省存储空间
5. **备份数据**：定期备份 `nexus_data` 目录

## 十、参考信息

- Nexus3 访问地址：`http://localhost:18081`
- 默认管理员账号：`admin`
- 默认密码文件：`nexus_data/admin.password`
- Docker 仓库端口：根据配置而定（默认建议 8082）

---

**最后更新**: 2024年

