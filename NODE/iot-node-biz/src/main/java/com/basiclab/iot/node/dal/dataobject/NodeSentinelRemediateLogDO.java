package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.util.List;
import java.util.Map;

@TableName(value = "node_sentinel_remediate_log", autoResultMap = true)
@KeySequence("node_sentinel_remediate_log_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NodeSentinelRemediateLogDO extends BaseDO {

    @TableId
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

    @TableField(typeHandler = JacksonTypeHandler.class)
    private List<Map<String, Object>> logs;
}
