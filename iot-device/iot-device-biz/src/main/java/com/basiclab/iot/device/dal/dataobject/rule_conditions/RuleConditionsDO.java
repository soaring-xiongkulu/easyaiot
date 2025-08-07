package com.basiclab.iot.device.dal.dataobject.rule_conditions;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 规则条件 DO
 *
 * @author BasicLab
 */
@TableName("rule_conditions")
@KeySequence("rule_conditions_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RuleConditionsDO extends BaseDO {

    /**
     * 主键
     */
    @TableId
    private Long id;
    /**
     * 规则ID
     */
    private Long ruleId;
    /**
     * 条件类型(0:匹配设备触发、1:指定设备触发、2:按策略定时触发)
     */
    private Short conditionType;
    /**
     * 设备标识(匹配设备设备类型存储一个产品下所有的设备标识逗号分隔，指定设备触发存储指定的设备标识)
     */
    private String did;
    /**
     * 产品标识
     */
    private String pid;
    /**
     * 服务ID
     */
    private Long serviceId;
    /**
     * 属性ID
     */
    private Long propertiesId;
    /**
     * 比较模式	<	<=	>	>=	==	!=	in	between
     */
    private String comparisonMode;
    /**
     * 比较值		between类型传值例子  [10,15] 必须是两位，且数字不能重复	判断数据是否处于一个离散的取值范围内，例如输入[1,2,3,4]，取值范围是1、2、3、4四个值，如果比较值类型为float(double)，两个float（double）型数值相差在0.000001范围内即为相等
     */
    private String comparisonValue;
    /**
     * 创建人
     */
    private String createBy;
    /**
     * 更新人
     */
    private String updateBy;

}