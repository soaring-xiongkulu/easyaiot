package com.basiclab.iot.sink.messagebus.publisher.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * DeviceInfoEvent
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public class DeviceInfoEvent extends AbstractIotDeviceEvent {

    public DeviceInfoEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

