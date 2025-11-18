package com.basiclab.iot.sink.messagebus.config;

import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.local.IotLocalMessageBus;
import com.basiclab.iot.sink.messagebus.core.kafka.IotKafkaMessageBus;
import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.ApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;
import org.springframework.kafka.core.KafkaTemplate;

import java.util.Map;

/**
 * IotMessageBusAutoConfiguration
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@AutoConfiguration
@EnableConfigurationProperties(IotMessageBusProperties.class)
@Slf4j
public class IotMessageBusAutoConfiguration {

    @Bean
    @ConditionalOnBean(IotMessageBus.class)
    public IotDeviceMessageProducer deviceMessageProducer(@Lazy IotMessageBus messageBus) {
        log.info("[deviceMessageProducer][创建 IoT 设备消息生产者]");
        return new IotDeviceMessageProducer(messageBus);
    }

    // ==================== Local 实现 ====================

    @Configuration
    @ConditionalOnProperty(prefix = "basiclab.iot.message-bus", name = "type", havingValue = "local", matchIfMissing = true)
    public static class IotLocalMessageBusConfiguration {

        @Bean
        public IotLocalMessageBus iotLocalMessageBus(ApplicationContext applicationContext) {
            log.info("[iotLocalMessageBus][创建 IoT Local 消息总线]");
            return new IotLocalMessageBus(applicationContext);
        }

    }

    // ==================== Kafka 实现 ====================

    @Configuration
    @ConditionalOnProperty(prefix = "basiclab.iot.message-bus", name = "type", havingValue = "kafka")
    @ConditionalOnClass(KafkaTemplate.class)
    public static class IotKafkaMessageBusConfiguration {

        @Bean
        public IotKafkaMessageBus iotKafkaMessageBus(
                @org.springframework.beans.factory.annotation.Qualifier("iotKafkaTemplate") KafkaTemplate<String, String> kafkaTemplate,
                @org.springframework.beans.factory.annotation.Qualifier("iotKafkaConsumerBootstrapServers") String consumerBootstrapServers,
                @org.springframework.beans.factory.annotation.Qualifier("iotKafkaDefaultGroupId") String defaultGroupId,
                Map<String, Object> consumerConfigs) {
            log.info("[iotKafkaMessageBus][创建 IoT Kafka 消息总线]");
            return new IotKafkaMessageBus(kafkaTemplate, consumerBootstrapServers, defaultGroupId, consumerConfigs);
        }

    }

}