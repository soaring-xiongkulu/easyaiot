package com.basiclab.iot.flow.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 告警处理记录（责任闭环）
 */
@TableName("flow_alert_record")
@KeySequence("flow_alert_record_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class FlowAlertRecordDO extends BaseDO {

    /** 处理状态：1 处理中 / 2 已处理（通过）/ 3 已关闭（误报-拒绝）/ 4 已取消 */
    public static final int STATUS_RUNNING = 1;
    public static final int STATUS_APPROVED = 2;
    public static final int STATUS_REJECTED = 3;
    public static final int STATUS_CANCELLED = 4;

    @TableId
    private Long id;
    /** 告警 ID（video 库 alert 表主键） */
    private Long alertId;
    /** 告警来源：VIDEO_TASK（算法任务）等 */
    private String alertSource;
    /** 告警快照 JSON（发起时的告警字段，防源数据变化） */
    private String alertSnapshot;
    /** 流程实例 ID */
    private String processInstanceId;
    /** 处理流程标识 */
    private String processDefinitionKey;
    /** 处理状态 */
    private Integer processInstanceStatus;
    /** 当前节点名称（冗余，列表直读） */
    private String currentTaskName;
    /** 当前责任人昵称（冗余，逗号分隔） */
    private String currentAssignees;
    /** 完成时间 */
    private java.time.LocalDateTime finishTime;

}
