package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Schema(description = "NFS 运维操作日志")
@Data
public class NodeStorageOpLogRespVO {

    private Long id;
    private Long nodeId;
    private String opType;
    private Boolean success;
    private String message;
    private LocalDateTime createTime;
    private List<NodeMediaRemoteDeployRespVO.DeployStep> steps = new ArrayList<>();
}
