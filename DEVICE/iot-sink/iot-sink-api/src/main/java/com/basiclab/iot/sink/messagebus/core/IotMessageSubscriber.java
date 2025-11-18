package com.basiclab.iot.sink.messagebus.core;

/**
 * IotMessageSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface IotMessageSubscriber<T> {

    /**
     * @return 主题
     */
    String getTopic();

    /**
     * @return 分组
     */
    String getGroup();

    /**
     * 处理接收到的消息
     *
     * @param message 消息内容
     */
    void onMessage(T message);

}