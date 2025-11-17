package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * 设备标签管理事件
 * <p>
 * 处理设备标签相关的消息：DEVICE_TAG_DOWNSTREAM_REPORT_ACK、DEVICE_TAG_UPSTREAM_DELETE、
 * DEVICE_TAG_UPSTREAM_REPORT、DEVICE_TAG_DOWNSTREAM_DELETE_ACK
 *
 * @author 翱翔的雄库鲁
 */
public class DeviceInfoEvent extends AbstractIotDeviceEvent {

    public DeviceInfoEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

