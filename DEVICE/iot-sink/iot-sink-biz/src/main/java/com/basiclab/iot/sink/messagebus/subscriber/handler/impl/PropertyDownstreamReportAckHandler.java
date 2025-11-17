package com.basiclab.iot.sink.messagebus.subscriber.handler.impl;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.handler.IotDownstreamMessageHandler;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;

/**
 * 属性上报确认下行消息处理器
 * <p>
 * 处理 Topic: PROPERTY_DOWNSTREAM_REPORT_ACK
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class PropertyDownstreamReportAckHandler extends AbstractTopicHandler implements IotDownstreamMessageHandler {

    @Override
    public boolean handleDownstreamMessage(IotDeviceMessage message) {
        return handleAndPublishEvent(message, IotDeviceTopicEnum.PROPERTY_DOWNSTREAM_REPORT_ACK);
    }
}
