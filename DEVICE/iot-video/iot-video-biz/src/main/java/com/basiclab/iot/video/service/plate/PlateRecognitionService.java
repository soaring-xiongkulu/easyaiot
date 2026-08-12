package com.basiclab.iot.video.service.plate;

import com.basiclab.iot.video.config.VideoProperties;
import com.basiclab.iot.video.exception.VideoBusinessException;
import com.basiclab.iot.video.inference.PythonInferenceWorker;
import com.basiclab.iot.video.inference.PythonInferenceWorker.WorkerResult;
import com.basiclab.iot.video.inference.onnx.PlateOnnxEngine;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Plate OCR: Part2 Wave-A prefers ORT Java; Python CLI only when python-cli-enabled.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PlateRecognitionService {

    private static final String NO_ENGINE_MSG =
            "车牌识别引擎未安装或加载失败: 需 plate_*.onnx（Java ORT）或开启 python-cli-enabled";

    private final VideoProperties videoProperties;
    private final PythonInferenceWorker pythonInferenceWorker;
    private final PlateOnnxEngine plateOnnxEngine;

    public boolean isEngineAvailable() {
        if (javaReady()) {
            return true;
        }
        return pythonCliAllowed() && pythonInferenceWorker.isPlateEngineAvailable();
    }

    private boolean javaReady() {
        return videoProperties.getInference().isOnnxEnabled() && plateOnnxEngine.isAvailable();
    }

    private boolean pythonCliAllowed() {
        VideoProperties.Inference inf = videoProperties.getInference();
        return inf.isEnabled() && inf.isPythonCliEnabled();
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
        if (javaReady()) {
            try {
                List<Map<String, Object>> plates = plateOnnxEngine.predictBytes(imageBytes, 0.25f);
                for (Map<String, Object> p : plates) {
                    p.put("engine", "onnx-java");
                }
                return plates;
            } catch (Exception ex) {
                if (!pythonCliAllowed()) {
                    throw new VideoBusinessException(500, "识别失败: " + ex.getMessage());
                }
                log.warn("Java plate OCR failed, fallback CLI: {}", ex.getMessage());
            }
        }
        if (!pythonCliAllowed()) {
            throw new VideoBusinessException(500, NO_ENGINE_MSG);
        }
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
        if (javaReady()) {
            try {
                byte[] bytes = Files.readAllBytes(Path.of(imagePath));
                List<Map<String, Object>> plates = plateOnnxEngine.predictBytes(bytes, 0.25f);
                for (Map<String, Object> p : plates) {
                    p.put("engine", "onnx-java");
                }
                return plates;
            } catch (Exception ex) {
                log.warn("Java plate OCR path failed {}: {}", imagePath, ex.getMessage());
                if (!pythonCliAllowed()) {
                    return List.of();
                }
            }
        }
        if (!pythonCliAllowed()) {
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
