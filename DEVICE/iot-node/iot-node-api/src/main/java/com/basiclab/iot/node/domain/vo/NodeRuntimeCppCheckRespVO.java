package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "单节点 RUNTIME(C++) 检测响应")
@Data
public class NodeRuntimeCppCheckRespVO {

    @Schema(description = "RUNTIME 是否就绪")
    private Boolean runtimeReady;

    @Schema(description = "远程 RUNTIME 二进制路径")
    private String runtimePath;

    @Schema(description = "是否成功")
    private Boolean success;

    @Schema(description = "摘要")
    private String message;

    @Schema(description = "检测步骤")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
}
