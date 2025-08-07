package com.basiclab.iot.device.dal.dataobject.product_event_response;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品模型事件响应 DO
 *
 * @author BasicLab
 */
@TableName("product_event_response")
@KeySequence("product_event_response_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductEventResponseDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 事件id
     */
    private Long eventId;
    /**
     * 服务ID
     */
    private Long serviceId;
    /**
     * 指示数据类型。取值范围：string、int、decimal
     */
    private String datatype;
    /**
     * 指示枚举值。	如开关状态status可有如下取值enumList : [OPEN,CLOSE]	目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
     */
    private String enumlist;
    /**
     * 指示最大值。	仅当dataType为int、decimal时生效，逻辑小于等于。
     */
    private String max;
    /**
     * 指示字符串长度。	仅当dataType为string时生效。
     */
    private String maxlength;
    /**
     * 指示最小值。	仅当dataType为int、decimal时生效，逻辑大于等于。
     */
    private String min;
    /**
     * 命令中参数的描述，不影响实际功能，可配置为空字符串""。
     */
    private String parameterDescription;
    /**
     * 命令中参数的名字。
     */
    private String parameterName;
    /**
     * 指示本条属性是否必填，取值为0或1，默认取值1（必填）。	目前本字段是非功能性字段，仅起到描述作用。
     */
    private String required;
    /**
     * 指示步长。
     */
    private String step;
    /**
     * 指示单位。	取值根据参数确定，如：	•温度单位：“C”或“K”	•百分比单位：“%”	•压强单位：“Pa”或“kPa”
     */
    private String unit;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;

}