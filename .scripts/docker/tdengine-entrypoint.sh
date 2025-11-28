#!/bin/bash
# TDengine 容器启动脚本
# 修复 FQDN 配置并启动 taosd 和 taosadapter 服务

set -e

# 修复 FQDN 配置
if [ -f "/etc/taos/taos.cfg" ]; then
  sed -i "s/^fqdn.*/fqdn                      localhost/" /etc/taos/taos.cfg 2>/dev/null || \
  (sed -i "/^fqdn/d" /etc/taos/taos.cfg && echo "fqdn                      localhost" >> /etc/taos/taos.cfg)
  
  # 禁用 UDF 以减少日志噪音（如果不需要 UDF 功能）
  if ! grep -q "^enableUdf" /etc/taos/taos.cfg; then
    echo "enableUdf                 0" >> /etc/taos/taos.cfg
  else
    sed -i "s/^enableUdf.*/enableUdf                 0/" /etc/taos/taos.cfg
  fi
fi

# 修复数据目录中的 dnode.json（如果存在）
if [ -f "/var/lib/taos/dnode/dnode.json" ]; then
  sed -i 's/"fqdn":\s*"[^"]*"/"fqdn": "localhost"/g' /var/lib/taos/dnode/dnode.json 2>/dev/null || true
fi

# 启动 taosd（后台运行）
taosd &
TAOSD_PID=$!

# 等待 taosd 就绪
echo "等待 TDengine 服务就绪..."
for i in $(seq 1 30); do
  if taos -h localhost -s "select 1;" > /dev/null 2>&1; then
    echo "✓ TDengine 服务已就绪"
    break
  fi
  sleep 1
done

# 启动 taosadapter（RESTful 接口，提供 6041 端口）
if [ -f "/usr/local/bin/taosadapter" ] || command -v taosadapter > /dev/null 2>&1; then
  echo "启动 taosadapter (RESTful 接口)..."
  taosadapter &
  TAOSADAPTER_PID=$!
  echo "✓ taosadapter 已启动"
  # 等待所有进程
  wait $TAOSD_PID $TAOSADAPTER_PID
else
  echo "⚠️  警告: taosadapter 未找到，6041 端口将不可用"
  # 只等待 taosd
  wait $TAOSD_PID
fi

