package com.basiclab.iot.video.service.plate;

import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;

@Service
public class PlateModelService {

    public Map<String, Object> health() {
        Map<String, Object> data = modelStatus();
        data.put("status", "ok");
        return data;
    }

    public Map<String, Object> modelStatus() {
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("exists", false);
        data.put("downloading", false);
        data.put("path", "VIDEO/plate_rec.onnx");
        data.put("size_bytes", 0);
        return data;
    }

    public Map<String, Object> startDownload() {
        Map<String, Object> data = modelStatus();
        data.put("started", false);
        return data;
    }
}
