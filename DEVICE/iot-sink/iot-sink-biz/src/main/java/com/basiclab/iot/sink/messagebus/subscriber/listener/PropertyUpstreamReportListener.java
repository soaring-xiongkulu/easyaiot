package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * 属性上报上行消息事件监听器
 * <p>
 * 处理 Topic: PROPERTY_UPSTREAM_REPORT
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class PropertyUpstreamReportListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handlePropertyUpstreamReportEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.PROPERTY_UPSTREAM_REPORT) {
                return;
            }

            log.info("[handlePropertyUpstreamReportEvent][处理属性上报上行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // TODO: 实现属性上报上行消息的业务逻辑

        } catch (Exception e) {
            log.error("[handlePropertyUpstreamReportEvent][处理属性上报上行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
