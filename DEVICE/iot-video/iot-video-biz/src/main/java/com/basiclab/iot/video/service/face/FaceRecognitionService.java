package com.basiclab.iot.video.service.face;

import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class FaceRecognitionService {

    private static final String NO_ENGINE_MSG = "InsightFace 未安装或加载失败: Java 端暂未集成人脸推理引擎";

    /** ORT/InsightFace not wired on JVM yet; matching process uses explicit bypass when false. */
    public boolean isEngineAvailable() {
        return false;
    }

    public void ensureFaceDetectable(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "上传文件不能为空");
        }
        throw new VideoBusinessException(500, NO_ENGINE_MSG);
    }

    public Map<String, Object> recognize(byte[] imageBytes, int topK, Integer libraryId, Double threshold) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        throw new VideoBusinessException(500, "识别失败: " + NO_ENGINE_MSG);
    }

    public Map<String, Object> recognizeDeviceSnapshot(String deviceId, int topK, Integer libraryId, Double threshold) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("device_id", deviceId);
        result.put("captured_at", java.time.Instant.now().toString());
        throw new VideoBusinessException(500, "识别失败: RTSP 抓帧失败");
    }

    public Map<String, Object> matchInLibrary(int libraryId, byte[] imageBytes, Double threshold, int topK) {
        ensureFaceDetectable(imageBytes);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("matched", false);
        result.put("candidates", List.of());
        return result;
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
}
