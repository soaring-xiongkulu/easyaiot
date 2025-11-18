package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * NtpDownstreamResponseListener
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class NtpDownstreamResponseListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleNtpDownstreamResponseEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.NTP_DOWNSTREAM_RESPONSE) {
                return;
            }

            log.info("[handleNtpDownstreamResponseEvent][处理NTP同步响应下行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // TODO: 实现NTP同步响应下行消息的业务逻辑

        } catch (Exception e) {
            log.error("[handleNtpDownstreamResponseEvent][处理NTP同步响应下行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
