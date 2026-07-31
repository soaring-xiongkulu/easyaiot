#Requires -Version 5.0
<#
.SYNOPSIS
  Move Docker Desktop WSL data from C: to E: via directory junction.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\move_docker_data_to_e.ps1
  powershell -ExecutionPolicy Bypass -File .\move_docker_data_to_e.ps1 -TargetRoot E:\DockerDesktop
#>

[CmdletBinding()]
param(
    [string]$TargetRoot = "E:\DockerDesktop",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok([string]$m)   { Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err([string]$m)  { Write-Host "[ERR]  $m" -ForegroundColor Red }

$SrcWsl = Join-Path $env:LOCALAPPDATA "Docker\wsl"
$DstWsl = Join-Path $TargetRoot "wsl"

function Get-FreeGb([string]$DriveLetter) {
    $name = $DriveLetter.Substring(0, 1)
    $d = Get-PSDrive -Name $name -ErrorAction SilentlyContinue
    if (-not $d) { return $null }
    return [math]::Round($d.Free / 1GB, 2)
}

function Stop-DockerDesktopHard {
    Write-Info "Stopping Docker Desktop processes..."
    Get-Process | Where-Object {
        $_.ProcessName -match '(?i)docker|vpnkit|com\.docker'
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Info "wsl --shutdown ..."
    & wsl.exe --shutdown 2>$null
    Start-Sleep -Seconds 3
}

function Test-IsJunction([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force
    return [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
}

Write-Host ""
Write-Host "======== Move Docker Desktop data to E: ========" -ForegroundColor Yellow
Write-Info ("Source: {0}" -f $SrcWsl)
Write-Info ("Target: {0}" -f $DstWsl)
Write-Info ("C free={0} GB, E free={1} GB" -f (Get-FreeGb "C"), (Get-FreeGb "E"))

if (-not (Test-Path -LiteralPath "E:\")) {
    Write-Err "Drive E: not found"
    exit 1
}

$eFree = Get-FreeGb "E"
if ($null -eq $eFree -or $eFree -lt 40) {
    Write-Err ("E: free space too low ({0} GB), need >= 40 GB" -f $eFree)
    exit 1
}

if ((Test-IsJunction $SrcWsl) -and (Test-Path -LiteralPath $DstWsl)) {
    Write-Ok ("Already migrated (junction exists). Data at {0}" -f $DstWsl)
    if (-not $Force) {
        exit 0
    }
    Write-Warn "Force re-check requested"
}

if (-not (Test-Path -LiteralPath $SrcWsl) -and -not (Test-Path -LiteralPath $DstWsl)) {
    Write-Err ("Docker WSL dir not found: {0}" -f $SrcWsl)
    Write-Host "Start Docker Desktop once, then retry."
    exit 1
}

Stop-DockerDesktopHard

if ((Test-IsJunction $SrcWsl) -and (Test-Path -LiteralPath $DstWsl)) {
    Write-Ok "Junction already OK, skip copy"
} else {
    New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

    if ((Test-Path -LiteralPath $SrcWsl) -and -not (Test-IsJunction $SrcWsl)) {
        if (Test-Path -LiteralPath $DstWsl) {
            $bak = "$DstWsl.bak.$(Get-Date -Format yyyyMMdd_HHmmss)"
            Write-Warn ("Target exists, rename to {0}" -f $bak)
            Rename-Item -LiteralPath $DstWsl -NewName (Split-Path $bak -Leaf)
        }

        Write-Info "Copying with robocopy (may take several minutes)..."
        $rcLog = Join-Path $TargetRoot "migrate_robocopy.log"
        $robArgs = @(
            $SrcWsl, $DstWsl, "/E", "/COPY:DAT", "/DCOPY:DAT",
            "/R:2", "/W:3", "/NFL", "/NDL", "/NP", "/LOG:$rcLog"
        )
        $p = Start-Process -FilePath "robocopy.exe" -ArgumentList $robArgs -Wait -PassThru -NoNewWindow
        if ($p.ExitCode -gt 7) {
            Write-Err ("robocopy failed, exit={0}, log={1}" -f $p.ExitCode, $rcLog)
            exit 1
        }
        Write-Ok ("Copied to {0}" -f $DstWsl)

        Write-Info "Removing source directory..."
        Remove-Item -LiteralPath $SrcWsl -Recurse -Force
    } elseif (-not (Test-Path -LiteralPath $SrcWsl) -and (Test-Path -LiteralPath $DstWsl)) {
        Write-Info "Source missing, target present: create junction only"
        $parent = Split-Path $SrcWsl -Parent
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    } else {
        Write-Err "Unrecognized source/target state"
        exit 1
    }

    if (Test-Path -LiteralPath $SrcWsl) {
        if (Test-IsJunction $SrcWsl) {
            cmd.exe /c "rmdir `"$SrcWsl`""
        } else {
            Remove-Item -LiteralPath $SrcWsl -Recurse -Force
        }
    }

    Write-Info "Creating directory junction..."
    $mkOut = cmd.exe /c "mklink /J `"$SrcWsl`" `"$DstWsl`"" 2>&1
    Write-Host ($mkOut | Out-String)
    if (-not (Test-IsJunction $SrcWsl)) {
        Write-Err "Failed to create junction"
        exit 1
    }
    Write-Ok ("Junction OK: {0} -> {1}" -f $SrcWsl, $DstWsl)
}

$dd = @(
    (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
    (Join-Path $env:LOCALAPPDATA "Docker\Docker Desktop.exe")
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if ($dd) {
    Write-Info ("Starting Docker Desktop: {0}" -f $dd)
    Start-Process $dd | Out-Null
} else {
    Write-Warn "Docker Desktop.exe not found; start it manually"
}

Write-Info "Waiting for Docker engine..."
$ready = $false
for ($i = 1; $i -le 60; $i++) {
    Start-Sleep -Seconds 3
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "docker"
        $psi.Arguments = "version --format {{.Server.Version}}"
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $proc = [Diagnostics.Process]::Start($psi)
        if ($proc.WaitForExit(15000) -and $proc.ExitCode -eq 0) {
            $ver = $proc.StandardOutput.ReadToEnd().Trim()
            if ($ver) {
                Write-Ok ("Docker engine ready: {0}" -f $ver)
                $ready = $true
                break
            }
        } else {
            try { $proc.Kill() } catch { }
        }
    } catch { }
    if (($i % 5) -eq 0) { Write-Info ("Waiting... {0}/60" -f $i) }
}

Write-Host ""
Write-Info ("After migrate: C free={0} GB, E free={1} GB" -f (Get-FreeGb "C"), (Get-FreeGb "E"))
if ($ready) {
    Write-Ok "Done. Continue with: .\install_windows.cmd install"
    exit 0
}
Write-Warn "Data moved, but engine not ready yet. Open Docker Desktop, wait Running, then install."
exit 2
