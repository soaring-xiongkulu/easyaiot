package com.basiclab.iot.sink.protocol.http;

import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import javax.annotation.PostConstruct;

/**
 * IotHttpDownstreamSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@RequiredArgsConstructor
@Slf4j
public class IotHttpDownstreamSubscriber implements IotMessageSubscriber<IotDeviceMessage> {

    private final IotHttpUpstreamProtocol protocol;

    private final IotMessageBus messageBus;

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
        log.info("[onMessage][IoT 网关 HTTP 协议不支持下行消息，忽略消息：{}]", message);
    }

}
