package com.basiclab.iot.device.config;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

import java.util.Properties;

@Configuration
public class KafkaConfig {
    @Value("${kafka.servers}")
    public String servers;
    @Value("${kafka.topic}")
    public String topic;
    @Value("${kafka.acks}")
    public String acks;
    @Value("${kafka.retries}")
    public String retries;
    @Value("${kafka.batchSize}")
    public String batchSize;
    @Value("${kafka.lingerMs}")
    public String lingerMs;
    @Value("${kafka.bufferMemory}")
    public String bufferMemory;
    @Value("${kafka.keySerializer}")
    public String keySerializer;
    @Value("${kafka.valueSerializer}")
    public String valueSerializer;

    public void pushMsgToKafka(String data) {
        Properties props = new Properties();
        props.put("bootstrap.servers", servers);//xxx服务器ip
        props.put("acks", acks);//所有follower都响应了才认为消息提交成功，即"committed"
        props.put("retries", retries);//retries = MAX 无限重试，直到你意识到出现了问题:)
        props.put("batch.size", batchSize);//producer将试图批处理消息记录，以减少请求次数.默认的批量处理消息字节数
        props.put("linger.ms", lingerMs);//延迟1ms发送，这项设置将通过增加小的延迟来完成--即，不是立即发送一条记录，producer将会等待给定的延迟时间以允许其他消息记录发送，这些消息记录可以批量处理
        props.put("buffer.memory", bufferMemory);//producer可以用来缓存数据的内存大小。
        props.put("key.serializer", keySerializer);
        props.put("value.serializer", valueSerializer);
        KafkaProducer<String, String> producer = new KafkaProducer<>(props);
        try {
            producer.send(new ProducerRecord<String, String>(topic, data));
        } catch (Exception e) {
            e.printStackTrace();
        }
        producer.close();
    }
}
