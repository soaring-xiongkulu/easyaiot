# ✅ 准备就绪！等待vcpkg安装完成

## 📋 当前状态

✅ **已完成：**
- [x] vcpkg已下载和初始化
- [x] vcpkg已集成到系统
- [x] ONNX Runtime已下载（GPU版本1.23.1）
- [x] ONNX Runtime已解压到正确位置
- [x] CMakeLists.txt已配置ONNX Runtime路径
- [x] 编译脚本已准备（build.bat）
- [x] 测试配置文件已准备（config/test.ini）

⏳ **进行中：**
- [ ] vcpkg正在安装依赖库（约40-60分钟）
  - opencv4
  - ffmpeg
  - glog
  - jsoncpp
  - curl

---

## 🎯 vcpkg安装完成后的步骤

### **第1步：验证安装**

```powershell
cd F:\EASYLOT\vcpkg-master

# 列出已安装的包
.\vcpkg list
```

**应该看到：**
```
curl:x64-windows
ffmpeg:x64-windows
glog:x64-windows
jsoncpp:x64-windows
opencv4:x64-windows
```

---

### **第2步：编译TASK模块**

**方式A：使用编译脚本（推荐，简单）**

```powershell
# 进入TASK目录
cd F:\EASYLOT\easyaiot-main\TASK

# 双击运行编译脚本
.\build.bat

# 或在PowerShell中运行
.\build.bat
```

**方式B：手动编译**

```powershell
# 1. 进入TASK目录
cd F:\EASYLOT\easyaiot-main\TASK

# 2. 创建build目录
mkdir build
cd build

# 3. 配置CMake
cmake .. -DCMAKE_TOOLCHAIN_FILE=F:/EASYLOT/vcpkg-master/scripts/buildsystems/vcpkg.cmake -G "Visual Studio 17 2022" -A x64

# 4. 编译
cmake --build . --config Release

# 5. 复制DLL
cd Release
copy F:\EASYLOT\vcpkg-master\installed\x64-windows\bin\*.dll .
copy F:\EASYLOT\onnxruntime-win-x64-gpu-1.23.1\lib\*.dll .
```

---

### **第3步：准备配置文件**

编辑 `config/test.ini`，修改：

```ini
[video]
# 改成您的RTSP地址
rtsp_url=rtsp://admin:password@192.168.1.64:554/path

[ai]
# 如果没有YOLO模型，先禁用
enable=false
```

---

### **第4步：测试运行**

```powershell
cd F:\EASYLOT\easyaiot-main\TASK\build\Release

# 运行TASK模块
.\TASK.exe ..\..\config\test.ini
```

**预期输出：**
```
╔════════════════════════════════════════════════════════╗
║     ████████╗ █████╗ ███████╗██╗  ██╗                ║
║     ...                                                ║
╚════════════════════════════════════════════════════════╝

🚀 TASK模块启动中...
✅ 配置文件解析成功
🎬 启动TASK服务...
✅ TASK服务启动成功!
🎉 系统运行中... 按 Ctrl+C 退出
```

---

## 📝 关键路径记录

```
vcpkg根目录：
F:\EASYLOT\vcpkg-master

vcpkg工具链：
F:/EASYLOT/vcpkg-master/scripts/buildsystems/vcpkg.cmake

ONNX Runtime：
F:/EASYLOT/onnxruntime-win-x64-gpu-1.23.1

TASK源码：
F:\EASYLOT\easyaiot-main\TASK

编译输出：
F:\EASYLOT\easyaiot-main\TASK\build\Release\TASK.exe
```

---

## ⚠️ 可能遇到的问题

### **问题1：CMake找不到Visual Studio**

**错误信息：**
```
Could not find Visual Studio
```

**解决：**
```powershell
# 改为VS2019（如果您装的是2019）
cmake .. -DCMAKE_TOOLCHAIN_FILE=... -G "Visual Studio 16 2019" -A x64
```

### **问题2：找不到OpenCV**

**错误信息：**
```
Could not find OpenCV
```

**解决：**
```powershell
# 确认vcpkg安装完成
cd F:\EASYLOT\vcpkg-master
.\vcpkg list | findstr opencv
```

### **问题3：编译错误**

**解决：**
- 查看详细错误信息
- 确认所有依赖都已安装
- 重新运行CMake配置

---

## 🎯 成功标志

✅ **编译成功：**
- 生成了 `TASK.exe`（约5-10MB）
- 所有DLL已复制到Release目录
- 无编译错误

✅ **运行成功：**
- 显示欢迎界面
- 配置文件解析成功
- 服务启动成功

---

## 📞 如果遇到问题

请提供以下信息：
1. 具体错误信息（复制完整输出）
2. vcpkg list的输出
3. Visual Studio版本
4. 编译日志

我会帮您解决！
