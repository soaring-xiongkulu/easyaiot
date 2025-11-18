package com.basiclab.iot.sink.messagebus.publisher.event.listener;

import com.basiclab.iot.sink.messagebus.publisher.event.DeviceInfoEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * DeviceInfoEventListener
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class DeviceInfoEventListener {

    @Async("iotDeviceEventExecutor")
    @EventListener
    public void handleDeviceInfoEvent(DeviceInfoEvent event) {
        try {
            log.info("[handleDeviceInfoEvent][处理设备标签消息，topic: {}, 类型: {}, 描述: {}]",
                    event.getMessage().getTopic(), event.getTopicEnum().name(), event.getTopicEnum().getDescription());
            // TODO: 实现设备标签消息处理逻辑
        } catch (Exception e) {
            log.error("[handleDeviceInfoEvent][处理设备标签消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}

