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
 * IotDownstreamMessageSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
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

