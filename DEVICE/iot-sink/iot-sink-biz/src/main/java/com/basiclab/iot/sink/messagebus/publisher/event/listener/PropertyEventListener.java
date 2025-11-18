package com.basiclab.iot.sink.messagebus.publisher.event.listener;

import com.basiclab.iot.sink.messagebus.publisher.event.PropertyEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * PropertyEventListener
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class PropertyEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handlePropertyEvent(PropertyEvent event) {
        try {
            log.info("[handlePropertyEvent][处理属性消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现属性消息处理逻辑
        } catch (Exception e) {
            log.error("[handlePropertyEvent][处理属性消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

