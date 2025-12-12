# RTSP推流诊断脚本
# 用于诊断RTSP推流到SRS的问题

param(
    [Parameter(Mandatory=$true)]
    [string]$RtspUrl,
    
    [Parameter(Mandatory=$false)]
    [string]$SrsHost = "127.0.0.1",
    
    [Parameter(Mandatory=$false)]
    [int]$SrsPort = 1935,
    
    [Parameter(Mandatory=$false)]
    [string]$FfmpegPath = "ffmpeg"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RTSP推流诊断工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查FFmpeg
Write-Host "[1/5] 检查FFmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = & $FfmpegPath -version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ FFmpeg版本: $ffmpegVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ FFmpeg未找到" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. 测试RTSP源连接
Write-Host "[2/5] 测试RTSP源连接..." -ForegroundColor Yellow
Write-Host "  正在尝试连接RTSP源（5秒超时）..." -ForegroundColor Gray
$rtspTest = & $FfmpegPath -rtsp_transport tcp -stimeout 5000000 -i "$RtspUrl" -t 1 -f null - 2>&1
if ($LASTEXITCODE -eq 0 -or $rtspTest -match "Stream.*Video|Stream.*Audio") {
    Write-Host "  ✓ RTSP源可访问" -ForegroundColor Green
    # 提取流信息
    if ($rtspTest -match "Stream #0:(\d+):Video:([^\s]+)") {
        Write-Host "    视频编码: $($matches[2])" -ForegroundColor Gray
    }
    if ($rtspTest -match "Stream #0:(\d+):Audio:([^\s]+)") {
        Write-Host "    音频编码: $($matches[2])" -ForegroundColor Gray
    }
} else {
    Write-Host "  ✗ RTSP源无法访问或连接超时" -ForegroundColor Red
    Write-Host "    错误信息:" -ForegroundColor Yellow
    $rtspTest | Select-Object -Last 5 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
}
Write-Host ""

# 3. 检查SRS服务器连接
Write-Host "[3/5] 检查SRS服务器连接..." -ForegroundColor Yellow
try {
    $srsApiUrl = "http://${SrsHost}:1985/api/v1/streams/"
    $response = Invoke-WebRequest -Uri $srsApiUrl -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ SRS服务器可访问" -ForegroundColor Green
        $streams = $response.Content | ConvertFrom-Json
        Write-Host "    当前流数量: $($streams.streams.Count)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ SRS服务器响应异常: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ 无法连接到SRS服务器" -ForegroundColor Red
    Write-Host "    请检查:" -ForegroundColor Yellow
    Write-Host "      - SRS服务器是否运行" -ForegroundColor Gray
    Write-Host "      - 地址是否正确: $SrsHost:$SrsPort" -ForegroundColor Gray
    Write-Host "      - 防火墙是否允许连接" -ForegroundColor Gray
}
Write-Host ""

# 4. 测试网络连接
Write-Host "[4/5] 测试网络连接..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName $SrsHost -Count 2 -Quiet
    if ($ping) {
        Write-Host "  ✓ 可以ping通SRS服务器" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 无法ping通SRS服务器" -ForegroundColor Red
    }
} catch {
    Write-Host "  ⚠ 无法测试ping（可能需要管理员权限）" -ForegroundColor Yellow
}
Write-Host ""

# 5. 测试RTMP推流（短时间）
Write-Host "[5/5] 测试RTMP推流（5秒）..." -ForegroundColor Yellow
$testRtmpUrl = "rtmp://${SrsHost}:${SrsPort}/live/diagnose_test"
Write-Host "  推流地址: $testRtmpUrl" -ForegroundColor Gray
Write-Host "  正在测试推流..." -ForegroundColor Gray

$testCmd = "`"$FfmpegPath`" -loglevel error -rtsp_transport tcp -stimeout 5000000 -i `"$RtspUrl`" -c:v copy -c:a copy -f flv -t 5 `"$testRtmpUrl`" 2>&1"
$testOutput = cmd.exe /c $testCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ RTMP推流测试成功" -ForegroundColor Green
} else {
    Write-Host "  ✗ RTMP推流测试失败" -ForegroundColor Red
    Write-Host "    错误信息:" -ForegroundColor Yellow
    $testOutput | Select-Object -Last 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
    
    Write-Host ""
    Write-Host "  尝试使用重新编码模式..." -ForegroundColor Yellow
    $testCmd2 = "`"$FfmpegPath`" -loglevel error -rtsp_transport tcp -stimeout 5000000 -i `"$RtspUrl`" -c:v libx264 -preset ultrafast -tune zerolatency -c:a aac -f flv -t 5 `"$testRtmpUrl`" 2>&1"
    $testOutput2 = cmd.exe /c $testCmd2
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 重新编码模式推流成功（建议使用此模式）" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 重新编码模式也失败" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "诊断完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan






