package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "切换生效主 NFS 集群")
@Data
public class NfsClusterActivateReqVO {

    @Schema(description = "目标主集群 ID")
    private Long clusterId;

    @Schema(description = "若仍有启用中的桥接，是否强制停止后切换；默认 false（拒绝切换）")
    private Boolean forceStopBridges;
}
