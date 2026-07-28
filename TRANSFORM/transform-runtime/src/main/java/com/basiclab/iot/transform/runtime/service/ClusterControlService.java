package com.basiclab.iot.transform.runtime.service;

import com.basiclab.iot.transform.capability.sense.DefaultSenseCapability;
import com.basiclab.iot.transform.capability.sense.SenseCapability;
import com.basiclab.iot.transform.core.control.TransformCommand;
import com.basiclab.iot.transform.core.control.TransformHeartbeat;
import com.basiclab.iot.transform.core.control.TransformTelemetry;
import com.basiclab.iot.transform.core.contract.TransformTopics;
import com.basiclab.iot.transform.core.domain.RuntimeInstance;
import com.basiclab.iot.transform.core.sense.NodeSenseSnapshot;
import com.basiclab.iot.transform.runtime.config.TransformRuntimeProperties;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.net.InetAddress;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 集群控制面：上行遥测落盘+Kafka，下行指令下发。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ClusterControlService {

    private final TransformRepository repository;
    private final SenseCapability senseCapability;
    private final MetricsService metricsService;
    private final TransformRuntimeProperties properties;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    public String localInstanceId() {
        if (senseCapability instanceof DefaultSenseCapability dsc) {
            return dsc.getInstanceId();
        }
        return properties.getInstanceId() == null || properties.getInstanceId().isBlank()
                ? "unknown"
                : properties.getInstanceId();
    }

    public TransformTelemetry publishTelemetry(String adaptDecision) {
        NodeSenseSnapshot snap = senseCapability.sense();
        snap.setNodeId(properties.getNodeId());
        Map<String, Long> metrics = metricsService.snapshot();
        long delivered = metrics.getOrDefault("delivered", 0L);
        long failed = metrics.getOrDefault("failed", 0L);
        double rate = (delivered + failed) == 0 ? 1.0 : (double) delivered / (delivered + failed);
        String host = resolveHost();
        String groups = String.join(",", List.of(
                "transform.kafka.consume.device",
                "transform.http.deliver",
                "transform.party.deliver"
        ));
        TransformTelemetry telemetry = TransformTelemetry.builder()
                .instanceId(snap.getInstanceId())
                .nodeId(properties.getNodeId())
                .host(host)
                .role(properties.getRole())
                .status("ONLINE")
                .joinedGroups(groups)
                .cpuLoad(snap.getCpuLoad())
                .heapUsedMb(snap.getHeapUsedMb())
                .heapMaxMb(snap.getHeapMaxMb())
                .maxConsumerLag(snap.getMaxConsumerLag())
                .deliverSuccessRate(rate)
                .metrics(metrics)
                .adaptDecision(adaptDecision)
                .timestampEpochMs(System.currentTimeMillis())
                .build();
        repository.upsertRuntimeInstance(RuntimeInstance.builder()
                .instanceId(telemetry.getInstanceId())
                .nodeId(telemetry.getNodeId())
                .host(telemetry.getHost())
                .role(telemetry.getRole())
                .status(telemetry.getStatus())
                .joinedGroups(telemetry.getJoinedGroups())
                .cpuLoad(telemetry.getCpuLoad())
                .heapUsedMb(telemetry.getHeapUsedMb())
                .heapMaxMb(telemetry.getHeapMaxMb())
                .maxConsumerLag(telemetry.getMaxConsumerLag())
                .deliverSuccessRate(telemetry.getDeliverSuccessRate())
                .metrics(telemetry.getMetrics())
                .adaptDecision(telemetry.getAdaptDecision())
                .lastHeartbeatTime(Instant.now())
                .build());
        try {
            kafkaTemplate.send(
                    TransformTopics.TELEMETRY,
                    telemetry.getInstanceId(),
                    objectMapper.writeValueAsString(telemetry));
        } catch (Exception e) {
            log.warn("[ClusterControlService] publish telemetry failed: {}", e.getMessage());
        }
        publishHeartbeat(telemetry);
        return telemetry;
    }

    /**
     * 发布轻量心跳到约定 topic，供 NODE 分发流水线 / 业务总览做存活验收。
     * 端口可变时不以 HTTP 探活为主，以本 topic 为准。
     */
    public void publishHeartbeat(TransformTelemetry telemetry) {
        if (telemetry == null) {
            return;
        }
        Integer port = null;
        try {
            String p = System.getenv("SERVER_PORT");
            if (p == null || p.isBlank()) {
                p = System.getenv("PORT");
            }
            if (p != null && !p.isBlank()) {
                port = Integer.parseInt(p.trim());
            }
        } catch (Exception ignored) {
            // ignore
        }
        TransformHeartbeat hb = TransformHeartbeat.builder()
                .kind("HEARTBEAT")
                .instanceId(telemetry.getInstanceId())
                .nodeId(telemetry.getNodeId())
                .host(telemetry.getHost())
                .status(telemetry.getStatus() == null ? "ONLINE" : telemetry.getStatus())
                .port(port)
                .timestampEpochMs(System.currentTimeMillis())
                .build();
        try {
            kafkaTemplate.send(
                    TransformTopics.HEARTBEAT,
                    hb.getInstanceId(),
                    objectMapper.writeValueAsString(hb));
        } catch (Exception e) {
            log.warn("[ClusterControlService] publish heartbeat failed: {}", e.getMessage());
        }
    }

    public String issueCommand(TransformCommand command) {
        if (command.getCommandId() == null || command.getCommandId().isBlank()) {
            command.setCommandId(UUID.randomUUID().toString().replace("-", ""));
        }
        if (command.getIssuedAt() <= 0) {
            command.setIssuedAt(System.currentTimeMillis());
        }
        if (command.getTargetInstanceId() == null || command.getTargetInstanceId().isBlank()) {
            command.setTargetInstanceId("*");
        }
        try {
            kafkaTemplate.send(
                    TransformTopics.COMMAND,
                    command.getTargetInstanceId(),
                    objectMapper.writeValueAsString(command)).get();
            return command.getCommandId();
        } catch (Exception e) {
            throw new IllegalStateException("issue command failed: " + e.getMessage(), e);
        }
    }

    public List<RuntimeInstance> listInstances() {
        return repository.listRuntimeInstances().stream()
                .sorted((a, b) -> Boolean.compare(b.isOnline(), a.isOnline()))
                .collect(Collectors.toList());
    }

    public void handleCommand(TransformCommand command) {
        if (command == null || command.getType() == null) {
            return;
        }
        String local = localInstanceId();
        String target = command.getTargetInstanceId();
        if (target != null && !"*".equals(target) && !target.equals(local)) {
            return;
        }
        String nodeTarget = command.getTargetNodeId();
        if (nodeTarget != null && !nodeTarget.isBlank()
                && properties.getNodeId() != null
                && !nodeTarget.equals(properties.getNodeId())) {
            return;
        }
        switch (command.getType()) {
            case "PING" -> log.info("[ClusterControlService] PING ok instance={}", local);
            case "RELOAD_CONFIG" -> log.info("[ClusterControlService] RELOAD_CONFIG acknowledged instance={}", local);
            case "SET_ROLE" -> log.info("[ClusterControlService] SET_ROLE payload={} (restart required to apply)",
                    command.getPayload());
            case "SET_CHANNELS" -> log.info("[ClusterControlService] SET_CHANNELS payload={} (restart required to apply)",
                    command.getPayload());
            case "SHUTDOWN_HINT" -> log.warn("[ClusterControlService] SHUTDOWN_HINT received instance={}", local);
            default -> log.info("[ClusterControlService] ignore command type={}", command.getType());
        }
    }

    private String resolveHost() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (Exception e) {
            return "unknown";
        }
    }
}
