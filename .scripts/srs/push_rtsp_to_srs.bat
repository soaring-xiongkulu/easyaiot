@echo off
REM Windows环境下使用ffmpeg将RTSP流推送到SRS服务器
REM 使用方法: push_rtsp_to_srs.bat rtsp://192.168.1.100:554/stream 192.168.1.200 1935 live test

REM 设置代码页为UTF-8以正确显示中文
chcp 65001 >nul 2>&1

setlocal enabledelayedexpansion

REM 参数解析
set RTSP_URL=%1
set SRS_HOST=%2
set SRS_PORT=%3
set APP=%4
set STREAM=%5

REM 默认值
if "%RTSP_URL%"=="" (
    echo 错误: 缺少RTSP源地址参数
    echo.
    echo 使用方法:
    echo   push_rtsp_to_srs.bat ^<RTSP地址^> [SRS主机] [SRS端口] [应用名] [流名]
    echo.
    echo 示例:
    echo   push_rtsp_to_srs.bat rtsp://192.168.1.100:554/stream
    echo   push_rtsp_to_srs.bat rtsp://192.168.1.100:554/stream 192.168.1.200 1935 live test
    echo.
    exit /b 1
)

if "%SRS_HOST%"=="" set SRS_HOST=127.0.0.1
if "%SRS_PORT%"=="" set SRS_PORT=1935
if "%APP%"=="" set APP=live
if "%STREAM%"=="" set STREAM=test

REM 检查ffmpeg是否可用
where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 无法找到ffmpeg，请确保ffmpeg已安装并添加到PATH环境变量中
    echo 或者修改脚本中的ffmpeg路径
    exit /b 1
)

REM 构建RTMP推流地址
set RTMP_URL=rtmp://%SRS_HOST%:%SRS_PORT%/%APP%/%STREAM%

echo ========================================
echo RTSP推流到SRS配置
echo ========================================
echo RTSP源地址: %RTSP_URL%
echo SRS服务器: %SRS_HOST%:%SRS_PORT%
echo 应用名称: %APP%
echo 流名称: %STREAM%
echo RTMP推流地址: %RTMP_URL%
echo ========================================
echo.

echo 开始推流...
echo 按 Ctrl+C 停止推流
echo.

REM 执行ffmpeg推流命令
ffmpeg -rtsp_transport tcp -i "%RTSP_URL%" -c:v copy -c:a copy -f flv -re "%RTMP_URL%"

REM 检查退出码
if %ERRORLEVEL% neq 0 (
    echo.
    echo 推流失败，退出码: %ERRORLEVEL%
    echo 可能的原因:
    echo   1. RTSP源地址无法访问
    echo   2. SRS服务器未运行或地址不正确
    echo   3. 网络连接问题
    echo   4. RTSP流格式不支持（可能需要重新编码）
    exit /b %ERRORLEVEL%
) else (
    echo.
    echo 推流已停止
)

endlocal

