package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "媒体栈 SSH 远程部署结果")
@Data
public class NodeMediaRemoteDeployRespVO {

    @Schema(description = "是否成功")
    private Boolean success;

    @Schema(description = "摘要信息")
    private String message;

    @Schema(description = "执行步骤")
    private List<DeployStep> steps = new ArrayList<>();

    @Data
    public static class DeployStep {
        @Schema(description = "步骤名称")
        private String name;
        @Schema(description = "状态: pending | running | success | failed | skipped")
        private String status;
        @Schema(description = "输出")
        private String output;
    }

}
