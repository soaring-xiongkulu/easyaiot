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
  或设置环境变量后重试：
    $env:EASYAIOT_AUTO_INSTALL_DOCKER = "1"; .\install_windows.ps1 install

.EXAMPLE
  .\install_windows.cmd
  .\install_windows.cmd check
  .\install_windows.cmd install
  .\install_windows.cmd bootstrap

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
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { return $false }
    return ((Invoke-NativeExitCode { & docker info }) -eq 0)
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
        Write-Ok "依赖已就绪，可继续: .\install_windows.ps1 install"
        return 0
    }
    if ($dockerOk -and -not (Test-DockerDaemonReady)) {
        Write-Warn "Docker 已安装但引擎未就绪。请打开 Docker Desktop，待 Running 后执行:"
        Write-Host "  .\install_windows.ps1 check"
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
