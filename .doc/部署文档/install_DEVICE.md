# DEVICE模块部署文档

## 1. 系统概述

DEVICE是一个基于Java的物联网设备管理系统，用于监控和管理各种IoT设备。本系统采用Spring Boot框架开发，支持设备注册、数据采集、远程控制等功能。

## 2. 系统要求

### 2.1 硬件要求
- CPU: 2核以上
- 内存: 4GB以上
- 硬盘: 50GB可用空间

### 2.2 软件环境
- JDK 8或以上版本
- PostgreSQL 16.9
- Redis 3.0或以上版本
- Maven 3.6或以上版本

## 3. 部署前准备

### 3.1 安装JDK
下载并安装JDK 8或更高版本
```
sudo apt-get update sudo apt-get install openjdk-8-jdk
```
验证安装
```
java -version
```

### 3.2 安装PostgreSQL 16.9
添加PostgreSQL官方APT仓库
```
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add - echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
```
更新包列表并安装PostgreSQL 16.9
```
sudo apt-get update sudo apt-get install postgresql-16 postgresql-client-16
```
启动并启用PostgreSQL服务
```
sudo systemctl start postgresql sudo systemctl enable postgresql
```

### 3.3 安装Redis
安装Redis
```
sudo apt-get install redis-server
```
启动并启用Redis服务
```
sudo systemctl start redis 
sudo systemctl enable redis
```
### 3.4 安装Maven
安装Maven
```
sudo apt-get install maven
```
验证安装
```
mvn -version
```

## 4. 获取并编译源代码

### 4.1 克隆代码仓库
克隆项目代码
```
git clone https://gitee.com/soaring-xiongkulu/easyaiot.git
```

### 4.2 编译项目
```
mvn clean package install -DskipTests
```

### 5 启动项目
```
nohup java -jar iot-broker*.jar > iot-broker.log 2>&1 &
nohup java -jar iot-dataset*.jar > iot-dataset.log 2>&1 &
nohup java -jar iot-device*.jar > iot-device.log 2>&1 &
nohup java -jar iot-file*.jar > iot-file.log 2>&1 &
nohup java -jar iot-gateway*.jar > iot-gateway.log 2>&1 &
nohup java -jar iot-infra*.jar > iot-infra.log 2>&1 &
nohup java -jar iot-model*.jar > iot-model.log 2>&1 &
nohup java -jar iot-system*.jar > iot-system.log 2>&1 &
nohup java -jar iot-tdengine*.jar > iot-tdengine.log 2>&1 &
```
