package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * PropertyDownstreamDesiredQueryListener
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class PropertyDownstreamDesiredQueryListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handlePropertyDownstreamDesiredQueryEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.PROPERTY_DOWNSTREAM_DESIRED_QUERY) {
                return;
            }

            log.info("[handlePropertyDownstreamDesiredQueryEvent][处理属性期望值查询下行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // TODO: 实现属性期望值查询下行消息的业务逻辑

        } catch (Exception e) {
            log.error("[handlePropertyDownstreamDesiredQueryEvent][处理属性期望值查询下行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
