package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "单节点工作负载 bundle 操作结果")
@Data
public class NodeWorkloadBundleNodeResultVO {

    @Schema(description = "节点 ID")
    private Long nodeId;

    @Schema(description = "节点名称")
    private String nodeName;

    @Schema(description = "主机地址")
    private String host;

    @Schema(description = "是否成功")
    private Boolean success;

    @Schema(description = "摘要")
    private String message;

    @Schema(description = "节点 RUNTIME 版本（runtime_cpp 检测时）")
    private String version;

    @Schema(description = "控制面 RUNTIME 版本（runtime_cpp 检测时）")
    private String controlPlaneVersion;

    @Schema(description = "与控制面版本是否一致")
    private Boolean versionMatch;

    @Schema(description = "执行步骤")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
}
