package com.basiclab.iot.broker.mqs.mqtt.handler;

/**
 * @description:
 * @packagename: com.basiclab.iot.mqtt.handler
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2023-05-05 22:45
 **/
public interface TopicHandler {

    /**
     * @param topic the MQTT topic the message was received on.
     * @param qos the quality of service level of the message.
     * @param body the payload of the message.
     */
    void handle(String topic, String qos, String body);
}
