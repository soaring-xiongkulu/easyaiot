# 系统要求

- 操作系统：Linux、Windows 或 macOS
- 内存：至少 2GB RAM
- 磁盘空间：至少 500MB 可用空间
- 权限：管理员或 root 权限

## 在不同平台上的安装步骤

### Linux (Ubuntu/Debian)

1. **更新包管理器**
```
bash sudo apt update
```

2. **安装必要的依赖**
```
sudo apt install wget ca-certificates
```

3. **添加 PostgreSQL 官方 GPG 密钥**
```
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
```

4. **添加 PostgreSQL 官方存储库**
```
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
```

5. **更新包列表**
```
sudo apt update
```

6. **安装 PostgreSQL 16.9**
```
sudo apt install postgresql-16 postgresql-client-16
```

7. **启动并启用 PostgreSQL 服务**
```
sudo systemctl start postgresql 
sudo systemctl enable postgresql
```

### Windows

1. **下载安装程序**
   - 访问 [PostgreSQL 官网下载页面](https://www.postgresql.org/download/windows/)
   - 下载适用于 Windows 的 PostgreSQL 16.9 安装程序

2. **运行安装程序**
   - 以管理员身份运行下载的安装程序
   - 按照安装向导的指示进行操作
   - 在安装过程中设置 postgres 用户密码
   - 选择要安装的组件（建议安装默认组件）

3. **配置环境变量**
   - 将 PostgreSQL 的 bin 目录添加到系统 PATH 环境变量中
   - 默认路径通常是 `C:\Program Files\PostgreSQL\16\bin`

### macOS

1. **使用 Homebrew 安装（推荐）**
```
brew install postgresql@16
```

2. **启动 PostgreSQL 服务**
```
brew services start postgresql@16
```
## 初始化数据库
```
安装完成后，需要初始化数据库集群：
sudo -u postgres initdb -D /var/lib/postgresql/data
```

## 配置 PostgreSQL

### 修改 postgres 用户密码
```
sudo -u postgres psql \password postgres \q
```

### 配置远程访问（可选）

1. 编辑 `postgresql.conf` 文件：
```
sudo nano /etc/postgresql/16/main/postgresql.conf
取消注释并修改以下行：
listen_addresses = '*'
```

2. 编辑 `pg_hba.conf` 文件：
```
sudo nano /etc/postgresql/16/main/pg_hba.conf
添加允许远程连接的规则。
```

3. 重启 PostgreSQL 服务：
```
sudo systemctl restart postgresql
```

## 验证安装
通过以下命令验证 PostgreSQL 是否正确安装并运行：
```
sudo -u postgres psql -c "SELECT version();"
```

## 常用管理命令

- 启动服务：`sudo systemctl start postgresql`
- 停止服务：`sudo systemctl stop postgresql`
- 重启服务：`sudo systemctl restart postgresql`
- 查看状态：`sudo systemctl status postgresql`

   
   
   
