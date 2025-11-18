package com.basiclab.iot.sink.messagebus.subscriber.listener;

import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * ConfigDownstreamQueryAckListener
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class ConfigDownstreamQueryAckListener {

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleConfigDownstreamQueryAckEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.CONFIG_DOWNSTREAM_QUERY_ACK) {
                return;
            }

            log.info("[handleConfigDownstreamQueryAckEvent][处理配置查询确认下行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // TODO: 实现配置查询确认下行消息的业务逻辑

        } catch (Exception e) {
            log.error("[handleConfigDownstreamQueryAckEvent][处理配置查询确认下行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }
}
