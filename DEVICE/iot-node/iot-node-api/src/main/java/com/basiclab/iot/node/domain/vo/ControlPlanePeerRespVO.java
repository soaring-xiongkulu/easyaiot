package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

@Schema(description = "管理后台 - 对等中心节点 Response VO")
@Data
public class ControlPlanePeerRespVO {

    @Schema(description = "主键 ID")
    private Long id;

    @Schema(description = "名称")
    private String name;

    @Schema(description = "API 根地址")
    private String apiBaseUrl;

    @Schema(description = "主机地址")
    private String host;

    @Schema(description = "状态: online | offline | unknown")
    private String status;

    @Schema(description = "远程平台节点 ID")
    private Long remotePlatformNodeId;

    @Schema(description = "最近同步时间")
    private LocalDateTime lastSyncAt;

    @Schema(description = "备注")
    private String remark;

}
