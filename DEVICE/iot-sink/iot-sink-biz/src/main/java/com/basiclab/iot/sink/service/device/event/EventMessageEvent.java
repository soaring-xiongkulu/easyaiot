package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 事件上报事件
 * <p>
 * 处理事件上报相关的消息：EVENT_UPSTREAM_REPORT、EVENT_DOWNSTREAM_REPORT_ACK
 *
 * @author 翱翔的雄库鲁
 */
public class EventMessageEvent extends AbstractIotDeviceEvent {

    public EventMessageEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

