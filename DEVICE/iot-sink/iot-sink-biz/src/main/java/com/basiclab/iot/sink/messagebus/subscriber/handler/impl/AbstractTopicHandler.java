package com.basiclab.iot.sink.messagebus.subscriber.handler.impl;

import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationContext;

import javax.annotation.Resource;

/**
 * AbstractTopicHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
public abstract class AbstractTopicHandler {

    @Resource
    private ApplicationContext applicationContext;

    @Resource
    private IotGatewayProperties gatewayProperties;

    /**
     * 处理消息并发布事件
     *
     * @param message   设备消息
     * @param topicEnum Topic 枚举
     * @return 是否处理成功
     */
    protected boolean handleAndPublishEvent(IotDeviceMessage message, IotDeviceTopicEnum topicEnum) {
        try {
            // 1. 校验消息
            if (message == null || message.getTopic() == null) {
                log.warn("[handleAndPublishEvent][消息或 Topic 为空]");
                return false;
            }

            // 2. 匹配 Topic 枚举
            IotDeviceTopicEnum matchedTopicEnum = IotDeviceTopicEnum.matchTopic(message.getTopic());
            if (matchedTopicEnum != topicEnum) {
                return false;
            }

            // 3. 检查 Topic 是否应该被处理
            if (gatewayProperties != null && gatewayProperties.getTopic() != null) {
                boolean shouldProcess = gatewayProperties.getTopic().shouldProcess(topicEnum);
                if (!shouldProcess) {
                    log.debug("[handleAndPublishEvent][Topic 不在订阅列表中，跳过处理，topic: {}, topicEnum: {}]",
                            message.getTopic(), topicEnum.name());
                    return false;
                }
            }

            // 4. 发布事件，异步处理
            IotMessageBusEvent event = new IotMessageBusEvent(this, message, topicEnum);
            applicationContext.publishEvent(event);

            return true;
        } catch (Exception e) {
            log.error("[handleAndPublishEvent][处理消息失败，messageId: {}, topic: {}, topicEnum: {}]",
                    message != null ? message.getId() : null,
                    message != null ? message.getTopic() : null,
                    topicEnum != null ? topicEnum.name() : null, e);
            return false;
        }
    }
}

