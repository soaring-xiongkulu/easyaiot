package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.Map;

@Schema(description = "Sentinel 组件修复 Request VO")
@Data
public class NodeSentinelRemediateReqVO {

    @Schema(description = "节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "nodeId 不能为空")
    private Long nodeId;

    @Schema(description = "组件 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "componentId 不能为空")
    private String componentId;

    @Schema(description = "修复动作（registry 定义）")
    private String action;

    @Schema(description = "动作参数")
    private Map<String, Object> params;

    @Schema(description = "Agent Token（Agent 侧调用时携带，管理端可省略）")
    private String agentToken;

    @Schema(description = "当前尝试次数")
    private Integer attempt;

    @Schema(description = "最大尝试次数")
    private Integer maxAttempts;
}
