# SRS推流脚本使用说明

## 概述

本目录包含用于将RTSP流和本地视频文件推送到SRS服务器的脚本，支持Windows、Linux/Ubuntu和Mac环境。

## 脚本文件

### RTSP推流脚本
- `push_rtsp_to_srs_mac.sh` - Mac Bash脚本
- `push_rtsp_to_srs.sh` - Linux/Ubuntu Bash脚本
- `push_rtsp_to_srs.ps1` - Windows PowerShell脚本（推荐）
- `push_rtsp_to_srs.bat` - Windows批处理脚本

### 视频文件推流脚本
- `push_video_to_srs.sh` - Linux/Ubuntu/Mac Bash脚本
- `push_video_to_srs.ps1` - Windows PowerShell脚本

## 前置要求

1. **安装FFmpeg**
   - **Mac**: `brew install ffmpeg`（推荐使用Homebrew）
   - **Linux/Ubuntu**: `sudo apt update && sudo apt install -y ffmpeg`
   - **Windows**: 下载地址: https://ffmpeg.org/download.html
   - 确保ffmpeg已添加到系统PATH环境变量中
   - 或使用脚本的参数指定ffmpeg完整路径

2. **SRS服务器**
   - 确保SRS服务器已启动并运行
   - 默认监听端口: 1935 (RTMP)

## Mac Bash脚本使用方法

### 基本用法

```bash
./push_rtsp_to_srs_mac.sh -u "rtsp://192.168.1.100:554/stream"
```

### 完整参数

```bash
./push_rtsp_to_srs_mac.sh \
    -u "rtsp://192.168.1.100:554/stream" \
    -h "192.168.1.200" \
    -p 1935 \
    -a "live" \
    -s "test" \
    -f "/opt/homebrew/bin/ffmpeg"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `-u, --url` | 是 | - | RTSP源流地址 |
| `-h, --host` | 否 | 127.0.0.1 | SRS服务器IP地址 |
| `-p, --port` | 否 | 1935 | SRS服务器RTMP端口 |
| `-a, --app` | 否 | live | 应用名称 |
| `-s, --stream` | 否 | test | 流名称 |
| `-f, --ffmpeg` | 否 | ffmpeg | FFmpeg可执行文件路径 |

### 示例

```bash
# 推流到本地SRS服务器
./push_rtsp_to_srs_mac.sh -u "rtsp://192.168.1.100:554/h264"

# 推流到局域网SRS服务器
./push_rtsp_to_srs_mac.sh -u "rtsp://192.168.1.100:554/stream" -h "192.168.1.200"

# 指定应用和流名称
./push_rtsp_to_srs_mac.sh -u "rtsp://192.168.1.100:554/stream" -h "192.168.1.200" -a "camera" -s "camera01"

# 使用自定义ffmpeg路径（Apple Silicon Mac）
./push_rtsp_to_srs_mac.sh -u "rtsp://192.168.1.100:554/stream" -f "/opt/homebrew/bin/ffmpeg"

# 使用自定义ffmpeg路径（Intel Mac）
./push_rtsp_to_srs_mac.sh -u "rtsp://192.168.1.100:554/stream" -f "/usr/local/bin/ffmpeg"
```

### 安装ffmpeg（Mac）

```bash
# 使用Homebrew安装（推荐）
brew install ffmpeg

# 如果使用Homebrew但找不到ffmpeg，可能需要添加到PATH
# Apple Silicon Mac:
export PATH="/opt/homebrew/bin:$PATH"

# Intel Mac:
export PATH="/usr/local/bin:$PATH"

# 将PATH添加到 ~/.zshrc 或 ~/.bash_profile 使其永久生效
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc  # Apple Silicon
# 或
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc     # Intel
```

### Mac脚本特性

- 自动检测常见的Mac ffmpeg安装路径（Homebrew默认路径）
- 支持Apple Silicon和Intel Mac
- 提供详细的错误提示和安装指导

## Linux/Ubuntu Bash脚本使用方法

### 基本用法

```bash
./push_rtsp_to_srs.sh -u "rtsp://192.168.1.100:554/stream"
```

### 完整参数

```bash
./push_rtsp_to_srs.sh \
    -u "rtsp://192.168.1.100:554/stream" \
    -h "192.168.1.200" \
    -p 1935 \
    -a "live" \
    -s "test" \
    -f "/usr/bin/ffmpeg"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `-u, --url` | 是 | - | RTSP源流地址 |
| `-h, --host` | 否 | 127.0.0.1 | SRS服务器IP地址 |
| `-p, --port` | 否 | 1935 | SRS服务器RTMP端口 |
| `-a, --app` | 否 | live | 应用名称 |
| `-s, --stream` | 否 | test | 流名称 |
| `-f, --ffmpeg` | 否 | ffmpeg | FFmpeg可执行文件路径 |

### 示例

```bash
# 推流到本地SRS服务器
./push_rtsp_to_srs.sh -u "rtsp://192.168.1.100:554/h264"

# 推流到局域网SRS服务器
./push_rtsp_to_srs.sh -u "rtsp://192.168.1.100:554/stream" -h "192.168.1.200"

# 指定应用和流名称
./push_rtsp_to_srs.sh -u "rtsp://192.168.1.100:554/stream" -h "192.168.1.200" -a "camera" -s "camera01"

# 使用自定义ffmpeg路径
./push_rtsp_to_srs.sh -u "rtsp://192.168.1.100:554/stream" -f "/usr/local/bin/ffmpeg"
```

### 安装ffmpeg（Ubuntu）

```bash
sudo apt update
sudo apt install -y ffmpeg
```

## PowerShell脚本使用方法

### 基本用法

```powershell
.\push_rtsp_to_srs.ps1 -RtspUrl "rtsp://192.168.1.100:554/stream"
```

### 完整参数

```powershell
.\push_rtsp_to_srs.ps1 `
    -RtspUrl "rtsp://192.168.1.100:554/stream" `
    -SrsHost "192.168.1.200" `
    -SrsPort 1935 `
    -App "live" `
    -Stream "test" `
    -FfmpegPath "C:\ffmpeg\bin\ffmpeg.exe"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `-RtspUrl` | 是 | - | RTSP源流地址 |
| `-SrsHost` | 否 | 127.0.0.1 | SRS服务器IP地址 |
| `-SrsPort` | 否 | 1935 | SRS服务器RTMP端口 |
| `-App` | 否 | live | 应用名称 |
| `-Stream` | 否 | test | 流名称 |
| `-FfmpegPath` | 否 | ffmpeg | FFmpeg可执行文件路径 |

### 示例

```powershell
# 推流到本地SRS服务器
.\push_rtsp_to_srs.ps1 -RtspUrl "rtsp://192.168.1.100:554/h264"

# 推流到局域网SRS服务器
.\push_rtsp_to_srs.ps1 -RtspUrl "rtsp://192.168.1.100:554/stream" -SrsHost "192.168.1.200"

# 指定应用和流名称
.\push_rtsp_to_srs.ps1 -RtspUrl "rtsp://192.168.1.100:554/stream" -App "camera" -Stream "camera01"

# 使用自定义ffmpeg路径
.\push_rtsp_to_srs.ps1 -RtspUrl "rtsp://192.168.1.100:554/stream" -FfmpegPath "D:\Tools\ffmpeg.exe"
```

## 批处理脚本使用方法

### 基本用法

```batch
push_rtsp_to_srs.bat rtsp://192.168.1.100:554/stream
```

### 完整参数

```batch
push_rtsp_to_srs.bat rtsp://192.168.1.100:554/stream 192.168.1.200 1935 live test
```

### 参数说明

1. RTSP源地址（必填）
2. SRS主机IP（可选，默认: 127.0.0.1）
3. SRS端口（可选，默认: 1935）
4. 应用名称（可选，默认: live）
5. 流名称（可选，默认: test）

### 示例

```batch
REM 推流到本地SRS服务器
push_rtsp_to_srs.bat rtsp://192.168.1.100:554/h264

REM 推流到局域网SRS服务器
push_rtsp_to_srs.bat rtsp://192.168.1.100:554/stream 192.168.1.200

REM 指定应用和流名称
push_rtsp_to_srs.bat rtsp://192.168.1.100:554/stream 192.168.1.200 1935 camera camera01
```

---

## 视频文件推流脚本使用方法

### 概述

视频文件推流脚本用于将本地视频文件（如MP4）推送到SRS服务器，支持循环播放和重新编码选项。

### Linux/Ubuntu/Mac Bash脚本使用方法

#### 基本用法

```bash
# 使用默认配置推流（默认文件: VIDEO/video/video2.mp4）
./push_video_to_srs.sh
```

#### 完整参数

```bash
./push_video_to_srs.sh \
    -v "VIDEO/video/video2.mp4" \
    -h "192.168.1.200" \
    -p 1935 \
    -a "live" \
    -s "test" \
    -f "/usr/bin/ffmpeg" \
    --no-loop \
    --re-encode
```

#### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `-v, --video` | 否 | VIDEO/video/video2.mp4 | 视频文件路径（相对于项目根目录或绝对路径） |
| `-h, --host` | 否 | 127.0.0.1 | SRS服务器IP地址 |
| `-p, --port` | 否 | 1935 | SRS服务器RTMP端口 |
| `-a, --app` | 否 | live | 应用名称 |
| `-s, --stream` | 否 | test | 流名称 |
| `-f, --ffmpeg` | 否 | ffmpeg | FFmpeg可执行文件路径 |
| `--no-loop` | 否 | - | 不循环播放（播放一次后退出） |
| `--re-encode` | 否 | - | 重新编码（兼容性更好，但CPU占用更高） |

#### 示例

```bash
# 使用默认配置推流（默认文件: VIDEO/video/video2.mp4）
./push_video_to_srs.sh

# 推流到指定服务器
./push_video_to_srs.sh -h "192.168.1.200"

# 推流到指定服务器和流名
./push_video_to_srs.sh -h "192.168.1.200" -s "camera01"

# 推流指定视频文件（相对路径）
./push_video_to_srs.sh -v "VIDEO/video/another_video.mp4"

# 推流指定视频文件（绝对路径）
./push_video_to_srs.sh -v "/path/to/video.mp4"

# 播放一次后退出（不循环）
./push_video_to_srs.sh --no-loop

# 使用重新编码模式（兼容性更好）
./push_video_to_srs.sh --re-encode

# 组合使用多个参数
./push_video_to_srs.sh -h "192.168.1.200" -s "camera01" -v "VIDEO/video/video2.mp4" --re-encode
```

### Windows PowerShell脚本使用方法

#### 基本用法

```powershell
# 使用默认配置推流（默认文件: VIDEO/video/video2.mp4）
.\push_video_to_srs.ps1
```

#### 完整参数

```powershell
.\push_video_to_srs.ps1 `
    -VideoFile "VIDEO/video/video2.mp4" `
    -SrsHost "192.168.1.200" `
    -SrsPort 1935 `
    -App "live" `
    -Stream "test" `
    -FfmpegPath "C:\ffmpeg\bin\ffmpeg.exe" `
    -NoLoop `
    -ReEncode
```

#### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `-VideoFile` | 否 | VIDEO/video/video2.mp4 | 视频文件路径（相对于项目根目录或绝对路径） |
| `-SrsHost` | 否 | 127.0.0.1 | SRS服务器IP地址 |
| `-SrsPort` | 否 | 1935 | SRS服务器RTMP端口 |
| `-App` | 否 | live | 应用名称 |
| `-Stream` | 否 | test | 流名称 |
| `-FfmpegPath` | 否 | ffmpeg | FFmpeg可执行文件路径 |
| `-NoLoop` | 否 | - | 不循环播放（播放一次后退出） |
| `-ReEncode` | 否 | - | 重新编码（兼容性更好，但CPU占用更高） |

#### 示例

```powershell
# 使用默认配置推流（默认文件: VIDEO/video/video2.mp4）
.\push_video_to_srs.ps1

# 推流到指定服务器
.\push_video_to_srs.ps1 -SrsHost "192.168.1.200"

# 推流到指定服务器和流名
.\push_video_to_srs.ps1 -SrsHost "192.168.1.200" -Stream "camera01"

# 推流指定视频文件（相对路径）
.\push_video_to_srs.ps1 -VideoFile "VIDEO/video/another_video.mp4"

# 推流指定视频文件（绝对路径）
.\push_video_to_srs.ps1 -VideoFile "D:\Videos\video.mp4"

# 播放一次后退出（不循环）
.\push_video_to_srs.ps1 -NoLoop

# 使用重新编码模式（兼容性更好）
.\push_video_to_srs.ps1 -ReEncode

# 组合使用多个参数
.\push_video_to_srs.ps1 -SrsHost "192.168.1.200" -Stream "camera01" -VideoFile "VIDEO/video/video2.mp4" -ReEncode
```

### 视频推流特性

1. **自动路径处理**：支持相对路径（相对于项目根目录）和绝对路径
2. **循环播放**：默认循环播放视频，可使用 `--no-loop` 或 `-NoLoop` 参数禁用
3. **编码模式**：
   - **Copy模式**（默认）：直接复制视频流，性能好，但需要编码格式兼容
   - **重新编码模式**：使用 `-ReEncode` 或 `--re-encode` 参数，兼容性更好，但CPU占用更高
4. **默认配置**：无需参数即可使用，默认推流 `VIDEO/video/video2.mp4` 到本地SRS服务器

### 视频推流常见问题

#### 1. 视频文件不存在

**问题**: 提示"视频文件不存在"

**解决方案**:
- 检查视频文件路径是否正确
- 确保使用相对路径时，文件位于项目根目录下
- 或使用绝对路径指定视频文件

#### 2. 视频格式不支持

**问题**: 推流失败，提示编码格式不兼容

**解决方案**:
- 使用 `--re-encode` 或 `-ReEncode` 参数启用重新编码模式
- 确保视频文件格式为常见格式（MP4、AVI、MOV等）
- 使用VLC等播放器测试视频文件是否可以正常播放

#### 3. 推流卡顿或延迟

**问题**: 推流过程中出现卡顿

**解决方案**:
- 检查网络连接是否稳定
- 检查SRS服务器性能
- 如果使用重新编码模式，可能需要降低编码质量或使用更快的预设

#### 4. 循环播放不工作

**问题**: 视频播放一次后停止

**解决方案**:
- 检查是否使用了 `--no-loop` 或 `-NoLoop` 参数
- 确保脚本版本支持循环播放功能
- 检查ffmpeg版本是否支持 `-stream_loop` 参数

## 推流地址格式

推流成功后，可以通过以下地址访问流：

- **RTMP播放**: `rtmp://<SRS_HOST>:<SRS_PORT>/<APP>/<STREAM>`
- **HTTP-FLV播放**: `http://<SRS_HOST>:8080/<APP>/<STREAM>.flv`
- **WebRTC播放**: `webrtc://<SRS_HOST>:8000/<APP>/<STREAM>`

## 常见问题

### 1. ffmpeg未找到

**问题**: 提示"无法找到ffmpeg"

**解决方案**:
- 确保ffmpeg已安装
- 将ffmpeg添加到系统PATH环境变量
- 或使用 `-FfmpegPath` 参数指定完整路径

### 2. 推流失败

**可能原因**:
- RTSP源地址无法访问
- SRS服务器未运行
- 网络连接问题
- RTSP流格式不支持（需要重新编码）

**解决方案**:
- 检查RTSP源是否可访问（使用VLC等播放器测试）
- 确认SRS服务器状态
- 检查防火墙设置
- 如果RTSP流格式不支持，可能需要修改ffmpeg参数进行转码

### 3. 需要重新编码

如果RTSP流格式与RTMP不兼容，可以修改脚本中的ffmpeg参数：

**Mac/Linux/Ubuntu**:
```bash
# 将 -c:v copy 改为 -c:v libx264
# 将 -c:a copy 改为 -c:a aac
```

**Windows PowerShell**:
```powershell
# 将 -c:v copy 改为 -c:v libx264
# 将 -c:a copy 改为 -c:a aac
```

### 4. RTSP连接不稳定

可以尝试：
- 使用TCP传输: `-rtsp_transport tcp`（已包含在脚本中）
- 添加重连逻辑: `-reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1`
- 增加超时时间: `-rtsp_transport tcp -timeout 5000000`

## 停止推流

按 `Ctrl+C` 停止推流。

## 注意事项

1. 确保RTSP源和SRS服务器在同一网络或网络可达
2. 检查防火墙是否允许相应端口通信
3. 推流会占用网络带宽，注意网络负载
4. 长时间推流建议使用后台服务或任务计划程序

