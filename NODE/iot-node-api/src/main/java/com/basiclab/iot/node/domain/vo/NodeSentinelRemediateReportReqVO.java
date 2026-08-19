package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.List;
import java.util.Map;

@Schema(description = "Sentinel 自愈结果汇报 Request VO")
@Data
public class NodeSentinelRemediateReportReqVO {

    @NotNull(message = "nodeId 不能为空")
    private Long nodeId;

    @NotBlank(message = "componentId 不能为空")
    private String componentId;

    private String agentToken;

    @Schema(description = "标记: marked | healing | exhausted | unhealable | healed")
    private String mark;

    private Boolean exhausted;

    private Boolean success;

    private Integer attemptCount;

    private Integer maxAttempts;

    private String probeState;

    private String message;

    private String action;

    private List<Map<String, Object>> logs;
}
