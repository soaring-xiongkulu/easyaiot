package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "控制面宿主机 Agent 自动启动引导信息")
@Data
public class PlatformAgentBootstrapRespVO {

    @Schema(description = "节点 ID")
    private Long nodeId;

    @Schema(description = "Agent 令牌")
    private String agentToken;

    @Schema(description = "Agent 监听端口")
    private Integer agentPort;

    @Schema(description = "控制面 Agent API 根地址")
    private String controlPlaneUrl;
}
