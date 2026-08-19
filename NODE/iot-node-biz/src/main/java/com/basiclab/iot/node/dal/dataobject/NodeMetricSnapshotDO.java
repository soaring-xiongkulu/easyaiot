package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@TableName(value = "node_metric_snapshot", autoResultMap = true)
@KeySequence("node_metric_snapshot_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NodeMetricSnapshotDO extends BaseDO {

    @TableId
    private Long id;

    private Long nodeId;

    private BigDecimal cpuPercent;

    private BigDecimal memPercent;

    private Long memUsedBytes;

    private Long memTotalBytes;

    private BigDecimal diskPercent;

    private Long diskUsedBytes;

    private Long diskTotalBytes;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private List<Map<String, Object>> gpuInfo;

    private Integer activeTasks;

    private BigDecimal bandwidthMbps;

    private LocalDateTime collectedAt;

}
