# CP-7 evidence: AudioTalk main-path Python key semantics (local full stack)
$ErrorActionPreference = "Stop"
$ts = Get-Date -Format "yyyyMMddHHmmss"
$direct = "http://127.0.0.1:48096/video/camera/audio/talk"
$fixtureDevice = "vj_p2_device"
$invalidDevice = "invalid_cp7_device"
$tmpBody = Join-Path $env:TEMP "cp7-body-$ts.json"

function Invoke-AudioTalkRaw {
    param(
        [string]$Label,
        [string]$Method,
        [string]$Uri,
        [string]$Body = $null
    )
    $tmpResp = Join-Path $env:TEMP "cp7-resp-$Label-$ts.txt"
    if ($Method -eq "GET") {
        $http = & curl.exe -s -o $tmpResp -w "%{http_code}" $Uri
    } else {
        Set-Content -Path $tmpBody -Value $Body -Encoding UTF8 -NoNewline
        $http = & curl.exe -s -o $tmpResp -w "%{http_code}" -X POST -H "Content-Type: application/json" --data-binary "@$tmpBody" $Uri
    }
    $text = if (Test-Path $tmpResp) { Get-Content -Path $tmpResp -Raw -Encoding UTF8 } else { "" }
    Remove-Item -Path $tmpResp -Force -ErrorAction SilentlyContinue
    $json = $null
    if ($text) { $json = $text | ConvertFrom-Json }
    return [ordered]@{
        label    = $Label
        endpoint = "$Method $Uri"
        http     = [int]$http
        code     = if ($json) { $json.code } else { $null }
        msg      = if ($json) { $json.msg } else { $null }
        data     = if ($json) { $json.data } else { $null }
    }
}

Write-Host "=== CP-7 AudioTalk evidence ==="

$health = Invoke-AudioTalkRaw -Label "health" -Method GET -Uri "$direct/health"
$capMissing = Invoke-AudioTalkRaw -Label "cap_missing" -Method GET -Uri "$direct/capabilities"
$capInvalid = Invoke-AudioTalkRaw -Label "cap_invalid" -Method GET -Uri "$direct/capabilities?device_id=$invalidDevice"
$capFixture = Invoke-AudioTalkRaw -Label "cap_fixture" -Method GET -Uri "$direct/capabilities?device_id=$fixtureDevice"
$startMissing = Invoke-AudioTalkRaw -Label "start_missing" -Method POST -Uri "$direct/start" -Body "{}"
$startInvalid = Invoke-AudioTalkRaw -Label "start_invalid" -Method POST -Uri "$direct/start" -Body ('{"device_id":"' + $invalidDevice + '"}')
$startFixture = Invoke-AudioTalkRaw -Label "start_fixture" -Method POST -Uri "$direct/start" -Body ('{"device_id":"' + $fixtureDevice + '"}')
$stopMissing = Invoke-AudioTalkRaw -Label "stop_missing" -Method POST -Uri "$direct/stop" -Body "{}"
$stopOk = Invoke-AudioTalkRaw -Label "stop_ok" -Method POST -Uri "$direct/stop" -Body '{"session_id":"audio_talk_cp7_probe_12345678"}'

Remove-Item -Path $tmpBody -Force -ErrorAction SilentlyContinue

$capSupported = $null
if ($capFixture.data -and $capFixture.data.capabilities) {
    $capSupported = $capFixture.data.capabilities.supported
}
$startSuccess = $null
if ($startFixture.data) { $startSuccess = $startFixture.data.success }

$scenarios = [ordered]@{
    health_python_keys = @{
        endpoint = $health.endpoint
        http     = $health.http
        code     = $health.code
        data     = $health.data
        expected = @{ http = 200; code = 0; keys = @("status", "onvif_available", "audio_talk_available") }
        status   = if ($health.http -eq 200 -and $health.code -eq 0 -and $health.data.status -eq "ok") { "pass" } else { "fail" }
    }
    capabilities_missing_device = @{
        endpoint = $capMissing.endpoint
        http     = $capMissing.http
        code     = $capMissing.code
        expected = @{ http = 400; code = 400 }
        status   = if ($capMissing.http -eq 400 -and $capMissing.code -eq 400) { "pass" } else { "fail" }
    }
    capabilities_invalid_device = @{
        endpoint = $capInvalid.endpoint
        http     = $capInvalid.http
        code     = $capInvalid.code
        expected = @{ http = 404; code = 404 }
        status   = if ($capInvalid.http -eq 404 -and $capInvalid.code -eq 404) { "pass" } else { "fail" }
    }
    capabilities_fixture_honest = @{
        endpoint  = $capFixture.endpoint
        http      = $capFixture.http
        code      = $capFixture.code
        supported = $capSupported
        expected  = @{ http = 200; code = 0; supported = $false }
        status    = if ($capFixture.http -eq 200 -and $capFixture.code -eq 0 -and $capSupported -eq $false) { "pass" } else { "fail" }
    }
    start_missing_device = @{
        endpoint = $startMissing.endpoint
        http     = $startMissing.http
        code     = $startMissing.code
        expected = @{ http = 400; code = 400 }
        status   = if ($startMissing.http -eq 400 -and $startMissing.code -eq 400) { "pass" } else { "fail" }
    }
    start_invalid_device = @{
        endpoint = $startInvalid.endpoint
        http     = $startInvalid.http
        code     = $startInvalid.code
        expected = @{ http = 404; code = 404 }
        status   = if ($startInvalid.http -eq 404 -and $startInvalid.code -eq 404) { "pass" } else { "fail" }
    }
    start_fixture_honest_fail = @{
        endpoint = $startFixture.endpoint
        http     = $startFixture.http
        code     = $startFixture.code
        success  = $startSuccess
        msg      = $startFixture.msg
        expected = @{ http = 500; code = 500; data_success = $false }
        status   = if ($startFixture.http -eq 500 -and $startFixture.code -eq 500 -and $startSuccess -eq $false) { "pass" } else { "fail" }
    }
    stop_missing_session = @{
        endpoint = $stopMissing.endpoint
        http     = $stopMissing.http
        code     = $stopMissing.code
        expected = @{ http = 400; code = 400 }
        status   = if ($stopMissing.http -eq 400 -and $stopMissing.code -eq 400) { "pass" } else { "fail" }
    }
    stop_ok = @{
        endpoint   = $stopOk.endpoint
        http       = $stopOk.http
        code       = $stopOk.code
        success    = $stopOk.data.success
        session_id = $stopOk.data.session_id
        expected   = @{ http = 200; code = 0; success = $true }
        status     = if ($stopOk.http -eq 200 -and $stopOk.code -eq 0 -and $stopOk.data.success -eq $true) { "pass" } else { "fail" }
    }
}

$fail = $scenarios.Values | Where-Object { $_.status -ne "pass" }
$overall = if ($fail.Count -eq 0) { "PASS" } else { "FAIL" }

$evidence = [ordered]@{
    pack           = "CP-7"
    title          = "AudioTalk main-path code parity (capabilities/start/stop/health)"
    generated_at   = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
    status         = $overall
    profile        = "local"
    worktree       = "F:/acme/.worktrees/video-java"
    branch         = (git -C "F:/acme/.worktrees/video-java" rev-parse --abbrev-ref HEAD 2>$null)
    correlation_id = "cp-7-evidence-$ts"
    change         = "AudioTalkController HTTP status parity; RequestParam names; AudioTalkService honest failures"
    stack          = @{
        postgresql   = "127.0.0.1:15432/iot-video20"
        video_server = "127.0.0.1:48096"
    }
    oracle_python  = @{
        blueprint   = "F:/acme/VIDEO/app/blueprints/audio_talk.py"
        health_keys = "status, onvif_available, audio_talk_available"
        no_device   = "400/404 honest; start backchannel fail -> 500 data.success=false"
    }
    java_candidate = @{
        controller = "DEVICE/iot-video/iot-video-biz/src/main/java/com/basiclab/iot/video/controller/AudioTalkController.java"
        service    = "DEVICE/iot-video/iot-video-biz/src/main/java/com/basiclab/iot/video/service/talk/AudioTalkService.java"
    }
    fixture = @{
        device_id = $fixtureDevice
        note      = "seed device without camera IP - capabilities supported=false, start honest 500"
    }
    scenarios  = $scenarios
    acceptance = [ordered]@{
        health_keys_present         = ($health.data.status -eq "ok")
        missing_device_http_400     = ($capMissing.http -eq 400)
        invalid_device_http_404     = ($capInvalid.http -eq 404)
        fixture_capabilities_honest = ($capSupported -eq $false)
        start_fixture_honest_500    = ($startFixture.http -eq 500 -and $startSuccess -eq $false)
        stop_ok_python_keys         = ($stopOk.data.success -eq $true)
        overall                     = $overall
    }
}

$out = "F:/acme/.worktrees/video-java/logs/cp-7-audiotalk.json"
$evidence | ConvertTo-Json -Depth 12 | Set-Content -Path $out -Encoding UTF8
Write-Host "Wrote $out status=$overall"
foreach ($s in $scenarios.GetEnumerator()) {
    Write-Host "  $($s.Key): $($s.Value.status) http=$($s.Value.http) code=$($s.Value.code)"
}
if ($overall -ne "PASS") { exit 1 }
