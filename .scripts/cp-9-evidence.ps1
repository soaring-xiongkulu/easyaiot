# CP-9 evidence: FlightHub config/live + directory key fields (local full stack)
$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMddHHmmss"
$gw = "http://127.0.0.1:48080/admin-api/video/camera"
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
        return Invoke-RestMethod -Method $Method -Uri $uri -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 12)
    }
    return Invoke-RestMethod -Method $Method -Uri $uri
}

function Invoke-Pg($Sql) {
    $env:PGPASSWORD = $pg.Pass
    & psql -h $pg.Host -p $pg.Port -U $pg.User -d $pg.Db -t -A -c $Sql
    if ($LASTEXITCODE -ne 0) { throw "psql failed: $Sql" }
}

function Test-ConfigShape($cfg) {
    $required = @(
        "allowed_ips", "workspace_id", "workspace_name", "platform_name",
        "platform_host", "openapi_host", "live_start_path",
        "mqtt_enabled", "mqtt_broker_uri", "mqtt_client_id", "mqtt_username"
    )
    $missing = @($required | Where-Object { -not ($cfg.PSObject.Properties.Name -contains $_) })
    return @{ ok = ($missing.Count -eq 0); missing = $missing }
}

function Test-TreeNodeShape($node) {
    $required = @("id", "name", "parent_id", "sort_order", "is_default", "device_count", "children")
    $missing = @($required | Where-Object { -not ($node.PSObject.Properties.Name -contains $_) })
    return @{ ok = ($missing.Count -eq 0); missing = $missing }
}

Write-Host "=== CP-9 GET flighthub/config ==="
$config = Invoke-Api GET "/flighthub/config"
$configShape = Test-ConfigShape $config.data

Write-Host "=== CP-9 POST flighthub/live-stream/start (no creds) ==="
$liveNoCreds = Invoke-Api POST "/flighthub/live-stream/start" @{}
$livePartial = Invoke-Api POST "/flighthub/live-stream/start" @{
    api_host      = "https://flighthub.example.com"
    project_uuid  = "test-workspace"
}

Write-Host "=== CP-9 POST register/device/dji-live (no source) ==="
$djiNoSourceCode = $null
$djiNoSourceMsg = $null
try {
    $djiResp = Invoke-Api POST "/register/device/dji-live" @{ device_type = "dock" }
    $djiNoSourceCode = $djiResp.code
    $djiNoSourceMsg = $djiResp.msg
} catch {
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $bodyText = $reader.ReadToEnd()
        $reader.Close()
        if ($bodyText) {
            $parsed = $bodyText | ConvertFrom-Json
            $djiNoSourceCode = $parsed.code
            $djiNoSourceMsg = $parsed.msg
        }
    }
    if ($null -eq $djiNoSourceCode) {
        $djiNoSourceCode = 500
        $djiNoSourceMsg = $_.Exception.Message
    }
}

Write-Host "=== CP-9 directory list + default directory detail ==="
$dirList = Invoke-Api GET "/directory/list"
$defaultDir = $null
foreach ($node in $dirList.data) {
    if ($node.is_default -eq $true) { $defaultDir = $node; break }
}
if (-not $defaultDir -and $dirList.data.Count -gt 0) { $defaultDir = $dirList.data[0] }
$defaultId = $defaultDir.id
$dirDetail = Invoke-Api GET "/directory/$defaultId"
$listShape = Test-TreeNodeShape $defaultDir

Write-Host "=== CP-9 directory monitor-tree (skip_sync=1) ==="
$monitor = Invoke-Api GET "/directory/monitor-tree?skip_sync=1"
$monitorRoot = $monitor.data.tree | Select-Object -First 1
$monitorDevice = $null
if ($monitorRoot -and $monitorRoot.devices -and $monitorRoot.devices.Count -gt 0) {
    $monitorDevice = $monitorRoot.devices[0]
}

Write-Host "=== CP-9 directory CRUD round-trip ==="
$tmpName = "cp9-evidence-$ts"
$created = Invoke-Api POST "/directory" @{ name = $tmpName; description = "cp-9 temp" }
$createdId = $created.data.id
$updated = Invoke-Api PUT "/directory/$createdId" @{ sort_order = 99 }
Invoke-Api DELETE "/directory/$createdId" | Out-Null
$deletedGone = $false
try {
    Invoke-Api GET "/directory/$createdId" | Out-Null
} catch {
    $deletedGone = $true
}

Write-Host "=== CP-9 DB cross-check default directory ==="
$dbDefaultId = Invoke-Pg "SELECT id FROM device_directory WHERE name='默认分组' AND parent_id IS NULL LIMIT 1;"
$dbDefaultId = ($dbDefaultId | Out-String).Trim()
$dbDeviceCount = Invoke-Pg "SELECT COUNT(*) FROM device WHERE directory_id=$dbDefaultId;"

$evidence = [ordered]@{
    pack           = "CP-9"
    title          = "FlightHub config/live + directory key fields vs Python"
    generated_at   = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
    status         = "PASS"
    profile        = "local"
    worktree       = "F:/acme/.worktrees/video-java"
    branch         = (git -C "F:/acme/.worktrees/video-java" rev-parse --abbrev-ref HEAD 2>$null)
    correlation_id = "cp-9-evidence-$ts"
    change         = "Fix CameraFlighthubService env fallback (coalesce data then FLIGHTHUB_* env)"
    stack          = @{
        postgresql   = "127.0.0.1:15432/iot-video20"
        gateway      = "127.0.0.1:48080"
        video_server = "127.0.0.1:48096"
    }
    oracle_python  = @{
        flighthub_config = "F:/acme/VIDEO/app/utils/flighthub_source.py get_flighthub_public_config"
        flighthub_live   = "F:/acme/VIDEO/app/utils/flighthub_source.py start_flighthub_live"
        directory_routes = "F:/acme/VIDEO/app/blueprints/camera.py /directory/* + /flighthub/*"
    }
    java_candidate = @{
        flighthub_support = "DEVICE/iot-video/iot-video-biz/.../FlighthubSourceSupport.java"
        flighthub_service = "DEVICE/iot-video/iot-video-biz/.../CameraFlighthubService.java"
        directory_service = "DEVICE/iot-video/iot-video-biz/.../CameraDirectoryService.java"
        controller        = "DEVICE/iot-video/iot-video-biz/.../CameraController.java"
    }
    scenarios      = [ordered]@{
        flighthub_config_shape = @{
            endpoint = "GET $gw/flighthub/config"
            api_code = $config.code
            keys_ok  = $configShape.ok
            missing  = $configShape.missing
            live_start_path = $config.data.live_start_path
            expected = @{ code = 0; keys = "allowed_ips..mqtt_username (11 fields)" }
            status   = if ($config.code -eq 0 -and $configShape.ok) { "pass" } else { "fail" }
        }
        live_start_missing_creds = @{
            endpoint     = "POST $gw/flighthub/live-stream/start {}"
            api_code     = $liveNoCreds.code
            msg          = $liveNoCreds.msg
            expected     = @{ code = 400; honest_fail = $true }
            status       = if ($liveNoCreds.code -eq 400 -and $liveNoCreds.msg -match "required") { "pass" } else { "fail" }
        }
        live_start_partial_creds = @{
            endpoint = "POST $gw/flighthub/live-stream/start (host+workspace, no token)"
            api_code = $livePartial.code
            msg      = $livePartial.msg
            expected = @{ code = 400; honest_fail = $true }
            status   = if ($livePartial.code -eq 400) { "pass" } else { "fail" }
        }
        dji_register_no_source = @{
            endpoint = "POST $gw/register/device/dji-live (no source)"
            api_code = $djiNoSourceCode
            msg      = $djiNoSourceMsg
            note     = "VideoBusinessException -> HTTP 400"
            status   = if ($djiNoSourceCode -eq 400) { "pass" } else { "fail" }
            expected = @{ code = 400; must_fail = $true }
        }
        directory_list_shape = @{
            endpoint      = "GET $gw/directory/list"
            api_code      = $dirList.code
            default_id    = $defaultId
            tree_keys_ok  = $listShape.ok
            missing_keys  = $listShape.missing
            db_default_id = [int]$dbDefaultId
            id_match_db   = ($defaultId -eq [int]$dbDefaultId)
            status        = if ($dirList.code -eq 0 -and $listShape.ok -and ($defaultId -eq [int]$dbDefaultId)) { "pass" } else { "fail" }
        }
        directory_detail_fields = @{
            endpoint       = "GET $gw/directory/$defaultId"
            api_code       = $dirDetail.code
            device_count   = $dirDetail.data.device_count
            children_count = $dirDetail.data.children_count
            db_device_count = [int]($dbDeviceCount | Out-String).Trim()
            count_match_db = ($dirDetail.data.device_count -eq [int]($dbDeviceCount | Out-String).Trim())
            fields         = @($dirDetail.data.PSObject.Properties.Name)
            status         = if ($dirDetail.code -eq 0 -and $dirDetail.data.device_count -ge 0 -and $dirDetail.data.children_count -ge 0) { "pass" } else { "fail" }
        }
        monitor_tree_shape = @{
            endpoint    = "GET $gw/directory/monitor-tree?skip_sync=1"
            api_code    = $monitor.code
            has_tree    = ($null -ne $monitor.data.tree)
            unassigned  = $monitor.data.unassigned_devices
            root_type   = $monitorRoot.type
            device_fields = if ($monitorDevice) { @($monitorDevice.PSObject.Properties.Name) } else { @() }
            expected_device_keys = @("type", "id", "name", "http_stream", "online", "directory_id", "device_kind", "source")
            status      = if ($monitor.code -eq 0 -and $monitor.data.tree -and $monitorRoot.type -eq "directory") { "pass" } else { "fail" }
        }
        directory_crud_roundtrip = @{
            created_id = $createdId
            updated_sort = $updated.data.sort_order
            deleted_gone = $deletedGone
            status     = if ($createdId -and $updated.data.sort_order -eq 99 -and $deletedGone) { "pass" } else { "fail" }
        }
    }
    acceptance     = [ordered]@{
        config_readable           = ($config.code -eq 0)
        missing_creds_honest_fail   = ($liveNoCreds.code -eq 400)
        directory_fields_explainable = ($dirList.code -eq 0 -and $dirDetail.code -eq 0)
        shared_db_default_dir_match = ($defaultId -eq [int]$dbDefaultId)
        overall                   = "PASS"
    }
}

$fail = @(
    $evidence.scenarios.flighthub_config_shape.status,
    $evidence.scenarios.live_start_missing_creds.status,
    $evidence.scenarios.live_start_partial_creds.status,
    $evidence.scenarios.dji_register_no_source.status,
    $evidence.scenarios.directory_list_shape.status,
    $evidence.scenarios.directory_detail_fields.status,
    $evidence.scenarios.monitor_tree_shape.status,
    $evidence.scenarios.directory_crud_roundtrip.status
) | Where-Object { $_ -ne "pass" }
if ($fail.Count -gt 0) {
    $evidence.status = "FAIL"
    $evidence.acceptance.overall = "FAIL"
}

$out = "F:/acme/.worktrees/video-java/logs/cp-9-flighthub-directory.json"
$evidence | ConvertTo-Json -Depth 14 | Set-Content -Path $out -Encoding UTF8
Write-Host "Wrote $out status=$($evidence.status)"
if ($evidence.status -ne "PASS") { exit 1 }
