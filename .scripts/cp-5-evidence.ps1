# CP-5 evidence: algorithm services/status honesty (local full stack)
$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMddHHmmss"
$gw = "http://127.0.0.1:48080/admin-api/video/algorithm"
$taskId = 61
$pg = @{
    Host = "127.0.0.1"
    Port = 15432
    Db   = "iot-video20"
    User = "postgres"
    Pass = "iot45722414822"
}

function Invoke-Api($Method, $Path, $Body = $null) {
    $uri = "$gw$Path"
    if ($Body) {
        return Invoke-RestMethod -Method $Method -Uri $uri -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 10)
    }
    return Invoke-RestMethod -Method $Method -Uri $uri
}

function Invoke-Pg($Sql) {
    $env:PGPASSWORD = $pg.Pass
    & psql -h $pg.Host -p $pg.Port -U $pg.User -d $pg.Db -t -A -c $Sql
    if ($LASTEXITCODE -ne 0) { throw "psql failed: $Sql" }
}

function Test-ProcessAlive($processId) {
    if (-not $processId) { return $false }
    return $null -ne (Get-Process -Id $processId -ErrorAction SilentlyContinue)
}

function Set-OrphanDbState($taskId) {
    Invoke-Pg "UPDATE algorithm_task SET is_enabled=true, run_status='running', service_last_heartbeat=NOW() - INTERVAL '5 minutes', service_process_id=NULL WHERE id=$taskId;"
}

Write-Host "=== CP-5 preclean stop task $taskId ==="
try { Invoke-Api POST "/task/$taskId/stop" | Out-Null } catch { }
Start-Sleep -Seconds 2

Write-Host "=== CP-5 start task $taskId ==="
$start = Invoke-Api POST "/task/$taskId/start"
Start-Sleep -Seconds 4
$statusAfterStart = Invoke-Api GET "/task/$taskId/services/status"
$rt = $statusAfterStart.data.realtime_service
$pidAfterStart = $rt.process_id
$pidAlive = Test-ProcessAlive $pidAfterStart

Write-Host "=== CP-5 orphan DB (stop supervisor, SQL run_status=running + stale heartbeat) ==="
try { Invoke-Api POST "/task/$taskId/stop" | Out-Null } catch { }
Start-Sleep -Seconds 2
Set-OrphanDbState $taskId
$orphanStatus = Invoke-Api GET "/task/$taskId/services/status"
$orphanRt = $orphanStatus.data.realtime_service

Write-Host "=== CP-5 kill RUNTIME with stale heartbeat (no DB-only running) ==="
$restart = Invoke-Api POST "/task/$taskId/start"
Start-Sleep -Seconds 4
$liveStatus = Invoke-Api GET "/task/$taskId/services/status"
$livePid = $liveStatus.data.realtime_service.process_id
if ($livePid) {
    Write-Host "Killing PID $livePid"
    Stop-Process -Id $livePid -Force -ErrorAction SilentlyContinue
}
Set-OrphanDbState $taskId
Start-Sleep -Milliseconds 800
$afterKill = Invoke-Api GET "/task/$taskId/services/status"
$afterKillRt = $afterKill.data.realtime_service

try { Invoke-Api POST "/task/$taskId/stop" | Out-Null } catch { }

$evidence = [ordered]@{
    pack         = "CP-5"
    title        = "Algorithm services/status honesty (no DB-only fake running)"
    generated_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
    status       = "PASS"
    profile      = "local"
    worktree     = "F:/acme/.worktrees/video-java"
    branch       = (git rev-parse --abbrev-ref HEAD 2>$null)
    correlation_id = "cp-5-evidence-$ts"
    change       = "Removed resolveServiceStatus certify heuristic (is_enabled+run_status=running without alive process)"
    stack        = @{
        postgresql   = "127.0.0.1:15432/iot-video20"
        gateway      = "127.0.0.1:48080"
        video_server = "127.0.0.1:48096"
    }
    oracle_python = @{
        services_status = "F:/acme/VIDEO/app/blueprints/algorithm_task.py get_task_services_status"
        running_sources = "daemon poll OR heartbeat<60s — NOT is_enabled+run_status alone"
        legacy_null     = "extractor/sorter/pusher always null in new architecture"
    }
    java_candidate = @{
        lifecycle = "DEVICE/iot-video/iot-video-biz/src/main/java/com/basiclab/iot/video/service/AlgorithmTaskLifecycleService.java"
        method    = "resolveServiceStatus"
    }
    fixture = @{
        task_id   = $taskId
        task_name = "frb26_alert_e2e"
        task_type = "realtime"
    }
    scenarios = [ordered]@{
        start_then_running = @{
            endpoint        = "POST/GET $gw/task/$taskId/start then /services/status"
            api_code        = $start.code
            realtime_status = $rt.status
            run_status      = $rt.run_status
            process_id      = $pidAfterStart
            pid_alive       = $pidAlive
            expected        = @{ status = "running"; pid_alive = $true }
            status          = if ($rt.status -eq "running" -and $pidAlive) { "pass" } else { "fail" }
        }
        null_legacy_fields_python_parity = @{
            endpoint  = "GET $gw/task/$taskId/services/status"
            extractor = $statusAfterStart.data.extractor
            sorter    = $statusAfterStart.data.sorter
            pusher    = $statusAfterStart.data.pusher
            expected  = @{ extractor = $null; sorter = $null; pusher = $null }
            note      = "Python new architecture also returns null for extractor/sorter/pusher — not a gap"
            status    = if ($null -eq $statusAfterStart.data.extractor -and $null -eq $statusAfterStart.data.sorter -and $null -eq $statusAfterStart.data.pusher) { "pass" } else { "fail" }
        }
        orphan_db_no_fake_running = @{
            method          = "stop supervisor then SQL is_enabled=true, run_status=running, heartbeat stale"
            db_run_status   = $orphanRt.run_status
            realtime_status = $orphanRt.status
            expected        = @{ status = "stopped"; must_not_be = "running_from_db_only" }
            status          = if ($orphanRt.status -eq "stopped") { "pass" } else { "fail" }
        }
        kill_process_stale_heartbeat = @{
            method          = "start, taskkill RUNTIME, age heartbeat 5m, GET status before restart window"
            killed_pid      = $livePid
            realtime_status = $afterKillRt.status
            db_run_status   = $afterKillRt.run_status
            expected        = @{ status = "stopped"; note = "must not report running solely from DB run_status" }
            status          = if ($afterKillRt.status -eq "stopped") { "pass" } else { "fail" }
        }
    }
    acceptance = [ordered]@{
        start_running_with_alive_pid     = ($rt.status -eq "running" -and $pidAlive)
        legacy_fields_null_python_parity = ($null -eq $statusAfterStart.data.extractor)
        orphan_db_not_fake_running       = ($orphanRt.status -eq "stopped")
        kill_not_fake_running_from_db    = ($afterKillRt.status -eq "stopped")
        overall                          = "PASS"
    }
}

$fail = @(
    $evidence.scenarios.start_then_running.status,
    $evidence.scenarios.null_legacy_fields_python_parity.status,
    $evidence.scenarios.orphan_db_no_fake_running.status,
    $evidence.scenarios.kill_process_stale_heartbeat.status
) | Where-Object { $_ -ne "pass" }
if ($fail.Count -gt 0) {
    $evidence.status = "FAIL"
    $evidence.acceptance.overall = "FAIL"
}

$out = "F:/acme/.worktrees/video-java/logs/cp-5-services-status.json"
$evidence | ConvertTo-Json -Depth 12 | Set-Content -Path $out -Encoding UTF8
Write-Host "Wrote $out status=$($evidence.status)"
if ($evidence.status -ne "PASS") { exit 1 }
