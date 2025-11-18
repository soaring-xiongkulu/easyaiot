package com.basiclab.iot.sink.messagebus.publisher.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * PropertyEvent
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public class PropertyEvent extends AbstractIotDeviceEvent {

    public PropertyEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

