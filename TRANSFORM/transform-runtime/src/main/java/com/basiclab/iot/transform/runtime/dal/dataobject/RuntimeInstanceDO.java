package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.time.Instant;

/** 运行实例监测。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_runtime_instance")
public class RuntimeInstanceDO extends BaseEntity {
    @TableId
    private String instanceId;
    private String nodeId;
    private String host;
    private String role;
    private String status;
    private String joinedGroups;
    private Double cpuLoad;
    private Long heapUsedMb;
    private Long heapMaxMb;
    private Long maxConsumerLag;
    private Double deliverSuccessRate;
    private String metricsJson;
    private String adaptDecision;
    private Instant lastHeartbeatTime;
}
