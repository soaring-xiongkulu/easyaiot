package com.basiclab.iot.sink.protocol.emqx;

import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import com.basiclab.iot.sink.protocol.emqx.router.IotEmqxDownstreamHandler;
import lombok.extern.slf4j.Slf4j;

import javax.annotation.PostConstruct;

/**
 * IotEmqxDownstreamSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
public class IotEmqxDownstreamSubscriber implements IotMessageSubscriber<IotDeviceMessage> {

    private final IotEmqxDownstreamHandler downstreamHandler;

    private final IotMessageBus messageBus;

    private final IotEmqxUpstreamProtocol protocol;

    public IotEmqxDownstreamSubscriber(IotEmqxUpstreamProtocol protocol, IotMessageBus messageBus) {
        this.protocol = protocol;
        this.messageBus = messageBus;
        this.downstreamHandler = new IotEmqxDownstreamHandler(protocol);
    }

    @PostConstruct
    public void init() {
        messageBus.register(this);
    }

    @Override
    public String getTopic() {
        return IotDeviceMessageUtils.buildMessageBusGatewayDeviceMessageTopic(protocol.getServerId());
    }

    @Override
    public String getGroup() {
        // 保证点对点消费，需要保证独立的 Group，所以使用 Topic 作为 Group
        return getTopic();
    }

    @Override
    public void onMessage(IotDeviceMessage message) {
        log.debug("[onMessage][接收到下行消息, messageId: {}, method: {}, deviceId: {}]",
                message.getId(), message.getMethod(), message.getDeviceId());
        try {
            // 1. 校验
            String method = message.getMethod();
            if (method == null) {
                log.warn("[onMessage][消息方法为空, messageId: {}, deviceId: {}]",
                        message.getId(), message.getDeviceId());
                return;
            }

            // 2. 处理下行消息
            downstreamHandler.handle(message);
        } catch (Exception e) {
            log.error("[onMessage][处理下行消息失败, messageId: {}, method: {}, deviceId: {}]",
                    message.getId(), message.getMethod(), message.getDeviceId(), e);
        }
    }

}