package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.Getter;
import org.springframework.context.ApplicationEvent;

/**
 * IoT 设备事件抽象基类
 * <p>
 * 所有设备消息处理事件都应该继承此类
 *
 * @author 翱翔的雄库鲁
 */
@Getter
public abstract class AbstractIotDeviceEvent extends ApplicationEvent {

    /**
     * 设备消息
     */
    private final IotDeviceMessage message;

    /**
     * Topic 枚举
     */
    private final IotDeviceTopicEnum topicEnum;

    public AbstractIotDeviceEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source);
        this.message = message;
        this.topicEnum = topicEnum;
    }
}

