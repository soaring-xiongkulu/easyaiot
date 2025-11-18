package com.basiclab.iot.sink.mq.producer;

import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import lombok.RequiredArgsConstructor;

/**
 * IotDeviceMessageProducer
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RequiredArgsConstructor
public class IotDeviceMessageProducer {

    private final IotMessageBus messageBus;

    /**
     * 发送设备消息
     *
     * @param message 设备消息
     */
    public void sendDeviceMessage(IotDeviceMessage message) {
        messageBus.post(IotDeviceMessage.MESSAGE_BUS_DEVICE_MESSAGE_TOPIC, message);
    }

    /**
     * 发送网关设备消息
     *
     * @param serverId 网关的 serverId 标识
     * @param message 设备消息
     */
    public void sendDeviceMessageToGateway(String serverId, IotDeviceMessage message) {
        messageBus.post(IotDeviceMessageUtils.buildMessageBusGatewayDeviceMessageTopic(serverId), message);
    }

}
