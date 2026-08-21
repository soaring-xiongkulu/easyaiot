package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "工作负载 - 远程部署 Response VO")
@Data
public class NodeWorkloadDeployRespVO {

    @Schema(description = "进程 PID")
    private Integer pid;

    @Schema(description = "节点 ID")
    private Long nodeId;

    @Schema(description = "工作负载类型")
    private String workloadType;

    @Schema(description = "工作负载 ID")
    private String workloadId;

    @Schema(description = "绑定 ID")
    private Long bindingId;

}
