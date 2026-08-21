package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.Map;

@Schema(description = "EDGE 模块自助纳管 Request")
@Data
public class EdgeEnrollReqVO {

    @Schema(description = "主机名")
    private String hostname;

    @Schema(description = "机器指纹")
    private String fingerprint;

    @Schema(description = "节点上报 IP/主机地址")
    private String host;

    @Schema(description = "加入令牌（与 easyaiot.edge.join-token 一致；开放纳管时可空）")
    private String joinToken;

    @Schema(description = "操作系统信息")
    private String osInfo;

    @Schema(description = "Agent/EDGE 版本")
    private String agentVersion;

    @Schema(description = "节点角色，默认 compute")
    private String nodeRole;

    @Schema(description = "最大任务数，边缘默认 1")
    private Integer maxTaskCount;

    @Schema(description = "能力声明")
    private Map<String, Boolean> capabilities;

}
