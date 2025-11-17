package com.basiclab.iot.sink.service.device.event.listener;

import com.basiclab.iot.sink.service.device.event.ShadowEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 设备影子事件监听器
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class ShadowEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handleShadowEvent(ShadowEvent event) {
        try {
            log.info("[handleShadowEvent][处理设备影子消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现设备影子消息处理逻辑
        } catch (Exception e) {
            log.error("[handleShadowEvent][处理设备影子消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

