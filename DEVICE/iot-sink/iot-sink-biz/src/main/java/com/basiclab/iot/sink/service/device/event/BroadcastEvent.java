package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 广播消息事件
 * <p>
 * 处理广播相关的消息：BROADCAST_DOWNSTREAM
 *
 * @author 翱翔的雄库鲁
 */
public class BroadcastEvent extends AbstractIotDeviceEvent {

    public BroadcastEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

