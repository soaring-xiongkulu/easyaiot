package com.basiclab.iot.message.consumer;

import com.basiclab.iot.message.domain.model.AlertNotificationMessage;
import com.basiclab.iot.message.service.AlertNotificationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

/**
 * 告警通知Kafka消费者
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
public class AlertNotificationConsumer {

    @Autowired
    private AlertNotificationService alertNotificationService;

    /**
     * 消费告警通知消息
     *
     * @param message 告警通知消息（Spring Kafka会自动反序列化为对象）
     * @param acknowledgment Kafka确认机制
     */
    @KafkaListener(
            topics = "${spring.kafka.alert-notification.topic:iot-alert-notification}",
            groupId = "${spring.kafka.alert-notification.group-id:iot-message-alert-notification-consumer}"
    )
    public void consumeAlertNotification(
            @Payload AlertNotificationMessage message,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {
        
        try {
            log.info("收到告警通知消息: topic={}, partition={}, offset={}, alertId={}", 
                    topic, partition, offset, message != null ? message.getAlertId() : null);
            
            if (message == null) {
                log.error("告警通知消息为空");
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }
            
            // 处理告警通知
            alertNotificationService.processAlertNotification(message);
            
            // 确认消息已处理
            if (acknowledgment != null) {
                acknowledgment.acknowledge();
            }
            
        } catch (Exception e) {
            log.error("处理告警通知消息失败: alertId={}, error={}", 
                    message != null ? message.getAlertId() : null, e.getMessage(), e);
            // 注意：这里不确认消息，让Kafka重新投递，或者可以配置死信队列
            // 如果确认消息，错误消息会被丢弃
            // if (acknowledgment != null) {
            //     acknowledgment.acknowledge();
            // }
        }
    }
}

