# Windows环境下使用ffmpeg将RTSP流推送到SRS服务器
# 使用方法: 
#   命名参数: .\push_rtsp_to_srs.ps1 -RtspUrl "rtsp://192.168.1.100:554/stream" -SrsHost "192.168.1.200"
#   位置参数: .\push_rtsp_to_srs.ps1 "rtsp://192.168.1.100:554/stream" "192.168.1.200"

# 设置脚本文件编码为UTF-8（处理中文注释和字符串）
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
if ($PSVersionTable.PSVersion.Major -ge 6) {
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
}

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
    [string]$FfmpegPath
)

# 设置默认值
if (-not $SrsHost) { $SrsHost = "127.0.0.1" }
if (-not $SrsPort) { $SrsPort = 1935 }
if (-not $App) { $App = "live" }
if (-not $Stream) { $Stream = "test" }
if (-not $FfmpegPath) { $FfmpegPath = "ffmpeg" }

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
& $FfmpegPath `
    -rtsp_transport tcp `
    -i "$RtspUrl" `
    -c:v copy `
    -c:a copy `
    -f flv `
    -re `
    "$RtmpUrl"

# 检查退出码
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "推流失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. RTSP源地址无法访问" -ForegroundColor Yellow
    Write-Host "  2. SRS服务器未运行或地址不正确" -ForegroundColor Yellow
    Write-Host "  3. 网络连接问题" -ForegroundColor Yellow
    Write-Host "  4. RTSP流格式不支持（可能需要重新编码）" -ForegroundColor Yellow
    exit $LASTEXITCODE
} else {
    Write-Host ""
    Write-Host "推流已停止" -ForegroundColor Green
}
