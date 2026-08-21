package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "调度 - 分配节点 Response VO")
@Data
public class NodeSchedulerAllocateRespVO {

    @Schema(description = "节点 ID")
    private Long nodeId;

    @Schema(description = "主机地址")
    private String host;

    @Schema(description = "Agent 端口")
    private Integer agentPort;

    @Schema(description = "推荐 GPU IDs")
    private String gpuIds;

    @Schema(description = "绑定 ID")
    private Long bindingId;

}
