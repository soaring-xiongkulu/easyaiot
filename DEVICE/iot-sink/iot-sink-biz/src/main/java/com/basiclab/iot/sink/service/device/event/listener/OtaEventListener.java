package com.basiclab.iot.sink.service.device.event.listener;

import com.basiclab.iot.sink.service.device.event.OtaEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * OTA 固件升级事件监听器
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class OtaEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handleOtaEvent(OtaEvent event) {
        try {
            log.info("[handleOtaEvent][处理 OTA 消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现 OTA 消息处理逻辑
        } catch (Exception e) {
            log.error("[handleOtaEvent][处理 OTA 消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

