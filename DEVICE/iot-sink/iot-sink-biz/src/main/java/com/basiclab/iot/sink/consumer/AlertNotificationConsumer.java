package com.basiclab.iot.sink.consumer;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.domain.model.AlertNotificationMessage;
import com.basiclab.iot.sink.service.AlertService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

/**
 * 告警通知Kafka消费者（iot-sink服务）
 * 处理流程：1. 存储告警到数据库 2. 上传图片到MinIO 3. 如果开启了通知，发送到通知主题供iot-message消费
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
public class AlertNotificationConsumer {

    @Autowired
    private AlertService alertService;

    @Autowired(required = false)
    private org.springframework.kafka.core.KafkaTemplate<String, String> iotKafkaTemplate;

    @Value("${spring.kafka.alert-notification.send-topic:iot-alert-notification-send}")
    private String notificationSendTopic;

    /**
     * 消费告警通知消息
     * 无论是否开启通知，都会执行存储和上传操作
     *
     * @param messageJson 告警通知消息（JSON字符串）
     * @param topic Kafka主题
     * @param partition 分区
     * @param offset 偏移量
     * @param acknowledgment Kafka确认机制
     */
    @KafkaListener(
            topics = "${spring.kafka.alert-notification.topic:iot-alert-notification}",
            groupId = "${spring.kafka.alert-notification.group-id:iot-sink-alert-consumer}"
    )
    public void consumeAlertNotification(
            @Payload String messageJson,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {
        
        try {
            log.info("收到告警通知消息: topic={}, partition={}, offset={}", topic, partition, offset);
            
            if (messageJson == null || messageJson.isEmpty()) {
                log.error("告警通知消息为空");
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            // 解析JSON消息
            AlertNotificationMessage message;
            try {
                message = JsonUtils.parseObject(messageJson, AlertNotificationMessage.class);
            } catch (Exception e) {
                log.error("解析告警通知消息失败: error={}", e.getMessage(), e);
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            if (message == null || message.getAlert() == null) {
                log.error("告警通知消息解析后为空或缺少alert字段");
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            log.info("开始处理告警: deviceId={}, deviceName={}", 
                    message.getDeviceId(), message.getDeviceName());
            
            // 1. 处理告警：存储到数据库、上传图片到MinIO（无论是否开启通知，都要执行）
            final Integer[] alertIdRef = new Integer[1];
            try {
                Integer alertId = alertService.processAlert(message);
                alertIdRef[0] = alertId;
                // 如果存储成功，更新消息中的alertId
                if (alertId != null) {
                    message.setAlertId(alertId);
                    log.info("告警处理成功: alertId={}", alertId);
                } else {
                    log.warn("告警处理失败，未返回alertId");
                }
            } catch (Exception e) {
                log.error("处理告警失败（存储数据库/上传图片）: deviceId={}, error={}", 
                        message.getDeviceId(), e.getMessage(), e);
                // 即使告警处理失败，也继续处理通知（如果配置了通知）
            }
            
            // 2. 如果开启了通知，发送到通知主题供iot-message消费
            try {
                // 检查是否有通知配置
                List<Map<String, Object>> channels = message.getChannels();
                List<Map<String, Object>> notifyUsers = message.getNotifyUsers();
                
                boolean hasNotificationConfig = (channels != null && !channels.isEmpty()) 
                        && (notifyUsers != null && !notifyUsers.isEmpty());
                
                if (hasNotificationConfig) {
                    // 发送到通知主题供iot-message消费
                    if (iotKafkaTemplate != null) {
                        try {
                            // 将消息转换为JSON字符串
                            String notificationMessageJson = JsonUtils.toJsonString(message);
                            final Integer finalAlertId = alertIdRef[0];
                            
                            // 发送到通知主题
                            iotKafkaTemplate.send(notificationSendTopic, message.getDeviceId(), notificationMessageJson)
                                    .addCallback(
                                            result -> {
                                                if (result != null) {
                                                    log.info("告警通知消息已发送到通知主题: topic={}, partition={}, offset={}, alertId={}", 
                                                            result.getRecordMetadata().topic(),
                                                            result.getRecordMetadata().partition(),
                                                            result.getRecordMetadata().offset(),
                                                            finalAlertId);
                                                }
                                            },
                                            failure -> {
                                                log.error("发送告警通知消息到通知主题失败: alertId={}, error={}", 
                                                        finalAlertId, failure.getMessage(), failure);
                                            }
                                    );
                        } catch (Exception e) {
                            log.error("发送告警通知消息到通知主题异常: alertId={}, error={}", 
                                    alertIdRef[0], e.getMessage(), e);
                        }
                    } else {
                        log.warn("KafkaTemplate不可用，无法发送通知消息: alertId={}", alertIdRef[0]);
                    }
                } else {
                    log.debug("告警消息中没有通知配置，跳过发送通知: deviceId={}, alertId={}", 
                            message.getDeviceId(), alertIdRef[0]);
                }
            } catch (Exception e) {
                log.error("处理告警通知发送失败: alertId={}, deviceId={}, error={}", 
                        alertIdRef[0], message.getDeviceId(), e.getMessage(), e);
                // 通知发送失败不影响消息确认
            }
            
            // 确认消息已处理
            if (acknowledgment != null) {
                acknowledgment.acknowledge();
            }
            
        } catch (Exception e) {
            log.error("处理告警通知消息失败: error={}", e.getMessage(), e);
            // 注意：这里不确认消息，让Kafka重新投递，或者可以配置死信队列
            // 如果确认消息，错误消息会被丢弃
            // if (acknowledgment != null) {
            //     acknowledgment.acknowledge();
            // }
        }
    }
}

