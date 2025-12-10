@echo off
REM TASK模块 - Windows编译脚本
REM 使用方法: 直接双击运行此脚本

echo ============================================================
echo   TASK模块编译脚本
echo ============================================================
echo.

REM 设置编码为UTF-8
chcp 65001 > nul

REM 检查是否在TASK目录
if not exist "src\main.cpp" (
    echo 错误：请在TASK根目录下运行此脚本！
    pause
    exit /b 1
)

echo [1/4] 创建build目录...
if not exist "build" mkdir build
cd build

echo.
echo [2/4] 配置CMake...
echo 工具链路径: F:/EASYLOT/vcpkg-master/scripts/buildsystems/vcpkg.cmake
echo ONNX Runtime: F:/EASYLOT/onnxruntime-win-x64-gpu-1.23.1
echo.

cmake .. -DCMAKE_TOOLCHAIN_FILE=F:/EASYLOT/vcpkg-master/scripts/buildsystems/vcpkg.cmake -G "Visual Studio 17 2022" -A x64

if %errorlevel% neq 0 (
    echo.
    echo ❌ CMake配置失败！
    echo.
    echo 可能的原因：
    echo 1. Visual Studio版本不对（请改为Visual Studio 16 2019）
    echo 2. vcpkg依赖未安装完成
    echo 3. 路径配置错误
    echo.
    pause
    exit /b 1
)

echo.
echo [3/4] 开始编译...
echo 这可能需要几分钟时间，请耐心等待...
echo.

cmake --build . --config Release

if %errorlevel% neq 0 (
    echo.
    echo ❌ 编译失败！请检查错误信息。
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] 复制DLL文件...
cd Release

REM 复制vcpkg的DLL
echo 复制vcpkg DLL文件...
xcopy /Y /Q F:\EASYLOT\vcpkg-master\installed\x64-windows\bin\*.dll . 2>nul

REM 复制ONNX Runtime的DLL（1.23.1版本的DLL在lib目录）
echo 复制ONNX Runtime DLL文件...
xcopy /Y /Q F:\EASYLOT\onnxruntime-win-x64-gpu-1.23.1\lib\*.dll . 2>nul

cd ..\..

echo.
echo ============================================================
echo ✅ 编译成功！
echo ============================================================
echo.
echo 可执行文件位置:
echo   build\Release\TASK.exe
echo.
echo 下一步：
echo   1. 准备配置文件 config\test.ini
echo   2. 准备YOLO模型文件
echo   3. 运行: cd build\Release
echo   4. 运行: .\TASK.exe ..\..\config\test.ini
echo.
echo ============================================================

pause
