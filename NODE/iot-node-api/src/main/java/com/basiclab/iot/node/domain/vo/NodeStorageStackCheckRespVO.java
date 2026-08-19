package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "Ceph 存储栈 SSH 部署状态检测结果")
@Data
public class NodeStorageStackCheckRespVO {

    @Schema(description = "检测是否完成（SSH 连通且探测成功）")
    private Boolean success;

    @Schema(description = "Ceph 集群与挂载是否就绪")
    private Boolean deployed;

    @Schema(description = "Ceph 集群健康")
    private Boolean cephHealthy;

    @Schema(description = "OSD 在线")
    private Boolean osdRunning;

    @Schema(description = "CephFS 已创建")
    private Boolean cephfsReady;

    @Schema(description = "存储池已创建")
    private Boolean poolExists;

    @Schema(description = "CephFS 挂载就绪")
    private Boolean mountReady;

    @Schema(description = "摘要信息")
    private String message;

    @Schema(description = "检测步骤明细")
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();

}
