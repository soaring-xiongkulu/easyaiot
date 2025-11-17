package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * NTP 时钟同步事件
 * <p>
 * 处理 NTP 相关的消息：NTP_UPSTREAM_REQUEST、NTP_DOWNSTREAM_RESPONSE
 *
 * @author 翱翔的雄库鲁
 */
public class NtpEvent extends AbstractIotDeviceEvent {

    public NtpEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

