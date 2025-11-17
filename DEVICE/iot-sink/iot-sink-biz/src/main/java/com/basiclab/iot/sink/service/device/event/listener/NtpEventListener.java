package com.basiclab.iot.sink.service.device.event.listener;

import com.basiclab.iot.sink.service.device.event.NtpEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * NTP 时钟同步事件监听器
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class NtpEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handleNtpEvent(NtpEvent event) {
        try {
            log.info("[handleNtpEvent][处理 NTP 消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现 NTP 消息处理逻辑
        } catch (Exception e) {
            log.error("[handleNtpEvent][处理 NTP 消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

