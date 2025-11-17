package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 配置管理事件
 * <p>
 * 处理配置相关的消息：CONFIG_DOWNSTREAM_PUSH、CONFIG_DOWNSTREAM_QUERY_ACK、CONFIG_UPSTREAM_QUERY
 *
 * @author 翱翔的雄库鲁
 */
public class ConfigEvent extends AbstractIotDeviceEvent {

    public ConfigEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

