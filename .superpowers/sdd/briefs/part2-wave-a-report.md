# Part2 Wave-A Report — 外部 SDK / Java 替代 face+plate 推理

**Pack:** Part2 Wave-A  
**SSOT:** `docs/video-java/PART2_WAVE_A_PACK.md`  
**Date:** 2026-08-12  
**nested_subagents:** none  
**Overall:** **PASS**（A0–A5 行为证据齐全；Out 项未宣称完成）

## Results

| ID | Status | Evidence | Notes |
|----|--------|----------|-------|
| A0 | **PASS** | `logs/p2a-a0-assets.json` | face/plate ONNX 齐；Milvus `:19530` ping OK |
| A1 | **PASS** | `logs/p2a-a1-face-ort.json` | Python InsightFace vs Java ORT 余弦 **0.99995**（≥0.99，可复用旧库） |
| A2 | **PASS** | `logs/p2a-a2-milvus.json` | milvus-sdk-java；collection `face_embeddings` |
| A3 | **PASS** | `logs/p2a-a3-face-match.json` | 入库→hit(score=1.0) / 无关向量 miss；**非 bypass** |
| A4 | **PASS** | `logs/p2a-a4-plate-ocr.json` | `POST /video/plate/recognize/image` → `engine=onnx-java`，`plate_no=A12345` |
| A5 | **PASS** | `logs/p2a-a5-cli-off.json` | `python-cli-enabled=false`；face health `onnx_java=true`；plate 走 Java |
| A6 | **PASS** | 本报告 + 文档更新 | — |

## Out（未做 / 另议）

| ID | 项 | 状态 |
|----|----|------|
| X1 | Patrol `run_deploy.py` | 未做 |
| X2 | post_process `run_worker.py` | 未做 |
| X3 | YOLO Pose CLI | 仍可 CLI（本包 Out） |
| X4 | 真机联调 | 未做 |
| X5 | 自研网络 / 重写 RUNTIME | 禁止 |
| X6 | U3 alternate 真流 | 保持 PARTIAL |

## Tech

- Maven: `onnxruntime 1.19.2`、`milvus-sdk-java 2.4.4`（排除 `log4j-slf4j-impl`）
- `FaceOnnxEngine` / `FaceDetOnnxEngine` / `PlateOnnxEngine` / `MilvusFaceVectorStore`
- `video.inference.python-cli-enabled=false`（local）

## Honest verdict

**Part2 Wave-A（face+plate Java ORT + Milvus）本机闭环已证。**  
**禁止 COMPLETE / 禁止删 Python VIDEO。** 巡检/后处理/姿态仍绑 py → 下一波讨论 sidecar。
