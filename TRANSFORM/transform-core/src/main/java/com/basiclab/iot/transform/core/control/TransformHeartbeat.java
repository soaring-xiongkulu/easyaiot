package com.basiclab.iot.transform.core.control;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 轻量心跳（Topic: iot_transform_heartbeat）。
 * <p>
 * 用于分发/部署验收：端口可随节点变化，不以固定 HTTP 端口判断存活，
 * 而以约定 topic 上出现匹配 instanceId / nodeId 的心跳为准。
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TransformHeartbeat {
    /** 固定约定：HEARTBEAT */
    private String kind;
    private String instanceId;
    private String nodeId;
    private String host;
    /** ONLINE | STARTING | STOPPING */
    private String status;
    /** 实际监听端口（容器内或主机映射均可，仅作观测） */
    private Integer port;
    private long timestampEpochMs;
}
