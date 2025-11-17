package com.basiclab.iot.sink.messagebus.subscriber.handler.impl;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.handler.IotDownstreamMessageHandler;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;

/**
 * 属性期望值设置下行消息处理器
 * <p>
 * 处理 Topic: PROPERTY_DOWNSTREAM_DESIRED_SET
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
public class PropertyDownstreamDesiredSetHandler extends AbstractTopicHandler implements IotDownstreamMessageHandler {

    @Override
    public boolean handleDownstreamMessage(IotDeviceMessage message) {
        return handleAndPublishEvent(message, IotDeviceTopicEnum.PROPERTY_DOWNSTREAM_DESIRED_SET);
    }
}
