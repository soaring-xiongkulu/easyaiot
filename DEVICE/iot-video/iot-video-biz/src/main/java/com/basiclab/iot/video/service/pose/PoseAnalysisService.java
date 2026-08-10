package com.basiclab.iot.video.service.pose;

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
public class PoseAnalysisService {

    private static final String NO_ENGINE_MSG =
            "YOLO pose 引擎未安装或加载失败: 需 Python worker + yolo26n-pose.pt";

    private final PythonInferenceWorker pythonInferenceWorker;

    public boolean isEngineAvailable() {
        return pythonInferenceWorker.isPoseEngineAvailable();
    }

    public void validateImageBytes(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
    }

    public List<Map<String, Object>> extractPersons(byte[] imageBytes, double conf) {
        validateImageBytes(imageBytes);
        if (!isEngineAvailable()) {
            log.debug("pose extract skipped: {}", NO_ENGINE_MSG);
            return List.of();
        }
        WorkerResult worker = pythonInferenceWorker.poseExtract(imageBytes, conf);
        if (!worker.ok()) {
            log.warn("pose extract worker failed: {}", worker.error());
            return List.of();
        }
        return castPersonList(worker.data().get("persons"));
    }

    @SuppressWarnings("unchecked")
    private static List<Map<String, Object>> castPersonList(Object raw) {
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
