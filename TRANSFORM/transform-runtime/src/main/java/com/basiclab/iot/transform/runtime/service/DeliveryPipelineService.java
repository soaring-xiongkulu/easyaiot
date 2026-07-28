package com.basiclab.iot.transform.runtime.service;

import com.basiclab.iot.transform.capability.backup.BackupCapability;
import com.basiclab.iot.transform.capability.map.MapCapability;
import com.basiclab.iot.transform.core.domain.Contract;
import com.basiclab.iot.transform.core.domain.DlqRecord;
import com.basiclab.iot.transform.core.domain.OutboxRecord;
import com.basiclab.iot.transform.core.domain.Party;
import com.basiclab.iot.transform.core.domain.PipelineDef;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.runtime.config.TransformRuntimeProperties;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 消费 → 映射 → Outbox → 内部投递 Topic → DLQ。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DeliveryPipelineService {

    private final TransformRepository repository;
    private final ObjectMapper objectMapper;
    private final BackupCapability backupCapability;
    private final MapCapability mapCapability;
    private final TransformRuntimeProperties properties;
    private final MetricsService metricsService;

    @Transactional
    public boolean accept(TransformEnvelope envelope) {
        try {
            TransformEnvelope mapped = applyPipelineMapping(envelope);
            if (!"deliver".equalsIgnoreCase(properties.getRole())
                    && !"edge".equalsIgnoreCase(properties.getRole())) {
                backupCapability.archive(mapped);
            }
            List<Contract> contracts = repository.enabledContracts(mapped.getFlowType().name());
            if (contracts.isEmpty()) {
                log.debug("[DeliveryPipelineService] no enabled contract for flowType={}",
                        mapped.getFlowType());
                metricsService.incAccepted();
                return true;
            }
            for (Contract contract : contracts) {
                TransformEnvelope perContract = mapped;
                if (contract.getMappingId() != null && !contract.getMappingId().isBlank()) {
                    perContract = mapCapability.map(contract.getMappingId(), cloneEnvelope(mapped));
                }
                publish(perContract, contract);
            }
            metricsService.incAccepted();
            return true;
        } catch (Exception ex) {
            log.error("[DeliveryPipelineService] accept failed eventId={}", envelope.getEventId(), ex);
            dlq("sink", null, envelope, ex);
            metricsService.incFailed();
            return false;
        }
    }

    @Transactional
    public void publish(TransformEnvelope envelope, Contract contract) throws Exception {
        OutboxRecord outbox = OutboxRecord.builder()
                .id(UUID.randomUUID().toString())
                .eventId(envelope.getEventId())
                .partyId(contract.getPartyId())
                .contractId(contract.getId())
                .channel(contract.getChannel())
                .status("PENDING")
                .attempts(0)
                .envelope(cloneEnvelope(envelope))
                .createdAt(Instant.now())
                .updatedAt(Instant.now())
                .build();
        TransformEnvelope copy = outbox.getEnvelope();
        applyContractHeaders(copy, contract, outbox.getId());
        outbox.setEnvelope(copy);
        // Database unique index (event_id, contract_id) makes duplicate Kafka consumption idempotent.
        repository.insertOutbox(outbox);
    }

    /**
     * 再推：用当前合同刷新 envelope，重置为 PENDING，由 Outbox 中继重新投递。
     * 避免再插一条 outbox 触发 (event_id, contract_id) 唯一约束。
     */
    @Transactional
    public void replayOutbox(String outboxId) {
        OutboxRecord outbox = repository.outbox(outboxId);
        if (outbox == null) {
            throw new NoSuchElementException("outbox not found: " + outboxId);
        }
        Contract contract = repository.contract(outbox.getContractId());
        if (contract == null) {
            throw new IllegalStateException("contract missing: " + outbox.getContractId());
        }
        TransformEnvelope envelope = outbox.getEnvelope();
        if (envelope == null) {
            throw new IllegalStateException("outbox envelope missing: " + outboxId);
        }
        applyContractHeaders(envelope, contract, outbox.getId());
        outbox.setEnvelope(envelope);
        outbox.setStatus("PENDING");
        outbox.setError(null);
        outbox.setUpdatedAt(Instant.now());
        repository.saveOutbox(outbox, Instant.now(), null);
    }

    public void dlq(String source, String outboxId, TransformEnvelope envelope, Exception error) {
        DlqRecord record = DlqRecord.builder()
                .id(UUID.randomUUID().toString())
                .source(source)
                .outboxId(outboxId)
                .reason(error == null ? "unknown" : error.toString())
                .envelope(envelope)
                .createdAt(Instant.now())
                .build();
        repository.saveDlq(record);
        metricsService.incDlq();
    }

    public void replay(String dlqId) throws Exception {
        DlqRecord record = repository.dlq(dlqId);
        if (record == null) {
            throw new NoSuchElementException("dlq not found: " + dlqId);
        }
        if (record.getOutboxId() != null && repository.outbox(record.getOutboxId()) != null) {
            replayOutbox(record.getOutboxId());
            repository.deleteDlq(dlqId);
            return;
        }
        Contract contract = repository.listContracts().stream()
                .filter(Contract::isEnabled)
                .findFirst()
                .orElseThrow(() -> new IllegalStateException("no enabled contract for replay"));
        TransformEnvelope envelope = record.getEnvelope();
        if (envelope != null && (envelope.getEventId() == null || envelope.getEventId().isBlank())) {
            envelope.setEventId(UUID.randomUUID().toString().replace("-", ""));
        }
        publish(envelope, contract);
        repository.deleteDlq(dlqId);
    }

    private void applyContractHeaders(TransformEnvelope copy, Contract contract, String outboxId) {
        copy.getHeaders().put("channel", contract.getChannel());
        copy.getHeaders().put("partyId", contract.getPartyId());
        copy.getHeaders().put("contractId", contract.getId());
        copy.getHeaders().put("outboxId", outboxId);
        copy.getHeaders().put("endpoint", contract.getEndpoint());
        copy.getHeaders().put("contract", objectMapper.convertValue(contract, Map.class));
        if (contract.getHeaders() != null && contract.getHeaders().get("partySecret") != null) {
            copy.getHeaders().put("partySecret", contract.getHeaders().get("partySecret"));
        } else {
            copy.getHeaders().remove("partySecret");
        }
        Party party = repository.party(contract.getPartyId());
        if (party != null) {
            copy.getHeaders().put("partyType", party.getType());
        }
    }

    private TransformEnvelope applyPipelineMapping(TransformEnvelope envelope) {
        PipelineDef pipeline = repository.enabledPipeline();
        if (pipeline == null || pipeline.getMappingId() == null || pipeline.getMappingId().isBlank()) {
            return envelope;
        }
        return mapCapability.map(pipeline.getMappingId(), envelope);
    }

    private TransformEnvelope cloneEnvelope(TransformEnvelope source) throws Exception {
        return objectMapper.readValue(objectMapper.writeValueAsString(source), TransformEnvelope.class);
    }
}
