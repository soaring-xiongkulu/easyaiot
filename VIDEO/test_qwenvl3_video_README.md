# QwenVL3 视频理解测试工具使用说明

## 简介

`test_qwenvl3_video.py` 是一个用于测试 QwenVL3 视频理解大模型的命令行工具。该工具根据阿里云百炼平台官方文档编写，支持从视频文件中提取帧或直接使用视频文件进行视频理解。

## 功能特性

- 📹 **视频帧提取**：支持从视频文件中均匀提取多帧作为图片列表
- 🎬 **视频文件上传**：支持直接使用视频文件（Base64编码，适用于小文件）
- 🤖 **官方 API**：严格按照阿里云百炼平台官方文档实现
- 📊 **流式输出**：支持实时显示推理结果
- 💾 **帧保存功能**：可选择保存提取的帧为图片文件

## 环境要求

### 系统依赖

- Python 3.8+
- OpenCV (cv2)
- requests
- python-dotenv

### 环境配置

1. **环境变量文件**：在 `VIDEO` 目录下创建 `.env` 文件，配置 `DASHSCOPE_API_KEY`
2. **API Key 获取**：
   - 登录 [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
   - 在控制台右上角选择"API-KEY"，创建新的 API Key
   - 将 API Key 配置到 `.env` 文件中：`DASHSCOPE_API_KEY=your-api-key`

## 安装依赖

```bash
pip install opencv-python requests python-dotenv
```

## 使用方法

### 基本用法

```bash
python test_qwenvl3_video.py <视频文件路径>
```

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `video_path` | 必需 | - | 视频文件路径 |
| `--num-frames` | 可选 | 4 | 从视频中提取的帧数（用于图片列表模式） |
| `--prompt` | 可选 | 默认提示词 | 提示词 |
| `--model` | 可选 | qwen-vl-plus | 模型名称（qwen-vl-plus, qwen-vl-max, qwen3-vl-plus, qwen3-vl-max） |
| `--use-video-file` | 可选 | False | 直接使用视频文件（Base64编码），而不是提取帧 |
| `--save-frames` | 可选 | False | 是否保存提取的帧到文件 |
| `--api-key` | 可选 | - | API Key（如果不提供，将从环境变量读取） |
| `--env` | 可选 | - | 指定环境配置文件（如 .env.prod） |

### 视频输入模式

#### 1. 图片列表模式（默认）

将视频拆分为多张连续的帧图像，作为图片列表传入。这是推荐的方式，适用于大多数场景。

- **优点**：支持任意大小的视频文件
- **限制**：需要从视频中提取帧

#### 2. 视频文件模式

直接使用视频文件的 Base64 编码。

- **优点**：保持视频的完整信息
- **限制**：文件大小不超过 10MB

## 使用示例

### 示例 1：基本使用（提取4帧）

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4
```

### 示例 2：提取更多帧

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 --num-frames 8
```

### 示例 3：使用自定义提示词

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \
    --prompt "请详细描述这个视频中的人物、动作和场景"
```

### 示例 4：使用视频文件模式（适用于小文件）

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \
    --use-video-file
```

### 示例 5：保存提取的帧

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \
    --save-frames
```

提取的帧将保存为 `VIDEO/test_frame_0.jpg`, `test_frame_1.jpg` 等

### 示例 6：指定模型

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \
    --model qwen-vl-max
```

### 示例 7：使用命令行参数指定 API Key

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \
    --api-key your-api-key-here
```

### 示例 8：完整参数组合

```bash
python test_qwenvl3_video.py /opt/projects/easyaiot/VIDEO/video/video2.mp4 \
    --num-frames 6 \
    --model qwen-vl-plus \
    --prompt "分析这个视频中的主要对象、场景和可能的行为" \
    --save-frames
```

## 输出说明

脚本运行时会显示以下信息：

1. **环境变量加载状态**
   - ✅ 已加载环境变量文件
   - ⚠️ 环境变量文件不存在

2. **视频信息**
   - 总帧数
   - 帧率 (fps)
   - 分辨率
   - 时长

3. **API 调用信息**
   - 使用的模式（图片列表或视频文件）
   - 模型名称
   - 提示词

4. **推理结果**
   - 实时流式输出推理响应内容
   - Token 使用情况（如果可用）

## 常见问题

### 1. 找不到视频文件

**错误信息**：`❌ 错误: 视频文件不存在`

**解决方法**：检查视频文件路径是否正确，使用绝对路径或相对路径

### 2. 未找到 API Key

**错误信息**：`未找到 API Key！`

**解决方法**：
- 在 `.env` 文件中设置 `DASHSCOPE_API_KEY=your-api-key`
- 或使用 `--api-key` 参数
- 或设置环境变量 `DASHSCOPE_API_KEY`

### 3. API 请求失败

**错误信息**：`❌ API 请求失败`

**解决方法**：
- 检查 API Key 是否正确
- 确认 API Key 有效且有足够配额
- 检查网络连接
- 查看错误详情中的具体错误信息

### 4. 无法打开视频文件

**错误信息**：`无法打开视频文件`

**解决方法**：
- 确认视频文件格式受支持（常见格式：mp4, avi, mov, mkv, flv, wmv 等）
- 检查文件是否损坏
- 确认有读取权限

### 5. 视频文件过大（视频文件模式）

**错误信息**：`视频文件过大`

**解决方法**：
- 视频文件模式仅支持不超过 10MB 的文件
- 使用默认的图片列表模式（不添加 `--use-video-file` 参数）
- 或使用公网 URL（需要自行实现）

## 技术细节

### API 端点

- **北京地域**：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- **新加坡地域**：`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`

### 帧提取逻辑

- 帧索引从 0 开始计数
- 均匀分布提取：将视频总帧数平均分成 `num_frames + 1` 段，提取每段的起始帧
- 如果 `num_frames >= 总帧数`，则提取所有帧

### 图像编码

- 使用 OpenCV 将视频帧编码为 JPEG 格式
- 默认 JPEG 质量为 95
- 转换为 base64 编码后发送给 API

### API 调用格式

根据官方文档，QwenVL3 视频理解 API 使用以下格式：

```json
{
  "model": "qwen-vl-plus",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "video",
          "video": ["data:image/jpeg;base64,...", ...]
        },
        {
          "type": "text",
          "text": "请描述这个视频的内容。"
        }
      ]
    }
  ],
  "modalities": ["text"],
  "stream": true
}
```

### 视频文件要求

- **大小限制**：
  - 图片列表模式：无限制（推荐）
  - Base64 编码模式：不超过 10MB
  - 公网 URL 模式：不超过 2GB
- **时长限制**：2 秒至 20 分钟
- **格式支持**：MP4、AVI、MKV、MOV、FLV、WMV 等常见视频格式

## 相关文档

- [阿里云百炼平台 API 文档](https://bailian.console.aliyun.com/?spm=5176.29597918.J_C-NDPSQ8SFKWB4aef8i6I.1.298d7b08IRr02o&tab=doc#/doc/?type=model&url=2877996)
- [通义千问 API 参考文档](https://help.aliyun.com/zh/model-studio/user-guide/qwen-omni)

## 作者信息

- **作者**：翱翔的雄库鲁
- **邮箱**：andywebjava@163.com
- **微信**：EasyAIoT2025

## 许可证

请参考项目根目录的 LICENSE 文件。
