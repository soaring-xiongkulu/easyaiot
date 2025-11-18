package com.basiclab.iot.sink.messagebus.subscriber.handler;

import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * IotUpstreamMessageHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
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

