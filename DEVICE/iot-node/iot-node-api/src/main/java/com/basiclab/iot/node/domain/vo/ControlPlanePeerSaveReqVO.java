package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import java.time.LocalDateTime;

@Schema(description = "管理后台 - 添加对等中心节点 Request VO")
@Data
public class ControlPlanePeerSaveReqVO {

    @Schema(description = "中心节点名称", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "中心节点名称不能为空")
    private String name;

    @Schema(description = "中心节点 API 根地址，如 http://host:48080/admin-api", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "中心节点 API 地址不能为空")
    private String apiBaseUrl;

    @Schema(description = "互联令牌（与对方协商一致）")
    private String peerToken;

    @Schema(description = "备注")
    private String remark;

}
