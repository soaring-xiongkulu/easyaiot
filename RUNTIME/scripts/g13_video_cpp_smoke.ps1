#Requires -Version 5.1
<#
.SYNOPSIS
  G-1.3: source deploy.env.ps1 then run VIDEO cpp daemon smoke harness.

.EXAMPLE
  . .\RUNTIME\scripts\g13_video_cpp_smoke.ps1
#>
[CmdletBinding()]
param(
    [int]$TaskId = 91301,
    [string]$Media = "people-detection.mp4",
    [double]$WaitSec = 45
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

. (Join-Path $ScriptDir "deploy.env.ps1")

Push-Location $RepoRoot
try {
    python tools\runtime_parity\g13_video_cpp_launch.py `
        --task-id $TaskId `
        --media $Media `
        --wait-sec $WaitSec
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
