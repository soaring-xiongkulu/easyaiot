package com.basiclab.iot.node.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Schema(description = "节点指标趋势数据点")
@Data
public class NodeMetricTrendPointRespVO {

    @Schema(description = "采集时间")
    private LocalDateTime collectedAt;

    @Schema(description = "CPU 使用率")
    private BigDecimal cpuPercent;

    @Schema(description = "内存使用率")
    private BigDecimal memPercent;

    @Schema(description = "磁盘使用率")
    private BigDecimal diskPercent;

    @Schema(description = "平均显存使用率")
    private BigDecimal gpuMemPercent;

    @Schema(description = "平均 GPU 利用率")
    private BigDecimal gpuUtilPercent;

    @Schema(description = "活跃任务数")
    private Integer activeTasks;

    @Schema(description = "内存已用字节")
    private Long memUsedBytes;

    @Schema(description = "磁盘已用字节")
    private Long diskUsedBytes;

    @Schema(description = "显存已用字节")
    private Long gpuMemUsedBytes;

}
