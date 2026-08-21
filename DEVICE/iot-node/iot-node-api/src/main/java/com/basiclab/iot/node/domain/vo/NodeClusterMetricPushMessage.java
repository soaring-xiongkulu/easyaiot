package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Schema(description = "集群概览 WebSocket 推送消息")
@Data
public class NodeClusterMetricPushMessage {

    @Schema(description = "消息类型：snapshot | node_update")
    private String type;

    @Schema(description = "全量节点列表（snapshot）")
    private List<NodeClusterMetricNodeVO> nodes;

    @Schema(description = "单节点更新（node_update）")
    private NodeClusterMetricNodeVO node;

    @Schema(description = "服务端时间戳（毫秒）")
    private Long timestamp;

    public static NodeClusterMetricPushMessage snapshot(List<NodeClusterMetricNodeVO> nodes) {
        NodeClusterMetricPushMessage message = new NodeClusterMetricPushMessage();
        message.setType("snapshot");
        message.setNodes(nodes);
        message.setTimestamp(System.currentTimeMillis());
        return message;
    }

    public static NodeClusterMetricPushMessage nodeUpdate(NodeClusterMetricNodeVO node) {
        NodeClusterMetricPushMessage message = new NodeClusterMetricPushMessage();
        message.setType("node_update");
        message.setNode(node);
        message.setTimestamp(System.currentTimeMillis());
        return message;
    }

}
