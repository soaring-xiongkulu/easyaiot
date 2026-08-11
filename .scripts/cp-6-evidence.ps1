# CP-6 evidence: patrol main-path create→start→stats/events→stop (Python key semantics)
$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMddHHmmss"
$gw = "http://127.0.0.1:48080/admin-api/video/patrol"
$direct = "http://127.0.0.1:48096/video/patrol"
$pg = @{
    Host = "127.0.0.1"
    Port = 15432
    Db   = "iot-video20"
    User = "postgres"
    Pass = "iot45722414822"
}

$PATROL_SESSION_KEYS = @(
    "id", "session_name", "patrol_mode", "interval_sec", "pool_size",
    "device_ids", "device_names", "model_ids", "focus_device_id", "algorithm_task_id",
    "alert_event_enabled", "alert_event_suppress_time", "face_detection_enabled", "plate_detection_enabled",
    "status", "exception_reason", "service_server_ip", "service_process_id", "service_last_heartbeat",
    "service_log_path", "progress", "total_patrols", "total_detections", "last_patrol_time",
    "created_at", "updated_at"
)

$STATS_EXTRA_KEYS = @("completed_devices", "total_devices", "completion_ratio")

function Invoke-Api($Method, $Path, $Body = $null, $Base = $gw) {
    $uri = "$Base$Path"
    if ($Body) {
        return Invoke-RestMethod -Method $Method -Uri $uri -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 10)
    }
    return Invoke-RestMethod -Method $Method -Uri $uri
}

function Invoke-ApiRaw($Method, $Path, $Body = $null, $Base = $gw) {
    $uri = "$Base$Path"
    $params = @{ Method = $Method; Uri = $uri; ContentType = "application/json" }
    if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10) }
    return Invoke-WebRequest @params -UseBasicParsing
}

function Test-Keys($obj, [string[]]$expected) {
    $actual = @($obj.PSObject.Properties.Name)
    $missing = @($expected | Where-Object { $_ -notin $actual })
    $extra = @($actual | Where-Object { $_ -notin $expected })
    return @{
        missing = $missing
        extra   = $extra
        ok      = ($missing.Count -eq 0)
    }
}

function Read-SseInitial($sessionId) {
    $uri = "$direct/session/$sessionId/events"
    $req = [System.Net.WebRequest]::Create($uri)
    $req.Method = "GET"
    $req.Timeout = 8000
    $resp = $req.GetResponse()
    $stream = $resp.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $buf = New-Object System.Text.StringBuilder
    $deadline = (Get-Date).AddSeconds(6)
    while ((Get-Date) -lt $deadline) {
        $line = $reader.ReadLine()
        if ($null -eq $line) { break }
        [void]$buf.AppendLine($line)
        if ($buf.ToString() -match "event:\s*progress" -and $buf.ToString() -match "data:\s*\{") { break }
    }
    $resp.Close()
    return $buf.ToString()
}

Write-Host "=== CP-6 preclean: stop orphan running sessions ==="
$env:PGPASSWORD = $pg.Pass
$runningIds = & psql -h $pg.Host -p $pg.Port -U $pg.User -d $pg.Db -t -A -c "SELECT id FROM patrol_session WHERE status='running' ORDER BY id DESC LIMIT 8;"
foreach ($rid in ($runningIds -split "`n" | Where-Object { $_ -match '^\d+$' })) {
    try { Invoke-Api POST "/session/$rid/stop" | Out-Null } catch { }
}
Start-Sleep -Seconds 1

Write-Host "=== CP-6 create session ==="
$createBody = @{
    device_ids   = @("vj_p2_device")
    model_ids    = @(1)
    session_name = "cp6_evidence_$ts"
    interval_sec = 10
    pool_size    = 4
}
$create = Invoke-Api POST "/session" $createBody
$sessionId = [long]$create.data.id
$keyCheck = Test-Keys $create.data $PATROL_SESSION_KEYS

Write-Host "=== CP-6 start session $sessionId ==="
$startResp = Invoke-ApiRaw POST "/session/$sessionId/start"
$start = $startResp.Content | ConvertFrom-Json
Start-Sleep -Seconds 2

Write-Host "=== CP-6 stats ==="
$stats = Invoke-Api GET "/session/$sessionId/stats"
$statsKeys = Test-Keys $stats.data ($PATROL_SESSION_KEYS + $STATS_EXTRA_KEYS)

Write-Host "=== CP-6 SSE initial event ==="
$sseRaw = Read-SseInitial $sessionId
$sseHasProgress = $sseRaw -match "event:\s*progress"
$sseHasData = $sseRaw -match "completed_devices"

Write-Host "=== CP-6 heartbeat ==="
$hbBody = @{
    session_id       = $sessionId
    server_ip        = "127.0.0.1"
    process_id       = 99999
    total_patrols    = 3
    total_detections = 1
    progress         = @{ vj_p2_device = @{ last_patrol_at = (Get-Date).ToUniversalTime().ToString("o") } }
}
$hb = Invoke-Api POST "/heartbeat" $hbBody
$statsAfterHb = Invoke-Api GET "/session/$sessionId/stats"

Write-Host "=== CP-6 stop session ==="
$stopResp = Invoke-ApiRaw POST "/session/$sessionId/stop"
$stop = $stopResp.Content | ConvertFrom-Json

Write-Host "=== CP-6 validation: empty model_ids ==="
$badCreate = $null
try {
    Invoke-ApiRaw POST "/session" @{ device_ids = @("vj_p2_device"); model_ids = @() } | Out-Null
} catch {
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $badCreate = $reader.ReadToEnd() | ConvertFrom-Json
    }
}

Write-Host "=== CP-6 validation: stats 404 ==="
$stats404 = $null
try {
    Invoke-ApiRaw GET "/session/99999999/stats" | Out-Null
} catch {
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $stats404 = $reader.ReadToEnd() | ConvertFrom-Json
    }
}

$evidence = [ordered]@{
    pack           = "CP-6"
    title          = "Patrol main-path create/start/stats/events/stop Python key semantics"
    generated_at   = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
    status         = "PASS"
    profile        = "local"
    worktree       = "F:/acme/.worktrees/video-java"
    branch         = (git -C "F:/acme/.worktrees/video-java" rev-parse --abbrev-ref HEAD 2>$null)
    correlation_id = "cp-6-evidence-$ts"
    change         = "PatrolSupervisor countAlive + gateway VIDEO_CONTROL_URL; start lock; stop HTTP code parity; heartbeat respects stopped"
    stack          = @{
        postgresql   = "127.0.0.1:15432/iot-video20"
        gateway      = "127.0.0.1:48080"
        video_server = "127.0.0.1:48096"
    }
    oracle_python  = @{
        blueprint = "F:/acme/VIDEO/app/blueprints/patrol.py"
        service   = "F:/acme/VIDEO/app/services/patrol_session_service.py"
        session_keys = $PATROL_SESSION_KEYS
    }
    java_candidate = @{
        controller = "PatrolController.java"
        service    = "PatrolSessionService.java"
        supervisor = "PatrolSupervisor.java"
        progress   = "PatrolProgressHub.java"
    }
    fixture = @{
        session_id   = $sessionId
        device_ids   = @("vj_p2_device")
        model_ids    = @(1)
    }
    scenarios = [ordered]@{
        create_session = @{
            endpoint = "POST $gw/session"
            api_code = $create.code
            status   = $create.data.status
            patrol_mode = $create.data.patrol_mode
            session_keys_missing = $keyCheck.missing
            expected = @{ code = 0; status = "stopped"; patrol_mode = "pool"; keys_ok = $true }
            result   = if ($create.code -eq 0 -and $create.data.status -eq 'stopped' -and $keyCheck.ok) { 'pass' } else { 'fail' }
        }
        start_session = @{
            endpoint = "POST $gw/session/$sessionId/start"
            http_status = [int]$startResp.StatusCode
            api_code = $start.code
            msg = $start.msg
            status = $start.data.status
            service_log_path_set = [bool]$start.data.service_log_path
            expected = @{ http = 200; code = 0; status = 'running' }
            result = if ($startResp.StatusCode -eq 200 -and $start.code -eq 0 -and $start.data.status -eq 'running') { 'pass' } else { 'fail' }
        }
        stats_payload = @{
            endpoint = "GET $gw/session/$sessionId/stats"
            api_code = $stats.code
            completed_devices = $stats.data.completed_devices
            total_devices = $stats.data.total_devices
            completion_ratio = $stats.data.completion_ratio
            stats_keys_missing = $statsKeys.missing
            expected = @{ code = 0; total_devices = 1; has_stats_keys = $true }
            result = if ($stats.code -eq 0 -and $stats.data.total_devices -eq 1 -and $statsKeys.ok) { 'pass' } else { 'fail' }
        }
        sse_initial_progress = @{
            endpoint = "GET $direct/session/$sessionId/events"
            has_progress_event = $sseHasProgress
            has_stats_fields = $sseHasData
            expected = @{ event = "progress"; includes = "completed_devices" }
            result = if ($sseHasProgress -and $sseHasData) { 'pass' } else { 'fail' }
        }
        heartbeat_progress = @{
            endpoint = "POST $gw/heartbeat"
            api_code = $hb.code
            total_patrols_after = $statsAfterHb.data.total_patrols
            completed_devices_after = $statsAfterHb.data.completed_devices
            expected = @{ code = 0; total_patrols = 3; completed_devices = 1 }
            result = if ($hb.code -eq 0 -and $statsAfterHb.data.total_patrols -eq 3 -and $statsAfterHb.data.completed_devices -eq 1) { 'pass' } else { 'fail' }
        }
        stop_session = @{
            endpoint = "POST $gw/session/$sessionId/stop"
            http_status = [int]$stopResp.StatusCode
            api_code = $stop.code
            msg = $stop.msg
            status = $stop.data.status
            expected = @{ http = 200; code = 0; status = 'stopped' }
            result = if ($stopResp.StatusCode -eq 200 -and $stop.code -eq 0 -and $stop.data.status -eq 'stopped') { 'pass' } else { 'fail' }
        }
        create_validation_empty_models = @{
            endpoint = "POST $gw/session (empty model_ids)"
            api_code = if ($badCreate) { $badCreate.code } else { $null }
            expected = @{ code = 400 }
            result = if ($badCreate -and $badCreate.code -eq 400) { 'pass' } else { 'fail' }
        }
        stats_not_found = @{
            endpoint = "GET $gw/session/99999999/stats"
            api_code = if ($stats404) { $stats404.code } else { $null }
            expected = @{ code = 404 }
            result = if ($stats404 -and $stats404.code -eq 404) { 'pass' } else { 'fail' }
        }
    }
    acceptance = [ordered]@{
        create_stopped_with_keys = ($create.code -eq 0 -and $keyCheck.ok)
        start_running_not_stub   = ($start.data.status -eq "running" -and $start.data.service_log_path)
        stats_shape              = ($statsKeys.ok -and $stats.data.total_devices -eq 1)
        sse_initial              = ($sseHasProgress -and $sseHasData)
        heartbeat_updates        = ($statsAfterHb.data.total_patrols -eq 3)
        stop_stopped             = ($stop.data.status -eq "stopped")
        validation_honest_fail   = ($badCreate.code -eq 400 -and $stats404.code -eq 404)
        overall                  = "PASS"
    }
}

$allPass = @(
    $create.code -eq 0 -and $keyCheck.ok
    $startResp.StatusCode -eq 200 -and $start.code -eq 0 -and $start.data.status -eq 'running'
    $stats.code -eq 0 -and $statsKeys.ok -and $stats.data.total_devices -eq 1
    $sseHasProgress -and $sseHasData
    $hb.code -eq 0 -and $statsAfterHb.data.total_patrols -eq 3
    $stopResp.StatusCode -eq 200 -and $stop.data.status -eq 'stopped'
    $badCreate -and $badCreate.code -eq 400
    $stats404 -and $stats404.code -eq 404
) | Where-Object { -not $_ }

if ($allPass.Count -gt 0) {
    $evidence.status = "FAIL"
    $evidence.acceptance.overall = "FAIL"
}

$out = "F:/acme/.worktrees/video-java/logs/cp-6-patrol.json"
$evidence | ConvertTo-Json -Depth 12 | Set-Content -Path $out -Encoding UTF8
Write-Host "Wrote $out status=$($evidence.status)"
if ($evidence.status -ne "PASS") { exit 1 }
