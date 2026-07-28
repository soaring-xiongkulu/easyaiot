package com.basiclab.iot.transform.runtime.dal;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.basiclab.iot.transform.core.domain.*;
import com.basiclab.iot.transform.core.envelope.TransformEnvelope;
import com.basiclab.iot.transform.runtime.dal.dataobject.*;
import com.basiclab.iot.transform.runtime.dal.mapper.*;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 领域仓储：对外仍暴露 Party/Contract/Outbox 等领域对象，
 * 持久化层使用 transform_* 专业表名与字段。
 */
@Repository
@RequiredArgsConstructor
public class TransformRepository {

    private final TargetSystemMapper targetSystems;
    private final PushRuleMapper pushRules;
    private final FieldMappingMapper fieldMappings;
    private final FlowPipelineMapper flowPipelines;
    private final PushRecordMapper pushRecords;
    private final PushFailureMapper pushFailures;
    private final RuntimeInstanceMapper runtimeInstances;
    private final ObjectMapper objectMapper;

    public long partyCount() {
        return targetSystems.selectCount(null);
    }

    public long contractCount() {
        return pushRules.selectCount(null);
    }

    public long mappingCount() {
        return fieldMappings.selectCount(null);
    }

    public long pipelineCount() {
        return flowPipelines.selectCount(null);
    }

    public long outboxCount() {
        return pushRecords.selectCount(null);
    }

    public long dlqCount() {
        return pushFailures.selectCount(null);
    }

    public List<Party> listParties() {
        return targetSystems.selectList(null).stream().map(this::party).toList();
    }

    public Party party(String id) {
        return Optional.ofNullable(targetSystems.selectById(id)).map(this::party).orElse(null);
    }

    public Party save(Party value) {
        TargetSystemDO d = new TargetSystemDO();
        d.setId(id(value.getId()));
        d.setSystemName(value.getName());
        d.setConnectorType(value.getType());
        d.setEnabled(value.isEnabled());
        d.setConfigJson(json(value.getConfig()));
        upsert(targetSystems, d);
        return party(d);
    }

    public void deleteParty(String id) {
        targetSystems.deleteById(id);
    }

    public List<Contract> listContracts() {
        return pushRules.selectList(null).stream().map(this::contract).toList();
    }

    public List<Contract> enabledContracts(String flow) {
        return pushRules.selectList(new LambdaQueryWrapper<PushRuleDO>().eq(PushRuleDO::getEnabled, true))
                .stream()
                .map(this::contract)
                .filter(c -> c.getFlowType() == null || c.getFlowType().isBlank() || c.getFlowType().equalsIgnoreCase(flow))
                .toList();
    }

    public Contract contract(String id) {
        return Optional.ofNullable(pushRules.selectById(id)).map(this::contract).orElse(null);
    }

    public Contract save(Contract value) {
        PushRuleDO d = new PushRuleDO();
        d.setId(id(value.getId()));
        d.setTargetSystemId(value.getPartyId());
        d.setFlowType(value.getFlowType());
        d.setDeliverChannel(value.getChannel());
        d.setEndpointUrl(value.getEndpoint());
        d.setFieldMappingId(value.getMappingId());
        d.setEnabled(value.isEnabled());
        d.setRequestHeadersJson(json(value.getHeaders()));
        upsert(pushRules, d);
        return contract(d);
    }

    public void deleteContract(String id) {
        pushRules.deleteById(id);
    }

    public List<MappingRule> listMappings() {
        return fieldMappings.selectList(null).stream().map(this::mapping).toList();
    }

    public MappingRule mapping(String id) {
        return Optional.ofNullable(fieldMappings.selectById(id)).map(this::mapping).orElse(null);
    }

    public MappingRule save(MappingRule value) {
        FieldMappingDO d = new FieldMappingDO();
        d.setId(id(value.getId()));
        d.setMappingName(value.getName());
        d.setEnabled(value.isEnabled());
        d.setFieldBindingsJson(json(value.getFields()));
        upsert(fieldMappings, d);
        return mapping(d);
    }

    public void deleteMapping(String id) {
        fieldMappings.deleteById(id);
    }

    public List<PipelineDef> listPipelines() {
        return flowPipelines.selectList(null).stream().map(this::pipeline).toList();
    }

    public PipelineDef enabledPipeline() {
        return pipeline(flowPipelines.selectOne(
                new LambdaQueryWrapper<FlowPipelineDO>().eq(FlowPipelineDO::getEnabled, true).last("LIMIT 1")));
    }

    public PipelineDef save(PipelineDef value) {
        FlowPipelineDO d = new FlowPipelineDO();
        d.setId(id(value.getId()));
        d.setPipelineName(value.getName());
        d.setFlowType(value.getFlowType());
        d.setFieldMappingId(value.getMappingId());
        d.setEnabled(value.isEnabled());
        upsert(flowPipelines, d);
        return pipeline(d);
    }

    public void deletePipeline(String id) {
        flowPipelines.deleteById(id);
    }

    public List<OutboxRecord> listOutbox() {
        return pushRecords.selectList(null).stream().map(this::outbox).toList();
    }

    public OutboxRecord outbox(String id) {
        return Optional.ofNullable(pushRecords.selectById(id)).map(this::outbox).orElse(null);
    }

    public boolean insertOutbox(OutboxRecord value) {
        PushRecordDO d = outboxDO(value);
        try {
            return pushRecords.insert(d) == 1;
        } catch (DuplicateKeyException ignored) {
            return false;
        } catch (org.springframework.dao.DataIntegrityViolationException ignored) {
            return false;
        }
    }

    public List<OutboxRecord> claimOutbox(int limit) {
        return pushRecords.claimBatch(limit).stream().map(this::outbox).toList();
    }

    public void saveOutbox(OutboxRecord value, Instant nextRetry, Instant publishedAt) {
        PushRecordDO d = outboxDO(value);
        d.setNextRetryTime(nextRetry);
        d.setRelayedAt(publishedAt);
        pushRecords.updateById(d);
    }

    public List<DlqRecord> listDlq() {
        return pushFailures.selectList(null).stream().map(this::dlq).toList();
    }

    public DlqRecord dlq(String id) {
        return Optional.ofNullable(pushFailures.selectById(id)).map(this::dlq).orElse(null);
    }

    public void saveDlq(DlqRecord value) {
        PushFailureDO d = new PushFailureDO();
        d.setId(id(value.getId()));
        d.setFailureSource(value.getSource());
        d.setPushRecordId(value.getOutboxId());
        d.setFailureReason(value.getReason());
        d.setEnvelopeJson(json(value.getEnvelope()));
        pushFailures.insert(d);
    }

    public void deleteDlq(String id) {
        pushFailures.deleteById(id);
    }

    public List<RuntimeInstance> listRuntimeInstances() {
        return runtimeInstances.selectList(null).stream().map(this::runtimeInstance).toList();
    }

    public void upsertRuntimeInstance(RuntimeInstance value) {
        RuntimeInstanceDO d = new RuntimeInstanceDO();
        d.setInstanceId(value.getInstanceId());
        d.setNodeId(value.getNodeId());
        d.setHost(value.getHost());
        d.setRole(value.getRole());
        d.setStatus(value.getStatus());
        d.setJoinedGroups(value.getJoinedGroups());
        d.setCpuLoad(value.getCpuLoad());
        d.setHeapUsedMb(value.getHeapUsedMb());
        d.setHeapMaxMb(value.getHeapMaxMb());
        d.setMaxConsumerLag(value.getMaxConsumerLag());
        d.setDeliverSuccessRate(value.getDeliverSuccessRate());
        d.setMetricsJson(json(value.getMetrics() == null ? Map.of() : value.getMetrics()));
        d.setAdaptDecision(value.getAdaptDecision());
        d.setLastHeartbeatTime(value.getLastHeartbeatTime() == null ? Instant.now() : value.getLastHeartbeatTime());
        if (runtimeInstances.updateById(d) == 0) {
            try {
                runtimeInstances.insert(d);
            } catch (DuplicateKeyException ex) {
                // 并发首次心跳场景：另一个线程已插入同一 instance_id，回退为更新即可。
                runtimeInstances.updateById(d);
            }
        }
    }

    private RuntimeInstance runtimeInstance(RuntimeInstanceDO d) {
        if (d == null) {
            return null;
        }
        Instant hb = d.getLastHeartbeatTime();
        boolean online = hb != null && hb.isAfter(Instant.now().minusSeconds(45));
        String status = online ? (d.getStatus() == null ? "ONLINE" : d.getStatus()) : "OFFLINE";
        Map<String, Long> metrics = new HashMap<>();
        map(d.getMetricsJson()).forEach((k, v) -> {
            if (v instanceof Number n) {
                metrics.put(k, n.longValue());
            }
        });
        return RuntimeInstance.builder()
                .instanceId(d.getInstanceId())
                .nodeId(d.getNodeId())
                .host(d.getHost())
                .role(d.getRole())
                .status(status)
                .joinedGroups(d.getJoinedGroups())
                .cpuLoad(d.getCpuLoad())
                .heapUsedMb(d.getHeapUsedMb())
                .heapMaxMb(d.getHeapMaxMb())
                .maxConsumerLag(d.getMaxConsumerLag())
                .deliverSuccessRate(d.getDeliverSuccessRate())
                .metrics(metrics)
                .adaptDecision(d.getAdaptDecision())
                .lastHeartbeatTime(hb)
                .online(online)
                .build();
    }

    private String id(String id) {
        return id == null || id.isBlank() ? UUID.randomUUID().toString() : id;
    }

    private <T> void upsert(com.baomidou.mybatisplus.core.mapper.BaseMapper<T> mapper, T value) {
        if (mapper.updateById(value) == 0) {
            mapper.insert(value);
        }
    }

    private Party party(TargetSystemDO d) {
        return d == null ? null : Party.builder()
                .id(d.getId())
                .name(d.getSystemName())
                .type(d.getConnectorType())
                .enabled(Boolean.TRUE.equals(d.getEnabled()))
                .config(map(d.getConfigJson()))
                .createdAt(d.getCreateTime())
                .build();
    }

    private Contract contract(PushRuleDO d) {
        return d == null ? null : Contract.builder()
                .id(d.getId())
                .partyId(d.getTargetSystemId())
                .flowType(d.getFlowType())
                .channel(d.getDeliverChannel())
                .endpoint(d.getEndpointUrl())
                .mappingId(d.getFieldMappingId())
                .enabled(Boolean.TRUE.equals(d.getEnabled()))
                .headers(map(d.getRequestHeadersJson()))
                .createdAt(d.getCreateTime())
                .build();
    }

    private MappingRule mapping(FieldMappingDO d) {
        return d == null ? null : MappingRule.builder()
                .id(d.getId())
                .name(d.getMappingName())
                .enabled(Boolean.TRUE.equals(d.getEnabled()))
                .fields(stringMap(d.getFieldBindingsJson()))
                .createdAt(d.getCreateTime())
                .build();
    }

    private PipelineDef pipeline(FlowPipelineDO d) {
        return d == null ? null : PipelineDef.builder()
                .id(d.getId())
                .name(d.getPipelineName())
                .flowType(d.getFlowType())
                .mappingId(d.getFieldMappingId())
                .enabled(Boolean.TRUE.equals(d.getEnabled()))
                .createdAt(d.getCreateTime())
                .build();
    }

    private PushRecordDO outboxDO(OutboxRecord v) {
        PushRecordDO d = new PushRecordDO();
        d.setId(id(v.getId()));
        d.setEventId(v.getEventId());
        d.setTargetSystemId(v.getPartyId());
        d.setPushRuleId(v.getContractId());
        d.setDeliverChannel(v.getChannel());
        d.setPushStatus(v.getStatus());
        d.setAttemptCount(v.getAttempts());
        d.setLastError(v.getError());
        d.setEnvelopeJson(json(v.getEnvelope()));
        return d;
    }

    private OutboxRecord outbox(PushRecordDO d) {
        return d == null ? null : OutboxRecord.builder()
                .id(d.getId())
                .eventId(d.getEventId())
                .partyId(d.getTargetSystemId())
                .contractId(d.getPushRuleId())
                .channel(d.getDeliverChannel())
                .status(d.getPushStatus())
                .attempts(Optional.ofNullable(d.getAttemptCount()).orElse(0))
                .error(d.getLastError())
                .envelope(read(d.getEnvelopeJson(), TransformEnvelope.class))
                .createdAt(d.getCreateTime())
                .updatedAt(d.getUpdateTime())
                .build();
    }

    private DlqRecord dlq(PushFailureDO d) {
        return d == null ? null : DlqRecord.builder()
                .id(d.getId())
                .source(d.getFailureSource())
                .outboxId(d.getPushRecordId())
                .reason(d.getFailureReason())
                .envelope(read(d.getEnvelopeJson(), TransformEnvelope.class))
                .createdAt(d.getCreateTime())
                .build();
    }

    private String json(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception e) {
            throw new IllegalArgumentException("serialize persistence data", e);
        }
    }

    private <T> T read(String value, Class<T> type) {
        try {
            return value == null ? null : objectMapper.readValue(value, type);
        } catch (Exception e) {
            throw new IllegalArgumentException("deserialize persistence data", e);
        }
    }

    private Map<String, Object> map(String value) {
        try {
            return value == null ? new HashMap<>() : objectMapper.readValue(value, new TypeReference<>() {});
        } catch (Exception e) {
            throw new IllegalArgumentException("deserialize map", e);
        }
    }

    private Map<String, String> stringMap(String value) {
        return map(value).entrySet().stream()
                .collect(Collectors.toMap(Map.Entry::getKey, e -> String.valueOf(e.getValue()), (a, b) -> b, LinkedHashMap::new));
    }
}
