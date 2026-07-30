package com.basiclab.iot.transform.runtime.service;

import com.basiclab.iot.transform.capability.sense.DefaultSenseCapability;
import com.basiclab.iot.transform.capability.sense.SenseCapability;
import com.basiclab.iot.transform.core.control.TransformCommand;
import com.basiclab.iot.transform.core.control.TransformCommandAck;
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
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.net.InetAddress;
import java.net.NetworkInterface;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Collectors;

/**
 * 集群控制面：上行遥测落盘+Kafka，下行指令下发与落地执行。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ClusterControlService {

    private static final int MAX_ACKS_PER_COMMAND = 64;
    private static final int MAX_TRACKED_COMMANDS = 256;

    private final TransformRepository repository;
    private final SenseCapability senseCapability;
    private final MetricsService metricsService;
    private final TransformRuntimeProperties properties;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;
    private final ConfigurableApplicationContext applicationContext;

    private final ConcurrentHashMap<String, ConcurrentLinkedDeque<TransformCommandAck>> ackStore =
            new ConcurrentHashMap<>();
    private final ExecutorService shutdownExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "transform-shutdown");
        t.setDaemon(true);
        return t;
    });

    public String localInstanceId() {
        if (senseCapability instanceof DefaultSenseCapability dsc) {
            return dsc.getInstanceId();
        }
        return properties.getInstanceId() == null || properties.getInstanceId().isBlank()
                ? "unknown"
                : properties.getInstanceId();
    }

    /** 本机上报用的主机名，供管理端标本机。 */
    public String localHost() {
        return resolveHost();
    }

    public TransformTelemetry publishTelemetry(String adaptDecision) {
        return publishTelemetry(adaptDecision, "ONLINE");
    }

    public TransformTelemetry publishTelemetry(String adaptDecision, String status) {
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
        String st = status == null || status.isBlank() ? "ONLINE" : status;
        TransformTelemetry telemetry = TransformTelemetry.builder()
                .instanceId(snap.getInstanceId())
                .nodeId(properties.getNodeId())
                .host(host)
                .role(properties.getRole())
                .status(st)
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
        // 预置空桶，便于 UI 立刻轮询
        ackStore.computeIfAbsent(command.getCommandId(), k -> new ConcurrentLinkedDeque<>());
        trimAckStore();
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

    /**
     * 清理幽灵实例记录（容器已删但监控表仍留行）。
     * @param offlineOnly true=清理超过 10 分钟无心跳；false=清理超过 30 分钟无心跳
     */
    public int purgeStaleInstances(boolean offlineOnly) {
        Instant cutoff = Instant.now().minusSeconds(offlineOnly ? 600 : 1800);
        int n = repository.deleteStaleRuntimeInstances(cutoff, localInstanceId());
        if (n > 0) {
            log.info("[ClusterControlService] purged {} ghost runtime instance(s), offlineOnly={}",
                    n, offlineOnly);
        }
        return n;
    }

    public boolean removeInstanceRecord(String instanceId) {
        if (instanceId == null || instanceId.isBlank()) {
            return false;
        }
        if (instanceId.equals(localInstanceId())) {
            throw new IllegalArgumentException("cannot remove the local serving instance record");
        }
        return repository.deleteRuntimeInstance(instanceId);
    }

    public List<TransformCommandAck> listCommandAcks(String commandId) {
        if (commandId == null || commandId.isBlank()) {
            return List.of();
        }
        ConcurrentLinkedDeque<TransformCommandAck> q = ackStore.get(commandId);
        if (q == null || q.isEmpty()) {
            return List.of();
        }
        return new ArrayList<>(q);
    }

    /** 汇聚对端回执（Kafka COMMAND_ACK）。 */
    public void ingestAck(TransformCommandAck ack) {
        if (ack == null || ack.getCommandId() == null || ack.getCommandId().isBlank()) {
            return;
        }
        ConcurrentLinkedDeque<TransformCommandAck> q =
                ackStore.computeIfAbsent(ack.getCommandId(), k -> new ConcurrentLinkedDeque<>());
        // 同实例同指令去重，保留最新
        q.removeIf(a -> ack.getInstanceId() != null && ack.getInstanceId().equals(a.getInstanceId()));
        q.addLast(ack);
        while (q.size() > MAX_ACKS_PER_COMMAND) {
            q.pollFirst();
        }
        trimAckStore();
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
                && !properties.getNodeId().isBlank()
                && !nodeTarget.equals(properties.getNodeId())) {
            return;
        }
        try {
            switch (command.getType()) {
                case "PING" -> {
                    publishTelemetry("PONG");
                    publishAck(command, "OK", "pong");
                    log.info("[ClusterControlService] PING ok instance={}", local);
                }
                case "RELOAD_CONFIG" -> {
                    // 规则/映射/目的地均直读 PG，无内存 cache；此处刷新感知并上报确认
                    long parties = repository.partyCount();
                    long contracts = repository.contractCount();
                    long mappings = repository.mappingCount();
                    publishTelemetry("RELOADED");
                    publishAck(command, "OK",
                            "config live from PG; parties=" + parties
                                    + ", contracts=" + contracts
                                    + ", mappings=" + mappings);
                    log.info("[ClusterControlService] RELOAD_CONFIG ok instance={} parties={} contracts={} mappings={}",
                            local, parties, contracts, mappings);
                }
                case "SET_ROLE" -> {
                    publishAck(command, "REQUIRES_RESTART",
                            "role change requires container recreate with TRANSFORM_ROLE; payload="
                                    + String.valueOf(command.getPayload()));
                    log.info("[ClusterControlService] SET_ROLE requires restart instance={} payload={}",
                            local, command.getPayload());
                }
                case "SET_CHANNELS" -> {
                    publishAck(command, "REQUIRES_RESTART",
                            "channel flags require container recreate; payload="
                                    + String.valueOf(command.getPayload()));
                    log.info("[ClusterControlService] SET_CHANNELS requires restart instance={} payload={}",
                            local, command.getPayload());
                }
                case "SHUTDOWN_HINT" -> {
                    publishTelemetry("DRAINING", "DRAINING");
                    publishAck(command, "ACCEPTED",
                            "graceful shutdown scheduled; docker unless-stopped needs Agent /workload/stop");
                    log.warn("[ClusterControlService] SHUTDOWN_HINT accepted instance={}", local);
                    scheduleGracefulShutdown();
                }
                default -> {
                    publishAck(command, "IGNORED", "unknown type " + command.getType());
                    log.info("[ClusterControlService] ignore command type={} instance={}",
                            command.getType(), local);
                }
            }
        } catch (Exception e) {
            publishAck(command, "FAILED", e.getMessage());
            log.error("[ClusterControlService] handle command failed type={} instance={}",
                    command.getType(), local, e);
        }
    }

    private void scheduleGracefulShutdown() {
        shutdownExecutor.execute(() -> {
            try {
                Thread.sleep(800L);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            try {
                log.warn("[ClusterControlService] exiting JVM after SHUTDOWN_HINT instance={}",
                        localInstanceId());
                int code = SpringApplication.exit(applicationContext, () -> 0);
                System.exit(code);
            } catch (Exception e) {
                log.error("[ClusterControlService] graceful shutdown failed: {}", e.getMessage());
                System.exit(0);
            }
        });
    }

    private void publishAck(TransformCommand command, String status, String message) {
        TransformCommandAck ack = TransformCommandAck.builder()
                .commandId(command.getCommandId())
                .instanceId(localInstanceId())
                .nodeId(properties.getNodeId())
                .host(resolveHost())
                .type(command.getType())
                .status(status)
                .message(message)
                .timestampEpochMs(System.currentTimeMillis())
                .build();
        ingestAck(ack);
        try {
            kafkaTemplate.send(
                    TransformTopics.COMMAND_ACK,
                    ack.getCommandId() == null ? localInstanceId() : ack.getCommandId(),
                    objectMapper.writeValueAsString(ack));
        } catch (Exception e) {
            log.warn("[ClusterControlService] publish ack failed: {}", e.getMessage());
        }
    }

    private void trimAckStore() {
        while (ackStore.size() > MAX_TRACKED_COMMANDS) {
            String oldest = ackStore.keys().nextElement();
            ackStore.remove(oldest);
        }
    }

    private String resolveHost() {
        if (properties.getHost() != null && !properties.getHost().isBlank()) {
            return properties.getHost().trim();
        }
        String fromEnv = System.getenv("TRANSFORM_HOST");
        if (fromEnv == null || fromEnv.isBlank()) {
            fromEnv = System.getenv("HOST_IP");
        }
        if (fromEnv != null && !fromEnv.isBlank()) {
            return fromEnv.trim();
        }
        try {
            // 优先非回环 IPv4，避免 Docker 内只用容器 hostname（短 hash）导致无法按机器聚合
            for (NetworkInterface nif : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!nif.isUp() || nif.isLoopback() || nif.isVirtual()) {
                    continue;
                }
                for (InetAddress addr : Collections.list(nif.getInetAddresses())) {
                    if (addr.isLoopbackAddress() || addr.isLinkLocalAddress()) {
                        continue;
                    }
                    if (addr instanceof java.net.Inet4Address) {
                        return addr.getHostAddress();
                    }
                }
            }
            return InetAddress.getLocalHost().getHostAddress();
        } catch (Exception e) {
            try {
                return InetAddress.getLocalHost().getHostName();
            } catch (Exception ignored) {
                return "unknown";
            }
        }
    }
}
