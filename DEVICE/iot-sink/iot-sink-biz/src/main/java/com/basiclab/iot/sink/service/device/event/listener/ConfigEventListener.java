package com.basiclab.iot.sink.service.device.event.listener;

import com.basiclab.iot.sink.service.device.event.ConfigEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 配置管理事件监听器
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class ConfigEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handleConfigEvent(ConfigEvent event) {
        try {
            log.info("[handleConfigEvent][处理配置消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现配置消息处理逻辑
        } catch (Exception e) {
            log.error("[handleConfigEvent][处理配置消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

