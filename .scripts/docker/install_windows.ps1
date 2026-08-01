#Requires -Version 5.0
<#
.SYNOPSIS
  EasyAIoT Windows 镜像部署入口（PowerShell）

.DESCRIPTION
  先汇总检测 Docker Desktop / Compose / Git Bash（或 WSL），
  缺什么就提示装什么并中止；全部通过后再转发到 install_windows.sh。
  仅支持拉取预构建镜像部署，不支持本地编译。

  若本机尚未安装 Docker Desktop / WSL，可用：
    .\install_windows.ps1 bootstrap
    .\install_windows.ps1 -Bootstrap
  调配引擎 CPU/内存（mini 4GB / standard 16GB / full 24GB）：
    .\install_windows.ps1 resources
  配置国内镜像加速（与 Linux 一致；FUXA 走专用 1ms 优先）：
    .\install_windows.ps1 mirrors
  或设置环境变量后重试：
    $env:EASYAIOT_AUTO_INSTALL_DOCKER = "1"; .\install_windows.ps1 install

.EXAMPLE
  .\install_windows.cmd
  .\install_windows.cmd check
  .\install_windows.cmd install
  .\install_windows.cmd bootstrap
  .\install_windows.cmd mirrors
  .\install_windows.cmd resources
  .\install_windows.cmd movedata   # C 盘空间不足时，把 Docker 数据迁到 E:\DockerDesktop

  # 若直接跑 .ps1 报「禁止运行脚本」，可用：
  #   powershell -ExecutionPolicy Bypass -File .\install_windows.ps1 bootstrap
  # 或改当前用户策略（一次即可）：
  #   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs = @(),
    [switch]$Bootstrap
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BashScript = Join-Path $ScriptDir "install_windows.sh"

# 控制台尽量用 UTF-8，避免中文提示乱码；外部命令（wsl 等）的本地化 stderr 仍可能乱码，探测时一律吞掉
try {
    if ($Host.Name -eq 'ConsoleHost') {
        [Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
        [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    }
    $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $null = cmd /c "chcp 65001 >nul"
} catch { }

function Write-Info($msg)  { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]  $msg" -ForegroundColor Red }

# 在 ErrorActionPreference=Stop 下，原生命令写 stderr 也会变成终止异常；探测类调用必须用 Continue + 丢弃输出
function Invoke-NativeExitCode {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Command 1>$null 2>$null
        if ($null -ne $LASTEXITCODE) { return [int]$LASTEXITCODE }
        return 0
    } catch {
        if ($null -ne $LASTEXITCODE) { return [int]$LASTEXITCODE }
        return 1
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Get-DockerBinCandidates {
    @(
        "$env:ProgramFiles\Docker\Docker\resources\bin",
        "${env:ProgramFiles(x86)}\Docker\Docker\resources\bin",
        "$env:LOCALAPPDATA\Docker\resources\bin",
        "$env:ProgramFiles\Docker\Docker\resources"
    )
}

function Ensure-DockerOnPath {
    if (Get-Command docker -ErrorAction SilentlyContinue) { return $true }
    foreach ($dir in (Get-DockerBinCandidates)) {
        $exe = Join-Path $dir "docker.exe"
        if (Test-Path $exe) {
            if ($env:Path -notlike "*$dir*") {
                $env:Path = "$dir;$env:Path"
                Write-Info "已将 Docker CLI 加入当前会话 PATH: $dir"
            }
            return $true
        }
    }
    return $false
}

function Find-BashCandidates {
    $candidates = New-Object System.Collections.Generic.List[string]
    @(
        "$env:ProgramFiles\Git\bin\bash.exe",
        "$env:ProgramFiles\Git\usr\bin\bash.exe",
        "${env:ProgramFiles(x86)}\Git\bin\bash.exe",
        "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe"
    ) | Where-Object { Test-Path $_ } | ForEach-Object { [void]$candidates.Add($_) }

    $pathBash = Get-Command bash -ErrorAction SilentlyContinue
    if ($pathBash -and $pathBash.Source -and (Test-Path $pathBash.Source)) {
        [void]$candidates.Add($pathBash.Source)
    }
    return $candidates
}

function Find-Bash {
    foreach ($c in (Find-BashCandidates)) {
        if ($c -and (Test-Path $c)) {
            return @{ Kind = "bash"; Path = $c }
        }
    }
    $wsl = Get-Command wsl -ErrorAction SilentlyContinue
    if ($wsl) {
        # wsl 存在不等于已安装发行版；仅当 --status 成功时采用
        if ((Invoke-NativeExitCode { & wsl.exe --status }) -eq 0) {
            return @{ Kind = "wsl"; Path = "wsl" }
        }
    }
    return $null
}

function Test-BashVersion4Plus([string]$BashPath) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $out = & $BashPath -c 'echo ${BASH_VERSINFO[0]}' 2>$null
        if ($LASTEXITCODE -ne 0) { return $false }
        $major = 0
        [int]::TryParse(($out | Select-Object -First 1).ToString().Trim(), [ref]$major) | Out-Null
        return ($major -ge 4)
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Find-DockerDesktopExe {
    return @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}

function Test-WslInstalled {
    $wsl = Get-Command wsl -ErrorAction SilentlyContinue
    if (-not $wsl) { return $false }
    # 未安装时 wsl 会输出本地化中文到 stderr，编码常与控制台不一致 → 乱码 + Stop 下抛异常
    return ((Invoke-NativeExitCode { & wsl.exe --status }) -eq 0)
}

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Start-DockerDesktopIfNeeded {
    $dd = Find-DockerDesktopExe
    if ($dd) {
        Write-Info "尝试启动 Docker Desktop: $dd"
        Start-Process $dd | Out-Null
        return $true
    }
    return $false
}

function Test-DockerDaemonReady {
    Ensure-DockerOnPath | Out-Null
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) { return $false }
    # 优先用轻量 version；docker info 在异常状态下可能长时间阻塞
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $dockerCmd.Source
        $psi.Arguments = "version --format {{.Server.Version}}"
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        $p = [System.Diagnostics.Process]::Start($psi)
        if (-not $p.WaitForExit(20000)) {
            try { $p.Kill() } catch { }
            return $false
        }
        if ($p.ExitCode -ne 0) { return $false }
        $out = $p.StandardOutput.ReadToEnd().Trim()
        return (-not [string]::IsNullOrWhiteSpace($out))
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Install-WslIfNeeded {
    if (Test-WslInstalled) {
        Write-Ok "WSL: 已安装"
        return $true
    }
    Write-Warn "未检测到可用的 WSL（Docker Desktop 通常需要 WSL2）"
    if (-not (Test-IsAdmin)) {
        Write-Err "安装 WSL 需要管理员权限。请用「以管理员身份运行」的 PowerShell 执行："
        Write-Host "  wsl --install"
        Write-Host "  或: .\install_windows.ps1 bootstrap"
        return $false
    }
    Write-Info "正在安装 WSL（可能需要几分钟，完成后通常需重启）..."
    $prevEa = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & wsl.exe --install --no-distribution
        $rc = $LASTEXITCODE
        if ($rc -ne 0) {
            Write-Warn "wsl --install --no-distribution 退出码 $rc，尝试 wsl --install ..."
            & wsl.exe --install
            $rc = $LASTEXITCODE
        }
    } finally {
        $ErrorActionPreference = $prevEa
    }
    if (Test-WslInstalled) {
        Write-Ok "WSL: 安装完成"
        return $true
    }
    Write-Warn "WSL 组件可能已开始安装，但当前会话仍不可用。请重启电脑后再继续。"
    Write-Host "  重启后执行: .\install_windows.ps1 bootstrap"
    Write-Host "  或:           .\install_windows.ps1 install"
    return $false
}

function Install-DockerDesktopIfNeeded {
    Ensure-DockerOnPath | Out-Null
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Ok ("Docker CLI: " + (docker --version 2>$null))
        return $true
    }
    if (Find-DockerDesktopExe) {
        Write-Ok "Docker Desktop: 已安装（CLI 稍后加入 PATH）"
        Ensure-DockerOnPath | Out-Null
        return $true
    }

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Err "未找到 winget，无法自动安装 Docker Desktop"
        Write-Host "请手动下载安装: https://www.docker.com/products/docker-desktop"
        return $false
    }

    Write-Info "正在通过 winget 安装 Docker Desktop（体积较大，请耐心等待）..."
    & winget install -e --id Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    $rc = $LASTEXITCODE
    # winget: 0 成功；-1978335189 等表示已安装
    if ($rc -ne 0 -and $rc -ne -1978335189) {
        Write-Warn "winget 退出码 $rc，请检查是否需管理员权限或手动安装"
    }

    # 刷新当前会话 PATH（机器/用户 PATH 可能已更新，但本进程未继承）
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($machinePath -or $userPath) {
        $env:Path = ($machinePath + ';' + $userPath)
    }
    Ensure-DockerOnPath | Out-Null

    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd -or (Find-DockerDesktopExe)) {
        Write-Ok 'Docker Desktop: install OK (or already present)'
        return $true
    }

    Write-Err 'Docker Desktop installed but not detected yet. Sign out/reboot, or open Docker Desktop once to finish setup.'
    Write-Host 'Download: https://www.docker.com/products/docker-desktop'
    return $false
}

function Get-EasyAIoTResourceTargets {
    $profile = if ($env:EASYAIOT_DEPLOY_PROFILE) { $env:EASYAIOT_DEPLOY_PROFILE.ToLower() } else { "full" }
    $hostMem = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 0)
    $hostCpu = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
    if (-not $hostCpu) { $hostCpu = $env:NUMBER_OF_PROCESSORS }

    switch ($profile) {
        "mini"     { $wantMem = 4;  $wantCpu = 4; $wantDisk = 60 }
        "standard" { $wantMem = 16; $wantCpu = 6; $wantDisk = 80 }
        default    { $wantMem = 24; $wantCpu = 8; $wantDisk = 100 }
    }
    if ($env:EASYAIOT_DOCKER_MEMORY_GB) { $wantMem = [int]$env:EASYAIOT_DOCKER_MEMORY_GB }
    if ($env:EASYAIOT_DOCKER_CPUS) { $wantCpu = [int]$env:EASYAIOT_DOCKER_CPUS }
    if ($env:EASYAIOT_DOCKER_DISK_GB) { $wantDisk = [int]$env:EASYAIOT_DOCKER_DISK_GB }

    $reserve = if ($hostMem -ge 32) { 8 } else { 4 }
    $memCap = [math]::Max(4, [math]::Min($hostMem - $reserve, [math]::Floor($hostMem * 0.75)))
    if ($wantMem -gt $memCap) { $wantMem = [int]$memCap }
    $cpuCap = [math]::Max(2, $hostCpu - 1)
    if ($wantCpu -gt $cpuCap) { $wantCpu = [int]$cpuCap }

    return @{
        Profile = $profile
        MemoryGB = [int]$wantMem
        Cpus = [int]$wantCpu
        DiskGB = [int]$wantDisk
        HostMemGB = [int]$hostMem
        HostCpus = [int]$hostCpu
    }
}

function Get-DockerEngineMemoryGB {
    Ensure-DockerOnPath | Out-Null
    if (-not (Test-DockerDaemonReady)) { return 0 }
    try {
        $bytes = [int64](docker info --format '{{.MemTotal}}' 2>$null)
        if ($bytes -gt 0) { return [int][math]::Floor($bytes / 1GB) }
    } catch { }
    return 0
}

function Update-DockerDesktopSettingsStore {
    param([int]$MemoryMiB, [int]$Cpus, [int]$DiskMiB, [int]$SwapMiB = 4096)
    $paths = @(
        (Join-Path $env:APPDATA "Docker\settings-store.json"),
        (Join-Path $env:APPDATA "Docker\settings.json")
    )
    $patched = $false
    foreach ($path in $paths) {
        if (-not (Test-Path $path)) { continue }
        try {
            $bak = "$path.easyaiot.bak"
            if (-not (Test-Path $bak)) { Copy-Item $path $bak -Force }
            $json = Get-Content -Raw -Encoding UTF8 $path | ConvertFrom-Json
            # PSCustomObject：动态加属性
            $map = @{
                memoryMiB = $MemoryMiB; MemoryMiB = $MemoryMiB
                cpus = $Cpus; Cpus = $Cpus
                diskSizeMiB = $DiskMiB; DiskSizeMiB = $DiskMiB
                swapMiB = $SwapMiB; SwapMiB = $SwapMiB
                useResourceSaver = $false; UseResourceSaver = $false
            }
            foreach ($k in $map.Keys) {
                if ($null -eq $json.PSObject.Properties[$k]) {
                    $json | Add-Member -NotePropertyName $k -NotePropertyValue $map[$k] -Force
                } else {
                    $json.$k = $map[$k]
                }
            }
            $json | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 -Path $path
            Write-Ok "已写入: $path"
            $patched = $true
        } catch {
            Write-Warn ("更新失败 {0}: {1}" -f $path, $_.Exception.Message)
        }
    }
    return $patched
}

function Update-WslConfigResources {
    param([int]$MemoryGB, [int]$Cpus)
    $cfg = Join-Path $env:USERPROFILE ".wslconfig"
    $block = @"
[wsl2]
memory=${MemoryGB}GB
processors=$Cpus
swap=4GB
localhostForwarding=true
"@
    try {
        if (Test-Path $cfg) {
            $text = Get-Content -Raw -Encoding UTF8 $cfg
            if ($text -match '(?im)^\[wsl2\]') {
                if ($text -match '(?im)^\s*memory\s*=') {
                    $text = [regex]::Replace($text, '(?im)^\s*memory\s*=.*$', "memory=${MemoryGB}GB", 1)
                } else {
                    $text = [regex]::Replace($text, '(?im)^\[wsl2\]\s*$', "[wsl2]`r`nmemory=${MemoryGB}GB", 1)
                }
                if ($text -match '(?im)^\s*processors\s*=') {
                    $text = [regex]::Replace($text, '(?im)^\s*processors\s*=.*$', "processors=$Cpus", 1)
                } else {
                    $text = [regex]::Replace($text, '(?im)^\[wsl2\]\s*$', "[wsl2]`r`nprocessors=$Cpus", 1)
                }
                if ($text -notmatch '(?im)^\s*swap\s*=') {
                    $text = [regex]::Replace($text, '(?im)^\[wsl2\]\s*$', "[wsl2]`r`nswap=4GB", 1)
                }
                Set-Content -Encoding UTF8 -Path $cfg -Value $text.TrimEnd() -NoNewline
                Add-Content -Encoding UTF8 -Path $cfg -Value ""
            } else {
                Add-Content -Encoding UTF8 -Path $cfg -Value "`r`n$block"
            }
        } else {
            Set-Content -Encoding UTF8 -Path $cfg -Value $block
        }
        Write-Ok "已更新 WSL2 资源: $cfg"
        return $true
    } catch {
        Write-Warn ("写入 .wslconfig 失败: {0}" -f $_.Exception.Message)
        return $false
    }
}

function Restart-DockerDesktopForResources {
    Write-Info "重启 Docker Desktop / WSL 以使资源生效..."
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        Get-Process "Docker Desktop","com.docker.backend" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
            & wsl.exe --shutdown 2>$null
        }
        Start-Sleep -Seconds 2
        $dd = Find-DockerDesktopExe
        if ($dd) { Start-Process $dd }
    } finally {
        $ErrorActionPreference = $prev
    }
    for ($i = 1; $i -le 90; $i++) {
        Start-Sleep -Seconds 2
        if (Test-DockerDaemonReady) {
            Write-Ok "Docker 引擎已重新就绪"
            return $true
        }
        if (($i % 10) -eq 0) { Write-Info "等待 Docker 重启... ($i/90)" }
    }
    Write-Warn "重启后引擎尚未就绪，请手动打开 Docker Desktop"
    return $false
}

function Update-DockerDesktopRegistryMirrors {
    # 与 Linux / Mac：写入 %USERPROFILE%\.docker\daemon.json 国内 registry-mirrors
    if ($env:EASYAIOT_DOCKER_SKIP_MIRROR -eq "1") {
        Write-Info "已设置 EASYAIOT_DOCKER_SKIP_MIRROR=1，跳过镜像源配置"
        return 0
    }
    $primary = if ($env:DOCKER_MIRROR) { $env:DOCKER_MIRROR.TrimEnd('/') } else { "https://docker.m.daocloud.io" }
    if ($primary -notmatch '^https?://') { $primary = "https://$primary" }
    $fb = if ($env:DOCKER_MIRROR_FALLBACKS) {
        $env:DOCKER_MIRROR_FALLBACKS
    } else {
        "docker.m.daocloud.io,docker.1ms.run,docker.1panel.live"
    }
    $mirrors = New-Object System.Collections.Generic.List[string]
    [void]$mirrors.Add($primary)
    foreach ($h in ($fb -split ',')) {
        $h = $h.Trim().TrimEnd('/')
        if (-not $h) { continue }
        $h = $h -replace '^https?://', ''
        $url = "https://$h"
        if (-not ($mirrors | Where-Object { $_.TrimEnd('/') -eq $url.TrimEnd('/') })) {
            [void]$mirrors.Add($url)
        }
    }

    Write-Host ""
    Write-Host "======== 配置 Docker Desktop 国内镜像源（对齐 Linux）========" -ForegroundColor Yellow
    Write-Info ("主源/回退: {0}" -f ($mirrors -join " → "))
    Write-Info "FUXA 例外: pull_fuxa.sh 优先 docker.1ms.run（DaoCloud 对 frangoteam 常 403）"

    $cfgPath = Join-Path $env:USERPROFILE ".docker\daemon.json"
    $dir = Split-Path -Parent $cfgPath
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

    $cfg = @{}
    if (Test-Path $cfgPath) {
        try {
            $cfg = Get-Content -Raw -Encoding UTF8 $cfgPath | ConvertFrom-Json
        } catch {
            Copy-Item $cfgPath "$cfgPath.easyaiot.broken.bak" -Force
            $cfg = [pscustomobject]@{}
        }
    } else {
        $cfg = [pscustomobject]@{}
    }

    $cur = @()
    if ($cfg.PSObject.Properties.Name -contains "registry-mirrors" -and $cfg."registry-mirrors") {
        $cur = @($cfg."registry-mirrors" | ForEach-Object { "$_".TrimEnd('/') })
    }
    $want = @($mirrors | ForEach-Object { $_.TrimEnd('/') })
    $same = ($cur.Count -eq $want.Count)
    if ($same) {
        for ($i = 0; $i -lt $cur.Count; $i++) {
            if ($cur[$i] -ne $want[$i]) { $same = $false; break }
        }
    }
    if ($same) {
        Write-Ok "Docker Desktop 镜像源已就绪: $cfgPath"
        return 0
    }

    $bak = "$cfgPath.easyaiot.bak"
    if ((Test-Path $cfgPath) -and -not (Test-Path $bak)) { Copy-Item $cfgPath $bak -Force }
    if ($null -eq $cfg.PSObject.Properties["registry-mirrors"]) {
        $cfg | Add-Member -NotePropertyName "registry-mirrors" -NotePropertyValue @($mirrors) -Force
    } else {
        $cfg."registry-mirrors" = @($mirrors)
    }
    $cfg | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 -Path $cfgPath
    Write-Ok "已写入 registry-mirrors → $cfgPath"

    Write-Info "重启 Docker Desktop 以使镜像源生效..."
    Restart-DockerDesktopForResources | Out-Null
    return 0
}

function Invoke-ConfigureDockerResources {
    param([switch]$Force)
    if ($env:EASYAIOT_DOCKER_SKIP_RESOURCES -eq "1") {
        Write-Info "已设置 EASYAIOT_DOCKER_SKIP_RESOURCES=1，跳过资源调配"
        return 0
    }

    Write-Host ""
    Write-Host "======== 调配 Docker 引擎资源（CPU / 内存 / 磁盘）========" -ForegroundColor Yellow
    Ensure-DockerOnPath | Out-Null
    $t = Get-EasyAIoTResourceTargets
    $curMem = Get-DockerEngineMemoryGB
    Write-Info ("部署形态: {0} · 主机约 {1}GB / {2} CPU" -f $t.Profile, $t.HostMemGB, $t.HostCpus)
    Write-Info ("目标: {0} CPU / {1}GB 内存 / {2}GB 磁盘" -f $t.Cpus, $t.MemoryGB, $t.DiskGB)
    Write-Info ("当前引擎内存: 约 {0}GB" -f $curMem)

    if (-not $Force -and $curMem -ge $t.MemoryGB) {
        Write-Ok "引擎资源已满足目标，无需调整"
        return 0
    }

    $okStore = Update-DockerDesktopSettingsStore -MemoryMiB ($t.MemoryGB * 1024) -Cpus $t.Cpus -DiskMiB ($t.DiskGB * 1024)
    $okWsl = Update-WslConfigResources -MemoryGB $t.MemoryGB -Cpus $t.Cpus
    if (-not $okStore -and -not $okWsl) {
        Write-Warn "未能自动写入配置。请在 Docker Desktop → Settings → Resources 手动将 Memory 调到 ≥$($t.MemoryGB)GB"
        return 1
    }

    Restart-DockerDesktopForResources | Out-Null
    Start-Sleep -Seconds 2
    $curMem = Get-DockerEngineMemoryGB
    Write-Info ("调整后引擎内存: 约 {0}GB" -f $curMem)
    if ($curMem -ge $t.MemoryGB) {
        Write-Ok "Docker 引擎内存已达标"
        return 0
    }
    Write-Warn "配置已写入，引擎汇报仍约 ${curMem}GB。可稍后重试: .\install_windows.ps1 resources"
    Write-Host "  或 GUI: Docker Desktop → Settings → Resources → Apply & Restart"
    return 0
}

function Invoke-BootstrapDeps {
    Write-Host ""
    Write-Host "======== 自动安装 Windows 部署依赖 ========" -ForegroundColor Yellow
    Write-Info "将尝试安装: WSL2（如缺失）+ Docker Desktop"
    Write-Host ""

    $wslOk = Install-WslIfNeeded
    $dockerOk = Install-DockerDesktopIfNeeded

    if ($dockerOk) {
        $launched = Start-DockerDesktopIfNeeded
        if ($launched) {
            Write-Info "等待 Docker 引擎就绪..."
            for ($i = 1; $i -le 60; $i++) {
                Start-Sleep -Seconds 2
                if (Test-DockerDaemonReady) {
                    Write-Ok "Docker Desktop: 引擎已就绪"
                    break
                }
                if (($i % 5) -eq 0) { Write-Info "等待 Docker Desktop 启动... ($i/60)" }
            }
        }
    }

    Write-Host ""
    if ($dockerOk -and (Test-DockerDaemonReady)) {
        Write-Ok "依赖已就绪"
        # 与 Linux 对齐：国内 registry-mirrors（FUXA 仍走 pull_fuxa.sh）
        Update-DockerDesktopRegistryMirrors | Out-Null
        # 按形态调高内存（WSL2/.settings）；full 默认常不足
        Invoke-ConfigureDockerResources | Out-Null
        Write-Info "可继续: .\install_windows.ps1 check"
        Write-Info "         .\install_windows.ps1 install"
        return 0
    }
    if ($dockerOk -and -not (Test-DockerDaemonReady)) {
        Write-Warn "Docker 已安装但引擎未就绪。请打开 Docker Desktop，待 Running 后执行:"
        Write-Host "  .\install_windows.ps1 check"
        Write-Host "  .\install_windows.ps1 resources"
        Write-Host "  .\install_windows.ps1 install"
        return 2
    }
    if (-not $wslOk) {
        Write-Warn "WSL 未就绪时，Docker Desktop 的 WSL2 后端可能无法启动。请先完成 WSL 安装并重启。"
    }
    return 1
}

function Invoke-PrerequisiteCheck {
    $missing = New-Object System.Collections.Generic.List[string]
    $howto = New-Object System.Collections.Generic.List[string]

    Write-Host ""
    Write-Host "======== 前置环境检测（Windows）========" -ForegroundColor Yellow

    Ensure-DockerOnPath | Out-Null

    # 1) Docker CLI
    $dockerCli = Get-Command docker -ErrorAction SilentlyContinue
    $dockerCliOk = $false
    if ($dockerCli) {
        try {
            Write-Ok ("Docker CLI: " + (docker --version))
            $dockerCliOk = $true
        } catch {
            Write-Ok "Docker CLI: 已安装"
            $dockerCliOk = $true
        }
    } else {
        [void]$missing.Add("Docker Desktop（未找到 docker 命令）")
        [void]$howto.Add("一键安装依赖:  .\install_windows.ps1 bootstrap")
        [void]$howto.Add("或管理员 PowerShell:  wsl --install")
        [void]$howto.Add("然后:  winget install -e --id Docker.DockerDesktop")
        [void]$howto.Add("手动下载: https://www.docker.com/products/docker-desktop （建议勾选 WSL2 后端）")
        [void]$howto.Add("装完后重启终端（必要时重启电脑）再执行本脚本")
    }

    # 2) Docker daemon
    $daemonOk = $false
    if ($dockerCliOk) {
        if (Test-DockerDaemonReady) {
            Write-Ok "Docker Desktop: 引擎已运行"
            $daemonOk = $true
        } else {
            $launched = Start-DockerDesktopIfNeeded
            if ($launched) {
                Write-Warn "Docker 引擎未就绪，已尝试启动 Docker Desktop，等待就绪..."
                for ($i = 1; $i -le 45; $i++) {
                    Start-Sleep -Seconds 2
                    if (Test-DockerDaemonReady) {
                        Write-Ok "Docker Desktop: 引擎已就绪"
                        $daemonOk = $true
                        break
                    }
                    if (($i % 5) -eq 0) { Write-Info "等待 Docker Desktop 启动... ($i/45)" }
                }
            }
            if (-not $daemonOk) {
                if (-not $launched) {
                    [void]$missing.Add("Docker Desktop 未安装或引擎未运行（docker info 失败）")
                    [void]$howto.Add("一键安装: .\install_windows.ps1 bootstrap")
                    [void]$howto.Add("或下载: https://www.docker.com/products/docker-desktop")
                } else {
                    [void]$missing.Add("Docker Desktop 引擎未运行（docker info 失败）")
                    [void]$howto.Add("请手动打开 Docker Desktop，等待托盘图标显示 Running 后重试")
                }
                if (-not (Test-WslInstalled)) {
                    [void]$howto.Add("本机尚未就绪 WSL2，请先: wsl --install  （完成后重启）")
                }
            }
        }
    }

    # 3) Compose
    if ($dockerCliOk) {
        $composeOk = $false
        try {
            docker compose version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Ok ("Docker Compose: " + ((docker compose version --short 2>$null) -join ""))
                $composeOk = $true
            }
        } catch { }
        if (-not $composeOk) {
            $dc = Get-Command docker-compose -ErrorAction SilentlyContinue
            if ($dc) {
                Write-Ok "Docker Compose: docker-compose 已安装"
                $composeOk = $true
            }
        }
        if (-not $composeOk) {
            [void]$missing.Add("Docker Compose（docker compose / docker-compose）")
            [void]$howto.Add("请升级 Docker Desktop 到较新版本（自带 Compose V2）")
        }
    }

    # 4) Git Bash / WSL
    $bashInfo = Find-Bash
    if (-not $bashInfo) {
        [void]$missing.Add("Git Bash 或 WSL（未找到 bash）")
        [void]$howto.Add("安装 Git for Windows: https://git-scm.com/download/win")
        [void]$howto.Add("或启用 WSL: wsl --install")
    } else {
        if ($bashInfo.Kind -eq "wsl") {
            Write-Ok "Shell: WSL"
        } else {
            if (Test-BashVersion4Plus $bashInfo.Path) {
                Write-Ok ("Shell: Git Bash 4+ → " + $bashInfo.Path)
            } else {
                [void]$missing.Add("Bash 4+（当前 Git Bash 版本过旧）")
                [void]$howto.Add("请升级 Git for Windows: https://git-scm.com/download/win")
                [void]$howto.Add("或改用 WSL: wsl --install")
            }
        }
    }

    if ($missing.Count -gt 0) {
        Write-Host ""
        Write-Err "前置环境不满足，已中止安装/部署"
        Write-Host ""
        Write-Host "缺少以下组件："
        foreach ($m in $missing) {
            Write-Host "  x $m"
        }
        Write-Host ""
        Write-Host "请按下列说明安装后重试："
        $n = 1
        foreach ($h in $howto) {
            Write-Host ("  {0}. {1}" -f $n, $h)
            $n++
        }
        Write-Host ""
        Write-Host "推荐一键引导安装依赖："
        Write-Host "  .\install_windows.ps1 bootstrap"
        Write-Host ""
        Write-Host "装好后可先自检："
        Write-Host "  .\install_windows.ps1 check"
        Write-Host ""
        exit 1
    }

    Write-Ok "前置环境检测通过"
    return $bashInfo
}

# ---- 解析命令：支持 bootstrap / -Bootstrap / EASYAIOT_AUTO_INSTALL_DOCKER ----
$forwardArgs = @()
if ($CommandArgs -and $CommandArgs.Count -gt 0) {
    $forwardArgs = @($CommandArgs)
} elseif ($args.Count -gt 0) {
    $forwardArgs = @($args)
}

$wantBootstrap = $Bootstrap.IsPresent
if ($forwardArgs.Count -gt 0 -and ($forwardArgs[0] -ieq "bootstrap" -or $forwardArgs[0] -ieq "deps")) {
    $wantBootstrap = $true
    if ($forwardArgs.Count -gt 1) {
        $forwardArgs = $forwardArgs[1..($forwardArgs.Count - 1)]
    } else {
        $forwardArgs = @()
    }
}
if ($env:EASYAIOT_AUTO_INSTALL_DOCKER -eq "1") {
    $wantBootstrap = $true
}

# C 盘不足：把 Docker Desktop WSL 数据迁到 E:\DockerDesktop
if ($forwardArgs.Count -gt 0 -and ($forwardArgs[0] -ieq "movedata" -or $forwardArgs[0] -ieq "move-data" -or $forwardArgs[0] -ieq "migrate-disk")) {
    $moveScript = Join-Path $ScriptDir "move_docker_data_to_e.ps1"
    if (-not (Test-Path $moveScript)) {
        Write-Err "未找到 $moveScript"
        exit 1
    }
    Write-Info "转发到 move_docker_data_to_e.ps1 ..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $moveScript
    exit $LASTEXITCODE
}

# 国内镜像加速（可在无 bash 时独立执行）
if ($forwardArgs.Count -gt 0 -and (
        $forwardArgs[0] -ieq "mirrors" -or $forwardArgs[0] -ieq "mirror" -or
        $forwardArgs[0] -ieq "registry-mirrors" -or $forwardArgs[0] -ieq "docker-mirrors"
    )) {
    Ensure-DockerOnPath | Out-Null
    exit (Update-DockerDesktopRegistryMirrors)
}

# 调配 Docker Desktop / WSL2 资源（可在无 bash 时独立执行）
if ($forwardArgs.Count -gt 0 -and (
        $forwardArgs[0] -ieq "resources" -or $forwardArgs[0] -ieq "tune" -or
        $forwardArgs[0] -ieq "tune-resources" -or $forwardArgs[0] -ieq "docker-resources"
    )) {
    $force = $false
    if ($forwardArgs.Count -gt 1 -and (
            $forwardArgs[1] -ieq "force" -or $forwardArgs[1] -eq "1" -or
            $forwardArgs[1] -ieq "-f" -or $forwardArgs[1] -ieq "--force"
        )) { $force = $true }
    Ensure-DockerOnPath | Out-Null
    if ($force) {
        exit (Invoke-ConfigureDockerResources -Force)
    } else {
        exit (Invoke-ConfigureDockerResources)
    }
}

# C 盘告警（不自动迁移，仅提示）
try {
    $cFree = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
    if ($cFree -lt 10) {
        Write-Warn ("C: 剩余仅 {0} GB。Docker 数据在 C: 时易出现 read-only / pull 失败。" -f $cFree)
        Write-Host "  建议先迁移: .\install_windows.ps1 movedata"
        Write-Host "  或:          powershell -ExecutionPolicy Bypass -File .\move_docker_data_to_e.ps1"
    }
} catch { }

if ($wantBootstrap) {
    $rc = Invoke-BootstrapDeps
    if ($rc -ne 0) { exit $rc }
    # bootstrap 且未附带后续子命令时结束
    if ($forwardArgs.Count -eq 0) { exit 0 }
}

if (-not (Test-Path $BashScript)) {
    Write-Err "未找到 $BashScript"
    exit 1
}

$bashInfo = Invoke-PrerequisiteCheck

Write-Info "使用 $($bashInfo.Kind): $($bashInfo.Path)"
Write-Info "转发到 install_windows.sh $($forwardArgs -join ' ')"

$env:EASYAIOT_FORCE_WINDOWS = "1"

# 确保 Git Bash 子进程也能找到 docker（MSYS 继承 Windows PATH）
Ensure-DockerOnPath | Out-Null

if ($bashInfo.Kind -eq "wsl") {
    $wslScript = (wsl wslpath -a "$BashScript" 2>$null)
    if (-not $wslScript) {
        Write-Err "无法将路径转换为 WSL 路径: $BashScript"
        exit 1
    }
    if ($forwardArgs.Count -gt 0) {
        & wsl bash "$wslScript" @forwardArgs
    } else {
        & wsl bash "$wslScript"
    }
} else {
    if ($forwardArgs.Count -gt 0) {
        & $bashInfo.Path "$BashScript" @forwardArgs
    } else {
        & $bashInfo.Path "$BashScript"
    }
}

exit $LASTEXITCODE
