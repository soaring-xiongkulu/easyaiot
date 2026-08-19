package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Schema(description = "节点指标趋势 Response VO")
@Data
public class NodeMetricTrendRespVO {

    @Schema(description = "各节点趋势序列")
    private List<NodeMetricTrendSeriesRespVO> series;

}
