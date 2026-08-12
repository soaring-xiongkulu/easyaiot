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
 * 网关代报子设备事件：按直连事件上报语义入库。
 */
@Slf4j
@Component
public class SubEventUpstreamReportListener {

    @Resource
    private DeviceDataStorageService deviceDataStorageService;

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleSubEventUpstreamReportEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.SUB_EVENT_UPSTREAM_REPORT) {
                return;
            }
            log.debug("[handleSubEventUpstreamReportEvent][网关代报事件 messageId={} deviceId={}]",
                    event.getMessage().getId(), event.getMessage().getDeviceId());
            deviceDataStorageService.storeDeviceData(event.getMessage(),
                    IotDeviceTopicEnum.EVENT_UPSTREAM_REPORT);
        } catch (Exception e) {
            log.error("[handleSubEventUpstreamReportEvent][处理失败 messageId={}]",
                    event.getMessage() != null ? event.getMessage().getId() : null, e);
        }
    }
}
