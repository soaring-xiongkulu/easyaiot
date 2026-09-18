# 场景姿态意图分析联调说明

## 功能范围

| 模块 | 说明 |
|------|------|
| 场景姿态库 | `/video/scenario-pose/libraries` CRUD + 条目图片录入 |
| 意图匹配 | post-process Worker 内 YOLO Pose → 单帧角度/规则匹配 |
| DTW 时序 | 任务开启 `temporal_dtw_enabled`，条目 `extra_rules.sequence_features` |
| 告警骨架 | 告警详情弹窗 Canvas 叠加；Worker 可保存 `*_pose_skeleton.jpg` |
| iot-sink | 自定义 `alerts[]` → `/alert/hook` → 通知链路 |

## 快速测试（无需服务）

```bash
cd VIDEO
python test_pose_intent/test_pose_intent.py \
  --image ../AI/test_pose/fixtures/pose_sample.jpg \
  --skip-api --skip-db
```

## HTTP API 联调（需 VIDEO 服务）

```bash
# 启动 VIDEO 后
python test_pose_intent/test_pose_intent.py \
  --api http://127.0.0.1:48080/admin-api/video \
  --skip-db
```

## 全链路联调（需 DB + Worker）

```bash
export EASYAIOT_ENABLE_POST_PROCESS_WORKER=1
python test_pose_intent/test_pose_intent.py \
  --image ../AI/test_pose/fixtures/pose_sample.jpg
```

## 手工联调步骤

### 1. 创建场景姿态库

```bash
curl -X POST http://127.0.0.1:48080/admin-api/video/scenario-pose/libraries \
  -H 'Content-Type: application/json' \
  -d '{"name":"跌倒检测库","scene_category":"fall","similarity_threshold":0.72}'
```

### 2. 导入内置模板或上传参考图

```bash
# 导入跌倒规则模板
curl -X POST http://127.0.0.1:48080/admin-api/video/scenario-pose/libraries/1/import-template \
  -H 'Content-Type: application/json' \
  -d '{"template_key":"fall"}'

# 或上传参考图片
curl -X POST http://127.0.0.1:48080/admin-api/video/scenario-pose/libraries/1/entries \
  -F 'name=侧躺参考' -F 'file=@pose_sample.jpg'
```

### 3. 配置算法任务

在 **摄像头 → 算法任务** 中：

- 开启 **姿态意图分析告警**
- 选择场景姿态库
- 可选：开启 **多帧 DTW 匹配**、**告警图叠骨架**

### 4. 验证告警

- 触发 person 检测后，查看 **告警中心 → 查看图片**
- 姿态意图告警应显示骨架叠加与匹配摘要（库名/相似度）

## DTW 时序条目格式

在条目 `extra_rules` 中配置参考序列（特征向量列表）：

```json
{
  "sequence_features": [
    [0.12, 0.45, ...],
    [0.15, 0.42, ...],
    [0.18, 0.40, ...]
  ]
}
```

任务 `pose_intent_config`：

```json
{
  "temporal_dtw_enabled": true,
  "temporal_window_frames": 6,
  "temporal_dtw_threshold": 0.65
}
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `EASYAIOT_ENABLE_POST_PROCESS_WORKER=1` | 启动姿态 Worker |
| `POSE_MODEL_PATH` | 自定义 YOLO Pose 模型路径 |
| `SCENARIO_POSE_IMAGE_BUCKET` | RustFS 桶名（默认 scenario-pose-library） |
| `IOT_SINK_HOST` / `IOT_SINK_PORT` | 后处理入队地址 |

## 相关文件

| 路径 | 说明 |
|------|------|
| `VIDEO/app/utils/pose_intent.py` | 特征/相似度/DTW |
| `VIDEO/app/services/pose_intent_matching_service.py` | 匹配编排 |
| `VIDEO/app/utils/pose_intent_visual.py` | 告警图骨架叠层 |
| `WEB/src/utils/poseSkeleton.ts` | 前端骨架绘制 |
| `WEB/src/views/alert/components/ImageModal` | 告警图片+骨架 |
