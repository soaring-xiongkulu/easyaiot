package com.basiclab.iot.video.service.face;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Slf4j
@Service
public class FaceModelService {

    public Map<String, Object> health() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("milvus_uri", "");
        data.put("collection_name", "face_vectors");
        data.put("collection_exists", false);
        data.put("error", "Milvus unavailable (mini profile)");
        data.put("recognition_model_loaded", false);
        data.put("recognition_model_downloading", false);
        return data;
    }

    public Map<String, Object> modelStatus() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("exists", false);
        data.put("filename", "face_rec.onnx");
        data.put("path", "VIDEO/face_rec.onnx");
        data.put("size_bytes", 0);
        data.put("downloading", false);
        data.put("resumable", false);
        data.put("stage", "idle");
        data.put("progress", 0);
        data.put("downloaded_bytes", 0);
        data.put("total_bytes", 0);
        data.put("error", null);
        return data;
    }

    public Map<String, Object> startDownload() {
        Map<String, Object> data = modelStatus();
        data.put("started", false);
        return data;
    }
}
