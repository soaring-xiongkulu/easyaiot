package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 属性事件
 * <p>
 * 处理属性相关的消息：PROPERTY_DOWNSTREAM_DESIRED_SET、PROPERTY_UPSTREAM_DESIRED_SET_ACK、
 * PROPERTY_DOWNSTREAM_DESIRED_QUERY、PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE、
 * PROPERTY_UPSTREAM_REPORT、PROPERTY_DOWNSTREAM_REPORT_ACK
 *
 * @author 翱翔的雄库鲁
 */
public class PropertyEvent extends AbstractIotDeviceEvent {

    public PropertyEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

