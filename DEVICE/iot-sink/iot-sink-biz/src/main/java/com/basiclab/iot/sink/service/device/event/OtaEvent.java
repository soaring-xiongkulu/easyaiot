package com.basiclab.iot.sink.service.device.event;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * OTA 固件升级事件
 * <p>
 * 处理 OTA 相关的消息：OTA_DOWNSTREAM_UPGRADE_TASK、OTA_UPSTREAM_VERSION_REPORT、
 * OTA_UPSTREAM_PROGRESS_REPORT、OTA_UPSTREAM_FIRMWARE_QUERY
 *
 * @author 翱翔的雄库鲁
 */
public class OtaEvent extends AbstractIotDeviceEvent {

    public OtaEvent(Object source, IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        super(source, message, topicEnum);
    }
}

