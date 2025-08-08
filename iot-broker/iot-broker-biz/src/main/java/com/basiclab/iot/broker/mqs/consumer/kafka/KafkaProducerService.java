package com.basiclab.iot.broker.mqs.consumer.kafka;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;
import org.springframework.util.concurrent.ListenableFuture;
import org.springframework.util.concurrent.ListenableFutureCallback;

/**
 * @Description: kafka生产者
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @CreateDate: 2023/01/06$ 16:02$
 * @UpdateDate: 2023/01/06$ 16:02$
 */
@Service
@Slf4j
public class KafkaProducerService {

    @Autowired
    @Qualifier("iotKafkaTemplate")
    private KafkaTemplate iotKafkaTemplate;


    public void iotKafkaTemplateSendMsg(String topic, String msg) {
        log.info("iotKafkaTemplate sendMsg ,topic:{},msg:{}", topic, msg);

        ListenableFuture<SendResult<Integer, String>> sendMsg = iotKafkaTemplate.send(topic, msg);
        //消息确认
        sendMsg.addCallback(new ListenableFutureCallback<SendResult<Integer, String>>() {
            @Override
            public void onFailure(Throwable throwable) {
                log.error("send error,ex:{},topic:{},msg:{}", throwable, topic, msg);
            }

            @Override
            public void onSuccess(SendResult<Integer, String> stringStringSendResult) {
                log.info("send success,topic:{},msg:{}", topic, msg);
            }
        });
        log.info("kafka send end!");
    }
}
