package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Schema(description = "单节点指标趋势序列")
@Data
public class NodeMetricTrendSeriesRespVO {

    @Schema(description = "节点 ID")
    private Long nodeId;

    @Schema(description = "节点名称")
    private String nodeName;

    @Schema(description = "主机地址")
    private String host;

    @Schema(description = "节点状态")
    private String status;

    @Schema(description = "趋势数据点（按时间升序）")
    private List<NodeMetricTrendPointRespVO> points;

}
