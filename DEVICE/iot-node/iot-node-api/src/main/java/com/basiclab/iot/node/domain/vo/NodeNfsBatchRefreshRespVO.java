package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "NFS 集群批量刷新现状结果")
@Data
public class NodeNfsBatchRefreshRespVO {

    @Schema(description = "整体是否全部成功（跳过不计失败）")
    private Boolean success;

    @Schema(description = "摘要")
    private String message;

    @Schema(description = "各节点探测结果")
    private List<NodeWorkloadBundleNodeResultVO> results = new ArrayList<>();

    @Schema(description = "刷新后的拓扑（含覆盖率）")
    private NodeCephTopologyRespVO topology;
}
