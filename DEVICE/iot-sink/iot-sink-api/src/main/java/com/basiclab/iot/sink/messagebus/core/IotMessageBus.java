package com.basiclab.iot.sink.messagebus.core;

/**
 * IotMessageBus
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface IotMessageBus {

    /**
     * 发布消息到消息总线
     *
     * @param topic 主题
     * @param message 消息内容
     */
    void post(String topic, Object message);

    /**
     * 注册消息订阅者
     *
     * @param subscriber 订阅者
     */
    void register(IotMessageSubscriber<?> subscriber);

}