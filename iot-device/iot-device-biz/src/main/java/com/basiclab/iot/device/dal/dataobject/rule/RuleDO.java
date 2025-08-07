package com.basiclab.iot.device.dal.dataobject.rule;

import lombok.*;
import java.util.*;
import java.time.LocalDateTime;
import java.time.LocalDateTime;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 规则信息 DO
 *
 * @author BasicLab
 */
@TableName("rule")
@KeySequence("rule_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuleDO extends BaseDO {

    /**
     * 主键
     */
    @TableId
    private Long id;
    /**
     * 应用ID
     */
    private String appId;
    /**
     * 规则标识
     */
    private String ruleCode;
    /**
     * 规则名称
     */
    private String ruleName;
    /**
     * 任务标识
     */
    private String jobCode;
    /**
     * 状态(字典值：0启用  1停用)
     */
    private String status;
    /**
     * 触发机制（0:全部，1:任意一个）
     */
    private Short triggering;
    /**
     * 规则描述，可以为空
     */
    private String remark;
    /**
     * 创建人
     */
    private String createBy;
    /**
     * 更新人
     */
    private String updateBy;

}