package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

@Schema(description = "EDGE 拉取运行时动态配置 Request")
@Data
public class EdgeRuntimeConfigReqVO {

    @Schema(description = "节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "节点 ID 不能为空")
    private Long nodeId;

    @Schema(description = "Agent 令牌", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "Agent 令牌不能为空")
    private String agentToken;

    @Schema(description = "机器指纹（可选校验）")
    private String fingerprint;

}
