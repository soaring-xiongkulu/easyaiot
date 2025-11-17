package com.basiclab.iot.sink.messagebus.subscriber;

import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.messagebus.subscriber.handler.IotDownstreamMessageHandler;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.stereotype.Component;

import org.springframework.beans.factory.annotation.Autowired;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;
import java.util.List;

/**
 * IoT 网关下行消息订阅器（抽象实现）
 * <p>
 * 负责订阅来自消息总线的下行消息（平台 -> 设备），并委托给下行消息处理器进行业务处理
 * <p>
 * 注意：此订阅器订阅的是通用下行消息主题，具体的协议实现（如 MQTT、TCP）应该订阅各自网关特定的主题
 * <p>
 * 如果需要订阅特定网关的下行消息，请使用协议特定的订阅器（如 {@link com.basiclab.iot.sink.protocol.mqtt.IotMqttDownstreamSubscriber}）
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
@Component
@ConditionalOnBean(IotMessageBus.class)
public class IotDownstreamMessageSubscriber implements IotMessageSubscriber<IotDeviceMessage> {

    @Resource
    private IotMessageBus messageBus;

    @Autowired(required = false)
    private List<IotDownstreamMessageHandler> downstreamMessageHandlers;

    @PostConstruct
    public void subscribe() {
        messageBus.register(this);
        log.info("[subscribe][IoT 网关下行消息订阅成功，主题：{}]", getTopic());
    }

    @Override
    public String getTopic() {
        // 订阅通用设备消息主题，用于处理所有下行消息
        // 注意：此订阅器主要用于通用的下行消息处理，具体的协议实现应该订阅各自网关特定的主题
        return IotDeviceMessage.MESSAGE_BUS_DEVICE_MESSAGE_TOPIC;
    }

    @Override
    public String getGroup() {
        // 使用固定的 Group，确保所有网关实例共享消费
        return "iot-gateway-downstream-subscriber";
    }

    @Override
    public void onMessage(IotDeviceMessage message) {
        log.debug("[onMessage][接收到下行消息, messageId: {}, method: {}, deviceId: {}, serverId: {}]",
                message.getId(), message.getMethod(), message.getDeviceId(), message.getServerId());

        try {
            // 1. 校验消息
            if (message == null || message.getMethod() == null) {
                log.warn("[onMessage][消息或方法为空, messageId: {}, deviceId: {}]",
                        message != null ? message.getId() : null,
                        message != null ? message.getDeviceId() : null);
                return;
            }

            // 2. 只处理下行消息（通过 method 判断是否为下行消息）
            // 注意：这里可以根据实际需求添加更精确的过滤逻辑
            if (!isDownstreamMessage(message)) {
                log.debug("[onMessage][消息不是下行消息，跳过处理, messageId: {}, method: {}]",
                        message.getId(), message.getMethod());
                return;
            }

            // 3. 委托给下行消息处理器处理业务逻辑
            if (downstreamMessageHandlers != null && !downstreamMessageHandlers.isEmpty()) {
                for (IotDownstreamMessageHandler handler : downstreamMessageHandlers) {
                    try {
                        boolean success = handler.handleDownstreamMessage(message);
                        if (success) {
                            log.debug("[onMessage][下行消息处理成功, messageId: {}, method: {}, deviceId: {}, handler: {}]",
                                    message.getId(), message.getMethod(), message.getDeviceId(),
                                    handler.getClass().getSimpleName());
                        } else {
                            log.warn("[onMessage][下行消息处理失败, messageId: {}, method: {}, deviceId: {}, handler: {}]",
                                    message.getId(), message.getMethod(), message.getDeviceId(),
                                    handler.getClass().getSimpleName());
                        }
                    } catch (Exception e) {
                        log.error("[onMessage][下行消息处理器执行异常, messageId: {}, method: {}, deviceId: {}, handler: {}]",
                                message.getId(), message.getMethod(), message.getDeviceId(),
                                handler.getClass().getSimpleName(), e);
                    }
                }
            } else {
                log.debug("[onMessage][未配置下行消息处理器，跳过处理, messageId: {}]", message.getId());
            }
        } catch (Exception e) {
            log.error("[onMessage][处理下行消息失败, messageId: {}, method: {}, deviceId: {}]",
                    message.getId(), message.getMethod(), message.getDeviceId(), e);
        }
    }

    /**
     * 判断是否为下行消息
     * <p>
     * 下行消息：从平台发送到设备的消息
     * 上行消息：从设备发送到平台的消息
     *
     * @param message 设备消息
     * @return 是否为下行消息
     */
    private boolean isDownstreamMessage(IotDeviceMessage message) {
        // 通过工具类判断是否为上行消息，取反即为下行消息
        return !IotDeviceMessageUtils.isUpstreamMessage(message);
    }

}

