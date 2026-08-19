package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@Schema(description = "Agent - 心跳 Request VO")
@Data
public class NodeAgentHeartbeatReqVO {

    @Schema(description = "节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "节点 ID 不能为空")
    private Long nodeId;

    @Schema(description = "Agent 令牌", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "Agent 令牌不能为空")
    private String agentToken;

    @Schema(description = "主机名（用于识别冲突 Agent，防止同一 NODE_ID 被多台机器交叉上报）")
    private String hostname;

    @Schema(description = "CPU 使用率")
    private BigDecimal cpuPercent;

    @Schema(description = "内存使用率")
    private BigDecimal memPercent;

    @Schema(description = "内存已用字节")
    private Long memUsedBytes;

    @Schema(description = "内存总字节")
    private Long memTotalBytes;

    @Schema(description = "磁盘使用率")
    private BigDecimal diskPercent;

    @Schema(description = "磁盘已用字节")
    private Long diskUsedBytes;

    @Schema(description = "磁盘总字节")
    private Long diskTotalBytes;

    @Schema(description = "带宽 Mbps")
    private BigDecimal bandwidthMbps;

    @Schema(description = "活跃任务数")
    private Integer activeTasks;

    @Schema(description = "GPU 信息")
    private List<Map<String, Object>> gpuInfo;

    @Schema(description = "运行中的工作负载")
    private List<Map<String, Object>> workloads;

    @Schema(description = "是否处于集群模式")
    private Boolean clusterMode;

    @Schema(description = "CephFS 挂载根路径")
    private String cephMountRoot;

    @Schema(description = "CephFS 挂载是否就绪")
    private Boolean cephMountReady;

}
