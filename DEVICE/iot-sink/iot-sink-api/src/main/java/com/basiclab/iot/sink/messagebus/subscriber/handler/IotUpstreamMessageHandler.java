package com.basiclab.iot.sink.messagebus.subscriber.handler;

import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * IoT 上行消息处理器接口
 * <p>
 * 用于处理从设备发送到平台的上行消息（设备 -> 平台）
 * <p>
 * 实现此接口的类需要标注 {@link org.springframework.stereotype.Component} 注解，
 * 订阅器会自动发现并调用所有注册的处理器
 *
 * @author 翱翔的雄库鲁
 */
public interface IotUpstreamMessageHandler {

    /**
     * 处理上行消息
     *
     * @param message 设备消息
     * @return 是否处理成功
     */
    boolean handleUpstreamMessage(IotDeviceMessage message);

}

