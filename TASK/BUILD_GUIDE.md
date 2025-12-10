# 🔨 TASK模块 编译指南

## 📋 第1步完成清单

✅ **已完成的文件：**
- [x] `src/main.cpp` - 程序入口
- [x] `src/ConfigParser.h` - 配置解析器头文件
- [x] `src/ConfigParser.cpp` - 配置解析器实现
- [x] `src/AlarmCallback.h` - HTTP回调头文件
- [x] `src/AlarmCallback.cpp` - HTTP回调实现
- [x] `config/config.example.ini` - 配置文件示例
- [x] `CMakeLists.txt` - 更新编译配置

---

## 🚀 编译步骤（Windows）

### 方式1：使用 vcpkg（推荐）

```powershell
# 1. 进入TASK目录
cd F:\EASYLOT\easyaiot-main\TASK

# 2. 创建build目录
mkdir build
cd build

# 3. 配置CMake（使用vcpkg工具链）
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake -G "Visual Studio 17 2022" -A x64

# 4. 编译
cmake --build . --config Release

# 5. 可执行文件位置
# build\Release\TASK.exe
```

### 方式2：如果还没安装vcpkg

```powershell
# 第一次需要先安装vcpkg
cd C:\
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg integrate install

# 安装依赖库（这一步需要时间，约1-2小时）
.\vcpkg install opencv4:x64-windows
.\vcpkg install onnxruntime-gpu:x64-windows  # 或 onnxruntime:x64-windows (CPU版本)
.\vcpkg install ffmpeg:x64-windows
.\vcpkg install glog:x64-windows
.\vcpkg install jsoncpp:x64-windows
.\vcpkg install curl:x64-windows

# 然后回到TASK目录编译
cd F:\EASYLOT\easyaiot-main\TASK
mkdir build
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
```

---

## 🧪 测试运行

### 1. 准备配置文件

```powershell
# 复制示例配置
cd F:\EASYLOT\easyaiot-main\TASK
mkdir config
copy config\config.example.ini config\test.ini

# 编辑 config\test.ini，修改以下内容：
# - rtsp_url: 您的RTSP摄像头地址
# - model_path: YOLOv11 ONNX模型路径
# - hook_url: AI模块回调地址
```

### 2. 运行TASK模块

```powershell
cd build\Release

# 运行
.\TASK.exe ..\..\config\test.ini

# 预期输出：
# ╔════════════════════════════════════════════════════════╗
# ║     ████████╗ █████╗ ███████╗██╗  ██╗                ║
# ║     ...                                                ║
# ╚════════════════════════════════════════════════════════╝
# 
# ✅ 配置文件解析成功
# 📋 配置信息:
#   • RTSP URL: rtsp://...
#   • 线程数量: 3
#   • AI推理: 启用
# ...
```

---

## ⚠️ 可能遇到的问题

### 问题1：找不到DLL

**错误**：无法启动此程序，因为计算机中丢失 opencv_world480.dll

**解决**：
```powershell
# 将所有DLL复制到TASK.exe同目录
cd build\Release

# 从vcpkg复制DLL
copy C:\vcpkg\installed\x64-windows\bin\*.dll .

# 或者添加到PATH（推荐）
$env:PATH += ";C:\vcpkg\installed\x64-windows\bin"
```

### 问题2：CMake找不到库

**错误**：Could not find OpenCV

**解决**：
```powershell
# 确保vcpkg integrate install已执行
cd C:\vcpkg
.\vcpkg integrate install

# 确保使用正确的工具链文件
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
```

### 问题3：编译错误

**错误**：C++语法错误

**解决**：
```powershell
# 确保使用C++17
# 查看CMakeLists.txt中的 set(CMAKE_CXX_STANDARD 17)

# 或者指定编译器
cmake .. -DCMAKE_CXX_COMPILER="C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.xx/bin/Hostx64/x64/cl.exe"
```

---

## 📊 编译完成检查

✅ **编译成功标志：**

```
build\Release\TASK.exe  (约5-10MB)
```

✅ **运行成功标志：**

```
🎉 系统运行中... 按 Ctrl+C 退出
```

---

## 🎯 下一步

编译成功后，请告诉我：

1. ✅ 编译是否成功？
2. ✅ 能否正常运行？
3. ✅ 是否能连接RTSP流？

**然后我们进入第2步：AI模块集成代码！**
