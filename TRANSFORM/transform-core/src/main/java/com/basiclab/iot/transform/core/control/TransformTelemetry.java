package com.basiclab.iot.transform.core.control;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.HashMap;
import java.util.Map;

/**
 * 上行监测遥测（Topic: iot_transform_telemetry）。
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TransformTelemetry {
    private String instanceId;
    private String nodeId;
    private String host;
    private String role;
    /** ONLINE | DEGRADED | STOPPING */
    private String status;
    private String joinedGroups;
    private double cpuLoad;
    private long heapUsedMb;
    private long heapMaxMb;
    private long maxConsumerLag;
    private double deliverSuccessRate;
    @Builder.Default
    private Map<String, Long> metrics = new HashMap<>();
    private String adaptDecision;
    private long timestampEpochMs;
}
