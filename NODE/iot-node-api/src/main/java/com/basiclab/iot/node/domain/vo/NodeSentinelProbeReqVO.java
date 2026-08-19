package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

@Schema(description = "Sentinel 主动探测 Request VO")
@Data
public class NodeSentinelProbeReqVO {

    @Schema(description = "节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "nodeId 不能为空")
    private Long nodeId;

    @Schema(description = "探测级别 L0|L1|L2，默认 L1")
    private String level;
}
