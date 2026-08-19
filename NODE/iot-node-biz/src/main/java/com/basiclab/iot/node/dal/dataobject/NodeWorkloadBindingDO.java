package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

import java.time.LocalDateTime;

@TableName("node_workload_binding")
@KeySequence("node_workload_binding_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NodeWorkloadBindingDO extends BaseDO {

    @TableId
    private Long id;

    private Long nodeId;

    private String workloadType;

    private String workloadId;

    private String status;

    private Integer processPid;

    private LocalDateTime bindAt;

}
