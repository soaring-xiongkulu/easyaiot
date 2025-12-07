# RTMP推流问题排查指南

## 问题现象

运行 `./test_video.py` 时出现错误：
```
Error opening output file rtmp://localhost:1935/live/...
Error opening output files: Input/output error
```

## 问题原因

SRS服务器配置了 `on_publish` 回调，当客户端尝试推流时，SRS会调用回调URL验证是否允许推流。如果回调服务不可访问，SRS会拒绝推流请求。

当前SRS配置的回调地址：
- `http://172.18.0.1:48080/admin-api/video/camera/callback/on_publish`

## 快速诊断

运行诊断工具：
```bash
cd /opt/projects/easyaiot/VIDEO
python diagnose_rtmp_issue.py
```

诊断工具会检查：
- ✅ SRS服务状态和端口
- ✅ VIDEO服务状态和端口
- ✅ 网关服务状态和端口
- ✅ 回调端点可访问性

## 解决方案

### 方案1: 启动VIDEO服务（推荐用于开发测试）

```bash
cd /opt/projects/easyaiot/VIDEO
python run.py
```

VIDEO服务会在端口6000上启动，但SRS配置的是通过网关(48080)访问。

**注意**: 如果SRS配置的回调地址是 `http://172.18.0.1:48080/...`，需要：
1. 启动网关服务（DEVICE服务），或
2. 使用方案2（临时mock服务器）

### 方案2: 使用临时Mock回调服务器（仅用于测试）

如果VIDEO服务或网关服务未运行，可以使用临时mock回调服务器：

```bash
cd /opt/projects/easyaiot/VIDEO
python mock_callback_server.py --port 48080
```

**重要**: 
- Mock服务器会快速响应所有回调请求，允许推流
- 仅用于测试，生产环境必须使用真实的VIDEO服务
- 确保SRS可以访问到mock服务器的地址（172.18.0.1:48080）

### 方案3: 修改SRS配置（临时禁用回调）

如果需要临时禁用回调进行测试，可以修改SRS配置文件：

1. 编辑SRS配置文件（通常在 `.scripts/srs/conf/docker.conf`）
2. 注释掉或删除 `http_hooks` 配置块中的 `on_publish` 行：

```conf
http_hooks {
    enabled             on;
    on_dvr              http://172.18.0.1:48080/admin-api/video/camera/callback/on_dvr;
    # on_publish          http://172.18.0.1:48080/admin-api/video/camera/callback/on_publish;  # 临时禁用
}
```

3. 重启SRS容器：
```bash
docker restart srs-server
```

**注意**: 禁用回调后，将无法检测和处理流冲突。

## 验证修复

修复后，重新运行测试：
```bash
./test_video.py
```

如果推流成功，应该看到：
```
✅ 推流进程已启动 (PID: ...)
```

## 相关文件

- `diagnose_rtmp_issue.py` - 诊断工具
- `mock_callback_server.py` - 临时mock回调服务器
- `test_video.py` - 视频推流测试脚本
- `.scripts/srs/conf/docker.conf` - SRS配置文件

## 常见问题

### Q: 为什么需要回调服务？

A: SRS的回调机制用于：
- 验证推流权限
- 检测和处理流冲突（同一流被多个客户端推流）
- 记录推流事件

### Q: 如何查看SRS日志？

A:
```bash
docker logs srs-server --tail 100
```

### Q: 如何测试回调端点是否可访问？

A:
```bash
curl -X POST http://172.18.0.1:48080/admin-api/video/camera/callback/on_publish \
  -H "Content-Type: application/json" \
  -d '{"action":"on_publish","stream":"test"}'
```

如果返回 `{"code":0,"msg":null}` 表示可访问。

