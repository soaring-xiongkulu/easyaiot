package com.basiclab.iot.video.service.plate;

import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.inference.PythonInferenceWorker;
import com.basiclab.iot.video.inference.PythonInferenceWorker.WorkerResult;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class PlateRecognitionService {

    private static final String NO_ENGINE_MSG =
            "车牌识别引擎未安装或加载失败: 需 Python worker + PaddleOCR ONNX 模型";

    private final PythonInferenceWorker pythonInferenceWorker;

    public boolean isEngineAvailable() {
        return pythonInferenceWorker.isPlateEngineAvailable();
    }

    public void ensurePlateEngine() {
        if (!isEngineAvailable()) {
            throw new VideoBusinessException(500, NO_ENGINE_MSG);
        }
    }

    public List<Map<String, Object>> recognizePlates(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        ensurePlateEngine();
        WorkerResult worker = pythonInferenceWorker.plateRecognize(imageBytes);
        if (!worker.ok()) {
            throw new VideoBusinessException(500, "识别失败: " + worker.error());
        }
        return castPlateList(worker.data().get("plates"));
    }

    public List<Map<String, Object>> recognizePlatesFromPath(String imagePath) {
        if (imagePath == null || imagePath.isBlank()) {
            return List.of();
        }
        if (!isEngineAvailable()) {
            return List.of();
        }
        WorkerResult worker = pythonInferenceWorker.plateRecognizePath(imagePath);
        if (!worker.ok()) {
            return List.of();
        }
        return castPlateList(worker.data().get("plates"));
    }

    public List<Map<String, Object>> recognizeDeviceSnapshot(String deviceId) {
        throw new VideoBusinessException(500, "识别失败: RTSP 抓帧失败");
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> castPlateList(Object raw) {
        if (raw instanceof List<?> list) {
            List<Map<String, Object>> out = new ArrayList<>();
            for (Object item : list) {
                if (item instanceof Map<?, ?> map) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    for (Map.Entry<?, ?> entry : map.entrySet()) {
                        row.put(String.valueOf(entry.getKey()), entry.getValue());
                    }
                    out.add(row);
                }
            }
            return out;
        }
        return List.of();
    }
}
