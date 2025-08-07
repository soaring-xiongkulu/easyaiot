package com.basiclab.iot.device.callback;

import com.basiclab.iot.device.config.KafkaConfig;
import com.basiclab.iot.device.config.MqttConfig;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.text.SimpleDateFormat;
import java.util.Date;

@Component
@Slf4j
public class PushKafkaCallback implements org.eclipse.paho.client.mqttv3.MqttCallback {

    @Autowired
    private MqttConfig mqttConfig;
    @Autowired
    @Lazy
    private MqttCallback mqttCallback;
    @Autowired
    private KafkaConfig kafkaHelper;
    private static MqttClient client;
    public static PushKafkaCallback PushCallback;
    private static String _topic;
    private static int _qos;
    private static String _msg;

    @PostConstruct //通过@PostConstruct实现初始化bean之前进行的操作
    public void init() {
        PushCallback = this;
        PushCallback.kafkaHelper = this.kafkaHelper;
    }

    @Override
    public void connectionLost(Throwable throwable) {
        while (true) {
            try {//如果没有发生异常说明连接成功，如果发生异常，则死循环
                Thread.sleep(1000);
                // 连接丢失后，一般在这里面进行重连
                mqttCallback.connectEmqx();
                break;
            } catch (Exception e) {
                e.printStackTrace();
                continue;
            }
        }
    }

    @Override
    public void messageArrived(String topic, MqttMessage mqttMessage) throws Exception {
        String nowTime = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date());
        _topic = topic;
        _qos = mqttMessage.getQos();
        _msg = new String(mqttMessage.getPayload());
        System.out.println(nowTime + "  topic 数据： " + _topic);
        PushCallback.kafkaHelper.pushMsgToKafka(_msg);
    }

    public void pushDataToKafka(String msgData) {
        kafkaHelper.pushMsgToKafka(msgData);
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken iMqttDeliveryToken) {
        log.info("deliveryComplete---------" + iMqttDeliveryToken.isComplete());
    }

}

