# SAM 万物分割 — 快速指南

SAM（Segment Anything Model）为 EasyAIoT 提供零样本图像分割能力，支持点/框提示交互标注与自动全图分割，后续可扩展文本描述万物识别（参考 [sam-changkang](https://gitee.com/ai-agents/sam-changkang)）。

## 1. 能力概览

| 模式 | API | 用途 |
|------|-----|------|
| 点提示 | `POST /model/sam/predict/point` | 点击目标自动提取 mask |
| 框提示 | `POST /model/sam/predict/box` | 框选目标精确分割 |
| 自动分割 | `POST /model/sam/predict/auto` | 全图自动发现所有物体 |
| 文本提示 | `POST /model/sam/predict/text` | 英文描述万物识别（二期） |

## 2. 安装

### 2.1 安装依赖

```bash
cd AI
pip install -r requirements-sam.txt
```

或手动安装：

```bash
pip install git+https://github.com/facebookresearch/segment-anything.git
pip install pycocotools
```

### 2.2 下载模型权重

```bash
mkdir -p /data/models/sam

# 推荐：vit_b（375MB，显存 ~4G）
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth \
  -O /data/models/sam/sam_vit_b_01ec64.pth
```

其他权重参见 [官方 README](https://github.com/facebookresearch/segment-anything#model-checkpoints)。

### 2.3 配置环境变量

在 `.env` 中追加：

```bash
SAM_ENABLED=true
SAM_MODEL_TYPE=vit_b
SAM_CHECKPOINT_PATH=/data/models/sam/sam_vit_b_01ec64.pth
SAM_DEVICE=cuda
```

### 2.4 启动服务

```bash
python run.py --env=prod
```

## 3. 快速验证

```bash
# 健康检查
curl "http://localhost:5000/model/sam/health"

# 点提示分割
curl -X POST "http://localhost:5000/model/sam/predict/point" \
  -F "file=@test.jpg" \
  -F 'points=[[512,384]]' \
  -F 'point_labels=[1]'

# 经网关
curl "http://localhost:48080/admin-api/model/sam/health"
```

## 4. 与标注平台集成

1. 用户在标注画布点击目标 → 调用点提示 API
2. 返回 mask 多边形 → 前端叠加预览
3. 用户确认 → 写入标注 JSON（`shape_type: "polygon"`）
4. （二期）批量自动分割 → 扩展 `auto_label` 写回 dataset

## 5. 前置条件

- CUDA 12.x + 显存 ≥ 8G（vit_b 最低 4G）
- `segment_anything` 已安装
- 模型权重文件存在
- `SAM_ENABLED=true`

## 6. 常见问题

| 问题 | 解决 |
|------|------|
| health 返回 unhealthy | 检查权重路径与 `pip list \| grep segment` |
| CUDA OOM | 改用 vit_b 或减小图片尺寸 |
| 推理很慢 | 确认 `SAM_DEVICE=cuda` 且 `nvidia-smi` 正常 |
| 文本提示 501 | 二期功能，需设 `SAM_TEXT_ENABLED=true` |

## 7. 参考链接

- [Segment Anything 官方仓库](https://github.com/facebookresearch/segment-anything)
- [sam-changkang 万物识别](https://gitee.com/ai-agents/sam-changkang)
- [SAM 2（视频分割）](https://github.com/facebookresearch/segment-anything-2)
