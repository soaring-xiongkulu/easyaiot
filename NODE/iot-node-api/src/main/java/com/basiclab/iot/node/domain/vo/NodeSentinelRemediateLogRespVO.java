package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Schema(description = "Sentinel 自愈日志 Response VO")
@Data
public class NodeSentinelRemediateLogRespVO {

    private Long id;
    private Long nodeId;
    private String componentId;
    private String mark;
    private String action;
    private Boolean success;
    private Boolean exhausted;
    private Integer attemptCount;
    private Integer maxAttempts;
    private String probeState;
    private String message;
    private List<Map<String, Object>> logs;
    private LocalDateTime createTime;
}
