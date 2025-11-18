package com.basiclab.iot.sink.messagebus.publisher.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * ShadowEvent
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public class ShadowEvent extends AbstractIotDeviceEvent {

    public ShadowEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

