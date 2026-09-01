package com.basiclab.iot.sink.messagebus.config;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.*;
import org.springframework.kafka.listener.ContainerProperties;

import java.util.HashMap;
import java.util.Map;

/**
 * KafkaConfig
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Configuration
@ConditionalOnProperty(prefix = "spring.kafka.iot.producer", name = "bootstrap-servers")
public class KafkaConfig {

    @Value("${spring.kafka.iot.producer.bootstrap-servers}")
    private String producerBootstrapServers;

    @Value("${spring.kafka.iot.producer.acks:all}")
    private String acks;

    @Value("${spring.kafka.iot.producer.retries:3}")
    private String retries;

    @Value("${spring.kafka.iot.producer.batch-size:104857600}")
    private String batchSize;

    @Value("${spring.kafka.iot.producer.buffer-memory:104857600}")
    private String bufferMemory;

    @Value("${spring.kafka.iot.consumer.bootstrap-servers}")
    private String consumerBootstrapServers;

    @Value("${spring.kafka.iot.consumer.group-id:iot-sink}")
    private String defaultGroupId;

    @Value("${spring.kafka.iot.consumer.enable-auto-commit:false}")
    private boolean enableAutoCommit;

    @Value("${spring.kafka.iot.consumer.auto-offset-reset:latest}")
    private String autoOffsetReset;

    @Value("${spring.kafka.iot.consumer.max-poll-records:100}")
    private String maxPollRecords;

    @Value("${spring.kafka.iot.properties.session.timeout.ms:10000}")
    private String sessionTimeout;

    @Value("${spring.kafka.iot.properties.max.poll.interval.ms:600000}")
    private String maxPollIntervalTime;

    /**
     * 告警消费并发线程数，建议不超过告警主题分区数（默认 64）
     */
    @Value("${spring.kafka.iot.listener.concurrency:16}")
    private int listenerConcurrency;

    /**
     * LLM 研判队列消费并发线程数（独立于告警消费，慢链路隔离）
     */
    @Value("${spring.kafka.iot.llm-judge.concurrency:3}")
    private int llmJudgeConcurrency;

    @Value("${spring.kafka.iot.llm-judge.max-poll-records:50}")
    private String llmJudgeMaxPollRecords;

    @Value("${spring.kafka.iot.llm-judge.max-poll-interval-ms:300000}")
    private String llmJudgeMaxPollInterval;

    @Value("${spring.kafka.iot.llm-judge.session-timeout-ms:10000}")
    private String llmJudgeSessionTimeout;

    @Bean
    public Map<String, Object> producerConfigs() {
        Map<String, Object> props = new HashMap<>(16);
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, producerBootstrapServers);
        props.put(ProducerConfig.ACKS_CONFIG, acks);
        props.put(ProducerConfig.RETRIES_CONFIG, retries);
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, batchSize);
        props.put(ProducerConfig.LINGER_MS_CONFIG, "5000");
        props.put(ProducerConfig.BUFFER_MEMORY_CONFIG, bufferMemory);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        return props;
    }

    @Bean
    public ProducerFactory<String, String> producerFactory() {
        return new DefaultKafkaProducerFactory<>(producerConfigs());
    }

    @Bean
    public KafkaTemplate<String, String> iotKafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }

    @Bean
    public Map<String, Object> consumerConfigs() {
        Map<String, Object> propsMap = new HashMap<>(16);
        propsMap.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, consumerBootstrapServers);
        propsMap.put(ConsumerConfig.GROUP_ID_CONFIG, defaultGroupId);
        propsMap.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, enableAutoCommit);
        propsMap.put(ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, "2000");
        propsMap.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, autoOffsetReset);
        propsMap.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, maxPollIntervalTime);
        propsMap.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, maxPollRecords);
        propsMap.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, sessionTimeout);
        propsMap.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        propsMap.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        return propsMap;
    }

    @Bean(name = "iotKafkaDefaultGroupId")
    public String iotKafkaDefaultGroupId() {
        return defaultGroupId;
    }

    @Bean(name = "iotKafkaConsumerBootstrapServers")
    public String iotKafkaConsumerBootstrapServers() {
        return consumerBootstrapServers;
    }

    /**
     * 创建消费者配置消费者
     *
     * @return
     */
    @Bean
    public ConsumerFactory<String, String> iotConsumerFactory() {
        return new DefaultKafkaConsumerFactory<>(consumerConfigs());
    }

    /**
     * 消费者监听容器工厂
     *
     * @return
     */
    @Bean(name = "iotKafkaListenerContainerFactory")
    public ConcurrentKafkaListenerContainerFactory<String, String> iotKafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, String> factory = new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(iotConsumerFactory());
        factory.setConcurrency(listenerConcurrency);
        // 设置手动确认模式，支持Acknowledgment参数
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        return factory;
    }

    /**
     * LLM 研判队列消费者配置（独立 group 语义在监听注解处指定；此处仅隔离并发与拉取参数）
     */
    @Bean
    public Map<String, Object> llmJudgeConsumerConfigs() {
        Map<String, Object> propsMap = consumerConfigs();
        propsMap.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, llmJudgeMaxPollRecords);
        propsMap.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, llmJudgeMaxPollInterval);
        propsMap.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, llmJudgeSessionTimeout);
        return propsMap;
    }

    @Bean
    public ConsumerFactory<String, String> llmJudgeConsumerFactory() {
        return new DefaultKafkaConsumerFactory<>(llmJudgeConsumerConfigs());
    }

    /**
     * LLM 研判队列监听容器工厂（独立并发，慢链路不占用告警消费线程）
     */
    @Bean(name = "iotLlmJudgeKafkaListenerContainerFactory")
    public ConcurrentKafkaListenerContainerFactory<String, String> iotLlmJudgeKafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, String> factory = new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(llmJudgeConsumerFactory());
        factory.setConcurrency(llmJudgeConcurrency);
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        return factory;
    }
}
