# 系统要求

- Linux 或类 Unix 操作系统
- 至少 2GB 内存
- 至少 5GB 可用磁盘空间
- GCC 4.4 或更高版本（用于编译源码）

## 安装步骤

### 1. 下载 Redis

访问 Redis 官网获取最新稳定版本的下载链接：

### 2. 编译安装
```
# 编译 Redis
make

# 可选：运行测试套件
make test

# 安装到系统目录
sudo make install

```

### 3. 配置 Redis
创建 Redis 配置目录和数据目录：
```
# 创建配置目录
sudo mkdir -p /etc/redis

# 创建数据目录
sudo mkdir -p /var/lib/redis

# 创建日志目录
sudo mkdir -p /var/log/redis

# 复制配置文件
sudo cp redis.conf /etc/redis/redis.conf

```
编辑配置文件：
```
sudo vim /etc/redis/redis.conf

```
主要配置项包括：
```
# 以守护进程方式运行
daemonize yes

# 监听地址 (生产环境建议绑定具体IP)
bind 127.0.0.1

# 端口号
port 6379

# 数据目录
dir /var/lib/redis

# 日志文件
logfile /var/log/redis/redis-server.log

# 数据库文件名
dbfilename dump.rdb

# 密码认证 (取消注释并设置密码)
# requirepass yourpassword

# 最大内存限制 (根据系统内存设置)
# maxmemory 2gb

# 内存淘汰策略
# maxmemory-policy allkeys-lru

```

### 4. 创建系统用户
```
# 创建 Redis 用户
sudo adduser --system --group --no-create-home redis

```

### 5. 设置权限
```
# 设置目录权限
sudo chown -R redis:redis /var/lib/redis
sudo chown -R redis:redis /var/log/redis
sudo chown redis:redis /etc/redis/redis.conf
sudo chmod 640 /etc/redis/redis.conf

```

### 6. 创建 systemd 服务文件
创建服务文件：
```
sudo vim /etc/systemd/system/redis.service

```
内容如下：
```
[Unit]
Description=Advanced key-value store
After=network.target
Documentation=http://redis.io/documentation, man:redis-server(1)

[Service]
Type=forking
User=redis
Group=redis
ExecStart=/usr/local/bin/redis-server /etc/redis/redis.conf
ExecStop=/usr/local/bin/redis-cli shutdown
TimeoutStopSec=0
Restart=always

[Install]
WantedBy=multi-user.target
Alias=redis.service

```
重新加载 systemd 配置：
```
sudo systemctl daemon-reload

```

### 7. 启动 Redis
```
# 启动 Redis 服务
sudo systemctl start redis

# 设置开机自启
sudo systemctl enable redis

# 检查服务状态
sudo systemctl status redis

```

验证 Redis 是否启动成功：
```
# 检查进程
ps aux | grep redis

# 检查端口监听
netstat -tuln | grep 6379

# 测试连接
redis-cli ping

```
如果返回 PONG，则表示 Redis 正常运行。

## 基本使用
### 连接 Redis
```
# 连接到本地 Redis
redis-cli

# 连接到远程 Redis (需要配置 bind 和密码)
redis-cli -h hostname -p port -a password

```
### 基本操作
```
# 设置键值对
SET mykey "Hello Redis"

# 获取键值
GET mykey

# 检查键是否存在
EXISTS mykey

# 删除键
DEL mykey

# 查看所有键
KEYS *

# 设置过期时间 (秒)
EXPIRE mykey 60

# 查看剩余过期时间
TTL mykey

```

### 常用管理命令
```
# 查看 Redis 服务器信息
INFO

# 查看客户端连接
CLIENT LIST

# 查看内存使用情况
INFO memory

# 清空当前数据库
FLUSHDB

# 清空所有数据库
FLUSHALL

# 保存数据到磁盘
SAVE

# 后台保存数据到磁盘
BGSAVE

# 查看慢查询日志
SLOWLOG GET

```

### 性能优化配置
在 /etc/redis/redis.conf 中添加或修改以下配置：
```
# TCP 连接队列大小
tcp-backlog 511

# 客户端最大连接数
maxclients 10000

# 最大内存限制
maxmemory 2gb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# 启用 AOF 持久化
appendonly yes

# AOF 同步策略 (everysec 平衡性能和安全性)
appendfsync everysec

# AOF 文件名
appendfilename "appendonly.aof"

# 启用 AOF 重写时的自动重写
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 关闭在磁盘满时的写入保护
no-appendfsync-on-rewrite yes

# 哈希表编码优化
hash-max-ziplist-entries 512
hash-max-ziplist-value 64

# 列表编码优化
list-max-ziplist-size -2

# 集合编码优化
set-max-intset-entries 512

# 有序集合编码优化
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

```
## 安全配置
### 设置密码认证
#### 在配置文件中设置密码：
```
requirepass yourstrongpassword

```
#### 连接时使用密码：
```
# 方式1：启动时指定密码
redis-cli -a yourstrongpassword

# 方式2：连接后认证
redis-cli
AUTH yourstrongpassword

```
#### 限制访问
```
# 绑定特定IP地址
bind 127.0.0.1 192.168.1.100

# 禁用危险命令
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_b8f2d3a7"

```

#### 启用 TLS/SSL (Redis 6.0+)
```
# 启用 TLS
tls-port 6380
port 0

# 证书文件路径
tls-cert-file /path/to/server.crt
tls-key-file /path/to/server.key
tls-ca-cert-file /path/to/ca.crt

# 客户端认证
tls-auth-clients yes

```
#### 监控和维护
```
# 查看连接数
redis-cli INFO clients | grep connected_clients

# 查看内存使用
redis-cli INFO memory | grep used_memory_human

# 查看命中率
redis-cli INFO stats | grep keyspace_hits
redis-cli INFO stats | grep keyspace_misses

```

#### 备份策略
```
# RDB 备份 (在 redis.conf 中配置)
save 900 1
save 300 10
save 60 10000

# AOF 备份
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
```


