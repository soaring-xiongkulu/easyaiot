package com.basiclab.iot.sink.service.device.event.listener;

import com.basiclab.iot.sink.service.device.event.EventMessageEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 事件上报事件监听器
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class EventMessageEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handleEventMessageEvent(EventMessageEvent event) {
        try {
            log.info("[handleEventMessageEvent][处理事件上报消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现事件上报消息处理逻辑
        } catch (Exception e) {
            log.error("[handleEventMessageEvent][处理事件上报消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

