#!/bin/bash
# TDengine 容器启动脚本
# 修复 FQDN 配置并启动 taosd 和 taosadapter 服务

set -e

# 增加文件描述符限制（在容器内再次设置，确保生效）
ulimit -n 65536 2>/dev/null || true

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
  
  # 添加其他优化配置
  if ! grep -q "^maxOpenFiles" /etc/taos/taos.cfg; then
    echo "maxOpenFiles               65536" >> /etc/taos/taos.cfg
  fi
  
  if ! grep -q "^numOfThreadsPerCore" /etc/taos/taos.cfg; then
    echo "numOfThreadsPerCore        2.0" >> /etc/taos/taos.cfg
  fi
fi

# 修复数据目录中的 dnode.json（如果存在）
if [ -f "/var/lib/taos/dnode/dnode.json" ]; then
  sed -i 's/"fqdn":\s*"[^"]*"/"fqdn": "localhost"/g' /var/lib/taos/dnode/dnode.json 2>/dev/null || true
fi

# 清理可能存在的锁文件
rm -f /var/lib/taos/taosd.lock 2>/dev/null || true

# 启动 taosd（后台运行）
echo "启动 taosd 服务..."
taosd &
TAOSD_PID=$!

# 检查 taosd 进程是否启动成功
sleep 2
if ! kill -0 $TAOSD_PID 2>/dev/null; then
  echo "✗ 错误: taosd 进程启动失败"
  exit 1
fi

# 等待 taosd 就绪（增加等待时间和检查逻辑）
echo "等待 TDengine 服务就绪..."
MAX_WAIT=120
WAIT_COUNT=0
READY=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
  # 检查进程是否还在运行
  if ! kill -0 $TAOSD_PID 2>/dev/null; then
    echo "✗ 错误: taosd 进程意外退出"
    exit 1
  fi
  
  # 检查端口是否监听
  if netstat -tuln 2>/dev/null | grep -q ":6030" || ss -tuln 2>/dev/null | grep -q ":6030"; then
    # 尝试连接数据库
    if taos -h localhost -s "select 1;" > /dev/null 2>&1; then
      # 再次确认，检查集群ID是否有效（不为0）
      cluster_check=$(taos -h localhost -s "show dnodes;" 2>/dev/null | grep -c "localhost" || echo "0")
      if [ "$cluster_check" -gt 0 ]; then
        echo "✓ TDengine 服务已就绪（进程运行正常，端口监听正常，连接测试通过）"
        READY=1
        break
      fi
    fi
  fi
  
  WAIT_COUNT=$((WAIT_COUNT + 1))
  if [ $((WAIT_COUNT % 10)) -eq 0 ]; then
    echo "  等待中... ($WAIT_COUNT/$MAX_WAIT 秒)"
  fi
  sleep 1
done

if [ $READY -eq 0 ]; then
  echo "✗ 错误: TDengine 服务在 $MAX_WAIT 秒内未能就绪"
  echo "检查 taosd 日志:"
  tail -n 50 /var/log/taos/taosd.log 2>/dev/null || echo "无法读取日志文件"
  exit 1
fi

# 启动 taosadapter（RESTful 接口，提供 6041 端口）
if [ -f "/usr/local/bin/taosadapter" ] || command -v taosadapter > /dev/null 2>&1; then
  echo "启动 taosadapter (RESTful 接口)..."
  taosadapter &
  TAOSADAPTER_PID=$!
  
  # 等待 taosadapter 启动
  sleep 2
  if kill -0 $TAOSADAPTER_PID 2>/dev/null; then
    echo "✓ taosadapter 已启动"
  else
    echo "⚠️  警告: taosadapter 启动可能失败，但继续运行"
  fi
  
  # 等待所有进程
  wait $TAOSD_PID $TAOSADAPTER_PID 2>/dev/null || wait $TAOSD_PID
else
  echo "⚠️  警告: taosadapter 未找到，6041 端口将不可用"
  # 只等待 taosd
  wait $TAOSD_PID
fi

