package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@TableName(value = "node_sentinel_snapshot", autoResultMap = true)
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NodeSentinelSnapshotDO extends BaseDO {

    @TableId
    private Long nodeId;

    private String nodeProfile;

    private String sentinelVersion;

    private String probeLevel;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private List<Map<String, Object>> components;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> schedulableCapabilities;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> summary;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> environmentProfile;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> declaredCapabilities;

    private String operationalState;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> remediation;

    private LocalDateTime lastProbeAt;
}
