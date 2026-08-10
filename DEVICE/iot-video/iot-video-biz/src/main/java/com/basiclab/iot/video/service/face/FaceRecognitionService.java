package com.basiclab.iot.video.service.face;

import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.inference.PythonInferenceWorker;
import com.basiclab.iot.video.inference.PythonInferenceWorker.WorkerResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class FaceRecognitionService {

    private static final String NO_ENGINE_MSG =
            "InsightFace 未安装或加载失败: 推理引擎不可用（需 Python worker + face_rec.onnx + Milvus）";

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
}
