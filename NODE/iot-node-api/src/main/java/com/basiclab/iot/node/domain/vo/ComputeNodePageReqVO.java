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

    @Schema(description = "按单个功能过滤: algorithm | forward | live | train | llm | label | infer | mqtt | nfs | transform")
    private String function;

    @Schema(description = "区域")
    private String region;

    @Schema(description = "所属中心节点 ID")
    private Long controlPlaneId;

}
