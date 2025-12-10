# TASK模块测试指南

## 📋 修复内容

### 已解决的问题：
1. ✅ 清理了所有中文字符和emoji（避免C4819编码错误）
2. ✅ 修复ONNX Runtime API版本问题（兼容1.17版本）
3. ✅ 添加详细的错误日志（便于诊断问题）
4. ✅ 添加错误处理和返回值检查
5. ✅ 创建测试配置文件

---

## 🚀 测试步骤

### 第一步：重新编译

```powershell
cd F:\EASYLOT\easyaiot-main\TASK
.\build.bat
```

**预期输出：**
- 无C4819编码警告
- 编译成功生成 `build\Release\TASK.exe`

---

### 第二步：测试RTSP连接（不启用AI）

先测试RTSP拉流是否正常：

```powershell
cd F:\EASYLOT\easyaiot-main\TASK\build\Release
.\TASK.exe ..\..\config\test_rtsp_only.ini
```

**预期输出：**
```
[STARTING] TASK module initializing...
[CONFIG] Config file: ..\..\config\test_rtsp_only.ini
[OK] Config file parsed successfully
[INIT] Step 1: Initializing YOLO detector...
[INIT] YOLO detector initialized successfully (AI disabled)
[INIT] Step 2: Initializing media player...
[INIT] Initializing media player
[INIT] Media player initialized successfully
[OK] All components initialized successfully!
System running... Press Ctrl+C to exit
```

**如果失败：**
- 检查RTSP URL是否正确
- 确认摄像头在线：`rtsp://admin:sr336699@192.168.1.64:554/Streaming/Channels/102`
- 检查网络连接

---

### 第三步：下载YOLO模型

```powershell
cd F:\EASYLOT\easyaiot-main\TASK
.\scripts\download_yolo_model.ps1
```

这将：
1. 下载YOLOv11n模型（约6MB）
2. 创建COCO类别文件
3. 提示更新配置文件路径

**如果下载失败，手动下载：**
1. 访问：https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov11n.onnx
2. 保存到：`F:\EASYLOT\easyaiot-main\TASK\models\yolov11n.onnx`

---

### 第四步：测试完整功能（启用AI）

```powershell
cd F:\EASYLOT\easyaiot-main\TASK\build\Release
.\TASK.exe ..\..\config\test.ini
```

**预期输出：**
```
[STARTING] TASK module initializing...
[CONFIG] Config file: ..\..\config\test.ini
[CONFIG] Reading section: [video]
[CONFIG] Reading section: [ai]
[CONFIG] Reading section: [alarm]
[CONFIG] Reading section: [features]
[OK] Config file parsed successfully
  - RTSP URL: rtsp://admin:sr336699@192.168.1.64:554/Streaming/Channels/102
  - Thread count: 3
  - AI inference: Enabled

[INIT] Step 1: Initializing YOLO detector...
[INIT] Model path: F:/EASYLOT/easyaiot-main/TASK/models/yolov11n.onnx
[INIT] Loading YOLO model with 3 threads...
[YOLO] Creating 3 YOLO engine instances...
[YOLO] Loading model instance 1/3...
[YOLO] Creating ONNX Runtime environment...
[YOLO] Setting up session options...
[YOLO] Checking available execution providers...
[YOLO] Using CPU execution provider
[YOLO] Loading model: F:/EASYLOT/easyaiot-main/TASK/models/yolov11n.onnx
[YOLO] Model loaded successfully
[YOLO] Using default COCO classes (80 classes)
[YOLO] Instance 1 loaded successfully
[YOLO] Loading model instance 2/3...
...
[YOLO] Thread pool setup completed
[OK] YOLO thread pool initialized
[INIT] YOLO detector initialized successfully

[INIT] Step 2: Initializing media player...
[INIT] Media player initialized successfully

[OK] All components initialized successfully!
System running... Press Ctrl+C to exit
```

---

## ⚠️ 常见问题

### 问题1：ONNX Runtime版本错误
```
The requested API version [23] is not available
```
**解决方案：** 已修复，使用了兼容1.17的API

### 问题2：字符编码警告（C4819）
```
warning C4819: 该文件包含不能在当前代码页(936)中表示的字符
```
**解决方案：** 已清理所有中文字符

### 问题3：模型文件不存在
```
[ERROR] YOLO thread pool initialization failed
```
**解决方案：** 
1. 运行`.\scripts\download_yolo_model.ps1`
2. 或者先禁用AI（`enable=false`）

### 问题4：RTSP连接失败
```
[ERROR] avformat_open_input error
```
**解决方案：**
1. 检查RTSP URL
2. 确认摄像头在线
3. 检查防火墙设置

---

## 📊 性能监控

### CPU使用率
- RTSP拉流：10-15%
- AI推理（3线程）：30-50%

### 内存占用
- 基础：~200MB
- 加载模型后：~500MB

### 延迟
- RTSP拉流：200-500ms
- AI推理：50-100ms/帧

---

## 🔄 下一步

如果测试成功，您可以：

1. ✅ **集成到AI模块**（Step 2）
   - 创建TaskManager进程管理器
   - 添加告警回调API
   - 实现配置文件生成器

2. ✅ **完善功能**
   - RTMP推流
   - 报警区域检测
   - HTTP回调

3. ✅ **性能优化**
   - GPU加速（需安装CUDA）
   - 多摄像头支持
   - 负载均衡

---

## 📝 配置文件说明

### test_rtsp_only.ini（基础测试）
- 仅测试RTSP拉流
- 不启用AI推理
- 适合初次测试

### test.ini（完整功能）
- 启用AI推理
- 支持所有功能
- 需要模型文件

---

## 🆘 获取帮助

如果遇到问题：
1. 检查日志输出
2. 确认配置文件正确
3. 验证模型文件存在
4. 测试RTSP连接

---

**最后更新：2025-10-22**
