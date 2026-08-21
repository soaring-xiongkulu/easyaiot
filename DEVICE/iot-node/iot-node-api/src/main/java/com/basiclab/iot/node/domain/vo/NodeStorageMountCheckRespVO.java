package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "CephFS 挂载 SSH 检测结果")
@Data
public class NodeStorageMountCheckRespVO {

    @Schema(description = "检测是否完成")
    private Boolean success;

    @Schema(description = "挂载是否就绪")
    private Boolean mountReady;

    @Schema(description = "摘要信息")
    private String message;

    @Schema(description = "检测步骤明细")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();

}
