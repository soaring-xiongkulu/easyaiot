# 系统要求

- Linux 或类 Unix 操作系统
- 至少 2GB 内存
- 至少 5GB 可用磁盘空间
- GCC 4.4 或更高版本（用于编译源码）

## TDEngine部署
### 1. 更新系统包
```
sudo yum update -y # CentOS/RHEL/Rocky Linux
或
sudo apt update -y # Ubuntu/Debian
安装必要的依赖
sudo yum install -y wget curl gnupg2 # CentOS/RHEL/Rocky Linux
或
sudo apt install -y wget curl gnupg2 # Ubuntu/Debian
```

### 2. 下载 TDengine

访问 [TDengine 官网](https://tdengine.com/) 获取最新版本的下载链接：

#### 下载 TDengine Server (以 3.0 版本为例)
```
wget https://www.tdengine.com/assets-download/3.0/TDengine-server-3.0.0.0-Linux-x64.tar.gz
```

### 3. 安装 TDengine
#### 解压安装包
```
tar -zxvf TDengine-server-3.0.0.0-Linux-x64.tar.gz cd TDengine-server-3.0.0.0-Linux-x64
```

#### 运行安装脚本
```
sudo ./install.sh
```

安装过程中会提示你选择安装组件和服务配置。

### 4. 启动 TDengine 服务

#### 启动 TDengine 服务
```
sudo systemctl start taosd
```
#### 设置开机自启
```
sudo systemctl enable taosd
```
#### 检查服务状态
```
sudo systemctl status taosd
```

### 5. 验证安装
#### 连接到 TDengine
```
taos
```
#### 在 TDengine shell 中执行测试命令
```
show databases;
```

如果看到系统默认数据库，说明 TDengine 安装成功。

## 配置 TDengine

### 主要配置文件

TDengine 的主要配置文件位于 `/etc/taos/taos.cfg`：
```
sudo vim /etc/taos/taos.cfg
```

### 常见配置项包括：
#### 数据目录
```
dataDir /var/lib/taos
```
#### 日志目录
```
logDir /var/log/taos
```
#### 数据目录
```dataDir /var/lib/taos```
#### 日志目录
```logDir /var/log/taos```
#### 服务端口
```serverPort 6030```
#### 监控端口
```monitorPort 6043```
#### 内部使用的端口范围
如果在防火墙环境中，需要开放这个端口范围
```arbitratorPort 6042```

### 配置防火墙

如果启用了防火墙，需要开放 TDengine 相关端口：
```
CentOS/RHEL/Rocky Linux (firewalld)
sudo firewall-cmd --permanent --add-port=6030/tcp sudo firewall-cmd --permanent --add-port=6030-6042/tcp sudo firewall-cmd --reload
Ubuntu/Debian (ufw)
sudo ufw allow 6030/tcp sudo ufw allow 6030:6042/tcp sudo ufw reload
```
### 重启服务使配置生效
```
sudo systemctl restart taosd
```
## 基本使用

### 连接 TDengine
#### 使用默认用户连接 (root 用户，无密码)
```taos```
#### 使用指定用户连接
```taos -u username -p```
#### 连接远程 TDengine 实例
```taos -h hostname -P port -u username -p```

### 基本操作
```
-- 创建数据库 CREATE DATABASE power;
-- 使用数据库 USE power;
-- 创建表 CREATE TABLE meters (ts TIMESTAMP, current FLOAT, voltage INT, phase FLOAT);
-- 插入数据 INSERT INTO meters VALUES (NOW, 10.2, 219, 0.32);
-- 查询数据 SELECT * FROM meters;
-- 创建子表 CREATE TABLE d1001 USING meters TAGS ('California.SanFrancisco', 2);
```
## 管理命令

### 服务管理
```
启动服务
sudo systemctl start taosd
停止服务
sudo systemctl stop taosd
重启服务
sudo systemctl restart taosd
查看服务状态
sudo systemctl status taosd
查看服务日志
sudo journalctl -u taosd -f
```
### 数据库管理
```
-- 查看数据库列表 SHOW DATABASES;
-- 查看数据表 SHOW TABLES;
-- 查看表结构 DESCRIBE table_name;
-- 删除数据库 DROP DATABASE database_name;
```

## 性能优化配置

在 `/etc/taos/taos.cfg` 中添加或修改以下配置项：
```
缓冲区大小 (根据系统内存调整)
cache 16
查询缓存大小
blocks 8
最大连接数
maxConnections 1000
最小创建表时的并行度
minimalCreateTableParallel 10
最大创建表时的并行度
maxCreateTableParallel 100
查询超时时间 (秒)
queryTimeout 10
RPC超时时间 (秒)
rpcTimer 300
数据文件滚动周期 (小时)
daysPerFile 10
数据保留天数
keep 3650
时间精度
precision us
```

## 安全配置

### 设置密码
```
-- 连接 TDengine 后修改 root 用户密码 
ALTER USER root PASS 'new_password';
```

### 配置用户权限
```
-- 创建新用户 CREATE USER username PASS 'password';
-- 授权用户访问数据库 GRANT READ ON database_name TO username; GRANT WRITE ON database_name TO username;
-- 撤销权限 REVOKE READ ON database_name FROM username;
-- 删除用户 DROP USER username;
```
### 启用 HTTPS (可选)

在配置文件中添加：
```
启用 HTTPS
enableHttps true
HTTPS 端口
httpsPort 443
证书文件路径
sslCertPath /path/to/cert.pem sslKeyPath /path/to/key.pem
```
## 监控和维护

### 查看系统信息
```
-- 查看系统状态 SHOW STATUS;
-- 查看数据库信息 SHOW DATABASES;
-- 查看连接信息 SHOW CONNECTIONS;
```
### 备份和恢复
```
备份数据库
taosdump -u root -p password database_name > backup.sql
恢复数据库
taosdump -u root -p password -i backup.sql
```
### 日志管理
```
查看 TDengine 日志
tail -f /var/log/taos/taosd.log
查看错误日志
tail -f /var/log/taos/taosd.log | grep ERROR
```
## 集群部署

对于生产环境，建议部署 TDengine 集群以提高可用性和扩展性：

1. 准备至少 3 台服务器
2. 在每台服务器上安装 TDengine
3. 配置各节点信息：
```
在第一台服务器上
fqdn tdengine1.example.com serverPort 6030
在第二台服务器上
fqdn tdengine2.example.com serverPort 6030
在第三台服务器上
fqdn tdengine3.example.com serverPort 6030
```
5. 启动所有节点：
```
sudo systemctl start taosd
```

## 故障排除

### 常见问题

1. **服务无法启动**：
   - 检查日志文件：`/var/log/taos/taosd.log`
   - 确认端口未被占用：`netstat -tuln | grep 6030`
   - 检查配置文件语法

2. **连接被拒绝**：
   - 确认服务正在运行：`systemctl status taosd`
   - 检查防火墙设置
   - 验证网络连接：`telnet hostname 6030`

3. **磁盘空间不足**：
   - 清理旧数据：`DROP DATABASE old_database`
   - 增加磁盘空间
   - 调整数据保留策略

### 性能调优

1. **内存使用过高**：
   - 调整 cache 和 blocks 参数
   - 优化查询语句
   - 考虑增加物理内存

2. **写入性能下降**：
   - 检查磁盘 I/O 性能
   - 调整 daysPerFile 参数
   - 考虑使用批量插入

3. **查询响应慢**：
   - 添加合适的索引
   - 优化查询语句
   - 考虑数据分片

通过以上步骤，您可以成功部署和配置 TDengine，开始处理和分析时序数据。
