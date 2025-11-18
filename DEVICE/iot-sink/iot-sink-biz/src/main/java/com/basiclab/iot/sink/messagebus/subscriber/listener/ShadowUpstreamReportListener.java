package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import com.basiclab.iot.sink.service.data.DeviceDataStorageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;

/**
 * 影子状态上报上行消息事件监听器
 * <p>
 * 处理 Topic: SHADOW_UPSTREAM_REPORT
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class ShadowUpstreamReportListener {

    @Resource
    private DeviceDataStorageService deviceDataStorageService;

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleShadowUpstreamReportEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.SHADOW_UPSTREAM_REPORT) {
                return;
            }

            log.info("[handleShadowUpstreamReportEvent][处理影子状态上报上行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // 存储数据到TDEngine和Redis
            deviceDataStorageService.storeDeviceData(event.getMessage(), event.getTopicEnum());

        } catch (Exception e) {
            log.error("[handleShadowUpstreamReportEvent][处理影子状态上报上行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
