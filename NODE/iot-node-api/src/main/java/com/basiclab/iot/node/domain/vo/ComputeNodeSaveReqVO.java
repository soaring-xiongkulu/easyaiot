package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.Map;

@Schema(description = "管理后台 - 服务器节点新增/修改 Request VO")
@Data
public class ComputeNodeSaveReqVO {

    @Schema(description = "主键ID")
    private Long id;

    @Schema(description = "节点名称", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "节点名称不能为空")
    private String name;

    @Schema(description = "主机地址", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "主机地址不能为空")
    private String host;

    @Schema(description = "SSH 端口", example = "22")
    private Integer sshPort;

    @Schema(description = "Agent 端口", example = "9100")
    private Integer agentPort;

    @Schema(description = "节点角色: compute | gpu | media | storage | hybrid", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "节点角色不能为空")
    private String nodeRole;

    @Schema(description = "区域/机房")
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

    @Schema(description = "SSH 用户名（创建时可选，用于纳管测试）")
    private String sshUsername;

    @Schema(description = "SSH 认证类型: password | private_key")
    private String sshAuthType;

    @Schema(description = "SSH 密码")
    private String sshPassword;

    @Schema(description = "SSH 私钥内容")
    private String sshPrivateKey;

}
