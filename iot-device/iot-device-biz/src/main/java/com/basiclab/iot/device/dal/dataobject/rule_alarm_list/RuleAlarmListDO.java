package com.basiclab.iot.device.dal.dataobject.rule_alarm_list;

import lombok.*;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 告警列 DO
 *
 * @author BasicLab
 */
@TableName("rule_alarm_list")
@KeySequence("rule_alarm_list_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuleAlarmListDO extends BaseDO {

    /**
     * 主键
     */
    @TableId
    private Long id;
    /**
     * 告警时间
     */
    private LocalDateTime alarmTime;
    /**
     * 告警名称
     */
    private String alarmName;
    /**
     * 告警级别
     */
    private Integer alarmLevel;
    /**
     * 告警描述
     */
    private String alarmDescribe;
    /**
     * 处理结果 0 未处理 1已处理
     */
    private Integer processingResult;
    /**
     * 处理意见
     */
    private String processingOpinions;
    /**
     * 告警内容
     */
    private String alarmContent;
    /**
     * 处理人
     */
    private String processingPeople;
    /**
     * 处理时间
     */
    private LocalDateTime processingTime;

}