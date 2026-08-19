package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Map;

@Schema(description = "管理后台 - 服务器节点 Response VO")
@Data
public class ComputeNodeRespVO {

    @Schema(description = "主键ID")
    private Long id;

    @Schema(description = "节点名称")
    private String name;

    @Schema(description = "主机地址")
    private String host;

    @Schema(description = "SSH 端口")
    private Integer sshPort;

    @Schema(description = "Agent 端口")
    private Integer agentPort;

    @Schema(description = "状态")
    private String status;

    @Schema(description = "节点角色")
    private String nodeRole;

    @Schema(description = "区域")
    private String region;

    @Schema(description = "标签")
    private Map<String, String> tags;

    @Schema(description = "能力声明")
    private Map<String, Boolean> capabilities;

    @Schema(description = "最大 GPU 数量")
    private Integer maxGpuCount;

    @Schema(description = "最大任务数")
    private Integer maxTaskCount;

    @Schema(description = "调度权重")
    private Integer weight;

    @Schema(description = "备注")
    private String remark;

    @Schema(description = "Agent 令牌（仅创建/重置时返回）")
    private String agentToken;

    @Schema(description = "SSH 用户名")
    private String sshUsername;

    @Schema(description = "SSH 认证方式：password / private_key")
    private String sshAuthType;

    @Schema(description = "SSH 凭据是否已配置")
    private Boolean sshCredentialConfigured;

    @Schema(description = "SSH 最近测试时间")
    private LocalDateTime sshLastTestAt;

    @Schema(description = "SSH 最近测试是否成功")
    private Boolean sshLastTestOk;

    @Schema(description = "最近心跳时间")
    private LocalDateTime lastHeartbeatAt;

    @Schema(description = "CPU 使用率")
    private BigDecimal cpuPercent;

    @Schema(description = "内存使用率")
    private BigDecimal memPercent;

    @Schema(description = "内存已用字节")
    private Long memUsedBytes;

    @Schema(description = "内存总字节")
    private Long memTotalBytes;

    @Schema(description = "磁盘使用率")
    private BigDecimal diskPercent;

    @Schema(description = "磁盘已用字节")
    private Long diskUsedBytes;

    @Schema(description = "磁盘总字节")
    private Long diskTotalBytes;

    @Schema(description = "活跃任务数")
    private Integer activeTasks;

    @Schema(description = "GPU 信息 JSON")
    private String gpuInfo;

    @Schema(description = "是否为控制面宿主机节点（平台自动纳管，不可删除）")
    private Boolean isPlatform;

    @Schema(description = "所属中心节点 ID")
    private Long controlPlaneId;

    @Schema(description = "是否为远程对等中心节点下的节点（联邦展示）")
    private Boolean isRemote;

    @Schema(description = "对等中心节点 ID（远程节点时有值）")
    private Long peerId;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;

}
