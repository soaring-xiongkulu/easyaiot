# RTSP推流到SRS故障排查指南

## 问题分析

根据您提供的SRS日志，主要问题包括：

### 1. 流立即断开问题

**现象**：
```
[2025-12-09 06:59:48.350][INFO][1][tn1b9u97] cleanup when unpublish
[2025-12-09 06:59:48.350][WARN][1][tn1b9u97][4] client disconnect peer. ret=1007
```

**原因分析**：
- 错误码 `1007` 表示连接被异常关闭
- 流在连接后立即断开，说明FFmpeg推流过程中遇到了问题
- 可能的原因：
  1. RTSP源无法正常读取（网络问题、认证失败、格式不支持）
  2. 编码格式不兼容（使用 `-c:v copy -c:a copy` 时，如果RTSP流的编码格式不是H.264/AAC，会导致失败）
  3. FFmpeg在推流时遇到错误，但没有正确输出错误信息

### 2. 流名称不正确问题

**现象**：
- 期望流名称：`test`
- 实际流名称：`liveStream_BD0BA26PAG5394F_0_1`

**原因分析**：
- 这通常是因为FFmpeg在推流时遇到了问题，导致流名称没有正确传递
- 或者SRS在接收到不完整的流时自动生成了流名称
- 当流立即断开时，SRS可能无法正确识别流名称

## 解决方案

### 方案1：使用重新编码模式（推荐）

如果copy模式失败，尝试使用重新编码模式：

```powershell
.\push_rtsp_to_srs.ps1 "rtsp://admin:Qaz123456@192.168.0.186:1953/cam/realmonitor?channel=1&subtype=0" "1.92.67.87" -FfmpegPath "C:\Users\admin\Downloads\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe" -ReEncode
```

**优点**：
- 兼容性更好，支持各种编码格式
- 可以处理H.265、G.711等不兼容的编码格式

**缺点**：
- CPU占用更高
- 可能有轻微延迟

### 方案2：运行诊断脚本

使用诊断脚本检查各个环节：

```powershell
.\diagnose_rtsp_push.ps1 "rtsp://admin:Qaz123456@192.168.0.186:1953/cam/realmonitor?channel=1&subtype=0" "1.92.67.87" -FfmpegPath "C:\Users\admin\Downloads\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
```

诊断脚本会检查：
1. FFmpeg是否可用
2. RTSP源是否可访问
3. SRS服务器是否可访问
4. 网络连接是否正常
5. RTMP推流是否成功

### 方案3：手动测试RTSP源

使用VLC播放器测试RTSP源是否正常：

1. 打开VLC播放器
2. 媒体 → 打开网络串流
3. 输入RTSP地址：`rtsp://admin:Qaz123456@192.168.0.186:1953/cam/realmonitor?channel=1&subtype=0`
4. 如果能正常播放，说明RTSP源正常

### 方案4：检查FFmpeg详细日志

脚本已启用 `-loglevel verbose`，查看FFmpeg的详细输出，查找错误信息：

- 如果看到 `Connection refused`：SRS服务器未运行或地址不正确
- 如果看到 `Unauthorized`：RTSP认证失败
- 如果看到 `Invalid data found`：RTSP流格式不支持
- 如果看到 `Codec not found`：编码格式不兼容，需要使用重新编码模式

### 方案5：检查SRS服务器状态

访问SRS API检查服务器状态：

```
http://1.92.67.87:1985/api/v1/streams/
```

如果无法访问，说明：
- SRS服务器未运行
- 防火墙阻塞了1985端口
- 地址不正确

## 常见问题

### Q1: 为什么流名称不对？

**A**: 当FFmpeg推流失败时，SRS可能无法正确识别流名称，会自动生成一个流名称。解决方法是确保推流成功。

### Q2: 为什么流立即断开？

**A**: 可能的原因：
1. RTSP源无法正常读取
2. 编码格式不兼容（需要使用 `-ReEncode` 参数）
3. 网络连接问题
4. SRS服务器配置问题

### Q3: 如何判断是RTSP源问题还是SRS问题？

**A**: 
- 如果VLC可以播放RTSP流，说明RTSP源正常
- 如果SRS API可以访问，说明SRS服务器正常
- 使用诊断脚本可以快速定位问题

### Q4: copy模式和重新编码模式有什么区别？

**A**:
- **copy模式**：直接复制编码数据，不重新编码，性能好但需要编码格式兼容（H.264视频 + AAC音频）
- **重新编码模式**：重新编码为H.264+AAC，兼容性好但CPU占用高

### Q5: 如何查看FFmpeg的详细错误信息？

**A**: 脚本已启用 `-loglevel verbose`，所有错误信息都会输出到控制台。如果看不到错误信息，可能是：
- FFmpeg输出被重定向
- 错误发生在连接阶段，FFmpeg还没有输出

## 改进的脚本功能

最新版本的脚本包含以下改进：

1. **详细的日志输出**：使用 `-loglevel verbose` 显示详细日志
2. **超时设置**：`-stimeout 5000000` 设置RTSP超时为5秒
3. **低延迟模式**：`-fflags nobuffer -flags low_delay` 降低延迟
4. **重新编码选项**：`-ReEncode` 参数支持重新编码模式
5. **更好的错误提示**：提供详细的故障排查建议

## 使用示例

### 基本用法（copy模式）
```powershell
.\push_rtsp_to_srs.ps1 "rtsp://admin:Qaz123456@192.168.0.186:1953/cam/realmonitor?channel=1&subtype=0" "1.92.67.87" -FfmpegPath "C:\Users\admin\Downloads\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
```

### 重新编码模式
```powershell
.\push_rtsp_to_srs.ps1 "rtsp://admin:Qaz123456@192.168.0.186:1953/cam/realmonitor?channel=1&subtype=0" "1.92.67.87" -FfmpegPath "C:\Users\admin\Downloads\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe" -ReEncode
```

### 指定应用和流名称
```powershell
.\push_rtsp_to_srs.ps1 "rtsp://admin:Qaz123456@192.168.0.186:1953/cam/realmonitor?channel=1&subtype=0" "1.92.67.87" -App "live" -Stream "camera1" -FfmpegPath "C:\Users\admin\Downloads\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"
```

## 联系支持

如果以上方法都无法解决问题，请提供：
1. FFmpeg的完整输出日志
2. SRS服务器的完整日志
3. 诊断脚本的输出结果
4. RTSP源的详细信息（编码格式、分辨率等）




