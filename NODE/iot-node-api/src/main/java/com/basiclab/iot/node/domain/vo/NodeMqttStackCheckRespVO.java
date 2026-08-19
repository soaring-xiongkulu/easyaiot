package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "MQTT 网关（EMQX）SSH 部署状态检测结果")
@Data
public class NodeMqttStackCheckRespVO {

    @Schema(description = "检测是否完成（SSH 连通且探测成功）")
    private Boolean success;

    @Schema(description = "EMQX 是否在运行")
    private Boolean deployed;

    @Schema(description = "EMQX 是否在运行")
    private Boolean emqxRunning;

    @Schema(description = "Docker 是否可用")
    private Boolean dockerReady;

    @Schema(description = "Docker Compose 是否可用")
    private Boolean composeReady;

    @Schema(description = "摘要信息")
    private String message;

    @Schema(description = "检测步骤明细")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();

}
