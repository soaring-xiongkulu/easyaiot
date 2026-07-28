package com.basiclab.iot.transform.core.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/** 运行实例监测视图。 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuntimeInstance {
    private String instanceId;
    private String nodeId;
    private String host;
    private String role;
    private String status;
    private String joinedGroups;
    private Double cpuLoad;
    private Long heapUsedMb;
    private Long heapMaxMb;
    private Long maxConsumerLag;
    private Double deliverSuccessRate;
    @Builder.Default
    private Map<String, Long> metrics = new HashMap<>();
    private String adaptDecision;
    private Instant lastHeartbeatTime;
    private boolean online;
}
