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
        data.put("collection", "face_vectors");
        data.put("status", "unavailable");
        data.put("recognition_model_loaded", false);
        data.put("recognition_model_downloading", false);
        return data;
    }

    public Map<String, Object> modelStatus() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("exists", false);
        data.put("downloading", false);
        data.put("path", "VIDEO/face_rec.onnx");
        data.put("size_bytes", 0);
        return data;
    }

    public Map<String, Object> startDownload() {
        Map<String, Object> data = modelStatus();
        data.put("started", false);
        return data;
    }
}
