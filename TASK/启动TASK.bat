@echo off
chcp 65001 >nul
echo ========================================
echo   启动 TASK 推流程序
echo ========================================
echo.

cd /d "%~dp0build\Release"

if not exist "TASK.exe" (
    echo ✗ TASK.exe 不存在，请先编译！
    echo.
    echo 运行以下命令编译：
    echo   cd F:\EASYLOT\easyaiot-main\TASK\build
    echo   cmake --build . --config Release
    pause
    exit /b 1
)

if not exist "..\..\config\test.ini" (
    echo ✗ 配置文件不存在：config\test.ini
    pause
    exit /b 1
)

echo 启动中...
echo 配置文件: config\test.ini
echo.

TASK.exe ..\..\config\test.ini

chcp 65001 >nul
echo ========================================
echo   启动 TASK 推流程序
echo ========================================
echo.

cd /d "%~dp0build\Release"

if not exist "TASK.exe" (
    echo ✗ TASK.exe 不存在，请先编译！
    echo.
    echo 运行以下命令编译：
    echo   cd F:\EASYLOT\easyaiot-main\TASK\build
    echo   cmake --build . --config Release
    pause
    exit /b 1
)

if not exist "..\..\config\test.ini" (
    echo ✗ 配置文件不存在：config\test.ini
    pause
    exit /b 1
)

echo 启动中...
echo 配置文件: config\test.ini
echo.

TASK.exe ..\..\config\test.ini

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 