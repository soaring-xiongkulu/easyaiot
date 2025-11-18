package com.basiclab.iot.sink.messagebus.publisher.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 日志上报事件
 * <p>
 * 处理日志上报相关的消息：LOG_UPSTREAM_REPORT、LOG_DOWNSTREAM_REPORT_ACK
 *
 * @author 翱翔的雄库鲁
 */
public class LogEvent extends AbstractIotDeviceEvent {

    public LogEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

