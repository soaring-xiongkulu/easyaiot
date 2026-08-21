package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Schema(description = "中心节点互联 - 快照 Response VO")
@Data
public class ControlPlaneSnapshotRespVO {

    @Schema(description = "本机中心节点名称")
    private String name;

    @Schema(description = "本机 API 根地址")
    private String apiBaseUrl;

    @Schema(description = "本机主机地址")
    private String host;

    @Schema(description = "平台节点")
    private ComputeNodeRespVO platformNode;

    @Schema(description = "工作节点")
    private List<ComputeNodeRespVO> workerNodes;

}
