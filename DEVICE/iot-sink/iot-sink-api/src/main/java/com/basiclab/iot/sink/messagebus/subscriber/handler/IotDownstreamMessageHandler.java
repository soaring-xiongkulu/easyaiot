package com.basiclab.iot.sink.messagebus.subscriber.handler;

import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * IotDownstreamMessageHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface IotDownstreamMessageHandler {

    /**
     * 处理下行消息
     *
     * @param message 设备消息
     * @return 是否处理成功
     */
    boolean handleDownstreamMessage(IotDeviceMessage message);

}

