# ============================================
# WEB服务 Docker Compose 管理脚本 (Windows)
# ============================================
# 使用方法：
#   .\install_win.ps1 [命令]
#
# 可用命令：
#   install    - 安装并启动服务（首次运行）
#   start      - 启动服务
#   stop       - 停止服务
#   restart    - 重启服务
#   status     - 查看服务状态
#   logs       - 查看服务日志
#   build      - 重新构建镜像
#   clean      - 清理容器和镜像
#   update     - 更新并重启服务
#   build-frontend - 构建前端项目
# ============================================

$ErrorActionPreference = "Stop"

# 颜色定义
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 脚本目录
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# 检查 Docker 是否安装
function Test-Docker {
    if (-not (Test-Command "docker")) {
        Write-Error "Docker 未安装，请先安装 Docker Desktop"
        Write-Host "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    }
    $version = docker --version
    Write-Success "Docker 已安装: $version"
}

# 检查 Docker Compose 是否安装
function Test-DockerCompose {
    if (-not (Test-Command "docker-compose") -and -not (docker compose version 2>&1 | Out-Null; $LASTEXITCODE -eq 0)) {
        Write-Error "Docker Compose 未安装，请先安装 Docker Compose"
        Write-Host "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    }
    
    if (Test-Command "docker-compose") {
        $script:COMPOSE_CMD = "docker-compose"
        $version = docker-compose --version
        Write-Success "Docker Compose 已安装: $version"
    } else {
        $script:COMPOSE_CMD = "docker compose"
        $version = docker compose version
        Write-Success "Docker Compose 已安装: $version"
    }
}

# 获取占用端口的进程PID
function Get-PortPids {
    param([int]$Port)
    $pids = @()
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            if ($conn.OwningProcess -and $conn.OwningProcess -notin $pids) {
                $pids += $conn.OwningProcess
            }
        }
    } catch {
        # 如果Get-NetTCPConnection不可用，使用netstat
        $netstat = netstat -ano | Select-String ":$Port "
        foreach ($line in $netstat) {
            $parts = $line -split '\s+'
            if ($parts[-1] -match '^\d+$') {
                $pid = [int]$parts[-1]
                if ($pid -notin $pids) {
                    $pids += $pid
                }
            }
        }
    }
    
    return $pids
}

# 处理端口占用
function Handle-PortConflict {
    param([int]$Port)
    
    Write-Warning "端口 $Port 已被占用"
    Write-Info "占用端口的进程信息:"
    
    $pids = Get-PortPids -Port $Port
    
    foreach ($pid in $pids) {
        try {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "  PID: $pid, 进程名: $($process.ProcessName), 路径: $($process.Path)"
            }
        } catch {
            Write-Host "  PID: $pid (无法获取详细信息)"
        }
    }
    
    if ($pids.Count -eq 0) {
        Write-Warning "无法自动获取占用端口的进程PID（可能需要管理员权限）"
        Write-Info "请手动停止占用端口的进程，或修改 .env 文件中的 WEB_PORT 配置"
        return $false
    }
    
    Write-Host ""
    Write-Info "检测到以下进程占用端口: $($pids -join ', ')"
    Write-Host ""
    Write-Info "请选择处理方式:"
    Write-Host "  1) 自动 - 自动kill占用端口的进程"
    Write-Host "  2) 手动 - 手动处理（脚本退出）"
    Write-Host "  3) 停止 - 停止脚本执行"
    Write-Host ""
    $choice = Read-Host "请输入选项 (1/2/3，默认: 2)"
    
    if ([string]::IsNullOrEmpty($choice)) {
        $choice = "2"
    }
    
    switch ($choice) {
        "1" {
            Write-Info "正在kill占用端口的进程..."
            $killedCount = 0
            $failedCount = 0
            
            foreach ($pid in $pids) {
                try {
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                        if ($?) {
                            Write-Info "已终止进程 $pid"
                            $killedCount++
                        } else {
                            Write-Error "无法kill进程 $pid（可能需要管理员权限）"
                            $failedCount++
                        }
                    }
                } catch {
                    Write-Error "无法kill进程 $pid: $_"
                    $failedCount++
                }
            }
            
            Start-Sleep -Seconds 1
            
            # 再次检查端口是否释放
            $remainingPids = Get-PortPids -Port $Port
            if ($remainingPids.Count -eq 0) {
                Write-Success "端口 $Port 已释放"
                return $true
            } else {
                if ($failedCount -gt 0) {
                    Write-Error "部分进程kill失败，端口可能仍被占用"
                    Write-Info "请手动处理或修改 .env 文件中的 WEB_PORT 配置"
                } else {
                    Write-Warning "端口可能仍被占用，请稍后重试或手动检查"
                }
                return $false
            }
        }
        "2" {
            Write-Info "请手动停止占用端口的进程，或修改 .env 文件中的 WEB_PORT 配置"
            Write-Info "占用端口的进程PID: $($pids -join ', ')"
            Write-Info "可以使用以下命令kill进程: Stop-Process -Id $($pids -join ',') -Force"
            return $false
        }
        "3" {
            Write-Info "已取消操作"
            exit 0
        }
        default {
            Write-Error "无效选项，已取消操作"
            return $false
        }
    }
}

# 检查端口是否被占用
function Test-Port {
    param([int]$Port = 0)
    
    if ($Port -eq 0) {
        # 从.env文件读取端口，如果没有则使用默认值8888
        if (Test-Path ".env") {
            $envContent = Get-Content ".env" | Where-Object { $_ -match "^WEB_PORT=" }
            if ($envContent) {
                $Port = [int]($envContent -replace "WEB_PORT=", "" -replace '"', '' -replace "'", '').Trim()
            }
        }
        if ($Port -eq 0) {
            $Port = 8888
        }
    }
    
    # 检查端口是否被占用
    $portInUse = $false
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($connections) {
            $portInUse = $true
        }
    } catch {
        # 如果Get-NetTCPConnection不可用，使用netstat
        $netstat = netstat -ano | Select-String ":$Port "
        if ($netstat) {
            $portInUse = $true
        }
    }
    
    if ($portInUse) {
        return Handle-PortConflict -Port $Port
    }
    
    return $true
}

# 创建必要的目录
function New-Directories {
    Write-Info "创建必要的目录..."
    @("conf", "logs", "conf/ssl", "dist") | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }
    Write-Success "目录创建完成"
}

# 创建 .env 文件
function New-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Info ".env 文件不存在，正在创建..."
        if (Test-Path "env.example") {
            Copy-Item "env.example" ".env"
            Write-Success ".env 文件已从 env.example 创建"
            Write-Warning "请编辑 .env 文件，配置端口等参数"
        } else {
            Write-Error "env.example 文件不存在，无法创建 .env 文件"
            exit 1
        }
    } else {
        Write-Info ".env 文件已存在"
    }
}

# 检查并切换 npm 源为国内源
function Test-NpmRegistry {
    if (-not (Test-Command "npm")) {
        return $true  # npm 不存在，跳过检查
    }
    
    # 获取当前 npm 源
    $currentRegistry = npm config get registry 2>&1
    if ($LASTEXITCODE -ne 0) {
        $currentRegistry = ""
    }
    
    # 国内源列表
    $domesticRegistries = @(
        "https://registry.npmmirror.com",
        "https://registry.npm.taobao.org"
    )
    
    # 检查是否为国内源
    $isDomestic = $false
    foreach ($registry in $domesticRegistries) {
        if ($currentRegistry -eq $registry -or $currentRegistry -eq "$registry/") {
            $isDomestic = $true
            break
        }
    }
    
    # 如果不是国内源，切换为国内源
    if (-not $isDomestic) {
        Write-Warning "当前 npm 源: $currentRegistry"
        $response = Read-Host "检测到非国内源，是否切换为国内源（淘宝镜像）？(Y/n)"
        if ($response -notmatch "^[nN]") {
            Write-Info "正在切换 npm 源为国内源..."
            $result = npm config set registry https://registry.npmmirror.com 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "npm 源已切换为: https://registry.npmmirror.com"
            } else {
                Write-Error "npm 源切换失败"
                return $false
            }
        } else {
            Write-Info "保持当前 npm 源: $currentRegistry"
        }
    } else {
        Write-Info "当前 npm 源已是国内源: $currentRegistry"
    }
    
    return $true
}

# 安装 pnpm
function Install-Pnpm {
    Write-Info "正在安装 pnpm..."
    
    if (-not (Test-Command "npm")) {
        Write-Error "npm 未安装，无法安装 pnpm，请先安装 Node.js"
        exit 1
    }
    
    $result = npm install -g pnpm 2>&1
    if ($LASTEXITCODE -eq 0) {
        $version = pnpm --version
        Write-Success "pnpm 安装成功: $version"
        return $true
    } else {
        Write-Error "pnpm 安装失败"
        return $false
    }
}

# 构建前端项目（在宿主机上，可选，主要用于测试）
function Build-Frontend {
    Write-Warning "注意：前端构建现在在Docker容器内自动完成"
    Write-Info "此命令仅用于在宿主机上测试构建，不影响Docker部署"
    Write-Info "开始构建前端项目..."
    
    if (-not (Test-Command "node")) {
        Write-Error "Node.js 未安装，请先安装 Node.js"
        Write-Host "安装指南: https://nodejs.org/"
        exit 1
    }
    
    # 检查并切换 npm 源为国内源
    Test-NpmRegistry | Out-Null
    
    # 检查 pnpm
    $packageManager = ""
    if (-not (Test-Command "pnpm")) {
        Write-Warning "pnpm 未安装"
        $response = Read-Host "是否自动安装 pnpm？(y/N)"
        if ($response -match "^[yY]") {
            if (Install-Pnpm) {
                $packageManager = "pnpm"
            } else {
                Write-Warning "pnpm 安装失败，尝试使用 npm..."
                if (-not (Test-Command "npm")) {
                    Write-Error "npm 未安装，请先安装 Node.js"
                    exit 1
                }
                $packageManager = "npm"
            }
        } else {
            Write-Info "跳过 pnpm 安装，尝试使用 npm..."
            if (-not (Test-Command "npm")) {
                Write-Error "npm 未安装，请先安装 Node.js"
                exit 1
            }
            $packageManager = "npm"
        }
    } else {
        $packageManager = "pnpm"
    }
    
    Write-Info "使用包管理器: $packageManager"
    
    # 安装依赖
    if (-not (Test-Path "node_modules")) {
        Write-Info "安装依赖..."
        if ($packageManager -eq "pnpm") {
            pnpm install
        } else {
            npm install
        }
    }
    
    # 构建项目
    Write-Info "构建前端项目..."
    if ($packageManager -eq "pnpm") {
        pnpm build
    } else {
        npm run build
    }
    
    Write-Success "前端项目构建完成（此构建仅用于测试，Docker部署时会重新构建）"
}

# 安装服务
function Install-Service {
    Write-Info "开始安装 WEB 服务..."
    
    Test-Docker
    Test-DockerCompose
    New-Directories
    New-EnvFile
    
    # 检查端口占用
    if (-not (Test-Port)) {
        Write-Error "端口检查失败，请解决端口占用问题后重试"
        exit 1
    }
    
    # 注意：前端构建现在在Docker容器内完成，不再需要在宿主机上构建
    Write-Info "前端构建将在Docker容器内自动完成"
    
    # 确保先清理可能存在的残留容器
    Write-Info "检查并清理残留容器..."
    docker rm -f web-service 2>&1 | Out-Null
    & $COMPOSE_CMD down --remove-orphans 2>&1 | Out-Null
    
    Write-Info "构建 Docker 镜像..."
    & $COMPOSE_CMD build
    
    Write-Info "启动服务..."
    & $COMPOSE_CMD up -d
    
    Write-Success "服务安装完成！"
    Write-Info "等待服务启动..."
    Start-Sleep -Seconds 3
    
    # 检查服务状态
    Get-Status
    
    # 读取端口配置
    $webPort = 8888
    if (Test-Path ".env") {
        $envContent = Get-Content ".env" | Where-Object { $_ -match "^WEB_PORT=" }
        if ($envContent) {
            $webPort = [int]($envContent -replace "WEB_PORT=", "" -replace '"', '' -replace "'", '').Trim()
        }
    }
    Write-Info "服务访问地址: http://localhost:$webPort"
    Write-Info "健康检查地址: http://localhost:$webPort/health"
    Write-Info "查看日志: .\install_win.ps1 logs"
}

# 启动服务
function Start-Service {
    Write-Info "启动服务..."
    Test-Docker
    Test-DockerCompose
    
    if (-not (Test-Path ".env")) {
        Write-Warning ".env 文件不存在，正在创建..."
        New-EnvFile
    }
    
    # 检查端口占用
    if (-not (Test-Port)) {
        Write-Error "端口检查失败，请解决端口占用问题后重试"
        exit 1
    }
    
    & $COMPOSE_CMD up -d
    Write-Success "服务已启动"
    Get-Status
}

# 停止服务
function Stop-Service {
    Write-Info "停止服务..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD down
    Write-Success "服务已停止"
}

# 重启服务
function Restart-Service {
    Write-Info "重启服务..."
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD restart
    Write-Success "服务已重启"
    Get-Status
}

# 查看服务状态
function Get-Status {
    Write-Info "服务状态:"
    Test-Docker
    Test-DockerCompose
    
    & $COMPOSE_CMD ps
    
    Write-Host ""
    Write-Info "容器健康状态:"
    $containers = docker ps --filter "name=web-service" --format "{{.Names}}" 2>&1
    if ($containers -contains "web-service") {
        docker ps --filter "name=web-service" --format "table {{.Names}}`t{{.Status}}" 2>&1
        
        $health = docker inspect --format='{{.State.Health.Status}}' web-service 2>&1
        if ($health -and $health -ne "N/A") {
            Write-Host "健康状态: $health"
        }
    } else {
        Write-Warning "服务未运行"
    }
}

# 查看日志
function Get-Logs {
    param([string]$Follow = "")
    Test-Docker
    Test-DockerCompose
    
    if ($Follow -eq "-f" -or $Follow -eq "--follow") {
        Write-Info "实时查看日志（按 Ctrl+C 退出）..."
        & $COMPOSE_CMD logs -f
    } else {
        Write-Info "查看最近日志..."
        & $COMPOSE_CMD logs --tail=100
    }
}

# 构建镜像
function Build-Image {
    Write-Info "重新构建 Docker 镜像..."
    Test-Docker
    Test-DockerCompose
    
    # 注意：前端构建现在在Docker容器内完成，构建镜像时会自动完成
    Write-Info "前端构建将在Docker容器内自动完成"
    
    & $COMPOSE_CMD build --no-cache
    Write-Success "镜像构建完成"
}

# 清理服务
function Clear-Service {
    Test-Docker
    Test-DockerCompose
    
    $response = Read-Host "这将删除容器、镜像和数据卷，确定要继续吗？(y/N)"
    
    if ($response -match "^[yY]") {
        Write-Info "停止并删除容器..."
        & $COMPOSE_CMD down -v --remove-orphans
        
        # 强制删除容器（即使已停止）
        Write-Info "强制删除残留容器..."
        docker rm -f web-service 2>&1 | Out-Null
        
        Write-Info "删除镜像..."
        docker rmi web-service:latest 2>&1 | Out-Null
        
        Write-Success "清理完成"
    } else {
        Write-Info "已取消清理操作"
    }
}

# 更新服务
function Update-Service {
    Write-Info "更新服务..."
    Test-Docker
    Test-DockerCompose
    
    Write-Info "拉取最新代码..."
    $result = git pull 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Git pull 失败，继续使用当前代码"
    }
    
    # 注意：前端构建现在在Docker容器内完成，重新构建镜像时会自动完成
    Write-Info "重新构建镜像（前端构建将在容器内自动完成）..."
    & $COMPOSE_CMD build
    
    Write-Info "重启服务..."
    & $COMPOSE_CMD up -d
    
    Write-Success "服务更新完成"
    Get-Status
}

# 显示帮助信息
function Show-Help {
    Write-Host "WEB服务 Docker Compose 管理脚本"
    Write-Host ""
    Write-Host "使用方法:"
    Write-Host "  .\install_win.ps1 [命令]"
    Write-Host ""
    Write-Host "可用命令:"
    Write-Host "  install         - 安装并启动服务（首次运行）"
    Write-Host "  start           - 启动服务"
    Write-Host "  stop            - 停止服务"
    Write-Host "  restart         - 重启服务"
    Write-Host "  status          - 查看服务状态"
    Write-Host "  logs            - 查看服务日志"
    Write-Host "  logs -f         - 实时查看服务日志"
    Write-Host "  build           - 重新构建镜像（前端构建在容器内自动完成）"
    Write-Host "  build-frontend  - 在宿主机上构建前端项目（可选，用于测试）"
    Write-Host "  clean           - 清理容器和镜像"
    Write-Host "  update          - 更新并重启服务"
    Write-Host "  help            - 显示此帮助信息"
    Write-Host ""
}

# 主函数
function Main {
    param([string]$Command = "help", [string]$Arg = "")
    
    switch ($Command.ToLower()) {
        "install" {
            Install-Service
        }
        "start" {
            Start-Service
        }
        "stop" {
            Stop-Service
        }
        "restart" {
            Restart-Service
        }
        "status" {
            Get-Status
        }
        "logs" {
            Get-Logs -Follow $Arg
        }
        "build" {
            Build-Image
        }
        "build-frontend" {
            Build-Frontend
        }
        "clean" {
            Clear-Service
        }
        "update" {
            Update-Service
        }
        { $_ -in @("help", "--help", "-h") } {
            Show-Help
        }
        default {
            Write-Error "未知命令: $Command"
            Write-Host ""
            Show-Help
            exit 1
        }
    }
}

# 运行主函数
$command = if ($args.Count -gt 0) { $args[0] } else { "help" }
$arg = if ($args.Count -gt 1) { $args[1] } else { "" }
Main -Command $command -Arg $arg

