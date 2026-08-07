package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.Map;

@Schema(description = "工作负载 - 远程部署 Request VO")
@Data
public class NodeWorkloadDeployReqVO {

    @Schema(description = "目标节点 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "节点 ID 不能为空")
    private Long nodeId;

    @Schema(description = "工作负载类型", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "工作负载类型不能为空")
    private String workloadType;

    @Schema(description = "工作负载 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "工作负载 ID 不能为空")
    private String workloadId;

    @Schema(description = "启动命令（runtime=process 时必填；runtime=docker 可空）")
    private List<String> command;

    @Schema(description = "运行时: process | docker，默认 process")
    private String runtime;

    @Schema(description = "Docker 镜像（runtime=docker 时使用）")
    private String image;

    @Schema(description = "工作目录")
    private String workDir;

    @Schema(description = "日志目录")
    private String logDir;

    @Schema(description = "GPU IDs，如 0,1")
    private String gpuIds;

    @Schema(description = "环境变量")
    private Map<String, String> env;

    @Schema(description = "部署前写入节点的文件列表（path + content），用于 RUNTIME ini 等")
    private List<Map<String, String>> files;

}
