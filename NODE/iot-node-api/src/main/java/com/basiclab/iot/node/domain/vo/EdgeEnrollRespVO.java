package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "EDGE 纳管响应")
@Data
public class EdgeEnrollRespVO {

    /** compute_node.id（调度 / Agent 侧节点 ID） */
    private Long nodeId;

    /** edge_node.id（统一边缘管理主键，业务数据区分用此维度） */
    private Long edgeNodeId;

    private String agentToken;
    private EdgeRuntimeConfigRespVO runtimeConfig;

}
