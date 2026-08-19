package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.Max;
import javax.validation.constraints.Min;
import java.util.List;

@Schema(description = "节点指标趋势查询 Request VO")
@Data
public class NodeMetricTrendReqVO {

    @Schema(description = "节点 ID 列表，为空则返回全部计算/混合节点")
    private List<Long> nodeIds;

    @Schema(description = "回溯分钟数", example = "30")
    @Min(1)
    @Max(1440)
    private Integer minutes = 30;

    @Schema(description = "每个节点最多返回的数据点数", example = "120")
    @Min(10)
    @Max(500)
    private Integer maxPoints = 120;

}
