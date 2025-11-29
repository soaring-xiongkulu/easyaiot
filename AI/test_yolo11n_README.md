# YOLO11n 模型推理测试脚本使用文档

## 简介

`test_yolo11n.py` 是一个独立的测试脚本，用于测试 YOLO11n 模型的推理功能。该脚本不依赖 Flask 应用上下文，可以直接运行，方便快速验证模型是否正常工作。

## 功能特性

- ✅ 自动加载 `yolo11n.pt` 模型
- ✅ 支持自定义测试图片或自动生成测试图片
- ✅ 完整的推理流程和结果展示
- ✅ 自动保存带标注的结果图片
- ✅ 性能统计（推理时间、FPS）
- ✅ 详细的检测结果信息
- ✅ 灵活的参数配置

## 环境要求

### 依赖库

确保已安装以下 Python 库：

```bash
pip install ultralytics opencv-python numpy
```

或者使用项目的 requirements.txt：

```bash
pip install -r requirements.txt
```

### 模型文件

确保 `yolo11n.pt` 模型文件位于 AI 目录下：

```
AI/
  ├── yolo11n.pt          # 模型文件（必需）
  ├── test_yolo11n.py     # 测试脚本
  └── ...
```

## 使用方法

### 基本用法

#### 1. 使用默认测试图片

如果不提供图片路径，脚本会自动创建一个测试图片：

```bash
cd /opt/projects/easyaiot/AI
python test_yolo11n.py
```

#### 2. 使用指定图片

提供图片路径进行推理：

```bash
python test_yolo11n.py path/to/your/image.jpg
```

支持的图片格式：`.jpg`, `.jpeg`, `.png`, `.bmp` 等 OpenCV 支持的格式。

#### 3. 自定义置信度阈值

调整检测的置信度阈值（默认 0.25）：

```bash
python test_yolo11n.py image.jpg --conf 0.5
```

- 较高的值（如 0.5）：只显示高置信度的检测结果，减少误检
- 较低的值（如 0.1）：显示更多检测结果，但可能包含误检

#### 4. 自定义 IoU 阈值

调整非极大值抑制（NMS）的 IoU 阈值（默认 0.45）：

```bash
python test_yolo11n.py image.jpg --iou 0.6
```

- 较高的值（如 0.6）：允许更多重叠的检测框
- 较低的值（如 0.3）：更严格的去重，减少重叠检测

#### 5. 不保存结果图片

如果只想查看结果而不保存图片：

```bash
python test_yolo11n.py image.jpg --no-save
```

#### 6. 使用自定义模型路径

如果模型文件不在当前目录或使用不同的模型：

```bash
python test_yolo11n.py image.jpg --model path/to/your/model.pt
```

### 完整参数说明

```bash
python test_yolo11n.py [图片路径] [选项]
```

**位置参数：**
- `image` (可选): 测试图片路径。如果不提供，会创建默认测试图片

**选项参数：**
- `--model MODEL`: 模型文件路径（默认: `yolo11n.pt`）
- `--conf CONF`: 置信度阈值，范围 0.0-1.0（默认: `0.25`）
- `--iou IOU`: IoU 阈值，范围 0.0-1.0（默认: `0.45`）
- `--no-save`: 不保存结果图片
- `-h, --help`: 显示帮助信息

## 输出说明

### 控制台输出

脚本运行时会显示以下信息：

1. **模型信息**
   - 模型文件路径和大小
   - 模型加载状态

2. **图片信息**
   - 测试图片路径
   - 图片尺寸

3. **推理参数**
   - 置信度阈值
   - IoU 阈值

4. **检测结果**
   - 检测到的目标数量
   - 每个目标的详细信息：
     - 类别名称
     - 置信度分数
     - 边界框坐标 (x1, y1, x2, y2)

5. **性能统计**
   - 推理时间（秒）
   - FPS（帧率）

6. **结果保存位置**
   - 结果图片的保存路径

### 输出示例

```
============================================================
🚀 YOLO11n 模型推理测试
============================================================
✅ 找到模型文件: yolo11n.pt
   文件大小: 5.40 MB

📦 正在加载模型...
✅ 模型加载成功
   模型类型: YOLO

✅ 使用测试图片: test_image.jpg
   图片尺寸: 640x480

🔍 开始推理...
   置信度阈值: 0.25
   IoU阈值: 0.45
✅ 推理完成 (耗时: 0.123秒)

📊 检测结果:
   检测到的目标数量: 3

   详细信息:
      [1] person: 置信度=0.856, 位置=(120.5, 80.3, 250.7, 380.2)
      [2] car: 置信度=0.742, 位置=(400.1, 200.5, 580.9, 350.8)
      [3] dog: 置信度=0.623, 位置=(50.2, 300.1, 180.4, 450.6)

💾 结果已保存: data/inference_results/yolo11n_test_test_image_20241126_143022.jpg

⚡ 性能统计:
   推理时间: 0.123秒
   FPS: 8.13

============================================================
✅ 测试完成
============================================================
```

### 结果图片

结果图片保存在 `data/inference_results/` 目录下，文件名格式为：

```
yolo11n_test_{原图片名}_{时间戳}.jpg
```

例如：`yolo11n_test_test_image_20241126_143022.jpg`

结果图片包含：
- 原始图片
- 检测框（边界框）
- 类别标签和置信度分数

## 常见问题

### 1. 模型文件不存在

**错误信息：**
```
❌ 模型文件不存在: yolo11n.pt
```

**解决方案：**
- 确保 `yolo11n.pt` 文件位于 AI 目录下
- 或使用 `--model` 参数指定正确的模型路径

### 2. 缺少依赖库

**错误信息：**
```
❌ 缺少必要的依赖库: No module named 'ultralytics'
```

**解决方案：**
```bash
pip install ultralytics opencv-python numpy
```

### 3. 图片无法读取

**错误信息：**
```
❌ 无法读取图片: path/to/image.jpg
```

**解决方案：**
- 检查图片路径是否正确
- 确认图片文件格式是否支持（jpg, png, bmp 等）
- 确认图片文件是否损坏

### 4. 推理速度慢

**可能原因：**
- 使用 CPU 推理（较慢）
- 图片尺寸过大
- 系统资源不足

**优化建议：**
- 如果有 GPU，确保 CUDA 环境配置正确
- 减小图片尺寸
- 关闭其他占用资源的程序

### 5. 检测结果不理想

**可能原因：**
- 置信度阈值设置不当
- 图片质量或内容不适合检测
- 模型未针对特定场景训练

**优化建议：**
- 调整 `--conf` 参数（尝试 0.1-0.5 之间的值）
- 使用更清晰的图片
- 如果针对特定场景，考虑使用自定义训练的模型

## 高级用法

### 批量测试

可以使用 shell 脚本批量测试多张图片：

**Linux/Mac:**
```bash
#!/bin/bash
for img in images/*.jpg; do
    echo "处理: $img"
    python test_yolo11n.py "$img"
done
```

**Windows (PowerShell):**
```powershell
Get-ChildItem images\*.jpg | ForEach-Object {
    Write-Host "处理: $($_.FullName)"
    python test_yolo11n.py $_.FullName
}
```

### 性能基准测试

测试不同参数组合的性能：

```bash
# 测试不同置信度阈值
for conf in 0.1 0.25 0.5 0.75; do
    echo "测试置信度阈值: $conf"
    python test_yolo11n.py test.jpg --conf $conf --no-save
done
```

## 技术细节

### 模型加载

脚本使用 `ultralytics` 库的 `YOLO` 类加载模型：

```python
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
```

### 推理过程

1. 读取输入图片
2. 使用模型进行预测
3. 应用置信度和 IoU 阈值过滤
4. 绘制检测结果
5. 保存结果图片

### 结果格式

检测结果包含：
- **类别 ID**: 检测到的对象类别编号
- **类别名称**: 可读的类别名称（如 'person', 'car' 等）
- **置信度**: 检测的置信度分数（0.0-1.0）
- **边界框**: 检测框的坐标 (x1, y1, x2, y2)

## 相关文件

- `test_yolo11n.py`: 测试脚本
- `yolo11n.pt`: YOLO11n 模型文件
- `app/services/inference_service.py`: 生产环境的推理服务实现
- `requirements.txt`: 项目依赖列表

## 更新日志

### v1.0.0 (2024-11-26)
- 初始版本
- 支持基本的模型推理测试
- 支持自定义参数配置
- 自动保存结果图片

## 联系与支持

如有问题或建议，请联系：
- 作者: 翱翔的雄库鲁
- 邮箱: andywebjava@163.com
- 微信: EasyAIoT2025

---

**注意**: 此脚本仅用于测试和开发目的。生产环境请使用完整的推理服务 (`app/services/inference_service.py`)。

