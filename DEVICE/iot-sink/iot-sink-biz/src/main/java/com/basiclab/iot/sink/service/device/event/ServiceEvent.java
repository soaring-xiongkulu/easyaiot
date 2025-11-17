package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 服务调用事件
 * <p>
 * 处理服务调用相关的消息：SERVICE_DOWNSTREAM_INVOKE、SERVICE_UPSTREAM_INVOKE_RESPONSE
 *
 * @author 翱翔的雄库鲁
 */
public class ServiceEvent extends AbstractIotDeviceEvent {

    public ServiceEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

