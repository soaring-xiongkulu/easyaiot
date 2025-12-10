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

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 抓拍算法任务告警Kafka消费者（iot-sink服务）
 * 处理流程：1. 存储告警到数据库（类型为抓拍算法任务） 2. 上传图片到MinIO抓拍空间 3. 如果开启了通知，发送到抓拍算法任务通知主题供iot-message消费
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
public class SnapshotAlertConsumer {

    @Autowired
    private AlertService alertService;

    @Autowired(required = false)
    private org.springframework.kafka.core.KafkaTemplate<String, String> iotKafkaTemplate;

    @Value("${spring.kafka.snapshot-alert.send-topic:iot-snapshot-alert-notification-send}")
    private String snapshotNotificationSendTopic;
    
    /**
     * 已处理的告警缓存，用于去重
     * Key: deviceId + "_" + time (格式: deviceId_YYYY-MM-DD HH:MM:SS)
     * Value: 处理时间戳（用于定期清理）
     */
    private final ConcurrentHashMap<String, Long> processedAlerts = new ConcurrentHashMap<>();
    
    /**
     * 定时清理任务执行器
     */
    private ScheduledExecutorService cleanupScheduler;
    
    /**
     * 告警记录保留时间（毫秒），默认1毫秒
     */
    @Value("${snapshot.alert.dedup.retention-ms:1}")
    private long retentionMs = 1;
    
    /**
     * 初始化定时清理任务
     */
    @PostConstruct
    public void init() {
        // 根据保留时间调整清理频率：如果保留时间很短（<1秒），则更频繁清理
        long cleanupInterval;
        if (retentionMs < 1000) {
            // 保留时间小于1秒，每100毫秒清理一次
            cleanupInterval = 100;
        } else if (retentionMs < 60000) {
            // 保留时间小于1分钟，每10秒清理一次
            cleanupInterval = 10000;
        } else {
            // 保留时间较长，每30分钟清理一次
            cleanupInterval = 30 * 60 * 1000;
        }
        
        cleanupScheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "snapshot-alert-cleanup");
            t.setDaemon(true);
            return t;
        });
        cleanupScheduler.scheduleWithFixedDelay(this::cleanupExpiredAlerts, cleanupInterval, cleanupInterval, TimeUnit.MILLISECONDS);
        log.info("抓拍算法任务告警去重机制已启动: retentionMs={}ms, cleanupInterval={}ms", retentionMs, cleanupInterval);
    }
    
    /**
     * 清理过期记录
     */
    private void cleanupExpiredAlerts() {
        try {
            long currentTime = System.currentTimeMillis();
            long expireTime = currentTime - retentionMs;
            
            int removedCount = 0;
            for (Map.Entry<String, Long> entry : processedAlerts.entrySet()) {
                if (entry.getValue() < expireTime) {
                    processedAlerts.remove(entry.getKey());
                    removedCount++;
                }
            }
            
            if (removedCount > 0) {
                log.debug("清理过期告警记录: 清理数量={}, 剩余数量={}", removedCount, processedAlerts.size());
            }
        } catch (Exception e) {
            log.error("清理过期告警记录失败", e);
        }
    }
    
    /**
     * 销毁时关闭定时任务
     */
    @PreDestroy
    public void destroy() {
        if (cleanupScheduler != null) {
            cleanupScheduler.shutdown();
            try {
                if (!cleanupScheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                    cleanupScheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                cleanupScheduler.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }
    
    /**
     * 检查告警是否已处理过（同一设备、同一时间）
     * 使用原子操作，确保并发安全
     * 
     * @param deviceId 设备ID
     * @param alertTime 告警时间（格式: YYYY-MM-DD HH:MM:SS）
     * @return true表示已处理过，false表示未处理过（且已标记为处理中）
     */
    private boolean isAlreadyProcessed(String deviceId, String alertTime) {
        if (deviceId == null || alertTime == null) {
            return false;
        }
        
        // 构建唯一key: deviceId_YYYY-MM-DD HH:MM:SS
        String key = deviceId + "_" + alertTime;
        
        // 使用putIfAbsent原子操作：如果key不存在，则添加并返回null；如果已存在，则返回旧值
        Long existingTime = processedAlerts.putIfAbsent(key, System.currentTimeMillis());
        
        if (existingTime != null) {
            // 已存在，说明有其他线程正在处理或已处理过
            log.debug("抓拍算法任务告警已处理过或正在处理，跳过: deviceId={}, alertTime={}", deviceId, alertTime);
            return true;
        }
        
        // 新添加的，返回false表示未处理过（但已标记为处理中）
        return false;
    }
    
    /**
     * 标记告警处理成功（用于在处理成功后确认）
     * 注意：由于isAlreadyProcessed已经标记，这里主要用于日志记录
     * 
     * @param deviceId 设备ID
     * @param alertTime 告警时间
     */
    private void markAsProcessed(String deviceId, String alertTime) {
        if (deviceId == null || alertTime == null) {
            return;
        }
        String key = deviceId + "_" + alertTime;
        // 更新处理时间
        processedAlerts.put(key, System.currentTimeMillis());
    }

    /**
     * 消费抓拍算法任务告警消息
     * 无论是否开启通知，都会执行存储和上传操作
     *
     * @param messageJson 告警通知消息（JSON字符串）
     * @param topic Kafka主题
     * @param partition 分区
     * @param offset 偏移量
     * @param acknowledgment Kafka确认机制
     */
    @KafkaListener(
            topics = "${spring.kafka.snapshot-alert.topic:iot-snapshot-alert}",
            groupId = "${spring.kafka.snapshot-alert.group-id:iot-sink-snapshot-alert-consumer}"
    )
    public void consumeSnapshotAlert(
            @Payload String messageJson,
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header(KafkaHeaders.RECEIVED_PARTITION_ID) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {
        
        try {
            log.info("收到抓拍算法任务告警消息: topic={}, partition={}, offset={}", topic, partition, offset);
            
            if (messageJson == null || messageJson.isEmpty()) {
                log.error("抓拍算法任务告警消息为空");
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
                log.error("解析抓拍算法任务告警消息失败: error={}", e.getMessage(), e);
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            if (message == null || message.getAlert() == null) {
                log.error("抓拍算法任务告警消息解析后为空或缺少alert字段");
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }

            log.info("开始处理抓拍算法任务告警: deviceId={}, deviceName={}, taskId={}, taskName={}", 
                    message.getDeviceId(), message.getDeviceName(), message.getTaskId(), message.getTaskName());
            
            // 检查告警时间
            String alertTime = null;
            if (message.getAlert() != null) {
                alertTime = message.getAlert().getTime();
            }
            
            // 去重检查：同一设备、同一时间只处理第一条
            if (isAlreadyProcessed(message.getDeviceId(), alertTime)) {
                log.info("⏭️  抓拍算法任务告警已处理过（同一时间），跳过: deviceId={}, alertTime={}, taskId={}", 
                        message.getDeviceId(), alertTime, message.getTaskId());
                // 确认消息已处理（即使跳过，也要确认，避免重复投递）
                if (acknowledgment != null) {
                    acknowledgment.acknowledge();
                }
                return;
            }
            
            // 记录通知配置信息
            List<Map<String, Object>> channels = message.getChannels();
            List<Map<String, Object>> notifyUsers = message.getNotifyUsers();
            List<String> notifyMethods = message.getNotifyMethods();
            Boolean shouldNotify = message.getShouldNotify();
            
            log.info("📊 抓拍算法任务告警通知配置信息: deviceId={}, taskId={}, alertTime={}, shouldNotify={}, " +
                    "channels数量={}, notifyUsers数量={}, notifyMethods={}", 
                    message.getDeviceId(), message.getTaskId(), alertTime, shouldNotify,
                    (channels != null ? channels.size() : 0),
                    (notifyUsers != null ? notifyUsers.size() : 0),
                    notifyMethods);
            
            // 1. 处理告警：存储到数据库（类型为抓拍算法任务）、上传图片到MinIO抓拍空间（无论是否开启通知，都要执行）
            final Integer[] alertIdRef = new Integer[1];
            try {
                // 标记为抓拍算法任务，AlertService会根据此标记上传到抓拍空间
                Integer alertId = alertService.processSnapshotAlert(message);
                alertIdRef[0] = alertId;
                // 如果存储成功，更新消息中的alertId
                if (alertId != null) {
                    message.setAlertId(alertId);
                    // 确认标记为已处理（虽然已经在isAlreadyProcessed中标记，但这里确认一下）
                    markAsProcessed(message.getDeviceId(), alertTime);
                    log.info("✅ 抓拍算法任务告警处理成功: alertId={}, deviceId={}, alertTime={}", 
                            alertId, message.getDeviceId(), alertTime);
                } else {
                    log.warn("⚠️  抓拍算法任务告警处理失败，未返回alertId: deviceId={}, alertTime={}", 
                            message.getDeviceId(), alertTime);
                    // 处理失败，但不移除标记（失败不重试，同一时间只处理第一条）
                    // 标记已处理，避免重试
                    markAsProcessed(message.getDeviceId(), alertTime);
                }
            } catch (Exception e) {
                log.error("❌ 处理抓拍算法任务告警失败（存储数据库/上传图片）: deviceId={}, alertTime={}, error={}", 
                        message.getDeviceId(), alertTime, e.getMessage(), e);
                // 处理失败，但不移除标记（失败不重试，同一时间只处理第一条）
                // 标记已处理，避免重试
                markAsProcessed(message.getDeviceId(), alertTime);
                // 即使告警处理失败，也继续处理通知（如果配置了通知）
            }
            
            // 2. 如果开启了通知，发送到抓拍算法任务通知主题供iot-message消费
            try {
                // 检查是否有通知配置
                boolean hasNotificationConfig = (channels != null && !channels.isEmpty()) 
                        && (notifyUsers != null && !notifyUsers.isEmpty());
                
                // 优先使用shouldNotify字段，如果没有则根据配置判断
                if (shouldNotify == null) {
                    shouldNotify = hasNotificationConfig;
                }
                
                log.info("📋 抓拍算法任务告警通知判断: deviceId={}, alertId={}, shouldNotify={}, " +
                        "hasNotificationConfig={}", 
                        message.getDeviceId(), alertIdRef[0], shouldNotify, hasNotificationConfig);
                
                if (shouldNotify && hasNotificationConfig) {
                    // 发送到抓拍算法任务通知主题供iot-message消费
                    if (iotKafkaTemplate != null) {
                        try {
                            // 将消息转换为JSON字符串
                            String notificationMessageJson = JsonUtils.toJsonString(message);
                            final Integer finalAlertId = alertIdRef[0];
                            
                            log.info("📤 准备发送抓拍算法任务告警通知消息到通知主题: alertId={}, deviceId={}, topic={}, " +
                                    "notifyUsers数量={}, notifyMethods={}, channels数量={}", 
                                    finalAlertId, message.getDeviceId(), snapshotNotificationSendTopic,
                                    (notifyUsers != null ? notifyUsers.size() : 0),
                                    notifyMethods,
                                    (channels != null ? channels.size() : 0));
                            
                            // 发送到抓拍算法任务通知主题
                            iotKafkaTemplate.send(snapshotNotificationSendTopic, message.getDeviceId(), notificationMessageJson)
                                    .addCallback(
                                            result -> {
                                                if (result != null) {
                                                    log.info("✅ 抓拍算法任务告警通知消息已发送到通知主题: alertId={}, topic={}, partition={}, offset={}, " +
                                                            "notifyUsers数量={}, notifyMethods={}", 
                                                            finalAlertId,
                                                            result.getRecordMetadata().topic(),
                                                            result.getRecordMetadata().partition(),
                                                            result.getRecordMetadata().offset(),
                                                            (notifyUsers != null ? notifyUsers.size() : 0),
                                                            notifyMethods);
                                                }
                                            },
                                            failure -> {
                                                log.error("❌ 发送抓拍算法任务告警通知消息到通知主题失败: alertId={}, deviceId={}, error={}", 
                                                        finalAlertId, message.getDeviceId(), failure.getMessage(), failure);
                                            }
                                    );
                        } catch (Exception e) {
                            log.error("❌ 发送抓拍算法任务告警通知消息到通知主题异常: alertId={}, deviceId={}, error={}", 
                                    alertIdRef[0], message.getDeviceId(), e.getMessage(), e);
                        }
                    } else {
                        log.warn("⚠️  KafkaTemplate不可用，无法发送抓拍算法任务通知消息: alertId={}, deviceId={}", 
                                alertIdRef[0], message.getDeviceId());
                    }
                } else {
                    log.info("ℹ️  抓拍算法任务告警消息中没有通知配置或shouldNotify=false，跳过发送通知: " +
                            "deviceId={}, alertId={}, shouldNotify={}, channels数量={}, notifyUsers数量={}", 
                            message.getDeviceId(), alertIdRef[0], shouldNotify,
                            (channels != null ? channels.size() : 0),
                            (notifyUsers != null ? notifyUsers.size() : 0));
                }
            } catch (Exception e) {
                log.error("处理抓拍算法任务告警通知发送失败: alertId={}, deviceId={}, error={}", 
                        alertIdRef[0], message.getDeviceId(), e.getMessage(), e);
                // 通知发送失败不影响消息确认
            }
            
            // 确认消息已处理
            if (acknowledgment != null) {
                acknowledgment.acknowledge();
            }
            
        } catch (Exception e) {
            log.error("处理抓拍算法任务告警消息失败: error={}", e.getMessage(), e);
            // 注意：这里不确认消息，让Kafka重新投递，或者可以配置死信队列
            // 如果确认消息，错误消息会被丢弃
            // if (acknowledgment != null) {
            //     acknowledgment.acknowledge();
            // }
        }
    }
}
