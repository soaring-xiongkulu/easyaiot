package com.basiclab.iot.device.callback;

import com.basiclab.iot.device.config.KafkaConfig;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class MqttCallback {
    @Autowired
    private PushKafkaCallback pushCallback;

    private static MqttClient client;

    private static MqttClient getClient() {
        return client;
    }

    private static void setClient(MqttClient client) {
        MqttCallback.client = client;
    }

    @Value("${emqx.username}")
    private String username;

    @Value("${emqx.password}")
    private String password;

    @Value("${emqx.serverURIs}")
    private String host;

    @Value("${emqx.clientId}")
    private String clientId;
    @Autowired
    private KafkaConfig kafkaHelper;
    @Value("${emqx.topic}")
    private String defaultTopic;

    @Value("${emqx.qos}")
    private int qos;

    @Value("${emqx.enabled}")
    private boolean enabled;

    @Value("${emqx.keepalive}")
    private int keepalive;

    @Value("${emqx.timeout}")
    private int timeout;

    public void connectEmqx() {
        MqttClient client;
        try {
            client = new MqttClient(host, clientId, new MemoryPersistence());
            MqttConnectOptions options = new MqttConnectOptions();
            options.setCleanSession(true);
            options.setUserName(username);
            options.setPassword(password.toCharArray());
            options.setConnectionTimeout(timeout);
            options.setKeepAliveInterval(keepalive);
            MqttCallback.setClient(client);
            client.setCallback(pushCallback);
            log.info("begin to connect to emqx:{}...", host);
            client.connect(options);
            String mqtt_topic[] = defaultTopic.split(",");
            for (int i = 0; i < mqtt_topic.length; i++) {
                subscribe(mqtt_topic[i], 0);//订阅主题
            }
            log.info("connect to emqx:{} success", host);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public boolean publish(int qos, boolean retained, String topic, String pushMessage) {
        MqttMessage message = new MqttMessage();
        message.setQos(qos);
        message.setRetained(retained);
        message.setPayload(pushMessage.getBytes());
        MqttTopic mTopic = MqttCallback.getClient().getTopic(topic);
        if (null == mTopic) {
            log.error("topic not exist");
        }
        MqttDeliveryToken token;
        try {
            token = mTopic.publish(message);
            token.waitForCompletion();
            return true;
        } catch (MqttPersistenceException e) {
            e.printStackTrace();
            return false;
        } catch (MqttException e) {
            e.printStackTrace();
            return false;
        }
    }

    public void subscribe(String topic, int qos) {
        try {
            MqttCallback.getClient().subscribe(topic, qos);
            log.info("subscribe topic:{}", topic);
        } catch (MqttException e) {
            e.printStackTrace();
        }
    }
}
