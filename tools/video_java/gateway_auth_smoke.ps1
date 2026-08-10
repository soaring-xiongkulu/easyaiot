# FR-W1-AUTH: short gateway + system-server auth smoke (non-observe).
# Prereqs: video-server :48096, system-server :48099, iot-gateway :48080 (mini profile).

$ErrorActionPreference = 'Stop'
$baseGateway = 'http://127.0.0.1:48080'
$baseSystem = 'http://127.0.0.1:48099'
$tenantId = '1'
$listUrl = "$baseGateway/admin-api/video/camera/list?pageNo=1&pageSize=1"

function Assert-Http($label, $status, $expect, $bodySnippet) {
    if ($status -ne $expect) {
        throw "$label expected HTTP $expect got $status body=$bodySnippet"
    }
    Write-Host "PASS $label HTTP $status"
}

# health
foreach ($pair in @(
    @{ n = 'video-server'; u = 'http://127.0.0.1:48096/actuator/health' },
    @{ n = 'system-server'; u = "$baseSystem/actuator/health" },
    @{ n = 'iot-gateway'; u = "$baseGateway/actuator/health" }
)) {
    $r = Invoke-WebRequest -Uri $pair.u -UseBasicParsing -TimeoutSec 10
    if ($r.StatusCode -ne 200) { throw "$($pair.n) not UP" }
    Write-Host "UP $($pair.n)"
}

# no bearer (passthrough)
$r1 = Invoke-WebRequest -Uri $listUrl -Headers @{ 'tenant-id' = $tenantId } -UseBasicParsing
Assert-Http 'no-bearer' $r1.StatusCode 200 ($r1.Content.Substring(0, [Math]::Min(80, $r1.Content.Length)))

# invalid bearer -> 401
try {
    Invoke-WebRequest -Uri $listUrl -Headers @{
        'tenant-id' = $tenantId
        'Authorization' = 'Bearer invalid-token-xyz'
    } -UseBasicParsing | Out-Null
    throw 'invalid-bearer expected 401'
} catch {
    $resp = $_.Exception.Response
    if ($null -eq $resp -or [int]$resp.StatusCode -ne 401) { throw }
    Write-Host 'PASS invalid-bearer HTTP 401'
}

# login
$loginBody = '{"username":"admin","password":"admin123"}'
$login = Invoke-RestMethod -Uri "$baseSystem/admin-api/system/auth/login" -Method Post `
    -Headers @{ 'tenant-id' = $tenantId; 'Content-Type' = 'application/json' } -Body $loginBody
$token = $login.data.accessToken
if (-not $token) { throw 'login missing accessToken' }
Write-Host "TOKEN $token"

# valid bearer -> 200
$r3 = Invoke-WebRequest -Uri $listUrl -Headers @{
    'tenant-id' = $tenantId
    'Authorization' = "Bearer $token"
} -UseBasicParsing
Assert-Http 'valid-bearer' $r3.StatusCode 200 ($r3.Content.Substring(0, [Math]::Min(80, $r3.Content.Length)))

# rpc check
$check = Invoke-RestMethod -Uri "$baseSystem/rpc-api/system/oauth2/token/check?accessToken=$token"
if ($check.code -ne 0) { throw "token check failed: $($check | ConvertTo-Json -Compress)" }
Write-Host 'PASS system-server token check'
Write-Host 'ALL PASS'
