package com.basiclab.iot.sink.messagebus.subscriber.handler.impl;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.handler.IotUpstreamMessageHandler;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;

/**
 * 设备标签上报上行消息处理器
 * <p>
 * 处理 Topic: DEVICE_TAG_UPSTREAM_REPORT
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class DeviceTagUpstreamReportHandler extends AbstractTopicHandler implements IotUpstreamMessageHandler {

    @Override
    public boolean handleUpstreamMessage(IotDeviceMessage message) {
        return handleAndPublishEvent(message, IotDeviceTopicEnum.DEVICE_TAG_UPSTREAM_REPORT);
    }
}
