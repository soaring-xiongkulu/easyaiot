package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * OTA进度上报上行消息事件监听器
 * <p>
 * 处理 Topic: OTA_UPSTREAM_PROGRESS_REPORT
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class OtaUpstreamProgressReportListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleOtaUpstreamProgressReportEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.OTA_UPSTREAM_PROGRESS_REPORT) {
                return;
            }

            log.info("[handleOtaUpstreamProgressReportEvent][处理OTA进度上报上行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // TODO: 实现OTA进度上报上行消息的业务逻辑

        } catch (Exception e) {
            log.error("[handleOtaUpstreamProgressReportEvent][处理OTA进度上报上行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
