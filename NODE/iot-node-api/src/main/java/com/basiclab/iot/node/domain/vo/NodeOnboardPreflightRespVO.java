package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Schema(description = "节点纳管预检结果")
@Data
public class NodeOnboardPreflightRespVO {

    @Schema(description = "是否全部通过")
    private Boolean ok;

    @Schema(description = "失败摘要，可直接展示")
    private String message;

    @Schema(description = "分项检查")
    private List<Check> checks = new ArrayList<>();

    @Data
    public static class Check {
        private String name;
        private Boolean ok;
        private String detail;
        @Schema(description = "为 false 时仅提示，不阻断纳管（如公网探测）")
        private Boolean required;
    }
}
