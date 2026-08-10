package com.basiclab.iot.video.service.plate;

import com.basiclab.iot.video.support.VideoModelPaths;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Plate model health — mirrors Python {@code get_plate_model_status()} / {@code plate.py} health.
 */
@Service
@RequiredArgsConstructor
public class PlateModelService {

    private final VideoModelPaths videoModelPaths;

    public Map<String, Object> health() {
        return plateModelStatusPayload();
    }

    public Map<String, Object> modelStatus() {
        return plateModelStatusPayload();
    }

    private Map<String, Object> plateModelStatusPayload() {
        Path detectPath = videoModelPaths.plateDetectModelPath();
        Path recPath = videoModelPaths.plateRecModelPath();
        boolean exists = videoModelPaths.isPlateModelReady();
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("exists", exists);
        data.put("detect_model", detectPath.getFileName().toString());
        data.put("rec_model", recPath.getFileName().toString());
        data.put("detect_path", detectPath.toString().replace('\\', '/'));
        data.put("rec_path", recPath.toString().replace('\\', '/'));
        data.put("downloading", false);
        data.put("stage", exists ? "done" : "idle");
        data.put("progress", exists ? 100 : 0);
        data.put("error", null);
        return data;
    }

    public Map<String, Object> startDownload() {
        Map<String, Object> data = modelStatus();
        data.put("started", false);
        return data;
    }
}
