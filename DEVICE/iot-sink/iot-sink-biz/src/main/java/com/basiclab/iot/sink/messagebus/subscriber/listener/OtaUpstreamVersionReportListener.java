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
 * OTA版本上报上行消息事件监听器
 * <p>
 * 处理 Topic: OTA_UPSTREAM_VERSION_REPORT
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class OtaUpstreamVersionReportListener {

    @Resource
    private DeviceDataStorageService deviceDataStorageService;

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleOtaUpstreamVersionReportEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.OTA_UPSTREAM_VERSION_REPORT) {
                return;
            }

            log.info("[handleOtaUpstreamVersionReportEvent][处理OTA版本上报上行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // 存储数据到TDEngine和Redis
            deviceDataStorageService.storeDeviceData(event.getMessage(), event.getTopicEnum());

        } catch (Exception e) {
            log.error("[handleOtaUpstreamVersionReportEvent][处理OTA版本上报上行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
