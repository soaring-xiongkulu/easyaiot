# 部署环境

本文档介绍如何在 CentOS 7.9 系统上准备 EasyAIoT 项目的部署环境。

## 系统要求

- 操作系统：CentOS 7.9
- JDK 版本：Java 8
- 内存：建议 8GB 以上
- 存储空间：建议 50GB 以上可用空间

## 安装基础工具

### 检查和卸载旧版本 JDK
# 检查是否已安装 JDK
rpm -qa | grep java

# 如果存在旧版本，卸载它们
sudo yum remove -y java-1.7.0-openjdk java-1.8.0-openjdk

# 安装 OpenJDK 8
sudo yum install -y java-1.8.0-openjdk java-1.8.0-openjdk-devel

# 验证安装
java -version
javac -version

# 设置 JAVA_HOME 环境变量
echo 'export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk' >> ~/.bashrc
echo 'export PATH=$PATH:$JAVA_HOME/bin' >> ~/.bashrc

# 使配置生效
source ~/.bashrc

# 验证环境变量
echo $JAVA_HOME

# 停止防火墙服务
sudo systemctl stop firewalld

# 禁用防火墙开机自启
sudo systemctl disable firewalld

# 检查防火墙状态
sudo systemctl status firewalld

# 临时关闭 SELinux
sudo setenforce 0

# 永久关闭 SELinux
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config

# 添加配置到 /etc/security/limits.conf
echo '* soft nofile 65535' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65535' | sudo tee -a /etc/security/limits.conf

# 添加内核参数
cat << EOF | sudo tee -a /etc/sysctl.conf
net.core.somaxconn = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_syn_backlog = 8192
EOF

# 使配置生效
sudo sysctl -p

# 检查 Java 版本
java -version

# 检查防火墙状态
sudo systemctl status firewalld

# 检查 SELinux 状态
getenforce

# 检查文件句柄限制
ulimit -n

