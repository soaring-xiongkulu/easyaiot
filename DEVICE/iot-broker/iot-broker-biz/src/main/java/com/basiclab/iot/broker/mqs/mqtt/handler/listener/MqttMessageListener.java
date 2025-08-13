package com.basiclab.iot.broker.mqs.mqtt.handler.listener;

import com.basiclab.iot.broker.mqs.mqtt.handler.TopicHandler;
import com.basiclab.iot.broker.mqs.mqtt.handler.event.MqttMessageEvent;
import com.basiclab.iot.broker.mqs.mqtt.handler.factory.TopicHandlerFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;


/**
 * @description:
 * @packagename: com.basiclab.iot.mqtt.handle.listener
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2023-04-28 14:43
 **/
@Component
@Slf4j
public class MqttMessageListener {

    private final TopicHandlerFactory topicHandlerFactory;

    @Autowired
    public MqttMessageListener(TopicHandlerFactory topicHandlerFactory) {
        this.topicHandlerFactory = topicHandlerFactory;
    }

    @EventListener
    public void handleMessage(MqttMessageEvent event) {
        // 校验并处理Topic
        processTopic(event.getTopic(), event.getQos(), event.getMessage());
    }

    private void processTopic(String topic, String qos, String body) {
        // Using the TopicHandlerFactory to find the matching handler
        TopicHandler matchingHandler = topicHandlerFactory.findMatchingHandler(topic);

        if (matchingHandler != null) {
            matchingHandler.handle(topic, qos, body);
        } else {
            // Handle the case when no topic matches
            log.warn("No topic handler found for topic: {}", topic);
        }
    }
}