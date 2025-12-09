# 视频文件推流快速操作指南

## 快速开始

### Windows PowerShell（推荐）

```powershell
# 1. 进入脚本目录
cd .scripts\srs

# 2. 使用默认配置推流（默认推流 VIDEO/video/video2.mp4 到本地SRS服务器）
.\push_video_to_srs.ps1

# 3. 推流到指定服务器
.\push_video_to_srs.ps1 -SrsHost "192.168.1.200"

# 4. 推流到指定服务器和流名
.\push_video_to_srs.ps1 -SrsHost "192.168.1.200" -Stream "camera01"
```

### Linux/Ubuntu/Mac

```bash
# 1. 进入脚本目录
cd .scripts/srs

# 2. 添加执行权限（首次使用）
chmod +x push_video_to_srs.sh

# 3. 使用默认配置推流（默认推流 VIDEO/video/video2.mp4 到本地SRS服务器）
./push_video_to_srs.sh

# 4. 推流到指定服务器
./push_video_to_srs.sh -h "192.168.1.200"

# 5. 推流到指定服务器和流名
./push_video_to_srs.sh -h "192.168.1.200" -s "camera01"
```

## 默认配置

- **视频文件**: `VIDEO/video/video2.mp4`（相对于项目根目录）
- **SRS服务器**: `127.0.0.1:1935`
- **应用名**: `live`
- **流名**: `test`
- **循环播放**: 是（默认循环）
- **编码模式**: Copy模式（性能更好）

## 常用参数

### Windows PowerShell

| 参数 | 说明 | 示例 |
|------|------|------|
| `-SrsHost` | SRS服务器地址 | `-SrsHost "192.168.1.200"` |
| `-SrsPort` | SRS服务器端口 | `-SrsPort 1935` |
| `-Stream` | 流名称 | `-Stream "camera01"` |
| `-VideoFile` | 视频文件路径 | `-VideoFile "VIDEO/video/video2.mp4"` |
| `-NoLoop` | 不循环播放 | `-NoLoop` |
| `-ReEncode` | 重新编码模式 | `-ReEncode` |

### Linux/Ubuntu/Mac

| 参数 | 说明 | 示例 |
|------|------|------|
| `-h, --host` | SRS服务器地址 | `-h "192.168.1.200"` |
| `-p, --port` | SRS服务器端口 | `-p 1935` |
| `-s, --stream` | 流名称 | `-s "camera01"` |
| `-v, --video` | 视频文件路径 | `-v "VIDEO/video/video2.mp4"` |
| `--no-loop` | 不循环播放 | `--no-loop` |
| `--re-encode` | 重新编码模式 | `--re-encode` |

## 使用场景示例

### 场景1：本地测试推流

```powershell
# Windows
.\push_video_to_srs.ps1
```

```bash
# Linux/Mac
./push_video_to_srs.sh
```

### 场景2：推流到远程SRS服务器

```powershell
# Windows
.\push_video_to_srs.ps1 -SrsHost "192.168.1.200" -Stream "video_stream_01"
```

```bash
# Linux/Mac
./push_video_to_srs.sh -h "192.168.1.200" -s "video_stream_01"
```

### 场景3：推流其他视频文件

```powershell
# Windows - 使用相对路径
.\push_video_to_srs.ps1 -VideoFile "VIDEO/video/another_video.mp4"

# Windows - 使用绝对路径
.\push_video_to_srs.ps1 -VideoFile "D:\Videos\test.mp4"
```

```bash
# Linux/Mac - 使用相对路径
./push_video_to_srs.sh -v "VIDEO/video/another_video.mp4"

# Linux/Mac - 使用绝对路径
./push_video_to_srs.sh -v "/home/user/videos/test.mp4"
```

### 场景4：播放一次后退出（不循环）

```powershell
# Windows
.\push_video_to_srs.ps1 -NoLoop
```

```bash
# Linux/Mac
./push_video_to_srs.sh --no-loop
```

### 场景5：视频格式不兼容，需要重新编码

```powershell
# Windows
.\push_video_to_srs.ps1 -ReEncode
```

```bash
# Linux/Mac
./push_video_to_srs.sh --re-encode
```

### 场景6：完整参数示例

```powershell
# Windows
.\push_video_to_srs.ps1 `
    -VideoFile "VIDEO/video/video2.mp4" `
    -SrsHost "192.168.1.200" `
    -SrsPort 1935 `
    -App "live" `
    -Stream "camera01" `
    -ReEncode
```

```bash
# Linux/Mac
./push_video_to_srs.sh \
    -v "VIDEO/video/video2.mp4" \
    -h "192.168.1.200" \
    -p 1935 \
    -a "live" \
    -s "camera01" \
    --re-encode
```

## 播放推流

推流成功后，可以通过以下方式播放：

### RTMP播放
```
rtmp://<SRS_HOST>:1935/<APP>/<STREAM>
示例: rtmp://127.0.0.1:1935/live/test
```

### HTTP-FLV播放
```
http://<SRS_HOST>:8080/<APP>/<STREAM>.flv
示例: http://127.0.0.1:8080/live/test.flv
```

### WebRTC播放
```
webrtc://<SRS_HOST>:8000/<APP>/<STREAM>
示例: webrtc://127.0.0.1:8000/live/test
```

### 使用VLC播放器测试

1. 打开VLC播放器
2. 媒体 → 打开网络串流
3. 输入RTMP地址：`rtmp://127.0.0.1:1935/live/test`
4. 点击播放

## 停止推流

按 `Ctrl+C` 停止推流。

## 故障排查

### 问题1：视频文件不存在

**错误信息**: `错误: 视频文件不存在`

**解决方法**:
1. 检查视频文件路径是否正确
2. 确保文件位于项目根目录下的 `VIDEO/video/` 目录
3. 或使用绝对路径指定视频文件

### 问题2：ffmpeg未找到

**错误信息**: `错误: 无法找到ffmpeg`

**解决方法**:
1. 安装ffmpeg：
   - Windows: 下载 https://ffmpeg.org/download.html
   - Linux/Ubuntu: `sudo apt install -y ffmpeg`
   - Mac: `brew install ffmpeg`
2. 将ffmpeg添加到系统PATH环境变量
3. 或使用 `-FfmpegPath` 参数指定ffmpeg完整路径

### 问题3：推流失败

**可能原因**:
- SRS服务器未运行
- 网络连接问题
- 视频编码格式不兼容

**解决方法**:
1. 检查SRS服务器状态：访问 `http://127.0.0.1:1985/api/v1/streams/`
2. 检查网络连接：`ping <SRS_HOST>`
3. 尝试使用重新编码模式：添加 `-ReEncode` 或 `--re-encode` 参数
4. 使用VLC等播放器测试视频文件是否可以正常播放

### 问题4：视频格式不兼容

**解决方法**:
使用重新编码模式：
```powershell
# Windows
.\push_video_to_srs.ps1 -ReEncode
```

```bash
# Linux/Mac
./push_video_to_srs.sh --re-encode
```

## 注意事项

1. **视频文件路径**：
   - 相对路径：相对于项目根目录（如 `VIDEO/video/video2.mp4`）
   - 绝对路径：完整路径（如 `D:\Videos\video.mp4` 或 `/home/user/videos/video.mp4`）

2. **循环播放**：
   - 默认循环播放视频
   - 使用 `-NoLoop` 或 `--no-loop` 参数可禁用循环

3. **编码模式**：
   - Copy模式（默认）：性能好，但需要编码格式兼容
   - 重新编码模式：兼容性好，但CPU占用更高

4. **网络要求**：
   - 确保视频文件所在机器与SRS服务器网络可达
   - 检查防火墙是否允许1935端口通信

5. **性能建议**：
   - 长时间推流建议使用后台服务或任务计划程序
   - 推流会占用网络带宽，注意网络负载

## 更多信息

详细文档请参考：[README.md](./README.md)
