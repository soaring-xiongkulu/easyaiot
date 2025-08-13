package com.basiclab.iot.broker.mqs.consumer.kafka;

import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.springframework.kafka.support.ProducerListener;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;

/**
 * @description: kafka消息发送回调
 * @packagename: com.basiclab.iot.common.kafka.handler
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2023-06-18 11:39
 **/
@Slf4j
@Component
public class KafkaSendResultHandler implements ProducerListener<String, String> {


    @Override
    public void onSuccess(ProducerRecord producerRecord, RecordMetadata recordMetadata) {

        log.info("消息发送成功：{}", producerRecord.toString());
    }

    @Override
    public void onError(ProducerRecord producerRecord, @Nullable RecordMetadata recordMetadata, Exception exception) {

        log.error("消息发送失败：{},{}", producerRecord.toString(), exception.getMessage());
    }
}
