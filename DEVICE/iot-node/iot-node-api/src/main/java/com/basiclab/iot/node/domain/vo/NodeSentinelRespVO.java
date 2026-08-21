package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Schema(description = "节点 Sentinel 快照 Response VO")
@Data
public class NodeSentinelRespVO {

    @Schema(description = "节点 ID")
    private Long nodeId;

    @Schema(description = "节点功能 CSV（与 NODE_FUNCTIONS 一致）")
    private String nodeProfile;

    @Schema(description = "节点功能列表")
    private List<String> nodeFunctions;

    @Schema(description = "Sentinel 版本")
    private String sentinelVersion;

    @Schema(description = "探测级别")
    private String probeLevel;

    @Schema(description = "组件探测结果")
    private List<Map<String, Object>> components;

    @Schema(description = "可调度能力")
    private Map<String, Object> schedulableCapabilities;

    @Schema(description = "摘要")
    private Map<String, Object> summary;

    @Schema(description = "环境画像")
    private Map<String, Object> environmentProfile;

    @Schema(description = "节点声明能力（与控制面 compute_node.capabilities 对齐）")
    private Map<String, Object> declaredCapabilities;

    @Schema(description = "运行态: healthy | degraded | unavailable | unknown")
    private String operationalState;

    @Schema(description = "自愈打标与次数摘要")
    private Map<String, Object> remediation;

    @Schema(description = "最近探测时间")
    private LocalDateTime lastProbeAt;

    @Schema(description = "是否有新鲜快照")
    private Boolean fresh;

    @Schema(description = "最近自愈日志")
    private List<NodeSentinelRemediateLogRespVO> remediateLogs;
}
