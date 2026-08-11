package com.basiclab.iot.sink.service.media;

import java.util.Map;

public interface DvrUploadService {

    /** 处理 SRS/ZLM DVR Hook 或 Kafka 同构事件 */
    boolean processDvrEvent(Map<String, Object> event);
}
