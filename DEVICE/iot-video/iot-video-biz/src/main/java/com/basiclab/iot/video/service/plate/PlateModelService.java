package com.basiclab.iot.video.service.plate;

import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class PlateModelService {

    public Map<String, Object> health() {
        return plateModelStatusPayload();
    }

    public Map<String, Object> modelStatus() {
        return plateModelStatusPayload();
    }

    private Map<String, Object> plateModelStatusPayload() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("exists", false);
        data.put("detect_model", "plate_detect.onnx");
        data.put("rec_model", "plate_rec.onnx");
        data.put("detect_path", "VIDEO/plate_detect.onnx");
        data.put("rec_path", "VIDEO/plate_rec.onnx");
        data.put("downloading", false);
        data.put("stage", "idle");
        data.put("progress", 0);
        data.put("error", null);
        return data;
    }

    public Map<String, Object> startDownload() {
        Map<String, Object> data = modelStatus();
        data.put("started", false);
        return data;
    }
}
