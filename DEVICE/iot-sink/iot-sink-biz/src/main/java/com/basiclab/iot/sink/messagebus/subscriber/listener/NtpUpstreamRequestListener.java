package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * NTP同步请求上行消息事件监听器
 * <p>
 * 处理 Topic: NTP_UPSTREAM_REQUEST
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class NtpUpstreamRequestListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleNtpUpstreamRequestEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.NTP_UPSTREAM_REQUEST) {
                return;
            }

            log.info("[handleNtpUpstreamRequestEvent][处理NTP同步请求上行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // TODO: 实现NTP同步请求上行消息的业务逻辑

        } catch (Exception e) {
            log.error("[handleNtpUpstreamRequestEvent][处理NTP同步请求上行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
