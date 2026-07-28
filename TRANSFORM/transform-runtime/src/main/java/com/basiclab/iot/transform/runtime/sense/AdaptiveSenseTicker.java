package com.basiclab.iot.transform.runtime.sense;

import com.basiclab.iot.transform.capability.sense.SenseCapability;
import com.basiclab.iot.transform.core.sense.NodeSenseSnapshot;
import com.basiclab.iot.transform.runtime.config.TransformRuntimeProperties;
import com.basiclab.iot.transform.runtime.service.ClusterControlService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 周期自感知 → 自适应决策 → 上行遥测 + 心跳（PG + Kafka）。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AdaptiveSenseTicker {

    private final SenseCapability senseCapability;
    private final TransformRuntimeProperties properties;
    private final ClusterControlService clusterControlService;

    /** 启动后立刻发一次心跳，缩短分发流水线验收等待。 */
    @EventListener(ApplicationReadyEvent.class)
    public void onReady() {
        try {
            clusterControlService.publishTelemetry("READY");
            log.info("[AdaptiveSenseTicker] initial heartbeat published instance={}",
                    clusterControlService.localInstanceId());
        } catch (Exception e) {
            log.warn("[AdaptiveSenseTicker] initial heartbeat failed: {}", e.getMessage());
        }
    }

    @Scheduled(fixedDelayString = "${transform.sense.interval-ms:15000}")
    public void tick() {
        NodeSenseSnapshot snapshot = senseCapability.sense();
        snapshot.setNodeId(properties.getNodeId());
        String decision = senseCapability.adapt(snapshot);
        clusterControlService.publishTelemetry(decision);
        if (!"KEEP".equals(decision)) {
            log.info("[AdaptiveSenseTicker] decision={} instance={}", decision, snapshot.getInstanceId());
        }
    }
}
