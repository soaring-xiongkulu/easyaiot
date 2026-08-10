package com.basiclab.iot.video.service.plate;

import com.basiclab.iot.video.exception.VideoBusinessException;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class PlateRecognitionService {

    private static final String NO_ENGINE_MSG = "车牌识别引擎未安装或加载失败: Java 端暂未集成 PaddleOCR";

    public void ensurePlateEngine() {
        throw new VideoBusinessException(500, NO_ENGINE_MSG);
    }

    public List<Map<String, Object>> recognizePlates(byte[] imageBytes) {
        if (imageBytes == null || imageBytes.length == 0) {
            throw new VideoBusinessException(400, "请上传文件字段 file");
        }
        ensurePlateEngine();
        return List.of();
    }

    public List<Map<String, Object>> recognizeDeviceSnapshot(String deviceId) {
        throw new VideoBusinessException(500, "识别失败: RTSP 抓帧失败");
    }
}
