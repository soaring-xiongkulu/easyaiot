package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "媒体栈 SSH 部署状态检测结果")
@Data
public class NodeMediaStackCheckRespVO {

    @Schema(description = "检测是否完成（SSH 连通且探测成功）")
    private Boolean success;

    @Schema(description = "SRS 与 ZLMediaKit 是否均在运行")
    private Boolean deployed;

    @Schema(description = "SRS 是否在运行")
    private Boolean srsRunning;

    @Schema(description = "ZLMediaKit 是否在运行")
    private Boolean zlmRunning;

    @Schema(description = "Docker 是否可用")
    private Boolean dockerReady;

    @Schema(description = "Docker Compose 是否可用")
    private Boolean composeReady;

    @Schema(description = "摘要信息")
    private String message;

    @Schema(description = "检测步骤明细")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();

}
