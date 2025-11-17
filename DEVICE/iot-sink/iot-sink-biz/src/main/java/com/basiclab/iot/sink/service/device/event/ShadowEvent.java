package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 设备影子事件
 * <p>
 * 处理设备影子相关的消息：SHADOW_DOWNSTREAM_DESIRED、SHADOW_UPSTREAM_REPORT
 *
 * @author 翱翔的雄库鲁
 */
public class ShadowEvent extends AbstractIotDeviceEvent {

    public ShadowEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

