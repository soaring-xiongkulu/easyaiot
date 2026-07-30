package com.basiclab.iot.transform.runtime.kafka;

import com.basiclab.iot.transform.core.control.TransformTelemetry;
import com.basiclab.iot.transform.core.contract.TransformTopics;
import com.basiclab.iot.transform.core.domain.RuntimeInstance;
import com.basiclab.iot.transform.runtime.dal.TransformRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

import java.time.Instant;

/**
 * 汇聚各 TRANSFORM 实例上行遥测：每实例独立 Group，保证控制面列表能看到集群内全部容器。
 * <p>
 * 仅靠本机 PG 自写心跳时，跨节点/跨库副本会在短时间窗口后被误判离线；
 * 订阅 {@link TransformTopics#TELEMETRY} 后把对端心跳落到本机可读的运行实例表。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ClusterTelemetryListener {

    private final ObjectMapper objectMapper;
    private final TransformRepository repository;

    @KafkaListener(
            topics = TransformTopics.TELEMETRY,
            groupId = "transform.telemetry.${transform.instance-id:local}",
            autoStartup = "true"
    )
    public void onTelemetry(ConsumerRecord<String, String> record, Acknowledgment ack) {
        try {
            TransformTelemetry telemetry = objectMapper.readValue(record.value(), TransformTelemetry.class);
            if (telemetry == null || telemetry.getInstanceId() == null || telemetry.getInstanceId().isBlank()) {
                ack.acknowledge();
                return;
            }
            Instant hb = telemetry.getTimestampEpochMs() > 0
                    ? Instant.ofEpochMilli(telemetry.getTimestampEpochMs())
                    : Instant.now();
            repository.upsertRuntimeInstance(RuntimeInstance.builder()
                    .instanceId(telemetry.getInstanceId())
                    .nodeId(telemetry.getNodeId())
                    .host(telemetry.getHost())
                    .role(telemetry.getRole())
                    .status(telemetry.getStatus() == null || telemetry.getStatus().isBlank()
                            ? "ONLINE"
                            : telemetry.getStatus())
                    .joinedGroups(telemetry.getJoinedGroups())
                    .cpuLoad(telemetry.getCpuLoad())
                    .heapUsedMb(telemetry.getHeapUsedMb())
                    .heapMaxMb(telemetry.getHeapMaxMb())
                    .maxConsumerLag(telemetry.getMaxConsumerLag())
                    .deliverSuccessRate(telemetry.getDeliverSuccessRate())
                    .metrics(telemetry.getMetrics())
                    .adaptDecision(telemetry.getAdaptDecision())
                    .lastHeartbeatTime(hb)
                    .online(true)
                    .build());
            ack.acknowledge();
        } catch (Exception e) {
            log.warn("[ClusterTelemetryListener] ingest failed: {}", e.getMessage());
            ack.acknowledge();
        }
    }
}
