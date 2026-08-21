package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Schema(description = "集群概览 WebSocket - 节点指标快照")
@Data
public class NodeClusterMetricNodeVO {

    private Long id;
    private String name;
    private String host;
    private String status;
    private String nodeRole;
    private BigDecimal cpuPercent;
    private BigDecimal memPercent;
    private Long memUsedBytes;
    private Long memTotalBytes;
    private BigDecimal diskPercent;
    private Long diskUsedBytes;
    private Long diskTotalBytes;
    private Integer activeTasks;
    private String gpuInfo;
    private LocalDateTime lastHeartbeatAt;
    private Boolean isPlatform;

}
