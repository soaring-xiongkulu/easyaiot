package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.Map;

@Schema(description = "媒体 - 远程部署 SRS/ZLM Request VO")
@Data
public class NodeMediaDeployReqVO {

    @Schema(description = "节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "节点 ID 不能为空")
    private Long nodeId;

    @Schema(description = "媒体栈类型: srs_live | srs_ai | zlm", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "媒体栈类型不能为空")
    private String stackType;

    @Schema(description = "部署环境变量")
    private Map<String, String> env;

}
