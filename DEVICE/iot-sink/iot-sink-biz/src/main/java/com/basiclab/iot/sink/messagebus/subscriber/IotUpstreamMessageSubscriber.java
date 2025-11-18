package com.basiclab.iot.sink.messagebus.subscriber;

import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.messagebus.subscriber.handler.IotUpstreamMessageHandler;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.stereotype.Component;

import org.springframework.beans.factory.annotation.Autowired;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;
import java.util.List;

/**
 * IotUpstreamMessageSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
@ConditionalOnBean(IotMessageBus.class)
public class IotUpstreamMessageSubscriber implements IotMessageSubscriber<IotDeviceMessage> {

    @Resource
    private IotMessageBus messageBus;

    @Autowired(required = false)
    private List<IotUpstreamMessageHandler> upstreamMessageHandlers;

    @PostConstruct
    public void subscribe() {
        messageBus.register(this);
        log.info("[subscribe][IoT 网关上行消息订阅成功，主题：{}]", getTopic());
    }

    @Override
    public String getTopic() {
        // 订阅通用设备消息主题（来自 iot-broker 或 iot-sink 的上行消息）
        return IotDeviceMessage.MESSAGE_BUS_DEVICE_MESSAGE_TOPIC;
    }

    @Override
    public String getGroup() {
        // 使用固定的 Group，确保所有网关实例共享消费
        return "iot-gateway-upstream-subscriber";
    }

    @Override
    public void onMessage(IotDeviceMessage message) {
        log.debug("[onMessage][接收到上行消息, messageId: {}, method: {}, deviceId: {}, serverId: {}]",
                message.getId(), message.getMethod(), message.getDeviceId(), message.getServerId());

        try {
            // 1. 校验消息
            if (message == null || message.getMethod() == null) {
                log.warn("[onMessage][消息或方法为空, messageId: {}, deviceId: {}]",
                        message != null ? message.getId() : null,
                        message != null ? message.getDeviceId() : null);
                return;
            }

            // 2. 委托给上行消息处理器处理业务逻辑
            if (upstreamMessageHandlers != null && !upstreamMessageHandlers.isEmpty()) {
                for (IotUpstreamMessageHandler handler : upstreamMessageHandlers) {
                    try {
                        boolean success = handler.handleUpstreamMessage(message);
                        if (success) {
                            log.debug("[onMessage][上行消息处理成功, messageId: {}, method: {}, deviceId: {}, handler: {}]",
                                    message.getId(), message.getMethod(), message.getDeviceId(),
                                    handler.getClass().getSimpleName());
                        } else {
                            log.warn("[onMessage][上行消息处理失败, messageId: {}, method: {}, deviceId: {}, handler: {}]",
                                    message.getId(), message.getMethod(), message.getDeviceId(),
                                    handler.getClass().getSimpleName());
                        }
                    } catch (Exception e) {
                        log.error("[onMessage][上行消息处理器执行异常, messageId: {}, method: {}, deviceId: {}, handler: {}]",
                                message.getId(), message.getMethod(), message.getDeviceId(),
                                handler.getClass().getSimpleName(), e);
                    }
                }
            } else {
                log.debug("[onMessage][未配置上行消息处理器，跳过处理, messageId: {}]", message.getId());
            }
        } catch (Exception e) {
            log.error("[onMessage][处理上行消息失败, messageId: {}, method: {}, deviceId: {}]",
                    message.getId(), message.getMethod(), message.getDeviceId(), e);
        }
    }

}

