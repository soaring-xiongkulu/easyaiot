package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 事件上报确认下行消息事件监听器
 * <p>
 * 处理 Topic: EVENT_DOWNSTREAM_REPORT_ACK
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class EventDownstreamReportAckListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleEventDownstreamReportAckEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.EVENT_DOWNSTREAM_REPORT_ACK) {
                return;
            }

            log.info("[handleEventDownstreamReportAckEvent][处理事件上报确认下行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // TODO: 实现事件上报确认下行消息的业务逻辑

        } catch (Exception e) {
            log.error("[handleEventDownstreamReportAckEvent][处理事件上报确认下行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
