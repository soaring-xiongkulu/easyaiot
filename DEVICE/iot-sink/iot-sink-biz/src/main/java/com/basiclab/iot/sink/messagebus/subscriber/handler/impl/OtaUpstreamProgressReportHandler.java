package com.basiclab.iot.sink.messagebus.subscriber.handler.impl;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.handler.IotUpstreamMessageHandler;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;

/**
 * OTA进度上报上行消息处理器
 * <p>
 * 处理 Topic: OTA_UPSTREAM_PROGRESS_REPORT
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class OtaUpstreamProgressReportHandler extends AbstractTopicHandler implements IotUpstreamMessageHandler {

    @Override
    public boolean handleUpstreamMessage(IotDeviceMessage message) {
        return handleAndPublishEvent(message, IotDeviceTopicEnum.OTA_UPSTREAM_PROGRESS_REPORT);
    }
}
