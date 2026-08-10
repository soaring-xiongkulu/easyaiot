package com.basiclab.iot.video.config;

import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.core.ProducerFactory;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class AlertKafkaConfig {

    @Bean
    public ProducerFactory<String, String> alertKafkaProducerFactory(VideoProperties videoProperties) {
        VideoProperties.Kafka kafka = videoProperties.getKafka();
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, kafka.getBootstrapServers());
        props.put(ProducerConfig.CLIENT_ID_CONFIG, kafka.getClientId());
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.RETRIES_CONFIG, kafka.getRetries());
        props.put(ProducerConfig.REQUEST_TIMEOUT_MS_CONFIG, kafka.getRequestTimeoutMs());
        props.put(ProducerConfig.MAX_BLOCK_MS_CONFIG, kafka.getMaxBlockMs());
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, 65_536);
        props.put(ProducerConfig.LINGER_MS_CONFIG, 5);
        return new DefaultKafkaProducerFactory<>(props);
    }

    @Bean
    public KafkaTemplate<String, String> alertKafkaTemplate(ProducerFactory<String, String> alertKafkaProducerFactory) {
        return new KafkaTemplate<>(alertKafkaProducerFactory);
    }
}
