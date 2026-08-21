package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Map;

@Schema(description = "边缘节点 Response")
@Data
public class EdgeNodeRespVO {

    private Long id;
    private Long computeNodeId;
    private String name;
    private String host;
    private String status;
    private String fingerprint;
    private String mqttClientId;
    private String mqttUsername;
    private String agentVersion;
    private String nodeRole;
    private Integer maxTaskCount;
    private Integer activeTaskCount;
    private Boolean cephMountReady;
    private LocalDateTime lastHeartbeatAt;
    private Boolean enabled;
    private String remark;
    private Map<String, String> tags;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    /** 关联 compute_node 实时指标（可选填充） */
    private Double cpuPercent;
    private Double memPercent;
    private Integer agentPort;

}
