package com.basiclab.iot.device.dal.dataobject.rule_alarm;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 规则告警 DO
 *
 * @author BasicLab
 */
@TableName("rule_alarm")
@KeySequence("rule_alarm_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuleAlarmDO extends BaseDO {

    /**
     * 规则告警ID
     */
    @TableId
    private Long id;
    /**
     * 规则ID
     */
    private Long ruleId;
    /**
     * 告警规则名称
     */
    private String ruleAlarmName;
    /**
     * 告警状态0 未启动  1运行中
     */
    private Integer ruleAlarmStatus;
    /**
     * 告警规则描述
     */
    private String ruleAlarmRemark;
    /**
     * 告警级别
     */
    private Integer ruleLevel;
    /**
     * 通知方式
     */
    private Integer noticeType;
    /**
     * 创建人
     */
    private String createBy;
    /**
     * 更新人
     */
    private String updateBy;

}