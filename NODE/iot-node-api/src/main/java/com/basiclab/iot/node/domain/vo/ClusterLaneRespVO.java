package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Schema(description = "管理后台 - 集群泳道 Response VO")
@Data
public class ClusterLaneRespVO {

    @Schema(description = "泳道唯一键：local 或 peer-{id}")
    private String laneKey;

    @Schema(description = "中心节点 ID（本地为平台节点 ID）")
    private Long controlPlaneId;

    @Schema(description = "是否为本机中心节点")
    private Boolean isLocal;

    @Schema(description = "对等中心节点 ID（远程泳道）")
    private Long peerId;

    @Schema(description = "中心节点")
    private ComputeNodeRespVO centralNode;

    @Schema(description = "工作节点列表")
    private List<ComputeNodeRespVO> workerNodes;

    @Schema(description = "互联状态: online | offline | unknown | synced")
    private String syncStatus;

}
