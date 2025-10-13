# 系统要求

- 操作系统：Linux、Windows 或 macOS
- 内存：至少 2GB RAM
- 磁盘空间：至少 500MB 可用空间
- 权限：管理员或 root 权限

## 下载并解压 Nacos

```
下载 Nacos 2.2.3（与 PostgreSQL 兼容的版本）
wget https://github.com/alibaba/nacos/releases/download/2.2.3/nacos-server-2.2.3.tar.gz
解压
tar -zxvf nacos-server-2.2.3.tar.gz
创建日志目录
mkdir -p /var/log/easyaiot/nacos
```

### 配置 PostgreSQL 数据库

```
首先需要在 PostgreSQL 中创建 Nacos 数据库和用户：

切换到 postgres 用户
sudo -u postgres psql
执行以下 SQL 命令

sql -- 创建数据库 CREATE DATABASE nacos;
-- 创建用户 CREATE USER nacos WITH PASSWORD 'nacos';
-- 授权 GRANT ALL PRIVILEGES ON DATABASE nacos TO nacos;
-- 退出 \q
```

### 配置 Nacos

```
进入 Nacos 配置目录
cd /opt/easyaiot/nacos/conf
备份原配置文件
cp application.properties application.properties.bak

编辑 `application.properties` 文件：

properties #*************** Spring Boot Related Configurations ***************#
Default web context path:
server.servlet.contextPath=/nacos
Default web server port:
server.port=8848
#*************** Network Related Configurations ***************#
If prefer hostname over ip for Nacos server addresses in cluster.conf:
nacos.inetutils.prefer-hostname-over-ip=false
Specify local server's IP:
nacos.inetutils.ip-address=
#*************** Config Module Related Configurations ***************#
If use MySQL as datasource:
spring.datasource.platform=postgresql
Count of DB:
db.num=1
Connect URL of DB:
db.url.0=jdbc:postgresql://127.0.0.1:5432/nacos?characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true&useUnicode=true&useSSL=false&serverTimezone=UTC&allowPublicKeyRetrieval=true db.user.0=nacos db.password.0=nacos
Connection pool configuration: hikariCP
db.pool.config.connectionTimeout=30000 db.pool.config.validationTimeout=10000 db.pool.config.maximumPoolSize=20 db.pool.config.minimumIdle=2
#*************** Cluster Related Configurations ***************#
if mode is standalone:
nacos.standalone=true
#*************** Metrics Related Configurations **************# management.endpoints.web.exposure.include=
#*************** Access Log Related Configurations ***************# server.tomcat.accesslog.enabled=true server.tomcat.accesslog.pattern=%h %l %u %t "%r" %s %b %D %{User-Agent}i %{Request-Source}i
#*************** Access Control Related Configurations ***************#
If enable spring security, this option is deprecated in 1.2.0:
spring.security.enabled=false
The ignore urls of auth, is deprecated in 1.2.0:
nacos.security.ignore.urls=/,/error,//*.css,//.js,/**/.html,//*.map,//.svg,/**/.png,//*.ico,/console-ui/public/,/v1/auth/,/v1/console/health/,/actuator/,/v1/console/server/
The auth system to use, currently only 'nacos' is supported:
nacos.core.auth.system.type=nacos
If turn on auth system:
nacos.core.auth.enabled=false
The token expiration in seconds:
nacos.core.auth.default.token.expire.seconds=18000
The default token:
nacos.core.auth.default.token.secret.key=SecretKey012345678901234567890123456789012345678901234567890123456789
Turn on/off caching of auth information. By turning on this switch, the update of auth information would have a 15 seconds delay.
nacos.core.auth.caching.enabled=true
#*************** Istio Related Configurations ***************#
If turn on the MCP server:
nacos.istio.mcp.server.enabled=false
```

### 初始化数据库

```
下载 PostgreSQL 驱动并初始化数据库：

下载 PostgreSQL 驱动
cd /opt/easyaiot/nacos/plugins wget https://jdbc.postgresql.org/download/postgresql-42.6.0.jar
复制数据库初始化脚本到可访问位置
cd /opt/easyaiot/nacos/conf cp schema.sql /tmp/nacos-schema.sql
导入 Nacos PostgreSQL 数据库结构
sudo -u postgres psql -d nacos -f /tmp/nacos-schema.sql
```

### 创建启动脚本

创建 `/opt/easyaiot/nacos/bin/start.sh`：

```
Nacos 启动脚本
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk export PATH=$JAVA_HOME/bin:$PATH export NACOS_HOME=/opt/easyaiot/nacos
JVM 参数设置
export JAVA_OPT="-server -Xms512m -Xmx512m -Xmn256m"
cd $NACOS_HOME/bin ./startup.sh -m standalone

```

创建 `/opt/easyaiot/nacos/bin/stop.sh`：

```
Nacos 停止脚本
export NACOS_HOME=/opt/easyaiot/nacos
cd $NACOS_HOME/bin ./shutdown.sh

```

设置脚本权限：

设置脚本执行权限
chmod +x /opt/easyaiot/nacos/bin/start.sh chmod +x /opt/easyaiot/nacos/bin/stop.sh

### 配置 systemd 服务（可选）

创建 `/etc/systemd/system/nacos.service`：

```
[Unit] Description=nacos After=network.target
[Service] Type=forking User=root ExecStart=/opt/easyaiot/nacos/bin/start.sh ExecStop=/opt/easyaiot/nacos/bin/stop.sh Restart=always RestartSec=10
[Install] WantedBy=multi-user.target
```

启用并启动服务：
```
重新加载 systemd 配置
sudo systemctl daemon-reload
设置开机自启
sudo systemctl enable nacos
启动服务
sudo systemctl start nacos
检查服务状态
sudo systemctl status nacos
```

### 验证部署

```
检查端口是否监听
netstat -tlnp | grep 8848
查看日志
tail -f /opt/easyaiot/nacos/logs/start.out
访问 Web 界面
浏览器访问: http://your-server-ip:8848/nacos
默认用户名/密码: nacos/nacos
```

Nacos 部署完成。默认登录账号密码为 `nacos/nacos`，建议登录后立即修改密码。




