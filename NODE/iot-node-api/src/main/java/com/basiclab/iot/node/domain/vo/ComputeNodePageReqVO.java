package com.basiclab.iot.node.domain.vo;

import com.basiclab.iot.common.domain.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;

@Schema(description = "管理后台 - 服务器节点分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class ComputeNodePageReqVO extends PageParam {

    @Schema(description = "节点名称")
    private String name;

    @Schema(description = "主机地址")
    private String host;

    @Schema(description = "状态: pending | online | offline | maintenance")
    private String status;

    @Schema(description = "节点角色: compute | media | hybrid")
    private String nodeRole;

    @Schema(description = "区域")
    private String region;

    @Schema(description = "所属中心节点 ID")
    private Long controlPlaneId;

}
