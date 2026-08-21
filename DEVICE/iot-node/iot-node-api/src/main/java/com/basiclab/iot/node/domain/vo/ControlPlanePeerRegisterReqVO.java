package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import java.util.List;

@Schema(description = "中心节点互联 - 对等注册 Request VO")
@Data
public class ControlPlanePeerRegisterReqVO {

    @Schema(description = "对方中心节点名称", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "中心节点名称不能为空")
    private String name;

    @Schema(description = "对方 API 根地址", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "API 地址不能为空")
    private String apiBaseUrl;

    @Schema(description = "对方主机地址")
    private String host;

    @Schema(description = "互联令牌", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "互联令牌不能为空")
    private String peerToken;

}
