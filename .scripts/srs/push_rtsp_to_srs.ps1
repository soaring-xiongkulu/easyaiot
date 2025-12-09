# Windows环境下使用ffmpeg将RTSP流推送到SRS服务器
# 使用方法: 
#   命名参数: .\push_rtsp_to_srs.ps1 -RtspUrl "rtsp://192.168.1.100:554/stream" -SrsHost "192.168.1.200"
#   位置参数: .\push_rtsp_to_srs.ps1 "rtsp://192.168.1.100:554/stream" "192.168.1.200"

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$RtspUrl,
    
    [Parameter(Mandatory=$false, Position=1)]
    [string]$SrsHost,
    
    [Parameter(Mandatory=$false)]
    [int]$SrsPort,
    
    [Parameter(Mandatory=$false)]
    [string]$App,
    
    [Parameter(Mandatory=$false)]
    [string]$Stream,
    
    [Parameter(Mandatory=$false)]
    [string]$FfmpegPath,
    
    [Parameter(Mandatory=$false)]
    [switch]$ReEncode
)

# 设置脚本文件编码为UTF-8（处理中文注释和字符串）
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
if ($PSVersionTable.PSVersion.Major -ge 6) {
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
}

# 验证必需参数
if ([string]::IsNullOrWhiteSpace($RtspUrl)) {
    Write-Host "错误: RTSP源地址参数不能为空" -ForegroundColor Red
    Write-Host "使用方法: .\push_rtsp_to_srs.ps1 -RtspUrl `"rtsp://...`" [-SrsHost `"IP`"] [-FfmpegPath `"路径`"]" -ForegroundColor Yellow
    exit 1
}

# 设置默认值
if ([string]::IsNullOrWhiteSpace($SrsHost)) { $SrsHost = "127.0.0.1" }
if (-not $SrsPort) { $SrsPort = 1935 }
if ([string]::IsNullOrWhiteSpace($App)) { $App = "live" }
if ([string]::IsNullOrWhiteSpace($Stream)) { $Stream = "test" }
if ([string]::IsNullOrWhiteSpace($FfmpegPath)) { $FfmpegPath = "ffmpeg" }

# 检查ffmpeg是否可用
try {
    $ffmpegVersion = & $FfmpegPath -version 2>&1 | Select-Object -First 1
    if ($LASTEXITCODE -ne 0) {
        throw "ffmpeg未找到或无法执行"
    }
    Write-Host "检测到ffmpeg: $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "错误: 无法找到ffmpeg，请确保ffmpeg已安装并添加到PATH环境变量中" -ForegroundColor Red
    Write-Host "或者使用 -FfmpegPath 参数指定ffmpeg的完整路径，例如: -FfmpegPath 'C:\ffmpeg\bin\ffmpeg.exe'" -ForegroundColor Yellow
    exit 1
}

# 构建RTMP推流地址
$RtmpUrl = "rtmp://${SrsHost}:${SrsPort}/${App}/${Stream}"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RTSP推流到SRS配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RTSP源地址: $RtspUrl" -ForegroundColor White
Write-Host "SRS服务器: ${SrsHost}:${SrsPort}" -ForegroundColor White
Write-Host "应用名称: $App" -ForegroundColor White
Write-Host "流名称: $Stream" -ForegroundColor White
Write-Host "RTMP推流地址: $RtmpUrl" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ffmpeg推流参数说明:
# -i: 输入源（RTSP流）
# -c:v copy: 视频编码器，使用copy避免重新编码（如果RTSP流是H.264）
# -c:a copy: 音频编码器，使用copy避免重新编码
# -f flv: 输出格式为FLV（RTMP协议要求）
# -rtsp_transport tcp: 使用TCP传输RTSP（更稳定，可选udp）
# -re: 按照原始帧率推流
# -stream_loop -1: 如果流断开则无限重试（可选）
# -loglevel info: 日志级别

Write-Host "开始推流..." -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止推流" -ForegroundColor Yellow
Write-Host ""

# 执行ffmpeg推流命令
# 使用cmd.exe来执行，避免PowerShell解析URL中的特殊字符（如&）
# 这样可以确保RTSP URL中的&等特殊字符被正确传递给ffmpeg

# 改进的FFmpeg参数：
# -loglevel verbose: 详细日志，便于调试
# -rtsp_transport tcp: 使用TCP传输RTSP（更稳定）
# -stimeout 5000000: RTSP超时设置（微秒），5秒
# -fflags nobuffer: 禁用缓冲，降低延迟
# -flags low_delay: 低延迟模式
# -strict experimental: 允许使用实验性编码器
# -c:v copy: 视频编码器，使用copy避免重新编码
# -c:a copy: 音频编码器，使用copy避免重新编码
# -f flv: 输出格式为FLV（RTMP协议要求）
# -re: 按照原始帧率推流
# -flvflags no_duration_filesize: FLV标志，避免写入文件大小和时长（适用于流媒体）

if ($ReEncode) {
    Write-Host "使用重新编码模式（兼容性更好，但CPU占用更高）" -ForegroundColor Yellow
    Write-Host "FFmpeg命令参数:" -ForegroundColor Cyan
    Write-Host "  -rtsp_transport tcp" -ForegroundColor Gray
    Write-Host "  -stimeout 5000000" -ForegroundColor Gray
    Write-Host "  -fflags nobuffer -flags low_delay" -ForegroundColor Gray
    Write-Host "  -c:v libx264 -preset ultrafast -tune zerolatency" -ForegroundColor Gray
    Write-Host "  -c:a aac -b:a 128k" -ForegroundColor Gray
    Write-Host "  -f flv -re" -ForegroundColor Gray
    Write-Host ""
    $ffmpegCmd = "`"$FfmpegPath`" -loglevel verbose -rtsp_transport tcp -stimeout 5000000 -fflags nobuffer -flags low_delay -i `"$RtspUrl`" -c:v libx264 -preset ultrafast -tune zerolatency -c:a aac -b:a 128k -f flv -re -flvflags no_duration_filesize `"$RtmpUrl`""
} else {
    Write-Host "使用copy模式（性能更好，但需要编码格式兼容）" -ForegroundColor Yellow
    Write-Host "FFmpeg命令参数:" -ForegroundColor Cyan
    Write-Host "  -rtsp_transport tcp" -ForegroundColor Gray
    Write-Host "  -stimeout 5000000" -ForegroundColor Gray
    Write-Host "  -fflags nobuffer -flags low_delay" -ForegroundColor Gray
    Write-Host "  -c:v copy -c:a copy" -ForegroundColor Gray
    Write-Host "  -f flv -re" -ForegroundColor Gray
    Write-Host ""
    $ffmpegCmd = "`"$FfmpegPath`" -loglevel verbose -rtsp_transport tcp -stimeout 5000000 -fflags nobuffer -flags low_delay -i `"$RtspUrl`" -c:v copy -c:a copy -f flv -re -flvflags no_duration_filesize `"$RtmpUrl`""
}

Write-Host "执行命令: $ffmpegCmd" -ForegroundColor DarkGray
Write-Host ""

# 使用cmd.exe执行，可以保持实时输出并正确处理特殊字符
cmd.exe /c $ffmpegCmd
$exitCode = $LASTEXITCODE

# 检查退出码
if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "推流失败，退出码: $exitCode" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. RTSP源地址无法访问或需要认证" -ForegroundColor Yellow
    Write-Host "  2. SRS服务器未运行或地址不正确" -ForegroundColor Yellow
    Write-Host "  3. 网络连接问题（防火墙、端口阻塞）" -ForegroundColor Yellow
    Write-Host "  4. RTSP流格式不支持copy模式（可能需要重新编码）" -ForegroundColor Yellow
    Write-Host "  5. RTSP流编码格式不兼容（H.265、G.711等）" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "故障排查建议:" -ForegroundColor Cyan
    Write-Host "  1. 检查RTSP源是否可访问: 使用VLC播放器测试RTSP地址" -ForegroundColor White
    Write-Host "  2. 检查SRS服务器状态: 访问 http://${SrsHost}:1985/api/v1/streams/" -ForegroundColor White
    Write-Host "  3. 检查网络连接: ping $SrsHost" -ForegroundColor White
    Write-Host "  4. 尝试使用重新编码模式: 添加 -ReEncode 参数" -ForegroundColor White
    Write-Host "     示例: .\push_rtsp_to_srs.ps1 `"$RtspUrl`" `"$SrsHost`" -FfmpegPath `"$FfmpegPath`" -ReEncode" -ForegroundColor Gray
    Write-Host "  5. 查看FFmpeg详细日志（已启用verbose模式）" -ForegroundColor White
    Write-Host "  6. 运行诊断脚本: .\diagnose_rtsp_push.ps1 `"$RtspUrl`" `"$SrsHost`" -FfmpegPath `"$FfmpegPath`"" -ForegroundColor White
    Write-Host ""
    exit $exitCode
} else {
    Write-Host ""
    Write-Host "推流已停止" -ForegroundColor Green
}
