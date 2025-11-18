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
import java.util.regex.Pattern;

/**
 * IotKafkaMessageBus
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
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
        // 如果 topic 包含 MQTT 通配符格式（如 iot/#），需要转换为 Kafka 正则表达式
        ContainerProperties containerProps;
        if (topic.contains("#") || topic.contains("+")) {
            // 将 MQTT 通配符格式转换为 Kafka 正则表达式
            // iot/# -> ^iot/.*
            // iot/+/device -> ^iot/[^/]+/device
            String regexPattern = convertMqttWildcardToKafkaRegex(topic);
            Pattern pattern = Pattern.compile(regexPattern);
            containerProps = new ContainerProperties(pattern);
            log.info("[register][将 MQTT 通配符主题 {} 转换为 Kafka 正则表达式: {}]", topic, regexPattern);
        } else {
            containerProps = new ContainerProperties(topic);
        }
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

    /**
     * 将 MQTT 通配符格式转换为 Kafka 正则表达式
     * 
     * MQTT 通配符规则：
     * - # 表示匹配零个或多个层级（只能放在最后）
     * - + 表示匹配单个层级
     * 
     * Kafka 使用 Java 正则表达式：
     * - .* 表示匹配任意字符（零个或多个）
     * - [^/]+ 表示匹配除 / 外的任意字符（一个或多个）
     * 
     * @param mqttTopic MQTT 格式的主题（如 iot/# 或 iot/+/device）
     * @return Kafka 正则表达式（如 ^iot/.* 或 ^iot/[^/]+/device）
     */
    private String convertMqttWildcardToKafkaRegex(String mqttTopic) {
        if (mqttTopic == null || mqttTopic.isEmpty()) {
            return mqttTopic;
        }
        
        // 转义特殊字符（除了 # 和 +）
        String regex = mqttTopic
                .replace(".", "\\.")
                .replace("$", "\\$")
                .replace("^", "\\^")
                .replace("[", "\\[")
                .replace("]", "\\]")
                .replace("(", "\\(")
                .replace(")", "\\)")
                .replace("{", "\\{")
                .replace("}", "\\}")
                .replace("|", "\\|");
        
        // 处理 # 通配符（只能出现在最后，匹配零个或多个层级）
        if (regex.endsWith("/#")) {
            regex = regex.substring(0, regex.length() - 2) + ".*";
        } else if (regex.endsWith("#")) {
            regex = regex.substring(0, regex.length() - 1) + ".*";
        }
        
        // 处理 + 通配符（匹配单个层级，即匹配除 / 外的任意字符）
        regex = regex.replace("+", "[^/]+");
        
        // 添加行首锚点
        if (!regex.startsWith("^")) {
            regex = "^" + regex;
        }
        
        return regex;
    }

}
