@echo off
REM Windows环境下使用ffmpeg将本地视频文件推送到SRS服务器
REM 使用方法: 
REM   默认执行: push_video_to_srs.bat
REM   位置参数: push_video_to_srs.bat [SRS主机] [流名] [端口] [应用名] [视频文件] [ffmpeg路径] [NoLoop] [ReEncode]
REM   示例: push_video_to_srs.bat 192.168.1.200 camera01
REM         push_video_to_srs.bat 192.168.1.200 camera01 1935 live video.mp4

REM 设置代码页为UTF-8以正确显示中文
chcp 65001 >nul 2>&1

setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM 参数解析
set SRS_HOST=%1
set STREAM=%2
set SRS_PORT=%3
set APP=%4
set VIDEO_FILE=%5
set FFMPEG_PATH=%6
set NO_LOOP=%7
set RE_ENCODE=%8

REM 设置默认值
if "%SRS_HOST%"=="" set SRS_HOST=127.0.0.1
if "%SRS_PORT%"=="" set SRS_PORT=1935
if "%APP%"=="" set APP=live
if "%STREAM%"=="" set STREAM=test
if "%FFMPEG_PATH%"=="" set FFMPEG_PATH=ffmpeg

REM 设置默认视频文件路径（在脚本同级目录查找）
if "%VIDEO_FILE%"=="" (
    set "FOUND_VIDEO="
    
    REM 查找视频文件
    for %%e in (mp4 avi mov mkv flv wmv webm m4v) do (
        if exist "%SCRIPT_DIR%\*.%%e" (
            for %%f in ("%SCRIPT_DIR%\*.%%e") do (
                set "FOUND_VIDEO=%%~f"
                goto :found_video
            )
        )
    )
    
    :found_video
    if "!FOUND_VIDEO!"=="" (
        echo 错误: 在脚本同级目录未找到视频文件
        echo 脚本目录: %SCRIPT_DIR%
        echo 支持的视频格式: mp4, avi, mov, mkv, flv, wmv, webm, m4v
        echo 请将视频文件放在脚本同级目录，或使用参数指定视频文件路径
        exit /b 1
    )
    
    set "VIDEO_FILE=!FOUND_VIDEO!"
) else (
    REM 如果用户提供的路径是相对路径，则相对于脚本目录
    echo %VIDEO_FILE%| findstr /r "^[A-Za-z]:\\" >nul
    if %ERRORLEVEL% neq 0 (
        set "VIDEO_FILE=%SCRIPT_DIR%\%VIDEO_FILE%"
    )
)

REM 检查视频文件是否存在
if not exist "%VIDEO_FILE%" (
    echo 错误: 视频文件不存在: %VIDEO_FILE%
    echo 请检查文件路径是否正确，或使用参数指定视频文件路径
    exit /b 1
)

REM 检查ffmpeg是否可用
"%FFMPEG_PATH%" -version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 无法找到ffmpeg，请确保ffmpeg已安装并添加到PATH环境变量中
    echo 或者使用参数指定ffmpeg的完整路径，例如: push_video_to_srs.bat %SRS_HOST% %STREAM% %SRS_PORT% %APP% %VIDEO_FILE% "C:\ffmpeg\bin\ffmpeg.exe"
    exit /b 1
)

REM 显示ffmpeg版本信息
for /f "tokens=*" %%i in ('"%FFMPEG_PATH%" -version 2^>^&1 ^| findstr /i "ffmpeg version"') do (
    echo 检测到ffmpeg: %%i
)

REM 构建RTMP推流地址
set RTMP_URL=rtmp://%SRS_HOST%:%SRS_PORT%/%APP%/%STREAM%

REM 显示视频文件路径（如果是脚本目录下的文件，显示相对路径）
set "VIDEO_FILE_DISPLAY=%VIDEO_FILE%"
echo %VIDEO_FILE%| findstr /c:"%SCRIPT_DIR%" >nul
if %ERRORLEVEL% equ 0 (
    set "VIDEO_FILE_DISPLAY=!VIDEO_FILE:%SCRIPT_DIR%\=!"
)

echo ========================================
echo 视频文件推流到SRS配置
echo ========================================
echo 视频文件: %VIDEO_FILE_DISPLAY%
echo SRS服务器: %SRS_HOST%:%SRS_PORT%
echo 应用名称: %APP%
echo 流名称: %STREAM%
echo RTMP推流地址: %RTMP_URL%
if "%NO_LOOP%"=="" (
    echo 循环播放: 是
) else (
    echo 循环播放: 否
)
if "%RE_ENCODE%"=="" (
    echo 编码模式: 复制（copy）
) else (
    echo 编码模式: 重新编码
)
echo ========================================
echo.

echo 开始推流...
echo 按 Ctrl+C 停止推流
echo.

REM 构建ffmpeg命令
set "FFMPEG_CMD=%FFMPEG_PATH% -loglevel info"

REM 添加循环播放参数
if "%NO_LOOP%"=="" (
    set "FFMPEG_CMD=!FFMPEG_CMD! -stream_loop -1"
)

REM 添加输入选项
set "FFMPEG_CMD=!FFMPEG_CMD! -re -i "%VIDEO_FILE%""

REM 添加编码参数
if "%RE_ENCODE%"=="" (
    echo 使用copy模式（性能更好，但需要编码格式兼容）
    echo FFmpeg命令参数:
    echo   -c:v copy -c:a copy
    echo   -f flv -fflags nobuffer -flags low_delay
    echo.
    set "FFMPEG_CMD=!FFMPEG_CMD! -c:v copy -c:a copy"
) else (
    echo 使用重新编码模式（兼容性更好，但CPU占用更高）
    echo FFmpeg命令参数:
    echo   -c:v libx264 -preset ultrafast -tune zerolatency
    echo   -c:a aac -b:a 128k
    echo   -f flv -fflags nobuffer -flags low_delay
    echo.
    set "FFMPEG_CMD=!FFMPEG_CMD! -c:v libx264 -preset ultrafast -tune zerolatency -c:a aac -b:a 128k"
)

REM 添加输出参数
set "FFMPEG_CMD=!FFMPEG_CMD! -f flv -fflags nobuffer -flags low_delay -flvflags no_duration_filesize "%RTMP_URL%""

REM 显示执行的命令（用于调试）
echo 执行命令: !FFMPEG_CMD!
echo.

REM 执行ffmpeg推流命令
!FFMPEG_CMD!
set EXIT_CODE=%ERRORLEVEL%

REM 检查退出码
if %EXIT_CODE% neq 0 (
    echo.
    echo 推流失败，退出码: %EXIT_CODE%
    echo.
    echo 可能的原因:
    echo   1. 视频文件格式不支持或已损坏
    echo   2. SRS服务器未运行或地址不正确
    echo   3. 网络连接问题（防火墙、端口阻塞）
    echo   4. 视频编码格式不兼容（H.265、G.711等，可能需要重新编码）
    echo.
    echo 故障排查建议:
    echo   1. 检查视频文件是否可播放: 使用VLC或其他播放器测试
    echo   2. 检查SRS服务器状态: 访问 http://%SRS_HOST%:1985/api/v1/streams/
    echo   3. 检查网络连接: ping %SRS_HOST%
    echo   4. 尝试使用重新编码模式: 添加 ReEncode 参数
    echo      示例: push_video_to_srs.bat %SRS_HOST% %STREAM% %SRS_PORT% %APP% %VIDEO_FILE% %FFMPEG_PATH% %NO_LOOP% ReEncode
    echo   5. 查看FFmpeg详细日志（已启用info模式）
    echo.
    exit /b %EXIT_CODE%
) else (
    echo.
    echo 推流已停止
)

endlocal
