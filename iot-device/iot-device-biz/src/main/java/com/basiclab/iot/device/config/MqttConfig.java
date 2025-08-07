package com.basiclab.iot.device.config;

import com.basiclab.iot.device.callback.MqttCallback;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;


@Configuration
public class MqttConfig {
    @Autowired
    @Lazy
    private MqttCallback mqttCallback;
    @Value("${emqx.topic}")
    private String defaultTopic;

    @Value("${emqx.enabled}")
    private boolean enabled;

    @Bean
    public MqttCallback getMqttSubscribeClient() {
        if (enabled == true) {
            String mqtt_topic[] = defaultTopic.split(",");
            mqttCallback.connectEmqx();
            for (int i = 0; i < mqtt_topic.length; i++) {
                mqttCallback.subscribe(mqtt_topic[i], 0);
            }
        }
        System.out.println("重连成功...");
        return mqttCallback;
    }
}
