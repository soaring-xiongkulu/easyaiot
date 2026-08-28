package com.basiclab.iot.flow.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.db.TenantBaseDO;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 流程抄送记录（任务抄送动作 / 抄送节点产出）
 */
@TableName("flow_copy")
@KeySequence("flow_copy_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class FlowProcessInstanceCopyDO extends TenantBaseDO {

    @TableId
    private Long id;
    /** 流程实例 ID */
    private String processInstanceId;
    /** 流程实例名称 */
    private String processInstanceName;
    /** 流程分类 */
    private String category;
    /** 任务编号（抄送节点产出时为空） */
    private String taskId;
    /** 任务/节点名称 */
    private String taskName;
    /** 活动 ID */
    private String activityId;
    /** 流程发起人 */
    private Long startUserId;
    /** 抄送说明 */
    private String reason;
    /** 抄送接收人 */
    private Long userId;

}
