package com.basiclab.iot.video.service.pose;

import com.basiclab.iot.video.exception.VideoBusinessException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class PoseAnalysisService {

  private static final String NO_ENGINE_MSG = "YOLO pose 引擎未安装或加载失败: Java 端暂未集成姿态推理";

  public void validateImageBytes(byte[] imageBytes) {
    if (imageBytes == null || imageBytes.length == 0) {
      throw new VideoBusinessException(400, "请上传文件字段 file");
    }
  }

  public List<Map<String, Object>> extractPersons(byte[] imageBytes, double conf) {
    validateImageBytes(imageBytes);
    log.debug("pose extract stub conf={}: {}", conf, NO_ENGINE_MSG);
    return List.of();
  }
}
