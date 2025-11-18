package com.basiclab.iot.sink.messagebus.publisher.event.listener;

import com.basiclab.iot.sink.messagebus.publisher.event.BroadcastEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * BroadcastEventListener
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class BroadcastEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handleBroadcastEvent(BroadcastEvent event) {
        try {
            log.info("[handleBroadcastEvent][处理广播消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现广播消息处理逻辑
        } catch (Exception e) {
            log.error("[handleBroadcastEvent][处理广播消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

