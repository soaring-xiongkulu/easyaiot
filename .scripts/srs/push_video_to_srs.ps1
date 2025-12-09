# Windows环境下使用ffmpeg将本地视频文件推送到SRS服务器
# 使用方法: 
#   默认执行: .\push_video_to_srs.ps1
#   命名参数: .\push_video_to_srs.ps1 -SrsHost "192.168.1.200" -Stream "camera01"
#   位置参数: .\push_video_to_srs.ps1 "192.168.1.200" "camera01"

param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$SrsHost,
    
    [Parameter(Mandatory=$false, Position=1)]
    [string]$Stream,
    
    [Parameter(Mandatory=$false)]
    [int]$SrsPort,
    
    [Parameter(Mandatory=$false)]
    [string]$App,
    
    [Parameter(Mandatory=$false)]
    [string]$VideoFile,
    
    [Parameter(Mandatory=$false)]
    [string]$FfmpegPath,
    
    [Parameter(Mandatory=$false)]
    [switch]$NoLoop,
    
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

# 获取脚本所在目录的绝对路径
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 设置默认值
if ([string]::IsNullOrWhiteSpace($SrsHost)) { $SrsHost = "127.0.0.1" }
if (-not $SrsPort) { $SrsPort = 1935 }
if ([string]::IsNullOrWhiteSpace($App)) { $App = "live" }
if ([string]::IsNullOrWhiteSpace($Stream)) { $Stream = "test" }
if ([string]::IsNullOrWhiteSpace($FfmpegPath)) { $FfmpegPath = "ffmpeg" }

# 设置默认视频文件路径（在脚本同级目录查找）
if ([string]::IsNullOrWhiteSpace($VideoFile)) {
    # 在脚本同级目录查找视频文件
    $VideoExtensions = @("*.mp4", "*.avi", "*.mov", "*.mkv", "*.flv", "*.wmv", "*.webm", "*.m4v")
    $FoundVideo = $null
    
    foreach ($ext in $VideoExtensions) {
        $videos = Get-ChildItem -Path $ScriptDir -Filter $ext -File -ErrorAction SilentlyContinue
        if ($videos.Count -gt 0) {
            $FoundVideo = $videos[0].FullName
            break
        }
    }
    
    if ($null -eq $FoundVideo) {
        Write-Host "错误: 在脚本同级目录未找到视频文件" -ForegroundColor Red
        Write-Host "脚本目录: $ScriptDir" -ForegroundColor Yellow
        Write-Host "支持的视频格式: mp4, avi, mov, mkv, flv, wmv, webm, m4v" -ForegroundColor Yellow
        Write-Host "请将视频文件放在脚本同级目录，或使用 -VideoFile 参数指定视频文件路径" -ForegroundColor Yellow
        exit 1
    }
    
    $VideoFile = $FoundVideo
} else {
    # 如果用户提供的路径是相对路径，则相对于脚本目录
    if (-not [System.IO.Path]::IsPathRooted($VideoFile)) {
        $VideoFile = Join-Path $ScriptDir $VideoFile
    }
}

# 检查视频文件是否存在
if (-not (Test-Path $VideoFile -PathType Leaf)) {
    Write-Host "错误: 视频文件不存在: $VideoFile" -ForegroundColor Red
    Write-Host "请检查文件路径是否正确，或使用 -VideoFile 参数指定视频文件路径" -ForegroundColor Yellow
    exit 1
}

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

# 显示视频文件路径（如果是脚本目录下的文件，显示相对路径）
$VideoFileDisplay = $VideoFile
if ($VideoFile.StartsWith($ScriptDir)) {
    $VideoFileDisplay = $VideoFile.Substring($ScriptDir.Length + 1)
    if ([string]::IsNullOrWhiteSpace($VideoFileDisplay)) {
        $VideoFileDisplay = Split-Path -Leaf $VideoFile
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "视频文件推流到SRS配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "视频文件: $VideoFileDisplay" -ForegroundColor White
Write-Host "SRS服务器: ${SrsHost}:${SrsPort}" -ForegroundColor White
Write-Host "应用名称: $App" -ForegroundColor White
Write-Host "流名称: $Stream" -ForegroundColor White
Write-Host "RTMP推流地址: $RtmpUrl" -ForegroundColor Green
if (-not $NoLoop) {
    Write-Host "循环播放: 是" -ForegroundColor White
} else {
    Write-Host "循环播放: 否" -ForegroundColor White
}
if ($ReEncode) {
    Write-Host "编码模式: 重新编码" -ForegroundColor White
} else {
    Write-Host "编码模式: 复制（copy）" -ForegroundColor White
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ffmpeg推流参数说明:
# -i: 输入源（视频文件）
# -stream_loop -1: 无限循环播放（如果启用）
# -c:v copy: 视频编码器，使用copy避免重新编码（如果视频是H.264）
# -c:a copy: 音频编码器，使用copy避免重新编码
# -f flv: 输出格式为FLV（RTMP协议要求）
# -re: 按照原始帧率推流
# -fflags nobuffer: 禁用缓冲，降低延迟
# -flags low_delay: 低延迟模式
# -flvflags no_duration_filesize: FLV标志，避免写入文件大小和时长（适用于流媒体）

Write-Host "开始推流..." -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止推流" -ForegroundColor Yellow
Write-Host ""

# 构建ffmpeg命令字符串
$ffmpegCmd = "`"$FfmpegPath`" -loglevel info"

# 添加循环播放参数
if (-not $NoLoop) {
    $ffmpegCmd += " -stream_loop -1"
}

# 添加输入文件
$ffmpegCmd += " -i `"$VideoFile`""

# 添加编码参数
if ($ReEncode) {
    Write-Host "使用重新编码模式（兼容性更好，但CPU占用更高）" -ForegroundColor Yellow
    Write-Host "FFmpeg命令参数:" -ForegroundColor Cyan
    Write-Host "  -c:v libx264 -preset ultrafast -tune zerolatency" -ForegroundColor Gray
    Write-Host "  -c:a aac -b:a 128k" -ForegroundColor Gray
    Write-Host "  -f flv -re -fflags nobuffer -flags low_delay" -ForegroundColor Gray
    Write-Host ""
    $ffmpegCmd += " -c:v libx264 -preset ultrafast -tune zerolatency -c:a aac -b:a 128k"
} else {
    Write-Host "使用copy模式（性能更好，但需要编码格式兼容）" -ForegroundColor Yellow
    Write-Host "FFmpeg命令参数:" -ForegroundColor Cyan
    Write-Host "  -c:v copy -c:a copy" -ForegroundColor Gray
    Write-Host "  -f flv -re -fflags nobuffer -flags low_delay" -ForegroundColor Gray
    Write-Host ""
    $ffmpegCmd += " -c:v copy -c:a copy"
}

# 添加输出参数
$ffmpegCmd += " -f flv -re -fflags nobuffer -flags low_delay -flvflags no_duration_filesize `"$RtmpUrl`""

# 显示执行的命令（用于调试）
Write-Host "执行命令: $ffmpegCmd" -ForegroundColor DarkGray
Write-Host ""

# 执行ffmpeg推流命令
# 使用cmd.exe来执行，避免PowerShell解析URL中的特殊字符（如&）
cmd.exe /c $ffmpegCmd
$exitCode = $LASTEXITCODE

# 检查退出码
if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "推流失败，退出码: $exitCode" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "  1. 视频文件格式不支持或已损坏" -ForegroundColor Yellow
    Write-Host "  2. SRS服务器未运行或地址不正确" -ForegroundColor Yellow
    Write-Host "  3. 网络连接问题（防火墙、端口阻塞）" -ForegroundColor Yellow
    Write-Host "  4. 视频编码格式不兼容（H.265、G.711等，可能需要重新编码）" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "故障排查建议:" -ForegroundColor Cyan
    Write-Host "  1. 检查视频文件是否可播放: 使用VLC或其他播放器测试" -ForegroundColor White
    Write-Host "  2. 检查SRS服务器状态: 访问 http://${SrsHost}:1985/api/v1/streams/" -ForegroundColor White
    Write-Host "  3. 检查网络连接: ping $SrsHost" -ForegroundColor White
    Write-Host "  4. 尝试使用重新编码模式: 添加 -ReEncode 参数" -ForegroundColor White
    Write-Host "     示例: .\push_video_to_srs.ps1 -SrsHost `"$SrsHost`" -ReEncode" -ForegroundColor Gray
    Write-Host "  5. 查看FFmpeg详细日志（已启用info模式）" -ForegroundColor White
    Write-Host ""
    exit $exitCode
} else {
    Write-Host ""
    Write-Host "推流已停止" -ForegroundColor Green
}
