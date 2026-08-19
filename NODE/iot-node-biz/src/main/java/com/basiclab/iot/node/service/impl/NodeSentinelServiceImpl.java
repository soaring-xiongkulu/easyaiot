package com.basiclab.iot.node.service.impl;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import com.basiclab.iot.node.dal.dataobject.NodeSentinelRemediateLogDO;
import com.basiclab.iot.node.dal.dataobject.NodeSentinelSnapshotDO;
import com.basiclab.iot.node.dal.pgsql.ComputeNodeMapper;
import com.basiclab.iot.node.dal.pgsql.NodeMetricSnapshotMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSentinelRemediateLogMapper;
import com.basiclab.iot.node.dal.pgsql.NodeSentinelSnapshotMapper;
import com.basiclab.iot.node.domain.vo.NodeSentinelProbeReqVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateLogRespVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateReportReqVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRemediateReqVO;
import com.basiclab.iot.node.domain.vo.NodeSentinelRespVO;
import com.basiclab.iot.node.enums.NodeStatusEnum;
import com.basiclab.iot.node.framework.SentinelCapabilityRegistry;
import com.basiclab.iot.node.service.NodeSentinelRemediatorService;
import com.basiclab.iot.node.service.NodeSentinelService;
import com.basiclab.iot.node.util.NodeFunctions;
import com.basiclab.iot.node.util.NodeSentinelAgentClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_COMMAND_FAILED;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_NOT_EXISTS;
import static com.basiclab.iot.node.enums.ErrorCodeConstants.COMPUTE_NODE_OFFLINE;

@Service
@Slf4j
public class NodeSentinelServiceImpl implements NodeSentinelService {

    private static final String REDIS_KEY_PREFIX = "node:sentinel:snapshot:";
    private static final long FRESH_SECONDS = 90;

    @Resource
    private NodeSentinelSnapshotMapper nodeSentinelSnapshotMapper;
    @Resource
    private NodeSentinelRemediateLogMapper nodeSentinelRemediateLogMapper;
    @Resource
    private ComputeNodeMapper computeNodeMapper;
    @Resource
    private NodeMetricSnapshotMapper nodeMetricSnapshotMapper;
    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private ObjectMapper objectMapper;
    @Resource
    private SentinelCapabilityRegistry sentinelCapabilityRegistry;
    @Resource
    private NodeSentinelAgentClient nodeSentinelAgentClient;
    @Resource
    private NodeSentinelRemediatorService nodeSentinelRemediatorService;

    @Value("${easyaiot.sentinel.enabled:true}")
    private boolean sentinelEnabled;

    @Value("${easyaiot.sentinel.resource-degrade-cpu-percent:85}")
    private double resourceDegradeCpuPercent;

    @Value("${easyaiot.sentinel.resource-degrade-mem-percent:95}")
    private double resourceDegradeMemPercent;

    @Override
    public void ingestHeartbeat(Long nodeId, Map<String, Object> sentinelPayload) {
        if (!sentinelEnabled || sentinelPayload == null || sentinelPayload.isEmpty()) {
            return;
        }
        try {
            ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
            Map<String, Boolean> declared = node != null && node.getCapabilities() != null
                    ? node.getCapabilities() : Collections.emptyMap();

            Map<String, Object> schedulable = applyAggregatorOverlay(
                    nodeId, asMap(sentinelPayload.get("schedulableCapabilities")), declared);

            NodeSentinelSnapshotDO existing = nodeSentinelSnapshotMapper.selectById(nodeId);
            NodeSentinelSnapshotDO snapshot = existing != null ? existing : new NodeSentinelSnapshotDO();
            snapshot.setNodeId(nodeId);
            snapshot.setNodeProfile(resolveFunctionsCsv(sentinelPayload, node));
            snapshot.setSentinelVersion(asString(sentinelPayload.get("sentinelVersion"), null));
            snapshot.setProbeLevel(asString(sentinelPayload.get("probeLevel"), "L0"));
            snapshot.setComponents(asList(sentinelPayload.get("components")));
            snapshot.setSchedulableCapabilities(schedulable);
            snapshot.setSummary(asMap(sentinelPayload.get("summary")));
            snapshot.setEnvironmentProfile(asMap(sentinelPayload.get("environmentProfile")));
            snapshot.setDeclaredCapabilities(toDeclaredView(declared));
            snapshot.setOperationalState(resolveOperationalState(schedulable, nodeId, asMap(sentinelPayload.get("remediation"))));
            snapshot.setRemediation(asMap(sentinelPayload.get("remediation")));
            snapshot.setLastProbeAt(resolveProbeTime(sentinelPayload.get("probedAt")));

            if (existing == null) {
                nodeSentinelSnapshotMapper.insert(snapshot);
            } else {
                nodeSentinelSnapshotMapper.updateById(snapshot);
            }
            cacheSnapshot(nodeId, snapshot);
        } catch (Exception e) {
            log.warn("Sentinel 快照写入失败 nodeId={}: {}", nodeId, e.getMessage());
        }
    }

    @Override
    public NodeSentinelRespVO getSnapshot(Long nodeId) {
        NodeSentinelSnapshotDO snapshot = loadSnapshot(nodeId);
        if (snapshot == null) {
            NodeSentinelRespVO empty = new NodeSentinelRespVO();
            empty.setNodeId(nodeId);
            empty.setFresh(false);
            empty.setOperationalState("unknown");
            empty.setComponents(Collections.emptyList());
            empty.setSchedulableCapabilities(Collections.emptyMap());
            empty.setSummary(Collections.emptyMap());
            empty.setEnvironmentProfile(Collections.emptyMap());
            empty.setDeclaredCapabilities(loadDeclaredFromNode(nodeId));
            empty.setRemediateLogs(listRemediateLogs(nodeId));
            return empty;
        }
        NodeSentinelRespVO resp = BeanUtils.toBean(snapshot, NodeSentinelRespVO.class);
        resp.setNodeFunctions(NodeFunctions.parse(snapshot.getNodeProfile()));
        resp.setFresh(isFresh(snapshot.getLastProbeAt()));
        if (resp.getDeclaredCapabilities() == null || resp.getDeclaredCapabilities().isEmpty()) {
            resp.setDeclaredCapabilities(loadDeclaredFromNode(nodeId));
        }
        resp.setRemediateLogs(listRemediateLogs(nodeId));
        return resp;
    }

    @Override
    public NodeSentinelRespVO probe(NodeSentinelProbeReqVO reqVO) {
        ComputeNodeDO node = requireOnlineNode(reqVO.getNodeId());
        String level = StrUtil.blankToDefault(reqVO.getLevel(), "L1");
        Map<String, Object> payload = nodeSentinelAgentClient.probe(node, level);
        ingestHeartbeat(node.getId(), payload);
        return getSnapshot(node.getId());
    }

    @Override
    public NodeSentinelRespVO resync(Long nodeId) {
        NodeSentinelProbeReqVO req = new NodeSentinelProbeReqVO();
        req.setNodeId(nodeId);
        req.setLevel("L1");
        return probe(req);
    }

    @Override
    public Map<String, Object> getRegistry() {
        return sentinelCapabilityRegistry.registryView();
    }

    @Override
    public boolean isCapabilitySchedulable(Long nodeId, String capability) {
        if (!sentinelEnabled || StrUtil.isBlank(capability)) {
            return true;
        }
        Map<String, Boolean> map = getSchedulableMap(nodeId);
        if (map.isEmpty()) {
            return true;
        }
        return Boolean.TRUE.equals(map.get(capability));
    }

    @Override
    @SuppressWarnings("unchecked")
    public Map<String, Boolean> getSchedulableMap(Long nodeId) {
        NodeSentinelSnapshotDO snapshot = loadSnapshot(nodeId);
        if (snapshot == null || !isFresh(snapshot.getLastProbeAt())) {
            return Collections.emptyMap();
        }
        Map<String, Object> raw = snapshot.getSchedulableCapabilities();
        if (raw == null || raw.isEmpty()) {
            return Collections.emptyMap();
        }
        Map<String, Boolean> result = new HashMap<>();
        for (Map.Entry<String, Object> entry : raw.entrySet()) {
            if (entry.getValue() instanceof Map<?, ?> detail) {
                Object sched = detail.get("schedulable");
                result.put(entry.getKey(), Boolean.TRUE.equals(sched));
            }
        }
        return result;
    }

    @Override
    public Map<String, Object> remediate(NodeSentinelRemediateReqVO reqVO) {
        Map<String, Object> result = nodeSentinelRemediatorService.remediate(reqVO);
        persistRemediateLog(reqVO.getNodeId(), reqVO.getComponentId(), result, false);
        return result;
    }

    @Override
    public Map<String, Object> reportRemediation(NodeSentinelRemediateReportReqVO reqVO) {
        ComputeNodeDO node = computeNodeMapper.selectById(reqVO.getNodeId());
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (StrUtil.isNotBlank(reqVO.getAgentToken())
                && !reqVO.getAgentToken().equals(node.getAgentToken())) {
            throw exception(com.basiclab.iot.node.enums.ErrorCodeConstants.AGENT_TOKEN_INVALID);
        }
        Map<String, Object> result = new HashMap<>();
        result.put("success", Boolean.TRUE.equals(reqVO.getSuccess()));
        result.put("message", reqVO.getMessage());
        result.put("action", reqVO.getAction());
        result.put("logs", reqVO.getLogs() != null ? reqVO.getLogs() : List.of());
        result.put("attempt", reqVO.getAttemptCount());
        result.put("maxAttempts", reqVO.getMaxAttempts());
        result.put("mark", reqVO.getMark());
        persistRemediateLog(reqVO.getNodeId(), reqVO.getComponentId(), result,
                Boolean.TRUE.equals(reqVO.getExhausted()) || "exhausted".equals(reqVO.getMark())
                        || "unhealable".equals(reqVO.getMark()));
        if (Boolean.TRUE.equals(reqVO.getExhausted()) || "exhausted".equals(reqVO.getMark())) {
            log.warn("Sentinel 自愈耗尽 nodeId={} component={} attempts={}/{}: {}",
                    reqVO.getNodeId(), reqVO.getComponentId(),
                    reqVO.getAttemptCount(), reqVO.getMaxAttempts(), reqVO.getMessage());
        }
        result.put("accepted", true);
        return result;
    }

    @Override
    public List<NodeSentinelRemediateLogRespVO> listRemediateLogs(Long nodeId) {
        return nodeSentinelRemediateLogMapper.selectRecentByNodeId(nodeId, 50).stream()
                .map(row -> BeanUtils.toBean(row, NodeSentinelRemediateLogRespVO.class))
                .toList();
    }

    @SuppressWarnings("unchecked")
    private void persistRemediateLog(Long nodeId, String componentId, Map<String, Object> result, boolean exhausted) {
        if (nodeId == null || StrUtil.isBlank(componentId) || result == null) {
            return;
        }
        try {
            NodeSentinelRemediateLogDO row = NodeSentinelRemediateLogDO.builder()
                    .nodeId(nodeId)
                    .componentId(componentId)
                    .mark(asString(result.get("mark"), exhausted ? "exhausted" : "healing"))
                    .action(asString(result.get("action"), null))
                    .success(Boolean.TRUE.equals(result.get("success")))
                    .exhausted(exhausted)
                    .attemptCount(result.get("attempt") instanceof Number n ? n.intValue() : 0)
                    .maxAttempts(result.get("maxAttempts") instanceof Number n ? n.intValue() : 3)
                    .probeState(asString(result.get("probeState"), null))
                    .message(asString(result.get("message"), asString(result.get("reason"), null)))
                    .logs(result.get("logs") instanceof List<?> list ? (List<Map<String, Object>>) list : List.of())
                    .build();
            nodeSentinelRemediateLogMapper.insert(row);
        } catch (Exception e) {
            log.warn("Sentinel 自愈日志写入失败 nodeId={} component={}: {}", nodeId, componentId, e.getMessage());
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    public void validateBeforeDeploy(Long nodeId, String workloadType, Map<String, Object> requirements) {
        if (!sentinelEnabled) {
            return;
        }
        ComputeNodeDO node = requireOnlineNode(nodeId);
        Map<String, Object> result = nodeSentinelAgentClient.validate(node, workloadType, requirements);
        if (Boolean.TRUE.equals(result.get("valid"))) {
            return;
        }
        List<String> missing = result.get("missingCapabilities") instanceof List<?> list
                ? (List<String>) list.stream().map(String::valueOf).toList()
                : List.of();
        throw exception(AGENT_COMMAND_FAILED,
                "Sentinel 部署前校验未通过: " + String.join(", ", missing));
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> applyAggregatorOverlay(
            Long nodeId, Map<String, Object> schedulable, Map<String, Boolean> declared) {
        if (schedulable == null) {
            schedulable = new HashMap<>();
        } else {
            schedulable = new HashMap<>(schedulable);
        }
        for (Map.Entry<String, Boolean> entry : declared.entrySet()) {
            if (!Boolean.TRUE.equals(entry.getValue())) {
                schedulable.put(entry.getKey(), Map.of(
                        "schedulable", false,
                        "state", "disabled",
                        "reason", "节点未声明该能力",
                        "missingComponents", List.of()));
            }
        }
        applyResourceDegradation(nodeId, schedulable);
        return schedulable;
    }

    @SuppressWarnings("unchecked")
    private void applyResourceDegradation(Long nodeId, Map<String, Object> schedulable) {
        NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(nodeId);
        if (metric == null) {
            return;
        }
        double cpu = metric.getCpuPercent() != null ? metric.getCpuPercent().doubleValue() : 0;
        double mem = metric.getMemPercent() != null ? metric.getMemPercent().doubleValue() : 0;
        if (cpu < resourceDegradeCpuPercent && mem < resourceDegradeMemPercent) {
            return;
        }
        String reason = String.format("资源过载 CPU=%.0f%% MEM=%.0f%%", cpu, mem);
        for (Map.Entry<String, Object> entry : schedulable.entrySet()) {
            if (!(entry.getValue() instanceof Map<?, ?> detail)) {
                continue;
            }
            Map<String, Object> copy = new HashMap<>((Map<String, Object>) detail);
            if (Boolean.TRUE.equals(copy.get("schedulable"))) {
                copy.put("schedulable", false);
                copy.put("state", "degraded");
                copy.put("reason", reason);
                schedulable.put(entry.getKey(), copy);
            }
        }
    }

    private String resolveOperationalState(Map<String, Object> schedulable, Long nodeId,
                                          Map<String, Object> remediation) {
        if (remediation != null) {
            Object summary = remediation.get("summary");
            if (summary instanceof Map<?, ?> sum) {
                Object exhausted = sum.get("exhausted");
                if (exhausted instanceof Number number && number.intValue() > 0) {
                    return "degraded";
                }
            }
        }
        if (schedulable == null || schedulable.isEmpty()) {
            return "unknown";
        }
        int schedCount = 0;
        int total = schedulable.size();
        for (Object value : schedulable.values()) {
            if (value instanceof Map<?, ?> detail && Boolean.TRUE.equals(detail.get("schedulable"))) {
                schedCount++;
            }
        }
        NodeMetricSnapshotDO metric = nodeMetricSnapshotMapper.selectLatestByNodeId(nodeId);
        if (metric != null) {
            double cpu = metric.getCpuPercent() != null ? metric.getCpuPercent().doubleValue() : 0;
            double mem = metric.getMemPercent() != null ? metric.getMemPercent().doubleValue() : 0;
            if (cpu >= resourceDegradeCpuPercent || mem >= resourceDegradeMemPercent) {
                return schedCount > 0 ? "degraded" : "unavailable";
            }
        }
        if (schedCount == 0) {
            return "unavailable";
        }
        if (schedCount < total) {
            return "degraded";
        }
        return "healthy";
    }

    private Map<String, Object> loadDeclaredFromNode(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        return toDeclaredView(node != null ? node.getCapabilities() : null);
    }

    private Map<String, Object> toDeclaredView(Map<String, Boolean> declared) {
        if (declared == null || declared.isEmpty()) {
            return Collections.emptyMap();
        }
        Map<String, Object> view = new HashMap<>();
        declared.forEach((k, v) -> view.put(k, Boolean.TRUE.equals(v)));
        return view;
    }

    private ComputeNodeDO requireOnlineNode(Long nodeId) {
        ComputeNodeDO node = computeNodeMapper.selectById(nodeId);
        if (node == null) {
            throw exception(COMPUTE_NODE_NOT_EXISTS);
        }
        if (!NodeStatusEnum.ONLINE.getStatus().equals(node.getStatus())) {
            throw exception(COMPUTE_NODE_OFFLINE);
        }
        return node;
    }

    private NodeSentinelSnapshotDO loadSnapshot(Long nodeId) {
        try {
            String cached = stringRedisTemplate.opsForValue().get(REDIS_KEY_PREFIX + nodeId);
            if (StrUtil.isNotBlank(cached)) {
                return objectMapper.readValue(cached, NodeSentinelSnapshotDO.class);
            }
        } catch (Exception ignored) {
            // fallback DB
        }
        return nodeSentinelSnapshotMapper.selectById(nodeId);
    }

    private void cacheSnapshot(Long nodeId, NodeSentinelSnapshotDO snapshot) {
        try {
            stringRedisTemplate.opsForValue().set(
                    REDIS_KEY_PREFIX + nodeId,
                    objectMapper.writeValueAsString(snapshot),
                    FRESH_SECONDS * 2,
                    TimeUnit.SECONDS);
        } catch (Exception e) {
            log.debug("Sentinel Redis 缓存失败 nodeId={}: {}", nodeId, e.getMessage());
        }
    }

    private boolean isFresh(LocalDateTime lastProbeAt) {
        if (lastProbeAt == null) {
            return false;
        }
        return lastProbeAt.isAfter(LocalDateTime.now().minusSeconds(FRESH_SECONDS));
    }

    private LocalDateTime resolveProbeTime(Object probedAt) {
        if (probedAt instanceof Number number) {
            long ms = number.longValue();
            if (ms > 0) {
                return LocalDateTime.ofInstant(Instant.ofEpochMilli(ms), ZoneId.systemDefault());
            }
        }
        return LocalDateTime.now();
    }

    private String resolveFunctionsCsv(Map<String, Object> sentinelPayload, ComputeNodeDO node) {
        Object raw = sentinelPayload.get("nodeFunctions");
        if (raw instanceof List<?> list) {
            String csv = NodeFunctions.toCsv(list.stream().map(String::valueOf).toList());
            if (!csv.isBlank()) {
                return csv;
            }
        }
        String fromProfile = NodeFunctions.toCsv(NodeFunctions.parse(asString(sentinelPayload.get("nodeProfile"), "")));
        if (!fromProfile.isBlank()) {
            return fromProfile;
        }
        return node != null ? NodeFunctions.toCsv(NodeFunctions.parse(node)) : "";
    }

    private String asString(Object value, String defaultValue) {
        if (value == null) {
            return defaultValue;
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() ? defaultValue : text;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> asList(Object value) {
        if (value instanceof List<?> list) {
            return (List<Map<String, Object>>) list;
        }
        return Collections.emptyList();
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return Collections.emptyMap();
    }
}
