package com.basiclab.iot.transform.runtime.service;

import com.basiclab.iot.transform.core.contract.TransformTopics;
import com.basiclab.iot.transform.core.domain.OutboxRecord;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Transactional Outbox 中继：短事务认领 → Kafka 投递 → 短事务落状态。
 * <p>
 * 多实例通过 {@code FOR UPDATE SKIP LOCKED} 并行认领，无中心锁。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class OutboxRelayScheduler {

    private final OutboxClaimService claimService;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    @Scheduled(fixedDelayString = "${transform.outbox.poll-interval-ms:1000}")
    public void relay() {
        List<OutboxRecord> batch = claimService.claimForRelay();
        for (OutboxRecord row : batch) {
            try {
                kafkaTemplate.send(
                        TransformTopics.DELIVER,
                        row.getEventId(),
                        objectMapper.writeValueAsString(row.getEnvelope())
                ).get(15, TimeUnit.SECONDS);
                claimService.markSent(row);
            } catch (Exception ex) {
                claimService.markFailed(row, ex);
            }
        }
    }
}
