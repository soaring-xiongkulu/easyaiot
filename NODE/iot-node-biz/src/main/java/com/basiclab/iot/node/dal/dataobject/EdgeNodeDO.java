package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 边缘节点管理实体（与 compute_node 一对一：compute_node_id）
 */
@TableName(value = "edge_node", autoResultMap = true)
@KeySequence("edge_node_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EdgeNodeDO extends BaseDO {

    @TableId
    private Long id;

    private Long computeNodeId;

    private String name;

    private String host;

    /** online / offline / disabled */
    private String status;

    private String fingerprint;

    private String mqttClientId;

    private String mqttUsername;

    private String agentVersion;

    private String nodeRole;

    private Integer maxTaskCount;

    private Integer activeTaskCount;

    private Boolean cephMountReady;

    private LocalDateTime lastHeartbeatAt;

    private Boolean enabled;

    private String remark;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, String> tags;

}
