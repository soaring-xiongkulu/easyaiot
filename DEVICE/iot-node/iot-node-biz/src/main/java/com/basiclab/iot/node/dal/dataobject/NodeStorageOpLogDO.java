package com.basiclab.iot.node.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.*;

/**
 * NFS/存储运维操作日志
 */
@TableName("node_storage_op_log")
@KeySequence("node_storage_op_log_id_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NodeStorageOpLogDO extends BaseDO {

    @TableId
    private Long id;

    /** 可为 null：汇总类日志 */
    private Long nodeId;

    /** refresh|check_stack|check_mount|deploy_server|deploy_client|deploy_export|unmount|auto_refresh */
    private String opType;

    private Boolean success;

    private String message;

    private String stepsJson;
}
