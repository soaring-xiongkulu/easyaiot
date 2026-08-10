# CLOSE-S3: wall-clock observe loop for gateway + video-server (>=15 min).
param(
    [int]$DurationMinutes = 16,
    [int]$IntervalSeconds = 45,
    [string]$LogPath = "docs/video-java/gates/OBSERVE_LOG.md"
)

$ErrorActionPreference = "Continue"
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $repoRoot

$gatewayHealth = "http://127.0.0.1:48080/actuator/health"
$gatewayCamera = "http://127.0.0.1:48080/admin-api/video/camera/list?pageNo=1&pageSize=1"
$directHealth = "http://127.0.0.1:48096/actuator/health"
$directCamera = "http://127.0.0.1:48096/video/camera/list?pageNo=1&pageSize=1"

$start = Get-Date
$end = $start.AddMinutes($DurationMinutes)
$ok = 0
$fail = 0
$lines = @()
$lines += "# OBSERVE_LOG — CLOSE-S3 gateway + video-server"
$lines += ""
$lines += "**Started:** $($start.ToString('yyyy-MM-dd HH:mm:ss'))"
$lines += "**Target end:** $($end.ToString('yyyy-MM-dd HH:mm:ss')) ($DurationMinutes min)"
$lines += "**Interval:** ${IntervalSeconds}s"
$lines += ""
$lines += "| # | Timestamp | Gateway health | Gateway camera | Direct health | Direct camera | Result |"
$lines += "|---|-----------|----------------|----------------|---------------|---------------|--------|"

function Test-Url {
    param([string]$Url, [hashtable]$Headers = @{})
    try {
        $params = @{ Uri = $Url; TimeoutSec = 8; UseBasicParsing = $true }
        if ($Headers.Count -gt 0) { $params.Headers = $Headers }
        $r = Invoke-WebRequest @params
        return @{ Code = [int]$r.StatusCode; Ok = ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) }
    }
    catch {
        $code = 0
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode.value__ }
        return @{ Code = $code; Ok = $false }
    }
}

$n = 0
while ((Get-Date) -lt $end) {
    $n++
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $gh = Test-Url $gatewayHealth
    $gc = Test-Url $gatewayCamera
    $dh = Test-Url $directHealth
    $dc = Test-Url $directCamera
    $pass = $gh.Ok -and $gc.Ok -and $dh.Ok -and $dc.Ok
    if ($pass) { $ok++ } else { $fail++ }
    $result = if ($pass) { "OK" } else { "FAIL" }
    $lines += "| $n | $ts | $($gh.Code) | $($gc.Code) | $($dh.Code) | $($dc.Code) | $result |"
    Write-Host "[$ts] poll $n $result (ok=$ok fail=$fail)"
    if ((Get-Date) -lt $end) { Start-Sleep -Seconds $IntervalSeconds }
}

$finished = Get-Date
$elapsed = $finished - $start
$verdict = if ($fail -eq 0) { "PASS" } else { "FAIL" }
$lines += ""
$lines += "**Finished:** $($finished.ToString('yyyy-MM-dd HH:mm:ss'))"
$lines += "**Elapsed:** $([math]::Floor($elapsed.TotalMinutes))m $($elapsed.Seconds)s"
$lines += "**Polls:** OK=$ok FAIL=$fail"
$lines += "**Verdict:** $verdict"

$logDir = Split-Path $LogPath -Parent
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$lines | Set-Content -Path $LogPath -Encoding UTF8
Write-Host "Wrote $LogPath verdict=$verdict"
exit $(if ($verdict -eq "PASS") { 0 } else { 1 })
