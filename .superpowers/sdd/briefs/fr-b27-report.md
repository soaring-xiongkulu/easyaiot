# FR-B27 Report — Matching Kafka 本地 produce 取证 + 字段矩阵自动扩面（Python-first）

**Status:** PARTIAL（local E2E ✅ / mini-safe restored / phase0 PASS / field 39/39）— **禁止 COMPLETE**

**Branch:** `feat/video-java`  
**Worktree:** `F:/acme/.worktrees/video-java`

---

## Python-first 对照（已读）

| 源 | 要点 |
|----|------|
| `VIDEO/_retired_python_video/app/services/face_matching_kafka_service.py` | `build_face_matching_message()` camelCase 键；`send_face_matching_to_kafka()` → topic `iot-face-matching`，key=`deviceId` |
| `VIDEO/_retired_python_video/app/services/plate_matching_kafka_service.py` | `build_plate_matching_message()`；topic `iot-plate-matching`，key=`deviceId` |
| `VIDEO/_retired_python_video/app/blueprints/face.py` | `POST /matching/publish` → Kafka produce（非 direct process） |
| `VIDEO/_retired_python_video/app/blueprints/plate.py` | 同上 plate 路径 |
| `VIDEO/_retired_python_video/models.py` | `FaceMatchRecord.to_dict` / `PlateMatchRecord.to_dict` / `FaceLibrary.to_dict` 等驱动深字段扩面 |

## 1. Matching Kafka produce（use-direct-process=false）

**设备/任务：** `frb27_device`（`seed_fr_b27_fixture.py`）task_id=62，face/plate library  
**Profile：** `local,fr-b27-soak` — `video.matching.use-direct-process=false`

**证据：** `logs/fr-b27-matching-kafka-latest.json`

| 验证项 | 结果 |
|--------|------|
| Face publish | `POST /video/face/matching/publish` HTTP 200 `code=0` |
| Face topic | `iot-face-matching` partition=4 offset=0 key=`frb27_device` |
| Plate publish | `POST /video/plate/matching/publish` HTTP 200 `code=0` |
| Plate topic | `iot-plate-matching` partition=4 offset=0 key=`frb27_device` |
| Worker 推理/命中告警 | **EX** — produce-only 取证（brief 允许） |

**Java 路径：** `FaceMatchingService.publish` / `PlateMatchingService.publish` → `MatchingKafkaProducer`（`use-direct-process=false` 时真 broker send）

## 2. 字段矩阵扩面（+14 深采样）

**工具：** `tools/video_java/field_contract.py`（`ARTIFACT_PREFIX=fr-b27`）

| 指标 | FR-B23 基线 | FR-B27 |
|------|------------|--------|
| 深采样端点 | 25 | **39** (+14) |
| 深断言 | — | **192 pass / 0 fail / 3 skip** |
| GET 信封矩阵 | 95/265（历史） | **265/265 pass** |

**新增端点（Python `to_dict` 引用）：** face/plate matching records、face/plate model status、library get、camera locations/directory/nvr/tracks、sna p space get、playback get、scenario-pose library get、stream-forward task status

**证据：** `logs/fr-b27-field-contract-latest.json`、`logs/fr-b27-field-matrix-latest.json`

**Java 修复：**
- `FaceMatchRecordRepository` / `PlateMatchRecordRepository`：`list` 键（对齐 Python，非 `data`）
- `FaceController` / `PlateController` matching records → `VideoApiResponse`（消除双层 envelope）
- `FaceModelService.modelStatus`：补全 `filename`/`stage`/`progress` 等 Python 键
- `SnapSpaceRepository`：`task_count` 子查询

## 3. mini-safe 恢复

Soak 后 Java 重启 `profile=local`；`use-direct-process=true`。  
证据：`logs/fr-b27-restore-mini.log`

## 4. Phase 0

`python tools/video_java/certify.py --phase 0` → **PASS 5/5** — `logs/fr-b27-phase0.log`

## 5. Checklist / GAP

- `PROD_SOAK_CHECKLIST.md` §1.4 + §0.4 更新为 FR-B27 local-only 证据
- `FULL_REPLACEMENT_GAP.md` §9 FR-B27 判定
- `HANDOFF.md` §8 摘要更新

## Remaining

- matching worker 推理 + 库命中告警链（Kafka consumer → Milvus/Paddle）
- prod broker 上 matching topic lag / 分区卫生
- 全量 259 路由字段矩阵
- WVP / GB28181 / 远程 node prod 联调

## Concerns

- **produce 证据**依赖 Java log `matching kafka sent`（API 响应仅返回 message body，与 Python 一致）
- **薄 jar 误用**：`java -jar` 需 `mvn -f DEVICE/pom.xml -pl iot-video/iot-video-biz -am package` 生成的 **fat jar**（~82MB）；否则 soak 重启静默失败
- shell `JAVA_HOME` 默认为 JDK 17；soak 脚本强制 `F:\acme\.tools\jdk-21.0.2`
- 禁止对外宣称 COMPLETE / prod 绿
