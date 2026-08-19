package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.Map;

@Schema(description = "Agent - 注册 Request VO")
@Data
public class NodeAgentRegisterReqVO {

    @Schema(description = "节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "节点 ID 不能为空")
    private Long nodeId;

    @Schema(description = "Agent 令牌", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "Agent 令牌不能为空")
    private String agentToken;

    @Schema(description = "主机名")
    private String hostname;

    @Schema(description = "操作系统")
    private String osInfo;

    @Schema(description = "Agent 版本")
    private String agentVersion;

    @Schema(description = "能力声明")
    private Map<String, Boolean> capabilities;

}
