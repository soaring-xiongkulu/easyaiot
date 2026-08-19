package com.basiclab.iot.node.domain.vo;

import com.basiclab.iot.common.domain.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Schema(description = "NFS 运维操作日志分页查询")
@Data
@EqualsAndHashCode(callSuper = true)
public class NodeStorageOpLogPageReqVO extends PageParam {

    @Schema(description = "节点 ID；为空查全部")
    private Long nodeId;

    @Schema(description = "操作类型")
    private String opType;
}
