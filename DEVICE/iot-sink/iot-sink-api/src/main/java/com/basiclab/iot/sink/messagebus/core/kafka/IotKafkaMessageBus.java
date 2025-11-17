package com.basiclab.iot.sink.messagebus.core.kafka;

import cn.hutool.core.util.TypeUtil;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.ConcurrentMessageListenerContainer;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.listener.MessageListener;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 基于 Kafka 的 {@link IotMessageBus} 实现类
 *
 * @author 翱翔的雄库鲁
 */
@Slf4j
public class IotKafkaMessageBus implements IotMessageBus {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final String bootstrapServers;
    private final String defaultGroupId;
    private final Map<String, Object> consumerConfigs;
    
    @Getter
    private final List<IotMessageSubscriber<?>> subscribers = new ArrayList<>();
    
    private final List<ConcurrentMessageListenerContainer<String, String>> containers = new ArrayList<>();

    public IotKafkaMessageBus(KafkaTemplate<String, String> kafkaTemplate, 
                               String bootstrapServers,
                               String defaultGroupId,
                               Map<String, Object> consumerConfigs) {
        this.kafkaTemplate = kafkaTemplate;
        this.bootstrapServers = bootstrapServers;
        this.defaultGroupId = defaultGroupId;
        this.consumerConfigs = consumerConfigs;
    }

    @PostConstruct
    public void init() {
        log.info("[init][Kafka 消息总线初始化完成]");
    }

    @PreDestroy
    public void destroy() {
        // 停止所有容器
        for (ConcurrentMessageListenerContainer<String, String> container : containers) {
            try {
                container.stop();
                log.info("[destroy][停止 Kafka 消费者容器成功]");
            } catch (Exception e) {
                log.error("[destroy][停止 Kafka 消费者容器异常]", e);
            }
        }
        log.info("[destroy][Kafka 消息总线销毁完成]");
    }

    @Override
    public void post(String topic, Object message) {
        try {
            String messageJson = JsonUtils.toJsonString(message);
            kafkaTemplate.send(topic, messageJson);
            log.debug("[post][topic({}) 发送消息成功]", topic);
        } catch (Exception e) {
            log.error("[post][topic({}) 发送消息失败]", topic, e);
            throw new RuntimeException("发送消息到 Kafka 失败", e);
        }
    }

    @Override
    public void register(IotMessageSubscriber<?> subscriber) {
        Type type = TypeUtil.getTypeArgument(subscriber.getClass(), 0);
        if (type == null) {
            throw new IllegalStateException(String.format("类型(%s) 需要设置消息类型", subscriber.getClass().getName()));
        }

        String topic = subscriber.getTopic();
        String groupId = subscriber.getGroup() != null ? subscriber.getGroup() : defaultGroupId;

        // 创建消费者配置，基于基础配置，覆盖 group-id
        Map<String, Object> props = new HashMap<>(consumerConfigs);
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);

        // 创建消费者工厂
        ConsumerFactory<String, String> consumerFactory = new DefaultKafkaConsumerFactory<>(props);

        // 创建容器属性
        ContainerProperties containerProps = new ContainerProperties(topic);
        containerProps.setMessageListener(new MessageListener<String, String>() {
            @Override
            @SuppressWarnings("unchecked")
            public void onMessage(ConsumerRecord<String, String> record) {
                try {
                    String value = record.value();
                    Object message = JsonUtils.parseObject(value, type);
                    ((IotMessageSubscriber<Object>) subscriber).onMessage(message);
                } catch (Exception e) {
                    log.error("[onMessage][topic({}/{}) 处理消息异常]",
                            topic, groupId, e);
                }
            }
        });
        containerProps.setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);

        // 创建并启动容器
        ConcurrentMessageListenerContainer<String, String> container =
                new ConcurrentMessageListenerContainer<>(consumerFactory, containerProps);
        container.setConcurrency(1);
        container.setBeanName("iot-kafka-listener-" + topic + "-" + groupId);
        container.start();

        containers.add(container);
        subscribers.add(subscriber);

        log.info("[register][topic({}/{}) 注册消费者({})成功]",
                topic, groupId, subscriber.getClass().getName());
    }

}
