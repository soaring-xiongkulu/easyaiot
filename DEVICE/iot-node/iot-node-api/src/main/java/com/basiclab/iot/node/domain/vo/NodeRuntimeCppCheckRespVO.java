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

    @Schema(description = "节点 RUNTIME version 字段")
    private String version;

    @Schema(description = "节点 git short")
    private String git;

    @Schema(description = "节点 built_at")
    private String builtAt;

    @Schema(description = "控制面 VERSION.version")
    private String controlPlaneVersion;

    @Schema(description = "与控制面版本是否一致（两侧皆有 version 时才判定）")
    private Boolean versionMatch;

    @Schema(description = "节点 os-release 映射的 RUNTIME 包键，如 openeuler24 / ubuntu24")
    private String osFamily;

    @Schema(description = "节点 CPU 架构键，x86_64 或 arm64")
    private String arch;

    @Schema(description = "是否成功")
    private Boolean success;

    @Schema(description = "摘要")
    private String message;

    @Schema(description = "检测步骤")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
}
