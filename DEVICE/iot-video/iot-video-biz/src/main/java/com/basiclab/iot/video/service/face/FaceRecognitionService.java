package com.basiclab.iot.video.service.face;

import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.inference.PythonInferenceWorker;
import com.basiclab.iot.video.inference.PythonInferenceWorker.WorkerResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class FaceRecognitionService {

    private static final String NO_ENGINE_MSG =
            "InsightFace 未安装或加载失败: 推理引擎不可用（需 Python worker + face_rec.onnx + Milvus）";

    /** Python face_library_service.add_entry L323-326 → face.py ValueError → HTTP 400. */
    public static final String FACE_MODEL_MISSING_ENTRY_MSG =
            "人脸特征模型 face_rec.onnx 未安装，请在人脸库页面下载安装后再录入";

    private final PythonInferenceWorker pythonInferenceWorker;

    public boolean isEngineAvailable() {
        return pythonInferenceWorker.isFaceEngineAvailable();
    }

    public void ensureFaceDetectable(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "上传文件不能为空");
        }
        if (!isEngineAvailable()) {
            throw new VideoBusinessException(500, NO_ENGINE_MSG);
        }
    }

    /** Entry path: Python hard-fails 400 when model missing — does not soft-save (face.py L282-283). */
    public void validateFaceEntryImage(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传人脸照片");
        }
        if (!isEngineAvailable()) {
            throw new VideoBusinessException(400, FACE_MODEL_MISSING_ENTRY_MSG);
        }
    }

    /**
     * Python face_library_service.add_entry L322-328 → extract_and_crop_largest_face.
     * Returns crop JPEG bytes and optional normalized embedding list for Milvus insert.
     */
    public FaceCropResult extractCropForEntry(byte[] imageBytes) {
        validateFaceEntryImage(imageBytes);
        WorkerResult worker = pythonInferenceWorker.faceExtractCrop(imageBytes);
        if (!worker.ok()) {
            String err = worker.error() != null ? worker.error() : "人脸特征提取失败";
            if (err.contains("face_rec.onnx") || err.contains("未安装")) {
                throw new VideoBusinessException(400, FACE_MODEL_MISSING_ENTRY_MSG);
            }
            if (err.contains("未检测到人脸")) {
                throw new VideoBusinessException(400, err);
            }
            throw new VideoBusinessException(500, "人脸特征提取失败: " + err);
        }
        Object cropBase64 = worker.data().get("crop_jpeg_base64");
        if (cropBase64 == null || String.valueOf(cropBase64).isBlank()) {
            throw new VideoBusinessException(400, "图片中未检测到人脸，请上传正面清晰的人脸照片");
        }
        try {
            byte[] cropBytes = java.util.Base64.getDecoder().decode(String.valueOf(cropBase64));
            List<Double> embedding = castEmbeddingList(worker.data().get("embedding"));
            return new FaceCropResult(cropBytes, embedding);
        } catch (IllegalArgumentException ex) {
            throw new VideoBusinessException(500, "人脸特征提取失败: crop decode error");
        }
    }

    /** Python face_library_service.add_entry L362-370 → add_face_to_library. */
    public String addFaceToLibrary(
            int libraryId,
            int faceEntryId,
            String personName,
            String personCode,
            List<Double> embedding
    ) {
        WorkerResult worker = pythonInferenceWorker.faceAddToLibrary(
                libraryId, faceEntryId, personName, personCode, embedding);
        if (!worker.ok()) {
            throw new VideoBusinessException(500, "Milvus 入库失败: " + worker.error());
        }
        Object milvusId = worker.data().get("milvus_id");
        return milvusId != null ? String.valueOf(milvusId) : null;
    }

    /** Python face_library_service.update_entry L463-467 → delete_by_milvus_id (best-effort). */
    public void deleteFaceByMilvusId(String milvusId) {
        if (milvusId == null || milvusId.isBlank()) {
            return;
        }
        try {
            WorkerResult worker = pythonInferenceWorker.faceDeleteByMilvusId(milvusId);
            if (!worker.ok()) {
                log.warn("delete milvus_id {} failed: {}", milvusId, worker.error());
            }
        } catch (Exception ex) {
            log.warn("delete milvus_id {} failed: {}", milvusId, ex.getMessage());
        }
    }

    public record FaceCropResult(byte[] cropJpegBytes, List<Double> embedding) {}

    public Map<String, Object> recognize(byte[] imageBytes, int topK, Integer libraryId, Double threshold) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        if (!isEngineAvailable()) {
            throw new VideoBusinessException(500, "识别失败: " + NO_ENGINE_MSG);
        }
        WorkerResult worker = pythonInferenceWorker.faceRecognize(imageBytes, libraryId, threshold, topK);
        if (!worker.ok()) {
            throw new VideoBusinessException(500, "识别失败: " + worker.error());
        }
        Object result = worker.data().get("result");
        if (result instanceof Map<?, ?> map) {
            return castMap(map);
        }
        throw new VideoBusinessException(500, "识别失败: worker 返回格式异常");
    }

    public Map<String, Object> recognizeDeviceSnapshot(String deviceId, int topK, Integer libraryId, Double threshold) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("device_id", deviceId);
        result.put("captured_at", java.time.Instant.now().toString());
        throw new VideoBusinessException(500, "识别失败: RTSP 抓帧失败");
    }

    public Map<String, Object> matchInLibrary(int libraryId, byte[] imageBytes, Double threshold, int topK) {
        ensureFaceDetectable(imageBytes);
        double useThreshold = threshold != null ? threshold : 0.55;
        WorkerResult worker = pythonInferenceWorker.faceMatchInLibrary(
                writeTempImage(imageBytes), libraryId, useThreshold);
        if (!worker.ok()) {
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("matched", false);
            empty.put("candidates", List.of());
            empty.put("threshold", useThreshold);
            return empty;
        }
        Object nested = worker.data().get("result");
        if (nested instanceof Map<?, ?> map) {
            return castMap(map);
        }
        Map<String, Object> empty = new LinkedHashMap<>();
        empty.put("matched", false);
        empty.put("candidates", List.of());
        empty.put("threshold", useThreshold);
        return empty;
    }

    public Map<String, Object> matchImageFileInLibrary(int libraryId, String imagePath, double threshold) {
        if (imagePath == null || imagePath.isBlank()) {
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("matched", false);
            empty.put("candidates", List.of());
            empty.put("threshold", threshold);
            return empty;
        }
        if (!isEngineAvailable()) {
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("matched", false);
            empty.put("candidates", List.of());
            empty.put("threshold", threshold);
            empty.put("error", NO_ENGINE_MSG);
            return empty;
        }
        WorkerResult worker = pythonInferenceWorker.faceMatchInLibrary(imagePath, libraryId, threshold);
        if (!worker.ok()) {
            log.warn("face match worker failed libraryId={} path={}: {}", libraryId, imagePath, worker.error());
            Map<String, Object> empty = new LinkedHashMap<>();
            empty.put("matched", false);
            empty.put("candidates", List.of());
            empty.put("threshold", threshold);
            return empty;
        }
        Object nested = worker.data().get("result");
        if (nested instanceof Map<?, ?> map) {
            return castMap(map);
        }
        Map<String, Object> empty = new LinkedHashMap<>();
        empty.put("matched", false);
        empty.put("candidates", List.of());
        empty.put("threshold", threshold);
        return empty;
    }

    public List<Map<String, Object>> listLegacyFaces(String label, int limit) {
        return List.of();
    }

    public Map<String, Object> addLegacyFace(String label, byte[] imageBytes) {
        if (label == null || label.isBlank()) {
            throw new VideoBusinessException(400, "label 不能为空");
        }
        ensureFaceDetectable(imageBytes);
        return Map.of("label", label);
    }

    public Map<String, Object> updateLegacyFace(String label, byte[] imageBytes) {
        if (label == null || label.isBlank()) {
            throw new VideoBusinessException(400, "label 不能为空");
        }
        ensureFaceDetectable(imageBytes);
        return Map.of("label", label);
    }

    public Map<String, Object> deleteLegacyFace(String label) {
        if (label == null || label.isBlank()) {
            throw new VideoBusinessException(400, "label 不能为空");
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("label", label);
        result.put("deleted", 0);
        return result;
    }

    private String writeTempImage(byte[] imageBytes) {
        try {
            java.nio.file.Path tmp = java.nio.file.Files.createTempFile("face-infer-", ".jpg");
            java.nio.file.Files.write(tmp, imageBytes);
            return tmp.toString();
        } catch (Exception ex) {
            throw new VideoBusinessException(500, "识别失败: 无法写入临时图片");
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> castMap(Map<?, ?> map) {
        Map<String, Object> out = new LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : map.entrySet()) {
            out.put(String.valueOf(entry.getKey()), entry.getValue());
        }
        return out;
    }

    private static List<Double> castEmbeddingList(Object raw) {
        if (raw == null) {
            return List.of();
        }
        if (raw instanceof List<?> list) {
            List<Double> out = new ArrayList<>();
            for (Object item : list) {
                if (item instanceof Number number) {
                    out.add(number.doubleValue());
                }
            }
            return out;
        }
        return List.of();
    }
}
