# ============================================
# EasyAIoT 统一安装脚本 (Windows)
# ============================================
# 使用方法：
#   .\install_win.ps1 [命令]
#
# 可用命令：
#   install    - 安装并启动所有服务（首次运行）
#   start      - 启动所有服务
#   stop       - 停止所有服务
#   restart    - 重启所有服务
#   status     - 查看所有服务状态
#   logs       - 查看服务日志
#   build      - 重新构建所有镜像
#   clean      - 清理所有容器和镜像
#   update     - 更新并重启所有服务
#   verify     - 验证所有服务是否启动成功
# ============================================

$ErrorActionPreference = "Stop"

# 颜色定义（带日志功能）
function Write-Section {
    param([string]$Section)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  $Section" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
}

# 项目根目录（从.scripts/docker回到项目根目录）
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $SCRIPT_DIR)
Set-Location $PROJECT_ROOT

# 日志文件配置
$LOG_DIR = Join-Path $SCRIPT_DIR "logs"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}
$LOG_FILE = Join-Path $LOG_DIR "install_win_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# 初始化日志文件
@"
=========================================
EasyAIoT 统一安装脚本日志
开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
命令: $($args -join ' ')
=========================================

"@ | Out-File -FilePath $LOG_FILE -Encoding utf8

# 模块列表（按依赖顺序）
$script:MODULES = @(
    ".scripts/docker"  # 基础服务（Nacos、PostgreSQL、Redis等）
    "DEVICE"           # Device服务（网关和微服务）
    "AI"               # AI服务
    "VIDEO"            # Video服务
    "WEB"              # Web前端服务
)

# 模块名称映射
$script:MODULE_NAMES = @{
    ".scripts/docker" = "基础服务"
    "DEVICE" = "Device服务"
    "AI" = "AI服务"
    "VIDEO" = "Video服务"
    "WEB" = "Web前端服务"
}

# 模块端口映射
$script:MODULE_PORTS = @{
    ".scripts/docker" = "8848"  # Nacos端口
    "DEVICE" = "48080"           # Gateway端口
    "AI" = "5000"
    "VIDEO" = "6000"
    "WEB" = "8888"
}

# 模块健康检查端点
$script:MODULE_HEALTH_ENDPOINTS = @{
    ".scripts/docker" = "/nacos/actuator/health"
    "DEVICE" = "/actuator/health"  # Gateway健康检查
    "AI" = "/actuator/health"
    "VIDEO" = "/actuator/health"
    "WEB" = "/health"
}

# 日志输出函数
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $LOG_FILE -Value $logEntry -Encoding utf8
}

# 打印带颜色的消息（同时输出到日志文件）
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
    Write-Log "[INFO] $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
    Write-Log "[SUCCESS] $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
    Write-Log "[WARNING] $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    Write-Log "[ERROR] $Message"
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# 检查 Docker 权限
function Test-DockerPermission {
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            $errorMsg = docker info 2>&1 | Out-String
            if ($errorMsg -match "permission denied|cannot connect") {
                Write-Error "没有权限访问 Docker daemon"
                Write-Host ""
                Write-Host "解决方案："
                Write-Host "  1. 确保 Docker Desktop 正在运行"
                Write-Host "  2. 检查当前用户是否有权限访问 Docker"
                Write-Host "  3. 尝试以管理员身份运行 PowerShell"
                Write-Host ""
                exit 1
            } elseif ($errorMsg -match "Is the docker daemon running") {
                Write-Error "Docker daemon 未运行"
                Write-Host ""
                Write-Host "解决方案："
                Write-Host "  1. 启动 Docker Desktop"
                Write-Host "  2. 等待 Docker Desktop 完全启动后再运行此脚本"
                Write-Host ""
                exit 1
            } else {
                Write-Error "无法连接到 Docker daemon"
                Write-Host ""
                Write-Host "错误信息: $errorMsg"
                Write-Host ""
                Write-Host "请检查："
                Write-Host "  1. Docker Desktop 是否正在运行"
                Write-Host "  2. 当前用户是否有权限访问 Docker"
                Write-Host ""
                exit 1
            }
        }
        
        # 验证 docker ps 命令是否可用
        $null = docker ps 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker 命令执行失败"
            exit 1
        }
    } catch {
        Write-Error "Docker 检查失败: $_"
        exit 1
    }
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
    Test-DockerPermission
}

# 检查 Docker Compose 是否安装
function Test-DockerCompose {
    # 先检查 docker-compose 命令
    if (Test-Command "docker-compose") {
        $script:COMPOSE_CMD = "docker-compose"
        $version = docker-compose --version
        Write-Success "Docker Compose 已安装: $version"
        return $true
    }
    
    # 再检查 docker compose 插件
    $result = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $script:COMPOSE_CMD = "docker compose"
        # 尝试获取版本信息
        $versionOutput = docker compose version --short 2>&1
        if ($LASTEXITCODE -eq 0 -and $versionOutput -notmatch "error|unknown") {
            Write-Success "Docker Compose 已安装: $versionOutput"
        } else {
            Write-Success "Docker Compose 已安装 (docker compose 命令可用)"
        }
        return $true
    }
    
    # 如果都不存在，报错
    Write-Error "Docker Compose 未安装，请先安装 Docker Compose"
    Write-Host "安装指南: https://docs.docker.com/compose/install/"
    exit 1
}

# 创建统一网络
function New-Network {
    Write-Info "创建统一网络 easyaiot-network..."
    $networks = docker network ls --format "{{.Name}}" 2>&1
    if ($networks -notcontains "easyaiot-network") {
        $result = docker network create easyaiot-network 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "网络 easyaiot-network 已创建"
        } else {
            Write-Error "无法创建网络 easyaiot-network"
            exit 1
        }
    } else {
        Write-Info "网络 easyaiot-network 已存在"
        
        # 检测网络是否可用（尝试创建一个临时容器测试）
        $testResult = docker run --rm --network easyaiot-network alpine:latest ping -c 1 8.8.8.8 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "检测到网络 easyaiot-network 可能存在问题（可能是IP变化导致）"
            Write-Info "正在尝试重新创建网络..."
            
            # 获取连接到该网络的所有容器
            $containers = docker network inspect easyaiot-network --format '{{range .Containers}}{{.Name}} {{end}}' 2>&1
            if ($containers -and $containers -notmatch "error") {
                $containerList = $containers.Trim() -split '\s+' | Where-Object { $_ }
                if ($containerList.Count -gt 0) {
                    Write-Warning "以下容器正在使用该网络，需要先停止："
                    foreach ($container in $containerList) {
                        Write-Host "  - $container"
                    }
                    Write-Info "请先停止所有相关容器，然后重新运行安装脚本"
                    return $false
                }
            }
            
            # 删除旧网络
            docker network rm easyaiot-network 2>&1 | Out-Null
            Start-Sleep -Seconds 1
            
            # 重新创建网络
            $result = docker network create easyaiot-network 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "网络 easyaiot-network 已重新创建"
            } else {
                Write-Error "无法重新创建网络 easyaiot-network"
                return $false
            }
        } else {
            Write-Info "网络 easyaiot-network 运行正常"
        }
    }
    return $true
}

# 执行模块命令
function Invoke-ModuleCommand {
    param(
        [string]$Module,
        [string]$Command
    )
    
    $moduleName = $MODULE_NAMES[$Module]
    
    $modulePath = Join-Path $PROJECT_ROOT $Module
    if (-not (Test-Path $modulePath)) {
        Write-Warning "模块 $Module 不存在，跳过"
        return $false
    }
    
    Push-Location $modulePath
    
    try {
        # 特殊处理.scripts/docker模块（使用install_middleware_win.ps1脚本）
        if ($Module -eq ".scripts/docker") {
            $installFile = "install_middleware_win.ps1"
            if (-not (Test-Path $installFile)) {
                Write-Warning "模块 $Module 没有 $installFile 文件，跳过"
                return $false
            }
            
            Write-Info "执行 $moduleName : $Command"
            
            $output = & powershell -ExecutionPolicy Bypass -File $installFile $Command 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
            if ($LASTEXITCODE -eq 0) {
                Write-Success "$moduleName : $Command 执行成功"
                return $true
            } else {
                Write-Error "$moduleName : $Command 执行失败"
                return $false
            }
        }
        # 特殊处理DEVICE模块（使用docker-compose.yml）
        elseif ($Module -eq "DEVICE") {
            $composeFile = "docker-compose.yml"
            if (-not (Test-Path $composeFile)) {
                Write-Warning "模块 $Module 没有 $composeFile 文件，跳过"
                return $false
            }
            
            # 确定docker compose命令
            if (Test-Command "docker-compose") {
                $composeCmd = "docker-compose"
            } else {
                $composeCmd = "docker compose"
            }
            
            Write-Info "执行 $moduleName : $Command"
            
            switch ($Command.ToLower()) {
                "install" {
                    $output = & $composeCmd -f $composeFile up -d 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "$moduleName : $Command 执行成功"
                        return $true
                    } else {
                        Write-Error "$moduleName : $Command 执行失败"
                        return $false
                    }
                }
                "start" {
                    $output = & $composeCmd -f $composeFile up -d 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "$moduleName : $Command 执行成功"
                        return $true
                    } else {
                        Write-Error "$moduleName : $Command 执行失败"
                        return $false
                    }
                }
                "stop" {
                    $output = & $composeCmd -f $composeFile down 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "$moduleName : $Command 执行成功"
                        return $true
                    } else {
                        Write-Error "$moduleName : $Command 执行失败"
                        return $false
                    }
                }
                "restart" {
                    $output = & $composeCmd -f $composeFile restart 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "$moduleName : $Command 执行成功"
                        return $true
                    } else {
                        Write-Error "$moduleName : $Command 执行失败"
                        return $false
                    }
                }
                "status" {
                    & $composeCmd -f $composeFile ps 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    return $?
                }
                "logs" {
                    & $composeCmd -f $composeFile logs --tail=100 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    return $?
                }
                "build" {
                    $output = & $composeCmd -f $composeFile build --no-cache 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "$moduleName : $Command 执行成功"
                        return $true
                    } else {
                        Write-Error "$moduleName : $Command 执行失败"
                        return $false
                    }
                }
                "clean" {
                    $output = & $composeCmd -f $composeFile down -v 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "$moduleName : $Command 执行成功"
                        return $true
                    } else {
                        Write-Error "$moduleName : $Command 执行失败"
                        return $false
                    }
                }
                "update" {
                    $output1 = & $composeCmd -f $composeFile pull 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    $output2 = & $composeCmd -f $composeFile up -d 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "$moduleName : $Command 执行成功"
                        return $true
                    } else {
                        Write-Error "$moduleName : $Command 执行失败"
                        return $false
                    }
                }
                default {
                    Write-Warning "未知命令: $Command"
                    return $false
                }
            }
        }
        else {
            # 其他模块使用install_win.ps1脚本
            $installFile = "install_win.ps1"
            if (-not (Test-Path $installFile)) {
                Write-Warning "模块 $Module 没有 $installFile 脚本，跳过"
                return $false
            }
            
            Write-Info "执行 $moduleName : $Command"
            
            $output = & powershell -ExecutionPolicy Bypass -File $installFile $Command 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
            if ($LASTEXITCODE -eq 0) {
                Write-Success "$moduleName : $Command 执行成功"
                return $true
            } else {
                Write-Error "$moduleName : $Command 执行失败"
                return $false
            }
        }
    } finally {
        Pop-Location
    }
}

# 等待服务就绪
function Wait-ServiceReady {
    param(
        [string]$ServiceName,
        [string]$Port,
        [string]$HealthEndpoint
    )
    
    $maxAttempts = 60
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            if ($HealthEndpoint) {
                # 使用健康检查端点
                $response = Invoke-WebRequest -Uri "http://localhost:$Port$HealthEndpoint" -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    return $true
                }
            } else {
                # 使用端口检测
                $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
                if ($connection.TcpTestSucceeded) {
                    return $true
                }
            }
        } catch {
            # 继续尝试
        }
        
        $attempt++
        Start-Sleep -Seconds 2
    }
    
    return $false
}

# 验证服务健康状态
function Test-ServiceHealth {
    param([string]$Module)
    
    $moduleName = $MODULE_NAMES[$Module]
    $port = $MODULE_PORTS[$Module]
    $healthEndpoint = $MODULE_HEALTH_ENDPOINTS[$Module]
    
    Write-Info "验证 $moduleName (端口: $port)..."
    
    if (Wait-ServiceReady -ServiceName $moduleName -Port $port -HealthEndpoint $healthEndpoint) {
        # 检查HTTP响应
        if ($healthEndpoint) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:$Port$healthEndpoint" -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Success "$moduleName 运行正常"
                    return $true
                } else {
                    Write-Warning "$moduleName 响应异常 (HTTP $($response.StatusCode))"
                    return $false
                }
            } catch {
                Write-Warning "$moduleName 健康检查失败: $_"
                return $false
            }
        } else {
            Write-Success "$moduleName 运行正常"
            return $true
        }
    } else {
        Write-Error "$moduleName 未就绪"
        return $false
    }
}

# 安装所有服务
function Install-All {
    Write-Section "开始安装所有服务"
    
    Test-Docker
    Test-DockerCompose
    if (-not (New-Network)) {
        exit 1
    }
    
    $successCount = 0
    $totalCount = $MODULES.Count
    
    foreach ($module in $MODULES) {
        Write-Section "安装 $($MODULE_NAMES[$module])"
        if (Invoke-ModuleCommand -Module $module -Command "install") {
            $successCount++
        } else {
            Write-Error "$($MODULE_NAMES[$module]) 安装失败"
        }
        Write-Host ""
    }
    
    Write-Section "安装完成"
    Write-Host "成功安装: $successCount / $totalCount 个模块"
    
    if ($successCount -eq $totalCount) {
        Write-Success "所有模块安装成功！"
    } else {
        Write-Warning "部分模块安装失败，请检查日志"
        exit 1
    }
}

# 等待基础服务就绪
function Wait-BaseServices {
    Write-Info "等待基础服务就绪..."
    
    # 等待 PostgreSQL
    $postgresContainer = docker ps --filter "name=postgres-server" --format "{{.Names}}" 2>&1
    if ($postgresContainer -contains "postgres-server") {
        Write-Info "等待 PostgreSQL 服务就绪..."
        $maxAttempts = 60
        $attempt = 0
        while ($attempt -lt $maxAttempts) {
            $result = docker exec postgres-server pg_isready -U postgres 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "PostgreSQL 服务已就绪"
                break
            }
            $attempt++
            Start-Sleep -Seconds 2
        }
        if ($attempt -ge $maxAttempts) {
            Write-Warning "PostgreSQL 服务未在预期时间内就绪，继续执行..."
        }
    }
    
    # 等待 Nacos
    $nacosContainer = docker ps --filter "name=nacos-server" --format "{{.Names}}" 2>&1
    if ($nacosContainer -contains "nacos-server") {
        Write-Info "等待 Nacos 服务就绪..."
        $maxAttempts = 60
        $attempt = 0
        while ($attempt -lt $maxAttempts) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8848/nacos/actuator/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-Success "Nacos 服务已就绪"
                    break
                }
            } catch {
                # 继续等待
            }
            $attempt++
            Start-Sleep -Seconds 2
        }
        if ($attempt -ge $maxAttempts) {
            Write-Warning "Nacos 服务未在预期时间内就绪，继续执行..."
        }
    }
    
    # 等待 Redis
    $redisContainer = docker ps --filter "name=redis-server" --format "{{.Names}}" 2>&1
    if ($redisContainer -contains "redis-server") {
        Write-Info "等待 Redis 服务就绪..."
        $maxAttempts = 30
        $attempt = 0
        while ($attempt -lt $maxAttempts) {
            $result = docker exec redis-server redis-cli ping 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Redis 服务已就绪"
                break
            }
            $attempt++
            Start-Sleep -Seconds 1
        }
        if ($attempt -ge $maxAttempts) {
            Write-Warning "Redis 服务未在预期时间内就绪，继续执行..."
        }
    }
}

# 启动所有服务
function Start-All {
    Write-Section "启动所有服务"
    
    Test-Docker
    Test-DockerCompose
    if (-not (New-Network)) {
        exit 1
    }
    
    # 先启动基础服务（.scripts/docker）
    Write-Section "启动基础服务"
    Invoke-ModuleCommand -Module ".scripts/docker" -Command "start"
    Write-Host ""
    
    # 等待基础服务就绪
    Wait-BaseServices
    Write-Host ""
    
    # 再启动其他服务
    foreach ($module in $MODULES) {
        # 跳过基础服务（已经启动）
        if ($module -eq ".scripts/docker") {
            continue
        }
        Invoke-ModuleCommand -Module $module -Command "start"
        Write-Host ""
    }
    
    Write-Success "所有服务启动完成"
}

# 停止所有服务
function Stop-All {
    Write-Section "停止所有服务"
    
    Test-Docker
    Test-DockerCompose
    
    # 逆序停止
    for ($idx = $MODULES.Count - 1; $idx -ge 0; $idx--) {
        Invoke-ModuleCommand -Module $MODULES[$idx] -Command "stop"
        Write-Host ""
    }
    
    Write-Success "所有服务已停止"
}

# 重启所有服务
function Restart-All {
    Write-Section "重启所有服务"
    
    Test-Docker
    Test-DockerCompose
    if (-not (New-Network)) {
        exit 1
    }
    
    foreach ($module in $MODULES) {
        Invoke-ModuleCommand -Module $module -Command "restart"
        Write-Host ""
    }
    
    Write-Success "所有服务重启完成"
}

# 查看所有服务状态
function Get-AllStatus {
    Write-Section "所有服务状态"
    
    Test-Docker
    Test-DockerCompose
    
    foreach ($module in $MODULES) {
        Write-Section "$($MODULE_NAMES[$module]) 状态"
        Invoke-ModuleCommand -Module $module -Command "status"
        Write-Host ""
    }
}

# 查看日志
function Get-AllLogs {
    param([string]$Module = "")
    
    if ([string]::IsNullOrEmpty($Module)) {
        Write-Info "查看所有服务日志..."
        Test-Docker
        Test-DockerCompose
        
        foreach ($module in $MODULES) {
            Write-Section "$($MODULE_NAMES[$module]) 日志"
            Invoke-ModuleCommand -Module $module -Command "logs"
            Write-Host ""
        }
    } else {
        Write-Info "查看 $Module 服务日志..."
        Invoke-ModuleCommand -Module $Module -Command "logs"
    }
}

# 构建所有镜像
function Build-All {
    Write-Section "构建所有镜像"
    
    Test-Docker
    Test-DockerCompose
    
    foreach ($module in $MODULES) {
        Invoke-ModuleCommand -Module $module -Command "build"
        Write-Host ""
    }
    
    Write-Success "所有镜像构建完成"
}

# 清理所有服务
function Clear-All {
    $response = Read-Host "这将删除所有容器、镜像和数据卷，确定要继续吗？(y/N)"
    
    if ($response -match "^[yY]") {
        Write-Section "清理所有服务"
        
        Test-Docker
        Test-DockerCompose
        
        # 逆序清理
        for ($idx = $MODULES.Count - 1; $idx -ge 0; $idx--) {
            Invoke-ModuleCommand -Module $MODULES[$idx] -Command "clean"
            Write-Host ""
        }
        
        # 清理网络
        Write-Info "清理网络..."
        docker network rm easyaiot-network 2>&1 | Out-Null
        
        Write-Success "清理完成"
    } else {
        Write-Info "已取消清理操作"
    }
}

# 更新所有服务
function Update-All {
    Write-Section "更新所有服务"
    
    Test-Docker
    Test-DockerCompose
    if (-not (New-Network)) {
        exit 1
    }
    
    foreach ($module in $MODULES) {
        Invoke-ModuleCommand -Module $module -Command "update"
        Write-Host ""
    }
    
    Write-Success "所有服务更新完成"
}

# 验证所有服务
function Test-AllServices {
    Write-Section "验证所有服务"
    
    Test-Docker
    
    $successCount = 0
    $totalCount = $MODULES.Count
    $failedModules = @()
    
    foreach ($module in $MODULES) {
        if (Test-ServiceHealth -Module $module) {
            $successCount++
        } else {
            $failedModules += $MODULE_NAMES[$module]
        }
        Write-Host ""
    }
    
    Write-Section "验证结果"
    Write-Host "成功: $successCount / $totalCount"
    
    if ($successCount -eq $totalCount) {
        Write-Success "所有服务运行正常！"
        Write-Host ""
        Write-Host "服务访问地址:" -ForegroundColor Green
        Write-Host "  基础服务 (Nacos):     http://localhost:8848/nacos"
        Write-Host "  基础服务 (MinIO):     http://localhost:9000 (API), http://localhost:9001 (Console)"
        Write-Host "  Device服务 (Gateway):  http://localhost:48080"
        Write-Host "  AI服务:                http://localhost:5000"
        Write-Host "  Video服务:             http://localhost:6000"
        Write-Host "  Web前端:               http://localhost:8888"
        Write-Host ""
        return $true
    } else {
        Write-Warning "部分服务未就绪:"
        foreach ($failed in $failedModules) {
            Write-Host "  ✗ $failed" -ForegroundColor Red
        }
        Write-Host ""
        Write-Info "查看日志: .\install_win.ps1 logs"
        return $false
    }
}

# 显示帮助信息
function Show-Help {
    Write-Host "EasyAIoT 统一安装脚本"
    Write-Host ""
    Write-Host "使用方法:"
    Write-Host "  .\install_win.ps1 [命令] [模块]"
    Write-Host ""
    Write-Host "可用命令:"
    Write-Host "  install         - 安装并启动所有服务（首次运行）"
    Write-Host "  start           - 启动所有服务"
    Write-Host "  stop            - 停止所有服务"
    Write-Host "  restart         - 重启所有服务"
    Write-Host "  status          - 查看所有服务状态"
    Write-Host "  logs            - 查看所有服务日志"
    Write-Host "  logs [模块]     - 查看指定模块日志"
    Write-Host "  build           - 重新构建所有镜像"
    Write-Host "  clean           - 清理所有容器和镜像"
    Write-Host "  update          - 更新并重启所有服务"
    Write-Host "  verify          - 验证所有服务是否启动成功"
    Write-Host "  help            - 显示此帮助信息"
    Write-Host ""
    Write-Host "模块列表:"
    foreach ($module in $MODULES) {
        Write-Host "  - $($MODULE_NAMES[$module]) ($module)"
    }
    Write-Host ""
}

# 主函数
function Main {
    param([string]$Command = "help", [string]$Arg = "")
    
    switch ($Command.ToLower()) {
        "install" {
            Install-All
        }
        "start" {
            Start-All
        }
        "stop" {
            Stop-All
        }
        "restart" {
            Restart-All
        }
        "status" {
            Get-AllStatus
        }
        "logs" {
            Get-AllLogs -Module $Arg
        }
        "build" {
            Build-All
        }
        "clean" {
            Clear-All
        }
        "update" {
            Update-All
        }
        "verify" {
            Test-AllServices
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

# 脚本结束时记录日志文件路径
if ($LOG_FILE -and (Test-Path $LOG_FILE)) {
    @"

=========================================
脚本结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
=========================================
"@ | Out-File -FilePath $LOG_FILE -Encoding utf8 -Append
    Write-Info "日志文件已保存到: $LOG_FILE"
}

