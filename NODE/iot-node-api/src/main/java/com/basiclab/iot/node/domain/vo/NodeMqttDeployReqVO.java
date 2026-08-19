package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;
import java.util.Map;

@Schema(description = "MQTT 网关 Agent 部署请求")
@Data
public class NodeMqttDeployReqVO {

    @Schema(description = "节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "节点 ID 不能为空")
    private Long nodeId;

    @Schema(description = "栈类型，固定 emqx")
    private String stackType = "emqx";

    @Schema(description = "覆盖环境变量")
    private Map<String, String> env;

}
