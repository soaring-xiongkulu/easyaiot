package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;

@Schema(description = "媒体 - 设备流绑定分配 Request VO")
@Data
public class NodeMediaAllocateReqVO {

    @Schema(description = "设备 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "设备 ID 不能为空")
    private String deviceId;

    @Schema(description = "是否需要 SRS live 播放池")
    private Boolean needSrsLive;

    @Schema(description = "是否需要 SRS ai 算法推流池")
    private Boolean needSrsAi;

    @Schema(description = "是否需要 ZLM 国标媒体节点")
    private Boolean needZlm;

    @Schema(description = "区域/机房（调度偏好）")
    private String region;

    @Schema(description = "HTTP 播放域名（边缘 Nginx，留空则用节点 IP）")
    private String httpPlayHost;

}
