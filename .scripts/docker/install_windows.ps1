#Requires -Version 5.0
<#
.SYNOPSIS
  EasyAIoT Windows 镜像部署入口（PowerShell）

.DESCRIPTION
  先汇总检测 Docker Desktop / Compose / Git Bash（或 WSL），
  缺什么就提示装什么并中止；全部通过后再转发到 install_windows.sh。
  仅支持拉取预构建镜像部署，不支持本地编译。

.EXAMPLE
  .\install_windows.ps1
  .\install_windows.ps1 check
  .\install_windows.ps1 install
  .\install_windows.ps1 pull
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BashScript = Join-Path $ScriptDir "install_windows.sh"

function Write-Info($msg)  { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]  $msg" -ForegroundColor Red }

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
        return @{ Kind = "wsl"; Path = "wsl" }
    }
    return $null
}

function Test-BashVersion4Plus([string]$BashPath) {
    try {
        $out = & $BashPath -c 'echo ${BASH_VERSINFO[0]}' 2>$null
        if ($LASTEXITCODE -ne 0) { return $false }
        $major = 0
        [int]::TryParse(($out | Select-Object -First 1).ToString().Trim(), [ref]$major) | Out-Null
        return ($major -ge 4)
    } catch {
        return $false
    }
}

function Find-DockerDesktopExe {
    return @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
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
    try {
        docker info 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Invoke-PrerequisiteCheck {
    $missing = New-Object System.Collections.Generic.List[string]
    $howto = New-Object System.Collections.Generic.List[string]

    Write-Host ""
    Write-Host "======== 前置环境检测（Windows）========" -ForegroundColor Yellow

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
        [void]$howto.Add("下载安装 Docker Desktop: https://www.docker.com/products/docker-desktop")
        [void]$howto.Add("安装时建议勾选 WSL2 后端；装完后重启终端再执行本脚本")
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
                    [void]$howto.Add("下载安装 Docker Desktop: https://www.docker.com/products/docker-desktop")
                } else {
                    [void]$missing.Add("Docker Desktop 引擎未运行（docker info 失败）")
                    [void]$howto.Add("请手动打开 Docker Desktop，等待托盘图标显示 Running 后重试")
                }
                [void]$howto.Add("安装地址: https://www.docker.com/products/docker-desktop")
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
        Write-Host "装好后可先自检："
        Write-Host "  .\install_windows.ps1 check"
        Write-Host ""
        exit 1
    }

    Write-Ok "前置环境检测通过"
    return $bashInfo
}

if (-not (Test-Path $BashScript)) {
    Write-Err "未找到 $BashScript"
    exit 1
}

$bashInfo = Invoke-PrerequisiteCheck

# 转发参数（默认进入交互菜单）
$forwardArgs = @()
if ($args.Count -gt 0) {
    $forwardArgs = $args
}

Write-Info "使用 $($bashInfo.Kind): $($bashInfo.Path)"
Write-Info "转发到 install_windows.sh $($forwardArgs -join ' ')"

$env:EASYAIOT_FORCE_WINDOWS = "1"

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
