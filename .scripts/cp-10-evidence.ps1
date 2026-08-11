# CP-10 — Boot daemons evidence: restart video-server, harvest boot log markers
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (Test-Path (Join-Path $PSScriptRoot '..\DEVICE\iot-video')) {
    $root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
$logPath = Join-Path $root 'logs\cp-10-video-server.log'
$errPath = Join-Path $root 'logs\cp-10-video-server.err.log'
$jar = Join-Path $root 'DEVICE\iot-video\iot-video-biz\target\iot-video-biz.jar'
$envFile = 'F:\acme\VIDEO\.env'
$javaHome = 'F:\acme\.tools\jdk-21.0.2'

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $k = $matches[1].Trim(); $v = $matches[2].Trim().Trim('"')
            if ($k -in @('NACOS_PASSWORD','MINIO_SECRET_KEY','MINIO_ACCESS_KEY')) {
                Set-Item -Path "Env:$k" -Value $v
            }
        }
    }
}

$listen = Get-NetTCPConnection -LocalPort 48096 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listen) {
    Write-Host "Stopping existing video-server PID $($listen.OwningProcess)"
    Stop-Process -Id $listen.OwningProcess -Force
    Start-Sleep -Seconds 4
}

$env:JAVA_HOME = $javaHome
$env:PATH = "$javaHome\bin;$env:PATH"
Remove-Item $logPath,$errPath -ErrorAction SilentlyContinue

$proc = Start-Process -FilePath "$javaHome\bin\java.exe" `
    -ArgumentList @('-jar',$jar,'--spring.profiles.active=local') `
    -RedirectStandardOutput $logPath -RedirectStandardError $errPath -PassThru -WindowStyle Hidden
Write-Host "Started PID $($proc.Id)"

$deadline = (Get-Date).AddSeconds(150)
while ((Get-Date) -lt $deadline) {
    if (Test-Path $logPath) {
        $content = Get-Content $logPath -Raw -ErrorAction SilentlyContinue
        if ($content -match 'view-forward startup auto-resume' -and $content -match '抓拍任务调度器初始化成功') {
            Write-Host 'Boot markers found'
            break
        }
    }
    Start-Sleep -Seconds 4
}

if (-not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
    Write-Host "Stopped $($proc.Id)"
}

Write-Host "Log: $logPath ($( (Get-Item $logPath).Length ) bytes)"
rg 'view-forward startup|抓拍任务调度器初始化|Janitor 周期|startup 抓拍空间|startup 录像空间' $logPath -n
