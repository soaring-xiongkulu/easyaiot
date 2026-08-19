package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "节点代理 SSH 部署状态检测结果")
@Data
public class NodeAgentCheckRespVO {

    @Schema(description = "检测是否完成（SSH 连通且探测成功）")
    private Boolean success;

    @Schema(description = "节点代理是否已部署且可用")
    private Boolean deployed;

    @Schema(description = "安装目录是否存在")
    private Boolean installDirReady;

    @Schema(description = "systemd 服务是否在运行")
    private Boolean serviceRunning;

    @Schema(description = "健康检查是否通过")
    private Boolean healthOk;

    @Schema(description = "agent.env 配置是否与平台一致")
    private Boolean configOk;

    @Schema(description = "NODE_ID 是否匹配")
    private Boolean nodeIdMatch;

    @Schema(description = "AGENT_TOKEN 是否匹配")
    private Boolean tokenMatch;

    @Schema(description = "目标机能否访问控制面地址")
    private Boolean controlPlaneReachable;

    @Schema(description = "目标机 agent.env 中的 CONTROL_PLANE_URL")
    private String controlPlaneUrl;

    @Schema(description = "平台期望的控制面地址")
    private String expectedControlPlaneUrl;

    @Schema(description = "摘要信息")
    private String message;

    @Schema(description = "检测步骤明细")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();

}
