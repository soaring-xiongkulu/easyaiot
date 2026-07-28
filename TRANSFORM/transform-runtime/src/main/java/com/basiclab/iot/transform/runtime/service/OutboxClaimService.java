package com.basiclab.iot.transform.runtime.service;

import com.basiclab.iot.transform.core.domain.DlqRecord;
import com.basiclab.iot.transform.core.domain.OutboxRecord;
import com.basiclab.iot.transform.runtime.config.TransformRuntimeProperties;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * Outbox 短事务认领：认领与 Kafka 发送解耦，避免长事务持锁。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class OutboxClaimService {

    private final TransformRepository repository;
    private final TransformRuntimeProperties properties;
    private final MetricsService metrics;

    @Transactional
    public List<OutboxRecord> claimForRelay() {
        List<OutboxRecord> claimed = repository.claimOutbox(properties.getOutbox().getBatchSize());
        List<OutboxRecord> result = new ArrayList<>(claimed.size());
        for (OutboxRecord row : claimed) {
            row.setStatus("RELAYING");
            repository.saveOutbox(row, null, null);
            result.add(row);
        }
        return result;
    }

    @Transactional
    public void markSent(OutboxRecord row) {
        row.setStatus("SENT");
        repository.saveOutbox(row, null, Instant.now());
        metrics.incPublished();
    }

    @Transactional
    public void markFailed(OutboxRecord row, Exception ex) {
        int attempts = row.getAttempts() + 1;
        row.setAttempts(attempts);
        row.setError(ex == null ? "unknown" : ex.toString());
        if (attempts >= properties.getOutbox().getMaxAttempts()) {
            row.setStatus("DEAD");
            repository.saveOutbox(row, null, null);
            repository.saveDlq(DlqRecord.builder()
                    .id(UUID.randomUUID().toString())
                    .source("outbox")
                    .outboxId(row.getId())
                    .reason(row.getError())
                    .envelope(row.getEnvelope())
                    .createdAt(Instant.now())
                    .build());
            metrics.incDlq();
            return;
        }
        row.setStatus("FAILED");
        long delaySeconds = Math.min(3600L, 1L << Math.min(20, attempts));
        repository.saveOutbox(row, Instant.now().plusSeconds(delaySeconds), null);
        log.warn("[OutboxClaimService] relay failed id={}, attempts={}", row.getId(), attempts);
    }
}
