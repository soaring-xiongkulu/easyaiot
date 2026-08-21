package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;
import java.util.Map;

@Schema(description = "EDGE 运行时动态配置（MQTT/路径等均由控制面分配）")
@Data
public class EdgeRuntimeConfigRespVO {

    @Schema(description = "有序 MQTT Broker 列表，如 10.0.0.31:1883")
    private List<String> mqttBrokerUrls;

    @Schema(description = "算法租户")
    private String mqttAlgoTenant;

    private String mqttUsername;
    private String mqttPassword;
    private String mqttClientId;

    private String mediaHostDataRoot;
    private String alertImagesDir;
    private String mediaSnapDir;

    @Schema(description = "控制面 agent API 前缀")
    private String controlPlaneUrl;

    @Schema(description = "算法 Topic 提示（与 Kafka 同名 + mqtt/ 前缀）")
    private Map<String, String> algoTopics;

    /** compute_node.id */
    private Long nodeId;

    /** edge_node.id，告警/任务入库应携带此字段 */
    private Long edgeNodeId;

    private String edgeNodeName;

    private String edgeNodeHost;

    private Integer agentPort;

}
