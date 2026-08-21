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

@TableName(value = "compute_node", autoResultMap = true)
@KeySequence("compute_node_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ComputeNodeDO extends BaseDO {

    @TableId
    private Long id;

    private String name;

    private String host;

    private Integer sshPort;

    private Integer agentPort;

    private String status;

    private String nodeRole;

    private String region;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, String> tags;

    @TableField(typeHandler = JacksonTypeHandler.class)
    private Map<String, Boolean> capabilities;

    private Integer maxGpuCount;

    private Integer maxTaskCount;

    private Integer weight;

    private String agentToken;

    private String remark;

    private LocalDateTime lastHeartbeatAt;

    /** 所属中心节点（平台节点）ID */
    private Long controlPlaneId;

}
